from src.dados.database import connect_to_mongodb, disconnect_from_mongodb

if __name__ == "__main__":
    try:
        db_client = connect_to_mongodb()
        disconnect_from_mongodb()
    except Exception as e:
        print(f"Teste falhou: {e}")