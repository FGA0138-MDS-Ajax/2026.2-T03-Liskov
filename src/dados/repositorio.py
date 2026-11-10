from datetime import datetime
from typing import Any

from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
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
                raise ErroAnaliseInvalida(f"{campo} deve ser uma data com fuso horário (UTC)")


def salvar_analise(colecao: Collection, documento: dict[str, Any]):

    validar_analise(documento)
    try:
        colecao.insert_one(dict(documento))
    except DuplicateKeyError:
        return False
    return True
    
