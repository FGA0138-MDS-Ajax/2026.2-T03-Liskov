"""Listagem paginada das análises (RF10, RF13, US11, US14).

Mostra os textos analisados com sentimento, fonte, datas e modelo. Quem filtra e pagina
é a fonte de dados (API), nunca a tela: aqui só se pede uma página por vez. Ao mudar os
filtros, a listagem volta para a primeira página.
"""

import pandas as pd
import streamlit as st

from src.apresentacao.componentes import estado_erro, estado_vazio
from src.apresentacao.contrato import (
    SENTIMENTOS,
    ErroFonteDados,
    FiltrosAnalises,
    FonteAnalises,
)
from src.apresentacao.tema import ESTILOS_SENTIMENTO, paleta
from src.apresentacao.transformacoes import (
    COLUNAS_LISTAGEM,
    descrever_intervalo,
    limitar_pagina,
    montar_linhas_listagem,
    total_de_paginas,
)

# Padrão do contrato (CONTRATO-API.md); o limite técnico da API é 100.
TAMANHO_PAGINA = 20

CHAVE_PAGINA = "listagem_pagina"
CHAVE_ESCOPO = "listagem_filtros"
ROTULOS = {s: ESTILOS_SENTIMENTO[s].rotulo for s in SENTIMENTOS}
_POR_ROTULO = {rotulo: s for s, rotulo in ROTULOS.items()}


def estilizar_tabela(tabela: pd.DataFrame):
    """Sentimento como etiqueta (#121): fundo tingido e texto contrastante, do tema ativo.

    O nome do sentimento continua escrito na célula: a cor só reforça.
    """
    etiquetas = paleta().etiqueta

    def etiqueta(valor: str) -> str:
        sentimento = _POR_ROTULO.get(valor)
        if sentimento is None:
            return ""
        fundo, texto = etiquetas[sentimento]
        return f"background-color:{fundo};color:{texto};font-weight:600"

    return tabela.style.map(etiqueta, subset=["Sentimento"])


def _ir_para(pagina: int) -> None:
    """Callback dos botões: roda antes da renderização, então a tela já nasce na página."""
    st.session_state[CHAVE_PAGINA] = pagina


def _pagina_solicitada(filtros: FiltrosAnalises) -> int:
    # Outro conjunto de filtros é outra lista: voltar à página 1 evita uma página vazia.
    if st.session_state.get(CHAVE_ESCOPO) != filtros:
        st.session_state[CHAVE_ESCOPO] = filtros
        st.session_state[CHAVE_PAGINA] = 1
    return st.session_state.get(CHAVE_PAGINA, 1)


def renderizar(fonte: FonteAnalises, filtros: FiltrosAnalises, total: int) -> None:
    """Mostra a página atual. `total` vem do resumo e limita a navegação."""
    st.subheader("Análises")
    pagina = limitar_pagina(_pagina_solicitada(filtros), total, TAMANHO_PAGINA)

    try:
        with st.spinner("Carregando a lista de análises..."):
            resultado = fonte.listar(filtros, pagina=pagina, tamanho=TAMANHO_PAGINA)
    except ErroFonteDados as erro:
        # O erro da lista não derruba os indicadores que já foram exibidos.
        estado_erro(str(erro))
        return

    if not resultado.itens:
        estado_vazio("Nenhuma análise nesta página.")
        return

    # O total da própria listagem é o que vale para navegar nela.
    paginas = total_de_paginas(resultado.total, resultado.tamanho)
    linhas = montar_linhas_listagem(resultado.itens, ROTULOS)
    st.dataframe(
        estilizar_tabela(pd.DataFrame(linhas, columns=list(COLUNAS_LISTAGEM))),
        hide_index=True,
        width="stretch",
        # Larguras em pixels: o texto leva o que sobra e as demais colunas cabem no
        # cabeçalho. Em telas estreitas a própria tabela rola na horizontal.
        column_config={
            "Texto": st.column_config.TextColumn("Texto", width=260),
            "Sentimento": st.column_config.TextColumn("Sentimento", width=105),
            "Fonte": st.column_config.TextColumn("Fonte", width=125),
            "Publicado em (UTC)": st.column_config.TextColumn(
                "Publicado em (UTC)", width=130
            ),
            "Processado em (UTC)": st.column_config.TextColumn(
                "Processado em (UTC)", width=150
            ),
            "Modelo": st.column_config.TextColumn("Modelo", width=120),
        },
    )

    col_anterior, col_pagina, col_proxima = st.columns([1, 3, 1], vertical_alignment="center")
    with col_anterior:
        st.button(
            "Anterior",
            key="listagem_anterior",
            icon=":material/chevron_left:",
            disabled=resultado.pagina <= 1,
            on_click=_ir_para,
            args=(resultado.pagina - 1,),
        )
    with col_pagina:
        st.caption(
            f"Página {resultado.pagina} de {paginas}. "
            + descrever_intervalo(
                resultado.pagina, resultado.tamanho, resultado.total, len(resultado.itens)
            )
        )
    with col_proxima:
        st.button(
            "Próxima",
            key="listagem_proxima",
            icon=":material/chevron_right:",
            icon_position="right",
            disabled=resultado.pagina >= paginas,
            on_click=_ir_para,
            args=(resultado.pagina + 1,),
        )
