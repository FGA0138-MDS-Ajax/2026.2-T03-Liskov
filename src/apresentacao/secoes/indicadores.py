"""Indicadores de total e percentual por sentimento (RF13, RF14)."""

import streamlit as st

from src.apresentacao.componentes import cartao_indicador
from src.apresentacao.contrato import SENTIMENTOS, ResumoAnalises
from src.apresentacao.tema import ESTILOS_SENTIMENTO
from src.apresentacao.transformacoes import calcular_percentuais, formatar_inteiro


def renderizar(resumo: ResumoAnalises) -> None:
    percentuais = calcular_percentuais(resumo.por_sentimento)
    # Em telas estreitas o Streamlit empilha as colunas, sem rolagem horizontal.
    colunas = st.columns(1 + len(SENTIMENTOS))
    with colunas[0]:
        cartao_indicador(":material/description: Analisados", formatar_inteiro(resumo.total))
    for coluna, sentimento in zip(colunas[1:], SENTIMENTOS):
        estilo = ESTILOS_SENTIMENTO[sentimento]
        with coluna:
            # Rótulo e ícone acompanham a cor: o sentimento nunca depende só dela.
            cartao_indicador(
                f":{estilo.cor_markdown}[{estilo.icone}] {estilo.rotulo}",
                f"{percentuais[sentimento]}%",
            )
