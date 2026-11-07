"""Testes de sistema do painel com streamlit.testing, como prevê a arquitetura."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.apresentacao.componentes import MENSAGEM_DADOS_DE_EXEMPLO
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO, FonteMockComErro

APP = str(Path(__file__).resolve().parents[1] / "src" / "apresentacao" / "app.py")


def executar_app(monkeypatch, **ambiente) -> AppTest:
    for variavel in ("SENTIA_FONTE_DADOS", "SENTIA_MOCK_CENARIO", "SENTIA_API_URL"):
        monkeypatch.delenv(variavel, raising=False)
    # Valores explícitos têm prioridade sobre um .env local do desenvolvedor.
    monkeypatch.setenv("SENTIA_FONTE_DADOS", ambiente.pop("fonte", "mock"))
    monkeypatch.setenv("SENTIA_MOCK_CENARIO", ambiente.pop("cenario", "normal"))
    for variavel, valor in ambiente.items():
        monkeypatch.setenv(variavel, valor)
    return AppTest.from_file(APP, default_timeout=10).run()


def avisos(app: AppTest) -> list[str]:
    return [elemento.value for elemento in app.warning]


def test_modo_mock_carrega_e_identifica_os_dados_de_exemplo(monkeypatch):
    app = executar_app(monkeypatch)
    assert not app.exception
    assert app.title[0].value == "SentIA"
    assert MENSAGEM_DADOS_DE_EXEMPLO in avisos(app)


def test_indicadores_refletem_os_dados_e_percentuais_somam_100(monkeypatch):
    app = executar_app(monkeypatch)
    valores = [metrica.value for metrica in app.metric]
    assert valores[0] == str(len(ANALISES_DE_EXEMPLO))
    assert sum(int(valor.rstrip("%")) for valor in valores[1:]) == 100
    rotulos = " ".join(metrica.label for metrica in app.metric)
    for rotulo in ("Analisados", "Positivo", "Neutro", "Negativo"):
        assert rotulo in rotulos


def test_sem_dados_mostra_estado_vazio_sem_percentuais_enganosos(monkeypatch):
    app = executar_app(monkeypatch, cenario="vazio")
    assert not app.exception
    assert "Nenhuma análise encontrada." in [i.value for i in app.info]
    assert not app.metric


def test_erro_da_fonte_mostra_mensagem_sem_quebrar_a_tela(monkeypatch):
    app = executar_app(monkeypatch, cenario="erro")
    assert not app.exception
    assert [e.value for e in app.error] == [FonteMockComErro.MENSAGEM]
    assert not app.metric


def test_modo_api_indisponivel_mostra_erro_e_nao_apresenta_mock(monkeypatch):
    # Porta 9 (discard) recusa a conexão: não depende de backend em execução.
    app = executar_app(monkeypatch, fonte="api", SENTIA_API_URL="http://127.0.0.1:9")
    assert not app.exception
    assert "Não foi possível conectar" in app.error[0].value
    assert MENSAGEM_DADOS_DE_EXEMPLO not in avisos(app)
    assert not app.metric


def test_configuracao_invalida_mostra_erro_claro(monkeypatch):
    app = executar_app(monkeypatch, fonte="desconhecida")
    assert not app.exception
    assert "SENTIA_FONTE_DADOS" in app.error[0].value


@pytest.mark.parametrize("cenario", ["normal", "vazio", "erro"])
def test_todos_os_cenarios_de_exemplo_mantem_o_aviso(monkeypatch, cenario):
    assert MENSAGEM_DADOS_DE_EXEMPLO in avisos(executar_app(monkeypatch, cenario=cenario))
