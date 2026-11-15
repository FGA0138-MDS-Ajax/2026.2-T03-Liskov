"""Configuração do painel, lida de variáveis de ambiente ou do arquivo .env."""

import math
import os
from dataclasses import dataclass

from dotenv import load_dotenv

FONTES_VALIDAS = ("mock", "api")
CENARIOS_MOCK = ("normal", "vazio", "erro")


@dataclass(frozen=True)
class Configuracao:
    fonte_dados: str
    api_url: str
    api_timeout_segundos: float
    cenario_mock: str


def carregar_configuracao() -> Configuracao:
    """Lê a configuração. Levanta ValueError se algum valor for inválido."""
    load_dotenv()

    fonte_dados = os.getenv("SENTIA_FONTE_DADOS", "mock")
    if fonte_dados not in FONTES_VALIDAS:
        raise ValueError(
            f"SENTIA_FONTE_DADOS deve ser um de: {', '.join(FONTES_VALIDAS)}."
        )

    cenario_mock = os.getenv("SENTIA_MOCK_CENARIO", "normal")
    if cenario_mock not in CENARIOS_MOCK:
        raise ValueError(
            f"SENTIA_MOCK_CENARIO deve ser um de: {', '.join(CENARIOS_MOCK)}."
        )

    try:
        timeout = float(os.getenv("SENTIA_API_TIMEOUT_SEGUNDOS", "5"))
    except ValueError as erro:
        raise ValueError("SENTIA_API_TIMEOUT_SEGUNDOS deve ser um número.") from erro
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(
            "SENTIA_API_TIMEOUT_SEGUNDOS deve ser um número finito positivo."
        )

    return Configuracao(
        fonte_dados=fonte_dados,
        api_url=os.getenv("SENTIA_API_URL", "http://localhost:8000").rstrip("/"),
        api_timeout_segundos=timeout,
        cenario_mock=cenario_mock,
    )
