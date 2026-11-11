"""Testes de QA [T09-T10] para contrato de persistência MongoDB e API FastAPI (#22).

Escopo executável na base atual da `developer`:
- T09: validação dos exemplos canônicos (`docs/banco/exemplos/analise-*.json`) e
  rejeição dos inválidos (`analises-invalidas.json`), serialização BSON real
  (`bson.BSON`), compatibilidade ponta a ponta `PipelineClassificacao -> BSON -> FonteApi`,
  privacidade de metadados do XFetch (sem `autor_id`/`conversa_id`), semântica da
  chave única `(fonte, id_origem)` e sanitização de falhas no encerramento do cliente.
- T10: contrato HTTP real da aplicação FastAPI (`src/servico/main.py`) via `TestClient`
  (`GET /health`, `405 Method Not Allowed`, OpenAPI) e integração real dos clientes
  `FonteApi` e `AdministracaoApi` contra o ASGI atual (confirmando `GET /health`
  funcional e erro claro `404` nas rotas que aguardam as issues #21 e #58).

Nota de bloqueio: testes de escrita/leitura em coleção real (`repositorio.py`) e
respostas `200`/`201`/`202` das rotas `/analises*`, `/auth/*`, `/datasets` e `/coletas*`
dependem da integração das issues #20 e #21 na `developer`.
"""

import json
import math
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from bson import BSON
from fastapi.testclient import TestClient
from pymongo.errors import ConnectionFailure, OperationFailure

from src.apresentacao.contrato import (
    SENTIMENTOS,
    ErroAutenticacao,
    ErroFonteDados,
    FiltrosAnalises,
    SessaoAdministrador,
)
from src.apresentacao.fontes.administracao_api import AdministracaoApi
from src.apresentacao.fontes.api import FonteApi
from src.dados import database
from src.processamento.aquisicao import xfetch
from src.processamento.aquisicao.csv_importer import importar_dataset_csv
from src.processamento.pipeline import PipelineClassificacao
from src.servico.administracao import ContextoAdministracao, obter_contexto
from src.servico.autenticacao import Autenticador
from src.servico.dependencias import obter_colecao_analises
from src.servico.main import app

RAIZ = Path(__file__).resolve().parents[1]
DIR_EXEMPLOS_BANCO = RAIZ / "docs" / "banco" / "exemplos"
EXEMPLOS_VALIDOS = (
    "analise-completa.json",
    "analise-minima.json",
    "analise-tweetsentbr.json",
    "analise-baseline.json",
)
CAMPOS_PROIBIDOS_XFETCH = {
    "author_id",
    "autor_id",
    "conversa_id",
    "user",
    "username",
    "author",
    "user_id",
    "screen_name",
}


class ClassificadorDeterministicoQA:
    """Classificador determinístico para validar o contrato Pipeline -> BSON."""

    nome_modelo = "pysentimiento/bertweet-pt-sentiment"

    def prever_com_probabilidades(self, textos: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "sentimento": "POS",
                "probabilidades": {"positivo": 0.85, "negativo": 0.05, "neutro": 0.10},
            }
            for _ in textos
        ]


class ErroContratoEsquemaMongoDB(ValueError):
    """Documento fora do contrato canônico da coleção `analises`."""


def _converter_extended_json_datas(documento: dict[str, Any]) -> dict[str, Any]:
    """Converte objetos `{"$date": "..."}` dos exemplos JSON em `datetime` UTC."""
    convertido = dict(documento)
    for campo in ("data_publicacao", "data_processamento"):
        valor = convertido.get(campo)
        if isinstance(valor, dict) and set(valor) == {"$date"}:
            iso = valor["$date"]
            if not isinstance(iso, str):
                raise ErroContratoEsquemaMongoDB(
                    f"{campo}.$date precisa ser string ISO 8601."
                )
            data = datetime.fromisoformat(iso)
            if data.tzinfo is None:
                raise ErroContratoEsquemaMongoDB(
                    f"{campo} precisa informar fuso horário."
                )
            convertido[campo] = data.astimezone(UTC)
    return convertido


