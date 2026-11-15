from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import BulkWriteError, OperationFailure

from src.dados.database import ErroConexaoMongoDB
from src.processamento.pipeline import ErroInferencia, PipelineClassificacao
from src.servico import dependencias
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


SEGREDO = "mongodb://admin:SENHA_NAO_EXPOR@servidor/sentia"
REGISTRO = {"id_origem": "1", "fonte": "teste", "texto_original": "Ótimo serviço"}


@pytest.fixture
def recursos(monkeypatch):
    classificador = Mock(nome_modelo="classificador-teste")
    classificador.prever_com_probabilidades.return_value = [{
        "sentimento": "POS",
        "probabilidades": {"positivo": 0.8, "negativo": 0.1, "neutro": 0.1},
    }]
    pipeline = PipelineClassificacao(classificador=classificador)
    colecao = Mock()
    colecao.insert_many.return_value.inserted_ids = ["id-mongo"]
    monkeypatch.setitem(app.dependency_overrides, obter_pipeline, lambda: pipeline)
    monkeypatch.setitem(app.dependency_overrides, obter_colecao_analises, lambda: colecao)
    return classificador, colecao


def test_post_analises_classifica_e_persiste(recursos):
    classificador, colecao = recursos
    resposta = client.post("/analises", json={"registros": [REGISTRO]})
    assert resposta.status_code == 201
    assert resposta.json() == {"recebidos": 1, "inseridos": 1, "duplicados": 0}
    classificador.prever_com_probabilidades.assert_called_once_with(["Ótimo serviço"])
    documentos = colecao.insert_many.call_args.args[0]
    assert documentos[0]["sentimento"] == "positivo"
    assert documentos[0]["modelo"] == {"nome": "classificador-teste"}
    assert documentos[0]["data_processamento"].tzinfo is not None
    assert "data_publicacao" not in documentos[0]
    assert colecao.insert_many.call_args.kwargs == {"ordered": False}


@pytest.mark.parametrize("registros", [[], [{}], [{**REGISTRO, "texto_original": " "}],
                                      [{**REGISTRO, "fonte": 123}],
                                      [{**REGISTRO, "campo_extra": True}]])
def test_post_analises_rejeita_entrada_pydantic_invalida(recursos, registros):
    classificador, colecao = recursos
    resposta = client.post("/analises", json={"registros": registros})
    assert resposta.status_code == 422
    classificador.prever_com_probabilidades.assert_not_called()
    colecao.insert_many.assert_not_called()


def test_post_analises_rejeita_data_invalida_sem_gravar(recursos):
    _, colecao = recursos
    resposta = client.post("/analises", json={"registros": [
        {**REGISTRO, "data_publicacao": "data-invalida"}
    ]})
    assert resposta.status_code == 400
    colecao.insert_many.assert_not_called()


def test_post_analises_conta_duplicata(recursos):
    _, colecao = recursos
    colecao.insert_many.side_effect = BulkWriteError({
        "nInserted": 0, "writeErrors": [{"code": 11000}],
    })
    resposta = client.post("/analises", json={"registros": [REGISTRO]})
    assert resposta.status_code == 201
    assert resposta.json() == {"recebidos": 1, "inseridos": 0, "duplicados": 1}


@pytest.mark.parametrize("origem", ["banco", "classificador"])
def test_post_analises_sanitiza_falhas_operacionais(recursos, origem):
    classificador, colecao = recursos
    if origem == "banco":
        colecao.insert_many.side_effect = OperationFailure(SEGREDO)
    else:
        classificador.prever_com_probabilidades.side_effect = RuntimeError(SEGREDO)
    resposta = client.post("/analises", json={"registros": [REGISTRO]})
    assert resposta.status_code == 503
    assert "SENHA_NAO_EXPOR" not in resposta.text
    assert resposta.json()["detail"] == (
        "Banco de dados indisponível." if origem == "banco"
        else "Serviço de classificação indisponível."
    )


@pytest.mark.parametrize("fase", ["conexao", "colecao", "indices", "encerramento"])
def test_dependencia_mongodb_sanitiza_falhas_e_fecha_cliente(monkeypatch, fase):
    mongo = Mock()
    conectar = Mock(return_value=mongo)
    fechar = Mock()
    colecao = Mock()
    colecao.insert_many.return_value.inserted_ids = ["id"]
    obter = Mock(return_value=colecao)
    indices = Mock()
    if fase == "conexao":
        conectar.side_effect = ErroConexaoMongoDB(SEGREDO)
    elif fase == "colecao":
        obter.side_effect = OperationFailure(SEGREDO)
    elif fase == "indices":
        indices.side_effect = OperationFailure(SEGREDO)
    else:
        fechar.side_effect = ErroConexaoMongoDB(SEGREDO)
    monkeypatch.setattr(dependencias, "connect_to_mongodb", conectar)
    monkeypatch.setattr(dependencias, "disconnect_from_mongodb", fechar)
    monkeypatch.setattr(dependencias, "obter_colecao", obter)
    monkeypatch.setattr(dependencias, "criar_indices", indices)
    pipeline = Mock()
    pipeline.processar_registros.return_value = [{
        **REGISTRO, "sentimento": "positivo", "modelo": {"nome": "teste"},
        "data_processamento": datetime.now(UTC),
    }]
    monkeypatch.setitem(app.dependency_overrides, obter_pipeline, lambda: pipeline)
    resposta = TestClient(app, raise_server_exceptions=False).post(
        "/analises", json={"registros": [REGISTRO]}
    )
    assert resposta.status_code == 503
    assert resposta.json() == {"detail": "Banco de dados indisponível."}
    if fase == "conexao":
        fechar.assert_not_called()
    else:
        fechar.assert_called_once_with(mongo)


def test_dependencia_classificador_sanitiza_falha_de_carregamento(monkeypatch):
    carregar = Mock(side_effect=RuntimeError(SEGREDO))
    monkeypatch.setattr(dependencias, "_carregar_pipeline", carregar)
    resposta = client.post("/analises", json={"registros": [REGISTRO]})
    assert resposta.status_code == 503
    assert resposta.json() == {"detail": "Classificador indisponível."}
