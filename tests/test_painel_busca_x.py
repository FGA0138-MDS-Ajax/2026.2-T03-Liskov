"""Busca do Usuário no X pelo dashboard (#120): cliente HTTP, modo de demonstração e tela."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.apresentacao.contrato import ErroFonteDados
from src.apresentacao.fontes.administracao_mock import AdministracaoMock
from tests.test_painel_administracao import cliente

APP = str(Path(__file__).resolve().parents[1] / "src" / "apresentacao" / "app.py")
COLETA = {
    "id": "col-7",
    "fonte": "pesquisa",
    "situacao": "em_andamento",
    "textos_coletados": 0,
    "textos_analisados": 0,
    "mensagem": None,
    "termo": "vacina",
    "por_sentimento": {"positivo": 0, "neutro": 0, "negativo": 0},
    "exemplos": [],
}


# --- Cliente HTTP ---------------------------------------------------------------


def test_busca_vai_para_a_rota_publica_sem_token_e_so_com_o_termo():
    api, http = cliente(status=202, corpo=COLETA)

    coleta = api.buscar_como_usuario("  vacina   infantil ")

    chamada = http.chamadas[0]
    assert chamada["metodo"] == "post" and chamada["url"] == "http://api/pesquisas"
    assert chamada["json"] == {"termo": "vacina infantil"}  # sem meta nem "forçar"
    assert "Authorization" not in chamada["headers"]
    assert coleta.id == "col-7" and coleta.situacao == "em_andamento"


def test_acompanhamento_consulta_a_rota_publica_pelo_id():
    api, http = cliente(status=200, corpo={**COLETA, "situacao": "concluida"})

    coleta = api.consultar_busca_usuario("col/7")

    assert http.chamadas[0]["url"] == "http://api/pesquisas/col%2F7"
    assert coleta.situacao == "concluida"


@pytest.mark.parametrize("termo", ["", "   ", "a" * 101])
def test_termo_invalido_e_recusado_antes_de_chamar_a_api(termo):
    api, http = cliente(status=202, corpo=COLETA)

    with pytest.raises(ErroFonteDados, match="até 100 caracteres"):
        api.buscar_como_usuario(termo)
    assert http.chamadas == []


@pytest.mark.parametrize(
    ("status", "corpo", "trecho"),
    [
        (422, {"mensagem": "Informe uma palavra ou frase de até 100 caracteres."}, "até 100"),
        (404, {"mensagem": "Pesquisa não encontrada."}, "não encontrada"),
        (503, {"mensagem": "Banco de dados indisponível."}, "indisponível"),
    ],
)
def test_erros_da_busca_viram_mensagens_claras(status, corpo, trecho):
    api, _ = cliente(status=status, corpo=corpo)

    with pytest.raises(ErroFonteDados, match=trecho):
        api.consultar_busca_usuario("col-7")


# --- Modo de demonstração -------------------------------------------------------


def test_mock_conclui_sem_buscar_nada_de_verdade_e_avisa():
    mock = AdministracaoMock()

    iniciada = mock.buscar_como_usuario("custo de vida")
    concluida = mock.consultar_busca_usuario(iniciada.id)

    assert iniciada.situacao == "em_andamento"
    assert concluida.situacao == "concluida" and concluida.termo == "custo de vida"
    assert "Dados de exemplo" in concluida.mensagem


def test_mock_recusa_busca_desconhecida():
    with pytest.raises(ErroFonteDados, match="não encontrada"):
        AdministracaoMock().consultar_busca_usuario("outra")


# --- Tela -----------------------------------------------------------------------


@pytest.fixture
def app(monkeypatch) -> AppTest:
    monkeypatch.setenv("SENTIA_FONTE_DADOS", "mock")
    monkeypatch.setenv("SENTIA_MOCK_CENARIO", "normal")
    monkeypatch.setenv("SENTIA_API_TIMEOUT_SEGUNDOS", "5")
    return AppTest.from_file(APP, default_timeout=10).run()


def _filtrar(app: AppTest, assunto: str) -> AppTest:
    app.text_input(key="filtro_assunto").set_value(assunto)
    return app.button(key="aplicar_filtros").click().run()


def _tem_botao(app: AppTest) -> bool:
    return any(b.key == "buscar_no_x" for b in app.button)


def test_sem_assunto_nao_oferece_busca_no_x(app):
    assert not _tem_botao(app)


def test_assunto_com_menos_de_50_oferece_a_busca_e_explica_o_limite(app):
    _filtrar(app, "aplicativo")

    assert _tem_botao(app)
    assert any("Há **3** análise(s) sobre “aplicativo”" in m.value for m in app.markdown)
    assert any("limitado" in c.value for c in app.caption)


def test_buscar_no_x_mostra_o_resultado_e_o_aviso_de_dados_de_exemplo(app):
    _filtrar(app, "aplicativo")

    app.button(key="buscar_no_x").click().run()

    assert not app.exception
    assert any(
        "Busca concluída: 3 texto(s) da base do SentIA e 12 novo(s) do X." in s.value
        for s in app.success
    )
    assert any("Dados de exemplo" in i.value for i in app.info)
    assert not _tem_botao(app)  # não oferece de novo o mesmo assunto


def test_assunto_sem_nenhum_texto_tambem_oferece_a_busca(app):
    _filtrar(app, "eleição municipal")

    assert _tem_botao(app)
    assert any("Nenhum texto sobre “eleição municipal”" in i.value for i in app.info)
