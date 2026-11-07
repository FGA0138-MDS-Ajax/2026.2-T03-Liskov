"""Dashboard do Usuário (RF13). Filtros, gráficos, listagem e resumo ainda serão
adicionados (issues #14, #27, #28 e #29)."""

import streamlit as st

from src.apresentacao.componentes import estado_erro, estado_vazio
from src.apresentacao.config import carregar_configuracao
from src.apresentacao.contrato import ErroFonteDados, FiltrosAnalises
from src.apresentacao.fontes import criar_fonte


def renderizar() -> None:
    st.subheader("Análises de sentimentos")
    st.caption(
        "O sentimento exibido é uma previsão do modelo, não uma certeza sobre a "
        "opinião de quem escreveu o texto."
    )

    filtros = FiltrosAnalises()
    fonte = criar_fonte(carregar_configuracao())
    try:
        with st.spinner("Carregando análises..."):
            resumo = fonte.resumir(filtros)
    except ErroFonteDados as erro:
        estado_erro(str(erro))
        return

    if resumo.total == 0:
        estado_vazio("Nenhuma análise encontrada.")
        return
