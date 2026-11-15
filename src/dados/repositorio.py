from collections.abc import Iterable
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
LIMITE_MAXIMO_PAGINA = 100


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


def salvar_analises(colecao: Collection, documentos: Iterable[dict[str, Any]]):

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


def _validar_data_filtro(valor: Any, campo: str) -> date | None:
    if valor is None:
        return None
    if not isinstance(valor, date) or isinstance(valor, datetime):
        raise ErroConsultaInvalida(f"{campo} deve ser uma data válida.")
    return valor


def _filtro_consulta(
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
) -> dict[str, Any]:
    inicio_validado = _validar_data_filtro(inicio, "inicio")
    fim_validado = _validar_data_filtro(fim, "fim")
    if (
        inicio_validado is not None
        and fim_validado is not None
        and inicio_validado > fim_validado
    ):
        raise ErroConsultaInvalida("inicio não pode ser maior que fim.")
    if sentimento is not None and sentimento not in SENTIMENTOS_VALIDOS:
        raise ErroConsultaInvalida(
            "sentimento deve ser positivo, negativo ou neutro."
        )

    filtro: dict[str, Any] = {}
    if sentimento is not None:
        filtro["sentimento"] = sentimento
    periodo: dict[str, datetime] = {}
    if inicio_validado is not None:
        periodo["$gte"] = datetime.combine(inicio_validado, time.min, UTC)
    if fim_validado is not None:
        periodo["$lte"] = datetime.combine(fim_validado, time.max, UTC)
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
    if type(pagina) is not int or pagina < 1:
        raise ErroConsultaInvalida("pagina deve ser um inteiro maior ou igual a 1.")
    if type(tamanho) is not int or not (1 <= tamanho <= LIMITE_MAXIMO_PAGINA):
        raise ErroConsultaInvalida(
            f"tamanho deve ser um inteiro entre 1 e {LIMITE_MAXIMO_PAGINA}."
        )

    filtro = _filtro_consulta(inicio, fim, sentimento)
    try:
        total = colecao.count_documents(filtro)
        # A chave única (fonte, id_origem) desempata datas iguais de forma estável.
        cursor = (
            colecao.find(filtro, {"_id": 0})
            .sort([("data_processamento", -1), ("fonte", 1), ("id_origem", 1)])
            .skip((pagina - 1) * tamanho)
            .limit(tamanho)
        )
        itens = list(cursor)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None
    return {"itens": itens, "pagina": pagina, "tamanho": tamanho, "total": total}


def resumir_analises(
    colecao: Collection,
    *,
    inicio: date | None = None,
    fim: date | None = None,
    sentimento: str | None = None,
) -> dict[str, Any]:
    filtro = _filtro_consulta(inicio, fim, sentimento)
    contagens = {classe: 0 for classe in ("positivo", "negativo", "neutro")}
    try:
        for grupo in colecao.aggregate([
            {"$match": filtro},
            {"$group": {"_id": "$sentimento", "total": {"$sum": 1}}},
        ]):
            if grupo.get("_id") in contagens:
                contagens[grupo["_id"]] = grupo["total"]
        sem_data = 0
        if inicio is not None or fim is not None:
            filtro_sem_data: dict[str, Any] = {"data_publicacao": None}
            if sentimento is not None:
                filtro_sem_data["sentimento"] = sentimento
            sem_data = colecao.count_documents(filtro_sem_data)
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None
    return {
        "total": sum(contagens.values()),
        "por_sentimento": contagens,
        "sem_data_publicacao": sem_data,
    }


def listar_registros_base(colecao: Collection) -> list[dict[str, Any]]:
    """Recupera registros base da coleção analises para deduplicação de coleta."""
    projecao = {
        "_id": 0,
        "id_origem": 1,
        "fonte": 1,
        "texto_original": 1,
        "data_publicacao": 1,
        "rotulo_original": 1,
        "metadados": 1,
    }
    try:
        documentos = list(colecao.find({}, projecao))
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None

    registros: list[dict[str, Any]] = []
    for doc in documentos:
        if all(
            isinstance(doc.get(campo), str) and doc[campo].strip()
            for campo in CAMPOS_TEXTO_OBRIGATORIOS
        ):
            registro: dict[str, Any] = {
                "id_origem": doc["id_origem"],
                "fonte": doc["fonte"],
                "texto_original": doc["texto_original"],
            }
            for opcional in ("data_publicacao", "rotulo_original", "metadados"):
                if doc.get(opcional) is not None:
                    registro[opcional] = doc[opcional]
            registros.append(registro)
    return registros


class RepositorioAnalises:
    """Repositório canônico para persistência e consulta da coleção analises."""

    def __init__(self, colecao: Collection) -> None:
        self.colecao = colecao

    def criar_indices(self):
        return criar_indices(self.colecao)

    def buscar_por_id_origem(self, fonte: str, id_origem: str) -> dict[str, Any] | None:
        return buscar_por_id_origem(self.colecao, fonte, id_origem)

    def buscar_por_id(self, id_documento: str | ObjectId) -> dict[str, Any] | None:
        return buscar_por_id(self.colecao, id_documento)

    def salvar_analise(self, documento: dict[str, Any]) -> bool:
        return salvar_analise(self.colecao, documento)

    def salvar_analises(self, documentos: Iterable[dict[str, Any]]) -> dict[str, int]:
        return salvar_analises(self.colecao, list(documentos))

    def listar_analises(
        self,
        *,
        inicio: date | None = None,
        fim: date | None = None,
        sentimento: str | None = None,
        pagina: int = 1,
        tamanho: int = 20,
    ) -> dict[str, Any]:
        return listar_analises(
            self.colecao,
            inicio=inicio,
            fim=fim,
            sentimento=sentimento,
            pagina=pagina,
            tamanho=tamanho,
        )

    def resumir_analises(
        self,
        *,
        inicio: date | None = None,
        fim: date | None = None,
        sentimento: str | None = None,
    ) -> dict[str, Any]:
        return resumir_analises(
            self.colecao,
            inicio=inicio,
            fim=fim,
            sentimento=sentimento,
        )

    def listar_registros_base(self) -> list[dict[str, Any]]:
        return listar_registros_base(self.colecao)

