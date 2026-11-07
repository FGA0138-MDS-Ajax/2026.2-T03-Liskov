"""Limites da configuração, sem depender do .env de quem executa os testes."""

import pytest

from src.apresentacao.config import carregar_configuracao


@pytest.fixture(autouse=True)
def isolar_ambiente(monkeypatch):
    monkeypatch.setattr("src.apresentacao.config.load_dotenv", lambda: None)
    monkeypatch.setenv("SENTIA_FONTE_DADOS", "mock")
    monkeypatch.setenv("SENTIA_MOCK_CENARIO", "normal")


@pytest.mark.parametrize(
    "valor", ["-1", "0", "-0.0", "NaN", "inf", "-inf", "Infinity", "texto", ""]
)
def test_timeout_invalido_e_rejeitado(monkeypatch, valor):
    monkeypatch.setenv("SENTIA_API_TIMEOUT_SEGUNDOS", valor)
    with pytest.raises(ValueError, match="SENTIA_API_TIMEOUT_SEGUNDOS"):
        carregar_configuracao()


@pytest.mark.parametrize("valor", ["0.5", "5", "1e3"])
def test_timeout_finito_positivo_e_aceito(monkeypatch, valor):
    monkeypatch.setenv("SENTIA_API_TIMEOUT_SEGUNDOS", valor)
    assert carregar_configuracao().api_timeout_segundos == float(valor)
