"""Testes de integração da persistência unificada com MongoDB real.

Exercita `RepositorioAnalises` (`src/dados/repositorio.py`), a API principal
(`src/servico/main.py`) e os fluxos administrativos (`src/servico/administracao.py`)
conectados ao mesmo banco `analises`. No CI, exige o serviço `mongo:7`.
"""

import os
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import ServerSelectionTimeoutError

from src.dados.database import (
    ErroConexaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)
from src.dados.repositorio import (
    ErroConsultaInvalida,
    ErroLeituraAnalises,
    RepositorioAnalises,
    criar_indices,
    obter_colecao,
)
from src.servico import administracao
from src.servico.autenticacao import Autenticador, ConfiguracaoAdmin, gerar_hash_senha
from src.servico.dependencias import obter_pipeline
from src.servico.main import app


def utc(ano: int, mes: int, dia: int, hora: int = 0, minuto: int = 0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=UTC)


def criar_documento(
    id_origem: str,
    sentimento: str = "positivo",
    fonte: str = "b2w",
    proc: datetime | None = None,
    pub: datetime | None = None,
    **extra,
) -> dict:
    doc: dict = {
        "id_origem": id_origem,
        "fonte": fonte,
        "texto_original": f"texto {id_origem}",
        "sentimento": sentimento,
        "modelo": {"nome": "pysentimiento/bertweet-pt-sentiment"},
        "data_processamento": proc or utc(2026, 11, 3, 14, 30),
    }
    if pub is not None:
        doc["data_publicacao"] = pub
    doc.update(extra)
    return doc


def uri_com_banco(uri_base: str, nome_banco: str) -> str:
    partes = urlsplit(uri_base)
    return urlunsplit((partes.scheme, partes.netloc, f"/{nome_banco}", partes.query, ""))


class PipelineFalso:
    @staticmethod
    def _normalizar_data_publicacao(valor: str | None) -> datetime | None:
        if not valor:
            return None
        data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        if data.tzinfo is None:
            data = data.replace(tzinfo=UTC)
        return data.astimezone(UTC)

    def processar_registros(self, registros):
        saida = []
        for registro in registros:
            sentimento = "negativo" if "ruim" in registro["texto_original"].lower() else "positivo"
            item = {
                "id_origem": registro["id_origem"],
                "fonte": registro["fonte"],
                "texto_original": registro["texto_original"],
                "sentimento": sentimento,
                "probabilidades": {
                    "positivo": 1.0 if sentimento == "positivo" else 0.0,
                    "negativo": 1.0 if sentimento == "negativo" else 0.0,
                    "neutro": 0.0,
                },
                "modelo": {"nome": "pipeline-falso"},
                "data_processamento": datetime.now(UTC),
            }
            if registro.get("data_publicacao"):
                item["data_publicacao"] = self._normalizar_data_publicacao(
                    str(registro["data_publicacao"])
                )
            if registro.get("rotulo_original") is not None:
                item["rotulo_original"] = registro["rotulo_original"]
            if registro.get("metadados") is not None:
                item["metadados"] = registro["metadados"]
            saida.append(item)
        return saida


@pytest.fixture(scope="session")
def uri_mongodb_teste() -> str:
    return os.getenv("MONGODB_URI_TESTE", "mongodb://127.0.0.1:27017")


@pytest.fixture(scope="session")
def client(uri_mongodb_teste: str):
    if os.getenv("SENTIA_TESTES_SEM_MONGODB") == "1":
        pytest.skip("MongoDB real desabilitado explicitamente nesta execução.")
    try:
        cliente = connect_to_mongodb(uri_mongodb_teste, timeout_ms=1000)
    except ErroConexaoMongoDB:
        if os.getenv("CI"):
            pytest.fail("MongoDB de teste indisponível no CI.")
        pytest.skip("MongoDB de teste indisponível (suba com docker/podman mongo:7).")
    yield cliente
    disconnect_from_mongodb(cliente)


@pytest.fixture
def nome_banco_teste(client):
    nome = f"sentia_teste_{uuid4().hex[:8]}"
    client.drop_database(nome)
    yield nome
    client.drop_database(nome)


