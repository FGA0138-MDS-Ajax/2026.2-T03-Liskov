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
    NOME_COLECAO,
    NOME_COLECAO_DATASETS,
    NOME_COLECAO_PESQUISAS,
    NOME_COLECAO_REGISTROS,
    RepositorioAnalises,
    criar_indices,
    garantir_id_origem,
    obter_colecao,
)
from src.processamento.aquisicao.csv_importer import converter_rotulo_para_sentia
from src.processamento.aquisicao.xfetch import ErroXFetch
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
            if registro.get("rotulo_padronizado") is not None:
                item["rotulo_padronizado"] = converter_rotulo_para_sentia(
                    registro["rotulo_padronizado"]
                )
            texto_tratado = registro.get("texto_tratado")
            if isinstance(texto_tratado, str) and texto_tratado.strip():
                item["texto_tratado"] = texto_tratado.strip()
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


def _configurar_ambiente_admin_mongo(monkeypatch, uri_teste: str) -> str:
    senha_admin = "senha-integracao-segura"
    monkeypatch.setenv("MONGODB_URI", uri_teste)
    monkeypatch.setenv("SENTIA_ADMIN_USUARIO", "admin")
    monkeypatch.setenv("SENTIA_ADMIN_SENHA_HASH", gerar_hash_senha(senha_admin))
    monkeypatch.setattr(administracao, "_criar_pipeline_padrao", PipelineFalso)
    administracao.obter_contexto.cache_clear()
    return senha_admin


def _login_admin(cliente: TestClient, senha_admin: str) -> dict[str, str]:
    login = cliente.post("/auth/login", json={"usuario": "admin", "senha": senha_admin})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_integracao_cenario_1_dataset_csv_persiste_e_reimportacao_nao_duplica(
    monkeypatch, client, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)
    try:
        ctx = administracao.obter_contexto()
        ctx.caminho_tweetsentbr = tmp_path / "nao-existe.csv"
        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)

        csv_bytes = (
            "id,texto,fonte,rotulo,data,campanha\n"
            "csv_1,Ótimo serviço público,portal,positivo,2026-10-10,outubro\n"
            "csv_2,Atendimento muito ruim,portal,negativo,2026-10-11,outubro\n"
        ).encode("utf-8")
        up = cliente.post(
            "/datasets",
            headers=headers,
            files={"arquivo": ("avaliacoes.csv", csv_bytes, "text/csv")},
        )
        assert up.status_code == 201
        id_dataset = up.json()["id_dataset"]

        banco = client[nome_banco_teste]
        assert banco[NOME_COLECAO_DATASETS].count_documents({"id_dataset": id_dataset}) == 1
        assert banco[NOME_COLECAO_REGISTROS].count_documents({"fonte": "portal"}) == 2
        doc_1 = banco[NOME_COLECAO_REGISTROS].find_one({"fonte": "portal", "id_origem": "csv_1"})
        assert doc_1["rotulo_original"] == "positivo"
        assert doc_1["rotulo_padronizado"] == "POS"
        assert doc_1["metadados"] == {"campanha": "outubro"}

        # Reimportação idêntica não duplica documentos em `registros`.
        reup = cliente.post(
            "/datasets",
            headers=headers,
            files={"arquivo": ("avaliacoes.csv", csv_bytes, "text/csv")},
        )
        assert reup.status_code == 201
        assert banco[NOME_COLECAO_REGISTROS].count_documents({"fonte": "portal"}) == 2

        # Novo contexto após reinício simulado recupera dataset e registros do MongoDB.
        administracao.obter_contexto.cache_clear()
        ctx_novo = administracao.ContextoAdministracao(
            Autenticador(ConfiguracaoAdmin.do_ambiente()),
            criar_pipeline=PipelineFalso,
            caminho_tweetsentbr=tmp_path / "nao-existe.csv",
        )
        assert any(f["id"] == id_dataset for f in ctx_novo.fontes())
        assert len(ctx_novo.repositorio.obter_dataset(id_dataset).registros) == 2

        # `texto_tratado` opcional também é preservado quando fornecido ao repositório/pipeline.
        with ctx_novo.repositorio_analises() as repo:
            repo.salvar_dataset(
                "tratado.csv",
                [
                    {
                        "id_origem": "tr_1",
                        "fonte": "portal",
                        "texto_original": "Texto ótimo!",
                        "texto_tratado": "texto otimo",
                    }
                ],
            )
            carregado = repo.obter_dataset(
                next(d["id_dataset"] for d in repo.listar_datasets() if d["nome_arquivo"] == "tratado.csv")
            )
            assert carregado["registros"][0]["texto_tratado"] == "texto otimo"
    finally:
        administracao.obter_contexto.cache_clear()


