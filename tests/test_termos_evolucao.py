"""Termos frequentes (#30) e evolução no período (#121): regra, API com MongoDB real e painel."""

import os
from datetime import UTC, date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.apresentacao.contrato import ErroFonteDados, FiltrosAnalises
from src.apresentacao.fontes.api import FonteApi
from src.apresentacao.fontes.mock import (
    ANALISES_DE_EXEMPLO,
    FonteMock,
    inicio_do_periodo,
)
from src.comum.busca_textual import contar_termos
from src.dados.database import (
    ErroConexaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)
from src.dados.repositorio import criar_indices, obter_colecao, salvar_analise
from src.servico.dependencias import obter_colecao_analises
from src.servico.main import app

# --- Contagem de termos (regra pura) -----------------------------------------------


def test_termos_ignoram_links_mencoes_vazias_risadas_e_numeros():
    textos = [
        "O custo de vida subiu! https://exemplo.com/a @fulano kkkk 2026",
        "Custo alto e salário baixo, rsrs www.site.com &gt;",
        "Salário não acompanha o custo",
    ]

    termos = dict(contar_termos(textos))

    assert termos["custo"] == 3 and termos["salário"] == 2
    for fora in (
        "https",
        "exemplo",
        "fulano",
        "kkkk",
        "rsrs",
        "2026",
        "site",
        "gt",
        "não",
        "o",
    ):
        assert fora not in termos


def test_termos_juntam_formas_com_e_sem_acento_e_mostram_a_mais_comum():
    termos = contar_termos(["Vacinação já", "vacinação hoje", "vacinacao amanhã"])

    assert termos[0] == ("vacinação", 3)


def test_termos_tiram_as_palavras_do_assunto_filtrado():
    textos = ["custo de vida e salário", "o custo da vida e o aluguel"]

    termos = [t for t, _ in contar_termos(textos, assunto="Custo de Vida")]

    assert "custo" not in termos and "vida" not in termos
    assert "salário" in termos and "aluguel" in termos


def test_hashtag_conta_como_palavra_e_empate_fica_em_ordem_alfabetica():
    termos = contar_termos(["#SaudePublica importa", "saudepublica e escola", "escola"])

    assert termos == [("escola", 2), ("saudepublica", 2), ("importa", 1)]


def test_limite_de_termos():
    assert (
        len(contar_termos([" ".join(f"palavra{c}" for c in "abcdefghij")], limite=3))
        == 3
    )


# --- Agrupamento por período ---------------------------------------------------------


@pytest.mark.parametrize(
    ("dia", "granularidade", "esperado"),
    [
        (date(2026, 11, 27), "dia", date(2026, 11, 27)),
        (date(2026, 11, 27), "semana", date(2026, 11, 23)),  # sexta -> segunda
        (date(2026, 11, 23), "semana", date(2026, 11, 23)),
        (date(2026, 11, 27), "mes", date(2026, 11, 1)),
    ],
)
def test_inicio_do_periodo(dia, granularidade, esperado):
    assert inicio_do_periodo(dia, granularidade) == esperado


# --- API com MongoDB real ------------------------------------------------------------

PROCESSAMENTO = datetime(2026, 11, 27, 12, tzinfo=UTC)
BRASILIA = timezone(timedelta(hours=-3))
BASE = [
    (
        "e1",
        "positivo",
        datetime(2026, 11, 2, 10, tzinfo=UTC),
        "Custo de vida e aluguel alto",
    ),
    (
        "e2",
        "negativo",
        datetime(2026, 11, 3, 10, tzinfo=UTC),
        "Aluguel subiu, custo de vida pesa",
    ),
    (
        "e3",
        "negativo",
        datetime(2026, 11, 10, 10, tzinfo=UTC),
        "Salário não acompanha o aluguel",
    ),
    (
        "e4",
        "neutro",
        datetime(2026, 12, 1, 10, tzinfo=UTC),
        "Vacinação começou no posto",
    ),
    # 30/11 às 22h em Brasília = 01/12 à 01h em UTC: conta em dezembro (D12).
    (
        "e5",
        "positivo",
        datetime(2026, 11, 30, 22, tzinfo=BRASILIA),
        "Vacinação infantil boa",
    ),
    ("e6", "neutro", None, "Aluguel e salário sem data"),
]


