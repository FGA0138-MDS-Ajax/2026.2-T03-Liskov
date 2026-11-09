"""Ponto de entrada do painel: streamlit run src/apresentacao/app.py"""

import sys
from pathlib import Path

# `streamlit run` só inclui a pasta deste arquivo no caminho de importação.
RAIZ_PROJETO = str(Path(__file__).resolve().parents[2])
if RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, RAIZ_PROJETO)

import streamlit as st

from src.apresentacao.componentes import aviso_dados_de_exemplo, estado_erro
from src.apresentacao.config import carregar_configuracao
from src.apresentacao.paginas import administracao, dashboard

st.set_page_config(page_title="SentIA", page_icon=":material/sentiment_satisfied:", layout="wide")
st.title("SentIA")

try:
    config = carregar_configuracao()
except ValueError as erro:
    estado_erro(f"Configuração inválida: {erro}")
    st.stop()

if config.fonte_dados == "mock":
    aviso_dados_de_exemplo()

pagina = st.navigation(
    [
        st.Page(
            dashboard.renderizar,
            title="Dashboard",
            icon=":material/dashboard:",
            url_path="dashboard",
            default=True,
        ),
        st.Page(
            administracao.renderizar,
            title="Administração",
            icon=":material/settings:",
            url_path="administracao",
        ),
    ]
)
pagina.run()
