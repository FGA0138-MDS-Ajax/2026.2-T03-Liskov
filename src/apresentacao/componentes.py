"""Componentes de interface reutilizáveis entre as páginas do painel."""

import streamlit as st

MENSAGEM_DADOS_DE_EXEMPLO = (
    "**Dados de exemplo.** Os valores desta tela são fictícios e não vêm da API nem "
    "de análises reais."
)


def aviso_dados_de_exemplo() -> None:
    st.warning(MENSAGEM_DADOS_DE_EXEMPLO, icon=":material/science:")


def cartao_indicador(
    rotulo: str,
    valor: str,
    detalhe: str | None = None,
    fracao: float | None = None,
) -> None:
    """Cartão do wireframe: número grande, barra de proporção e uma linha de detalhe.

    A barra é nativa (`st.progress`) e acompanha o tema; o valor escrito no cartão e o
    rótulo dizem o mesmo que ela, então a informação nunca depende só da cor.
    """
    with st.container(border=True):
        st.metric(label=rotulo, value=valor)
        if fracao is not None:
            st.progress(min(max(fracao, 0.0), 1.0))
        if detalhe:
            st.caption(detalhe)


def estado_vazio(mensagem: str) -> None:
    st.info(mensagem, icon=":material/search_off:")


def estado_erro(mensagem: str) -> None:
    st.error(mensagem, icon=":material/error:")
