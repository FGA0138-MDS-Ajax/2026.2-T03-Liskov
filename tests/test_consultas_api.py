"""Contrato HTTP e consultas com coleção simulada; não valida MongoDB real."""

from collections import Counter
from datetime import UTC, date, datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.errors import OperationFailure

from src.apresentacao.contrato import FiltrosAnalises
from src.apresentacao.fontes.api import FonteApi
from src.dados.repositorio import listar_analises, resumir_analises
from src.servico.dependencias import obter_colecao_analises
from src.servico.main import app


@pytest.fixture
def documentos():
    base = {
        "fonte": "teste", "texto_original": "Avaliação", "modelo": {"nome": "modelo-teste"},
        "data_processamento": datetime(2026, 11, 10, 12),
    }
    publicacoes = [
        datetime(2026, 10, 1, tzinfo=UTC),
        datetime(2026, 10, 31, 23, 59, 59, 999000, tzinfo=UTC),
        datetime(2026, 11, 1, tzinfo=UTC),
        None, None,
        datetime(2026, 9, 30, 23, 59, 59, 999000, tzinfo=UTC),
    ]
    sentimentos = ["positivo", "negativo", "neutro", "positivo", "negativo", "positivo"]
    docs = [dict(base, _id=ObjectId(), id_origem=str(i), sentimento=s, data_publicacao=d)
            for i, (s, d) in enumerate(zip(sentimentos, publicacoes))]
    del docs[3]["data_publicacao"]
    # Ordem de armazenamento deliberadamente diferente da ordem pública.
    return list(reversed(docs))


@pytest.fixture
def colecao(monkeypatch, documentos):
    """Simula só as operações usadas; as expressões enviadas são verificadas abaixo."""
    def selecionar(filtro):
        def atende(doc):
            for campo, esperado in filtro.items():
                valor = doc.get(campo)
                if isinstance(esperado, dict):
                    if valor is None:
                        return False
                    if "$gte" in esperado and valor < esperado["$gte"]:
                        return False
                    if "$lte" in esperado and valor > esperado["$lte"]:
                        return False
                elif valor != esperado:
                    return False
            return True
        return [d for d in documentos if atende(d)]

    def encontrar(filtro, projecao):
        dados = selecionar(filtro)
        cursor = MagicMock()

        def ordenar(chaves):
            for campo, sentido in reversed(chaves):
                dados.sort(key=lambda d: d[campo], reverse=sentido == -1)
            return cursor

        def pular(quantidade):
            del dados[:quantidade]
            return cursor

        def limitar(quantidade):
            del dados[quantidade:]
            return cursor

        cursor.sort.side_effect = ordenar
        cursor.skip.side_effect = pular
        cursor.limit.side_effect = limitar
        # Mantém _id de propósito: também verifica a proteção no modelo de resposta.
        cursor.__iter__.side_effect = lambda: iter(dados)
        return cursor

    def agregar(etapas):
        contagens = Counter(d["sentimento"] for d in selecionar(etapas[0]["$match"]))
        return [{"_id": classe, "total": n} for classe, n in contagens.items()]

    banco = Mock()
    banco.find.side_effect = encontrar
    banco.count_documents.side_effect = lambda filtro: len(selecionar(filtro))
    banco.aggregate.side_effect = agregar
    monkeypatch.setitem(app.dependency_overrides, obter_colecao_analises, lambda: banco)
    return banco


@pytest.fixture
def cliente(colecao):
    return TestClient(app)


def test_colecao_vazia(cliente, documentos):
    documentos.clear()
    assert cliente.get("/analises").json() == {
        "itens": [], "pagina": 1, "tamanho": 20, "total": 0,
    }
    resposta = cliente.get("/analises/resumo")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "total": 0, "por_sentimento": {"positivo": 0, "negativo": 0, "neutro": 0},
        "sem_data_publicacao": 0,
    }


