from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from src.dados.repositorio import ErroAnaliseInvalida, salvar_analises
from src.processamento.pipeline import ErroPipeline, PipelineClassificacao
from src.servico.dependencias import obter_colecao_analises, obter_pipeline
from src.servico.esquemas import Erro, LoteEntrada, ResultadoProcessamento

app = FastAPI(title="SentIA API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/analises",
    status_code=status.HTTP_201_CREATED,
    response_model=ResultadoProcessamento,
    responses={400: {"model": Erro}, 503: {"model": Erro}},
)
def processar_analises(
    lote: LoteEntrada,
    pipeline: Annotated[PipelineClassificacao, Depends(obter_pipeline)],
    colecao: Annotated[Collection, Depends(obter_colecao_analises)],
):
    registros = [registro.model_dump(exclude_none=True) for registro in lote.registros]

    try:
        documentos = pipeline.processar_registros(registros)
        resumo = salvar_analises(colecao, documentos)
    except (ErroPipeline, ErroAnaliseInvalida) as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(erro),
        ) from erro
    except PyMongoError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponível.",
        ) from erro

    return ResultadoProcessamento(recebidos=len(registros), **resumo)