@pytest.fixture
def colecao(client, nome_banco_teste):
    col = obter_colecao(client, nome_banco_teste)
    col.delete_many({})
    criar_indices(col)
    yield col
    col.delete_many({})


@pytest.fixture
def repositorio(colecao) -> RepositorioAnalises:
    return RepositorioAnalises(colecao)


# ---------- testes do repositório canônico com MongoDB real ----------


def test_insere_e_le_por_chave_natural_e_object_id(repositorio):
    repositorio.salvar_analises(
        [criar_documento("a1", rotulo_original="5", metadados={"category": "x"})]
    )

    lido = repositorio.buscar_por_id_origem("b2w", "a1")
    assert lido is not None
    assert lido["texto_original"] == "texto a1"
    assert lido["sentimento"] == "positivo"
    assert lido["rotulo_original"] == "5"
    assert lido["metadados"] == {"category": "x"}
    assert "data_publicacao" not in lido

    por_id = repositorio.buscar_por_id(str(lido["_id"]))
    assert por_id is not None
    assert por_id["id_origem"] == "a1"
    assert repositorio.buscar_por_id_origem("b2w", "nao-existe") is None
    assert repositorio.buscar_por_id("id-malformado") is None


def test_mesmo_id_em_fontes_diferentes_nao_conflita(repositorio):
    resultado = repositorio.salvar_analises(
        [criar_documento("x", fonte="b2w"), criar_documento("x", fonte="olist")]
    )
    assert resultado == {"inseridos": 2, "duplicados": 0}
    assert repositorio.buscar_por_id_origem("olist", "x")["fonte"] == "olist"


def test_colecao_vazia_retorna_pagina_e_resumo_vazios(repositorio):
    assert repositorio.listar_analises() == {
        "itens": [],
        "pagina": 1,
        "tamanho": 20,
        "total": 0,
    }
    assert repositorio.resumir_analises() == {
        "total": 0,
        "por_sentimento": {"positivo": 0, "negativo": 0, "neutro": 0},
        "sem_data_publicacao": 0,
    }


def test_listar_analises_filtra_ordena_pagina_e_omite_id(repositorio):
    repositorio.salvar_analises([
        criar_documento("1", "positivo", proc=utc(2026, 11, 1), pub=utc(2026, 10, 1)),
        criar_documento("2", "negativo", proc=utc(2026, 11, 2), pub=utc(2026, 10, 15)),
        criar_documento("3", "negativo", fonte="olist", proc=utc(2026, 11, 2), pub=utc(2026, 10, 20)),
        criar_documento("4", "negativo", proc=utc(2026, 11, 5), pub=utc(2026, 11, 1)),
        criar_documento("5", "negativo", proc=utc(2026, 11, 6)),  # sem data_publicacao
    ])

    pagina1 = repositorio.listar_analises(
        sentimento="negativo",
        inicio=date(2026, 10, 15),
        fim=date(2026, 10, 31),
        pagina=1,
        tamanho=1,
    )
    pagina2 = repositorio.listar_analises(
        sentimento="negativo",
        inicio=date(2026, 10, 15),
        fim=date(2026, 10, 31),
        pagina=2,
        tamanho=1,
    )

    assert pagina1["total"] == 2
    assert pagina1["pagina"] == 1
    assert pagina1["tamanho"] == 1
    assert [d["id_origem"] for d in pagina1["itens"]] == ["2"]
    assert [d["id_origem"] for d in pagina2["itens"]] == ["3"]
    assert all("_id" not in d for d in pagina1["itens"] + pagina2["itens"])


def test_resumir_analises_agrega_sentimentos_e_conta_sem_data(repositorio):
    repositorio.salvar_analises([
        criar_documento("1", "positivo", pub=utc(2026, 10, 10)),
        criar_documento("2", "negativo", pub=utc(2026, 10, 11)),
        criar_documento("3", "neutro", pub=utc(2026, 10, 12)),
        criar_documento("4", "positivo"),  # sem data_publicacao
        criar_documento("5", "negativo", pub=utc(2026, 9, 1)),  # fora do período
    ])

    assert repositorio.resumir_analises() == {
        "total": 5,
        "por_sentimento": {"positivo": 2, "negativo": 2, "neutro": 1},
        "sem_data_publicacao": 0,
    }
    assert repositorio.resumir_analises(inicio=date(2026, 10, 1), fim=date(2026, 10, 31)) == {
        "total": 3,
        "por_sentimento": {"positivo": 1, "negativo": 1, "neutro": 1},
        "sem_data_publicacao": 1,
    }