def test_paginacao_estavel_serializacao_e_desempate(cliente, documentos):
    ids = []
    for pagina in (1, 2, 3, 4):
        resposta = cliente.get("/analises", params={"pagina": pagina, "tamanho": 2})
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert (corpo["pagina"], corpo["tamanho"], corpo["total"]) == (pagina, 2, 6)
        ids.extend(d["id_origem"] for d in corpo["itens"])
        for doc in corpo["itens"]:
            assert "_id" not in doc
            assert datetime.fromisoformat(doc["data_processamento"]).utcoffset() == timedelta(0)
            if doc["data_publicacao"] is not None:
                assert datetime.fromisoformat(doc["data_publicacao"]).tzinfo is not None
    assert ids == ["0", "1", "2", "3", "4", "5"]
    documentos.reverse()
    assert [d["id_origem"] for d in cliente.get("/analises").json()["itens"]] == ids
    documentos[0]["fonte"] = "aaa"
    documentos[-1]["data_processamento"] += timedelta(days=1)
    esperados = [documentos[-1]["id_origem"], documentos[0]["id_origem"]]
    assert [d["id_origem"] for d in cliente.get("/analises").json()["itens"][:2]] == esperados


@pytest.mark.parametrize("parametros,ids,sem_data", [
    ({}, ["0", "1", "2", "3", "4", "5"], 0),
    ({"sentimento": "positivo"}, ["0", "3", "5"], 0),
    ({"sentimento": "negativo"}, ["1", "4"], 0),
    ({"sentimento": "neutro"}, ["2"], 0),
    ({"inicio": "2026-10-01"}, ["0", "1", "2"], 2),
    ({"fim": "2026-10-31"}, ["0", "1", "5"], 2),
    ({"inicio": "2026-10-01", "fim": "2026-10-31"}, ["0", "1"], 2),
    ({"inicio": "2026-10-01", "fim": "2026-10-01"}, ["0"], 2),
    ({"inicio": "2026-10-01", "fim": "2026-10-31", "sentimento": "positivo"}, ["0"], 1),
    ({"inicio": "2026-12-01", "sentimento": "positivo"}, [], 1),
    ({"fim": "9999-12-31"}, ["0", "1", "2", "5"], 2),
])
def test_filtros_e_resumo_coerentes(cliente, parametros, ids, sem_data):
    resposta = cliente.get("/analises", params=parametros)
    resumo = cliente.get("/analises/resumo", params=parametros)
    assert resposta.status_code == resumo.status_code == 200
    assert [d["id_origem"] for d in resposta.json()["itens"]] == ids
    corpo = resumo.json()
    assert corpo["total"] == resposta.json()["total"] == len(ids)
    contagens = Counter(d["sentimento"] for d in resposta.json()["itens"])
    assert corpo["por_sentimento"] == {s: contagens[s] for s in ("positivo", "negativo", "neutro")}
    assert corpo["sem_data_publicacao"] == sem_data
    paginada = cliente.get("/analises", params={**parametros, "tamanho": 1, "pagina": 2})
    assert paginada.json()["total"] == len(ids)
    assert len(paginada.json()["itens"]) == min(1, max(0, len(ids) - 1))


@pytest.mark.parametrize("parametros", [
    {"inicio": "2026-11-01", "fim": "2026-10-01"}, {"inicio": "2026-02-30"},
    {"fim": "2026-13-01"}, {"inicio": "2026-1-01"}, {"inicio": "1790812800"},
    {"fim": "2026-10-31T00:00:00Z"}, {"sentimento": "POS"},
    {"sentimento": ""}, {"inicio": ""},
])
@pytest.mark.parametrize("rota", ["/analises", "/analises/resumo"])
def test_filtros_invalidos_retorna_422(cliente, rota, parametros, colecao):
    assert cliente.get(rota, params=parametros).status_code == 422
    colecao.find.assert_not_called()
    colecao.aggregate.assert_not_called()


@pytest.mark.parametrize("parametros", [
    {"pagina": 0}, {"pagina": -1}, {"pagina": "true"}, {"pagina": "1.5"},
    {"tamanho": 0}, {"tamanho": 101}, {"tamanho": "2.5"},
    {"pagina": "1.0"}, {"tamanho": "2e1"},
])
def test_paginacao_invalida(cliente, parametros):
    assert cliente.get("/analises", params=parametros).status_code == 422


