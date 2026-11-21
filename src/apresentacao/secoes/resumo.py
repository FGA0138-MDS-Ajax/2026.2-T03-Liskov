"""Resumo textual das análises (RF15, US16).

Mostra, em linguagem natural, o total, a distribuição por sentimento e a predominância
da seleção atual. O texto é montado por regras a partir do mesmo resumo dos indicadores
e do gráfico, sem modelo de linguagem, então nunca diverge deles nem inventa inferências.
"""

import streamlit as st

from src.apresentacao.contrato import SENTIMENTOS, FiltrosAnalises, ResumoAnalises
from src.apresentacao.tema import ESTILOS_SENTIMENTO
from src.apresentacao.transformacoes import montar_resumo_textual

ROTULOS = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}


def renderizar(resumo: ResumoAnalises, filtros: FiltrosAnalises) -> None:
    st.subheader("Resumo")
    with st.container(border=True):
        st.write(montar_resumo_textual(resumo, filtros, ROTULOS))
