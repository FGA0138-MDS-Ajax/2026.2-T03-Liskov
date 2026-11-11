import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pymongo.errors import ServerSelectionTimeoutError

from src.persistencia.escrita import criar_indices, obter_colecao, salvar_analises
from src.persistencia.conexao import (
    ErroConexaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)
from src.persistencia.leitura import (
    ErroConsultaInvalida,
    ErroLeituraAnalises,
    buscar_por_id,
    buscar_por_id_origem,
    contar_analises,
    contar_por_sentimento,
    listar_analises,
    montar_filtro,
    serializar_analise,
)


def utc(ano, mes, dia, hora=0, minuto=0):
    return datetime(ano, mes, dia, hora, minuto, tzinfo=timezone.utc)


def doc(id_origem, sentimento="positivo", fonte="b2w", proc=None, pub=None, **extra):
    d = {
        "id_origem": id_origem,
        "fonte": fonte,
        "texto_original": f"texto {id_origem}",
        "sentimento": sentimento,
        "modelo": {"nome": "pysentimiento/bertweet-pt-sentiment"},
        "data_processamento": proc or utc(2026, 11, 3, 14, 30),
    }
    if pub is not None:
        d["data_publicacao"] = pub
    d.update(extra)
    return d


@pytest.fixture(scope="session")
def client():
    uri = os.getenv("MONGODB_URI_TESTE", "mongodb://localhost:27017")
    try:
        cliente = connect_to_mongodb(uri, timeout_ms=1000)
    except ErroConexaoMongoDB:
        if os.getenv("CI"):
            pytest.fail("MongoDB de teste indisponível no CI.")
        pytest.skip("MongoDB de teste indisponível (suba com docker run ... mongo:7).")
    yield cliente
    disconnect_from_mongodb(cliente)


@pytest.fixture(scope="session")
def nome_banco_teste(client):
    nome = f"sentia_teste_{uuid4().hex[:8]}"
    yield nome
    client.drop_database(nome)


@pytest.fixture
def colecao(client, nome_banco_teste):
    col = obter_colecao(client, nome_banco_teste)
    col.delete_many({})
    criar_indices(col)
    yield col
    col.delete_many({})


# ---------- leitura simples ----------

def test_insere_e_le_de_volta_por_chave_natural(colecao):
    salvar_analises(colecao, [doc("a1", rotulo_original="5", metadados={"category": "x"})])

    lido = buscar_por_id_origem(colecao, "b2w", "a1")

    assert lido["texto_original"] == "texto a1"
    assert lido["sentimento"] == "positivo"
    assert lido["modelo"] == {"nome": "pysentimiento/bertweet-pt-sentiment"}
    assert lido["rotulo_original"] == "5"
    assert lido["metadados"] == {"category": "x"}


def test_busca_inexistente_devolve_none(colecao):
    assert buscar_por_id_origem(colecao, "b2w", "nao-existe") is None
    assert buscar_por_id(colecao, "id-malformado") is None


def test_busca_por_object_id(colecao):
    salvar_analises(colecao, [doc("a1")])
    _id = buscar_por_id_origem(colecao, "b2w", "a1")["_id"]
    assert buscar_por_id(colecao, str(_id))["id_origem"] == "a1"


def test_mesmo_id_em_fontes_diferentes_nao_conflita(colecao):
    resultado = salvar_analises(colecao, [doc("x", fonte="b2w"), doc("x", fonte="olist")])
    assert resultado == {"inseridos": 2, "duplicados": 0}
    assert buscar_por_id_origem(colecao, "olist", "x")["fonte"] == "olist"


# ---------- datas ----------

def test_data_publicacao_ausente_continua_omitida(colecao):
    salvar_analises(colecao, [doc("sem-data")])
    lido = buscar_por_id_origem(colecao, "b2w", "sem-data")
    assert "data_publicacao" not in lido
    assert "data_publicacao" not in serializar_analise(lido)


def test_datas_voltam_como_datetime_e_serializam_em_utc(colecao):
    salvar_analises(colecao, [doc("d1", pub=utc(2026, 10, 1), proc=utc(2026, 11, 3, 14, 30))])
    lido = buscar_por_id_origem(colecao, "b2w", "d1")

    assert isinstance(lido["data_publicacao"], datetime)
    serial = serializar_analise(lido)
    assert serial["data_publicacao"] == "2026-10-01T00:00:00Z"
    assert serial["data_processamento"] == "2026-11-03T14:30:00Z"
    assert isinstance(serial["_id"], str)


# ---------- filtros (seção 4.7) ----------

def test_filtro_por_sentimento_e_fonte(colecao):
    salvar_analises(colecao, [
        doc("1", "positivo"), doc("2", "negativo"), doc("3", "negativo", fonte="olist"),
    ])
    assert contar_analises(colecao, montar_filtro(sentimento="negativo")) == 2
    assert contar_analises(colecao, montar_filtro(sentimento="negativo", fonte="olist")) == 1


