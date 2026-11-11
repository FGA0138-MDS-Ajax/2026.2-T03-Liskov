import pytest
from pymongo.errors import ConnectionFailure
from unittest.mock import Mock

from fastapi.testclient import TestClient

from src.processamento.pipeline import PipelineClassificacao
from src.servico.dependencias import obter_colecao_analises, obter_pipeline
from src.servico.main import app


def test_api_classifica_lote_e_encaminha_documentos_ao_banco(monkeypatch):
    # Modelo simulado: permite verificar os textos recebidos mas sem baixar pesos
    classificador = Mock()
    classificador.nome_modelo = "modelo-simulado-de-teste"
    classificador.prever_com_probabilidades.return_value = [
        {
            "sentimento": "NEG",
            "probabilidades": {
                "positivo": 0.05,
                "negativo": 0.90,
                "neutro": 0.05,
            },
        },
        {
            "sentimento": "POS",
            "probabilidades": {
                "positivo": 0.90,
                "negativo": 0.05,
                "neutro": 0.05,
            },
        },
    ]
    pipeline = PipelineClassificacao(classificador=classificador)

    # Vai simular somente a coleção do Mongodb
    colecao = Mock()
    colecao.insert_many.return_value.inserted_ids = ["mongo-1", "mongo-2"]

    monkeypatch.setitem(
        app.dependency_overrides, obter_pipeline, lambda: pipeline
    )
    monkeypatch.setitem(
        app.dependency_overrides, obter_colecao_analises, lambda: colecao
    )

    registros = [
        {
            "id_origem": "1",
            "fonte": "teste",
            "texto_original": "Não gostei 😞 @loja https://exemplo.com",
            "rotulo_original": "positivo",
            "rotulo_padronizado": "POS",
            "metadados": {"categoria": "atendimento"},
        },
        {
            "id_origem": "2",
            "fonte": "teste",
            "texto_original": "Adorei o atendimento!",
        },
    ]

    with TestClient(app) as client:
        resposta = client.post("/analises", json={"registros": registros})

    assert resposta.status_code == 201, resposta.text
    assert resposta.json() == {
        "recebidos": 2,
        "inseridos": 2,
        "duplicados": 0,
    }

    # Pra garantir que o texto foi preservado até a entrada do classificador
    classificador.prever_com_probabilidades.assert_called_once_with(
        [registro["texto_original"] for registro in registros]
    )

    # Vai inspecionar os documentos que a persistência enviou ao MongoDB simulado
    colecao.insert_many.assert_called_once()
    documentos = colecao.insert_many.call_args.args[0]

    assert len(documentos) == 2
    assert [doc["id_origem"] for doc in documentos] == ["1", "2"]
    assert [doc["sentimento"] for doc in documentos] == ["negativo", "positivo"]

    for registro, documento in zip(registros, documentos):
        assert documento["texto_original"] == registro["texto_original"]
        assert documento["fonte"] == registro["fonte"]
        assert documento["modelo"]["nome"] == "modelo-simulado-de-teste"
        assert documento["data_processamento"].utcoffset().total_seconds() == 0
        assert set(documento["probabilidades"]) == {
            "positivo", "negativo", "neutro"
        }

    # O rótulo humano não deve ser sobrescrito pela previsão do modelo.
    assert documentos[0]["rotulo_original"] == "positivo"
    assert documentos[0]["rotulo_padronizado"] == "positivo"
    assert documentos[0]["sentimento"] == "negativo"
    assert documentos[0]["metadados"] == {"categoria": "atendimento"}

    # O segundo registro não tinha rótulos humanos nem data de publicação.
    assert "rotulo_original" not in documentos[1]
    assert "rotulo_padronizado" not in documentos[1]
    assert "data_publicacao" not in documentos[1]

    # O parametrize executa o mesmo teste para 7 entradas inválidas diferentes. O último teste provoca uma falha
    # # no classificador e verifica o tratamento pelo pipeline real e pela APi, (ja inclui tbm a proteção dos detalhes internos)
