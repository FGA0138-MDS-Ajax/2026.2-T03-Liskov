"""Compatibilidade histórica para consultas à coleção de análises.

As operações e validações vivem em ``src.dados.repositorio``. Este módulo
mantém assinaturas usadas por consumidores antigos e delega ao repositório
canônico, sem implementar outra camada MongoDB.
"""

from typing import Any

from pymongo.collection import Collection

from src.dados.repositorio import (
    ErroConsultaInvalida,
    ErroLeituraAnalises,
    RepositorioAnalises,
    buscar_por_id,
    buscar_por_id_origem,
    contar_analises,
    contar_por_sentimento,
    montar_filtro,
    serializar_analise,
)

LIMITE_PADRAO = 50
LIMITE_MAXIMO = 500

__all__ = [
    "ErroConsultaInvalida", "ErroLeituraAnalises", "LIMITE_MAXIMO", "LIMITE_PADRAO",
    "buscar_por_id", "buscar_por_id_origem", "contar_analises",
    "contar_por_sentimento", "listar_analises", "montar_filtro", "serializar_analise",
]


def listar_analises(
    colecao: Collection,
    filtro: dict[str, Any] | None = None,
    *,
    limite: int = LIMITE_PADRAO,
    pular: int = 0,
) -> list[dict[str, Any]]:
    """Assinatura legada delegada ao repositório canônico."""
    return RepositorioAnalises(colecao).listar_com_filtro(
        filtro, limite=limite, pular=pular
    )