def test_datas_mongodb_em_utc_e_offset_normalizado(cliente, documentos):
    documentos[0]["data_publicacao"] = datetime(2026, 10, 1, 3, tzinfo=timezone(timedelta(hours=3)))
    resposta = cliente.get("/analises").json()
    doc = next(d for d in resposta["itens"] if d["id_origem"] == documentos[0]["id_origem"])
    assert doc["data_publicacao"] == "2026-10-01T00:00:00Z"
    documentos[0]["data_publicacao"] = datetime(2026, 10, 1)
    resposta = cliente.get("/analises").json()
    doc = next(d for d in resposta["itens"] if d["id_origem"] == documentos[0]["id_origem"])
    assert doc["data_publicacao"] == "2026-10-01T00:00:00Z"


def test_respostas_aceitas_pelo_cliente_fonte_api(cliente):
    fonte = FonteApi("http://testserver", sessao=cliente)
    filtros = FiltrosAnalises(inicio=date(2026, 10, 1), fim=date(2026, 10, 31))
    pagina = fonte.listar(filtros, tamanho=1)
    resumo = fonte.resumir(filtros)
    assert pagina.total == resumo.total == 2
    assert pagina.itens[0].data_processamento.tzinfo == UTC
    assert resumo.sem_data_publicacao == 2


@pytest.mark.parametrize("rota,operacao", [
    ("/analises", "find"), ("/analises", "count_documents"),
    ("/analises/resumo", "aggregate"), ("/analises/resumo?inicio=2026-10-01", "count_documents"),
])
def test_falha_de_consulta_sanitizada(cliente, colecao, rota, operacao):
    getattr(colecao, operacao).side_effect = OperationFailure("mongodb://admin:SEGREDO@servidor")
    resposta = cliente.get(rota)
    assert resposta.status_code == 503
    assert resposta.json() == {"detail": "Banco de dados indisponível."}


def test_falha_na_iteracao_do_cursor_e_sanitizada(cliente, colecao):
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.side_effect = OperationFailure("mongodb://admin:SEGREDO@servidor")
    colecao.find.side_effect = None
    colecao.find.return_value = cursor
    resposta = cliente.get("/analises")
    assert resposta.status_code == 503
    assert resposta.json() == {"detail": "Banco de dados indisponível."}


def test_repositorio_envia_filtros_paginacao_e_agregacao_ao_banco():
    banco = MagicMock()
    banco.count_documents.return_value = 3
    banco.aggregate.return_value = [{"_id": "positivo", "total": 2}]
    filtros = dict(inicio=date(2026, 10, 1), fim=date(2026, 10, 31), sentimento="positivo")
    consulta = {"sentimento": "positivo", "data_publicacao": {
        "$gte": datetime(2026, 10, 1, tzinfo=UTC),
        "$lte": datetime(2026, 10, 31, 23, 59, 59, 999999, tzinfo=UTC),
    }}
    listar_analises(banco, **filtros, pagina=3, tamanho=2)
    banco.find.assert_called_once_with(consulta, {"_id": 0})
    banco.count_documents.assert_called_once_with(consulta)
    cursor = banco.find.return_value
    cursor.sort.assert_called_once_with([("data_processamento", -1), ("fonte", 1), ("id_origem", 1)])
    cursor.sort.return_value.skip.assert_called_once_with(4)
    cursor.sort.return_value.skip.return_value.limit.assert_called_once_with(2)
    resumo = resumir_analises(banco, **filtros)
    banco.aggregate.assert_called_once_with([
        {"$match": consulta}, {"$group": {"_id": "$sentimento", "total": {"$sum": 1}}},
    ])
    banco.count_documents.assert_called_with({"data_publicacao": None, "sentimento": "positivo"})
    assert resumo == {"total": 2, "por_sentimento": {"positivo": 2, "negativo": 0, "neutro": 0},
                      "sem_data_publicacao": 3}
