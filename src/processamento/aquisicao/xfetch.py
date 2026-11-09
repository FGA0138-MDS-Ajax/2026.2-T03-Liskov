
"""Aquisição de tweets recentes pela API XFetch para o SentIA."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


URL_BUSCA_RECENTE = "https://api.xfetch.io/v1/search/recent"

# A API permite solicitar até 20 tweets por página.
LIMITE_POR_PAGINA = 20

# None significa que a paginação é automática.
MAX_PAGINAS: int | None = None

LIMITE_MAXIMO_POR_PAGINA = 20
LIMITE_MAXIMO_TOTAL = 100
TEMPO_LIMITE = 30


class ErroXFetch(RuntimeError):
    """Erro ocorrido durante a comunicação com a API XFetch."""


def _validar_parametros(
    consulta: str,
    quantidade: int,
    limite_por_pagina: int,
    max_paginas: int | None,
) -> None:
    """Valida os parâmetros da busca."""

    if not isinstance(consulta, str) or not consulta.strip():
        raise ValueError("A consulta não pode ser vazia.")

    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise TypeError("A quantidade deve ser um número inteiro.")

    if not 1 <= quantidade <= LIMITE_MAXIMO_TOTAL:
        raise ValueError("A quantidade deve estar entre 1 e 100.")

    if isinstance(limite_por_pagina, bool) or not isinstance(
        limite_por_pagina, int
    ):
        raise TypeError("O limite por página deve ser um número inteiro.")

    if not 1 <= limite_por_pagina <= LIMITE_MAXIMO_POR_PAGINA:
        raise ValueError("O limite por página deve estar entre 1 e 20.")

    if max_paginas is not None:
        if isinstance(max_paginas, bool) or not isinstance(max_paginas, int):
            raise TypeError("O máximo de páginas deve ser um inteiro ou None.")

        if max_paginas <= 0:
            raise ValueError("O máximo de páginas deve ser maior que zero.")


def _extrair_proximo_token(resposta: dict[str, Any]) -> str | None:
    """Extrai o token da próxima página da resposta da API."""

    meta = resposta.get("meta", {})

    if meta is None:
        return None

    if not isinstance(meta, dict):
        raise ErroXFetch("O campo 'meta' possui formato inválido.")

    paginacao = meta.get("pagination", {})

    if paginacao is None:
        return None

    if not isinstance(paginacao, dict):
        raise ErroXFetch("O campo 'pagination' possui formato inválido.")

    token = paginacao.get("next_token")

    if token is None or token == "":
        return None

    if not isinstance(token, str):
        raise ErroXFetch("O next_token retornado pela API é inválido.")

    return token


def _normalizar_tweet(tweet: dict[str, Any]) -> dict[str, Any] | None:
    """Converte um tweet da XFetch para o contrato de aquisição do SentIA."""

    identificador = tweet.get("id")
    texto = tweet.get("text")

    if identificador is None or not isinstance(texto, str):
        return None

    if not texto.strip():
        return None

    metadados = {
        "provedor": "XFetch",
    }

    campos_opcionais = (
        "author_id",
        "lang",
        "like_count",
        "retweet_count",
        "reply_count",
        "quote_count",
    )

    for campo in campos_opcionais:
        if campo in tweet:
            metadados[campo] = tweet[campo]

    return {
        "id_origem": str(identificador),
        "texto_original": texto,
        "fonte": "X",
        "rotulo_original": None,
        "rotulo_padronizado": None,
        "data_publicacao": tweet.get("created_at"),
        "metadados": metadados,
    }


def buscar_tweets_xfetch(
    consulta: str,
    quantidade: int = 100,
    *,
    api_key: str | None = None,
    limite_por_pagina: int = LIMITE_POR_PAGINA,
    max_paginas: int | None = MAX_PAGINAS,
) -> list[dict[str, Any]]:
    """Busca tweets recentes e retorna registros padronizados para o SentIA.

    A quantidade é um máximo, não uma quantidade obrigatória.

    A paginação é automática por padrão: novas páginas são consultadas
    até atingir a quantidade solicitada ou até a API não fornecer
    um próximo token.

    Args:
        consulta: Palavra-chave ou frase pesquisada.
        quantidade: Quantidade máxima de tweets desejada (1 a 100).
        api_key: Chave opcional da API. Se omitida, usa XFETCH_API_KEY.
        limite_por_pagina: Quantidade máxima solicitada por requisição.
        max_paginas: Limite opcional de páginas. None permite paginação
            automática até atingir a quantidade ou acabar os resultados.

    Returns:
        Lista de tweets no formato padronizado do SentIA.

    Raises:
        ValueError: Quando algum parâmetro está fora dos limites.
        TypeError: Quando algum parâmetro possui tipo inválido.
        ErroXFetch: Quando ocorre falha na comunicação ou resposta inválida.
    """

    _validar_parametros(
        consulta,
        quantidade,
        limite_por_pagina,
        max_paginas,
    )

    raiz_projeto = Path(__file__).resolve().parents[3]
    load_dotenv(dotenv_path=raiz_projeto / ".env")

    chave = api_key or os.getenv("XFETCH_API_KEY")

    if not chave:
        raise ErroXFetch(
            "Chave da API não encontrada. Configure XFETCH_API_KEY."
        )

    cabecalhos = {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
    }

    registros: list[dict[str, Any]] = []
    ids_vistos: set[str] = set()
    tokens_utilizados: set[str] = set()

    proximo_token: str | None = None
    paginas_consultadas = 0

    while len(registros) < quantidade:

        # Só limita as páginas quando max_paginas foi informado.
        if max_paginas is not None and paginas_consultadas >= max_paginas:
            break

        # Ajusta automaticamente o tamanho da requisição final.
        parametros: dict[str, Any] = {
            "query": consulta.strip(),
            "limit": min(limite_por_pagina, quantidade),
            "sort_order": "recency",
        }

        # A primeira página não utiliza token.
        # As seguintes utilizam o next_token recebido da API.
        if proximo_token:
            parametros["next_token"] = proximo_token

        try:
            resposta = requests.get(
                URL_BUSCA_RECENTE,
                headers=cabecalhos,
                params=parametros,
                timeout=TEMPO_LIMITE,
            )

            resposta.raise_for_status()

        except requests.RequestException as erro:
            raise ErroXFetch(
                f"Falha na comunicação com o XFetch: {erro}"
            ) from erro

        try:
            conteudo = resposta.json()

        except ValueError as erro:
            raise ErroXFetch(
                "A API XFetch retornou uma resposta JSON inválida."
            ) from erro

        if not isinstance(conteudo, dict):
            raise ErroXFetch(
                "A resposta da API XFetch possui formato inválido."
            )

        paginas_consultadas += 1

        dados = conteudo.get("data", [])

        if not isinstance(dados, list):
            raise ErroXFetch(
                "O campo 'data' da resposta não é uma lista."
            )

        # Normaliza os tweets e elimina duplicatas.
        for tweet in dados:

            if not isinstance(tweet, dict):
                continue

            registro = _normalizar_tweet(tweet)

            if registro is None:
                continue

            identificador = registro["id_origem"]

            if identificador in ids_vistos:
                continue

            ids_vistos.add(identificador)
            registros.append(registro)

            if len(registros) >= quantidade:
                break

        # Se a quantidade solicitada foi alcançada, não precisa
        # verificar outra página.
        if len(registros) >= quantidade:
            break

        # Verifica se a API disponibilizou outra página.
        proximo_token = _extrair_proximo_token(conteudo)

        if not proximo_token:
            break

        # Evita consultar novamente uma página já visitada.
        if proximo_token in tokens_utilizados:
            break

        tokens_utilizados.add(proximo_token)

    return registros
