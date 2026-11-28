from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from src.dados.repositorio import (
    ErroAnaliseInvalida,
    ErroConsultaInvalida,
    ErroLeituraAnalises,
    RepositorioAnalises,
)

from src.processamento.pipeline import (
    ErroInferencia,
    ErroPipeline,
    PipelineClassificacao,
)
from src.servico.dependencias import obter_colecao_analises, obter_pipeline
from src.servico.esquemas import (
    ConsultaAnalises,
    ConsultaEvolucao,
    ConsultaTermos,
    Erro,
    EvolucaoSaida,
    FiltrosConsulta,
    LoteEntrada,
    PaginaAnalisesSaida,
    ResultadoProcessamento,
    ResumoAnalisesSaida,
    TermosSaida,
)

from .administracao import (
    NaoAutenticado,
    responder_nao_autenticado,
    roteador,
)

app = FastAPI(title="SentIA API")
app.add_exception_handler(NaoAutenticado, responder_nao_autenticado)
app.include_router(roteador)


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
    colecao: Annotated[
        Collection,
        Depends(obter_colecao_analises, scope="function"),
    ],
):
    registros = [registro.model_dump(exclude_none=True) for registro in lote.registros]

    try:
        documentos = pipeline.processar_registros(registros)
        resumo = RepositorioAnalises(colecao).salvar_analises(documentos)
    except ErroInferencia as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de classificação indisponível.",
        ) from erro
    except (ErroPipeline, ErroAnaliseInvalida) as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(erro),
        ) from erro
    except (PyMongoError, ErroLeituraAnalises) as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponível.",
        ) from erro

    return ResultadoProcessamento(recebidos=len(registros), **resumo)


@app.get("/analises", response_model=PaginaAnalisesSaida, responses={503: {"model": Erro}})
def consultar_analises(
    consulta: Annotated[ConsultaAnalises, Query()],
    colecao: Annotated[Collection, Depends(obter_colecao_analises, scope="function")],
):
    try:
        return RepositorioAnalises(colecao).listar_analises(**consulta.model_dump())
    except ErroConsultaInvalida as erro:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(erro)) from erro
    except (PyMongoError, ErroLeituraAnalises) as erro:
        raise HTTPException(
            503, "Banco de dados indisponível."
        ) from erro


@app.get("/analises/resumo", response_model=ResumoAnalisesSaida, responses={503: {"model": Erro}})
def consultar_resumo(
    filtros: Annotated[FiltrosConsulta, Query()],
    colecao: Annotated[Collection, Depends(obter_colecao_analises, scope="function")],
):
    try:
        return RepositorioAnalises(colecao).resumir_analises(**filtros.model_dump())
    except ErroConsultaInvalida as erro:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(erro)) from erro
    except (PyMongoError, ErroLeituraAnalises) as erro:
        raise HTTPException(
            503, "Banco de dados indisponível."
        ) from erro


@app.get("/analises/termos", response_model=TermosSaida, responses={503: {"model": Erro}})
def consultar_termos(
    consulta: Annotated[ConsultaTermos, Query()],
    colecao: Annotated[Collection, Depends(obter_colecao_analises, scope="function")],
):
    """Termos mais frequentes nos textos do filtro (#30), para o gráfico de barras."""
    try:
        return RepositorioAnalises(colecao).termos_frequentes(**consulta.model_dump())
    except ErroConsultaInvalida as erro:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(erro)) from erro
    except (PyMongoError, ErroLeituraAnalises) as erro:
        raise HTTPException(503, "Banco de dados indisponível.") from erro


@app.get("/analises/evolucao", response_model=EvolucaoSaida, responses={503: {"model": Erro}})
def consultar_evolucao(
    consulta: Annotated[ConsultaEvolucao, Query()],
    colecao: Annotated[Collection, Depends(obter_colecao_analises, scope="function")],
):
    """Análises por dia, semana ou mês e por sentimento (#121), só com textos datados."""
    try:
        return RepositorioAnalises(colecao).evolucao_analises(**consulta.model_dump())
    except ErroConsultaInvalida as erro:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(erro)) from erro
    except (PyMongoError, ErroLeituraAnalises) as erro:
        raise HTTPException(503, "Banco de dados indisponível.") from erro

