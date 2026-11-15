"""Testes de normalização dos rótulos e validação das métricas."""

import pytest

from src.processamento.classificacao.avaliacao import avaliar


def test_avaliacao_reconhece_rotulos_equivalentes():
    # Siglas e nomes em português tem que representar as mesmas classes.
    resultado = avaliar(
        ["POS", "NEG", "NEU"],
        [" positivo ", "NEGATIVO", "neutro"],
    )

    assert resultado["acuracia"] == pytest.approx(1.0)
    assert resultado["f1_macro"] == pytest.approx(1.0)

    # Linhas: respostas corretas, colunas: previsões
    # Ordem: positivo, negativo, neutro
    assert resultado["matriz_confusao"] == [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]


def test_avaliacao_contabiliza_previsao_incorreta():
    # Primeira previsão ta errada, as outras duas estão corretas.
    resultado = avaliar(
        ["POS", "NEG", "NEU"],
        ["NEG", "NEG", "NEU"],
    )

    assert resultado["acuracia"] == pytest.approx(2 / 3)
    assert resultado["f1_macro"] == pytest.approx(5 / 9)
    assert resultado["matriz_confusao"] == [
        [0, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]


@pytest.mark.parametrize("entrada,erro", [
    ([], ValueError),
    (["POS", "NEG"], ValueError),
    (["desconhecido"], ValueError),
    ([None], TypeError),
    ("POS", TypeError),
    ({"POS": 1}, TypeError),
    (None, TypeError),
])
@pytest.mark.parametrize("lado", [0, 1])
def test_avaliacao_rejeita_entradas_invalidas(entrada, erro, lado):
    # Repete cada caso nas respostas corretas e nas previsões.
    argumentos = [["POS"], ["POS"]]
    argumentos[lado] = entrada

    with pytest.raises(erro):
        avaliar(*argumentos)