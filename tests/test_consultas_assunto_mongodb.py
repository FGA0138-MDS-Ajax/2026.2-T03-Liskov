"""Filtro por assunto (#113) nas rotas de consulta, contra um MongoDB real.

As rotas ``GET /analises`` e ``GET /analises/resumo`` rodam de ponta a ponta. O
resultado esperado vem de ``corresponde`` (src/comum/busca_textual.py), a mesma regra
da pesquisa do Administrador, para garantir que o MongoDB decide igual.
"""

import os
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.comum.busca_textual import corresponde
from src.dados.database import (
    ErroConexaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)
from src.dados.repositorio import criar_indices, obter_colecao, salvar_analise
from src.servico.dependencias import obter_colecao_analises
from src.servico.main import app

PROCESSAMENTO = datetime(2026, 11, 26, 12, tzinfo=UTC)

# (id_origem, sentimento, data de publicação ou None, texto)
BASE = [
    (
        "a01",
        "negativo",
        datetime(2026, 11, 2, tzinfo=UTC),
        "O custo de vida subiu de novo.",
    ),
    (
        "a02",
        "negativo",
        datetime(2026, 11, 20, tzinfo=UTC),
        "CUSTO DE VIDA em Brasília assusta",
    ),
    ("a03", "neutro", None, "Custo e vida: debate na TV"),
    (
        "a04",
        "positivo",
        datetime(2026, 11, 5, tzinfo=UTC),
        "Custo alto, mas a vida segue",
    ),
    (
        "a05",
        "positivo",
        datetime(2026, 11, 6, tzinfo=UTC),
        "A vacinação infantil começou.",
    ),
    ("a06", "neutro", datetime(2026, 11, 7, tzinfo=UTC), "Vacinas chegaram ao posto"),
    ("a07", "negativo", None, "Sem vacina no posto hoje"),
    ("a08", "positivo", datetime(2026, 11, 8, tzinfo=UTC), "Golpe de mestre no jogo"),
    ("a09", "positivo", datetime(2026, 11, 9, tzinfo=UTC), "Que GOL!"),
    (
        "a10",
        "neutro",
        datetime(2026, 11, 10, tzinfo=UTC),
        "Texto (sem) relação .* nenhuma",
    ),
]
TEXTOS = {id_origem: texto for id_origem, _, _, texto in BASE}


