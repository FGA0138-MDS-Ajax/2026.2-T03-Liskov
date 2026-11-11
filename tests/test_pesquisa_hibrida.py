"""Regras da pesquisa híbrida local (src/servico/pesquisa.py)."""

import pytest

from src.servico.pesquisa import pesquisar, pontuar, termos_da_consulta


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
