"""Gráfico de distribuição dos sentimentos (RF14, US15), em rosca (#121).

Usa o mesmo resumo dos indicadores, então os números nunca divergem deles. O centro da
rosca mostra o total; a legenda escreve nome, quantidade e percentual de cada sentimento,
e uma tabela com os mesmos dados fica logo abaixo. O sentimento nunca depende só da cor.
As cores vêm da paleta do tema ativo (claro ou escuro).
"""

import altair as alt
import pandas as pd
import streamlit as st

from src.apresentacao.contrato import SENTIMENTOS, ResumoAnalises
from src.apresentacao.tema import ESTILOS_SENTIMENTO, Paleta, paleta
from src.apresentacao.transformacoes import formatar_inteiro, montar_distribuicao

ROTULOS = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}
ORDEM = [ROTULOS[s] for s in SENTIMENTOS]
FONTE = "Source Sans Pro, Source Sans 3, sans-serif"  # a fonte padrão do Streamlit


def cores(cores_tema: Paleta) -> list[str]:
    return [cores_tema.grafico[s] for s in SENTIMENTOS]


def construir_grafico(
    linhas: list[dict[str, str | int]], cores_tema: Paleta | None = None
) -> alt.LayerChart:
    """Monta a rosca; separado da renderização para poder ser testado."""
    cores_tema = cores_tema or paleta()
    dados = pd.DataFrame(linhas).assign(Ordem=range(len(linhas)))
    total = int(dados["Quantidade"].sum())
    arco = (
        alt.Chart(dados)
        .mark_arc(innerRadius=62, outerRadius=92, padAngle=0.012)
        .encode(
            theta=alt.Theta("Quantidade:Q", stack=True),
            color=alt.Color(
                "Sentimento:N",
                scale=alt.Scale(domain=ORDEM, range=cores(cores_tema)),
                legend=None,
            ),
            order="Ordem:O",
            tooltip=["Sentimento:N", "Quantidade:Q", "Percentual:Q"],
        )
    )
    centro = (
        alt.Chart(pd.DataFrame({"t": [formatar_inteiro(total)]}))
        .mark_text(fontSize=26, fontWeight=600, color=cores_tema.texto, dy=-6, font=FONTE)
        .encode(text="t:N")
    )
    legenda = (
        alt.Chart(pd.DataFrame({"t": ["análises"]}))
        .mark_text(fontSize=12, color=cores_tema.texto_secundario, dy=16, font=FONTE)
        .encode(text="t:N")
    )
    return (
        alt.layer(arco, centro, legenda)
        .properties(width=200, height=200, background="transparent")
        .configure_view(stroke=None)
    )


def renderizar(resumo: ResumoAnalises) -> None:
    linhas = montar_distribuicao(resumo, ROTULOS)
    with st.container(border=True):
        st.markdown("##### Distribuição dos sentimentos")
        st.caption("Quantidade de análises por sentimento")
        with st.container(horizontal_alignment="center"):
            st.altair_chart(construir_grafico(linhas), width="content")
        for sentimento, linha in zip(SENTIMENTOS, linhas):
            estilo = ESTILOS_SENTIMENTO[sentimento]
            st.markdown(
                f":{estilo.cor_markdown}[:material/circle:] {estilo.rotulo}: "
                f"**{formatar_inteiro(int(linha['Quantidade']))}** ({linha['Percentual']}%)"
            )
        with st.expander("Ver os dados do gráfico em tabela"):
            st.table(
                pd.DataFrame(linhas, columns=["Sentimento", "Quantidade", "Percentual"]).assign(
                    Percentual=lambda d: d["Percentual"].astype(str) + "%"
                )
            )
