"""Componentes de interface reutilizáveis entre as páginas do painel."""

import streamlit as st

MENSAGEM_DADOS_DE_EXEMPLO = (
    "**Dados de exemplo.** Os valores desta tela são fictícios e não vêm da API nem "
    "de análises reais."
)


def aviso_dados_de_exemplo() -> None:
    st.warning(MENSAGEM_DADOS_DE_EXEMPLO, icon=":material/science:")


def barra_proporcao(fracao: float, cor: str, trilho: str, descricao: str) -> None:
    """Barra fina com a cor do sentimento (protótipo de alta fidelidade, #121).

    HTML porque o `st.progress` nativo só tem a cor primária do tema, e o protótipo pinta
    cada barra com a cor do seu sentimento. As cores vêm de `tema.paleta()`, então a barra
    acompanha o tema claro e o escuro. O `aria-label` e o número escrito no cartão dizem o
    mesmo que a barra: a informação nunca depende só da cor.
    """
    largura = f"{min(max(fracao, 0.0), 1.0):.1%}"
    st.markdown(
        f'<div role="img" aria-label="{descricao}" style="height:6px;border-radius:3px;'
        f'background:{trilho};overflow:hidden;margin:4px 0 8px">'
        f'<div style="width:{largura};height:100%;background:{cor}"></div></div>',
        unsafe_allow_html=True,
    )


def cartao_indicador(
    rotulo: str,
    valor: str,
    detalhe: str | None = None,
    barra: tuple[float, str, str, str] | None = None,
) -> None:
    """Cartão do wireframe: número grande, barra de proporção e uma linha de detalhe.

    `barra` é (fração, cor, cor do trilho, descrição para leitores de tela).
    """
    with st.container(border=True):
        st.metric(label=rotulo, value=valor)
        if barra is not None:
            barra_proporcao(*barra)
        if detalhe:
            st.caption(detalhe)


def estado_vazio(mensagem: str) -> None:
    st.info(mensagem, icon=":material/search_off:")


def estado_erro(mensagem: str) -> None:
    st.error(mensagem, icon=":material/error:")
