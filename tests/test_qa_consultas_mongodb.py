"""QA da #26 (T11, T12 e T13): rotas de consulta contra um MongoDB real.

Diferente de ``test_consultas_api.py``, que simula a coleção, aqui as rotas
``GET /analises`` e ``GET /analises/resumo`` rodam de ponta a ponta: HTTP,
validação, repositório, índices e MongoDB. A base é um conjunto conhecido de
12 análises, e cada resposta é comparada com um oráculo calculado no próprio
teste a partir da regra documentada:

- os dias de ``inicio`` e ``fim`` são inclusivos e contados em UTC (decisão da
  PO em 26/11: datas em UTC, porque os textos vêm de fontes e fusos diferentes);
- textos sem ``data_publicacao`` aparecem sem filtro de período e saem quando há
  período (decisão D-04); o resumo informa quantos ficaram de fora;
- a ordem é ``data_processamento`` decrescente, com desempate por ``fonte`` e
  ``id_origem``.

Requer MongoDB (``MONGODB_URI_TESTE``); sem ele o módulo é pulado localmente e
falha no CI, como os demais testes de persistência.
"""

import os
from datetime import UTC, date, datetime, timedelta, timezone
from itertools import product
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.dados.database import (
    ErroConexaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)
from src.dados.repositorio import criar_indices, obter_colecao, salvar_analise
from src.servico.dependencias import obter_colecao_analises
from src.servico.main import app

BRASILIA = timezone(timedelta(hours=-3))
PROCESSAMENTO_BASE = datetime(2026, 11, 25, 12, tzinfo=UTC)

# (id_origem, fonte, sentimento, data_publicacao, minutos antes do processamento base)
# "ausente" = campo não existe; None = campo gravado como null (dado legado).
BASE_CONHECIDA = [
    ("d01", "csv", "positivo", datetime(2026, 11, 1, 0, 0, 0, tzinfo=UTC), 1),
    ("d02", "csv", "negativo", datetime(2026, 11, 1, 12, tzinfo=UTC), 2),
    ("d03", "csv", "neutro", datetime(2026, 11, 10, 23, 59, 59, 999000, tzinfo=UTC), 3),
    ("d04", "X", "positivo", datetime(2026, 11, 11, 0, 0, 0, tzinfo=UTC), 4),
    ("d05", "X", "negativo", datetime(2026, 10, 31, 23, 59, 59, 999000, tzinfo=UTC), 5),
    ("d06", "X", "neutro", datetime(2026, 11, 20, 8, tzinfo=UTC), 6),
    (
        "d07",
        "csv",
        "positivo",
        datetime(2026, 11, 30, 23, 59, 59, 999000, tzinfo=UTC),
        7,
    ),
    ("d08", "csv", "negativo", datetime(2026, 12, 1, 0, 0, 0, tzinfo=UTC), 8),
    # 15/11 às 22h em Brasília = 16/11 à 01h em UTC.
    ("d09", "X", "positivo", datetime(2026, 11, 15, 22, tzinfo=BRASILIA), 9),
    ("d10", "TweetSentBR", "positivo", "ausente", 10),
    ("d11", "TweetSentBR", "neutro", "ausente", 10),  # mesmo processamento que d10
    ("d12", "legado", "negativo", None, 11),
]
SEM_DATA = {"d10", "d11", "d12"}
TODOS = [item[0] for item in BASE_CONHECIDA]

PERIODOS = [
    (None, None),
    ("2026-11-01", None),
    (None, "2026-11-10"),
    ("2026-11-01", "2026-11-10"),
    ("2026-11-10", "2026-11-10"),
    ("2026-11-11", "2026-11-11"),
    ("2026-10-31", "2026-10-31"),
    ("2026-11-15", "2026-11-15"),
    ("2026-11-16", "2026-11-16"),
    ("2026-12-01", None),
    ("2026-01-01", "2026-01-31"),
]
SENTIMENTOS = [None, "positivo", "negativo", "neutro"]