@pytest.mark.parametrize(
    "registros",
    [
        [],
        [{"id_origem": "1", "fonte": "teste"}],
        [{"id_origem": "1", "fonte": "teste", "texto_original": ""}],
        [{"id_origem": "1", "fonte": "teste", "texto_original": "   "}],
        [{"id_origem": "1", "fonte": "teste", "texto_original": 123}],
        [{"fonte": "teste", "texto_original": "Texto válido"}],
        [{"id_origem": "1", "texto_original": "Texto válido"}],
    ],
    ids=[
        "lote-vazio",
        "texto-ausente",
        "texto-vazio",
        "texto-so-espacos",
        "texto-numerico",
        "id-ausente",
        "fonte-ausente",
    ],
)
def test_entrada_invalida_nao_processa_nem_grava(monkeypatch, registros):
    pipeline = Mock()
    colecao = Mock()

    monkeypatch.setitem(
        app.dependency_overrides, obter_pipeline, lambda: pipeline
    )
    monkeypatch.setitem(
        app.dependency_overrides, obter_colecao_analises, lambda: colecao
    )

    with TestClient(app) as client:
        resposta = client.post("/analises", json={"registros": registros})

    assert resposta.status_code == 422, resposta.text
    pipeline.processar_registros.assert_not_called()
    assert colecao.mock_calls == []


def test_falha_do_modelo_retorna_503_sem_gravar(monkeypatch):
    classificador = Mock()
    classificador.nome_modelo = "modelo-simulado-de-teste"
    classificador.prever_com_probabilidades.side_effect = RuntimeError(
        "DETALHE_INTERNO_DO_MODELO"
    )
    pipeline = PipelineClassificacao(classificador=classificador)
    colecao = Mock()

    monkeypatch.setitem(
        app.dependency_overrides, obter_pipeline, lambda: pipeline
    )
    monkeypatch.setitem(
        app.dependency_overrides, obter_colecao_analises, lambda: colecao
    )

    with TestClient(app) as client:
        resposta = client.post(
            "/analises",
            json={
                "registros": [
                    {
                        "id_origem": "1",
                        "fonte": "teste",
                        "texto_original": "Texto válido",
                    }
                ]
            },
        )

    assert resposta.status_code == 503, resposta.text
    assert resposta.json() == {
        "detail": "Serviço de classificação indisponível."
    }
    assert "DETALHE_INTERNO_DO_MODELO" not in resposta.text
    classificador.prever_com_probabilidades.assert_called_once_with(
        ["Texto válido"]
    )
    assert colecao.mock_calls == []
def test_falha_na_gravacao_retorna_503(monkeypatch):
    classificador = Mock()
    classificador.nome_modelo = "modelo-simulado-de-teste"
    classificador.prever_com_probabilidades.return_value = [
        {
            "sentimento": "POS",
            "probabilidades": {
                "positivo": 0.90,
                "negativo": 0.05,
                "neutro": 0.05,
            },
        }
    ]
    pipeline = PipelineClassificacao(classificador=classificador)

    colecao = Mock()
    colecao.insert_many.side_effect = ConnectionFailure(
        "DETALHE_INTERNO_DO_BANCO"
    )

    monkeypatch.setitem(
        app.dependency_overrides, obter_pipeline, lambda: pipeline
    )
    monkeypatch.setitem(
        app.dependency_overrides, obter_colecao_analises, lambda: colecao
    )

    with TestClient(app) as client:
        resposta = client.post(
            "/analises",
            json={
                "registros": [
                    {
                        "id_origem": "1",
                        "fonte": "teste",
                        "texto_original": "Gostei do atendimento!",
                    }
                ]
            },
        )

    assert resposta.status_code == 503, resposta.text
    assert resposta.json() == {
        "detail": "Banco de dados indisponível."
    }
    assert "DETALHE_INTERNO_DO_BANCO" not in resposta.text
    colecao.insert_many.assert_called_once()