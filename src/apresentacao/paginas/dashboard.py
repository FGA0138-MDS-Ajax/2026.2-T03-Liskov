"""Dashboard do Usuário (RF13): filtros, indicadores e listagem de análises (#27).
Gráfico e resumo textual ainda serão adicionados (issues #28 e #29)."""

import streamlit as st

from src.apresentacao.componentes import estado_erro, estado_vazio
from src.apresentacao.config import carregar_configuracao
from src.apresentacao.contrato import ErroFonteDados
from src.apresentacao.fontes import criar_fonte
from src.apresentacao.secoes import filtros, indicadores, listagem
from src.apresentacao.transformacoes import filtros_ativos, formatar_inteiro


def renderizar() -> None:
    st.subheader("Análises de sentimentos")
    st.caption(
        "O sentimento exibido é uma previsão do modelo, não uma certeza sobre a "
        "opinião de quem escreveu o texto."
    )

    filtros_aplicados = filtros.renderizar()
    fonte = criar_fonte(carregar_configuracao())
    try:
        with st.spinner("Carregando análises..."):
            resumo = fonte.resumir(filtros_aplicados)
    except ErroFonteDados as erro:
        estado_erro(str(erro))
        return

    if resumo.sem_data_publicacao:
        quantidade = formatar_inteiro(resumo.sem_data_publicacao)
        st.info(
            f"{quantidade} texto(s) sem data de publicação ficaram fora do filtro de "
            "período.",
            icon=":material/event_busy:",
        )

    if resumo.total == 0:
        estado_vazio(
            "Nenhuma análise encontrada para os filtros aplicados."
            if filtros_ativos(filtros_aplicados)
            else "Nenhuma análise encontrada."
        )
        return

    indicadores.renderizar(resumo)
    listagem.renderizar(fonte, filtros_aplicados, resumo.total)
