"""Executar após integração experimental de A + PR64 corrigido + PR65 corrigido.

uv run pytest docs/qa/pc1/evidencias/test_integracao_prs.py -v -ra
Não é coletado pela suíte da base (testpaths=tests), pois depende do PR #65.
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from bson import BSON

from src.processamento.aquisicao import adquirir_dados
from src.processamento.aquisicao.xfetch import buscar_tweets_xfetch
from src.processamento.classificacao.bertweet import ClassificadorBertweet
from src.processamento.pipeline import PipelineClassificacao


class Analisador:
    def __init__(self):
        self.recebidos = []

    def predict(self, textos):
        self.recebidos.extend(textos)
        return [SimpleNamespace(output="NEG", probas={"POS": .1, "NEG": .8, "NEU": .1}) for _ in textos]


def verificar_documentos(registros):
    analisador = Analisador()
    pipeline = PipelineClassificacao(classificador=ClassificadorBertweet(analisador=analisador))
    documentos = pipeline.processar_registros(registros)
    assert analisador.recebidos == [r["texto_original"] for r in registros]
    assert len(documentos) == len(registros)
    for entrada, doc in zip(registros, documentos, strict=True):
        for campo in ("id_origem", "fonte", "texto_original"):
            assert doc[campo] == entrada[campo]
        assert doc["sentimento"] == "negativo"
        assert set(doc["probabilidades"]) == {"positivo", "negativo", "neutro"}
        assert sum(doc["probabilidades"].values()) == 1
        assert doc["data_processamento"].utcoffset().total_seconds() == 0
        assert "author_id" not in doc.get("metadados", {})
        BSON.encode(doc)
    return documentos


def test_xfetch_pipeline_bson_offline(monkeypatch):
    texto = "  Não gostei! @exemplo 😊 https://example.invalid  "
    resposta = Mock()
    resposta.json.return_value = {"data": [
        {"id": "synthetic-1", "text": texto, "author_id": "autor-ficticio",
         "created_at": "2026-11-09T07:00:00-03:00", "like_count": 2},
        {"id": "synthetic-1", "text": texto},
        {"id": "synthetic-2", "text": "Sem data"},
    ]}
    get = Mock(return_value=resposta)
    monkeypatch.setattr("src.processamento.aquisicao.xfetch.requests.get", get)
    registros = buscar_tweets_xfetch("consulta sintética", quantidade=3, api_key="fake")
    assert len(registros) == 2 and get.call_count == 1
    assert all("sentimento" not in r for r in registros)
    documentos = verificar_documentos(registros)
    assert documentos[0]["texto_original"] == texto
    assert documentos[0]["data_publicacao"] == datetime(2026, 11, 9, 10, tzinfo=timezone.utc)
    assert "data_publicacao" not in documentos[1]
    assert "rotulo_original" not in documentos[0]


def test_csv_e_tweetsentbr_pipeline_bson(tmp_path):
    csv = tmp_path / "sentia.csv"
    csv.write_text("id,texto,rotulo,fonte,data\nsyn-1,Texto sintético,POS,sintetica,2026-11-09\n", encoding="utf-8")
    docs = verificar_documentos(adquirir_dados(csv))
    assert docs[0]["rotulo_original"] == "POS"
    assert docs[0]["rotulo_padronizado"] == "positivo"
    tweets = tmp_path / "tweets.csv"
    tweets.write_text("id,texto,rotulo\nsyn-2,Outro texto sintético,neutro\n", encoding="utf-8")
    docs = verificar_documentos(adquirir_dados(tweets))
    assert docs[0]["rotulo_padronizado"] == "neutro"
