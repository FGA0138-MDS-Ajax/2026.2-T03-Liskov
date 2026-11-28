"""Regra de busca por palavras (src/comum/busca_textual.py), usada pela #113.

O ponto central: a expressão regular enviada ao MongoDB precisa decidir exatamente
como a regra em Python (``corresponde``), que é a mesma da pesquisa do Administrador.
"""

import re

import pytest

from src.comum.busca_textual import (
    corresponde,
    minimo_de_termos,
    padrao_do_termo,
    relevancia_minima,
    termos_da_consulta,
)

TEXTOS = [
    "A vacinação infantil começou hoje.",
    "VACINAS chegaram ao posto; Vacinacao amanhã.",
    "Pré-vacina e pós-vacinação: o que muda?",
    "O custo de vida subiu de novo em Brasília.",
    "Custo alto, vida difícil",
    "golpe no gol? GOL! gols",
    "Saúde pública e SAUDE privada",
    "#SaudeMental importa @ministerio_saude",
    "copa_do_mundo 2026 começa em 2026!",
    "ação, AÇÃO, acao e Ação",
    "Ele não vai; eu NÃO vou.",
    "Trump e o trumpismo",
    "Texto sem nada a ver.",
    "dívida pública gigante",
    "emoji 🎉 vacina🎉 e café☕",
    "",
]
CONSULTAS = [
    "vacina",
    "Vacinação",
    "custo de vida",
    "gol",
    "saúde",
    "SAUDE mental",
    "2026",
    "ação",
    "não",
    "Trump",
    "dívida pública",
    "copa do mundo brasil seleção",
    "o de",
    "café",
    "(",
    ".*",
    "a+b",
]


def _corresponde_por_regex(consulta: str, texto: str) -> bool:
    termos = termos_da_consulta(consulta)
    if not termos:
        return False
    presentes = sum(bool(re.search(padrao_do_termo(t), texto)) for t in termos)
    return presentes >= minimo_de_termos(termos)


@pytest.mark.parametrize("consulta", CONSULTAS)
def test_expressao_regular_decide_igual_a_regra_em_python(consulta):
    for texto in TEXTOS:
        assert _corresponde_por_regex(consulta, texto) == corresponde(
            consulta, texto
        ), texto


@pytest.mark.parametrize(
    ("consulta", "texto", "esperado"),
    [
        ("Vacinação", "vacinacao em massa", True),
        ("vacinacao", "A VACINAÇÃO começou", True),
        ("vacina", "vacinas e vacinação", True),  # mesmo radical
        ("gol", "golpe no meio-campo", False),  # termo curto exige a palavra inteira
        ("gol", "foi GOL!", True),
        ("custo de vida", "o custo da vida", True),  # "de" é palavra vazia
        ("custo de vida", "custo alto", False),  # até 3 termos: todos precisam aparecer
        ("(", "qualquer (texto)", False),  # sem palavras: nada corresponde
    ],
)
def test_casos_da_regra(consulta, texto, esperado):
    assert corresponde(consulta, texto) is esperado


@pytest.mark.parametrize("total", range(1, 13))
def test_minimo_de_termos_e_a_relevancia_minima_em_inteiro(total):
    termos = [f"termo{i}" for i in range(total)]
    minimo = minimo_de_termos(termos)
    assert minimo / total >= relevancia_minima(termos)
    assert (minimo - 1) / total < relevancia_minima(termos)


@pytest.mark.parametrize("digitado", [".*", "a+b", "(x)", "[abc]", "\\d", "$1", "a|b"])
def test_texto_digitado_nunca_vira_expressao_regular(digitado):
    for termo in termos_da_consulta(digitado) or [digitado]:
        padrao = padrao_do_termo(termo)
        re.compile(padrao)  # nunca quebra
        assert not re.search(padrao, "zzzzzzzz")
