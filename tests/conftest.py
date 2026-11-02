"""Configurações globais, fixtures reutilizáveis e resolução de contrato para o pytest.

Este módulo concentra as fixtures da suíte de testes da Sprint 1 (Issue #4),
cobrindo os requisitos RF01/US01 (Importação de CSV - Issue #2) e
RF02/US02 (Aquisição de textos / TweetSentBR - Issue #1).

Contrato homologado (Issues #2, #4, #11 e #19):
-----------------------------------------------
1. Aquisição de dados (Issue #1 — RF02/US02):
   - Módulo: ``src.processamento.aquisicao`` (ou submódulo dedicado ao TweetSentBR)
   - Função principal: ``adquirir_dados(origem: str | Path, fonte: str = "TweetSentBR") -> list[dict[str, Any]]``
   - Estrutura de cada registro retornado (dict):
     * ``id_origem``: ``str`` não vazio (preservado da fonte ou determinístico)
     * ``texto_original``: ``str`` com o conteúdo textual original preservado
     * ``fonte``: ``str`` identificando a origem (ex.: ``"TweetSentBR"``)
     * ``rotulo_original``: ``str | None`` (valor original do dataset ou ``None`` se sem anotação)
     * ``rotulo_padronizado``: ``"POS" | "NEG" | "NEU" | None``
     * ``data_publicacao``: ``str | None`` (data da publicação ou ``None`` se ausente)
     * Nota: o campo ``sentimento`` pertence exclusivamente à saída de classificação ML e não deve ser criado na aquisição/importação.

2. Importação de CSV (Issue #2 — RF01/US01):
   - Módulo: ``src.processamento.aquisicao`` / ``src.processamento.aquisicao.csv_importer``
   - Funções principais: ``importar_csv`` / ``importar_dataset_csv`` e ``iterar_csv`` / ``iterar_dataset_csv``
   - Colunas obrigatórias no CSV padrão: ``texto`` (ou ``texto_original``) e ``fonte``
   - Colunas opcionais: ``id_origem``/``id``/``identificador``, ``rotulo_original``/``rotulo``/``sentimento``, ``data_publicacao``/``data`` e metadados extras
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
    "src.processamento.aquisicao",
    "src.processamento.aquisicao.tweetsentbr",
    "src.processamento.aquisicao.aquisicao",
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
    "src.processamento.aquisicao",
    "src.processamento.aquisicao.csv_importer",
    "sentia.importacao",
    "src.importacao",
    "importacao",
    "sentia.dados.importacao",
    "src.dados.importacao",
)
FUNCOES_CANDIDATAS_IMPORTACAO: tuple[str, ...] = (
    "importar_csv",
    "importar_dataset_csv",
    "carregar_csv",
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
    """Extrai o identificador de um registro priorizando 'id_origem' (contrato homologado)."""
    if "id_origem" in registro:
        return registro["id_origem"]
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
    """Retorna os registros esperados após leitura de ``dataset_valido.csv`` no contrato aprovado."""
    return [
        {
            "id_origem": "tw_001",
            "texto_original": "A programação da conferência foi ótima e trouxe inovação ao país!",
            "rotulo_original": "positivo",
            "rotulo_padronizado": "POS",
            "fonte": "TweetSentBR",
            "data_publicacao": "2026-10-01",
        },
        {
            "id_origem": "tw_002",
            "texto_original": "Péssimo serviço de atenção ao usuário, não recomendo de jeito nenhum.",
            "rotulo_original": "negativo",
            "rotulo_padronizado": "NEG",
            "fonte": "TweetSentBR",
            "data_publicacao": "2026-10-02",
        },
        {
            "id_origem": "tw_003",
            "texto_original": "O relatório técnico sobre inteligência artificial foi publicado hoje.",
            "rotulo_original": "neutro",
            "rotulo_padronizado": "NEU",
            "fonte": "TweetSentBR",
            "data_publicacao": "2026-10-03",
        },
        {
            "id_origem": "tw_004",
            "texto_original": "A seleção brasileira venceu a partida com atuação incrível da equipe.",
            "rotulo_original": "positivo",
            "rotulo_padronizado": "POS",
            "fonte": "TweetSentBR",
            "data_publicacao": "2026-10-04",
        },
        {
            "id_origem": "tw_005",
            "texto_original": "O sistema permaneceu indisponível durante a manutenção programada.",
            "rotulo_original": "negativo",
            "rotulo_padronizado": "NEG",
            "fonte": "TweetSentBR",
            "data_publicacao": None,
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