def test_integracao_cenario_2_tweetsentbr_persiste_e_sobrevive_sem_arquivo_local(
    monkeypatch, client, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)
    caminho_corpus = tmp_path / "tweetsentbr.csv"
    caminho_corpus.write_text(
        "id,texto,fonte,rotulo\n"
        "ts_1,Adorei a campanha,TweetSentBR,Positivo\n"
        "ts_2,Fila muito ruim hoje,TweetSentBR,Negativo\n",
        encoding="utf-8",
    )
    try:
        ctx = administracao.obter_contexto()
        ctx.caminho_tweetsentbr = caminho_corpus
        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)

        fontes = cliente.get("/coletas/fontes", headers=headers).json()["fontes"]
        assert {"id": "tweetsentbr", "nome": "TweetSentBR"} in fontes

        banco = client[nome_banco_teste]
        assert banco[NOME_COLECAO_DATASETS].count_documents({"id_dataset": "tweetsentbr"}) == 1
        assert banco[NOME_COLECAO_REGISTROS].count_documents({"fonte": "TweetSentBR"}) == 2

        # Remove o arquivo CSV local e recria o contexto sem o arquivo físico.
        caminho_corpus.unlink()
        administracao.obter_contexto.cache_clear()
        ctx_reiniciado = administracao.ContextoAdministracao(
            Autenticador(ConfiguracaoAdmin.do_ambiente()),
            criar_pipeline=PipelineFalso,
            caminho_tweetsentbr=tmp_path / "arquivo-inexistente.csv",
        )
        assert {"id": "tweetsentbr", "nome": "TweetSentBR"} in ctx_reiniciado.fontes()
        assert {r["id_origem"] for r in ctx_reiniciado.registros_da_base()} >= {"ts_1", "ts_2"}
        assert len(ctx_reiniciado.registros_da_fonte("tweetsentbr")) == 2
    finally:
        administracao.obter_contexto.cache_clear()


def test_integracao_cenario_3_aquisicao_xfetch_persiste_em_registros_datasets_e_analises(
    monkeypatch, client, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)

    def buscar_x_falso(_termo: str, quantidade: int) -> list[dict]:
        return [
            {
                "id_origem": "tw_inf_1",
                "fonte": "X",
                "texto_original": "Preço alto da inflação no mercado",
                "data_publicacao": "2026-11-05T10:00:00Z",
                "metadados": {"provedor": "XFetch", "lang": "pt", "like_count": 7},
            },
            {
                "id_origem": "tw_inf_2",
                "fonte": "X",
                "texto_original": "Inflação pesa demais no bolso",
                "data_publicacao": "2026-11-05T11:00:00Z",
                "metadados": {"provedor": "XFetch", "lang": "pt", "retweet_count": 2},
            },
        ][:quantidade]

    try:
        ctx = administracao.obter_contexto()
        ctx.caminho_tweetsentbr = tmp_path / "nao-existe.csv"
        ctx.buscar_x = buscar_x_falso
        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)

        res = cliente.post(
            "/coletas",
            headers=headers,
            json={
                "fonte": "pesquisa",
                "termo": "inflação",
                "quantidade": 2,
                "complementar_com_x": True,
            },
        )
        assert res.status_code == 202
        status_col = cliente.get(f"/coletas/{res.json()['id']}", headers=headers).json()
        assert status_col["situacao"] == "concluida"

        banco = client[nome_banco_teste]
        assert banco[NOME_COLECAO_REGISTROS].count_documents({"fonte": "X"}) == 2
        assert (
            banco[NOME_COLECAO_DATASETS].count_documents({"tipo": "pesquisa_x"}) == 1
        )
        assert banco[NOME_COLECAO].count_documents({"fonte": "X"}) == 2
        salvo = banco[NOME_COLECAO_REGISTROS].find_one({"id_origem": "tw_inf_1"})
        assert salvo["metadados"]["provedor"] == "XFetch"
    finally:
        administracao.obter_contexto.cache_clear()