def test_documentos_invalidos_no_banco_nao_quebram_resumo_nem_base(colecao, repositorio):
    colecao.insert_many([
        criar_documento("valido", sentimento="positivo"),
        {
            "id_origem": "sem-texto",
            "fonte": "legado",
            "sentimento": "desconhecido",
            "data_processamento": utc(2026, 11, 3),
        },
        {
            "id_origem": "sem-sentimento",
            "fonte": "legado",
            "texto_original": "   ",
            "data_processamento": utc(2026, 11, 3),
        },
    ])

    resumo = repositorio.resumir_analises()
    assert resumo == {
        "total": 1,
        "por_sentimento": {"positivo": 1, "negativo": 0, "neutro": 0},
        "sem_data_publicacao": 0,
    }
    registros = repositorio.listar_registros_base()
    assert [r["id_origem"] for r in registros] == ["valido"]


def test_conexao_porta_invalida_e_consulta_invalida_falham_com_seguranca(repositorio):
    with pytest.raises(ErroConexaoMongoDB) as erro:
        connect_to_mongodb("mongodb://usuario:senha@127.0.0.1:1", timeout_ms=300)
    assert "senha" not in str(erro.value)

    with pytest.raises(ErroConsultaInvalida):
        repositorio.listar_analises(pagina=0)

    class ColecaoFalha:
        def _falha(self, *_args, **_kwargs):
            raise ServerSelectionTimeoutError("mongodb://usuario:senha@host caiu")

        count_documents = aggregate = find = find_one = _falha

    repo_quebrado = RepositorioAnalises(ColecaoFalha())
    for acao in (
        repo_quebrado.listar_analises,
        repo_quebrado.resumir_analises,
        repo_quebrado.listar_registros_base,
        lambda: repo_quebrado.buscar_por_id_origem("b2w", "1"),
    ):
        with pytest.raises(ErroLeituraAnalises) as erro_leitura:
            acao()
        assert "senha" not in str(erro_leitura.value)


# ---------- testes end-to-end API + Administração + MongoDB real ----------


