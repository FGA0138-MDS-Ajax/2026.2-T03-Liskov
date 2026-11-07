"""Dashboard do Usuário (RF13). Filtros, gráficos, listagem e resumo ainda serão
adicionados (issues #14, #27, #28 e #29)."""

import streamlit as st

from src.apresentacao.componentes import cartao_indicador, estado_erro, estado_vazio
from src.apresentacao.config import carregar_configuracao
from src.apresentacao.contrato import (
    SENTIMENTOS,
    ErroFonteDados,
    FiltrosAnalises,
    ResumoAnalises,
)
from src.apresentacao.fontes import criar_fonte
from src.apresentacao.tema import ESTILOS_SENTIMENTO
from src.apresentacao.transformacoes import calcular_percentuais, formatar_inteiro


def _secao_indicadores(resumo: ResumoAnalises) -> None:
    percentuais = calcular_percentuais(resumo.por_sentimento)
    colunas = st.columns(1 + len(SENTIMENTOS))
    with colunas[0]:
        cartao_indicador(":material/description: Analisados", formatar_inteiro(resumo.total))
    for coluna, sentimento in zip(colunas[1:], SENTIMENTOS):
        estilo = ESTILOS_SENTIMENTO[sentimento]
        with coluna:
            cartao_indicador(
                f":{estilo.cor_markdown}[{estilo.icone}] {estilo.rotulo}",
                f"{percentuais[sentimento]}%",
            )


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

    _secao_indicadores(resumo)