def test_integracao_cenario_4_cache_pesquisa_hibrida_e_forcar_atualizacao(
    monkeypatch, client, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)
    chamadas_x: list[tuple[str, int]] = []

    def buscar_x_spy(termo: str, quantidade: int) -> list[dict]:
        chamadas_x.append((termo, quantidade))
        indice = len(chamadas_x)
        if termo.casefold() in {"vacinação", "vacinacao"} and indice == 1:
            return [
                {
                    "id_origem": "vx_1",
                    "fonte": "X",
                    "texto_original": "Campanha de vacinação excelente",
                },
                {
                    "id_origem": "vx_2",
                    "fonte": "X",
                    "texto_original": "Vacinação no posto foi ruim",
                },
            ]
        return [
            {
                "id_origem": f"ext_{indice}",
                "fonte": "X",
                "texto_original": f"Novo registro sobre {termo}",
            }
        ]

    try:
        ctx = administracao.obter_contexto()
        ctx.caminho_tweetsentbr = tmp_path / "nao-existe.csv"
        ctx.buscar_x = buscar_x_spy
        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)

        # 1) Busca inicial com meta=5, mas X devolve apenas 2 -> esgotado_na_origem=True.
        r1 = cliente.post(
            "/coletas",
            headers=headers,
            json={
                "fonte": "pesquisa",
                "termo": "Vacinação",
                "quantidade": 5,
                "complementar_com_x": True,
            },
        )
        assert r1.status_code == 202
        st1 = cliente.get(f"/coletas/{r1.json()['id']}", headers=headers).json()
        assert st1["situacao"] == "concluida"
        assert len(chamadas_x) == 1

        banco = client[nome_banco_teste]
        doc_cache = banco[NOME_COLECAO_PESQUISAS].find_one({"consulta_normalizada": "vacinacao"})
        assert doc_cache is not None
        assert doc_cache["esgotado_na_origem"] is True

        # 2) Recria contexto e repete com consulta equivalente sem acento e caixa alta.
        administracao.obter_contexto.cache_clear()
        ctx2 = administracao.ContextoAdministracao(
            Autenticador(ConfiguracaoAdmin.do_ambiente()),
            criar_pipeline=PipelineFalso,
            caminho_tweetsentbr=tmp_path / "nao-existe.csv",
            buscar_x=buscar_x_spy,
        )
        app.dependency_overrides[administracao.obter_contexto] = lambda: ctx2
        headers2 = _login_admin(cliente, senha_admin)
        r2 = cliente.post(
            "/coletas",
            headers=headers2,
            json={
                "fonte": "pesquisa",
                "termo": "  VACINACAO  ",
                "quantidade": 5,
                "complementar_com_x": True,
            },
        )
        st2 = cliente.get(f"/coletas/{r2.json()['id']}", headers=headers2).json()
        assert st2["situacao"] == "concluida"
        assert len(chamadas_x) == 1, "consulta equivalente deveria reutilizar o cache sem ir ao X"

        # 3) Substring parcial incompatível ("vac") não reutiliza cache de "vacinacao".
        r3 = cliente.post(
            "/coletas",
            headers=headers2,
            json={
                "fonte": "pesquisa",
                "termo": "vac",
                "quantidade": 2,
                "complementar_com_x": True,
            },
        )
        assert cliente.get(f"/coletas/{r3.json()['id']}", headers=headers2).json()["situacao"] == "concluida"
        assert len(chamadas_x) == 2

        # 4) forcar_atualizacao=True consulta o X novamente sem apagar histórico anterior.
        r4 = cliente.post(
            "/coletas",
            headers=headers2,
            json={
                "fonte": "pesquisa",
                "termo": "vacinacao",
                "quantidade": 5,
                "complementar_com_x": True,
                "forcar_atualizacao": True,
            },
        )
        st4 = cliente.get(f"/coletas/{r4.json()['id']}", headers=headers2).json()
        assert st4["situacao"] == "concluida"
        assert len(chamadas_x) == 3
        assert banco[NOME_COLECAO_REGISTROS].count_documents({"id_origem": {"$in": ["vx_1", "vx_2"]}}) == 2
        assert banco[NOME_COLECAO_REGISTROS].count_documents({"id_origem": "ext_3"}) == 1
    finally:
        app.dependency_overrides.clear()
        administracao.obter_contexto.cache_clear()


