from datetime import UTC, date, datetime, time
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, DuplicateKeyError, PyMongoError
from pymongo.mongo_client import MongoClient

NOME_BANCO_PADRAO = "sentia"
NOME_COLECAO = "analises"
SENTIMENTOS_VALIDOS = {"positivo", "negativo", "neutro"}
CAMPOS_TEXTO_OBRIGATORIOS = ("id_origem", "fonte", "texto_original")


class ErroAnaliseInvalida(ValueError):
    """Documento fora do esquema da coleção analises."""


class ErroConsultaInvalida(ValueError):
    """Chave natural inválida para a busca de uma análise."""


class ErroLeituraAnalises(RuntimeError):
    """Falha de leitura com mensagem segura, sem URI ou credenciais."""


def _buscar_analise(colecao: Collection, filtro: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return colecao.find_one(filtro)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None


def buscar_por_id_origem(
    colecao: Collection, fonte: str, id_origem: str
) -> dict[str, Any] | None:
    """Busca interna pela chave natural exata, sem serializar o documento BSON."""
    for nome, valor in (("fonte", fonte), ("id_origem", id_origem)):
        if not isinstance(valor, str) or not valor.strip():
            raise ErroConsultaInvalida(f"{nome} deve ser texto não vazio.")
    return _buscar_analise(colecao, {"fonte": fonte, "id_origem": id_origem})


def buscar_por_id(
    colecao: Collection, id_documento: str | ObjectId
) -> dict[str, Any] | None:
    """Busca interna por ObjectId ou seu hexadecimal; ID inválido retorna None."""
    if not isinstance(id_documento, (str, ObjectId)):
        return None
    try:
        identificador = ObjectId(id_documento)
    except (InvalidId, TypeError):
        return None
    return _buscar_analise(colecao, {"_id": identificador})


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
    
    data_processamento = documento["data_processamento"]

    if not isinstance(data_processamento, datetime) or data_processamento.tzinfo is None:
        raise ErroAnaliseInvalida(
            "data_processamento deve ser uma data com fuso horário (UTC)"
        )

    if "data_publicacao" in documento:
        data_publicacao = documento["data_publicacao"]

        if (
            not isinstance(data_publicacao, datetime)
            or data_publicacao.tzinfo is None
        ):
            raise ErroAnaliseInvalida(
                "data_publicacao deve ser uma data com fuso horário (UTC)"
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
    
def _filtrar_analises_memoria(
    analises: list[dict[str, Any]],
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
) -> list[dict[str, Any]]:
    resultado = []

    data_inicio = datetime.combine(inicio, time.min, UTC) if inicio else None
    data_fim = datetime.combine(fim, time.max, UTC) if fim else None

    for analise in analises:
        if sentimento is not None and analise.get("sentimento") != sentimento:
            continue

        data = analise.get("data_publicacao")

        if data_inicio is not None:
            if data is None or data < data_inicio:
                continue

        if data_fim is not None:
            if data is None or data > data_fim:
                continue

        resultado.append(analise)

    return resultado


def listar_analises_memoria(
    analises: list[dict[str, Any]],
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
    pagina: int = 1,
    tamanho: int = 20,
) -> dict[str, Any]:
    filtradas = _filtrar_analises_memoria(
        analises,
        inicio=inicio,
        fim=fim,
        sentimento=sentimento,
    )

    filtradas.sort(key=lambda item: (item["fonte"], item["id_origem"]))
    filtradas.sort(key=lambda item: item["data_processamento"], reverse=True)

    total = len(filtradas)
    inicio_pagina = (pagina - 1) * tamanho

    return {
        "itens": filtradas[inicio_pagina:inicio_pagina + tamanho],
        "pagina": pagina,
        "tamanho": tamanho,
        "total": total,
    }


def resumir_analises_memoria(
    analises: list[dict[str, Any]],
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
) -> dict[str, Any]:
    filtradas = _filtrar_analises_memoria(
        analises,
        inicio=inicio,
        fim=fim,
        sentimento=sentimento,
    )

    contagens = {
        "positivo": 0,
        "negativo": 0,
        "neutro": 0,
    }

    for analise in filtradas:
        contagens[analise["sentimento"]] += 1

    sem_data = 0

    if inicio is not None or fim is not None:
        sem_data = sum(
            1
            for analise in analises
            if analise.get("data_publicacao") is None
            and (
                sentimento is None
                or analise.get("sentimento") == sentimento
            )
        )

    return {
        "total": sum(contagens.values()),
        "por_sentimento": contagens,
        "sem_data_publicacao": sem_data,
    }

