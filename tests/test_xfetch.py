
"""Testes unitários para a aquisição de tweets pelo XFetch."""

import os
from unittest.mock import Mock, patch

import pytest
import requests

from src.processamento.aquisicao import xfetch


def criar_tweet(identificador, texto="Tweet de teste"):
    """Cria um tweet no formato bruto esperado pela API."""
    return {
        "id": str(identificador),
        "text": texto,
        "created_at": "2026-11-09T10:00:00.000Z",
        "author_id": "12345",
        "lang": "pt",
        "like_count": 5,
    }


def criar_resposta(data, next_token=None):
    """Cria uma resposta simulada da API XFetch."""
    resposta = Mock()
    resposta.raise_for_status.return_value = None

    conteudo = {"data": data}

    if next_token is not None:
        conteudo["meta"] = {
            "pagination": {"next_token": next_token}
        }

    resposta.json.return_value = conteudo
    return resposta


class TestNormalizacaoXFetch:

    def test_normaliza_tweet_corretamente(self):
        tweet = criar_tweet("123", "Olá, Brasil!")

        resultado = xfetch._normalizar_tweet(tweet)

        assert resultado == {
            "id_origem": "123",
            "texto_original": "Olá, Brasil!",
            "fonte": "X",
            "rotulo_original": None,
            "rotulo_padronizado": None,
            "data_publicacao": "2026-11-09T10:00:00Z",
            "metadados": {
                "provedor": "XFetch",
                "lang": "pt",
                "like_count": 5,
            },
        }

    @pytest.mark.parametrize(
        "tweet",
        [
            {"text": "Tweet sem ID"},
            {"id": "123"},
            {"id": "123", "text": ""},
            {"id": "123", "text": "   "},
        ],
    )
    def test_ignora_tweet_invalido(self, tweet):
        assert xfetch._normalizar_tweet(tweet) is None


class TestValidacaoParametros:

    def test_rejeita_consulta_vazia(self):
        with pytest.raises(ValueError):
            xfetch.buscar_tweets_xfetch("", api_key="chave-teste")

    def test_rejeita_quantidade_acima_de_100(self):
        with pytest.raises(ValueError):
            xfetch.buscar_tweets_xfetch(
                "Brasil", quantidade=101, api_key="chave-teste"
            )

    def test_rejeita_quantidade_igual_a_zero(self):
        with pytest.raises(ValueError):
            xfetch.buscar_tweets_xfetch(
                "Brasil", quantidade=0, api_key="chave-teste"
            )

    def test_rejeita_quantidade_nao_inteira(self):
        with pytest.raises(TypeError):
            xfetch.buscar_tweets_xfetch(
                "Brasil", quantidade=2.5, api_key="chave-teste"
            )

    def test_rejeita_limite_por_pagina_acima_de_20(self):
        with pytest.raises(ValueError):
            xfetch.buscar_tweets_xfetch(
                "Brasil",
                api_key="chave-teste",
                limite_por_pagina=21,
            )

    def test_rejeita_maximo_de_paginas_igual_a_zero(self):
        with pytest.raises(ValueError):
            xfetch.buscar_tweets_xfetch(
                "Brasil",
                api_key="chave-teste",
                max_paginas=0,
            )


