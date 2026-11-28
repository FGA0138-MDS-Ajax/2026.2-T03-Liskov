"""Dashboard no layout de alta fidelidade (#121): termos (#30), evolução, etiqueta do assunto,
"Última análise", selo do predominante e cores por tema. Modo de demonstração."""

from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.apresentacao.contrato import (
    EvolucaoAnalises,
    PontoEvolucao,
    TermoFrequente,
    TermosAnalises,
)
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO
from src.apresentacao.tema import PALETAS

APP = str(Path(__file__).resolve().parents[1] / "src" / "apresentacao" / "app.py")


@pytest.fixture
def app(monkeypatch) -> AppTest:
    monkeypatch.setenv("SENTIA_FONTE_DADOS", "mock")
    monkeypatch.setenv("SENTIA_MOCK_CENARIO", "normal")
    monkeypatch.setenv("SENTIA_API_TIMEOUT_SEGUNDOS", "5")
    return AppTest.from_file(APP, default_timeout=10).run()


def _tabela(app: AppTest, coluna: str):
    return next(t.value for t in app.table if coluna in t.value.columns)


def _filtrar(app: AppTest, assunto: str = "", sentimento: str = "Todos") -> AppTest:
    app.text_input(key="filtro_assunto").set_value(assunto)
    app.selectbox(key="filtro_sentimento").select(sentimento)
    return app.button(key="aplicar_filtros").click().run()


def test_secoes_novas_aparecem_sem_erro(app):
    assert not app.exception and not app.error
    titulos = [m.value for m in app.markdown]
    for titulo in (
        "##### Distribuição dos sentimentos",
        "##### Evolução no período",
        "##### Resumo",
        "##### Termos mais frequentes",
    ):
        assert titulo in titulos


def test_termos_mostram_as_palavras_do_filtro_em_tabela(app):
    termos = _tabela(app, "Termo")

    assert termos["Termo"].iloc[0] == "aplicativo"  # 3 textos de exemplo
    assert int(termos["Quantidade"].iloc[0]) == 3


def test_termos_acompanham_o_assunto_e_tiram_as_palavras_dele(app):
    _filtrar(app, "aplicativo")

    termos = list(_tabela(app, "Termo")["Termo"])
    assert "aplicativo" not in termos and termos


def test_evolucao_soma_os_textos_com_data_e_avisa_os_sem_data(app):
    evolucao = _tabela(app, "Período")
    com_data = sum(a.data_publicacao is not None for a in ANALISES_DE_EXEMPLO)
    sem_data = len(ANALISES_DE_EXEMPLO) - com_data

    total = int(evolucao[["Positivo", "Neutro", "Negativo"]].to_numpy().sum())
    assert total == com_data
    assert any(f"{sem_data} texto(s) sem data" in c.value for c in app.caption)


def test_evolucao_troca_entre_dia_semana_e_mes(app):
    por_semana = len(_tabela(app, "Período"))
    app.segmented_control(key="evolucao_granularidade").set_value("mes").run()
    por_mes = len(_tabela(app, "Período"))

    assert not app.exception
    assert por_mes == 3 and por_semana >= por_mes  # agosto, setembro e outubro


def test_etiqueta_do_assunto_remove_so_o_assunto(app):
    _filtrar(app, "aplicativo", sentimento="Negativo")
    assert app.metric[0].value == "1"

    app.button(key="remover_assunto").click().run()

    negativos = sum(a.sentimento == "negativo" for a in ANALISES_DE_EXEMPLO)
    assert app.metric[0].value == str(negativos)  # o sentimento continua aplicado
    assert app.text_input(key="filtro_assunto").value == ""
    assert not [b for b in app.button if b.key == "remover_assunto"]


def test_ultima_analise_aparece_no_topo_sem_inventar_data(app):
    legenda = next(
        c.value for c in app.caption if c.value.startswith("Última análise:")
    )

    assert legenda.endswith("(UTC)")


def test_selo_mostra_o_sentimento_predominante_com_icone_e_nome(app):
    _filtrar(app, sentimento="Negativo")

    selos = [m.value for m in app.markdown if "Predominante" in m.value]
    assert selos == [":red-badge[:material/sentiment_dissatisfied: Predominante: Negativo]"]


# --- Gráficos: especificação e cores por tema ----------------------------------------


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_grafico_de_termos_usa_a_cor_primaria_do_tema(tema):
    from src.apresentacao.secoes.termos import construir_grafico

    termos = TermosAnalises(
        [TermoFrequente("aluguel", 4), TermoFrequente("salário", 2)], 6, 6
    )
    barras, rotulos = construir_grafico(termos, PALETAS[tema]).to_dict()["layer"]

    assert barras["mark"]["color"] == PALETAS[tema].primaria
    assert rotulos["mark"]["type"] == "text"


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_grafico_de_evolucao_tem_uma_cor_por_sentimento_do_tema(tema):
    from src.apresentacao.secoes.evolucao import ORDEM, construir_grafico

    evolucao = EvolucaoAnalises(
        "semana",
        [
            PontoEvolucao(
                date(2026, 11, 23), {"positivo": 1, "neutro": 0, "negativo": 2}
            )
        ],
    )
    cor = construir_grafico(evolucao, PALETAS[tema]).to_dict()["encoding"]["color"]

    assert cor["scale"]["domain"] == ORDEM
    assert cor["scale"]["range"] == [
        PALETAS[tema].grafico[s] for s in ("positivo", "neutro", "negativo")
    ]
