"""Integração da persistência canônica e da API contra MongoDB real (mongo:7 na CI)."""

import os
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.dados.database import ErroConexaoMongoDB, connect_to_mongodb, disconnect_from_mongodb
from src.dados.repositorio import (
    ErroAnaliseInvalida,
    RepositorioAnalises,
    criar_indices,
    obter_colecao,
)
from src.servico.administracao import ContextoAdministracao, executar_coleta
from src.servico.autenticacao import Autenticador
from src.servico.dependencias import obter_pipeline
from src.servico.main import app


@pytest.fixture
def mongo_teste():
    uri = os.getenv("MONGODB_URI_TESTE", "mongodb://127.0.0.1:27017")
    try:
        cliente = connect_to_mongodb(uri, timeout_ms=1000)
    except ErroConexaoMongoDB:
        if os.getenv("CI"):
            pytest.fail("MongoDB de teste indisponível no CI.")
        pytest.skip("MongoDB de teste indisponível; use o serviço mongo:7.")
    nome_banco = f"sentia_teste_api_{uuid4().hex}"
    colecao = obter_colecao(cliente, nome_banco)
    criar_indices(colecao)
    yield uri, nome_banco, cliente, colecao
    cliente.drop_database(nome_banco)
    disconnect_from_mongodb(cliente)


def documento(id_origem="a1", **alteracoes):
    resultado = {
        "id_origem": id_origem,
        "fonte": "integracao",
        "texto_original": "Texto de integração.",
        "sentimento": "positivo",
        "modelo": {"nome": "modelo-de-teste"},
        "data_processamento": datetime(2026, 11, 14, tzinfo=UTC),
    }
    resultado.update(alteracoes)
    return resultado


def uri_do_banco(uri: str, nome_banco: str) -> str:
    return urlsplit(uri)._replace(path=f"/{nome_banco}").geturl()


def test_repositorio_api_grava_lista_resume_e_trata_vazio_e_invalidos(mongo_teste):
    _, _, _, colecao = mongo_teste
    repositorio = RepositorioAnalises(colecao)

    assert repositorio.listar_analises() == {
        "itens": [], "pagina": 1, "tamanho": 20, "total": 0,
    }
    assert repositorio.resumir_analises() == {
        "total": 0,
        "por_sentimento": {"positivo": 0, "negativo": 0, "neutro": 0},
        "sem_data_publicacao": 0,
    }
    with pytest.raises(ErroAnaliseInvalida):
        repositorio.salvar_analises([documento(sentimento="desconhecido")])
    assert colecao.count_documents({}) == 0

    assert repositorio.salvar_analises([documento(), documento("a2", sentimento="neutro")]) == {
        "inseridos": 2, "duplicados": 0,
    }
    pagina = repositorio.listar_analises()
    resumo = repositorio.resumir_analises()
    assert pagina["total"] == 2
    assert {item["id_origem"] for item in pagina["itens"]} == {"a1", "a2"}
    assert resumo == {
        "total": 2,
        "por_sentimento": {"positivo": 1, "negativo": 0, "neutro": 1},
        "sem_data_publicacao": 0,
    }


def test_documento_sem_data_publicacao_e_legivel_depois_de_nova_conexao(mongo_teste):
    uri, nome_banco, _, colecao = mongo_teste
    RepositorioAnalises(colecao).salvar_analises([documento()])

    novo_cliente = connect_to_mongodb(uri, timeout_ms=1000)
    try:
        repositorio = RepositorioAnalises(obter_colecao(novo_cliente, nome_banco))
        resposta = repositorio.listar_analises()
        resumo = repositorio.resumir_analises()
        assert resposta["total"] == 1
        assert "data_publicacao" not in resposta["itens"][0]
        assert resumo["total"] == 1
    finally:
        disconnect_from_mongodb(novo_cliente)


def test_post_da_api_persiste_no_mongo_e_sobrevive_a_nova_conexao(mongo_teste, monkeypatch):
    uri, nome_banco, _, _ = mongo_teste
    monkeypatch.setenv("MONGODB_URI", uri_do_banco(uri, nome_banco))

    class PipelineFalso:
        def processar_registros(self, registros):
            return [documento(registros[0]["id_origem"], texto_original=registros[0]["texto_original"])]

    app.dependency_overrides[obter_pipeline] = PipelineFalso
    try:
        with TestClient(app) as cliente:
            resposta = cliente.post(
                "/analises",
                json={"registros": [
                    {"id_origem": "api-1", "fonte": "teste", "texto_original": "Persistente."}
                ]},
            )
    finally:
        app.dependency_overrides.clear()

    assert resposta.status_code == 201
    assert resposta.json() == {"recebidos": 1, "inseridos": 1, "duplicados": 0}
    novo_cliente = connect_to_mongodb(uri, timeout_ms=1000)
    try:
        pagina = RepositorioAnalises(obter_colecao(novo_cliente, nome_banco)).listar_analises()
    finally:
        disconnect_from_mongodb(novo_cliente)
    assert pagina["total"] == 1
    assert pagina["itens"][0]["id_origem"] == "api-1"


def test_coleta_administrativa_alimenta_consulta_da_api(mongo_teste, monkeypatch):
    uri, nome_banco, _, _ = mongo_teste
    monkeypatch.setenv("MONGODB_URI", uri_do_banco(uri, nome_banco))

    class PipelineFalso:
        def processar_registros(self, registros):
            return [
                {
                    **registro,
                    "sentimento": "negativo",
                    "modelo": {"nome": "modelo-integracao"},
                    "data_processamento": datetime.now(UTC),
                }
                for registro in registros
            ]

    contexto = ContextoAdministracao(
        Autenticador(None),
        criar_pipeline=PipelineFalso,
    )
    dataset = contexto.repositorio.adicionar_dataset(
        "amostra.csv", [{"id_origem": "admin-1", "fonte": "amostra", "texto_original": "Ruim."}]
    )
    coleta = contexto.repositorio.criar_coleta(dataset.id)
    executar_coleta(contexto, coleta.id)

    with TestClient(app) as cliente:
        resposta = cliente.get("/analises", params={"sentimento": "negativo"})
        resumo = cliente.get("/analises/resumo")

    assert resposta.status_code == resumo.status_code == 200
    assert resposta.json()["total"] == 1
    assert resposta.json()["itens"][0]["id_origem"] == "admin-1"
    assert resumo.json()["por_sentimento"]["negativo"] == 1
    assert contexto.repositorio.obter_coleta(coleta.id).situacao == "concluida"
