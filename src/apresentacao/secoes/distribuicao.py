"""Gráfico de distribuição dos sentimentos (RF14, US15).

Barras horizontais com a quantidade de análises de cada sentimento no filtro aplicado.
O gráfico usa o mesmo resumo dos indicadores, então os números nunca divergem deles.
Acessibilidade: o sentimento é identificado pelo nome e pelo valor escrito em cada barra,
nunca só pela cor, e uma tabela com os mesmos dados fica disponível logo abaixo.
"""

import altair as alt
import pandas as pd
import streamlit as st

from src.apresentacao.contrato import SENTIMENTOS, ResumoAnalises
from src.apresentacao.tema import ESTILOS_SENTIMENTO
from src.apresentacao.transformacoes import montar_distribuicao

ROTULOS = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}
ORDEM = [ROTULOS[s] for s in SENTIMENTOS]
CORES = [ESTILOS_SENTIMENTO[s].cor_grafico for s in SENTIMENTOS]


def construir_grafico(linhas: list[dict[str, str | int]]) -> alt.LayerChart:
    """Monta o gráfico; separado da renderização para poder ser testado."""
    dados = pd.DataFrame(linhas)
    maior = int(dados["Quantidade"].max())
    base = alt.Chart(dados).encode(
        y=alt.Y(
            "Sentimento:N", sort=ORDEM, title=None, axis=alt.Axis(labelFontSize=14, labelLimit=140)
        ),
        x=alt.X(
            "Quantidade:Q",
            axis=None,
            # Folga à direita para o valor escrito não ser cortado na barra maior.
            scale=alt.Scale(domain=[0, max(maior, 1) * 1.3]),
        ),
        color=alt.Color(
            "Sentimento:N", scale=alt.Scale(domain=ORDEM, range=CORES), legend=None
        ),
        tooltip=["Sentimento:N", "Quantidade:Q", "Percentual:Q"],
    )
    barras = base.mark_bar()
    # A cor fixa vai no encode: a cor por sentimento do `base` sobrescreveria a do mark.
    valores = base.mark_text(align="left", dx=6, fontSize=14).encode(
        text="Rótulo:N", color=alt.value("#1F2937")
    )
    return (barras + valores).properties(
        height=160, title="Quantidade de análises por sentimento"
    )


def renderizar(resumo: ResumoAnalises) -> None:
    st.subheader("Distribuição dos sentimentos")
    linhas = montar_distribuicao(resumo, ROTULOS)
    st.altair_chart(construir_grafico(linhas), width="stretch")
    with st.expander("Ver os dados do gráfico em tabela"):
        st.table(
            pd.DataFrame(linhas, columns=["Sentimento", "Quantidade", "Percentual"]).assign(
                Percentual=lambda d: d["Percentual"].astype(str) + "%"
            )
        )
