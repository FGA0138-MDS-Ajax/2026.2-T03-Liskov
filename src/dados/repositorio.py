from datetime import UTC, date, datetime, time, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING, IndexModel
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
    """Parâmetro ou chave de consulta inválida."""


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


def _texto_consulta(valor: Any, nome: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ErroConsultaInvalida(f"{nome} deve ser texto não vazio.")
    return valor


def _intervalo_consulta(inicio: datetime | None, fim: datetime | None, nome: str):
    intervalo: dict[str, datetime] = {}
    for valor, chave, sufixo in ((inicio, "$gte", "inicio"), (fim, "$lt", "fim")):
        if valor is not None:
            if not isinstance(valor, datetime) or valor.tzinfo is None:
                raise ErroConsultaInvalida(
                    f"{nome}_{sufixo} deve ser datetime com fuso horário."
                )
            intervalo[chave] = valor.astimezone(timezone.utc)
    if len(intervalo) == 2 and intervalo["$gte"] >= intervalo["$lt"]:
        raise ErroConsultaInvalida(f"{nome}_inicio deve ser anterior a {nome}_fim.")
    return intervalo


def montar_filtro(
    *, sentimento: str | None = None, fonte: str | None = None,
    modelo: str | None = None, data_publicacao_inicio: datetime | None = None,
    data_publicacao_fim: datetime | None = None,
    data_processamento_inicio: datetime | None = None,
    data_processamento_fim: datetime | None = None,
    sem_data_publicacao: bool = False,
) -> dict[str, Any]:
    """Monta filtros auxiliares para consultas internas à coleção canônica."""
    filtro: dict[str, Any] = {}
    if sentimento is not None:
        if sentimento not in SENTIMENTOS_VALIDOS:
            raise ErroConsultaInvalida("sentimento deve ser positivo, negativo ou neutro.")
        filtro["sentimento"] = sentimento
    if fonte is not None:
        filtro["fonte"] = _texto_consulta(fonte, "fonte")
    if modelo is not None:
        filtro["modelo.nome"] = _texto_consulta(modelo, "modelo")
    publicacao = _intervalo_consulta(data_publicacao_inicio, data_publicacao_fim, "data_publicacao")
    if sem_data_publicacao:
        if publicacao:
            raise ErroConsultaInvalida(
                "sem_data_publicacao não combina com filtro por período de publicação."
            )
        filtro["data_publicacao"] = {"$exists": False}
    elif publicacao:
        filtro["data_publicacao"] = publicacao
    processamento = _intervalo_consulta(
        data_processamento_inicio, data_processamento_fim, "data_processamento"
    )
    if processamento:
        filtro["data_processamento"] = processamento
    return filtro


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


class RepositorioAnalises:
    """Fachada canônica das operações MongoDB sobre a coleção ``analises``."""

    def __init__(self, colecao: Collection) -> None:
        self.colecao = colecao

    def salvar_analises(self, documentos: list[dict[str, Any]]) -> dict[str, int]:
        return salvar_analises(self.colecao, documentos)

    def listar_analises(self, **filtros: Any) -> dict[str, Any]:
        return listar_analises(self.colecao, **filtros)

    def resumir_analises(self, **filtros: Any) -> dict[str, Any]:
        return resumir_analises(self.colecao, **filtros)

    def listar_com_filtro(
        self, filtro: dict[str, Any] | None = None, *, limite: int = 50, pular: int = 0
    ) -> list[dict[str, Any]]:
        if type(limite) is not int or not 1 <= limite <= 500:
            raise ErroConsultaInvalida("limite deve ser inteiro entre 1 e 500.")
        if type(pular) is not int or pular < 0:
            raise ErroConsultaInvalida("pular deve ser inteiro maior ou igual a zero.")
        try:
            return list(
                self.colecao.find(filtro or {})
                .sort([("data_processamento", DESCENDING), ("_id", DESCENDING)])
                .skip(pular)
                .limit(limite)
            )
        except PyMongoError:
            raise ErroLeituraAnalises(
                "Falha ao consultar o MongoDB; verifique a conexão."
            ) from None

    def contar_analises(self, filtro: dict[str, Any] | None = None) -> int:
        try:
            return self.colecao.count_documents(filtro or {})
        except PyMongoError:
            raise ErroLeituraAnalises(
                "Falha ao consultar o MongoDB; verifique a conexão."
            ) from None

    def contar_por_sentimento(self, filtro: dict[str, Any] | None = None) -> dict[str, int]:
        pipeline = [
            {"$match": filtro or {}},
            {"$group": {"_id": "$sentimento", "total": {"$sum": 1}}},
        ]
        try:
            linhas = list(self.colecao.aggregate(pipeline))
        except PyMongoError:
            raise ErroLeituraAnalises(
                "Falha ao consultar o MongoDB; verifique a conexão."
            ) from None
        contagem = {classe: 0 for classe in ("positivo", "negativo", "neutro")}
        for linha in linhas:
            if linha["_id"] in contagem:
                contagem[linha["_id"]] = linha["total"]
        return contagem


def contar_analises(colecao: Collection, filtro: dict[str, Any] | None = None) -> int:
    return RepositorioAnalises(colecao).contar_analises(filtro)


def contar_por_sentimento(
    colecao: Collection, filtro: dict[str, Any] | None = None
) -> dict[str, int]:
    return RepositorioAnalises(colecao).contar_por_sentimento(filtro)


def serializar_analise(documento: dict[str, Any]) -> dict[str, Any]:
    """Converte BSON para JSON: ObjectId em string e datas em ISO UTC."""
    def converter(valor: Any) -> Any:
        if isinstance(valor, ObjectId):
            return str(valor)
        if isinstance(valor, datetime):
            if valor.tzinfo is None:
                valor = valor.replace(tzinfo=timezone.utc)
            return valor.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if isinstance(valor, dict):
            return {chave: converter(item) for chave, item in valor.items()}
        if isinstance(valor, list):
            return [converter(item) for item in valor]
        return valor
    return converter(documento)


def persistir_analises(documentos: list[dict[str, Any]]) -> dict[str, int]:
    """Persiste lote administrativo usando conexão própria, inclusive em background."""
    from src.dados.database import connect_to_mongodb, disconnect_from_mongodb

    cliente = connect_to_mongodb()
    try:
        colecao = obter_colecao(cliente)
        criar_indices(colecao)
        return RepositorioAnalises(colecao).salvar_analises(documentos)
    finally:
        disconnect_from_mongodb(cliente)