def validar_documento_esquema_mongodb(documento: dict[str, Any]) -> None:
    """Valida as regras canônicas de `docs/banco/esquema-mongodb.md` e `contratos-dados.md`."""
    if not isinstance(documento, dict):
        raise ErroContratoEsquemaMongoDB("Documento deve ser um dicionário.")

    for campo in ("id_origem", "fonte", "texto_original"):
        valor = documento.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ErroContratoEsquemaMongoDB(f"Campo obrigatório inválido: {campo}")

    if documento.get("sentimento") not in SENTIMENTOS:
        raise ErroContratoEsquemaMongoDB("sentimento fora dos valores canônicos.")

    modelo = documento.get("modelo")
    if not isinstance(modelo, dict):
        raise ErroContratoEsquemaMongoDB("modelo deve ser um objeto.")
    nome_modelo = modelo.get("nome")
    if not isinstance(nome_modelo, str) or not nome_modelo.strip():
        raise ErroContratoEsquemaMongoDB("modelo.nome é obrigatório.")

    if "data_processamento" not in documento:
        raise ErroContratoEsquemaMongoDB("data_processamento é obrigatória.")

    for campo in ("data_processamento", "data_publicacao"):
        if campo in documento:
            data = documento[campo]
            if not isinstance(data, datetime) or data.tzinfo is None:
                raise ErroContratoEsquemaMongoDB(
                    f"{campo} deve ser datetime com fuso horário UTC."
                )

    if (
        "rotulo_padronizado" in documento
        and documento["rotulo_padronizado"] not in SENTIMENTOS
    ):
        raise ErroContratoEsquemaMongoDB(
            "rotulo_padronizado deve usar positivo, negativo ou neutro."
        )

    if "probabilidades" in documento:
        probs = documento["probabilidades"]
        if not isinstance(probs, dict) or set(probs) != set(SENTIMENTOS):
            raise ErroContratoEsquemaMongoDB(
                "probabilidades deve conter positivo, negativo e neutro."
            )
        for classe, prob in probs.items():
            if isinstance(prob, bool) or not isinstance(prob, (int, float)):
                raise ErroContratoEsquemaMongoDB(
                    f"Probabilidade inválida para {classe}."
                )
            if not math.isfinite(float(prob)) or not 0.0 <= float(prob) <= 1.0:
                raise ErroContratoEsquemaMongoDB(
                    f"Probabilidade fora de [0, 1] para {classe}."
                )
        if not math.isclose(sum(probs.values()), 1.0, rel_tol=0.0, abs_tol=1e-3):
            raise ErroContratoEsquemaMongoDB("Soma das probabilidades deve ser 1.0.")

    for opcional in (
        "texto_tratado",
        "probabilidades",
        "rotulo_original",
        "rotulo_padronizado",
        "data_publicacao",
        "metadados",
    ):
        if opcional in documento and documento[opcional] is None:
            raise ErroContratoEsquemaMongoDB(
                f"Campo opcional {opcional} deve ser omitido quando None."
            )


# --- T09: Esquema BSON, Exemplos do Banco, Pipeline e Conexão ----------------


@pytest.mark.parametrize("nome_arquivo", EXEMPLOS_VALIDOS)
def test_t09_exemplos_validos_do_banco_seguem_contrato_e_serializam_em_bson(nome_arquivo):
    bruto = json.loads((DIR_EXEMPLOS_BANCO / nome_arquivo).read_text(encoding="utf-8"))
    documento = _converter_extended_json_datas(bruto)

    validar_documento_esquema_mongodb(documento)

    bytes_bson = BSON.encode(documento)
    decodificado = BSON(bytes_bson).decode()
    assert decodificado["id_origem"] == documento["id_origem"]
    assert decodificado["fonte"] == documento["fonte"]
    assert decodificado["sentimento"] == documento["sentimento"]
    assert decodificado["modelo"]["nome"] == documento["modelo"]["nome"]