class TestBuscaXFetch:

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_busca_tweets_com_sucesso(self, mock_get, mock_dotenv):
        mock_get.return_value = criar_resposta([
            criar_tweet("1", "Primeiro tweet"),
            criar_tweet("2", "Segundo tweet"),
        ])

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=2,
            api_key="chave-teste",
        )

        assert len(resultado) == 2
        assert resultado[0]["id_origem"] == "1"
        assert resultado[1]["id_origem"] == "2"
        assert mock_get.call_count == 1

        argumentos = mock_get.call_args.kwargs

        assert argumentos["headers"]["Authorization"] == "Bearer chave-teste"
        assert argumentos["params"]["query"] == "Brasil"
        assert argumentos["params"]["limit"] == 2

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_paginacao_automatica_para_45_tweets(
        self, mock_get, mock_dotenv
    ):
        """Mantém o limit de 20 nas três páginas, conforme contrato XFetch."""

        primeira_pagina = [
            criar_tweet(i) for i in range(1, 21)
        ]
        segunda_pagina = [
            criar_tweet(i) for i in range(21, 41)
        ]
        terceira_pagina = [
            criar_tweet(i) for i in range(41, 46)
        ]

        mock_get.side_effect = [
            criar_resposta(
                primeira_pagina,
                next_token="token-pagina-2",
            ),
            criar_resposta(
                segunda_pagina,
                next_token="token-pagina-3",
            ),
            criar_resposta(terceira_pagina),
        ]

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=45,
            api_key="chave-teste",
        )

        assert len(resultado) == 45
        assert mock_get.call_count == 3

        limites = [
            chamada.kwargs["params"]["limit"]
            for chamada in mock_get.call_args_list
        ]

        assert limites == [20, 20, 20]

        segunda_chamada = mock_get.call_args_list[1]
        terceira_chamada = mock_get.call_args_list[2]

        assert (
            segunda_chamada.kwargs["params"]["next_token"]
            == "token-pagina-2"
        )
        assert (
            terceira_chamada.kwargs["params"]["next_token"]
            == "token-pagina-3"
        )

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_paginacao_com_limite_personalizado(
        self, mock_get, mock_dotenv
    ):
        """Deve respeitar o tamanho de página escolhido pelo usuário."""

        mock_get.side_effect = [
            criar_resposta(
                [criar_tweet("1"), criar_tweet("2")],
                next_token="pagina-2",
            ),
            criar_resposta(
                [criar_tweet("3"), criar_tweet("4")],
                next_token="pagina-3",
            ),
            criar_resposta([criar_tweet("5")]),
        ]

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=5,
            api_key="chave-teste",
            limite_por_pagina=2,
        )

        assert len(resultado) == 5
        assert mock_get.call_count == 3

        limites = [
            chamada.kwargs["params"]["limit"]
            for chamada in mock_get.call_args_list
        ]

        assert limites == [2, 2, 2]

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_para_quando_atinge_quantidade_solicitada(
        self, mock_get, mock_dotenv
    ):
        mock_get.return_value = criar_resposta(
            [
                criar_tweet("1"),
                criar_tweet("2"),
            ],
            next_token="pagina-seguinte",
        )

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=2,
            api_key="chave-teste",
        )

        assert len(resultado) == 2
        assert mock_get.call_count == 1

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_remove_tweets_duplicados(self, mock_get, mock_dotenv):
        mock_get.side_effect = [
            criar_resposta(
                [criar_tweet("1"), criar_tweet("2")],
                next_token="pagina-2",
            ),
            criar_resposta([
                criar_tweet("2"),
                criar_tweet("3"),
            ]),
        ]

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=10,
            api_key="chave-teste",
            limite_por_pagina=2,
        )

        ids = [tweet["id_origem"] for tweet in resultado]

        assert ids == ["1", "2", "3"]
        assert len(ids) == len(set(ids))
        assert mock_get.call_count == 2

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_retorna_menos_tweets_quando_api_nao_tem_mais_resultados(
        self, mock_get, mock_dotenv
    ):
        mock_get.return_value = criar_resposta([
            criar_tweet("1"),
            criar_tweet("2"),
        ])

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=50,
            api_key="chave-teste",
        )

        assert len(resultado) == 2
        assert mock_get.call_count == 1

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_retorna_lista_vazia_sem_resultados(
        self, mock_get, mock_dotenv
    ):
        mock_get.return_value = criar_resposta([])

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            api_key="chave-teste",
        )

        assert resultado == []
        assert mock_get.call_count == 1

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_respeita_limite_manual_de_paginas(
        self, mock_get, mock_dotenv
    ):
        mock_get.side_effect = [
            criar_resposta(
                [criar_tweet("1")],
                next_token="pagina-2",
            ),
            criar_resposta(
                [criar_tweet("2")],
                next_token="pagina-3",
            ),
        ]

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=10,
            api_key="chave-teste",
            max_paginas=2,
        )

        assert len(resultado) == 2
        assert mock_get.call_count == 2

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_interrompe_ao_repetir_token(
        self, mock_get, mock_dotenv
    ):
        mock_get.side_effect = [
            criar_resposta(
                [criar_tweet("1")],
                next_token="token-repetido",
            ),
            criar_resposta(
                [criar_tweet("2")],
                next_token="token-repetido",
            ),
        ]

        resultado = xfetch.buscar_tweets_xfetch(
            "Brasil",
            quantidade=10,
            api_key="chave-teste",
        )

        assert len(resultado) == 2
        assert mock_get.call_count == 2

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_trata_erro_http(self, mock_get, mock_dotenv):
        resposta = Mock()
        resposta.raise_for_status.side_effect = requests.HTTPError(
            "Erro HTTP simulado"
        )
        mock_get.return_value = resposta

        with pytest.raises(xfetch.ErroXFetch):
            xfetch.buscar_tweets_xfetch(
                "Brasil",
                api_key="chave-teste",
            )

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_trata_json_invalido(self, mock_get, mock_dotenv):
        resposta = Mock()
        resposta.raise_for_status.return_value = None
        resposta.json.side_effect = ValueError("JSON inválido")
        mock_get.return_value = resposta

        with pytest.raises(xfetch.ErroXFetch):
            xfetch.buscar_tweets_xfetch(
                "Brasil",
                api_key="chave-teste",
            )

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.requests, "get")
    def test_trata_campo_data_invalido(self, mock_get, mock_dotenv):
        mock_get.return_value = criar_resposta(
            {"tweet": "Formato incorreto"}
        )

        with pytest.raises(xfetch.ErroXFetch):
            xfetch.buscar_tweets_xfetch(
                "Brasil",
                api_key="chave-teste",
            )

    @patch.object(xfetch, "load_dotenv")
    @patch.object(xfetch.os, "getenv", return_value=None)
    def test_rejeita_ausencia_de_chave(
        self, mock_getenv, mock_dotenv
    ):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(xfetch.ErroXFetch):
                xfetch.buscar_tweets_xfetch("Brasil")


