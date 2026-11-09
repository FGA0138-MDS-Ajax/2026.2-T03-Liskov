"""Filtros de período e sentimento do dashboard (RF11, RF12), com dados de exemplo."""

from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.apresentacao.contrato import FiltrosAnalises
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO
from src.apresentacao.secoes.filtros import ROTULOS
from src.apresentacao.transformacoes import descrever_filtros, montar_filtros

APP = str(Path(__file__).resolve().parents[1] / "src" / "apresentacao" / "app.py")
AGOSTO = (date(2026, 8, 1), date(2026, 8, 31))
SEM_DATA = sum(a.data_publicacao is None for a in ANALISES_DE_EXEMPLO)


# --- Regras, sem Streamlit ----------------------------------------------------


def test_periodo_invertido_e_recusado_com_mensagem_clara():
    with pytest.raises(ValueError, match="data inicial"):
        montar_filtros(date(2026, 9, 1), date(2026, 8, 1), None)


@pytest.mark.parametrize(
    ("inicio", "fim"),
    [(None, None), (date(2026, 8, 1), None), (None, date(2026, 8, 1)), AGOSTO],
)
def test_periodo_aberto_ou_completo_e_aceito(inicio, fim):
    assert montar_filtros(inicio, fim, None) == FiltrosAnalises(inicio=inicio, fim=fim)


def test_mesmo_dia_no_inicio_e_no_fim_e_aceito():
    dia = date(2026, 8, 3)
    assert montar_filtros(dia, dia, "positivo").inicio == dia


def test_sentimento_fora_das_classes_e_recusado():
    with pytest.raises(ValueError):
        montar_filtros(None, None, "irritado")


@pytest.mark.parametrize(
    ("filtros", "esperado"),
    [
        (FiltrosAnalises(), "Exibindo todas as análises."),
        (
            FiltrosAnalises(*AGOSTO, "negativo"),
            (
                "Exibindo análises publicadas de 01/08/2026 a 31/08/2026, "
                "com sentimento negativo."
            ),
        ),
        (FiltrosAnalises(inicio=AGOSTO[0]), "Exibindo análises publicadas a partir de 01/08/2026."),
        (FiltrosAnalises(fim=AGOSTO[1]), "Exibindo análises publicadas até 31/08/2026."),
    ],
)
def test_descricao_textual_dos_filtros(filtros, esperado):
    assert descrever_filtros(filtros, ROTULOS) == esperado


# --- Tela ---------------------------------------------------------------------


@pytest.fixture
def app(monkeypatch) -> AppTest:
    monkeypatch.setenv("SENTIA_FONTE_DADOS", "mock")
    monkeypatch.setenv("SENTIA_MOCK_CENARIO", "normal")
    monkeypatch.setenv("SENTIA_API_TIMEOUT_SEGUNDOS", "5")
    return AppTest.from_file(APP, default_timeout=10).run()


def aplicar(app: AppTest, inicio=None, fim=None, sentimento="Todos") -> AppTest:
    app.date_input(key="filtro_inicio").set_value(inicio)
    app.date_input(key="filtro_fim").set_value(fim)
    app.selectbox(key="filtro_sentimento").select(sentimento)
    return app.button(key="aplicar_filtros").click().run()


def total(app: AppTest) -> str:
    return app.metric[0].value


def test_filtro_de_sentimento_restringe_os_indicadores(app):
    aplicar(app, sentimento="Negativo")
    negativos = sum(a.sentimento == "negativo" for a in ANALISES_DE_EXEMPLO)
    assert total(app) == str(negativos)
    assert [m.value for m in app.metric[1:]] == ["0%", "0%", "100%"]


def test_filtro_de_periodo_avisa_quantos_textos_ficaram_sem_data(app):
    aplicar(app, *AGOSTO)
    em_agosto = sum(
        a.data_publicacao is not None and a.data_publicacao.month == 8
        for a in ANALISES_DE_EXEMPLO
    )
    assert total(app) == str(em_agosto)
    assert any(f"{SEM_DATA} texto(s) sem data" in i.value for i in app.info)


def test_periodo_invertido_mostra_erro_e_mantem_os_filtros_anteriores(app):
    aplicar(app, sentimento="Negativo")
    antes = total(app)
    aplicar(app, date(2026, 9, 1), date(2026, 8, 1), "Negativo")
    assert "data inicial" in app.error[0].value
    assert total(app) == antes


def test_periodo_sem_resultados_mostra_estado_vazio_proprio(app):
    aplicar(app, date(2020, 1, 1), date(2020, 1, 31))
    assert "Nenhuma análise encontrada para os filtros aplicados." in [
        i.value for i in app.info
    ]
    assert not app.metric


def test_limpar_volta_a_exibir_todas_as_analises(app):
    aplicar(app, *AGOSTO, "Positivo")
    app.button(key="limpar_filtros").click().run()
    assert total(app) == str(len(ANALISES_DE_EXEMPLO))
    assert "Exibindo todas as análises." in [c.value for c in app.caption]


def test_sem_filtro_de_periodo_nao_ha_aviso_de_textos_sem_data(app):
    assert not any("sem data" in i.value for i in app.info)


def test_limpar_restaura_campos_e_permite_nova_aplicacao(app):
    aplicar(app, date(2026, 9, 1), date(2026, 8, 1), "Negativo")
    app.button(key="limpar_filtros").click().run()
    assert app.date_input(key="filtro_inicio").value is None
    assert app.date_input(key="filtro_fim").value is None
    assert app.selectbox(key="filtro_sentimento").value == "Todos"
    aplicar(app, sentimento="Negativo")
    assert total(app) == "5"
    assert not app.error