def test_t09_todos_os_exemplos_invalidos_do_banco_sao_rejeitados():
    invalidos = json.loads(
        (DIR_EXEMPLOS_BANCO / "analises-invalidas.json").read_text(encoding="utf-8")
    )
    assert len(invalidos) == 8

    ids_rejeitados = []
    for item in invalidos:
        documento = _converter_extended_json_datas(item)
        with pytest.raises(ValueError):
            validar_documento_esquema_mongodb(documento)
        ids_rejeitados.append(item["id_origem"])

    assert ids_rejeitados == [f"inv_{i:03d}" for i in range(1, 9)]


def test_t09_pipeline_gera_bson_compativel_com_leitura_da_fonte_api():
    pipeline = PipelineClassificacao(
        classificador=ClassificadorDeterministicoQA(),
        versao_modelo="qa-sprint4",
    )
    registros = [
        {
            "id_origem": "reg_com_data",
            "fonte": "b2w",
            "texto_original": "Entrega rápida e produto excelente.",
            "rotulo_original": "5",
            "rotulo_padronizado": "POS",
            "data_publicacao": "2026-10-15",
            "metadados": {"categoria": "informatica"},
        },
        {
            "id_origem": "reg_sem_data",
            "fonte": "TweetSentBR",
            "texto_original": "Episódio bastante interessante hoje.",
            "rotulo_original": None,
            "rotulo_padronizado": None,
            "data_publicacao": None,
            "metadados": None,
        },
    ]

    documentos = pipeline.processar_registros(registros)
    assert len(documentos) == 2

    itens_api = []
    for doc in documentos:
        validar_documento_esquema_mongodb(doc)
        # Garante codificação BSON sem perda de campos obrigatórios
        persistido = BSON(BSON.encode(doc)).decode()
        item_json = {
            "id_origem": persistido["id_origem"],
            "fonte": persistido["fonte"],
            "texto_original": persistido["texto_original"],
            "sentimento": persistido["sentimento"],
            "probabilidades": persistido["probabilidades"],
            "modelo": persistido["modelo"],
            "data_processamento": doc["data_processamento"].isoformat().replace("+00:00", "Z"),
            "data_publicacao": (
                doc["data_publicacao"].isoformat().replace("+00:00", "Z")
                if "data_publicacao" in doc
                else None
            ),
        }
        itens_api.append(item_json)

    sessao_http = Mock()
    sessao_http.get.return_value = Mock(
        status_code=200,
        json=lambda: {"itens": itens_api, "pagina": 1, "tamanho": 20, "total": 2},
    )
    fonte_api = FonteApi("http://api.local", sessao=sessao_http)
    pagina = fonte_api.listar(FiltrosAnalises())

    assert pagina.total == 2
    assert pagina.itens[0].id_origem == "reg_com_data"
    assert pagina.itens[0].data_publicacao == datetime(2026, 10, 15, 0, 0, tzinfo=UTC)
    assert pagina.itens[1].id_origem == "reg_sem_data"
    assert pagina.itens[1].data_publicacao is None


def test_t09_xfetch_pipeline_nao_persiste_autor_id_nem_conversa_id_no_bson(monkeypatch):
    resposta_falsa = Mock(
        status_code=200,
        raise_for_status=Mock(),
        json=lambda: {
            "data": [
                {
                    "id": "tw_9001",
                    "text": "Serviço funcionando perfeitamente.",
                    "created_at": "2026-11-03T12:00:00-03:00",
                    "lang": "pt",
                    "author_id": "autor_secreto_123",
                    "autor_id": "autor_secreto_123",
                    "conversa_id": "conv_999",
                    "username": "usuario_real",
                    "like_count": 7,
                    "retweet_count": 2,
                }
            ]
        },
    )
    monkeypatch.setattr(xfetch.requests, "get", Mock(return_value=resposta_falsa))
    coletados = xfetch.buscar_tweets_xfetch(
        "serviço", quantidade=10, api_key="chave-sintetica-qa"
    )
    assert len(coletados) == 1

    pipeline = PipelineClassificacao(classificador=ClassificadorDeterministicoQA())
    documento = pipeline.processar_registros(coletados)[0]
    validar_documento_esquema_mongodb(documento)

    chaves_documento = set(documento) | set(documento.get("metadados", {}))
    assert chaves_documento.isdisjoint(CAMPOS_PROIBIDOS_XFETCH)
    assert documento["metadados"] == {
        "provedor": "XFetch",
        "lang": "pt",
        "like_count": 7,
        "retweet_count": 2,
    }