def test_integracao_cenario_5_deduplicacao_e_fallback_id_origem(client, nome_banco_teste):
    col = obter_colecao(client, nome_banco_teste)
    repo = RepositorioAnalises(col)

    sem_id_a = {"fonte": "X", "texto_original": "Texto repetido sem id", "data_publicacao": "2026-11-01T10:00:00Z"}
    sem_id_a_dup = {"fonte": "X", "id_origem": "   ", "texto_original": "Texto repetido sem id", "data_publicacao": "2026-11-01T10:00:00Z"}
    sem_id_b = {"fonte": "X", "texto_original": "Outro texto sem id"}

    assert garantir_id_origem(sem_id_a).startswith("auto_")
    assert garantir_id_origem(sem_id_a) == garantir_id_origem(sem_id_a_dup)

    repo.salvar_registros([sem_id_a, sem_id_a_dup, sem_id_b], id_dataset="ds_a", origem_coleta="xfetch")
    # Reimportação repetida envolvendo registros já existentes em X/CSV não duplica documentos.
    repo.salvar_registros(
        [
            {"id_origem": garantir_id_origem(sem_id_a), "fonte": "X", "texto_original": "Texto repetido sem id"},
            {"id_origem": "fixo_1", "fonte": "csv_a", "texto_original": "Texto fixo"},
        ],
        id_dataset="ds_b",
        origem_coleta="csv",
    )
    repo.salvar_registros(
        [{"id_origem": "fixo_1", "fonte": "csv_a", "texto_original": "Texto fixo"}],
        id_dataset="ds_c",
        origem_coleta="csv",
    )

    banco = client[nome_banco_teste]
    assert banco[NOME_COLECAO_REGISTROS].count_documents({}) == 3
    base = repo.listar_registros_base()
    assert len(base) == 3


def test_integracao_cenario_6_recuperacao_completa_apos_reinicio(
    monkeypatch, client, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)
    corpus_csv = tmp_path / "tweetsentbr.csv"
    corpus_csv.write_text("id,texto,fonte\nts_rec_1,Texto base do corpus sobre saude,TweetSentBR\n", encoding="utf-8")

    chamadas_x: list[tuple[str, int]] = []

    def buscar_x(termo: str, qtd: int) -> list[dict]:
        chamadas_x.append((termo, qtd))
        return [{"id_origem": "rx_1", "fonte": "X", "texto_original": f"Post sobre {termo}"}]

    try:
        ctx = administracao.obter_contexto()
        ctx.caminho_tweetsentbr = corpus_csv
        ctx.buscar_x = buscar_x
        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)

        csv_up = "id,texto,fonte\nc_1,Atendimento hospitalar bom,portal\n".encode("utf-8")
        id_ds = cliente.post(
            "/datasets",
            headers=headers,
            files={"arquivo": ("saude.csv", csv_up, "text/csv")},
        ).json()["id_dataset"]
        assert cliente.post("/coletas", headers=headers, json={"fonte": id_ds}).status_code == 202
        assert cliente.post("/coletas", headers=headers, json={"fonte": "tweetsentbr"}).status_code == 202
        assert (
            cliente.post(
                "/coletas",
                headers=headers,
                json={"fonte": "pesquisa", "termo": "economia", "quantidade": 3, "complementar_com_x": True},
            ).status_code
            == 202
        )
        assert len(chamadas_x) == 1

        # Remove corpus físico e reinicia completamente contexto/cliente.
        corpus_csv.unlink()
        administracao.obter_contexto.cache_clear()
        ctx_novo = administracao.ContextoAdministracao(
            Autenticador(ConfiguracaoAdmin.do_ambiente()),
            criar_pipeline=PipelineFalso,
            caminho_tweetsentbr=tmp_path / "nao-existe.csv",
            buscar_x=buscar_x,
        )
        app.dependency_overrides[administracao.obter_contexto] = lambda: ctx_novo
        headers_reinicio = _login_admin(cliente, senha_admin)

        fontes = cliente.get("/coletas/fontes", headers=headers_reinicio).json()["fontes"]
        ids_fontes = {f["id"] for f in fontes}
        assert "tweetsentbr" in ids_fontes
        assert id_ds in ids_fontes

        # Pesquisa equivalente usa cache sem nova chamada ao X.
        rep = cliente.post(
            "/coletas",
            headers=headers_reinicio,
            json={"fonte": "pesquisa", "termo": "Economia", "quantidade": 3, "complementar_com_x": True},
        )
        assert (
            cliente.get(f"/coletas/{rep.json()['id']}", headers=headers_reinicio).json()["situacao"]
            == "concluida"
        )
        assert len(chamadas_x) == 1

        # Dashboard reflete todas as análises persistidas.
        assert cliente.get("/analises").json()["total"] == 3
        assert cliente.get("/analises/resumo").json()["total"] == 3
    finally:
        app.dependency_overrides.clear()
        administracao.obter_contexto.cache_clear()


