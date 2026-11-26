"""Busca do Usuário no X (#120): completa o assunto com textos recentes até 50.

Só aparece com o filtro de assunto ativo e menos de 50 análises sobre ele. Quem
decide a meta, o limite diário de buscas e se o X é chamado é a API; a tela só pede
a busca, acompanha e mostra o resultado. Depois, o dashboard é recarregado com os
textos novos.
"""

import time

import streamlit as st

from src.apresentacao.componentes import estado_erro
from src.apresentacao.contrato import (
    META_PESQUISA_USUARIO,
    Coleta,
    ErroFonteDados,
    FiltrosAnalises,
    FonteAdministracao,
)
from src.apresentacao.transformacoes import formatar_inteiro

CHAVE_EM_ANDAMENTO = "busca_x_em_andamento"
CHAVE_RESULTADO = "busca_x_resultado"
ESPERA_MAXIMA_SEGUNDOS = 90
INTERVALO_SEGUNDOS = 1.5


def renderizar(
    filtros: FiltrosAnalises, total: int, administracao: FonteAdministracao
) -> None:
    assunto = filtros.assunto
    if not assunto:
        return

    resultado: Coleta | None = st.session_state.get(CHAVE_RESULTADO)
    if resultado is not None and resultado.termo == assunto:
        _mostrar_resultado(resultado)

    em_andamento = st.session_state.get(CHAVE_EM_ANDAMENTO)
    if em_andamento is not None:
        _acompanhar(administracao, em_andamento)
        return

    if total >= META_PESQUISA_USUARIO:
        return
    if resultado is not None and resultado.termo == assunto:
        return  # já buscou este assunto nesta sessão; o resultado está acima

    with st.container(border=True):
        st.markdown(
            f"Há **{formatar_inteiro(total)}** análise(s) sobre “{assunto}”. Para chegar a "
            f"{META_PESQUISA_USUARIO}, o SentIA pode buscar textos recentes no X e "
            "analisar o sentimento deles."
        )
        st.caption(
            "O número de buscas no X por dia é limitado. Se o assunto já foi buscado "
            "nos últimos 30 dias, os textos guardados são reaproveitados."
        )
        if st.button("Buscar no X", icon=":material/travel_explore:", key="buscar_no_x"):
            try:
                coleta = administracao.buscar_como_usuario(assunto)
            except ErroFonteDados as erro:
                estado_erro(str(erro))
                return
            st.session_state[CHAVE_EM_ANDAMENTO] = {"id": coleta.id, "termo": assunto}
            _acompanhar(administracao, st.session_state[CHAVE_EM_ANDAMENTO])


def _acompanhar(administracao: FonteAdministracao, busca: dict[str, str]) -> None:
    """Espera a API concluir, sem prometer atualização automática para sempre."""
    prazo = time.monotonic() + ESPERA_MAXIMA_SEGUNDOS
    with st.status(
        f"Buscando e analisando textos sobre “{busca['termo']}”...", expanded=False
    ) as status:
        while True:
            try:
                coleta = administracao.consultar_busca_usuario(busca["id"])
            except ErroFonteDados as erro:
                st.session_state.pop(CHAVE_EM_ANDAMENTO, None)
                status.update(label="A busca não pôde ser acompanhada.", state="error")
                estado_erro(str(erro))
                return
            if coleta.situacao in ("concluida", "falhou"):
                break
            if time.monotonic() >= prazo:
                status.update(
                    label="A análise ainda está em andamento. Clique em Atualizar.",
                    state="running",
                )
                st.button("Atualizar", icon=":material/refresh:", key="atualizar_busca_x")
                return
            time.sleep(INTERVALO_SEGUNDOS)

    st.session_state.pop(CHAVE_EM_ANDAMENTO, None)
    if coleta.situacao == "falhou":
        estado_erro(coleta.mensagem or "A busca no X não pôde ser concluída.")
        return
    st.session_state[CHAVE_RESULTADO] = coleta
    st.rerun()  # recarrega indicadores, gráfico e tabela com os textos novos


def _mostrar_resultado(coleta: Coleta) -> None:
    origem = coleta.origem or {}
    da_base = formatar_inteiro(origem.get("base", 0))
    do_x = formatar_inteiro(origem.get("x", 0))
    st.success(
        f"Busca concluída: {da_base} texto(s) da base do SentIA e {do_x} novo(s) do X.",
        icon=":material/check_circle:",
    )
    if coleta.mensagem:
        st.info(coleta.mensagem, icon=":material/info:")