def test_t09_chave_composta_fonte_id_origem_distingue_fontes_e_detecta_duplicata(tmp_path):
    csv_a = tmp_path / "a.csv"
    csv_b = tmp_path / "b.csv"
    csv_a.write_text("texto,fonte\nMesmo texto de avaliação,b2w\n", encoding="utf-8")
    csv_b.write_text("texto,fonte\nMesmo texto de avaliação,olist\n", encoding="utf-8")

    reg_a1 = importar_dataset_csv(csv_a)[0]
    reg_a2 = importar_dataset_csv(csv_a)[0]
    reg_b1 = importar_dataset_csv(csv_b)[0]

    chave_a1 = (reg_a1["fonte"], reg_a1["id_origem"])
    chave_a2 = (reg_a2["fonte"], reg_a2["id_origem"])
    chave_b1 = (reg_b1["fonte"], reg_b1["id_origem"])

    # Mesma fonte e mesmo conteúdo/posição -> mesma chave única (duplicata)
    assert chave_a1 == chave_a2
    # Fontes distintas -> chaves distintas no índice uq_fonte_id_origem
    assert chave_a1 != chave_b1


@pytest.mark.parametrize("erro_driver", [ConnectionFailure, OperationFailure])
def test_t09_disconnect_sanitiza_excecoes_do_driver_ao_fechar(erro_driver):
    segredo = "SENHA_SUPER_SECRETA_ATLAS"
    cliente = Mock()
    cliente.close.side_effect = erro_driver(f"mongodb+srv://admin:{segredo}@cluster/db")

    with pytest.raises(database.ErroConexaoMongoDB) as capturada:
        database.disconnect_from_mongodb(cliente)

    assert segredo not in str(capturada.value)
    assert "Não foi possível encerrar o cliente MongoDB" in str(capturada.value)


# --- T10: API FastAPI Real (TestClient) e Contratos HTTP ---------------------


