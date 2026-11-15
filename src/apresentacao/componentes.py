"""Componentes de interface reutilizáveis entre as páginas do painel."""

import streamlit as st

MENSAGEM_DADOS_DE_EXEMPLO = (
    "**Dados de exemplo.** Os valores desta tela são fictícios e não vêm da API nem "
    "de análises reais."
)


def aviso_dados_de_exemplo() -> None:
    st.warning(MENSAGEM_DADOS_DE_EXEMPLO, icon=":material/science:")


def cartao_indicador(rotulo: str, valor: str) -> None:
    st.metric(label=rotulo, value=valor, border=True)


def estado_vazio(mensagem: str) -> None:
    st.info(mensagem, icon=":material/search_off:")


def estado_erro(mensagem: str) -> None:
    st.error(mensagem, icon=":material/error:")
