"""Administração FICTÍCIA, para desenvolver o painel sem o backend.

As credenciais abaixo só funcionam no modo mock e não protegem nada: servem para
demonstrar o fluxo de login. No modo api, quem valida o acesso é a API.
"""

import csv
import io
from datetime import UTC, datetime, timedelta

from src.apresentacao.contrato import (
    Coleta,
    ErroAutenticacao,
    ErroFonteDados,
    FonteColeta,
    ResultadoImportacao,
    SessaoAdministrador,
)
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO

USUARIO_EXEMPLO = "admin"
SENHA_EXEMPLO = "senha-de-exemplo"
_TOKEN_EXEMPLO = "token-de-exemplo"
DURACAO_SESSAO = timedelta(hours=1)

# Mesmas colunas aceitas pelo importador do backend (csv_importer.py).
COLUNAS_TEXTO = ("texto", "texto_original")
COLUNA_FONTE = "fonte"

FONTES_EXEMPLO = [
    FonteColeta(id="tweetsentbr", nome="TweetSentBR"),
    FonteColeta(id="dataset_exemplo", nome="Dataset importado de exemplo"),
]


class AdministracaoMock:
    """Imita a API: valida a sessão, lê o CSV e conclui coletas imediatamente."""

    def entrar(self, usuario: str, senha: str) -> SessaoAdministrador:
        if usuario != USUARIO_EXEMPLO or senha != SENHA_EXEMPLO:
            raise ErroAutenticacao("Usuário ou senha inválidos.")
        return SessaoAdministrador(
            token=_TOKEN_EXEMPLO,
            usuario=usuario,
            expira_em=datetime.now(UTC) + DURACAO_SESSAO,
        )

    def sair(self, sessao: SessaoAdministrador) -> None:
        self._validar(sessao)

    def importar_dataset(
        self, sessao: SessaoAdministrador, nome_arquivo: str, conteudo: bytes
    ) -> ResultadoImportacao:
        self._validar(sessao)
        try:
            texto = conteudo.decode("utf-8-sig")
        except UnicodeDecodeError as erro:
            raise ErroFonteDados("O arquivo precisa estar codificado em UTF-8.") from erro

        leitor = csv.DictReader(io.StringIO(texto))
        colunas = leitor.fieldnames or []
        coluna_texto = next((c for c in COLUNAS_TEXTO if c in colunas), None)
        if coluna_texto is None or COLUNA_FONTE not in colunas:
            raise ErroFonteDados(
                "O CSV precisa das colunas `texto` (ou `texto_original`) e `fonte`."
            )

        lidos = importados = 0
        descartes: dict[str, int] = {}
        for linha in leitor:
            lidos += 1
            if not (linha.get(coluna_texto) or "").strip():
                descartes["texto_vazio"] = descartes.get("texto_vazio", 0) + 1
            elif not (linha.get(COLUNA_FONTE) or "").strip():
                descartes["fonte_vazia"] = descartes.get("fonte_vazia", 0) + 1
            else:
                importados += 1
        if importados == 0:
            raise ErroFonteDados("O arquivo não tem registros válidos para importar.")

        return ResultadoImportacao(
            id_dataset="dataset_exemplo",
            nome_arquivo=nome_arquivo,
            registros_lidos=lidos,
            registros_importados=importados,
            registros_descartados=lidos - importados,
            descartes_por_motivo=descartes,
        )

    def listar_fontes_coleta(self, sessao: SessaoAdministrador) -> list[FonteColeta]:
        self._validar(sessao)
        return list(FONTES_EXEMPLO)

    def iniciar_coleta(self, sessao: SessaoAdministrador, fonte: str) -> Coleta:
        self._validar(sessao)
        if fonte not in {f.id for f in FONTES_EXEMPLO}:
            raise ErroFonteDados("Fonte de coleta desconhecida.")
        return Coleta(id=f"coleta_{fonte}", fonte=fonte, situacao="em_andamento")

    def consultar_coleta(self, sessao: SessaoAdministrador, id_coleta: str) -> Coleta:
        """Sem estado entre execuções do Streamlit: toda coleta conhecida já terminou."""
        self._validar(sessao)
        fonte = id_coleta.removeprefix("coleta_")
        if fonte == id_coleta or fonte not in {f.id for f in FONTES_EXEMPLO}:
            raise ErroFonteDados("Coleta não encontrada.")
        total = len(ANALISES_DE_EXEMPLO)
        return Coleta(
            id=id_coleta,
            fonte=fonte,
            situacao="concluida",
            textos_coletados=total,
            textos_analisados=total,
        )

    @staticmethod
    def _validar(sessao: SessaoAdministrador) -> None:
        if sessao.token != _TOKEN_EXEMPLO or sessao.expirada():
            raise ErroAutenticacao("Sua sessão expirou. Entre novamente.")


class AdministracaoMockComErro:
    """Simula a API indisponível, para validar o estado de erro da administração."""

    MENSAGEM = "Erro simulado: a API de administração está indisponível."

    def entrar(self, usuario: str, senha: str) -> SessaoAdministrador:
        raise ErroFonteDados(self.MENSAGEM)

    def sair(self, sessao: SessaoAdministrador) -> None:
        raise ErroFonteDados(self.MENSAGEM)

    def importar_dataset(
        self, sessao: SessaoAdministrador, nome_arquivo: str, conteudo: bytes
    ) -> ResultadoImportacao:
        raise ErroFonteDados(self.MENSAGEM)

    def listar_fontes_coleta(self, sessao: SessaoAdministrador) -> list[FonteColeta]:
        raise ErroFonteDados(self.MENSAGEM)

    def iniciar_coleta(self, sessao: SessaoAdministrador, fonte: str) -> Coleta:
        raise ErroFonteDados(self.MENSAGEM)

    def consultar_coleta(self, sessao: SessaoAdministrador, id_coleta: str) -> Coleta:
        raise ErroFonteDados(self.MENSAGEM)
