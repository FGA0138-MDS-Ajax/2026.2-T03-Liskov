"""Cálculos exibidos no painel (critério da issue #28: percentuais somam 100%)."""

from datetime import UTC, datetime

import pytest

from src.apresentacao.contrato import Analise, ResumoAnalises
from src.apresentacao.transformacoes import (
    COLUNAS_LISTAGEM,
    SEM_DATA,
    calcular_percentuais,
    descrever_intervalo,
    formatar_inteiro,
    limitar_pagina,
    montar_distribuicao,
    montar_linhas_listagem,
    total_de_paginas,
)


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


# --- Listagem de análises (#27) ---------------------------------------------------

ROTULOS = {"positivo": "Positivo", "neutro": "Neutro", "negativo": "Negativo"}


def _analise(**campos) -> Analise:
    base = {
        "id_origem": "a1",
        "fonte": "teste",
        "texto_original": "Texto de exemplo.",
        "sentimento": "positivo",
        "modelo_nome": "modelo-teste",
        "data_processamento": datetime(2026, 11, 10, 14, 5, tzinfo=UTC),
        "data_publicacao": datetime(2026, 10, 3, 23, 59, tzinfo=UTC),
    }
    return Analise(**{**base, **campos})


@pytest.mark.parametrize(
    ("total", "tamanho", "esperado"),
    [(0, 20, 1), (1, 20, 1), (20, 20, 1), (21, 20, 2), (1568, 20, 79), (-5, 20, 1)],
)
def test_total_de_paginas_nunca_e_menor_que_um(total, tamanho, esperado):
    assert total_de_paginas(total, tamanho) == esperado


@pytest.mark.parametrize("tamanho", [0, -1])
def test_tamanho_de_pagina_invalido_e_recusado(tamanho):
    with pytest.raises(ValueError):
        total_de_paginas(10, tamanho)


@pytest.mark.parametrize(
    ("pagina", "total", "esperado"),
    [(1, 50, 1), (3, 50, 3), (9, 50, 3), (0, 50, 1), (-2, 50, 1), (5, 0, 1)],
)
def test_pagina_fica_dentro_dos_limites(pagina, total, esperado):
    assert limitar_pagina(pagina, total, 20) == esperado


def test_intervalo_descrito_no_padrao_brasileiro():
    assert descrever_intervalo(1, 20, 1568, 20) == "Exibindo 1 a 20 de 1.568 análises."
    assert descrever_intervalo(79, 20, 1568, 8) == "Exibindo 1.561 a 1.568 de 1.568 análises."


def test_intervalo_sem_itens_nao_inventa_numeros():
    assert descrever_intervalo(1, 20, 0, 0) == "Nenhuma análise nesta página."
    assert descrever_intervalo(9, 20, 50, 0) == "Nenhuma análise nesta página."


def test_linha_da_listagem_tem_as_colunas_previstas_e_formatos_brasileiros():
    (linha,) = montar_linhas_listagem([_analise()], ROTULOS)
    assert tuple(linha) == COLUNAS_LISTAGEM
    assert linha["Sentimento"] == "Positivo"
    assert linha["Publicado em"] == "03/10/2026"
    assert linha["Processado em (UTC)"] == "10/11/2026 14:05"
    assert linha["Fonte"] == "teste"
    assert linha["Modelo"] == "modelo-teste"


def test_data_de_publicacao_ausente_nunca_e_inventada():
    (linha,) = montar_linhas_listagem([_analise(data_publicacao=None)], ROTULOS)
    assert linha["Publicado em"] == SEM_DATA


def test_mencoes_sao_mascaradas_na_listagem():
    (linha,) = montar_linhas_listagem(
        [_analise(texto_original="@fulano concordo com @ciclana, ok? a@b.com")], ROTULOS
    )
    assert linha["Texto"] == "@usuário concordo com @usuário, ok? a@b.com"


def test_lista_vazia_gera_zero_linhas():
    assert montar_linhas_listagem([], ROTULOS) == []


# --- Distribuição dos sentimentos (#28) --------------------------------------------


def test_distribuicao_tem_todas_as_classes_na_ordem_fixa():
    resumo = ResumoAnalises(total=10, por_sentimento={"negativo": 6, "positivo": 3, "neutro": 1})
    linhas = montar_distribuicao(resumo, ROTULOS)
    assert [l["Sentimento"] for l in linhas] == ["Positivo", "Neutro", "Negativo"]
    assert [l["Quantidade"] for l in linhas] == [3, 1, 6]
    assert sum(l["Percentual"] for l in linhas) == 100


def test_distribuicao_mostra_zero_em_vez_de_esconder_a_classe():
    resumo = ResumoAnalises(total=4, por_sentimento={"positivo": 4, "neutro": 0, "negativo": 0})
    linhas = montar_distribuicao(resumo, ROTULOS)
    assert [l["Quantidade"] for l in linhas] == [4, 0, 0]
    assert [l["Rótulo"] for l in linhas] == ["4 (100%)", "0 (0%)", "0 (0%)"]


def test_distribuicao_usa_o_formato_brasileiro_nos_milhares():
    resumo = ResumoAnalises(total=1568, por_sentimento={"positivo": 1000, "neutro": 400, "negativo": 168})
    assert montar_distribuicao(resumo, ROTULOS)[0]["Rótulo"] == "1.000 (64%)"


def test_distribuicao_com_classe_ausente_no_resumo_conta_zero():
    resumo = ResumoAnalises(total=2, por_sentimento={"positivo": 2})
    assert [l["Quantidade"] for l in montar_distribuicao(resumo, ROTULOS)] == [2, 0, 0]
