"""Contrato de dados entre as telas do painel e a origem das análises.

As telas dependem apenas destes tipos. Trocar os dados de exemplo pela API real
não exige alterar as telas (ver docs/frontend/CONTRATO-API.md).
"""

from dataclasses import dataclass
from datetime import date, datetime
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
    itens: list[Analise]
    pagina: int
    tamanho: int
    total: int


@dataclass(frozen=True)
class ResumoAnalises:
    """Totais calculados sobre todos os registros que atendem aos filtros."""

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