def _esperado(assunto, inicio=None, fim=None, sentimento=None):
    ids = []
    for id_origem, sent, publicacao, texto in BASE:
        if sentimento and sent != sentimento:
            continue
        if (inicio or fim) and publicacao is None:
            continue
        if inicio and publicacao.date() < date.fromisoformat(inicio):
            continue
        if fim and publicacao.date() > date.fromisoformat(fim):
            continue
        if assunto and not corresponde(assunto, texto):
            continue
        ids.append(id_origem)
    return sorted(ids)


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
    nome_banco = f"sentia_assunto_{uuid4().hex[:8]}"
    colecao = obter_colecao(conexao, nome_banco)
    criar_indices(colecao)
    for minutos, (id_origem, sentimento, publicacao, texto) in enumerate(BASE):
        documento = {
            "id_origem": id_origem,
            "fonte": "teste",
            "texto_original": texto,
            "sentimento": sentimento,
            "modelo": {"nome": "modelo-teste"},
            "data_processamento": PROCESSAMENTO - timedelta(minutes=minutos),
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
        conexao.drop_database(nome_banco)
        disconnect_from_mongodb(conexao)


def _consultar(cliente, **parametros):
    parametros = {
        chave: valor for chave, valor in parametros.items() if valor is not None
    }
    lista = cliente.get("/analises", params={**parametros, "tamanho": 100})
    resumo = cliente.get("/analises/resumo", params=parametros)
    assert lista.status_code == resumo.status_code == 200, (lista.text, resumo.text)
    return (
        sorted(i["id_origem"] for i in lista.json()["itens"]),
        lista.json(),
        resumo.json(),
    )


@pytest.mark.parametrize(
    "assunto",
    [
        "custo de vida",
        "Custo de Vida",
        "vacina",
        "Vacinação",
        "gol",
        "trump",
        "(",
        ".*",
        "a+b",
    ],
)
def test_assunto_filtra_listagem_e_resumo_igual_a_regra_da_pesquisa(cliente, assunto):
    ids, lista, resumo = _consultar(cliente, assunto=assunto)

    assert ids == _esperado(assunto)
    assert lista["total"] == resumo["total"] == len(ids)
    assert sum(resumo["por_sentimento"].values()) == resumo["total"]


def test_assunto_encontra_textos_com_acentos_e_maiusculas(cliente):
    ids, _, _ = _consultar(cliente, assunto="VACINACAO")

    # "vacina", "vacinas" e "vacinação" têm o mesmo radical.
    assert ids == ["a05", "a06", "a07"]


def test_termo_curto_exige_a_palavra_inteira(cliente):
    ids, _, _ = _consultar(cliente, assunto="gol")

    assert ids == ["a09"]  # "golpe" fica de fora


def test_consulta_com_ate_tres_termos_exige_todos(cliente):
    ids, _, _ = _consultar(cliente, assunto="custo de vida")

    # a04 tem "custo" e "vida"; "de" é palavra vazia. Todos os quatro têm os dois termos.
    assert ids == ["a01", "a02", "a03", "a04"]


def test_assunto_sem_resultado_responde_vazio_sem_erro(cliente):
    ids, lista, resumo = _consultar(cliente, assunto="eleição municipal")

    assert ids == [] and lista["total"] == 0
    assert resumo == {
        "total": 0,
        "por_sentimento": {"positivo": 0, "negativo": 0, "neutro": 0},
        "sem_data_publicacao": 0,
    }


@pytest.mark.parametrize("assunto", ["(", ".*", "[a-z]+", "\\d", "a|b"])
def test_caracteres_especiais_nao_quebram_nem_viram_expressao_regular(cliente, assunto):
    ids, _, _ = _consultar(cliente, assunto=assunto)

    # Se ".*" virasse regex, traria todos os textos.
    assert ids == _esperado(assunto)
    assert len(ids) < len(BASE)


@pytest.mark.parametrize(
    ("inicio", "fim", "sentimento"),
    [
        ("2026-11-01", "2026-11-10", None),
        ("2026-11-15", None, None),
        (None, None, "negativo"),
        ("2026-11-01", "2026-11-30", "negativo"),
    ],
)
def test_assunto_combinado_com_periodo_e_sentimento(cliente, inicio, fim, sentimento):
    ids, lista, resumo = _consultar(
        cliente, assunto="custo de vida", inicio=inicio, fim=fim, sentimento=sentimento
    )

    assert ids == _esperado("custo de vida", inicio, fim, sentimento)
    assert lista["total"] == resumo["total"] == len(ids)


def test_textos_sem_data_fora_do_periodo_contam_so_os_do_assunto(cliente):
    _, _, resumo = _consultar(cliente, assunto="custo de vida", inicio="2026-11-01")

    # Sem data na base: a03 (custo de vida) e a07 (vacina). Só a03 é do assunto.
    assert resumo["sem_data_publicacao"] == 1


def test_assunto_em_branco_e_o_mesmo_que_sem_filtro(cliente):
    com_espacos, _, _ = _consultar(cliente, assunto="   ")
    sem_filtro, _, _ = _consultar(cliente)

    assert com_espacos == sem_filtro == sorted(TEXTOS)


def test_paginacao_com_assunto_nao_repete_nem_perde(cliente):
    vistos = []
    for pagina in (1, 2, 3):
        corpo = cliente.get(
            "/analises",
            params={"assunto": "custo de vida", "pagina": pagina, "tamanho": 2},
        ).json()
        vistos += [item["id_origem"] for item in corpo["itens"]]
        assert corpo["total"] == 4

    assert sorted(vistos) == _esperado("custo de vida")
    assert len(vistos) == len(set(vistos))


@pytest.mark.parametrize("rota", ["/analises", "/analises/resumo"])
def test_assunto_com_mais_de_100_caracteres_e_recusado(cliente, rota):
    resposta = cliente.get(rota, params={"assunto": "a" * 101})

    assert resposta.status_code == 422
    assert "100 caracteres" in str(resposta.json()["detail"])