def test_api_persiste_analises_e_mantem_dados_em_nova_conexao(
    monkeypatch, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    monkeypatch.setenv("MONGODB_URI", uri_teste)
    app.dependency_overrides[obter_pipeline] = lambda: PipelineFalso()
    try:
        cliente = TestClient(app)
        resposta_post = cliente.post(
            "/analises",
            json={
                "registros": [
                    {
                        "id_origem": "api_1",
                        "fonte": "app",
                        "texto_original": "Atendimento excelente!",
                        "data_publicacao": "2026-11-01T12:00:00Z",
                    },
                    {
                        "id_origem": "api_2",
                        "fonte": "app",
                        "texto_original": "Entrega muito ruim.",
                    },
                ]
            },
        )
        assert resposta_post.status_code == 201
        assert resposta_post.json() == {"recebidos": 2, "inseridos": 2, "duplicados": 0}

        listagem = cliente.get("/analises")
        assert listagem.status_code == 200
        dados = listagem.json()
        assert dados["total"] == 2
        assert {item["id_origem"] for item in dados["itens"]} == {"api_1", "api_2"}

        resumo = cliente.get("/analises/resumo")
        assert resumo.status_code == 200
        assert resumo.json() == {
            "total": 2,
            "por_sentimento": {"positivo": 1, "negativo": 1, "neutro": 0},
            "sem_data_publicacao": 0,
        }
    finally:
        app.dependency_overrides.clear()

    # Nova conexão independente confirma persistência fora da memória da requisição.
    novo_cliente = connect_to_mongodb(uri_teste, timeout_ms=1000)
    try:
        repo_novo = RepositorioAnalises(obter_colecao(novo_cliente, nome_banco_teste))
        assert repo_novo.listar_analises()["total"] == 2
        assert repo_novo.buscar_por_id_origem("app", "api_2")["sentimento"] == "negativo"
    finally:
        disconnect_from_mongodb(novo_cliente)


def test_administracao_coleta_e_pesquisa_persistem_para_dashboard_apos_recriar_contexto(
    monkeypatch, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = "senha-integracao-segura"
    monkeypatch.setenv("MONGODB_URI", uri_teste)
    monkeypatch.setenv("SENTIA_ADMIN_USUARIO", "admin")
    monkeypatch.setenv("SENTIA_ADMIN_SENHA_HASH", gerar_hash_senha(senha_admin))
    monkeypatch.setattr(administracao, "_criar_pipeline_padrao", PipelineFalso)
    administracao.obter_contexto.cache_clear()

    chamadas_x = []

    def buscar_x_falso(termo: str, quantidade: int) -> list[dict]:
        chamadas_x.append((termo, quantidade))
        return [
            {
                "id_origem": "x_1",
                "fonte": "X",
                "texto_original": f"Comentário positivo sobre {termo}",
                "data_publicacao": "2026-11-05T10:00:00Z",
            },
            {
                "id_origem": "x_2",
                "fonte": "X",
                "texto_original": f"Serviço ruim para {termo}",
                "data_publicacao": "2026-11-05T11:00:00Z",
            },
        ][:quantidade]

    try:
        ctx = administracao.obter_contexto()
        ctx._criar_pipeline = PipelineFalso
        ctx.caminho_tweetsentbr = tmp_path / "nao-existe.csv"
        ctx.buscar_x = buscar_x_falso

        cliente = TestClient(app)
        login = cliente.post("/auth/login", json={"usuario": "admin", "senha": senha_admin})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['token']}"}

        csv_conteudo = (
            "texto,fonte,data\n"
            "Gostei da vacinação no posto,csv_teste,2026-11-02\n"
        ).encode("utf-8")
        up = cliente.post(
            "/datasets",
            headers=headers,
            files={"arquivo": ("lote.csv", csv_conteudo, "text/csv")},
        )
        assert up.status_code == 201
        id_dataset = up.json()["id_dataset"]

        col_ds = cliente.post("/coletas", headers=headers, json={"fonte": id_dataset})
        assert col_ds.status_code == 202
        st_ds = cliente.get(f"/coletas/{col_ds.json()['id']}", headers=headers).json()
        assert st_ds["situacao"] == "concluida", st_ds
        assert st_ds["textos_analisados"] == 1

        col_pesq = cliente.post(
            "/coletas",
            headers=headers,
            json={
                "fonte": "pesquisa",
                "termo": "vacinação",
                "quantidade": 3,
                "complementar_com_x": True,
            },
        )
        assert col_pesq.status_code == 202
        st_pesq = cliente.get(f"/coletas/{col_pesq.json()['id']}", headers=headers).json()
        assert st_pesq["situacao"] == "concluida"
        assert st_pesq["origem"] == {"base": 1, "x": 2, "duplicatas": 0}
        assert len(chamadas_x) == 1

        # Dashboard lê diretamente da mesma coleção MongoDB.
        assert cliente.get("/analises").json()["total"] == 3
        assert cliente.get("/analises/resumo").json()["por_sentimento"] == {
            "positivo": 2,
            "negativo": 1,
            "neutro": 0,
        }

        # Simula reinício do servidor limpando contexto e repositórios em memória.
        administracao.obter_contexto.cache_clear()
        ctx_novo = administracao.ContextoAdministracao(
            Autenticador(ConfiguracaoAdmin.do_ambiente()),
            criar_pipeline=PipelineFalso,
            caminho_tweetsentbr=tmp_path / "nao-existe.csv",
            buscar_x=buscar_x_falso,
        )
        ids_base = {r["id_origem"] for r in ctx_novo.registros_da_base()}
        assert {"x_1", "x_2"}.issubset(ids_base)
        assert len(chamadas_x) == 1
        assert cliente.get("/analises").json()["total"] == 3
    finally:
        administracao.obter_contexto.cache_clear()
        app.dependency_overrides.clear()
