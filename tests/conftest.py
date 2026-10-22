"""Configurações globais, fixtures reutilizáveis e resolução de contrato para o pytest.

Este módulo concentra as fixtures da suíte de testes da Sprint 1 (Issue #4),
cobrindo os requisitos RF01/US01 (Importação de CSV - Issue #2) e
RF02/US02 (Aquisição de textos / TweetSentBR - Issue #1).

Contrato mínimo proposto (a alinhar com Breno nas Issues #1 e #2):
------------------------------------------------------------------
1. Aquisição de dados (Issue #1 — RF02/US02):
   - Módulo sugerido: ``src.aquisicao`` ou ``sentia.aquisicao`` (ou ``aquisicao``)
   - Função principal: ``adquirir_dados(origem: str | Path, fonte: str = "TweetSentBR") -> list[dict[str, Any]]``
   - Estrutura de cada registro retornado (dict):
     * ``id`` (ou ``identificador``): ``str | int`` não vazio
     * ``texto``: ``str`` com o conteúdo textual original preservado
     * ``fonte``: ``str`` identificando a origem (ex.: ``"TweetSentBR"``)
     * ``sentimento`` (opcional/quando existente): ``str | None`` (ex.: ``"positivo"``, ``"negativo"``, ``"neutro"``)
     * ``data`` (opcional/quando existente): ``str | None`` (ISO 8601 ou ``None`` se ausente)
   - Exceções esperadas em falhas previsíveis:
     * Fonte/arquivo inexistente: ``FileNotFoundError`` ou ``ValueError``
     * Fonte indisponível (permissão, diretório inválido, falha de leitura/IO): ``OSError``, ``ConnectionError``, ``RuntimeError`` ou ``ValueError``
     * Entrada vazia, sem registros válidos ou formato inesperado: ``ValueError`` ou ``TypeError``

2. Importação de CSV (Issue #2 — RF01/US01):
   - Módulo sugerido: ``src.importacao`` ou ``sentia.importacao`` (ou ``importacao``)
   - Função principal: ``importar_csv(caminho_arquivo: str | Path, encoding: str = "utf-8") -> list[dict[str, Any]]``
   - Colunas mínimas esperadas no CSV: ``texto`` (e ``id``/``identificador``, ``sentimento``, ``fonte``, ``data`` quando disponíveis)
   - Exceções esperadas:
     * Arquivo inexistente: ``FileNotFoundError`` ou ``ValueError``
     * CSV vazio, apenas cabeçalho, colunas obrigatórias ausentes ou estrutura inválida: ``ValueError`` (ou ``UnicodeDecodeError`` para encoding incompatível)
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

DIRETORIO_TESTES = Path(__file__).resolve().parent
DIRETORIO_RAIZ = DIRETORIO_TESTES.parent
DIRETORIO_FIXTURES = DIRETORIO_TESTES / "fixtures"

if str(DIRETORIO_RAIZ) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_RAIZ))

MODULOS_CANDIDATOS_AQUISICAO: tuple[str, ...] = (
    "sentia.aquisicao",
    "src.aquisicao",
    "aquisicao",
    "sentia.dados.aquisicao",
    "src.dados.aquisicao",
)
FUNCOES_CANDIDATAS_AQUISICAO: tuple[str, ...] = (
    "adquirir_dados",
    "carregar_tweetsentbr",
    "adquirir_textos",
    "obter_textos",
)

MODULOS_CANDIDATOS_IMPORTACAO: tuple[str, ...] = (
    "sentia.importacao",
    "src.importacao",
    "importacao",
    "sentia.dados.importacao",
    "src.dados.importacao",
)
FUNCOES_CANDIDATAS_IMPORTACAO: tuple[str, ...] = (
    "importar_csv",
    "carregar_csv",
    "importar_dataset_csv",
)

CARACTERES_PT_BR_OBRIGATORIOS: tuple[str, ...] = ("ç", "ã", "é", "í")


def _resolver_funcao_producao(
    modulos_candidatos: tuple[str, ...],
    funcoes_candidatas: tuple[str, ...],
) -> Callable[..., Any] | None:
    """Procura dinamicamente uma função de produção nos módulos candidatos."""
    for nome_modulo in modulos_candidatos:
        try:
            modulo = importlib.import_module(nome_modulo)
        except ModuleNotFoundError:
            continue

        for nome_funcao in funcoes_candidatas:
            atributo = getattr(modulo, nome_funcao, None)
            if callable(atributo):
                return atributo

    return None


def extrair_identificador(registro: dict[str, Any]) -> Any:
    """Extrai o identificador de um registro aceitando 'id' ou 'identificador'."""
    if "id" in registro:
        return registro["id"]
    if "identificador" in registro:
        return registro["identificador"]
    return None


@pytest.fixture(scope="session")
def diretorio_fixtures() -> Path:
    """Retorna o caminho absoluto para o diretório de fixtures."""
    assert DIRETORIO_FIXTURES.is_dir(), (
        f"Diretório de fixtures não encontrado em: {DIRETORIO_FIXTURES}"
    )
    return DIRETORIO_FIXTURES


@pytest.fixture(scope="session")
def arquivo_csv_valido(diretorio_fixtures: Path) -> Path:
    """Retorna o caminho para o arquivo CSV válido controlado."""
    caminho = diretorio_fixtures / "dataset_valido.csv"
    assert caminho.is_file(), f"Fixture obrigatória ausente: {caminho}"
    return caminho


@pytest.fixture(scope="session")
def arquivo_csv_vazio(diretorio_fixtures: Path) -> Path:
    """Retorna o caminho para o arquivo CSV vazio (0 bytes)."""
    caminho = diretorio_fixtures / "dataset_vazio.csv"
    assert caminho.is_file(), f"Fixture obrigatória ausente: {caminho}"
    return caminho


@pytest.fixture(scope="session")
def arquivo_csv_invalido(diretorio_fixtures: Path) -> Path:
    """Retorna o caminho para o arquivo CSV com colunas obrigatórias ausentes."""
    caminho = diretorio_fixtures / "dataset_invalido.csv"
    assert caminho.is_file(), f"Fixture obrigatória ausente: {caminho}"
    return caminho


@pytest.fixture
def arquivo_csv_apenas_cabecalho(tmp_path: Path) -> Path:
    """Cria um CSV temporário contendo apenas a linha de cabeçalho, sem registros."""
    caminho = tmp_path / "dataset_apenas_cabecalho.csv"
    caminho.write_text("id,texto,sentimento,fonte,data\n", encoding="utf-8")
    return caminho


@pytest.fixture
def arquivo_csv_registros_em_branco(tmp_path: Path) -> Path:
    """Cria um CSV temporário cujas linhas possuem apenas espaços ou texto vazio."""
    caminho = tmp_path / "dataset_registros_em_branco.csv"
    conteudo = (
        "id,texto,sentimento,fonte,data\n"
        'tw_010,"   ",neutro,TweetSentBR,2026-10-05\n'
        'tw_011,"",positivo,TweetSentBR,2026-10-06\n'
    )
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


@pytest.fixture
def arquivo_csv_estrutura_corrompida(tmp_path: Path) -> Path:
    """Cria um arquivo com estrutura malformada (aspas não fechadas e colunas quebradas)."""
    caminho = tmp_path / "dataset_corrompido.csv"
    conteudo = (
        "id,texto,sentimento,fonte,data\n"
        'tw_001,"Texto com aspas nao fechadas,positivo,TweetSentBR\n'
        "linha_sem_delimitadores_validos\n"
    )
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


@pytest.fixture(scope="session")
def registros_esperados_valido() -> list[dict[str, Any]]:
    """Retorna os registros esperados após leitura de ``dataset_valido.csv``."""
    return [
        {
            "id": "tw_001",
            "texto": "A programação da conferência foi ótima e trouxe inovação ao país!",
            "sentimento": "positivo",
            "fonte": "TweetSentBR",
            "data": "2026-10-01",
        },
        {
            "id": "tw_002",
            "texto": "Péssimo serviço de atenção ao usuário, não recomendo de jeito nenhum.",
            "sentimento": "negativo",
            "fonte": "TweetSentBR",
            "data": "2026-10-02",
        },
        {
            "id": "tw_003",
            "texto": "O relatório técnico sobre inteligência artificial foi publicado hoje.",
            "sentimento": "neutro",
            "fonte": "TweetSentBR",
            "data": "2026-10-03",
        },
        {
            "id": "tw_004",
            "texto": "A seleção brasileira venceu a partida com atuação incrível da equipe.",
            "sentimento": "positivo",
            "fonte": "TweetSentBR",
            "data": "2026-10-04",
        },
        {
            "id": "tw_005",
            "texto": "O sistema permaneceu indisponível durante a manutenção programada.",
            "sentimento": "negativo",
            "fonte": "TweetSentBR",
            "data": None,
        },
    ]


@pytest.fixture
def adquirir_dados() -> Callable[..., list[dict[str, Any]]]:
    """Resolve a função de aquisição (Issue #1 / RF02) ou registra o teste como BLOQUEADO."""
    funcao = _resolver_funcao_producao(
        MODULOS_CANDIDATOS_AQUISICAO,
        FUNCOES_CANDIDATAS_AQUISICAO,
    )
    if funcao is None:
        pytest.skip(
            "BLOQUEADO [Issue #1 / RF02]: Módulo de aquisição de dados ainda não implementado "
            f"(procurado em {MODULOS_CANDIDATOS_AQUISICAO} -> {FUNCOES_CANDIDATAS_AQUISICAO}). "
            "Aguardando implementação e confirmação de contrato com Breno."
        )
    return funcao


@pytest.fixture
def importar_csv() -> Callable[..., list[dict[str, Any]]]:
    """Resolve a função de importação CSV (Issue #2 / RF01) ou registra o teste como BLOQUEADO."""
    funcao = _resolver_funcao_producao(
        MODULOS_CANDIDATOS_IMPORTACAO,
        FUNCOES_CANDIDATAS_IMPORTACAO,
    )
    if funcao is None:
        pytest.skip(
            "BLOQUEADO [Issue #2 / RF01]: Módulo de importação CSV ainda não implementado "
            f"(procurado em {MODULOS_CANDIDATOS_IMPORTACAO} -> {FUNCOES_CANDIDATAS_IMPORTACAO}). "
            "Aguardando implementação e confirmação de contrato com Breno."
        )
    return funcao
