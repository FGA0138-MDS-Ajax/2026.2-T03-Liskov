"""Cálculos exibidos no painel (critério da issue #28: percentuais somam 100%)."""

import pytest

from src.apresentacao.transformacoes import calcular_percentuais, formatar_inteiro


@pytest.mark.parametrize(
    "contagens",
    [
        {"positivo": 1, "neutro": 1, "negativo": 1},
        {"positivo": 2, "neutro": 2, "negativo": 3},
        {"positivo": 8, "neutro": 4, "negativo": 5},
        {"positivo": 1, "neutro": 0, "negativo": 0},
        {"positivo": 1, "neutro": 998, "negativo": 1},
    ],
)
def test_percentuais_somam_exatamente_100(contagens):
    assert sum(calcular_percentuais(contagens).values()) == 100


def test_percentuais_exatos_nao_sao_alterados():
    assert calcular_percentuais({"positivo": 50, "neutro": 30, "negativo": 20}) == {
        "positivo": 50,
        "neutro": 30,
        "negativo": 20,
    }


def test_percentuais_sem_registros_sao_zero():
    assert calcular_percentuais({}) == {"positivo": 0, "neutro": 0, "negativo": 0}


@pytest.mark.parametrize(
    ("valor", "esperado"), [(0, "0"), (999, "999"), (1568, "1.568"), (1234567, "1.234.567")]
)
def test_formatar_inteiro_no_padrao_brasileiro(valor, esperado):
    assert formatar_inteiro(valor) == esperado