def test_integracao_cenario_7_pula_reclassificacao_para_analises_existentes(
    monkeypatch, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)
    lotes_enviados: list[list[str]] = []

    class PipelineSpy(PipelineFalso):
        def processar_registros(self, registros):
            lotes_enviados.append([r["id_origem"] for r in registros])
            return super().processar_registros(registros)

    monkeypatch.setattr(administracao, "_criar_pipeline_padrao", PipelineSpy)
    administracao.obter_contexto.cache_clear()
    try:
        ctx = administracao.obter_contexto()
        ctx._criar_pipeline = PipelineSpy
        ctx.caminho_tweetsentbr = tmp_path / "nao-existe.csv"

        # Salva previamente 2 análises na coleção `analises`.
        with ctx.repositorio_analises() as repo:
            repo.salvar_analises([
                criar_documento("id_1", sentimento="positivo", fonte="crm"),
                criar_documento("id_2", sentimento="negativo", fonte="crm"),
            ])

        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)
        csv_bytes = (
            "id,texto,fonte\n"
            "id_1,texto id_1,crm\n"
            "id_2,texto id_2,crm\n"
            "id_3,Novo comentário ruim,crm\n"
        ).encode("utf-8")
        id_ds = cliente.post(
            "/datasets",
            headers=headers,
            files={"arquivo": ("misto.csv", csv_bytes, "text/csv")},
        ).json()["id_dataset"]

        col = cliente.post("/coletas", headers=headers, json={"fonte": id_ds}).json()["id"]
        st = cliente.get(f"/coletas/{col}", headers=headers).json()
        assert st["situacao"] == "concluida"
        assert st["textos_analisados"] == 3
        assert lotes_enviados == [["id_3"]], "apenas o registro inédito deve ir para inferência"

        # Segunda execução sobre os mesmos dados não aciona o pipeline novamente.
        col2 = cliente.post("/coletas", headers=headers, json={"fonte": id_ds}).json()["id"]
        st2 = cliente.get(f"/coletas/{col2}", headers=headers).json()
        assert st2["situacao"] == "concluida"
        assert st2["textos_analisados"] == 3
        assert lotes_enviados == [["id_3"]]
    finally:
        administracao.obter_contexto.cache_clear()


