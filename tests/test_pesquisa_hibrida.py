"""Regras da pesquisa híbrida local (src/servico/pesquisa.py)."""

import pytest

from src.servico.pesquisa import chave, pesquisar, pontuar, termos_da_consulta


def test_consulta_ignora_palavras_vazias_e_acentos():
    assert termos_da_consulta("O preço das coisas não está aumentando") == [
        "preco",
        "coisas",
        "aumentando",
    ]


def test_consulta_so_com_palavras_vazias_usa_todas():
    assert termos_da_consulta("de o") == ["de", "o"]


@pytest.mark.parametrize(
    ("consulta", "texto", "esperado"),
    [
        ("vacina", "Campanha de vacinação começa hoje", 1.0),
        ("VACINAÇÃO", "fila para tomar vacinas", 1.0),
        ("custo de vida", "O custo do aluguel subiu", 0.5),
        ("futebol", "Choveu o dia todo", 0.0),
    ],
)
def test_pontuacao_flexivel(consulta, texto, esperado):
    assert pontuar(termos_da_consulta(consulta), texto) == esperado


def _registro(i, texto, fonte="teste"):
    return {"id_origem": i, "texto_original": texto, "fonte": fonte}


def test_consulta_curta_exige_todos_os_termos_e_nao_repete():
    base = [
        _registro("1", "O custo do aluguel subiu"),
        _registro("2", "Custo de vida está alto demais"),
        _registro("2", "Custo de vida está alto demais"),
        _registro("3", "Ele é muito inteligente"),
    ]
    resultado = pesquisar("custo de vida", 5, base, buscar_x=None, complementar_com_x=False)
    assert [r["id_origem"] for r in resultado.da_base] == ["2"]
    sem_ia = pesquisar("inteligência artificial", 5, base, buscar_x=None, complementar_com_x=False)
    assert sem_ia.da_base == []


def test_consulta_longa_aceita_dois_tercos_dos_termos():
    base = [
        _registro("1", "preço do arroz e do feijão subiu no mercado"),
        _registro("2", "o feijão acabou"),
    ]
    resultado = pesquisar(
        "preço arroz feijão mercado", 5, base, buscar_x=None, complementar_com_x=False
    )
    assert [r["id_origem"] for r in resultado.da_base] == ["1"]


def test_meta_limita_os_textos_da_base():
    base = [_registro(str(i), "vacina") for i in range(10)]
    resultado = pesquisar("vacina", 4, base, buscar_x=None, complementar_com_x=True)
    assert len(resultado.da_base) == 4
    assert resultado.aviso is None


def test_reutiliza_cache_quando_origem_esgotada_ou_meta_coberta():
    chamadas = []

    def x_spy(consulta, qtd):
        chamadas.append((consulta, qtd))
        return [_registro("x1", "sobre tema raro", fonte="X")]

    base = [_registro("b1", "tema raro")]
    resultado_esgotado = pesquisar(
        "tema raro",
        5,
        base,
        buscar_x=x_spy,
        complementar_com_x=True,
        cache_pesquisa={"quantidade_solicitada": 5, "esgotado_na_origem": True},
    )
    assert chamadas == []
    assert resultado_esgotado.cache_reutilizado is True
    assert resultado_esgotado.esgotado_na_origem is True
    assert [r["id_origem"] for r in resultado_esgotado.registros] == ["b1"]

    resultado_coberto = pesquisar(
        "tema raro",
        3,
        base,
        buscar_x=x_spy,
        complementar_com_x=True,
        cache_pesquisa={"quantidade_solicitada": 4, "esgotado_na_origem": False},
    )
    assert chamadas == []
    assert resultado_coberto.cache_reutilizado is True

    # Meta maior que o cache não esgotado consulta novamente o XFetch.
    resultado_maior = pesquisar(
        "tema raro",
        6,
        base,
        buscar_x=x_spy,
        complementar_com_x=True,
        cache_pesquisa={"quantidade_solicitada": 3, "esgotado_na_origem": False},
    )
    assert chamadas == [("tema raro", 5)]
    assert resultado_maior.consultou_x is True
    assert resultado_maior.esgotado_na_origem is True  # retornou 1 < 5


def test_forcar_atualizacao_ignora_cache_e_consulta_x():
    chamadas = []

    def x_spy(consulta, qtd):
        chamadas.append((consulta, qtd))
        return [_registro("x_novo", "texto vacina atualizado", fonte="X")]

    base = [_registro("b1", "vacina"), _registro("b2", "vacina")]
    resultado = pesquisar(
        "vacina",
        2,
        base,
        buscar_x=x_spy,
        complementar_com_x=True,
        cache_pesquisa={"quantidade_solicitada": 2, "esgotado_na_origem": True},
        forcar_atualizacao=True,
    )
    assert chamadas == [("vacina", 2)]
    assert resultado.consultou_x is True
    assert resultado.cache_reutilizado is False
    assert [r["id_origem"] for r in resultado.do_x] == ["x_novo"]
    assert len(resultado.registros) == 2


def test_chave_gera_fallback_deterministico_quando_id_origem_ausente():
    r1 = {"fonte": "X", "texto_original": "Sem ID", "data_publicacao": "2026-11-01T10:00:00Z"}
    r2 = {"fonte": "X", "texto_original": "Sem ID", "data_publicacao": "2026-11-01T10:00:00Z"}
    r3 = {"fonte": "X", "id_origem": "  ", "texto_original": "Outro texto"}
    assert chave(r1) == chave(r2)
    assert chave(r1)[1].startswith("auto_")
    assert chave(r1) != chave(r3)
