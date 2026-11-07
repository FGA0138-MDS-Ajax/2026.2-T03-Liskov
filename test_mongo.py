import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

def test_connection():
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        client.admin.command('ping')
        print("Sucesso: Conexão com o MongoDB estabelecida com sucesso!")
        
    except ConnectionFailure as e:
        print(f"Erro: Falha ao conectar ao MongoDB: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    test_connection()