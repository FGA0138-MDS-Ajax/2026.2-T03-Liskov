"""Indicadores de total e percentual por sentimento (RF13, RF14), no layout do #121.

Cartões em duas linhas de dois, com barra de proporção na cor do sentimento e a quantidade
escrita: os números nunca são cortados, mesmo com o menu aberto em 820 px.
"""

import streamlit as st

from src.apresentacao.componentes import cartao_indicador
from src.apresentacao.contrato import SENTIMENTOS, FiltrosAnalises, ResumoAnalises
from src.apresentacao.tema import ESTILOS_SENTIMENTO, paleta
from src.apresentacao.transformacoes import calcular_percentuais, formatar_inteiro


def renderizar(resumo: ResumoAnalises, filtros: FiltrosAnalises | None = None) -> None:
    cores = paleta()
    percentuais = calcular_percentuais(resumo.por_sentimento)
    assunto = filtros.assunto if filtros else None
    detalhe = f"textos sobre “{assunto}”" if assunto else "textos classificados"
    # Em telas estreitas o Streamlit empilha as colunas, sem rolagem horizontal.
    colunas = [*st.columns(2), *st.columns(2)]
    with colunas[0]:
        # Barra cheia na cor primária: os quatro cartões ficam com a mesma altura.
        cartao_indicador(
            ":material/description: Analisados",
            formatar_inteiro(resumo.total),
            detalhe,
            (1.0 if resumo.total else 0.0, cores.primaria, cores.borda, "Total de análises"),
        )
    for coluna, sentimento in zip(colunas[1:], SENTIMENTOS):
        estilo = ESTILOS_SENTIMENTO[sentimento]
        quantidade = resumo.por_sentimento.get(sentimento, 0)
        with coluna:
            # Rótulo e ícone acompanham a cor: o sentimento nunca depende só dela.
            cartao_indicador(
                f":{estilo.cor_markdown}[{estilo.icone}] {estilo.rotulo}",
                f"{percentuais[sentimento]}%",
                f"{formatar_inteiro(quantidade)} texto(s)",
                (
                    quantidade / resumo.total if resumo.total else 0.0,
                    cores.grafico[sentimento],
                    cores.etiqueta[sentimento][0],
                    f"{estilo.rotulo}: {percentuais[sentimento]}% dos textos",
                ),
            )
