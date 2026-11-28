"""Páginas do painel, num lugar só: o menu (app.py) e os links entre páginas usam as mesmas."""

import streamlit as st


def pagina_dashboard() -> st.Page:
    from src.apresentacao.paginas import dashboard

    return st.Page(
        dashboard.renderizar,
        title="Dashboard",
        icon=":material/dashboard:",
        url_path="dashboard",
        default=True,
    )
