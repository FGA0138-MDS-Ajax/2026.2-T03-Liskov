"""Dashboard do Usuário (RF13), no layout de alta fidelidade (#121): filtros, indicadores,
distribuição (#28), evolução no período, resumo textual (#29), termos frequentes (#30) e
listagem de análises (#27)."""

from dataclasses import replace

import streamlit as st

from src.apresentacao.componentes import estado_erro, estado_vazio
from src.apresentacao.config import carregar_configuracao
from src.apresentacao.contrato import ErroFonteDados, FiltrosAnalises, FonteAnalises
from src.apresentacao.fontes import criar_administracao, criar_fonte
from src.apresentacao.secoes import (
    busca_x,
    distribuicao,
    evolucao,
    filtros,
    indicadores,
    listagem,
    termos,
)
from src.apresentacao.secoes import resumo as secao_resumo
from src.apresentacao.transformacoes import filtros_ativos, formatar_inteiro


def _ultima_analise(fonte: FonteAnalises) -> str | None:
    """Data e hora da análise mais recente, como a API ordena a listagem. Nunca inventada."""
    try:
        pagina = fonte.listar(FiltrosAnalises(), pagina=1, tamanho=1)
    except ErroFonteDados:
        return None
    if not pagina.itens:
        return None
    return pagina.itens[0].data_processamento.strftime("%d/%m/%Y %H:%M")


def renderizar() -> None:
    configuracao = carregar_configuracao()
    fonte = criar_fonte(configuracao)
    titulo, ultima = st.columns([4, 1], vertical_alignment="bottom")
    with titulo:
        st.subheader("Análises de sentimentos")
        st.caption(
            "O sentimento exibido é uma previsão do modelo, não uma certeza sobre a "
            "opinião de quem escreveu o texto."
        )
    quando = _ultima_analise(fonte)
    if quando:
        ultima.caption(f"Última análise: {quando} (UTC)")

    filtros_aplicados = filtros.renderizar()
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

    indicadores.renderizar(resumo, filtros_aplicados)
    # Grade do protótipo (#121); em telas estreitas, o Streamlit empilha as colunas.
    esquerda, direita = st.columns(2)
    with esquerda:
        distribuicao.renderizar(resumo)
    with direita:
        evolucao.renderizar(fonte, filtros_aplicados)
    esquerda, direita = st.columns(2)
    with esquerda:
        secao_resumo.renderizar(resumo, filtros_aplicados)
    with direita:
        termos.renderizar(fonte, filtros_aplicados)
    listagem.renderizar(fonte, filtros_aplicados, resumo.total)