@pytest.fixture(scope="module")
def cliente():
    if os.getenv("SENTIA_TESTES_SEM_MONGODB") == "1":
        pytest.skip("MongoDB real desabilitado explicitamente nesta execução.")
    try:
        conexao = connect_to_mongodb(
            os.getenv("MONGODB_URI_TESTE", "mongodb://127.0.0.1:27017"), timeout_ms=1000
        )
    except ErroConexaoMongoDB:
        if os.getenv("CI"):
            pytest.fail("MongoDB de teste indisponível no CI.")
        pytest.skip("MongoDB de teste indisponível (suba com docker/podman mongo:7).")
    nome = f"sentia_te_{uuid4().hex[:8]}"
    colecao = obter_colecao(conexao, nome)
    criar_indices(colecao)
    for i, (id_origem, sentimento, publicacao, texto) in enumerate(BASE):
        documento = {
            "id_origem": id_origem,
            "fonte": "teste",
            "texto_original": texto,
            "sentimento": sentimento,
            "modelo": {"nome": "modelo-teste"},
            "data_processamento": PROCESSAMENTO - timedelta(minutes=i),
        }
        if publicacao is not None:
            documento["data_publicacao"] = publicacao
        assert salvar_analise(colecao, documento)

    def colecao_de_teste():
        yield colecao

    app.dependency_overrides[obter_colecao_analises] = colecao_de_teste
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(obter_colecao_analises, None)
        conexao.drop_database(nome)
        disconnect_from_mongodb(conexao)


def test_rota_de_termos_conta_os_textos_do_filtro(cliente):
    corpo = cliente.get("/analises/termos", params={"limite": 3}).json()

    assert corpo["termos"][0] == {"termo": "aluguel", "quantidade": 4}
    assert len(corpo["termos"]) == 3
    assert corpo["textos_lidos"] == corpo["total"] == len(BASE)


def test_rota_de_termos_respeita_assunto_e_sentimento(cliente):
    corpo = cliente.get(
        "/analises/termos",
        params={"assunto": "custo de vida", "sentimento": "negativo"},
    ).json()

    termos = {t["termo"]: t["quantidade"] for t in corpo["termos"]}
    assert corpo["total"] == 1  # só e2 é negativo e fala de custo de vida
    assert termos == {"aluguel": 1, "pesa": 1, "subiu": 1}


def test_rota_de_termos_sem_textos_devolve_lista_vazia(cliente):
    corpo = cliente.get("/analises/termos", params={"assunto": "eleição"}).json()

    assert corpo == {"termos": [], "textos_lidos": 0, "total": 0}


@pytest.mark.parametrize(
    ("granularidade", "esperado"),
    [
        ("dia", {"2026-11-02": 1, "2026-11-03": 1, "2026-11-10": 1, "2026-12-01": 2}),
        ("semana", {"2026-11-02": 2, "2026-11-09": 1, "2026-11-30": 2}),
        ("mes", {"2026-11-01": 3, "2026-12-01": 2}),
    ],
)
def test_rota_de_evolucao_agrupa_em_utc_e_conta_sem_data(
    cliente, granularidade, esperado
):
    corpo = cliente.get(
        "/analises/evolucao", params={"granularidade": granularidade}
    ).json()

    assert corpo["granularidade"] == granularidade
    assert {p["periodo"]: p["total"] for p in corpo["pontos"]} == esperado
    assert [p["periodo"] for p in corpo["pontos"]] == sorted(esperado)
    assert corpo["sem_data_publicacao"] == 1  # e6
    for ponto in corpo["pontos"]:
        assert sum(ponto["por_sentimento"].values()) == ponto["total"]


