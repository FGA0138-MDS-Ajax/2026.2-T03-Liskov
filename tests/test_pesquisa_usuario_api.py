"""Busca do Usuário sem login (#120): base primeiro, X só para completar até 50.

Travas de gasto decididas pela PO em 25 e 26/11: meta fixa de 50, sem "forçar
atualização", limite diário de buscas no X (só conta a busca que chama o X) e cache
de 30 dias. Usa as mesmas peças falsas dos testes da Administração.
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.dados.repositorio import NOME_COLECAO_BUSCAS_X_PUBLICAS, RepositorioAnalises
from src.servico.administracao import obter_contexto
from src.servico.main import app
from tests.test_api_administracao import (
    ColecaoAnalisesFalsa,
    XFalso,
    _contexto,
    _entrar,
    _importar,
    _tweets,
)


def _csv_base(quantidade: int, assunto: str = "vacina") -> bytes:
    linhas = ["id,texto,fonte"]
    linhas += [f"b{i},Notícia {i} sobre {assunto} no posto,teste" for i in range(quantidade)]
    return ("\n".join(linhas) + "\n").encode()


@pytest.fixture
def montar(tmp_path):
    """Cria API e contexto com X falso, base importada e limite diário configurável."""

    def criar(x, *, na_base=3, limite=15, assunto="vacina"):
        contexto = _contexto(tmp_path, buscar_x=x, limite_buscas_x_dia=limite)
        app.dependency_overrides[obter_contexto] = lambda: contexto
        cliente = TestClient(app)
        if na_base:
            _importar(cliente, _entrar(cliente), _csv_base(na_base, assunto), "base.csv")
        return cliente, contexto

    yield criar
    app.dependency_overrides.clear()


def _buscar(cliente, termo="vacina", **extras):
    resposta = cliente.post("/pesquisas", json={"termo": termo, **extras})
    assert resposta.status_code == 202, resposta.json()
    dados = cliente.get(f"/pesquisas/{resposta.json()['id']}").json()
    assert dados["situacao"] == "concluida", dados
    return dados


def _buscas_do_dia(contexto) -> int:
    with contexto.repositorio_analises() as repo:
        return repo.contar_buscas_x_publicas()


# --- Regra de produto -----------------------------------------------------------


def test_nao_precisa_de_login(montar):
    cliente, _ = montar(XFalso(_tweets("t1")))
    resposta = cliente.post("/pesquisas", json={"termo": "vacina"})  # sem cabeçalho

    assert resposta.status_code == 202


def test_base_com_50_ou_mais_nao_chama_o_x_nem_conta_no_limite(montar):
    x = XFalso(_tweets("t1"))
    cliente, contexto = montar(x, na_base=55)

    dados = _buscar(cliente)

    assert x.pedidos == []
    assert dados["origem"] == {"base": 50, "x": 0, "duplicatas": 0}
    assert "não foi preciso buscar no X" in dados["mensagem"]
    assert _buscas_do_dia(contexto) == 0


def test_base_com_menos_de_50_pede_ao_x_so_a_diferenca(montar):
    x = XFalso(_tweets(*[f"t{i}" for i in range(47)]))
    cliente, contexto = montar(x, na_base=3)

    dados = _buscar(cliente)

    assert x.pedidos == [("vacina", 47)]  # 50 - 3 da base
    assert dados["origem"] == {"base": 3, "x": 47, "duplicatas": 0}
    assert dados["textos_analisados"] == 50
    assert _buscas_do_dia(contexto) == 1


def test_usuario_nao_escolhe_quantidade_nem_forca_atualizacao(montar):
    x = XFalso(_tweets("t1"), _tweets("t2"))
    cliente, _ = montar(x, na_base=3)

    _buscar(cliente, quantidade=100, forcar_atualizacao=True, complementar_com_x=False)

    assert x.pedidos == [("vacina", 47)]  # meta fixa de 50, X ligado, sem forçar


def test_x_com_poucos_textos_avisa_quantos_vieram(montar):
    cliente, _ = montar(XFalso(_tweets("t1", "t2")), na_base=3)

    dados = _buscar(cliente)

    assert dados["origem"]["x"] == 2
    assert "só 2 texto(s)" in dados["mensagem"]


# --- Limite diário --------------------------------------------------------------


def test_limite_diario_corta_a_busca_no_x_e_mostra_so_a_base(montar):
    x = XFalso(_tweets("a1"), _tweets("b1"), _tweets("c1"))
    cliente, contexto = montar(x, na_base=0, limite=2)
    _importar(cliente, _entrar(cliente), _csv_base(3, "futebol") + b"", "futebol.csv")

    _buscar(cliente, "vacina")
    _buscar(cliente, "eleição")
    terceira = _buscar(cliente, "futebol")

    assert len(x.pedidos) == 2  # a terceira não chamou o X
    assert _buscas_do_dia(contexto) == 2
    assert "limite de buscas no X de hoje" in terceira["mensagem"]
    assert terceira["origem"] == {"base": 3, "x": 0, "duplicatas": 0}


def test_limite_do_usuario_nao_afeta_a_administracao(montar):
    x = XFalso(_tweets("t1"))
    cliente, _ = montar(x, na_base=3, limite=0)

    resposta = cliente.post(
        "/coletas",
        headers=_entrar(cliente),
        json={"fonte": "pesquisa", "termo": "vacina", "quantidade": 5, "complementar_com_x": True},
    )

    assert resposta.status_code == 202
    assert x.pedidos == [("vacina", 2)]


def test_reserva_concorrente_nunca_passa_do_limite():
    repo = RepositorioAnalises(ColecaoAnalisesFalsa())
    agora = datetime(2026, 11, 26, 15, tzinfo=UTC)

    resultados = [repo.reservar_busca_x_publica("t", 2, agora) for _ in range(4)]

    assert resultados == [True, True, False, False]
    assert repo.contar_buscas_x_publicas(agora) == 2
    # As reservas recusadas não ficam no banco.
    assert len(repo.colecao.database[NOME_COLECAO_BUSCAS_X_PUBLICAS].documentos) == 2


def test_limite_vale_por_dia_em_utc():
    repo = RepositorioAnalises(ColecaoAnalisesFalsa())
    hoje = datetime(2026, 11, 26, 23, 59, tzinfo=UTC)

    assert repo.reservar_busca_x_publica("t", 1, hoje)
    assert not repo.reservar_busca_x_publica("t", 1, hoje)
    assert repo.reservar_busca_x_publica("t", 1, hoje + timedelta(minutes=2))  # 27/11


# --- Cache de 30 dias -----------------------------------------------------------


def test_repetir_a_busca_usa_o_cache_avisa_a_data_e_nao_gasta(montar):
    x = XFalso(_tweets("t1", "t2"), _tweets("t3"))
    cliente, contexto = montar(x, na_base=3)

    _buscar(cliente)
    segunda = _buscar(cliente)

    assert len(x.pedidos) == 1
    assert _buscas_do_dia(contexto) == 1
    hoje = datetime.now(UTC).strftime("%d/%m")
    assert segunda["mensagem"] == (
        f"Este assunto já foi buscado no X em {hoje}; mostrando os textos guardados."
    )


def test_cache_com_mais_de_30_dias_deixa_buscar_de_novo(montar):
    x = XFalso(_tweets("t1", "t2"), _tweets("t3"))
    cliente, contexto = montar(x, na_base=3)
    _buscar(cliente)
    pesquisas = contexto._colecao_analises.database["pesquisas"].documentos
    for documento in pesquisas:
        documento["atualizado_em"] = datetime.now(UTC) - timedelta(days=31)

    _buscar(cliente)

    assert len(x.pedidos) == 2


# --- Erros e fronteiras ---------------------------------------------------------


def test_sem_chave_do_xfetch_mostra_so_a_base(montar):
    cliente, _ = montar(None, na_base=3)

    dados = _buscar(cliente)

    assert dados["origem"] == {"base": 3, "x": 0, "duplicatas": 0}
    assert "não está configurada" in dados["mensagem"]


@pytest.mark.parametrize("termo", ["", "   ", "a" * 101])
def test_termo_invalido_e_recusado(montar, termo):
    cliente, _ = montar(XFalso())

    resposta = cliente.post("/pesquisas", json={"termo": termo})

    assert resposta.status_code == 422
    assert "até 100 caracteres" in resposta.json()["mensagem"]


def test_pesquisa_publica_nao_mostra_coletas_da_administracao(montar):
    cliente, _ = montar(XFalso(), na_base=3)
    resposta = cliente.post(
        "/coletas", headers=_entrar(cliente), json={"fonte": "pesquisa", "termo": "x", "quantidade": 1}
    )

    assert cliente.get(f"/pesquisas/{resposta.json()['id']}").status_code == 404
    assert cliente.get("/pesquisas/nao-existe").status_code == 404


def test_limite_diario_e_cache_com_mongodb_real():
    """Mesma regra num MongoDB real: contador do dia e validade do cache."""
    import os
    from uuid import uuid4

    from src.dados.database import (
        ErroConexaoMongoDB,
        connect_to_mongodb,
        disconnect_from_mongodb,
    )
    from src.dados.repositorio import NOME_COLECAO_PESQUISAS, obter_colecao

    if os.getenv("SENTIA_TESTES_SEM_MONGODB") == "1":
        pytest.skip("MongoDB real desabilitado explicitamente nesta execução.")
    try:
        conexao = connect_to_mongodb(
            os.getenv("MONGODB_URI_TESTE", "mongodb://127.0.0.1:27017"), timeout_ms=1000
        )
    except ErroConexaoMongoDB:
        if os.getenv("CI"):
            pytest.fail("MongoDB de teste indisponível no CI.")
        pytest.skip("MongoDB de teste indisponível.")
    nome = f"sentia_limite_{uuid4().hex[:8]}"
    try:
        repo = RepositorioAnalises(obter_colecao(conexao, nome))
        agora = datetime(2026, 11, 26, 15, tzinfo=UTC)
        assert [repo.reservar_busca_x_publica("t", 2, agora) for _ in range(3)] == [
            True,
            True,
            False,
        ]
        assert repo.contar_buscas_x_publicas(agora) == 2

        repo.salvar_cache_pesquisa(
            "vacina",
            complementar_com_x=True,
            quantidade_solicitada=50,
            quantidade_atendida=10,
            esgotado_na_origem=True,
        )
        assert repo.buscar_cache_pesquisa("vacina") is not None
        conexao[nome][NOME_COLECAO_PESQUISAS].update_many(
            {}, {"$set": {"atualizado_em": datetime.now(UTC) - timedelta(days=31)}}
        )
        assert repo.buscar_cache_pesquisa("vacina") is None
    finally:
        conexao.drop_database(nome)
        disconnect_from_mongodb(conexao)
