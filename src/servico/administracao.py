"""Rotas de administração: login, importação de dataset e coleta com análise.

Implementa a seção "Administração" de docs/frontend/CONTRATO-API.md (issues #58 a #61).

LIMITAÇÃO: enquanto a persistência no MongoDB (issue #20) não existir, datasets
importados, coletas e análises ficam na memória do processo e se perdem quando a
API reinicia. ``RepositorioAdministracao`` concentra esse armazenamento para que
a troca pelo banco não mude as rotas.
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from src.processamento.aquisicao import (
    CAMINHO_PADRAO_TWEETSENTBR,
    RelatorioImportacao,
    iterar_dataset_csv,
    iterar_tweetsentbr,
)

from .autenticacao import Autenticador, ConfiguracaoAdmin, Sessao

logger = logging.getLogger(__name__)

LIMITE_CSV_MB_PADRAO = 10
LIMITE_COLETA_PADRAO = 1000
TAMANHO_LOTE_ANALISE = 32
ID_TWEETSENTBR = "tweetsentbr"

MAXIMO_EXEMPLOS = 10
SENTIMENTOS = ("positivo", "neutro", "negativo")


class ErroClassificadorIndisponivel(RuntimeError):
    """O servidor não tem as dependências do BERTweet instaladas."""


def _erro(codigo: int, mensagem: str, **cabecalhos: str) -> JSONResponse:
    return JSONResponse({"mensagem": mensagem}, status_code=codigo, headers=cabecalhos or None)


def _inteiro_do_ambiente(nome: str, padrao: int) -> int:
    valor = os.getenv(nome, "").strip()
    if not valor:
        return padrao
    try:
        numero = int(valor)
    except ValueError:
        raise ValueError(f"{nome} deve ser um número inteiro.") from None
    if numero <= 0:
        raise ValueError(f"{nome} deve ser maior que zero.")
    return numero


@dataclass
class Dataset:
    id: str
    nome_arquivo: str
    registros: list[dict[str, Any]]


@dataclass
class Coleta:
    id: str
    fonte: str
    situacao: str = "pendente"
    textos_coletados: int = 0
    textos_analisados: int = 0
    mensagem: str | None = None
    por_sentimento: dict[str, int] = field(default_factory=lambda: dict.fromkeys(SENTIMENTOS, 0))
    exemplos: list[dict[str, str]] = field(default_factory=list)

    def como_resposta(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fonte": self.fonte,
            "situacao": self.situacao,
            "textos_coletados": self.textos_coletados,
            "textos_analisados": self.textos_analisados,
            "mensagem": self.mensagem,
            "por_sentimento": dict(self.por_sentimento),
            "exemplos": [dict(e) for e in self.exemplos],
        }


@dataclass
class RepositorioAdministracao:
    """Armazenamento em memória de datasets, coletas e análises (até a issue #20)."""

    datasets: dict[str, Dataset] = field(default_factory=dict)
    coletas: dict[str, Coleta] = field(default_factory=dict)
    analises: list[dict[str, Any]] = field(default_factory=list)
    _trava: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _sequencia: int = 0

    def _proximo_id(self, prefixo: str) -> str:
        self._sequencia += 1
        momento = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return f"{prefixo}_{momento}_{self._sequencia:02d}"

    def adicionar_dataset(self, nome_arquivo: str, registros: list[dict[str, Any]]) -> Dataset:
        with self._trava:
            dataset = Dataset(self._proximo_id("ds"), nome_arquivo, registros)
            self.datasets[dataset.id] = dataset
            return dataset

    def listar_datasets(self) -> list[Dataset]:
        with self._trava:
            return list(self.datasets.values())

    def obter_dataset(self, id_dataset: str) -> Dataset | None:
        with self._trava:
            return self.datasets.get(id_dataset)

    def criar_coleta(self, fonte: str) -> Coleta:
        with self._trava:
            coleta = Coleta(id=self._proximo_id("col"), fonte=fonte)
            self.coletas[coleta.id] = coleta
            return replace(coleta)

    def obter_coleta(self, id_coleta: str) -> Coleta | None:
        with self._trava:
            coleta = self.coletas.get(id_coleta)
            if coleta is None:
                return None
            return replace(
                coleta,
                por_sentimento=dict(coleta.por_sentimento),
                exemplos=list(coleta.exemplos),
            )

    def atualizar_coleta(self, id_coleta: str, **campos: Any) -> None:
        with self._trava:
            self.coletas[id_coleta] = replace(self.coletas[id_coleta], **campos)

    def salvar_analises(self, documentos: Iterable[dict[str, Any]]) -> None:
        with self._trava:
            self.analises.extend(documentos)


def _criar_pipeline_padrao() -> Any:
    try:
        from src.processamento.pipeline import PipelineClassificacao

        return PipelineClassificacao(tamanho_lote=TAMANHO_LOTE_ANALISE)
    except ImportError as erro:
        raise ErroClassificadorIndisponivel from erro


class ContextoAdministracao:
    """Reúne autenticação, armazenamento e configuração das rotas de administração."""

    def __init__(
        self,
        autenticador: Autenticador,
        repositorio: RepositorioAdministracao | None = None,
        *,
        criar_pipeline: Callable[[], Any] = _criar_pipeline_padrao,
        limite_csv_bytes: int = LIMITE_CSV_MB_PADRAO * 1024 * 1024,
        limite_coleta: int = LIMITE_COLETA_PADRAO,
        caminho_tweetsentbr: Path = CAMINHO_PADRAO_TWEETSENTBR,
    ) -> None:
        self.autenticador = autenticador
        self.repositorio = repositorio or RepositorioAdministracao()
        self._criar_pipeline = criar_pipeline
        self._pipeline: Any = None
        self._trava_pipeline = threading.Lock()
        self.limite_csv_bytes = limite_csv_bytes
        self.limite_coleta = limite_coleta
        self.caminho_tweetsentbr = caminho_tweetsentbr

    @classmethod
    def do_ambiente(cls) -> ContextoAdministracao:
        return cls(
            Autenticador(ConfiguracaoAdmin.do_ambiente()),
            limite_csv_bytes=_inteiro_do_ambiente("SENTIA_LIMITE_CSV_MB", LIMITE_CSV_MB_PADRAO)
            * 1024
            * 1024,
            limite_coleta=_inteiro_do_ambiente("SENTIA_LIMITE_COLETA", LIMITE_COLETA_PADRAO),
        )

    def pipeline(self) -> Any:
        """Carrega o classificador uma única vez; o BERTweet demora para iniciar."""
        with self._trava_pipeline:
            if self._pipeline is None:
                self._pipeline = self._criar_pipeline()
            return self._pipeline

    def fontes(self) -> list[dict[str, str]]:
        fontes = []
        if self.caminho_tweetsentbr.is_file():
            fontes.append({"id": ID_TWEETSENTBR, "nome": "TweetSentBR"})
        for dataset in self.repositorio.listar_datasets():
            fontes.append(
                {"id": dataset.id, "nome": f"Dataset importado: {dataset.nome_arquivo}"}
            )
        return fontes

    def registros_da_fonte(self, fonte: str) -> list[dict[str, Any]]:
        if fonte == ID_TWEETSENTBR:
            return list(
                iterar_tweetsentbr(
                    self.caminho_tweetsentbr, modo_estrito=False, limite=self.limite_coleta
                )
            )
        dataset = self.repositorio.obter_dataset(fonte)
        if dataset is None:
            raise KeyError(fonte)
        return dataset.registros


@lru_cache(maxsize=1)
def obter_contexto() -> ContextoAdministracao:
    """Contexto do processo. Os testes substituem esta dependência."""
    from dotenv import load_dotenv

    load_dotenv()
    return ContextoAdministracao.do_ambiente()


def _token_do_cabecalho(request: Request) -> str | None:
    esquema, _, token = request.headers.get("Authorization", "").partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


class NaoAutenticado(Exception):
    """Requisição sem token válido; vira 401 no tratador registrado em main.py."""


Contexto = Annotated[ContextoAdministracao, Depends(obter_contexto)]


def exigir_administrador(request: Request, contexto: Contexto) -> Sessao:
    token = _token_do_cabecalho(request)
    sessao = contexto.autenticador.sessoes.validar(token) if token else None
    if sessao is None:
        raise NaoAutenticado
    return sessao


def responder_nao_autenticado(_request: Request, _excecao: Exception) -> JSONResponse:
    return _erro(401, "Sessão inválida ou expirada.", **{"WWW-Authenticate": "Bearer"})


Administrador = Annotated[Sessao, Depends(exigir_administrador)]

roteador = APIRouter()


class CorpoLogin(BaseModel):
    usuario: str
    senha: str


class CorpoColeta(BaseModel):
    fonte: str


@roteador.post("/auth/login")
def entrar(
    corpo: CorpoLogin,
    request: Request,
    contexto: Contexto,
) -> Any:
    autenticador = contexto.autenticador
    if not autenticador.configurado:
        return _erro(503, "A administração não está configurada neste servidor.")

    origem = request.client.host if request.client else "desconhecida"
    chave = f"{origem}|{corpo.usuario.strip().lower()}"
    if autenticador.limitador.bloqueado(chave):
        return _erro(429, "Muitas tentativas. Aguarde um pouco e tente de novo.")

    if not autenticador.credenciais_validas(corpo.usuario, corpo.senha):
        autenticador.limitador.registrar_falha(chave)
        return _erro(401, "Usuário ou senha inválidos.")

    autenticador.limitador.limpar(chave)
    token, sessao = autenticador.iniciar_sessao(corpo.usuario)
    return {
        "token": token,
        "usuario": sessao.usuario,
        "expira_em": sessao.expira_em.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


@roteador.post("/auth/logout", status_code=204)
def sair(
    request: Request,
    _sessao: Administrador,
    contexto: Contexto,
) -> Response:
    token = _token_do_cabecalho(request)
    if token:
        contexto.autenticador.sessoes.revogar(token)
    return Response(status_code=204)


def _ler_com_limite(arquivo: UploadFile, limite: int) -> bytes | None:
    conteudo = arquivo.file.read(limite + 1)
    return None if len(conteudo) > limite else conteudo


@roteador.post("/datasets", status_code=201)
def importar_dataset(
    arquivo: Annotated[UploadFile, File()],
    _sessao: Administrador,
    contexto: Contexto,
) -> Any:
    nome = Path(arquivo.filename or "").name
    if not nome.lower().endswith(".csv"):
        return _erro(415, "Envie um arquivo com extensão .csv.")

    conteudo = _ler_com_limite(arquivo, contexto.limite_csv_bytes)
    if conteudo is None:
        limite_mb = contexto.limite_csv_bytes // (1024 * 1024)
        return _erro(413, f"O arquivo passa do limite de {limite_mb} MB.")

    relatorio = RelatorioImportacao()
    caminho = None
    try:
        with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as temporario:
            temporario.write(conteudo)
            caminho = temporario.name
        registros = list(
            iterar_dataset_csv(caminho, modo_estrito=False, relatorio=relatorio)
        )
    except ValueError as erro:
        return _erro(422, str(erro))
    finally:
        if caminho:
            Path(caminho).unlink(missing_ok=True)

    dataset = contexto.repositorio.adicionar_dataset(nome, registros)
    importados = len(registros)
    descartados = relatorio.total_descartados
    return {
        "id_dataset": dataset.id,
        "nome_arquivo": nome,
        "registros_lidos": importados + descartados,
        "registros_importados": importados,
        "registros_descartados": descartados,
        "descartes_por_motivo": dict(relatorio.descartes_por_motivo),
    }


@roteador.get("/coletas/fontes")
def listar_fontes(
    _sessao: Administrador,
    contexto: Contexto,
) -> Any:
    return {"fontes": contexto.fontes()}


def executar_coleta(contexto: ContextoAdministracao, id_coleta: str) -> None:
    """Coleta os textos da fonte e os classifica em lotes, atualizando o progresso."""
    repositorio = contexto.repositorio
    coleta = repositorio.obter_coleta(id_coleta)
    if coleta is None:
        return
    try:
        registros = contexto.registros_da_fonte(coleta.fonte)
        repositorio.atualizar_coleta(
            id_coleta, situacao="em_andamento", textos_coletados=len(registros)
        )
        if registros:
            pipeline = contexto.pipeline()
        analisados = 0
        por_sentimento = dict.fromkeys(SENTIMENTOS, 0)
        exemplos: list[dict[str, str]] = []
        for inicio in range(0, len(registros), TAMANHO_LOTE_ANALISE):
            lote = registros[inicio : inicio + TAMANHO_LOTE_ANALISE]
            documentos = pipeline.processar_registros(lote)
            repositorio.salvar_analises(documentos)
            for documento in documentos:
                sentimento = documento.get("sentimento")
                if sentimento in por_sentimento:
                    por_sentimento[sentimento] += 1
                if len(exemplos) < MAXIMO_EXEMPLOS:
                    exemplos.append(
                        {"texto": documento["texto_original"], "sentimento": sentimento}
                    )
            analisados += len(lote)
            repositorio.atualizar_coleta(
                id_coleta,
                textos_analisados=analisados,
                por_sentimento=dict(por_sentimento),
                exemplos=list(exemplos),
            )
        campos: dict[str, Any] = {"situacao": "concluida"}
        if not registros:
            campos["mensagem"] = "Nenhum texto encontrado para analisar."
        repositorio.atualizar_coleta(id_coleta, **campos)
    except ErroClassificadorIndisponivel:
        repositorio.atualizar_coleta(
            id_coleta,
            situacao="falhou",
            mensagem="O classificador de sentimentos não está instalado neste servidor.",
        )
    except Exception:  # A coleta roda em segundo plano e não pode derrubar a API.
        logger.exception("Falha na coleta %s", id_coleta)
        repositorio.atualizar_coleta(
            id_coleta,
            situacao="falhou",
            mensagem="A coleta parou por um erro ao ler ou analisar os textos.",
        )


@roteador.post("/coletas", status_code=202)
def iniciar_coleta(
    corpo: CorpoColeta,
    tarefas: BackgroundTasks,
    _sessao: Administrador,
    contexto: Contexto,
) -> Any:
    if corpo.fonte not in {f["id"] for f in contexto.fontes()}:
        return _erro(422, "Fonte de coleta desconhecida.")
    coleta = contexto.repositorio.criar_coleta(corpo.fonte)
    tarefas.add_task(executar_coleta, contexto, coleta.id)
    return JSONResponse(coleta.como_resposta(), status_code=202)


@roteador.get("/coletas/{id_coleta}")
def consultar_coleta(
    id_coleta: str,
    _sessao: Administrador,
    contexto: Contexto,
) -> Any:
    coleta = contexto.repositorio.obter_coleta(id_coleta)
    if coleta is None:
        return _erro(404, "Coleta não encontrada.")
    return coleta.como_resposta()