def test_filtro_periodo_publicacao_exclui_documentos_sem_data(colecao):
    salvar_analises(colecao, [
        doc("dentro", pub=utc(2026, 10, 15)),
        doc("fora", pub=utc(2026, 11, 1)),          # fim é exclusivo
        doc("sem-data"),
    ])
    filtro = montar_filtro(
        data_publicacao_inicio=utc(2026, 10, 1), data_publicacao_fim=utc(2026, 11, 1)
    )
    ids = {d["id_origem"] for d in listar_analises(colecao, filtro)}
    assert ids == {"dentro"}


def test_filtro_sem_data_publicacao(colecao):
    salvar_analises(colecao, [doc("com", pub=utc(2026, 10, 1)), doc("sem")])
    ids = [d["id_origem"] for d in listar_analises(colecao, montar_filtro(sem_data_publicacao=True))]
    assert ids == ["sem"]


def test_filtro_sentimento_mais_periodo(colecao):
    salvar_analises(colecao, [
        doc("1", "negativo", pub=utc(2026, 10, 10)),
        doc("2", "positivo", pub=utc(2026, 10, 10)),
    ])
    filtro = montar_filtro(
        sentimento="negativo",
        data_publicacao_inicio=utc(2026, 10, 1),
        data_publicacao_fim=utc(2026, 11, 1),
    )
    assert [d["id_origem"] for d in listar_analises(colecao, filtro)] == ["1"]


def test_filtro_por_modelo_e_periodo_de_processamento(colecao):
    salvar_analises(colecao, [
        doc("1", proc=utc(2026, 11, 3)),
        doc("2", proc=utc(2026, 11, 8), modelo={"nome": "baseline-tfidf-logreg"}),
    ])
    assert contar_analises(colecao, montar_filtro(modelo="baseline-tfidf-logreg")) == 1
    filtro = montar_filtro(
        data_processamento_inicio=utc(2026, 11, 1), data_processamento_fim=utc(2026, 11, 5)
    )
    assert [d["id_origem"] for d in listar_analises(colecao, filtro)] == ["1"]


def test_contagem_por_sentimento_sempre_devolve_tres_classes(colecao):
    salvar_analises(colecao, [doc("1", "positivo"), doc("2", "positivo"), doc("3", "negativo")])
    assert contar_por_sentimento(colecao) == {"positivo": 2, "negativo": 1, "neutro": 0}


# ---------- paginação ----------

def test_paginacao_mais_recentes_primeiro(colecao):
    salvar_analises(colecao, [doc(str(i), proc=utc(2026, 11, i)) for i in range(1, 6)])

    pagina1 = listar_analises(colecao, limite=2, pular=0)
    pagina2 = listar_analises(colecao, limite=2, pular=2)
    pagina3 = listar_analises(colecao, limite=2, pular=4)

    assert [d["id_origem"] for d in pagina1] == ["5", "4"]
    assert [d["id_origem"] for d in pagina2] == ["3", "2"]
    assert [d["id_origem"] for d in pagina3] == ["1"]


# ---------- validação de parâmetros ----------

@pytest.mark.parametrize("kwargs", [
    {"sentimento": "POS"},
    {"sentimento": "feliz"},
    {"fonte": "   "},
    {"data_publicacao_inicio": datetime(2026, 10, 1)},  # sem fuso
    {"data_publicacao_inicio": utc(2026, 11, 1), "data_publicacao_fim": utc(2026, 10, 1)},
    {"sem_data_publicacao": True, "data_publicacao_inicio": utc(2026, 10, 1)},
])
def test_montar_filtro_rejeita_parametros_invalidos(kwargs):
    with pytest.raises(ErroConsultaInvalida):
        montar_filtro(**kwargs)


@pytest.mark.parametrize("limite,pular", [(0, 0), (501, 0), (True, 0), (10, -1)])
def test_listar_rejeita_paginacao_invalida(colecao, limite, pular):
    with pytest.raises(ErroConsultaInvalida):
        listar_analises(colecao, limite=limite, pular=pular)


# ---------- erros de conexão (não precisam de banco) ----------

def test_conexao_com_porta_invalida_levanta_erro_seguro():
    with pytest.raises(ErroConexaoMongoDB) as erro:
        connect_to_mongodb("mongodb://usuario:senha@127.0.0.1:1", timeout_ms=300)
    assert "senha" not in str(erro.value)


class ColecaoQuebrada:
    def _falha(self, *args, **kwargs):
        raise ServerSelectionTimeoutError("mongodb://usuario:senha@host caiu")

    find = find_one = count_documents = aggregate = _falha


def test_falha_do_banco_na_leitura_vira_erro_seguro():
    col = ColecaoQuebrada()
    for chamada in (
        lambda: listar_analises(col),
        lambda: contar_analises(col),
        lambda: contar_por_sentimento(col),
        lambda: buscar_por_id_origem(col, "b2w", "1"),
    ):
        with pytest.raises(ErroLeituraAnalises) as erro:
            chamada()
        assert "senha" not in str(erro.value)