from collections.abc import Iterator
from functools import lru_cache

from fastapi import HTTPException, status
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from src.dados.database import (
    ErroConexaoMongoDB,
    ErroConfiguracaoMongoDB,
    connect_to_mongodb,
    disconnect_from_mongodb,
)
from src.dados.repositorio import criar_indices, obter_colecao
from src.processamento.pipeline import PipelineClassificacao


def obter_colecao_analises() -> Iterator[Collection]:
    try:
        client = connect_to_mongodb()
        try:
            colecao = obter_colecao(client)
            criar_indices(colecao)
            yield colecao
        finally:
            disconnect_from_mongodb(client)
    except (ErroConfiguracaoMongoDB, ErroConexaoMongoDB, PyMongoError) as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponível.",
        ) from erro


@lru_cache(maxsize=1)
def _carregar_pipeline() -> PipelineClassificacao:
    return PipelineClassificacao()


def obter_pipeline() -> PipelineClassificacao:
    try:
        return _carregar_pipeline()
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Classificador indisponível.",
        ) from erro
