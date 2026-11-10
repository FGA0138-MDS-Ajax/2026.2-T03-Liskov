"""Escolhe de onde o painel obtém os dados, conforme a configuração."""

from src.apresentacao.config import Configuracao
from src.apresentacao.contrato import FonteAdministracao, FonteAnalises
from src.apresentacao.fontes.administracao_api import AdministracaoApi
from src.apresentacao.fontes.administracao_mock import (
    AdministracaoMock,
    AdministracaoMockComErro,
)
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


def criar_administracao(config: Configuracao) -> FonteAdministracao:
    if config.fonte_dados == "api":
        return AdministracaoApi(config.api_url, config.api_timeout_segundos)
    if config.cenario_mock == "erro":
        return AdministracaoMockComErro()
    return AdministracaoMock()
