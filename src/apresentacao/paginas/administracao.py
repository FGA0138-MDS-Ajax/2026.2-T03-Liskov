"""Área do Administrador (RF01, RF02, T01 a T03). Ainda não implementada."""

import streamlit as st

from src.apresentacao.componentes import estado_vazio


def renderizar() -> None:
    st.subheader("Administração")
    estado_vazio(
        "Esta área ainda não foi implementada. Importação de datasets e coleta "
        "dependem da API e da decisão sobre o acesso do Administrador."
    )
