from fastapi.testclient import TestClient
from src.servico.main import app

client = TestClient(app)


def test_health():
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