def _documento(id_origem, fonte, sentimento, publicacao, minutos):
    doc = {
        "id_origem": id_origem,
        "fonte": fonte,
        "texto_original": f"texto {id_origem}",
        "sentimento": sentimento,
        "modelo": {"nome": "modelo-qa"},
        "data_processamento": PROCESSAMENTO_BASE - timedelta(minutes=minutos),
    }
    if publicacao != "ausente":
        doc["data_publicacao"] = publicacao
    return doc


def _oraculo(inicio=None, fim=None, sentimento=None):
    """Ids esperados, na ordem pública, segundo a regra documentada."""
    selecionados = []
    for id_origem, fonte, sent, publicacao, minutos in BASE_CONHECIDA:
        if sentimento is not None and sent != sentimento:
            continue
        if inicio is not None or fim is not None:
            if publicacao in ("ausente", None):
                continue
            dia_utc = publicacao.astimezone(UTC).date()
            if inicio is not None and dia_utc < date.fromisoformat(inicio):
                continue
            if fim is not None and dia_utc > date.fromisoformat(fim):
                continue
        selecionados.append((minutos, fonte, id_origem))
    # data_processamento decrescente = minutos crescentes; depois fonte e id_origem.
    return [id_origem for _, _, id_origem in sorted(selecionados)]


def _parametros(inicio=None, fim=None, sentimento=None, **extra):
    base = {"inicio": inicio, "fim": fim, "sentimento": sentimento, **extra}
    return {chave: valor for chave, valor in base.items() if valor is not None}


def _todas_as_paginas(cliente, tamanho, **filtros):
    ids, pagina = [], 1
    while True:
        resposta = cliente.get(
            "/analises", params=_parametros(**filtros, pagina=pagina, tamanho=tamanho)
        )
        assert resposta.status_code == 200, resposta.text
        corpo = resposta.json()
        if not corpo["itens"]:
            return ids, corpo["total"], pagina
        ids += [item["id_origem"] for item in corpo["itens"]]
        pagina += 1


# ---------- fixtures: MongoDB real e banco descartável ----------


@pytest.fixture(scope="module")
def cliente_mongodb():
    if os.getenv("SENTIA_TESTES_SEM_MONGODB") == "1":
        pytest.skip("MongoDB real desabilitado explicitamente nesta execução.")
    uri = os.getenv("MONGODB_URI_TESTE", "mongodb://127.0.0.1:27017")
    try:
        cliente = connect_to_mongodb(uri, timeout_ms=1000)
    except ErroConexaoMongoDB:
        if os.getenv("CI"):
            pytest.fail("MongoDB de teste indisponível no CI.")
        pytest.skip("MongoDB de teste indisponível (suba com docker/podman mongo:7).")
    yield cliente
    disconnect_from_mongodb(cliente)


@pytest.fixture(scope="module")
def colecao(cliente_mongodb):
    nome_banco = f"sentia_qa26_{uuid4().hex[:8]}"
    col = obter_colecao(cliente_mongodb, nome_banco)
    criar_indices(col)
    for item in BASE_CONHECIDA:
        documento = _documento(*item)
        if item[3] is None:
            # Dado legado: a validação atual não aceita null, então grava direto.
            col.insert_one(documento)
        else:
            assert salvar_analise(col, documento)
    yield col
    cliente_mongodb.drop_database(nome_banco)


@pytest.fixture(scope="module")
def cliente(colecao):
    def colecao_de_teste():
        yield colecao

    app.dependency_overrides[obter_colecao_analises] = colecao_de_teste
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(obter_colecao_analises, None)


# ---------- T11: listagem e paginação ----------


def test_t11_listagem_sem_filtros_traz_tudo_na_ordem_publica(cliente):
    resposta = cliente.get("/analises", params={"tamanho": 100})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == len(BASE_CONHECIDA)
    assert corpo["pagina"] == 1 and corpo["tamanho"] == 100
    assert [item["id_origem"] for item in corpo["itens"]] == _oraculo()


