import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

def connect_to_mongodb():
    """Tenta conectar ao MongoDB e retorna o cliente ativo."""
    try:
        client.admin.command('ping')
        print("Sucesso: Conexão com o MongoDB estabelecida com sucesso!")
        return client
    except ConnectionFailure as e:
        print(f"Erro: Falha ao conectar ao MongoDB: {e}")
        raise e
    except Exception as e:
        print(f"Erro inesperado: {e}")
        raise e

def disconnect_from_mongodb():
    """Fecha a conexão com o MongoDB."""
    client.close()
    print("Conexão com o MongoDB encerrada.")