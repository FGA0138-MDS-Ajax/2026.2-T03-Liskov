"""Testes de sistema do painel com streamlit.testing, como prevê a arquitetura."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from src.apresentacao.componentes import MENSAGEM_DADOS_DE_EXEMPLO
from src.apresentacao.contrato import ErroFonteDados
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO, FonteMockComErro
from src.apresentacao.secoes import listagem

APP = str(Path(__file__).resolve().parents[1] / "src" / "apresentacao" / "app.py")


def executar_app(monkeypatch, **ambiente) -> AppTest:
    for variavel in ("SENTIA_FONTE_DADOS", "SENTIA_MOCK_CENARIO", "SENTIA_API_URL"):
        monkeypatch.delenv(variavel, raising=False)
    # Valores explícitos têm prioridade sobre um .env local do desenvolvedor.
    monkeypatch.setenv("SENTIA_FONTE_DADOS", ambiente.pop("fonte", "mock"))
    monkeypatch.setenv("SENTIA_MOCK_CENARIO", ambiente.pop("cenario", "normal"))
    monkeypatch.setenv("SENTIA_API_TIMEOUT_SEGUNDOS", "5")
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
    assert MENSAGEM_DADOS_DE_EXEMPLO in avisos(
        executar_app(monkeypatch, cenario=cenario)
    )


@pytest.mark.parametrize("valor", ["-1", "0", "NaN", "inf", "-inf", "texto"])
def test_timeout_invalido_mostra_erro_de_configuracao_sem_excecao(monkeypatch, valor):
    app = executar_app(monkeypatch, fonte="api", SENTIA_API_TIMEOUT_SEGUNDOS=valor)
    assert not app.exception
    assert "SENTIA_API_TIMEOUT_SEGUNDOS" in app.error[0].value
    assert not app.metric


@pytest.mark.parametrize(
    "corpo",
    [
        {"total": "3", "por_sentimento": {"positivo": 1, "neutro": 1, "negativo": 1}},
        {"total": 3, "por_sentimento": {"positivo": -1, "neutro": 2, "negativo": 2}},
        {"total": 17, "por_sentimento": {"positivo": 1, "neutro": 1, "negativo": 1}},
    ],
)
def test_resposta_http_invalida_nao_quebra_a_interface(monkeypatch, corpo):
    resposta = Mock(status_code=200)
    resposta.json.return_value = corpo
    monkeypatch.setattr("requests.Session.get", Mock(return_value=resposta))
    app = executar_app(monkeypatch, fonte="api")
    assert not app.exception
    assert "não segue o contrato" in app.error[0].value
    assert not app.metric
    assert MENSAGEM_DADOS_DE_EXEMPLO not in avisos(app)


# --- Listagem de análises (#27) ---------------------------------------------------


def test_listagem_mostra_todas_as_analises_de_exemplo_com_as_colunas_previstas(monkeypatch):
    app = executar_app(monkeypatch)
    assert not app.exception
    tabela = app.dataframe[0].value
    assert len(tabela) == len(ANALISES_DE_EXEMPLO)
    assert list(tabela.columns) == [
        "Texto", "Sentimento", "Fonte", "Publicado em (UTC)", "Processado em (UTC)", "Modelo",
    ]
    assert set(tabela["Sentimento"]) == {"Positivo", "Neutro", "Negativo"}
    assert "Sem data" in set(tabela["Publicado em (UTC)"])
    # Ainda é mock: a tela precisa continuar dizendo isso.
    assert MENSAGEM_DADOS_DE_EXEMPLO in avisos(app)


def test_sem_dados_nao_mostra_tabela(monkeypatch):
    app = executar_app(monkeypatch, cenario="vazio")
    assert not app.dataframe


def test_erro_da_fonte_nao_mostra_tabela(monkeypatch):
    app = executar_app(monkeypatch, cenario="erro")
    assert not app.dataframe


def test_paginacao_navega_entre_paginas_sem_repetir_nem_perder_itens(monkeypatch):
    monkeypatch.setattr(listagem, "TAMANHO_PAGINA", 6)
    app = executar_app(monkeypatch)
    textos = list(app.dataframe[0].value["Texto"])
    assert len(textos) == 6
    assert app.button(key="listagem_anterior").disabled
    assert "Página 1 de 3" in app.caption[-1].value

    for pagina in (2, 3):
        app.button(key="listagem_proxima").click().run()
        assert not app.exception
        assert f"Página {pagina} de 3" in app.caption[-1].value
        textos += list(app.dataframe[0].value["Texto"])

    assert app.button(key="listagem_proxima").disabled
    assert sorted(textos) == sorted(a.texto_original for a in ANALISES_DE_EXEMPLO)
    assert "Exibindo 13 a 17 de 17 análises." in app.caption[-1].value


def test_mudar_o_filtro_volta_a_listagem_para_a_primeira_pagina(monkeypatch):
    monkeypatch.setattr(listagem, "TAMANHO_PAGINA", 4)
    app = executar_app(monkeypatch)
    app.button(key="listagem_proxima").click().run()
    assert "Página 2 de" in app.caption[-1].value

    app.selectbox(key="filtro_sentimento").select("Positivo")
    app.button(key="aplicar_filtros").click().run()
    assert not app.exception
    assert set(app.dataframe[0].value["Sentimento"]) == {"Positivo"}
    assert "Página 1 de 2" in app.caption[-1].value


def test_filtro_de_sentimento_filtra_a_lista_na_fonte(monkeypatch):
    app = executar_app(monkeypatch)
    app.selectbox(key="filtro_sentimento").select("Negativo")
    app.button(key="aplicar_filtros").click().run()
    tabela = app.dataframe[0].value
    esperado = sum(a.sentimento == "negativo" for a in ANALISES_DE_EXEMPLO)
    assert len(tabela) == esperado
    assert set(tabela["Sentimento"]) == {"Negativo"}


def test_falha_so_na_listagem_mantem_os_indicadores_e_mostra_o_erro(monkeypatch):
    def falhar(self, filtros, pagina=1, tamanho=20):
        raise ErroFonteDados("Falha simulada na listagem.")

    monkeypatch.setattr("src.apresentacao.fontes.mock.FonteMock.listar", falhar)
    app = executar_app(monkeypatch)
    assert not app.exception
    assert [e.value for e in app.error] == ["Falha simulada na listagem."]
    assert app.metric and not app.dataframe


def test_modo_api_com_resposta_invalida_na_listagem_nao_quebra_a_tela(monkeypatch):
    def responder(self, url, params=None, timeout=None):
        corpo = (
            {"total": 1, "por_sentimento": {"positivo": 1, "neutro": 0, "negativo": 0}}
            if url.endswith("/resumo")
            else {"itens": [{"id_origem": "x"}], "pagina": 1, "tamanho": 20, "total": 1}
        )
        return Mock(status_code=200, json=Mock(return_value=corpo))

    monkeypatch.setattr("requests.Session.get", responder)
    app = executar_app(monkeypatch, fonte="api")
    assert not app.exception
    assert "não segue o contrato" in app.error[0].value
    assert not app.dataframe
    assert MENSAGEM_DADOS_DE_EXEMPLO not in avisos(app)


# --- Gráfico de distribuição (#28) -------------------------------------------------


def grafico(app):
    return app.get("vega_lite_chart")


def test_grafico_aparece_com_os_mesmos_numeros_dos_indicadores(monkeypatch):
    app = executar_app(monkeypatch)
    assert not app.exception
    assert len(grafico(app)) == 1
    tabela = app.table[0].value
    assert list(tabela["Sentimento"]) == ["Positivo", "Neutro", "Negativo"]
    esperado = [sum(a.sentimento == s for a in ANALISES_DE_EXEMPLO)
                for s in ("positivo", "neutro", "negativo")]
    assert [int(q) for q in tabela["Quantidade"]] == esperado
    assert sum(esperado) == len(ANALISES_DE_EXEMPLO)
    assert app.metric[0].value == str(len(ANALISES_DE_EXEMPLO))


def test_grafico_acompanha_o_filtro_de_sentimento(monkeypatch):
    app = executar_app(monkeypatch)
    app.selectbox(key="filtro_sentimento").select("Negativo")
    app.button(key="aplicar_filtros").click().run()
    assert not app.exception
    quantidades = [int(q) for q in app.table[0].value["Quantidade"]]
    assert quantidades[0] == 0 and quantidades[1] == 0 and quantidades[2] > 0


def test_sem_dados_ou_com_erro_nao_mostra_grafico(monkeypatch):
    for cenario in ("vazio", "erro"):
        app = executar_app(monkeypatch, cenario=cenario)
        assert not app.exception
        assert not grafico(app)


def test_especificacao_do_grafico_usa_as_cores_do_tema_e_ordem_fixa():
    from src.apresentacao.secoes.distribuicao import CORES, ORDEM, construir_grafico

    linhas = [
        {"Sentimento": "Positivo", "Quantidade": 8, "Percentual": 47, "Rótulo": "8 (47%)"},
        {"Sentimento": "Neutro", "Quantidade": 4, "Percentual": 24, "Rótulo": "4 (24%)"},
        {"Sentimento": "Negativo", "Quantidade": 5, "Percentual": 29, "Rótulo": "5 (29%)"},
    ]
    especificacao = construir_grafico(linhas).to_dict()
    barras, valores = especificacao["layer"]
    assert barras["mark"]["type"] == "bar" and valores["mark"]["type"] == "text"
    assert barras["encoding"]["color"]["scale"] == {"domain": ORDEM, "range": CORES}
    assert barras["encoding"]["y"]["sort"] == ORDEM
    # Sem legenda de cor: o nome do sentimento já está no eixo e no valor.
    assert barras["encoding"]["color"]["legend"] is None
    assert [d["Quantidade"] for d in next(iter(especificacao["datasets"].values()))] == [8, 4, 5]


# --- Resumo textual (#29) ----------------------------------------------------------


def texto_do_resumo(app) -> str:
    """O resumo é o único `markdown` que começa com "Total de" ou "Nenhuma análise"."""
    textos = [m.value for m in app.markdown]
    achados = [t for t in textos if t.startswith(("Total de", "Nenhuma análise"))]
    assert len(achados) == 1, textos
    return achados[0]


def test_resumo_textual_aparece_e_bate_com_indicadores_e_grafico(monkeypatch):
    app = executar_app(monkeypatch)
    assert not app.exception
    texto = texto_do_resumo(app)
    assert f"Total de {len(ANALISES_DE_EXEMPLO)} análises" in texto
    tabela = app.table[0].value
    for sentimento, quantidade in zip(tabela["Sentimento"], tabela["Quantidade"], strict=True):
        assert f"{sentimento} {int(quantidade)} (" in texto
    percentuais = [metrica.value for metrica in app.metric[1:]]
    assert all(p in texto for p in percentuais)


def test_resumo_textual_acompanha_o_filtro_de_sentimento(monkeypatch):
    app = executar_app(monkeypatch)
    app.selectbox(key="filtro_sentimento").select("Negativo")
    app.button(key="aplicar_filtros").click().run()
    assert not app.exception
    texto = texto_do_resumo(app)
    assert "com sentimento negativo" in texto
    assert "predominante:" not in texto


def test_resumo_textual_sem_dados_informa_ausencia_sem_afirmar_sentimento(monkeypatch):
    app = executar_app(monkeypatch, cenario="vazio")
    assert not app.exception
    texto = texto_do_resumo(app)
    assert "não há distribuição nem sentimento predominante" in texto
    assert "%" not in texto


def test_resumo_textual_nao_aparece_com_erro_da_fonte(monkeypatch):
    app = executar_app(monkeypatch, cenario="erro")
    assert not app.exception
    assert not [m for m in app.markdown if m.value.startswith(("Total de", "Nenhuma análise"))]
