from fastapi.testclient import TestClient

from src.processamento.pipeline import ErroInferencia
from src.servico.main import app
from src.servico.dependencias import obter_colecao_analises, obter_pipeline

client = TestClient(app)


def test_health():
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_falha_de_inferencia_retorna_servico_indisponivel(monkeypatch):
    class PipelineComFalha:
        def processar_registros(self, registros):
            raise ErroInferencia("falha operacional")

    monkeypatch.setitem(
        app.dependency_overrides,
        obter_pipeline,
        lambda: PipelineComFalha(),
    )
    monkeypatch.setitem(
        app.dependency_overrides,
        obter_colecao_analises,
        lambda: object(),
    )

    resposta = client.post(
        "/analises",
        json={
            "registros": [
                {
                    "id_origem": "1",
                    "fonte": "teste",
                    "texto_original": "Texto de teste",
                }
            ]
        },
    )

    assert resposta.status_code == 503
    assert resposta.json() == {
        "detail": "Serviço de classificação indisponível."
    }
