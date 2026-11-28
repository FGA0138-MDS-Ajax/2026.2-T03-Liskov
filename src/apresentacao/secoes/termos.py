"""Termos mais frequentes (RF16, #30), em barras no lugar da nuvem de palavras (#121).

São as palavras que mais aparecem nos textos do filtro atual, e não os assuntos em alta
no X. Quem conta é a API (`GET /analises/termos`), sem palavras vazias, menções e links e
sem as palavras do próprio assunto filtrado. Barras se leem melhor que uma nuvem e não
pedem biblioteca nova. A tabela logo abaixo é a alternativa em texto.
"""

import altair as alt
import pandas as pd
import streamlit as st

from src.apresentacao.componentes import estado_erro
from src.apresentacao.contrato import (
    ErroFonteDados,
    FiltrosAnalises,
    FonteAnalises,
    TermosAnalises,
)
from src.apresentacao.tema import Paleta, paleta
from src.apresentacao.transformacoes import formatar_inteiro

LIMITE = 8


def construir_grafico(
    termos: TermosAnalises, cores: Paleta | None = None
) -> alt.LayerChart:
    """Barras horizontais com o número escrito; separado para poder ser testado."""
    cores = cores or paleta()
    dados = pd.DataFrame(
        [{"Termo": t.termo, "Quantidade": t.quantidade} for t in termos.termos]
    )
    maior = max(int(dados["Quantidade"].max()), 1)
    base = alt.Chart(dados).encode(
        y=alt.Y(
            "Termo:N",
            sort=None,
            title=None,
            axis=alt.Axis(
                domain=False,
                ticks=False,
                labelColor=cores.texto,
                labelFontSize=13,
                labelLimit=160,
            ),
        ),
        # Folga à direita para o número não ser cortado na barra maior.
        x=alt.X("Quantidade:Q", axis=None, scale=alt.Scale(domain=[0, maior * 1.25])),
        tooltip=["Termo:N", "Quantidade:Q"],
    )
    barras = base.mark_bar(color=cores.primaria, cornerRadiusEnd=4, height=12)
    rotulos = base.mark_text(
        align="left", dx=6, color=cores.texto_secundario, fontSize=12
    ).encode(text="Quantidade:Q")
    return (
        alt.layer(barras, rotulos)
        .properties(height=30 * len(dados), background="transparent")
        .configure_view(stroke=None)
    )


def renderizar(fonte: FonteAnalises, filtros: FiltrosAnalises) -> None:
    with st.container(border=True):
        st.markdown("##### Termos mais frequentes")
        st.caption(
            "Palavras que mais aparecem nos textos do filtro, sem palavras vazias, "
            "menções e links"
        )
        try:
            termos = fonte.termos(filtros, limite=LIMITE)
        except ErroFonteDados as erro:
            estado_erro(str(erro))
            return
        if not termos.termos:
            st.info(
                "Não há palavras para mostrar neste filtro.",
                icon=":material/search_off:",
            )
            return
        st.altair_chart(construir_grafico(termos), width="stretch")
        if termos.limitado:
            st.caption(
                f"Contados os {formatar_inteiro(termos.textos_lidos)} textos mais recentes, "
                f"de {formatar_inteiro(termos.total)}."
            )
        with st.expander("Ver os termos em tabela"):
            st.table(
                pd.DataFrame(
                    [
                        {"Termo": t.termo, "Quantidade": t.quantidade}
                        for t in termos.termos
                    ]
                )
            )