class AdaptadorTestClientRequests:
    """Conecta `FonteApi` e `AdministracaoApi` diretamente ao `TestClient(app)`."""

    def __init__(self, cliente_asgi: TestClient) -> None:
        self._cliente = cliente_asgi

    def get(self, url: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        rota = "/" + url.split("://", 1)[-1].split("/", 1)[-1]
        cabecalhos = kwargs.get("headers") or {}
        return self._cliente.get(rota, params=params, headers=cabecalhos)

    def post(self, url: str, **kwargs: Any) -> Any:
        rota = "/" + url.split("://", 1)[-1].split("/", 1)[-1]
        cabecalhos = kwargs.get("headers") or {}
        return self._cliente.post(
            rota,
            json=kwargs.get("json"),
            files=kwargs.get("files"),
            headers=cabecalhos,
        )


def test_t10_health_contrato_http_cabecalhos_e_esquema_openapi():
    cliente = TestClient(app)
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("application/json")
    assert resposta.json() == {"status": "ok"}

    openapi = cliente.get("/openapi.json")
    assert openapi.status_code == 200
    esquema = openapi.json()
    assert esquema["info"]["title"] == "SentIA API"
    assert {
        "/health",
        "/auth/login",
        "/auth/logout",
        "/datasets",
        "/coletas/fontes",
        "/coletas",
        "/coletas/{id_coleta}",
        "/analises",
        "/analises/resumo",
    } <= set(esquema["paths"])


@pytest.mark.parametrize("metodo", ["post", "put", "delete", "patch"])
def test_t10_health_rejeita_metodos_http_nao_permitidos_com_405(metodo):
    cliente = TestClient(app)
    resposta = getattr(cliente, metodo)("/health")
    assert resposta.status_code == 405


def test_t10_fonte_api_contra_fastapi_real_valida_health_e_consultas_vazias(monkeypatch):
    colecao = Mock()
    colecao.count_documents.return_value = 0
    colecao.find.return_value.sort.return_value.skip.return_value.limit.return_value = []
    colecao.aggregate.return_value = []
    monkeypatch.setitem(app.dependency_overrides, obter_colecao_analises, lambda: colecao)
    sessao_asgi = AdaptadorTestClientRequests(TestClient(app))
    fonte = FonteApi("http://testserver", sessao=sessao_asgi)

    assert fonte.verificar_saude() is True

    pagina = fonte.listar(FiltrosAnalises(inicio=date(2026, 10, 1), sentimento="positivo"))
    assert pagina.total == 0
    assert pagina.itens == []
    resumo = fonte.resumir(FiltrosAnalises())
    assert resumo.total == 0
    assert resumo.sem_data_publicacao == 0
    assert resumo.por_sentimento == {"positivo": 0, "negativo": 0, "neutro": 0}


def test_t10_administracao_api_contra_fastapi_real_sinaliza_503_e_sessao_invalida(
    monkeypatch,
):
    contexto = ContextoAdministracao(Autenticador(configuracao=None))
    monkeypatch.setitem(app.dependency_overrides, obter_contexto, lambda: contexto)
    cliente = TestClient(app)
    sessao_asgi = AdaptadorTestClientRequests(cliente)
    admin = AdministracaoApi("http://testserver", sessao=sessao_asgi)
    sessao_admin = SessaoAdministrador(
        token="token-qa",
        usuario="admin",
        expira_em=datetime(2030, 1, 1, tzinfo=UTC),
    )

    resposta = cliente.post("/auth/login", json={"usuario": "admin", "senha": "senha"})
    assert resposta.status_code == 503

    with pytest.raises(ErroFonteDados, match="A administração não está configurada"):
        admin.entrar("admin", "senha")

    with pytest.raises(ErroAutenticacao, match="Sua sessão expirou. Entre novamente."):
        admin.importar_dataset(sessao_admin, "lote.csv", b"texto,fonte\nola,x\n")

    with pytest.raises(ErroAutenticacao, match="Sua sessão expirou. Entre novamente."):
        admin.listar_fontes_coleta(sessao_admin)

    with pytest.raises(ErroAutenticacao, match="Sua sessão expirou. Entre novamente."):
        admin.iniciar_coleta(sessao_admin, "tweetsentbr")

    with pytest.raises(ErroAutenticacao, match="Sua sessão expirou. Entre novamente."):
        admin.consultar_coleta(sessao_admin, "c1")


@pytest.mark.parametrize(
    ("status_code", "corpo", "trecho_esperado"),
    [
        (415, {"mensagem": "Formato deve ser text/csv."}, "Formato deve ser text/csv."),
        (429, None, "Muitas tentativas"),
    ],
)
def test_t10_administracao_api_trata_codigos_415_e_429_do_contrato(
    status_code, corpo, trecho_esperado
):
    sessao_http = Mock()
    sessao_http.post.return_value = Mock(
        status_code=status_code,
        json=(lambda: corpo) if corpo is not None else Mock(side_effect=ValueError),
    )
    admin = AdministracaoApi("http://api.local", sessao=sessao_http)
    sessao_admin = SessaoAdministrador(
        token="token-qa",
        usuario="admin",
        expira_em=datetime(2030, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(ErroFonteDados, match=trecho_esperado):
        admin.importar_dataset(sessao_admin, "arquivo.bin", b"\x00\x01")