@pytest.mark.parametrize("max_paginas", [None, 1, 4, 1000])
def test_teto_absoluto_com_tokens_sempre_novos(monkeypatch, max_paginas):
    respostas = iter(criar_resposta([], next_token=f"pagina-{i}") for i in range(50))
    get = Mock(side_effect=lambda *a, **k: next(respostas))
    monkeypatch.setattr(xfetch.requests, "get", get)
    assert xfetch.buscar_tweets_xfetch("consulta sintética", api_key="fake", max_paginas=max_paginas) == []
    assert get.call_count == min(max_paginas or 10, 10)


@pytest.mark.parametrize("status", [401, 402, 403, 429, 500, 503])
def test_status_http_sem_retry_nem_vazamento(monkeypatch, status):
    resposta = Mock(status_code=status)
    resposta.raise_for_status.side_effect = requests.HTTPError("SEGREDO consulta privada", response=resposta)
    get = Mock(return_value=resposta)
    monkeypatch.setattr(xfetch.requests, "get", get)
    with pytest.raises(xfetch.ErroXFetch) as erro:
        xfetch.buscar_tweets_xfetch("consulta privada", api_key="SEGREDO")
    assert f"HTTP {status}" in str(erro.value)
    assert "SEGREDO" not in str(erro.value) and "privada" not in str(erro.value)
    assert erro.value.__suppress_context__
    assert get.call_count == 1


def test_timeout_sem_retry(monkeypatch):
    get = Mock(side_effect=requests.Timeout("SEGREDO"))
    monkeypatch.setattr(xfetch.requests, "get", get)
    with pytest.raises(xfetch.ErroXFetch, match="comunicação") as erro:
        xfetch.buscar_tweets_xfetch("sintética", api_key="fake")
    assert "SEGREDO" not in str(erro.value) and get.call_count == 1


@pytest.mark.parametrize("corpo", [None, [], {}, {"data": None}, {"error": "falhou"},
                                  {"data": [], "meta": []},
                                  {"data": [], "meta": {"pagination": []}},
                                  {"data": [], "meta": {"pagination": {"next_token": 3}}},
                                  {"data": [], "meta": {"pagination": {"next_token": " "}}}])
def test_envelope_invalido(monkeypatch, corpo):
    resposta = criar_resposta([])
    resposta.json.return_value = corpo
    monkeypatch.setattr(xfetch.requests, "get", Mock(return_value=resposta))
    with pytest.raises(xfetch.ErroXFetch):
        xfetch.buscar_tweets_xfetch("sintética", api_key="fake")


@pytest.mark.parametrize("identificador", [True, {}, [], "", "  ", 1.1])
def test_identificador_invalido(identificador):
    assert xfetch._normalizar_tweet({"id": identificador, "text": "Texto"}) is None


@pytest.mark.parametrize("data", ["2026-11-09T10:00:00", "inválida", 42, "2026-11-09"])
def test_data_sem_fuso_ou_invalida(data):
    with pytest.raises(xfetch.ErroXFetch):
        xfetch._normalizar_tweet({"id": "syn-1", "text": "Texto", "created_at": data})


def test_preserva_texto_e_filtra_metadados():
    texto = "  @exemplo Não gostei!!! 😊 https://example.invalid  "
    tweet = {"id": "synthetic-1", "text": texto, "created_at": "2026-11-09T07:00:00-03:00",
             "author_id": "autor-sintetico", "author": {"name": "sintético"},
             "lang": {"segredo": "não copiar"}, "like_count": -1, "reply_count": True,
             "quote_count": {"author_id": "não copiar"}, "retweet_count": 2}
    registro = xfetch._normalizar_tweet(tweet)
    assert registro["texto_original"] == texto
    assert registro["metadados"] == {"provedor": "XFetch", "retweet_count": 2}
    assert registro["data_publicacao"] == "2026-11-09T10:00:00Z"
    assert "sentimento" not in registro
    sem_data = xfetch._normalizar_tweet({"id": "synthetic-2", "text": "Texto"})
    assert sem_data["data_publicacao"] is None


@pytest.mark.parametrize("chave", ["", "  ", 42])
def test_chave_invalida_nao_faz_requisicao(monkeypatch, chave):
    get = Mock()
    monkeypatch.setattr(xfetch.requests, "get", get)
    with pytest.raises(xfetch.ErroXFetch):
        xfetch.buscar_tweets_xfetch("sintética", api_key=chave)
    get.assert_not_called()
