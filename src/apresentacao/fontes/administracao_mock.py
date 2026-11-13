"""Administração FICTÍCIA, para desenvolver o painel sem o backend.

As credenciais abaixo só funcionam no modo mock e não protegem nada: servem para
demonstrar o fluxo de login. No modo api, quem valida o acesso é a API.
"""

import csv
import io
from datetime import UTC, datetime, timedelta
from urllib.parse import quote, unquote

from src.apresentacao.contrato import (
    FONTE_PESQUISA,
    SENTIMENTOS,
    Coleta,
    ErroAutenticacao,
    ErroFonteDados,
    ExemploAnalise,
    FonteColeta,
    ResultadoImportacao,
    SessaoAdministrador,
)
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO
from src.apresentacao.transformacoes import validar_busca

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

# Pesquisa simulada: a "base" sempre tem 3 textos sobre o assunto, o X devolve no máximo
# 12 tweets novos e 1 repetido é descartado, para mostrar todos os casos da tela.
TEXTOS_NA_BASE_EXEMPLO = 3
TWEETS_DO_X_EXEMPLO = 12
_PREFIXO_PESQUISA = "pesquisa_"


def _resultado_exemplo(quantidade: int, origens: list[str] | None = None) -> dict:
    """Contagens e exemplos tirados dos primeiros textos de exemplo."""
    amostra = ANALISES_DE_EXEMPLO[:quantidade]
    origens = origens or [None] * len(amostra)
    return {
        "por_sentimento": {s: sum(a.sentimento == s for a in amostra) for s in SENTIMENTOS},
        "exemplos": tuple(
            ExemploAnalise(texto=a.texto_original, sentimento=a.sentimento, origem=o)
            for a, o in list(zip(amostra, origens, strict=True))[:10]
        ),
    }


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

        try:
            leitor = csv.DictReader(io.StringIO(texto), strict=True)
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
        except csv.Error as erro:
            raise ErroFonteDados(
                "O CSV está malformado ou contém um campo maior que o limite de leitura."
            ) from erro
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

    def pesquisar(
        self,
        sessao: SessaoAdministrador,
        termo: str,
        quantidade: int,
        complementar_com_x: bool,
    ) -> Coleta:
        self._validar(sessao)
        try:
            termo, quantidade = validar_busca(termo, quantidade)
        except ValueError as erro:
            raise ErroFonteDados(str(erro)) from erro
        # O id guarda a pesquisa porque o mock não tem estado entre execuções.
        completar = int(complementar_com_x)
        return Coleta(
            id=f"{_PREFIXO_PESQUISA}{quantidade}_{completar}_{quote(termo, safe='')}",
            fonte=FONTE_PESQUISA,
            situacao="em_andamento",
            termo=termo,
        )

    def consultar_coleta(self, sessao: SessaoAdministrador, id_coleta: str) -> Coleta:
        """Sem estado entre execuções do Streamlit: toda coleta conhecida já terminou."""
        self._validar(sessao)
        if id_coleta.startswith(_PREFIXO_PESQUISA):
            return self._pesquisa_concluida(id_coleta)
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
            **_resultado_exemplo(total),
        )

    @staticmethod
    def _pesquisa_concluida(id_coleta: str) -> Coleta:
        partes = id_coleta.removeprefix(_PREFIXO_PESQUISA).split("_", 2)
        if len(partes) != 3 or not partes[0].isdigit() or partes[1] not in ("0", "1"):
            raise ErroFonteDados("Coleta não encontrada.")
        meta, completar, termo = int(partes[0]), partes[1] == "1", unquote(partes[2])
        da_base = min(meta, TEXTOS_NA_BASE_EXEMPLO)
        do_x = min(meta - da_base, TWEETS_DO_X_EXEMPLO) if completar else 0
        total = da_base + do_x
        aviso = None
        if not completar and da_base < meta:
            aviso = (
                f"A base tem {da_base} texto(s) sobre o assunto. Marque a opção de "
                "completar com o X para chegar à meta."
            )
        return Coleta(
            id=id_coleta,
            fonte=FONTE_PESQUISA,
            situacao="concluida",
            textos_coletados=total,
            textos_analisados=total,
            mensagem=aviso,
            termo=termo,
            origem={"base": da_base, "x": do_x, "duplicatas": int(do_x > 0)},
            **_resultado_exemplo(total, ["base"] * da_base + ["x"] * do_x),
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

    def pesquisar(
        self,
        sessao: SessaoAdministrador,
        termo: str,
        quantidade: int,
        complementar_com_x: bool,
    ) -> Coleta:
        raise ErroFonteDados(self.MENSAGEM)

    def consultar_coleta(self, sessao: SessaoAdministrador, id_coleta: str) -> Coleta:
        raise ErroFonteDados(self.MENSAGEM)
