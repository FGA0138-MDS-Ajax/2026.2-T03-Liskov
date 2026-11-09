"""Escolhe de onde o painel obtém os dados, conforme a configuração."""

from src.apresentacao.config import Configuracao
from src.apresentacao.contrato import FonteAnalises
from src.apresentacao.fontes.api import FonteApi
from src.apresentacao.fontes.mock import FonteMock, FonteMockComErro


def criar_fonte(config: Configuracao) -> FonteAnalises:
    if config.fonte_dados == "api":
        return FonteApi(config.api_url, config.api_timeout_segundos)
    if config.cenario_mock == "erro":
        return FonteMockComErro()
    if config.cenario_mock == "vazio":
        return FonteMock(analises=[])
    return FonteMock()
