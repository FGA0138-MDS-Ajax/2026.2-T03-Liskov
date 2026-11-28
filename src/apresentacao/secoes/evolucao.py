"""Evolução no período (#121; a D4 mudou em 27/11): análises por dia, semana ou mês.

Só entram textos com data de publicação (o TweetSentBR não tem data); a seção diz quantos
ficaram de fora. A API agrupa no MongoDB, em UTC (D12), e a semana começa na segunda-feira.
Uma linha por sentimento, com o nome no tooltip e na tabela logo abaixo: a informação não
depende só da cor.
"""

import altair as alt
import pandas as pd
import streamlit as st

from src.apresentacao.componentes import estado_erro
from src.apresentacao.contrato import (
    GRANULARIDADES,
    SENTIMENTOS,
    ErroFonteDados,
    EvolucaoAnalises,
    FiltrosAnalises,
    FonteAnalises,
)
from src.apresentacao.tema import ESTILOS_SENTIMENTO, Paleta, paleta
from src.apresentacao.transformacoes import formatar_inteiro

ROTULOS = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}
ORDEM = [ROTULOS[s] for s in SENTIMENTOS]
CHAVE_GRANULARIDADE = "evolucao_granularidade"
FORMATO = {"dia": "%d/%m", "semana": "%d/%m", "mes": "%m/%Y"}


def _linhas(evolucao: EvolucaoAnalises) -> list[dict[str, object]]:
    return [
        {
            "Período": pd.Timestamp(ponto.periodo),
            "Sentimento": ROTULOS[s],
            "Quantidade": ponto.por_sentimento.get(s, 0),
        }
        for ponto in evolucao.pontos
        for s in SENTIMENTOS
    ]


def construir_grafico(
    evolucao: EvolucaoAnalises, cores: Paleta | None = None
) -> alt.Chart:
    """Uma linha por sentimento; separado da renderização para poder ser testado."""
    cores = cores or paleta()
    formato = FORMATO[evolucao.granularidade]
    return (
        alt.Chart(pd.DataFrame(_linhas(evolucao)))
        .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=40))
        .encode(
            x=alt.X(
                "Período:T",
                title=None,
                axis=alt.Axis(
                    format=formato,
                    grid=False,
                    labelAngle=0,
                    labelColor=cores.texto_secundario,
                ),
            ),
            y=alt.Y(
                "Quantidade:Q",
                title=None,
                # Contagem de textos: só números inteiros no eixo.
                axis=alt.Axis(
                    tickCount=4,
                    format="d",
                    tickMinStep=1,
                    labelColor=cores.texto_secundario,
                    gridColor=cores.borda,
                ),
            ),
            color=alt.Color(
                "Sentimento:N",
                scale=alt.Scale(
                    domain=ORDEM, range=[cores.grafico[s] for s in SENTIMENTOS]
                ),
                legend=alt.Legend(orient="bottom", title=None, labelColor=cores.texto),
            ),
            tooltip=[
                alt.Tooltip("Período:T", format="%d/%m/%Y"),
                "Sentimento:N",
                "Quantidade:Q",
            ],
        )
        .properties(height=230, background="transparent")
        .configure_view(stroke=None)
    )


def renderizar(fonte: FonteAnalises, filtros: FiltrosAnalises) -> None:
    with st.container(border=True):
        st.markdown("##### Evolução no período")
        st.caption("Só textos com data de publicação · datas em UTC")
        granularidade = (
            st.segmented_control(
                "Agrupar por",
                list(GRANULARIDADES),
                format_func=GRANULARIDADES.get,
                default="semana",
                key=CHAVE_GRANULARIDADE,
            )
            or "semana"
        )
        try:
            evolucao = fonte.evolucao(filtros, granularidade)
        except ErroFonteDados as erro:
            estado_erro(str(erro))
            return
        if not evolucao.pontos:
            st.info("Nenhum texto com data neste filtro.", icon=":material/event_busy:")
        else:
            st.altair_chart(construir_grafico(evolucao), width="stretch")
            with st.expander("Ver a evolução em tabela"):
                tabela = pd.DataFrame(
                    [
                        {
                            "Período": ponto.periodo.strftime("%d/%m/%Y"),
                            **{
                                ROTULOS[s]: ponto.por_sentimento.get(s, 0)
                                for s in SENTIMENTOS
                            },
                        }
                        for ponto in evolucao.pontos
                    ]
                )
                st.table(tabela)
        if evolucao.sem_data_publicacao:
            st.caption(
                f"{formatar_inteiro(evolucao.sem_data_publicacao)} texto(s) sem data de "
                "publicação ficaram fora do gráfico."
            )
