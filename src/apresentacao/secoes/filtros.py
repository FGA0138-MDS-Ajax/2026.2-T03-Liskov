"""Filtros de assunto (#113), período e sentimento (RF11, RF12).

Os filtros só mudam quando o usuário clica em "Aplicar filtros" e valem para todas
as seções. Quem filtra é a fonte de dados, nunca a tela.
"""

from dataclasses import replace

import streamlit as st

from src.apresentacao.componentes import estado_erro
from src.apresentacao.contrato import (
    SENTIMENTOS,
    TAMANHO_MAXIMO_TERMO,
    FiltrosAnalises,
    Sentimento,
)
from src.apresentacao.tema import ESTILOS_SENTIMENTO
from src.apresentacao.transformacoes import descrever_filtros, montar_filtros

CHAVE_FILTROS = "filtros_aplicados"
TODOS = "Todos"
ROTULOS: dict[Sentimento, str] = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}
_POR_ROTULO: dict[str, Sentimento] = {rotulo: s for s, rotulo in ROTULOS.items()}


def filtros_atuais() -> FiltrosAnalises:
    return st.session_state.get(CHAVE_FILTROS, FiltrosAnalises())


def _limpar_filtros() -> None:
    """Callback executado antes de renderizar os widgets, inclusive no navegador."""
    st.session_state[CHAVE_FILTROS] = FiltrosAnalises()
    st.session_state["filtro_assunto"] = ""
    st.session_state["filtro_inicio"] = None
    st.session_state["filtro_fim"] = None
    st.session_state["filtro_sentimento"] = TODOS


def _remover_assunto() -> None:
    """Callback: roda antes de desenhar os campos, então o campo de assunto já nasce vazio."""
    st.session_state[CHAVE_FILTROS] = replace(filtros_atuais(), assunto=None)
    st.session_state["filtro_assunto"] = ""


def renderizar() -> FiltrosAnalises:
    """Mostra o formulário e devolve os filtros aplicados."""
    with st.form("filtros", border=True, enter_to_submit=False):
        assunto = st.text_input(
            "Assunto",
            placeholder="Ex.: custo de vida",
            max_chars=TAMANHO_MAXIMO_TERMO,
            key="filtro_assunto",
            help=(
                "Mostra só os textos que falam do assunto. Maiúsculas e acentos não "
                "importam. Deixe vazio para ver todos os assuntos."
            ),
        )
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
        # Botões juntos numa linha, com a largura do próprio rótulo: nunca são cortados.
        with st.container(horizontal=True):
            aplicar = st.form_submit_button(
                "Aplicar filtros", type="primary", key="aplicar_filtros"
            )
            st.form_submit_button("Limpar", key="limpar_filtros", on_click=_limpar_filtros)

    if aplicar:
        try:
            st.session_state[CHAVE_FILTROS] = montar_filtros(
                inicio, fim, _POR_ROTULO.get(rotulo), assunto
            )
        except ValueError as erro:
            # Mantém os filtros anteriores para não mostrar dados que ninguém pediu.
            estado_erro(f"{erro} Os filtros anteriores foram mantidos.")

    filtros = filtros_atuais()
    if filtros.assunto:
        # Etiqueta removível do protótipo (#121): tira só o assunto e mantém o resto.
        texto, etiqueta = st.columns([3, 1], vertical_alignment="center")
        texto.caption(descrever_filtros(filtros, ROTULOS))
        etiqueta.button(
            f"Assunto: {filtros.assunto}",
            icon=":material/close:",
            on_click=_remover_assunto,
            key="remover_assunto",
            help="Remover só o filtro de assunto",
            type="tertiary",
        )
    else:
        st.caption(descrever_filtros(filtros, ROTULOS))
    return filtros
