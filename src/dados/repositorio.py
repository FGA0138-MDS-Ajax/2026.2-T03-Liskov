from datetime import UTC, date, datetime, time
from typing import Any

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, DuplicateKeyError
from pymongo.mongo_client import MongoClient

NOME_BANCO_PADRAO = "sentia"
NOME_COLECAO = "analises"
SENTIMENTOS_VALIDOS = {"positivo", "negativo", "neutro"}
CAMPOS_TEXTO_OBRIGATORIOS = ("id_origem", "fonte", "texto_original")


class ErroAnaliseInvalida(ValueError):
    """Documento fora do esquema da coleção analises."""


INDICES = [
    IndexModel(
        [("fonte", ASCENDING), ("id_origem", ASCENDING)],
        unique=True,
        name="uq_fonte_id_origem",
    ),
    IndexModel(
        [("sentimento", ASCENDING), ("data_publicacao", ASCENDING)],
        name="idx_sentimento_data_publicacao",
    ),
    IndexModel([("data_publicacao", ASCENDING)], name="idx_data_publicacao"),
    IndexModel([("data_processamento", ASCENDING)], name="idx_data_processamento"),
]


def obter_colecao(client: MongoClient, nome_banco: str | None = None):

    if nome_banco is None:
        banco = client.get_default_database(NOME_BANCO_PADRAO)

    else:
        banco = client[nome_banco]

    return banco[NOME_COLECAO]


def criar_indices(colecao: Collection):

    return colecao.create_indexes(INDICES)


def validar_analise(documento: dict[str, Any]):

    for campo in CAMPOS_TEXTO_OBRIGATORIOS:
        valor = documento.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ErroAnaliseInvalida(f"Campo obrigatório ausente ou vazio: {campo}")

    if documento.get("sentimento") not in SENTIMENTOS_VALIDOS:
        raise ErroAnaliseInvalida("Sentimento deve ser positivo, negativo ou neutro")

    modelo = documento.get("modelo")
    if not isinstance(modelo, dict) or not modelo.get("nome"):
        raise ErroAnaliseInvalida("modelo.nome deve ser obrigatório")

    if "data_processamento" not in documento:
        raise ErroAnaliseInvalida("data_processamento deve ser obrigatória")

    for campo in ("data_processamento", "data_publicacao"):
        if campo in documento:
            data = documento[campo]
            if not isinstance(data, datetime) or data.tzinfo is None:
                raise ErroAnaliseInvalida(
                    f"{campo} deve ser uma data com fuso horário (UTC)"
                )


def salvar_analise(colecao: Collection, documento: dict[str, Any]):

    validar_analise(documento)
    try:
        colecao.insert_one(dict(documento))
    except DuplicateKeyError:
        return False
    return True


def salvar_analises(colecao: Collection, documentos: list[dict[str, Any]]):

    copias = [dict(documento) for documento in documentos]
    for copia in copias:
        validar_analise(copia)

    if not copias:
        return {"inseridos": 0, "duplicados": 0}

    try:
        resultado = colecao.insert_many(copias, ordered=False)
    except BulkWriteError as erro:
        falhas = erro.details["writeErrors"]
        if erro.details.get("writeConcernErrors") or any(
            falha["code"] != 11000 for falha in falhas
        ):
            raise
        return {"inseridos": erro.details["nInserted"], "duplicados": len(falhas)}
    return {"inseridos": len(resultado.inserted_ids), "duplicados": 0}


def _filtro_consulta(
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
) -> dict[str, Any]:
    filtro: dict[str, Any] = {}
    if sentimento is not None:
        filtro["sentimento"] = sentimento
    periodo = {}
    if inicio is not None:
        periodo["$gte"] = datetime.combine(inicio, time.min, UTC)
    if fim is not None:
        periodo["$lte"] = datetime.combine(fim, time.max, UTC)
    if periodo:
        filtro["data_publicacao"] = periodo
    return filtro


def listar_analises(
    colecao: Collection,
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
    pagina: int = 1,
    tamanho: int = 20,
) -> dict[str, Any]:
    filtro = _filtro_consulta(inicio, fim, sentimento)
    total = colecao.count_documents(filtro)
    # A chave única (fonte, id_origem) desempata datas iguais de forma estável.
    cursor = (
        colecao.find(filtro, {"_id": 0})
        .sort([("data_processamento", -1), ("fonte", 1), ("id_origem", 1)])
        .skip((pagina - 1) * tamanho)
        .limit(tamanho)
    )
    return {"itens": list(cursor), "pagina": pagina, "tamanho": tamanho, "total": total}


def resumir_analises(
    colecao: Collection,
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
) -> dict[str, Any]:
    filtro = _filtro_consulta(inicio, fim, sentimento)
    contagens = {classe: 0 for classe in ("positivo", "negativo", "neutro")}
    for grupo in colecao.aggregate([
        {"$match": filtro},
        {"$group": {"_id": "$sentimento", "total": {"$sum": 1}}},
    ]):
        contagens[grupo["_id"]] = grupo["total"]
    sem_data = 0
    if inicio is not None or fim is not None:
        filtro_sem_data = {"data_publicacao": None}
        if sentimento is not None:
            filtro_sem_data["sentimento"] = sentimento
        sem_data = colecao.count_documents(filtro_sem_data)
    return {
        "total": sum(contagens.values()),
        "por_sentimento": contagens,
        "sem_data_publicacao": sem_data,
    }
