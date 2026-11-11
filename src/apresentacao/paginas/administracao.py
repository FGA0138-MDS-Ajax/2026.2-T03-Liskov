"""Área do Administrador: login, importação de dataset, coleta e análise.

Requisitos: RF01, RF02, UC01 a UC03 e testes T01 a T03 (issues #59, #60 e #61).
O token da sessão fica só em `st.session_state` e some ao fechar a aba; a senha
não é guardada.
"""

import streamlit as st

from src.apresentacao.componentes import estado_erro, estado_vazio
from src.apresentacao.config import carregar_configuracao
from src.apresentacao.contrato import (
    Coleta,
    ErroAutenticacao,
    ErroFonteDados,
    FonteAdministracao,
    ResultadoImportacao,
    ResumoAnalises,
    SessaoAdministrador,
)
from src.apresentacao.fontes import criar_administracao
from src.apresentacao.fontes.administracao_mock import SENHA_EXEMPLO, USUARIO_EXEMPLO
from src.apresentacao.secoes import indicadores
from src.apresentacao.tema import ESTILOS_SENTIMENTO
from src.apresentacao.transformacoes import formatar_inteiro, mascarar_mencoes

CHAVE_SESSAO = "sessao_admin"
CHAVE_AVISO = "aviso_login"
CHAVE_COLETA = "coleta_atual"

ROTULOS_SITUACAO = {
    "pendente": "aguardando início",
    "em_andamento": "em andamento",
    "concluida": "concluída",
    "falhou": "falhou",
}


def sessao_ativa() -> SessaoAdministrador | None:
    sessao = st.session_state.get(CHAVE_SESSAO)
    if sessao is not None and sessao.expirada():
        encerrar_sessao("Sua sessão expirou. Entre novamente.")
        return None
    return sessao


def encerrar_sessao(aviso: str | None = None) -> None:
    for chave in (CHAVE_SESSAO, CHAVE_COLETA):
        st.session_state.pop(chave, None)
    if aviso:
        st.session_state[CHAVE_AVISO] = aviso


def renderizar_login() -> None:
    st.subheader("Entrar como administrador")
    st.caption(
        "A administração permite importar datasets e iniciar coletas. O dashboard "
        "continua disponível sem login."
    )
    aviso = st.session_state.pop(CHAVE_AVISO, None)
    if aviso:
        st.warning(aviso, icon=":material/info:")

    config = carregar_configuracao()
    if config.fonte_dados == "mock":
        st.caption(
            f"No modo de exemplo, use o usuário `{USUARIO_EXEMPLO}` e a senha "
            f"`{SENHA_EXEMPLO}`."
        )

    with st.form("login"):
        usuario = st.text_input("Usuário", autocomplete="username", key="login_usuario")
        senha = st.text_input(
            "Senha", type="password", autocomplete="current-password", key="login_senha"
        )
        entrar = st.form_submit_button("Entrar", type="primary", key="entrar")

    if not entrar:
        return
    if not usuario.strip() or not senha:
        estado_erro("Informe o usuário e a senha.")
        return
    try:
        with st.spinner("Verificando acesso..."):
            sessao = criar_administracao(config).entrar(usuario.strip(), senha)
    except ErroFonteDados as erro:
        estado_erro(str(erro))
        return
    st.session_state[CHAVE_SESSAO] = sessao
    st.rerun()


def renderizar() -> None:
    sessao = sessao_ativa()
    if sessao is None:
        renderizar_login()
        return
    admin = criar_administracao(carregar_configuracao())

    titulo, acao = st.columns([4, 1], vertical_alignment="bottom")
    with titulo:
        st.subheader("Administração")
        st.caption(f"Conectado como **{sessao.usuario}**.")
    with acao:
        if st.button("Sair", icon=":material/logout:", key="sair"):
            try:
                admin.sair(sessao)
            except ErroFonteDados:
                pass  # A sessão local termina mesmo que a API não responda.
            encerrar_sessao("Você saiu da administração.")
            st.rerun()

    try:
        _secao_importacao(admin, sessao)
        st.divider()
        _secao_coleta(admin, sessao)
    except ErroAutenticacao as erro:
        encerrar_sessao(str(erro))
        st.rerun()


def importar_e_analisar(
    admin: FonteAdministracao,
    sessao: SessaoAdministrador,
    nome_arquivo: str,
    conteudo: bytes,
    analisar: bool,
) -> tuple[ResultadoImportacao, Coleta | None, str]:
    """Importa o CSV e, se pedido, já inicia a coleta e análise do dataset importado.

    Devolve o relatório, a coleta iniciada (ou None) e o próximo passo para o usuário.
    Uma falha ao iniciar a análise não desfaz a importação.
    """
    resultado = admin.importar_dataset(sessao, nome_arquivo, conteudo)
    if not analisar:
        return resultado, None, "Para analisá-los, escolha o dataset em **Coleta e análise**."
    try:
        coleta = admin.iniciar_coleta(sessao, resultado.id_dataset)
    except ErroAutenticacao:
        raise
    except ErroFonteDados as erro:
        return (
            resultado,
            None,
            f"A análise não pôde começar ({erro}). Tente pela seção **Coleta e análise**.",
        )
    return resultado, coleta, "A análise começou: acompanhe em **Coleta e análise**."


