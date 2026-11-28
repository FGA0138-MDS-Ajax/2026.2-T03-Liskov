"""Dashboard do Usuário (RF13): filtros, indicadores, gráfico de distribuição (#28),
resumo textual (#29) e listagem de análises (#27)."""

from dataclasses import replace

import streamlit as st

from src.apresentacao.componentes import estado_erro, estado_vazio
from src.apresentacao.config import carregar_configuracao
from src.apresentacao.contrato import ErroFonteDados
from src.apresentacao.fontes import criar_administracao, criar_fonte
from src.apresentacao.secoes import (
    busca_x,
    distribuicao,
    filtros,
    indicadores,
    listagem,
)
from src.apresentacao.secoes import resumo as secao_resumo
from src.apresentacao.transformacoes import filtros_ativos, formatar_inteiro


def renderizar() -> None:
    st.subheader("Análises de sentimentos")
    st.caption(
        "O sentimento exibido é uma previsão do modelo, não uma certeza sobre a "
        "opinião de quem escreveu o texto."
    )

    filtros_aplicados = filtros.renderizar()
    configuracao = carregar_configuracao()
    fonte = criar_fonte(configuracao)
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

    # Com assunto e menos de 50 análises, o Usuário pode completar com o X (#120).
    busca_x.renderizar(filtros_aplicados, resumo.total, criar_administracao(configuracao))

    if resumo.total == 0:
        if filtros_aplicados.assunto:
            mensagem = f"Nenhum texto sobre “{filtros_aplicados.assunto}” na base"
            mensagem += (
                " com os outros filtros aplicados."
                if filtros_ativos(replace(filtros_aplicados, assunto=None))
                else "."
            )
        elif filtros_ativos(filtros_aplicados):
            mensagem = "Nenhuma análise encontrada para os filtros aplicados."
        else:
            mensagem = "Nenhuma análise encontrada."
        estado_vazio(mensagem)
        secao_resumo.renderizar(resumo, filtros_aplicados)
        return

    indicadores.renderizar(resumo)
    distribuicao.renderizar(resumo)
    secao_resumo.renderizar(resumo, filtros_aplicados)
    listagem.renderizar(fonte, filtros_aplicados, resumo.total)
