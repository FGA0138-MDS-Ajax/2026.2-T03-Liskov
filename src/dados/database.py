"""Conexão explícita ao MongoDB; importar este módulo não cria clientes."""

import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, OperationFailure


class ErroConfiguracaoMongoDB(ValueError):
    """Configuração ausente ou inválida, sem reproduzir credenciais."""


class ErroConexaoMongoDB(RuntimeError):
    """Falha de conectividade ou encerramento, com mensagem pública segura."""


def connect_to_mongodb(
    uri: str | None = None,
    *,
    timeout_ms: int = 5000,
    client_factory: Callable[..., Any] | None = None,
) -> MongoClient:
    """Cria cliente, executa ping e o devolve; o chamador deve fechá-lo.

    Sem URI explícita, lê MONGODB_URI do ambiente/.env. A fábrica é injetável
    para testes sem rede. Se a conexão falhar, fecha o cliente antes de lançar
    uma exceção segura. Não mantém instância global nem estado entre chamadas.
    """
    if uri is None:
        load_dotenv()
        uri = os.getenv("MONGODB_URI")
    if not isinstance(uri, str) or not uri.strip():
        raise ErroConfiguracaoMongoDB(
            "Defina MONGODB_URI no ambiente ou no arquivo .env."
        )
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ErroConfiguracaoMongoDB(
            "O timeout do MongoDB deve ser inteiro positivo em ms."
        )

    fabrica = MongoClient if client_factory is None else client_factory
    client = None
    conectado = False
    try:
        client = fabrica(
            uri,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            socketTimeoutMS=timeout_ms,
        )
        client.admin.command("ping")
        conectado = True
        return client
    except ConfigurationError:
        raise ErroConfiguracaoMongoDB(
            "Configuração do MongoDB inválida; verifique a URI e o DNS."
        ) from None
    except OperationFailure:
        raise ErroConexaoMongoDB(
            "MongoDB recusou a operação; verifique autenticação e permissões."
        ) from None
    except ConnectionFailure:
        raise ErroConexaoMongoDB(
            "Não foi possível conectar ao MongoDB; verifique rede e timeout."
        ) from None
    except Exception:  # noqa: BLE001 - Fronteira pública: não propagar URI do driver/fábrica.
        # Exceções de driver/fábrica podem carregar a URI. Nunca as imprimir.
        raise ErroConexaoMongoDB(
            "Falha ao inicializar ou validar a conexão com o MongoDB."
        ) from None
    finally:
        if client is not None and not conectado:
            try:
                disconnect_from_mongodb(client)
            except ErroConexaoMongoDB:
                # Preserva a falha original de conexão se close também falhar.
                pass


def disconnect_from_mongodb(client: MongoClient) -> None:
    """Fecha a instância recebida, sem depender de singleton global."""
    try:
        client.close()
    except Exception:  # noqa: BLE001 - close também pode conter credenciais na exceção.
        raise ErroConexaoMongoDB(
            "Não foi possível encerrar o cliente MongoDB."
        ) from None