def _secao_importacao(admin: FonteAdministracao, sessao: SessaoAdministrador) -> None:
    st.markdown("#### Importar dataset")
    st.caption(
        "Arquivo CSV em UTF-8 com as colunas `texto` (ou `texto_original`) e `fonte`. "
        "Opcionais: `id`, `sentimento` e `data`."
    )
    with st.form("importacao", clear_on_submit=True):
        arquivo = st.file_uploader("Arquivo CSV", type=["csv"], key="arquivo_csv")
        analisar = st.checkbox(
            "Analisar o sentimento logo após importar",
            value=True,
            help="Inicia a coleta e análise do arquivo; o resultado aparece em Coleta e análise.",
            key="analisar_ao_importar",
        )
        enviar = st.form_submit_button("Importar", key="importar")
    if not enviar:
        return
    if arquivo is None:
        estado_erro("Escolha um arquivo CSV.")
        return
    try:
        with st.spinner("Importando o arquivo..."):
            resultado, coleta, proximo_passo = importar_e_analisar(
                admin, sessao, arquivo.name, arquivo.getvalue(), analisar
            )
    except ErroAutenticacao:
        raise
    except ErroFonteDados as erro:
        estado_erro(str(erro))
        return
    if coleta is not None:
        st.session_state[CHAVE_COLETA] = coleta

    st.success(
        f"Importação de **{resultado.nome_arquivo}** concluída: "
        f"{formatar_inteiro(resultado.registros_importados)} de "
        f"{formatar_inteiro(resultado.registros_lidos)} registros importados. "
        + proximo_passo,
        icon=":material/task_alt:",
    )
    if resultado.registros_descartados:
        st.warning(
            f"{formatar_inteiro(resultado.registros_descartados)} registro(s) "
            "descartado(s).",
            icon=":material/warning:",
        )
        st.table(
            {
                "Motivo": list(resultado.descartes_por_motivo),
                "Registros": list(resultado.descartes_por_motivo.values()),
            }
        )


def _secao_coleta(admin: FonteAdministracao, sessao: SessaoAdministrador) -> None:
    st.markdown("#### Coleta e análise")
    st.caption("Coleta os textos da fonte escolhida e classifica o sentimento de cada um.")
    try:
        fontes = admin.listar_fontes_coleta(sessao)
    except ErroAutenticacao:
        raise
    except ErroFonteDados as erro:
        estado_erro(str(erro))
        return
    if not fontes:
        estado_vazio("Nenhuma fonte de coleta disponível.")
        return

    nomes = {f.id: f.nome for f in fontes}
    with st.form("coleta"):
        fonte = st.selectbox("Fonte", list(nomes), format_func=nomes.get, key="fonte_coleta")
        iniciar = st.form_submit_button(
            "Iniciar coleta e análise", type="primary", key="iniciar_coleta"
        )
    if iniciar:
        try:
            st.session_state[CHAVE_COLETA] = admin.iniciar_coleta(sessao, fonte)
        except ErroAutenticacao:
            raise
        except ErroFonteDados as erro:
            estado_erro(str(erro))
            return

    coleta = st.session_state.get(CHAVE_COLETA)
    if coleta is None:
        return
    _mostrar_coleta(coleta, nomes)
    if coleta.situacao in ("pendente", "em_andamento") and st.button(
        "Atualizar situação", icon=":material/refresh:", key="atualizar_coleta"
    ):
        try:
            st.session_state[CHAVE_COLETA] = admin.consultar_coleta(sessao, coleta.id)
        except ErroAutenticacao:
            raise
        except ErroFonteDados as erro:
            estado_erro(str(erro))
            return
        st.rerun()


def _mostrar_coleta(coleta: Coleta, nomes: dict[str, str]) -> None:
    nome = nomes.get(coleta.fonte, coleta.fonte)
    if coleta.situacao == "concluida":
        st.success(
            f"Coleta de {nome} concluída: "
            f"{formatar_inteiro(coleta.textos_analisados)} texto(s) analisado(s).",
            icon=":material/task_alt:",
        )
        if coleta.mensagem:
            st.info(coleta.mensagem, icon=":material/info:")
        _mostrar_resultado(coleta)
    elif coleta.situacao == "falhou":
        estado_erro(coleta.mensagem or "A coleta falhou. Tente novamente mais tarde.")
    else:
        st.info(
            f"Coleta de {nome}: {ROTULOS_SITUACAO[coleta.situacao]}. "
            f"{formatar_inteiro(coleta.textos_coletados)} coletado(s) e "
            f"{formatar_inteiro(coleta.textos_analisados)} analisado(s) até agora.",
            icon=":material/hourglass_top:",
        )


def _mostrar_resultado(coleta: Coleta) -> None:
    """Resultado da coleta: indicadores e alguns textos com o sentimento previsto."""
    total = sum(coleta.por_sentimento.values())
    if total:
        indicadores.renderizar(ResumoAnalises(total=total, por_sentimento=coleta.por_sentimento))
    if coleta.exemplos:
        st.caption(
            f"Primeiros {len(coleta.exemplos)} texto(s). O sentimento é uma previsão do "
            "modelo, não uma certeza. Menções a perfis aparecem como @usuário."
        )
        tabela = {
            "Texto": [mascarar_mencoes(e.texto) for e in coleta.exemplos],
            "Sentimento previsto": [
                ESTILOS_SENTIMENTO[e.sentimento].rotulo for e in coleta.exemplos
            ],
        }
        st.table(tabela)
