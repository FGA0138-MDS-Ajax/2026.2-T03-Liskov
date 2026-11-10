from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient

NOME_BANCO_PADRAO = "sentia"
NOME_COLECAO = "analises"

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