def test_t11_contrato_de_cada_item(cliente):
    itens = cliente.get("/analises", params={"tamanho": 100}).json()["itens"]
    por_id = {item["id_origem"]: item for item in itens}

    for item in itens:
        assert "_id" not in item
        assert set(item) >= {
            "id_origem",
            "fonte",
            "texto_original",
            "sentimento",
            "modelo",
            "data_processamento",
            "data_publicacao",
        }
        assert item["sentimento"] in {"positivo", "negativo", "neutro"}
        assert datetime.fromisoformat(
            item["data_processamento"]
        ).utcoffset() == timedelta(0)
    # Datas voltam em UTC, mesmo quando o texto foi publicado com outro fuso.
    assert datetime.fromisoformat(por_id["d09"]["data_publicacao"]) == datetime(
        2026, 11, 16, 1, tzinfo=UTC
    )
    # Sem data (campo ausente ou null legado) aparece como null, sem inventar data.
    for sem_data in SEM_DATA:
        assert por_id[sem_data]["data_publicacao"] is None


@pytest.mark.parametrize("tamanho", [1, 5, 7, 12, 100])
def test_t11_paginacao_percorre_tudo_sem_repetir_nem_perder(cliente, tamanho):
    ids, total, paginas_lidas = _todas_as_paginas(cliente, tamanho)

    assert total == len(BASE_CONHECIDA)
    assert ids == _oraculo()
    assert len(ids) == len(set(ids))
    assert paginas_lidas - 1 == -(-total // tamanho)  # arredonda para cima


def test_t11_pagina_alem_da_ultima_vem_vazia_com_o_total(cliente):
    corpo = cliente.get("/analises", params={"pagina": 99, "tamanho": 5}).json()

    assert corpo["itens"] == []
    assert corpo["total"] == len(BASE_CONHECIDA)
    assert corpo["pagina"] == 99


def test_t11_desempate_estavel_entre_paginas(cliente):
    # d10 e d11 têm o mesmo data_processamento; a ordem desempata por fonte e id_origem.
    primeira = cliente.get("/analises", params={"pagina": 10, "tamanho": 1}).json()
    segunda = cliente.get("/analises", params={"pagina": 11, "tamanho": 1}).json()

    assert [primeira["itens"][0]["id_origem"], segunda["itens"][0]["id_origem"]] == [
        "d10",
        "d11",
    ]


# ---------- T12: período ----------


@pytest.mark.parametrize(("inicio", "fim"), PERIODOS)
def test_t12_periodo_inclui_os_dois_dias_inteiros_em_utc(cliente, inicio, fim):
    esperado = _oraculo(inicio, fim)

    ids, total, _ = _todas_as_paginas(cliente, 5, inicio=inicio, fim=fim)
    resumo = cliente.get("/analises/resumo", params=_parametros(inicio, fim)).json()

    assert ids == esperado
    assert total == resumo["total"] == len(esperado)


def test_t12_textos_sem_data_aparecem_sem_periodo_e_saem_com_periodo(cliente):
    sem_periodo = cliente.get("/analises/resumo").json()
    com_periodo = cliente.get(
        "/analises/resumo", params={"inicio": "2026-01-01", "fim": "2026-12-31"}
    ).json()

    assert sem_periodo["total"] == len(BASE_CONHECIDA)
    assert sem_periodo["sem_data_publicacao"] == 0
    assert com_periodo["total"] == len(BASE_CONHECIDA) - len(SEM_DATA)
    assert com_periodo["sem_data_publicacao"] == len(SEM_DATA)


def test_t12_limite_do_dia_e_utc_e_nao_horario_de_brasilia(cliente):
    """Decisão da PO (26/11/2026): datas armazenadas, filtradas e exibidas em UTC.

    Os textos vêm de fontes e fusos diferentes. d09 foi publicado em 15/11 às 22h
    de Brasília, então aparece no dia 16/11 (UTC), como na coluna do painel.
    """
    dia_15 = cliente.get(
        "/analises", params={"inicio": "2026-11-15", "fim": "2026-11-15"}
    ).json()
    dia_16 = cliente.get(
        "/analises", params={"inicio": "2026-11-16", "fim": "2026-11-16"}
    ).json()

    assert dia_15["total"] == 0
    assert [item["id_origem"] for item in dia_16["itens"]] == ["d09"]


# ---------- T13: sentimento e combinações ----------


@pytest.mark.parametrize("sentimento", ["positivo", "negativo", "neutro"])
def test_t13_filtro_por_sentimento(cliente, sentimento):
    ids, total, _ = _todas_as_paginas(cliente, 100, sentimento=sentimento)
    resumo = cliente.get("/analises/resumo", params={"sentimento": sentimento}).json()

    assert ids == _oraculo(sentimento=sentimento)
    assert total == resumo["total"] == resumo["por_sentimento"][sentimento]
    assert {
        classe: quantidade
        for classe, quantidade in resumo["por_sentimento"].items()
        if classe != sentimento
    } == {
        classe: 0
        for classe in ("positivo", "negativo", "neutro")
        if classe != sentimento
    }


@pytest.mark.parametrize(
    ("periodo", "sentimento"), list(product(PERIODOS, SENTIMENTOS))
)
def test_t13_combinacoes_sem_perder_nem_incluir_registros(cliente, periodo, sentimento):
    inicio, fim = periodo
    esperado = _oraculo(inicio, fim, sentimento)

    ids, total, _ = _todas_as_paginas(
        cliente, 5, inicio=inicio, fim=fim, sentimento=sentimento
    )
    resumo = cliente.get(
        "/analises/resumo", params=_parametros(inicio, fim, sentimento)
    ).json()

    assert ids == esperado
    assert total == resumo["total"] == len(esperado)
    assert sum(resumo["por_sentimento"].values()) == resumo["total"]
    sem_data_esperado = (
        sum(
            1
            for item in BASE_CONHECIDA
            if item[0] in SEM_DATA and sentimento in (None, item[2])
        )
        if inicio or fim
        else 0
    )
    assert resumo["sem_data_publicacao"] == sem_data_esperado


# ---------- contrato HTTP: entradas inválidas e banco fora do ar ----------


@pytest.mark.parametrize(
    "parametros",
    [
        {"sentimento": "feliz"},
        {"inicio": "2026-13-01"},
        {"inicio": "01/11/2026"},
        {"fim": "2026-11-31"},
        {"inicio": "2026-11-10", "fim": "2026-11-01"},
    ],
)
@pytest.mark.parametrize("rota", ["/analises", "/analises/resumo"])
def test_contrato_filtros_invalidos_retornam_422_com_detalhe(cliente, rota, parametros):
    resposta = cliente.get(rota, params=parametros)

    assert resposta.status_code == 422
    assert resposta.json()["detail"]


@pytest.mark.parametrize(
    "parametros",
    [
        {"pagina": 0},
        {"pagina": "a"},
        {"tamanho": 0},
        {"tamanho": 101},
        {"tamanho": "1.5"},
    ],
)
def test_contrato_paginacao_invalida_retorna_422(cliente, parametros):
    resposta = cliente.get("/analises", params=parametros)

    assert resposta.status_code == 422
    assert resposta.json()["detail"]


def test_contrato_banco_fora_do_ar_retorna_503_sem_vazar_detalhes(monkeypatch):
    """Usa a dependência real, apontando para uma porta sem MongoDB."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:1/sentia")
    # Guarda o override do módulo para devolvê-lo depois, seja qual for a ordem dos testes.
    override = app.dependency_overrides.pop(obter_colecao_analises, None)
    try:
        with TestClient(app) as cliente_http:
            for rota in ("/analises", "/analises/resumo"):
                resposta = cliente_http.get(rota)
                assert resposta.status_code == 503
                assert resposta.json() == {"detail": "Banco de dados indisponível."}
    finally:
        if override is not None:
            app.dependency_overrides[obter_colecao_analises] = override
