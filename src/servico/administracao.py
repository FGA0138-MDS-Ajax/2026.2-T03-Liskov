"""Rotas de administração: login, importação de dataset e coleta com análise.

Implementa a seção "Administração" de docs/frontend/CONTRATO-API.md (issues #58 a #61).

Datasets importados, corpus TweetSentBR, cache de pesquisa híbrida, registros e
análises geradas são persistidos no MongoDB por meio de ``RepositorioAnalises``
(``src/dados/repositorio.py``); coletas em andamento e sessões ficam na memória do processo.
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from src.dados.database import (
    ErroConexaoMongoDB,
    ErroConfiguracaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)
from src.dados.repositorio import (
    ErroLeituraAnalises,
    RepositorioAnalises,
    criar_indices,
    criar_indices_complementares,
    garantir_id_origem,
    obter_colecao,
)

from src.processamento.aquisicao import (
    CAMINHO_PADRAO_TWEETSENTBR,
    RelatorioImportacao,
    iterar_dataset_csv,
    iterar_tweetsentbr,
)

from .autenticacao import Autenticador, ConfiguracaoAdmin, Sessao
from .pesquisa import pesquisar

logger = logging.getLogger(__name__)

LIMITE_CSV_MB_PADRAO = 10
LIMITE_COLETA_PADRAO = 1000
TAMANHO_LOTE_ANALISE = 100
ID_TWEETSENTBR = "tweetsentbr"

# Pesquisa híbrida (src/servico/pesquisa.py): base do SentIA e, se faltar, o X.
FONTE_PESQUISA = "pesquisa"
TAMANHO_MAXIMO_TERMO = 100
QUANTIDADE_MAXIMA_PESQUISA = 100
MAXIMO_EXEMPLOS = 100
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
    termo: str | None = None
    quantidade: int | None = None
    complementar_com_x: bool = False
    forcar_atualizacao: bool = False
    # Pesquisa: quantos textos vieram da base, quantos do X e quantos repetidos saíram.
    origem: dict[str, int] | None = None
    por_sentimento: dict[str, int] = field(default_factory=lambda: dict.fromkeys(SENTIMENTOS, 0))
    exemplos: list[dict[str, str]] = field(default_factory=list)

    def como_resposta(self) -> dict[str, Any]:
        resposta = {
            "id": self.id,
            "fonte": self.fonte,
            "situacao": self.situacao,
            "textos_coletados": self.textos_coletados,
            "textos_analisados": self.textos_analisados,
            "mensagem": self.mensagem,
            "por_sentimento": dict(self.por_sentimento),
            "exemplos": [dict(e) for e in self.exemplos],
        }
        if self.termo is not None:
            resposta["termo"] = self.termo
        if self.origem is not None:
            resposta["origem"] = dict(self.origem)
        return resposta


@dataclass
class RepositorioAdministracao:
    """Controle de coletas em andamento e fachada de datasets persistidos no MongoDB."""

    datasets: dict[str, Dataset] = field(default_factory=dict)
    coletas: dict[str, Coleta] = field(default_factory=dict)
    _trava: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _sequencia: int = 0
    _provedor_repositorio: (
        Callable[[], AbstractContextManager[RepositorioAnalises]] | None
    ) = field(default=None, repr=False)

    def vincular_persistencia(
        self,
        provedor: Callable[[], AbstractContextManager[RepositorioAnalises]],
    ) -> None:
        """Associa o provedor canônico de ``RepositorioAnalises`` aos datasets."""
        self._provedor_repositorio = provedor

    def _proximo_id(self, prefixo: str) -> str:
        self._sequencia += 1
        momento = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        return f"{prefixo}_{momento}_{self._sequencia:02d}"

    def adicionar_dataset(
        self,
        nome_arquivo: str,
        registros: list[dict[str, Any]],
        *,
        id_dataset: str | None = None,
        tipo: str = "upload_csv",
        origem_coleta: str | None = "csv",
        metadados: dict[str, Any] | None = None,
    ) -> Dataset:
        if self._provedor_repositorio is not None:
            with self._provedor_repositorio() as repo:
                salvo = repo.salvar_dataset(
                    nome_arquivo,
                    registros,
                    id_dataset=id_dataset,
                    tipo=tipo,
                    origem_coleta=origem_coleta,
                    metadados=metadados,
                )
            return Dataset(
                salvo["id_dataset"], salvo["nome_arquivo"], salvo["registros"]
            )
        with self._trava:
            dataset = Dataset(id_dataset or self._proximo_id("ds"), nome_arquivo, registros)
            self.datasets[dataset.id] = dataset
            return dataset

    def listar_datasets(self, *, incluir_registros: bool = True) -> list[Dataset]:
        if self._provedor_repositorio is not None:
            with self._provedor_repositorio() as repo:
                itens = repo.listar_datasets(incluir_registros=incluir_registros)
            return [
                Dataset(item["id_dataset"], item["nome_arquivo"], item.get("registros", []))
                for item in itens
            ]
        with self._trava:
            return list(self.datasets.values())

    def obter_dataset(self, id_dataset: str) -> Dataset | None:
        if self._provedor_repositorio is not None:
            with self._provedor_repositorio() as repo:
                item = repo.obter_dataset(id_dataset, incluir_registros=True)
            if item is None:
                return None
            return Dataset(item["id_dataset"], item["nome_arquivo"], item.get("registros", []))
        with self._trava:
            return self.datasets.get(id_dataset)

    def criar_coleta(
        self,
        fonte: str,
        termo: str | None = None,
        quantidade: int | None = None,
        complementar_com_x: bool = False,
        forcar_atualizacao: bool = False,
    ) -> Coleta:
        with self._trava:
            coleta = Coleta(
                id=self._proximo_id("col"),
                fonte=fonte,
                termo=termo,
                quantidade=quantidade,
                complementar_com_x=complementar_com_x,
                forcar_atualizacao=forcar_atualizacao,
            )
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


@contextmanager
def _abrir_colecao_analises() -> Iterator[Collection]:
    client = connect_to_mongodb()
    try:
        colecao = obter_colecao(client)
        criar_indices(colecao)
        criar_indices_complementares(colecao)
        yield colecao
    finally:
        disconnect_from_mongodb(client)


def _buscar_x_padrao(termo: str, quantidade: int) -> list[dict[str, Any]]:
    from src.processamento.aquisicao.xfetch import buscar_tweets_xfetch

    # Só tweets em português; o módulo pagina e limita a 10 requisições por busca.
    return buscar_tweets_xfetch(f"{termo} lang:pt", quantidade=quantidade)


def _criar_pipeline_padrao() -> Any:
    try:
        from src.processamento.pipeline import PipelineClassificacao

        return PipelineClassificacao(tamanho_lote=TAMANHO_LOTE_ANALISE)
    except ImportError as erro:
        raise ErroClassificadorIndisponivel from erro


class ContextoAdministracao:
    """Reúne autenticação, estado operacional e persistência das rotas de administração."""

    def __init__(
        self,
        autenticador: Autenticador,
        repositorio: RepositorioAdministracao | None = None,
        *,
        criar_pipeline: Callable[[], Any] | None = None,
        limite_csv_bytes: int = LIMITE_CSV_MB_PADRAO * 1024 * 1024,
        limite_coleta: int = LIMITE_COLETA_PADRAO,
        caminho_tweetsentbr: Path = CAMINHO_PADRAO_TWEETSENTBR,
        buscar_x: Callable[[str, int], list[dict[str, Any]]] | None = None,
        colecao_analises: Collection | None = None,
        provedor_colecao: Callable[[], AbstractContextManager[Collection]] = _abrir_colecao_analises,
    ) -> None:
        self.autenticador = autenticador
        self.repositorio = repositorio or RepositorioAdministracao()
        self._criar_pipeline = criar_pipeline or _criar_pipeline_padrao
        self._pipeline: Any = None
        self._trava_pipeline = threading.Lock()
        self.limite_csv_bytes = limite_csv_bytes
        self.limite_coleta = limite_coleta
        self.caminho_tweetsentbr = caminho_tweetsentbr
        # Sem função de busca (sem XFETCH_API_KEY), a busca no X fica desligada.
        self.buscar_x = buscar_x
        self._colecao_analises = colecao_analises
        self._provedor_colecao = provedor_colecao
        self._trava_tweetsentbr = threading.Lock()
        self.repositorio.vincular_persistencia(self.repositorio_analises)

    @contextmanager
    def repositorio_analises(self) -> Iterator[RepositorioAnalises]:
        if self._colecao_analises is not None:
            yield RepositorioAnalises(self._colecao_analises)
            return
        with self._provedor_colecao() as colecao:
            yield RepositorioAnalises(colecao)

    def salvar_analises(self, documentos: list[dict[str, Any]]) -> dict[str, int]:
        with self.repositorio_analises() as repositorio:
            return repositorio.salvar_analises(documentos)

    @classmethod
    def do_ambiente(cls) -> ContextoAdministracao:
        chave_xfetch = os.getenv("XFETCH_API_KEY", "").strip()
        return cls(
            Autenticador(ConfiguracaoAdmin.do_ambiente()),
            buscar_x=_buscar_x_padrao if chave_xfetch else None,
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

    def garantir_tweetsentbr(self, repo: RepositorioAnalises | None = None) -> bool:
        """Persiste o corpus TweetSentBR no MongoDB de forma idempotente quando disponível."""
        with self._trava_tweetsentbr:
            if repo is not None:
                return self._sincronizar_tweetsentbr(repo)
            with self.repositorio_analises() as repo_aberto:
                return self._sincronizar_tweetsentbr(repo_aberto)

    def _sincronizar_tweetsentbr(self, repo: RepositorioAnalises) -> bool:
        if repo.possui_dataset(ID_TWEETSENTBR):
            return True
        if not self.caminho_tweetsentbr.is_file():
            return False
        registros = list(iterar_tweetsentbr(self.caminho_tweetsentbr, modo_estrito=False))
        if not registros:
            return False
        repo.salvar_dataset(
            "TweetSentBR",
            registros,
            id_dataset=ID_TWEETSENTBR,
            tipo="corpus",
            origem_coleta="tweetsentbr",
        )
        return True

    def fontes(self) -> list[dict[str, str]]:
        with self.repositorio_analises() as repo:
            tem_tweetsentbr = self._sincronizar_tweetsentbr(repo)
            datasets = repo.listar_datasets(incluir_registros=False)
        fontes = []
        if tem_tweetsentbr:
            fontes.append({"id": ID_TWEETSENTBR, "nome": "TweetSentBR"})
        for dataset in datasets:
            if dataset["id_dataset"] == ID_TWEETSENTBR:
                continue
            fontes.append(
                {
                    "id": dataset["id_dataset"],
                    "nome": f"Dataset importado: {dataset['nome_arquivo']}",
                }
            )
        return fontes

    def registros_da_base(self) -> list[dict[str, Any]]:
        """Tudo o que a API tem no MongoDB: TweetSentBR, datasets, pesquisas X e análises."""
        with self.repositorio_analises() as repo:
            self._sincronizar_tweetsentbr(repo)
            return repo.listar_registros_base()

    def registros_da_fonte(self, fonte: str) -> list[dict[str, Any]]:
        if fonte == ID_TWEETSENTBR:
            with self.repositorio_analises() as repo:
                if not self._sincronizar_tweetsentbr(repo):
                    raise KeyError(fonte)
                dataset = repo.obter_dataset(ID_TWEETSENTBR, incluir_registros=True)
            if dataset is None:
                raise KeyError(fonte)
            return list(dataset.get("registros", []))[: self.limite_coleta]
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
    termo: str | None = None
    quantidade: int | None = None
    complementar_com_x: bool = False
    forcar_atualizacao: bool = False


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

    try:
        dataset = contexto.repositorio.adicionar_dataset(
            nome,
            registros,
            tipo="upload_csv",
            origem_coleta="csv",
            metadados={
                "registros_lidos": len(registros) + relatorio.total_descartados,
                "registros_descartados": relatorio.total_descartados,
            },
        )
    except (
        ErroConfiguracaoMongoDB,
        ErroConexaoMongoDB,
        PyMongoError,
        ErroLeituraAnalises,
    ):
        logger.exception("Falha ao persistir dataset %s", nome)
        return _erro(503, "Banco de dados indisponível ao salvar dataset.")

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
    try:
        return {"fontes": contexto.fontes()}
    except (
        ErroConfiguracaoMongoDB,
        ErroConexaoMongoDB,
        PyMongoError,
        ErroLeituraAnalises,
    ):
        logger.exception("Falha ao listar fontes persistidas")
        return _erro(503, "Banco de dados indisponível ao consultar fontes.")


def _registros_da_coleta(
    contexto: ContextoAdministracao, coleta: Coleta
) -> tuple[list[dict[str, Any]], list[str | None]]:
    """Textos a analisar e a origem de cada um: "base" ou "x" na pesquisa; None nas demais."""
    if coleta.fonte != FONTE_PESQUISA:
        registros = contexto.registros_da_fonte(coleta.fonte)
        return registros, [None] * len(registros)
    assert coleta.termo and coleta.quantidade

    with contexto.repositorio_analises() as repo:
        contexto._sincronizar_tweetsentbr(repo)
        base = repo.listar_registros_base()
        cache = repo.buscar_cache_pesquisa(
            coleta.termo,
            complementar_com_x=coleta.complementar_com_x,
        )

    resultado = pesquisar(
        coleta.termo,
        coleta.quantidade,
        base,
        buscar_x=contexto.buscar_x,
        complementar_com_x=coleta.complementar_com_x,
        cache_pesquisa=cache,
        forcar_atualizacao=coleta.forcar_atualizacao,
    )

    with contexto.repositorio_analises() as repo:
        if resultado.do_x:
            # Os tweets novos entram na base: próximas pesquisas os reaproveitam sem novo custo.
            momento = datetime.now(UTC).strftime("%d/%m %H:%M")
            repo.salvar_dataset(
                f"busca no X por “{coleta.termo}” ({momento} UTC)",
                resultado.do_x,
                tipo="pesquisa_x",
                origem_coleta="xfetch",
                metadados={"termo": coleta.termo},
            )
        pode_cachear = not resultado.cache_reutilizado and (
            not coleta.complementar_com_x
            or resultado.consultou_x
            or len(resultado.registros) >= coleta.quantidade
        )
        if pode_cachear:
            chaves_cache = [
                {"fonte": r["fonte"].strip(), "id_origem": garantir_id_origem(r)}
                for r in resultado.registros
            ]
            repo.salvar_cache_pesquisa(
                coleta.termo,
                complementar_com_x=coleta.complementar_com_x,
                quantidade_solicitada=coleta.quantidade,
                quantidade_atendida=len(resultado.registros),
                esgotado_na_origem=resultado.esgotado_na_origem,
                origem={
                    "base": len(resultado.da_base),
                    "x": len(resultado.do_x),
                    "duplicatas": resultado.duplicatas,
                },
                chaves_registros=chaves_cache,
            )

    contexto.repositorio.atualizar_coleta(
        coleta.id,
        origem={
            "base": len(resultado.da_base),
            "x": len(resultado.do_x),
            "duplicatas": resultado.duplicatas,
        },
        mensagem=resultado.aviso,
    )
    return resultado.registros, resultado.origens


def _resumir_resolvidos(
    resolvidos: dict[int, dict[str, Any]],
    total: int,
    origens: list[str | None],
) -> tuple[dict[str, int], list[dict[str, str]]]:
    por_sentimento = dict.fromkeys(SENTIMENTOS, 0)
    exemplos: list[dict[str, str]] = []
    for posicao in range(total):
        documento = resolvidos.get(posicao)
        if documento is None:
            continue
        sentimento = documento.get("sentimento")
        if sentimento in por_sentimento:
            por_sentimento[sentimento] += 1
        if len(exemplos) < MAXIMO_EXEMPLOS:
            exemplo = {"texto": documento["texto_original"], "sentimento": sentimento}
            if origens[posicao] is not None:
                exemplo["origem"] = origens[posicao]
            exemplos.append(exemplo)
    return por_sentimento, exemplos


def executar_coleta(contexto: ContextoAdministracao, id_coleta: str) -> None:
    """Coleta os textos da fonte e os classifica em lotes, pulando análises já persistidas."""
    from src.processamento.aquisicao.xfetch import ErroXFetch

    repositorio = contexto.repositorio
    coleta = repositorio.obter_coleta(id_coleta)
    if coleta is None:
        return
    try:
        registros, origens = _registros_da_coleta(contexto, coleta)
        repositorio.atualizar_coleta(
            id_coleta, situacao="em_andamento", textos_coletados=len(registros)
        )
        existentes: dict[tuple[str, str], dict[str, Any]] = {}
        if registros:
            chaves = [(r["fonte"].strip(), garantir_id_origem(r)) for r in registros]
            with contexto.repositorio_analises() as repo_analises:
                existentes = repo_analises.obter_analises_por_chaves(chaves)

        resolvidos: dict[int, dict[str, Any]] = {}
        pendentes: list[tuple[int, dict[str, Any]]] = []
        for posicao, registro in enumerate(registros):
            chave = (registro["fonte"].strip(), garantir_id_origem(registro))
            analise = existentes.get(chave)
            if (
                analise is not None
                and analise.get("sentimento") in SENTIMENTOS
                and isinstance(analise.get("texto_original"), str)
            ):
                resolvidos[posicao] = analise
            else:
                if (
                    not isinstance(registro.get("id_origem"), str)
                    or not registro["id_origem"].strip()
                ):
                    registro = {**registro, "id_origem": chave[1]}
                pendentes.append((posicao, registro))

        analisados = len(resolvidos)
        if pendentes:
            pipeline = contexto.pipeline()
            for inicio in range(0, len(pendentes), TAMANHO_LOTE_ANALISE):
                fatia = pendentes[inicio : inicio + TAMANHO_LOTE_ANALISE]
                lote = [reg for _, reg in fatia]
                documentos = pipeline.processar_registros(lote)
                contexto.salvar_analises(documentos)
                for (posicao, _), documento in zip(fatia, documentos):
                    resolvidos[posicao] = documento
                analisados += len(lote)
                por_sentimento, exemplos = _resumir_resolvidos(
                    resolvidos, len(registros), origens
                )
                repositorio.atualizar_coleta(
                    id_coleta,
                    textos_analisados=analisados,
                    por_sentimento=por_sentimento,
                    exemplos=exemplos,
                )
        elif resolvidos:
            por_sentimento, exemplos = _resumir_resolvidos(
                resolvidos, len(registros), origens
            )
            repositorio.atualizar_coleta(
                id_coleta,
                textos_analisados=analisados,
                por_sentimento=por_sentimento,
                exemplos=exemplos,
            )
        campos: dict[str, Any] = {"situacao": "concluida"}
        if not registros and not repositorio.obter_coleta(id_coleta).mensagem:
            campos["mensagem"] = "Nenhum texto encontrado para analisar."
        repositorio.atualizar_coleta(id_coleta, **campos)
    except ErroClassificadorIndisponivel:
        repositorio.atualizar_coleta(
            id_coleta,
            situacao="falhou",
            mensagem="O classificador de sentimentos não está instalado neste servidor.",
        )
    except ErroXFetch as erro:
        # As mensagens do módulo XFetch não trazem chave, cabeçalhos nem consulta.
        repositorio.atualizar_coleta(id_coleta, situacao="falhou", mensagem=str(erro))
    except (
        ErroConfiguracaoMongoDB,
        ErroConexaoMongoDB,
        PyMongoError,
        ErroLeituraAnalises,
    ):
        logger.exception("Falha de persistência na coleta %s", id_coleta)
        repositorio.atualizar_coleta(
            id_coleta,
            situacao="falhou",
            mensagem="Banco de dados indisponível ao consultar ou salvar análises.",
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
    termo = quantidade = None
    if corpo.fonte == FONTE_PESQUISA:
        termo = " ".join((corpo.termo or "").split())
        if not termo or len(termo) > TAMANHO_MAXIMO_TERMO:
            return _erro(422, "Informe uma palavra ou frase de até 100 caracteres.")
        quantidade = corpo.quantidade
        if quantidade is None or not 1 <= quantidade <= QUANTIDADE_MAXIMA_PESQUISA:
            return _erro(422, "A meta de textos deve ficar entre 1 e 100.")
    else:
        try:
            fontes_disponiveis = {f["id"] for f in contexto.fontes()}
        except (
            ErroConfiguracaoMongoDB,
            ErroConexaoMongoDB,
            PyMongoError,
            ErroLeituraAnalises,
        ):
            logger.exception("Falha ao validar fonte de coleta %s", corpo.fonte)
            return _erro(503, "Banco de dados indisponível ao validar fonte de coleta.")
        if corpo.fonte not in fontes_disponiveis:
            return _erro(422, "Fonte de coleta desconhecida.")
    coleta = contexto.repositorio.criar_coleta(
        corpo.fonte,
        termo,
        quantidade,
        corpo.complementar_com_x,
        corpo.forcar_atualizacao,
    )
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