def test_rota_de_evolucao_respeita_assunto_periodo_e_sentimento(cliente):
    corpo = cliente.get(
        "/analises/evolucao",
        params={
            "granularidade": "mes",
            "assunto": "aluguel",
            "inicio": "2026-11-01",
            "fim": "2026-11-30",
            "sentimento": "negativo",
        },
    ).json()

    assert corpo["pontos"] == [
        {
            "periodo": "2026-11-01",
            "por_sentimento": {"positivo": 0, "negativo": 2, "neutro": 0},
            "total": 2,
        }
    ]
    assert corpo["sem_data_publicacao"] == 0  # o único sem data (e6) é neutro


@pytest.mark.parametrize(
    ("rota", "parametros"),
    [
        ("/analises/evolucao", {"granularidade": "ano"}),
        ("/analises/termos", {"limite": 0}),
        ("/analises/termos", {"limite": 31}),
        ("/analises/termos", {"inicio": "2026-12-01", "fim": "2026-11-01"}),
    ],
)
def test_parametros_invalidos_retornam_422(cliente, rota, parametros):
    assert cliente.get(rota, params=parametros).status_code == 422


# --- Painel: fontes ----------------------------------------------------------------


def test_mock_conta_termos_e_evolucao_com_a_mesma_regra():
    fonte = FonteMock()

    termos = fonte.termos(FiltrosAnalises(sentimento="negativo"), limite=3)
    evolucao = fonte.evolucao(FiltrosAnalises(), "mes")

    assert len(termos.termos) <= 3 and not termos.limitado
    datados = [a for a in ANALISES_DE_EXEMPLO if a.data_publicacao is not None]
    assert sum(sum(p.por_sentimento.values()) for p in evolucao.pontos) == len(datados)
    assert evolucao.sem_data_publicacao == len(ANALISES_DE_EXEMPLO) - len(datados)


class _Resposta:
    def __init__(self, corpo, status=200):
        self.status_code = status
        self._corpo = corpo

    def json(self):
        return self._corpo


class _Sessao:
    def __init__(self, corpo):
        self.corpo = corpo
        self.chamadas = []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append((url, params))
        return _Resposta(self.corpo)


def test_cliente_da_api_envia_filtros_e_le_os_termos():
    sessao = _Sessao(
        {
            "termos": [{"termo": "aluguel", "quantidade": 4}],
            "textos_lidos": 5,
            "total": 9,
        }
    )
    fonte = FonteApi("http://api", sessao=sessao)

    termos = fonte.termos(FiltrosAnalises(assunto="custo"), limite=5)

    assert sessao.chamadas[0] == (
        "http://api/analises/termos",
        {"assunto": "custo", "limite": 5},
    )
    assert termos.termos[0].termo == "aluguel" and termos.limitado


def test_cliente_da_api_le_a_evolucao():
    sessao = _Sessao(
        {
            "granularidade": "semana",
            "pontos": [
                {
                    "periodo": "2026-11-23",
                    "por_sentimento": {"positivo": 1, "neutro": 0, "negativo": 2},
                    "total": 3,
                }
            ],
            "sem_data_publicacao": 7,
        }
    )
    fonte = FonteApi("http://api", sessao=sessao)

    evolucao = fonte.evolucao(FiltrosAnalises(), "semana")

    assert sessao.chamadas[0][1] == {"granularidade": "semana"}
    assert evolucao.pontos[0].periodo == date(2026, 11, 23)
    assert evolucao.sem_data_publicacao == 7


@pytest.mark.parametrize(
    "corpo",
    [
        {"termos": [{"termo": "", "quantidade": 1}], "textos_lidos": 1, "total": 1},
        {"termos": [], "textos_lidos": 5, "total": 1},
        {"granularidade": "mes", "pontos": [], "sem_data_publicacao": 0},
    ],
)
def test_respostas_fora_do_contrato_viram_mensagem_clara(corpo):
    fonte = FonteApi("http://api", sessao=_Sessao(corpo))

    with pytest.raises(ErroFonteDados, match="contrato"):
        if "termos" in corpo:
            fonte.termos(FiltrosAnalises())
        else:
            fonte.evolucao(FiltrosAnalises(), "semana")
