"""Contrato de dados entre as telas do painel e a origem das análises.

As telas dependem apenas destes tipos. Trocar os dados de exemplo pela API real
não exige alterar as telas (ver docs/frontend/CONTRATO-API.md).
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Literal, Protocol

Sentimento = Literal["positivo", "neutro", "negativo"]

# Ordem de exibição definida no wireframe do dashboard.
SENTIMENTOS: tuple[Sentimento, ...] = ("positivo", "neutro", "negativo")


class ErroFonteDados(Exception):
    """Falha ao obter dados. A mensagem é exibida ao usuário e deve ser clara."""


@dataclass(frozen=True)
class FiltrosAnalises:
    """Filtros de consulta. `None` significa que o filtro não foi aplicado."""

    inicio: date | None = None
    fim: date | None = None  # inclusivo
    sentimento: Sentimento | None = None


@dataclass(frozen=True)
class Analise:
    """Um texto analisado (subconjunto de docs/banco/esquema-mongodb.md)."""

    id_origem: str
    fonte: str
    texto_original: str
    sentimento: Sentimento  # previsão do modelo, não uma certeza
    modelo_nome: str
    data_processamento: datetime
    data_publicacao: datetime | None = None  # nunca é inventada


@dataclass(frozen=True)
class PaginaAnalises:
    """Índices positivos, total não negativo; itens limitados à página solicitada."""

    itens: list[Analise]
    pagina: int
    tamanho: int
    total: int


@dataclass(frozen=True)
class ResumoAnalises:
    """Total filtrado igual à soma das três classes; excluídos não compõem o total."""

    total: int
    por_sentimento: dict[Sentimento, int]
    # Registros deixados de fora do filtro de período por não terem data.
    sem_data_publicacao: int = 0


class FonteAnalises(Protocol):
    """Fronteira de integração implementada por `FonteMock` e `FonteApi`."""

    def listar(
        self, filtros: FiltrosAnalises, pagina: int = 1, tamanho: int = 20
    ) -> PaginaAnalises: ...

    def resumir(self, filtros: FiltrosAnalises) -> ResumoAnalises: ...


# --- Administração (RF01, RF02, UC01 a UC03, T01 a T03) -------------------------
# O Administrador entra com login e senha (decisão da PO de 07/11/2026). As rotas
# são uma PROPOSTA do frontend; ver docs/frontend/CONTRATO-API.md.


class ErroAutenticacao(ErroFonteDados):
    """Credencial recusada ou sessão expirada. A tela volta para o login."""


@dataclass(frozen=True)
class SessaoAdministrador:
    """Sessão emitida pela API. O token nunca é exibido nem gravado em disco."""

    token: str = field(repr=False)
    usuario: str
    expira_em: datetime

    def expirada(self, agora: datetime | None = None) -> bool:
        return (agora or datetime.now(UTC)) >= self.expira_em


@dataclass(frozen=True)
class ResultadoImportacao:
    """Relatório de importação; lidos = importados + descartados."""

    id_dataset: str
    nome_arquivo: str
    registros_lidos: int
    registros_importados: int
    registros_descartados: int
    descartes_por_motivo: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class FonteColeta:
    """Origem que o Administrador pode coletar e analisar."""

    id: str
    nome: str


SituacaoColeta = Literal["pendente", "em_andamento", "concluida", "falhou"]
SITUACOES_COLETA: tuple[SituacaoColeta, ...] = (
    "pendente",
    "em_andamento",
    "concluida",
    "falhou",
)


@dataclass(frozen=True)
class ExemploAnalise:
    """Texto analisado na coleta, com o sentimento previsto pelo modelo."""

    texto: str
    sentimento: Sentimento
    origem: str | None = None  # Na pesquisa: "base" (já guardado) ou "x" (tweet novo).


@dataclass(frozen=True)
class Coleta:
    """Execução de coleta e análise; textos analisados nunca superam os coletados."""

    id: str
    fonte: str
    situacao: SituacaoColeta
    textos_coletados: int = 0
    textos_analisados: int = 0
    mensagem: str | None = None
    termo: str | None = None  # Só na pesquisa por assunto.
    # Na pesquisa: textos vindos da base, do X e repetidos descartados.
    origem: dict[str, int] | None = None
    # Resultado parcial ou final: contagem por sentimento e alguns textos analisados.
    por_sentimento: dict[Sentimento, int] = field(default_factory=dict)
    exemplos: tuple[ExemploAnalise, ...] = ()


# Pesquisa híbrida por assunto (docs/pesquisa_hibrida_mongodb_xfetch.md): a API procura
# primeiro na base do SentIA e, se faltar e for permitido, completa com tweets do X.
FONTE_PESQUISA = "pesquisa"
QUANTIDADE_BUSCA_PADRAO = 5
PASSO_QUANTIDADE_BUSCA = 5
QUANTIDADE_BUSCA_MAXIMA = 100
TAMANHO_MAXIMO_TERMO = 100


class FonteAdministracao(Protocol):
    """Operações do Administrador, implementadas pelo mock e pelo cliente HTTP."""

    def entrar(self, usuario: str, senha: str) -> SessaoAdministrador: ...

    def sair(self, sessao: SessaoAdministrador) -> None: ...

    def importar_dataset(
        self, sessao: SessaoAdministrador, nome_arquivo: str, conteudo: bytes
    ) -> ResultadoImportacao: ...

    def listar_fontes_coleta(self, sessao: SessaoAdministrador) -> list[FonteColeta]: ...

    def iniciar_coleta(self, sessao: SessaoAdministrador, fonte: str) -> Coleta: ...

    def pesquisar(
        self,
        sessao: SessaoAdministrador,
        termo: str,
        quantidade: int,
        complementar_com_x: bool,
    ) -> Coleta: ...

    def consultar_coleta(self, sessao: SessaoAdministrador, id_coleta: str) -> Coleta: ...
