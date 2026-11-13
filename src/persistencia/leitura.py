from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from src.dados.repositorio import SENTIMENTOS_VALIDOS

LIMITE_PADRAO = 50
LIMITE_MAXIMO = 500


class ErroConsultaInvalida(ValueError):
    """Parâmetro de consulta inválido (erro de uso, não de banco)."""


class ErroLeituraAnalises(RuntimeError):
    """Falha ao consultar o MongoDB, com mensagem segura (sem URI/credenciais)."""


def _executar(operacao):
    try:
        return operacao()
    except PyMongoError:
        raise ErroLeituraAnalises(
            "Falha ao consultar o MongoDB; verifique a conexão."
        ) from None


def _texto(valor: Any, nome: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ErroConsultaInvalida(f"{nome} deve ser texto não vazio.")
    return valor


def _data_utc(valor: Any, nome: str) -> datetime:
    if not isinstance(valor, datetime) or valor.tzinfo is None:
        raise ErroConsultaInvalida(f"{nome} deve ser datetime com fuso horário.")
    return valor.astimezone(timezone.utc)


def _intervalo(inicio, fim, nome: str) -> dict[str, datetime]:
    """Intervalo [inicio, fim): início inclusivo, fim exclusivo."""
    intervalo: dict[str, datetime] = {}
    if inicio is not None:
        intervalo["$gte"] = _data_utc(inicio, f"{nome}_inicio")
    if fim is not None:
        intervalo["$lt"] = _data_utc(fim, f"{nome}_fim")
    if len(intervalo) == 2 and intervalo["$gte"] >= intervalo["$lt"]:
        raise ErroConsultaInvalida(f"{nome}_inicio deve ser anterior a {nome}_fim.")
    return intervalo


def montar_filtro(
    *,
    sentimento: str | None = None,
    fonte: str | None = None,
    modelo: str | None = None,
    data_publicacao_inicio: datetime | None = None,
    data_publicacao_fim: datetime | None = None,
    data_processamento_inicio: datetime | None = None,
    data_processamento_fim: datetime | None = None,
    sem_data_publicacao: bool = False,
) -> dict[str, Any]:
    """Monta o filtro das consultas.

    Documentos sem ``data_publicacao`` não aparecem em filtro por período de
    publicação; use ``sem_data_publicacao=True`` para contá-los/listá-los.
    """
    filtro: dict[str, Any] = {}

    if sentimento is not None:
        if sentimento not in SENTIMENTOS_VALIDOS:
            raise ErroConsultaInvalida(
                "sentimento deve ser positivo, negativo ou neutro."
            )
        filtro["sentimento"] = sentimento
    if fonte is not None:
        filtro["fonte"] = _texto(fonte, "fonte")
    if modelo is not None:
        filtro["modelo.nome"] = _texto(modelo, "modelo")

    pub = _intervalo(data_publicacao_inicio, data_publicacao_fim, "data_publicacao")
    if sem_data_publicacao:
        if pub:
            raise ErroConsultaInvalida(
                "sem_data_publicacao não combina com filtro por período de publicação."
            )
        filtro["data_publicacao"] = {"$exists": False}
    elif pub:
        filtro["data_publicacao"] = pub

    proc = _intervalo(
        data_processamento_inicio, data_processamento_fim, "data_processamento"
    )
    if proc:
        filtro["data_processamento"] = proc

    return filtro


def buscar_por_id_origem(
    colecao: Collection, fonte: str, id_origem: str
) -> dict[str, Any] | None:
    """Busca pela chave natural (fonte + id_origem), coberta pelo índice único."""
    _texto(fonte, "fonte")
    _texto(id_origem, "id_origem")
    return _executar(
        lambda: colecao.find_one({"fonte": fonte, "id_origem": id_origem})
    )


def buscar_por_id(colecao: Collection, id_documento: str) -> dict[str, Any] | None:
    """Busca pelo _id (string hexadecimal). Id malformado devolve None."""
    try:
        oid = ObjectId(id_documento)
    except (InvalidId, TypeError):
        return None
    return _executar(lambda: colecao.find_one({"_id": oid}))


def listar_analises(
    colecao: Collection,
    filtro: dict[str, Any] | None = None,
    *,
    limite: int = LIMITE_PADRAO,
    pular: int = 0,
) -> list[dict[str, Any]]:
    """Lista com paginação, da mais recente para a mais antiga (processamento)."""
    if type(limite) is not int or not 1 <= limite <= LIMITE_MAXIMO:
        raise ErroConsultaInvalida(f"limite deve ser inteiro entre 1 e {LIMITE_MAXIMO}.")
    if type(pular) is not int or pular < 0:
        raise ErroConsultaInvalida("pular deve ser inteiro maior ou igual a zero.")

    def consultar():
        cursor = (
            colecao.find(filtro or {})
            .sort([("data_processamento", DESCENDING), ("_id", DESCENDING)])
            .skip(pular)
            .limit(limite)
        )
        return list(cursor)

    return _executar(consultar)


def contar_analises(colecao: Collection, filtro: dict[str, Any] | None = None) -> int:
    return _executar(lambda: colecao.count_documents(filtro or {}))


def contar_por_sentimento(
    colecao: Collection, filtro: dict[str, Any] | None = None
) -> dict[str, int]:
    """Distribuição para o gráfico do dashboard; sempre devolve as 3 classes."""
    pipeline = [
        {"$match": filtro or {}},
        {"$group": {"_id": "$sentimento", "total": {"$sum": 1}}},
    ]
    linhas = _executar(lambda: list(colecao.aggregate(pipeline)))
    contagem = {sentimento: 0 for sentimento in ("positivo", "negativo", "neutro")}
    for linha in linhas:
        if linha["_id"] in contagem:
            contagem[linha["_id"]] = linha["total"]
    return contagem


def _serializar_valor(valor: Any) -> Any:
    if isinstance(valor, ObjectId):
        return str(valor)
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(valor, dict):
        return {chave: _serializar_valor(item) for chave, item in valor.items()}
    if isinstance(valor, list):
        return [_serializar_valor(item) for item in valor]
    return valor


def serializar_analise(documento: dict[str, Any]) -> dict[str, Any]:
    """Converte para JSON: _id vira string e datas viram ISO 8601 com 'Z'."""
    return _serializar_valor(documento)
