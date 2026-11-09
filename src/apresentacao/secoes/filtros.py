"""Filtros de período e sentimento (RF11, RF12).

Os filtros só mudam quando o usuário clica em "Aplicar filtros" e valem para todas
as seções. Quem filtra é a fonte de dados, nunca a tela.
"""

import streamlit as st

from src.apresentacao.componentes import estado_erro
from src.apresentacao.contrato import SENTIMENTOS, FiltrosAnalises, Sentimento
from src.apresentacao.tema import ESTILOS_SENTIMENTO
from src.apresentacao.transformacoes import descrever_filtros, montar_filtros

CHAVE_FILTROS = "filtros_aplicados"
TODOS = "Todos"
ROTULOS: dict[Sentimento, str] = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}
_POR_ROTULO: dict[str, Sentimento] = {rotulo: s for s, rotulo in ROTULOS.items()}


def filtros_atuais() -> FiltrosAnalises:
    return st.session_state.get(CHAVE_FILTROS, FiltrosAnalises())


def renderizar() -> FiltrosAnalises:
    """Mostra o formulário e devolve os filtros aplicados."""
    with st.form("filtros", border=True, enter_to_submit=False):
        col_inicio, col_fim, col_sentimento = st.columns(3)
        with col_inicio:
            inicio = st.date_input(
                "Publicado a partir de",
                value=None,
                format="DD/MM/YYYY",
                key="filtro_inicio",
                help="Deixe vazio para não limitar o início do período.",
            )
        with col_fim:
            fim = st.date_input(
                "Publicado até",
                value=None,
                format="DD/MM/YYYY",
                key="filtro_fim",
                help="Data incluída no resultado. Deixe vazio para não limitar o fim.",
            )
        with col_sentimento:
            rotulo = st.selectbox(
                "Sentimento", [TODOS, *ROTULOS.values()], key="filtro_sentimento"
            )
        col_aplicar, col_limpar, _ = st.columns([1, 1, 4])
        with col_aplicar:
            aplicar = st.form_submit_button(
                "Aplicar filtros", type="primary", key="aplicar_filtros"
            )
        with col_limpar:
            limpar = st.form_submit_button("Limpar", key="limpar_filtros")

    if limpar:
        st.session_state[CHAVE_FILTROS] = FiltrosAnalises()
        for chave in ("filtro_inicio", "filtro_fim", "filtro_sentimento"):
            st.session_state.pop(chave, None)
        st.rerun()
    if aplicar:
        try:
            st.session_state[CHAVE_FILTROS] = montar_filtros(
                inicio, fim, _POR_ROTULO.get(rotulo)
            )
        except ValueError as erro:
            # Mantém os filtros anteriores para não mostrar dados que ninguém pediu.
            estado_erro(f"{erro} Os filtros anteriores foram mantidos.")

    filtros = filtros_atuais()
    st.caption(descrever_filtros(filtros, ROTULOS))
    return filtros