def test_integracao_cenario_8_dashboard_com_proveniencia_e_texto_tratado(
    monkeypatch, client, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)
    corpus_csv = tmp_path / "tweetsentbr.csv"
    corpus_csv.write_text("id,texto,fonte,rotulo\nts_dash_1,Muito bom o atendimento,TweetSentBR,Positivo\n", encoding="utf-8")

    try:
        ctx = administracao.obter_contexto()
        ctx.caminho_tweetsentbr = corpus_csv
        ctx.buscar_x = lambda termo, _qtd: [
            {
                "id_origem": "x_dash_1",
                "fonte": "X",
                "texto_original": f"Comentário ruim sobre {termo}",
                "data_publicacao": "2026-11-04T12:00:00Z",
                "metadados": {"provedor": "XFetch", "lang": "pt"},
            }
        ]
        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)

        csv_bytes = (
            "id,texto,fonte,rotulo,data,canal\n"
            "csv_dash_1,Entrega excelente,loja,5,2026-11-02,web\n"
        ).encode("utf-8")
        id_ds = cliente.post(
            "/datasets",
            headers=headers,
            files={"arquivo": ("dash.csv", csv_bytes, "text/csv")},
        ).json()["id_dataset"]
        cliente.post("/coletas", headers=headers, json={"fonte": id_ds})
        cliente.post("/coletas", headers=headers, json={"fonte": "tweetsentbr"})
        cliente.post(
            "/coletas",
            headers=headers,
            json={"fonte": "pesquisa", "termo": "transporte", "quantidade": 1, "complementar_com_x": True},
        )

        # Valida também preservação de `texto_tratado` no PipelineClassificacao + MongoDB.
        pipeline_tratado = PipelineFalso()
        with ctx.repositorio_analises() as repo:
            docs_tratados = pipeline_tratado.processar_registros([
                {
                    "id_origem": "bl_1",
                    "fonte": "baseline",
                    "texto_original": "O produto cumpriu o esperado!",
                    "texto_tratado": "produto cumpriu esperado",
                    "data_publicacao": "2026-11-03T08:00:00Z",
                }
            ])
            repo.salvar_analises(docs_tratados)

        doc_baseline = client[nome_banco_teste][NOME_COLECAO].find_one({"id_origem": "bl_1"})
        assert doc_baseline["texto_tratado"] == "produto cumpriu esperado"

        itens = cliente.get("/analises").json()["itens"]
        por_id = {item["id_origem"]: item for item in itens}
        assert por_id["csv_dash_1"]["rotulo_original"] == "5"
        assert por_id["csv_dash_1"]["rotulo_padronizado"] == "positivo"
        assert por_id["csv_dash_1"]["metadados"] == {"canal": "web"}
        assert por_id["ts_dash_1"]["fonte"] == "TweetSentBR"
        assert por_id["x_dash_1"]["metadados"] == {"provedor": "XFetch", "lang": "pt"}

        resumo_periodo = cliente.get(
            "/analises/resumo", params={"inicio": "2026-11-01", "fim": "2026-11-10"}
        ).json()
        assert resumo_periodo["total"] == 3
        assert resumo_periodo["sem_data_publicacao"] == 1  # ts_dash_1 do TweetSentBR
    finally:
        administracao.obter_contexto.cache_clear()


def test_integracao_cenario_9_falha_xfetch_nao_grava_cache_indevido(
    monkeypatch, client, tmp_path: Path, uri_mongodb_teste, nome_banco_teste
):
    uri_teste = uri_com_banco(uri_mongodb_teste, nome_banco_teste)
    senha_admin = _configurar_ambiente_admin_mongo(monkeypatch, uri_teste)
    chamadas_x: list[str] = []

    def x_que_falha(termo: str, _qtd: int) -> list[dict]:
        chamadas_x.append(f"falha:{termo}")
        raise ErroXFetch("Falha na comunicação com o XFetch (HTTP 402).")

    def x_saudavel(termo: str, _qtd: int) -> list[dict]:
        chamadas_x.append(f"ok:{termo}")
        return [{"id_origem": "recup_1", "fonte": "X", "texto_original": f"Texto sobre {termo}"}]

    try:
        ctx = administracao.obter_contexto()
        ctx.caminho_tweetsentbr = tmp_path / "nao-existe.csv"
        ctx.buscar_x = x_que_falha
        cliente = TestClient(app)
        headers = _login_admin(cliente, senha_admin)

        r_falha = cliente.post(
            "/coletas",
            headers=headers,
            json={"fonte": "pesquisa", "termo": "energia", "quantidade": 3, "complementar_com_x": True},
        )
        st_falha = cliente.get(f"/coletas/{r_falha.json()['id']}", headers=headers).json()
        assert st_falha["situacao"] == "falhou"
        assert "HTTP 402" in st_falha["mensagem"]

        banco = client[nome_banco_teste]
        assert banco[NOME_COLECAO_PESQUISAS].count_documents({"consulta_normalizada": "energia"}) == 0

        # Nova tentativa posterior volta a chamar XFetch normalmente e grava o cache válido.
        ctx.buscar_x = x_saudavel
        r_ok = cliente.post(
            "/coletas",
            headers=headers,
            json={"fonte": "pesquisa", "termo": "energia", "quantidade": 3, "complementar_com_x": True},
        )
        st_ok = cliente.get(f"/coletas/{r_ok.json()['id']}", headers=headers).json()
        assert st_ok["situacao"] == "concluida"
        assert chamadas_x == ["falha:energia", "ok:energia"]
        assert banco[NOME_COLECAO_PESQUISAS].count_documents({"consulta_normalizada": "energia"}) == 1
    finally:
        administracao.obter_contexto.cache_clear()
