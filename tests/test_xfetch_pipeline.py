"""Integração XFetch → classificador → BSON com HTTP e analisador sintéticos."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from bson import BSON

from src.processamento.aquisicao import xfetch
from src.processamento.classificacao.bertweet import ClassificadorBertweet
from src.processamento.pipeline import PipelineClassificacao


def resposta(dados, proximo_token=None):
    http = Mock()
    http.raise_for_status.return_value = None
    http.json.return_value = {
        "data": dados,
        "meta": {"pagination": {"next_token": proximo_token}},
    }
    return http


@pytest.mark.parametrize("tamanho_lote", [1, 2])
def test_aquisicao_paginada_preserva_contrato_ate_bson(monkeypatch, tamanho_lote):
    textos = [
        "  @exemplo Não gostei!!! 😠 https://example.invalid  ",
        "Adorei a experiência! 😊",
    ]
    primeiro = {
        "id": 101,
        "text": textos[0],
        "created_at": "2026-11-09T07:00:00-03:00",
        "author_id": "autor-sintetico",
        "lang": "pt",
        "like_count": 3,
    }
    segundo = {"id": "102", "text": textos[1]}
    get = Mock(side_effect=[
        resposta([primeiro], "pagina-2"),
        resposta([primeiro, segundo]),
    ])
    monkeypatch.setattr(xfetch.requests, "get", get)
    registros = xfetch.buscar_tweets_xfetch(
        "consulta sintética lang:pt", quantidade=2, api_key="chave-ficticia"
    )
    assert get.call_count == 2
    assert [c.kwargs["params"]["limit"] for c in get.call_args_list] == [2, 2]
    assert get.call_args_list[1].kwargs["params"]["next_token"] == "pagina-2"
    assert [r["id_origem"] for r in registros] == ["101", "102"]

    analisador = Mock()
    analisador.predict.side_effect = lambda lote: [
        SimpleNamespace(
            output="NEG" if texto == textos[0] else "POS",
            probas={"POS": 0.1, "NEU": 0.1, "NEG": 0.8}
            if texto == textos[0] else {"POS": 0.8, "NEU": 0.1, "NEG": 0.1},
        )
        for texto in lote
    ]
    classificador = ClassificadorBertweet(analisador=analisador)
    documentos = PipelineClassificacao(
        classificador=classificador,
        tamanho_lote=tamanho_lote,
        versao_modelo="SIMULADO-TESTE",
    ).processar_registros(registros)

    recebidos = [texto for chamada in analisador.predict.call_args_list
                 for texto in chamada.args[0]]
    assert recebidos == textos
    assert [d["texto_original"] for d in documentos] == textos
    assert [d["id_origem"] for d in documentos] == ["101", "102"]
    assert [d["sentimento"] for d in documentos] == ["negativo", "positivo"]
    assert documentos[0]["data_publicacao"] == datetime(
        2026, 11, 9, 10, tzinfo=timezone.utc
    )
    assert "data_publicacao" not in documentos[1]
    assert documentos[0]["metadados"] == {
        "provedor": "XFetch", "lang": "pt", "like_count": 3,
    }
    assert documentos[1]["metadados"] == {"provedor": "XFetch"}
    for documento in documentos:
        assert documento["fonte"] == "X"
        assert documento["modelo"]["versao"] == "SIMULADO-TESTE"
        assert documento["data_processamento"].utcoffset().total_seconds() == 0
        assert "rotulo_original" not in documento
        assert "rotulo_padronizado" not in documento
        assert sum(documento["probabilidades"].values()) == pytest.approx(1)
        assert BSON.encode(documento)


def test_falha_na_segunda_pagina_nao_retorna_resultado_parcial(monkeypatch):
    falha = Mock(status_code=429)
    falha.raise_for_status.side_effect = requests.HTTPError(
        "detalhe privado sintético", response=falha
    )
    get = Mock(side_effect=[
        resposta([{"id": "101", "text": "Texto sintético"}], "pagina-2"),
        falha,
    ])
    monkeypatch.setattr(xfetch.requests, "get", get)

    with pytest.raises(xfetch.ErroXFetch, match="HTTP 429") as erro:
        xfetch.buscar_tweets_xfetch(
            "consulta sintética", quantidade=2, api_key="chave-ficticia"
        )

    assert get.call_count == 2
    assert "privado" not in str(erro.value)
    assert erro.value.__suppress_context__
