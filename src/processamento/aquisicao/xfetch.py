"""Aquisição de tweets recentes pela API XFetch para o SentIA."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


URL_BUSCA_RECENTE = "https://api.xfetch.io/v1/search/recent"

# A API permite solicitar até 20 tweets por página.
LIMITE_POR_PAGINA = 20

# None habilita paginação automática, sempre limitada pelo teto local.
MAX_PAGINAS: int | None = None
LIMITE_SEGURANCA_PAGINAS = 10

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

    if not token.strip():
        raise ErroXFetch("O next_token retornado pela API é inválido.")
    return token


def _normalizar_tweet(tweet: dict[str, Any]) -> dict[str, Any] | None:
    """Converte um tweet da XFetch para o contrato de aquisição do SentIA."""

    identificador = tweet.get("id")
    texto = tweet.get("text")

    if isinstance(identificador, bool) or not isinstance(identificador, (str, int)):
        return None
    if not str(identificador).strip() or not isinstance(texto, str) or not texto.strip():
        return None

    data = tweet.get("created_at")
    if data is not None:
        if not isinstance(data, str):
            raise ErroXFetch("Data de publicação inválida; esperado ISO 8601 com fuso.")
        try:
            instante = datetime.fromisoformat(data.replace("Z", "+00:00"))
            if instante.tzinfo is None:
                raise ValueError("Data sem fuso")
            data = instante.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            raise ErroXFetch("Data de publicação inválida; esperado ISO 8601 com fuso.") from None

    # Lista de permissão: nunca transportar author_id ou perfis para persistência.
    metadados = {"provedor": "XFetch"}
    idioma = tweet.get("lang")
    if isinstance(idioma, str) and idioma.strip():
        metadados["lang"] = idioma
    for campo in ("like_count", "retweet_count", "reply_count", "quote_count"):
        valor = tweet.get(campo)
        if type(valor) is int and valor >= 0:
            metadados[campo] = valor

    return {
        "id_origem": str(identificador),
        "texto_original": texto,
        "fonte": "X",
        "rotulo_original": None,
        "rotulo_padronizado": None,
        "data_publicacao": data,
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
            Todas as chamadas respeitam o teto local de 10 requisições.

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

    if api_key is None:
        raiz_projeto = Path(__file__).resolve().parents[3]
        load_dotenv(dotenv_path=raiz_projeto / ".env")
        chave = os.getenv("XFETCH_API_KEY")
    else:
        chave = api_key
    if not isinstance(chave, str) or not chave.strip():
        raise ErroXFetch("Chave da API não encontrada. Configure XFETCH_API_KEY.")
    chave = chave.strip()

    cabecalhos = {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
    }

    registros: list[dict[str, Any]] = []
    ids_vistos: set[str] = set()
    tokens_utilizados: set[str] = set()

    proximo_token: str | None = None
    paginas_consultadas = 0
    teto_paginas = min(max_paginas or LIMITE_SEGURANCA_PAGINAS, LIMITE_SEGURANCA_PAGINAS)

    while len(registros) < quantidade:

        # Teto absoluto mesmo com tokens novos e páginas vazias/duplicadas.
        if paginas_consultadas >= teto_paginas:
            break

        # XFetch exige manter query, limit e ordenação entre páginas.
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
            status = getattr(getattr(erro, "response", None), "status_code", None)
            detalhe = f" (HTTP {status})" if type(status) is int else ""
            # Não propagar URL/consulta, headers ou chave contidos no erro do driver.
            raise ErroXFetch(f"Falha na comunicação com o XFetch{detalhe}.") from None

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

        dados = conteudo.get("data")

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
