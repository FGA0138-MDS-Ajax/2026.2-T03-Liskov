"""Resumo textual das análises (RF15, US16), com barra de proporção (#121).

Mostra, em linguagem natural, o total, a distribuição por sentimento e a predominância
da seleção atual. O texto é montado por regras a partir do mesmo resumo dos indicadores
e do gráfico, sem modelo de linguagem, então nunca diverge deles nem inventa inferências.
A barra repete a distribuição do texto; ela não traz informação nova, só a resume.
"""

import altair as alt
import pandas as pd
import streamlit as st

from src.apresentacao.contrato import SENTIMENTOS, FiltrosAnalises, ResumoAnalises
from src.apresentacao.tema import ESTILOS_SENTIMENTO, Paleta, paleta
from src.apresentacao.transformacoes import montar_distribuicao, montar_resumo_textual

ROTULOS = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}
ORDEM = [ROTULOS[s] for s in SENTIMENTOS]


def construir_barra(
    resumo: ResumoAnalises, cores_tema: Paleta | None = None
) -> alt.Chart:
    """Barra 100% empilhada; separada da renderização para poder ser testada."""
    cores_tema = cores_tema or paleta()
    dados = pd.DataFrame(montar_distribuicao(resumo, ROTULOS)).assign(
        Ordem=range(len(SENTIMENTOS))
    )
    return (
        alt.Chart(dados)
        .mark_bar(height=14)
        .encode(
            x=alt.X("Quantidade:Q", stack="normalize", axis=None),
            color=alt.Color(
                "Sentimento:N",
                scale=alt.Scale(
                    domain=ORDEM, range=[cores_tema.grafico[s] for s in SENTIMENTOS]
                ),
                legend=None,
            ),
            order="Ordem:O",
            tooltip=["Sentimento:N", "Quantidade:Q", "Percentual:Q"],
        )
        .properties(height=18, background="transparent")
        .configure_view(stroke=None)
    )


def renderizar(resumo: ResumoAnalises, filtros: FiltrosAnalises) -> None:
    with st.container(border=True):
        st.markdown("##### Resumo")
        st.markdown(montar_resumo_textual(resumo, filtros, ROTULOS))
        if resumo.total:
            st.altair_chart(construir_barra(resumo), width="stretch")
