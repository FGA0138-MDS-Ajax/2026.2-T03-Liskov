"""Cliente HTTP: consome o contrato proposto e transforma falhas em mensagens claras.

As respostas são simuladas. Estes testes NÃO comprovam integração com o backend,
que ainda não oferece as rotas de análises.
"""

from copy import deepcopy
from datetime import UTC, date, datetime

import pytest
import requests

from src.apresentacao.contrato import ErroFonteDados, FiltrosAnalises
from src.apresentacao.fontes.api import FonteApi

ANALISE_JSON = {
    "id_origem": "c_001",
    "fonte": "exemplo_coleta",
    "texto_original": "Não recomendo.",
    "sentimento": "negativo",
    "modelo": {"nome": "pysentimiento/bertweet-pt-sentiment"},
    "data_processamento": "2026-10-29T14:30:05Z",
}


class RespostaFalsa:
    def __init__(self, status_code=200, corpo=None):
        self.status_code = status_code
        self._corpo = corpo

    def json(self):
        if self._corpo is None:
            raise ValueError("corpo não é JSON")
        return self._corpo


class SessaoFalsa:
    def __init__(self, resposta=None, excecao=None):
        self.resposta = resposta
        self.excecao = excecao
        self.chamadas = []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append({"url": url, "params": params, "timeout": timeout})
        if self.excecao is not None:
            raise self.excecao
        return self.resposta


def criar_fonte(**kwargs):
    sessao = SessaoFalsa(**kwargs)
    return FonteApi("http://api", timeout_segundos=3, sessao=sessao), sessao


def test_verificar_saude_usa_a_rota_existente():
    fonte, sessao = criar_fonte(resposta=RespostaFalsa(corpo={"status": "ok"}))
    assert fonte.verificar_saude() is True
    assert sessao.chamadas[0]["url"] == "http://api/health"


def test_listar_envia_filtros_e_converte_a_resposta():
    corpo = {"itens": [ANALISE_JSON], "pagina": 2, "tamanho": 10, "total": 11}
    fonte, sessao = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    filtros = FiltrosAnalises(
        inicio=date(2026, 10, 1), fim=date(2026, 10, 31), sentimento="negativo"
    )

    pagina = fonte.listar(filtros, pagina=2, tamanho=10)

    assert sessao.chamadas[0]["params"] == {
        "inicio": "2026-10-01",
        "fim": "2026-10-31",
        "sentimento": "negativo",
        "pagina": 2,
        "tamanho": 10,
    }
    assert sessao.chamadas[0]["timeout"] == 3
    assert pagina.total == 11
    analise = pagina.itens[0]
    assert analise.modelo_nome == "pysentimiento/bertweet-pt-sentiment"
    assert analise.data_processamento == datetime(2026, 10, 29, 14, 30, 5, tzinfo=UTC)
    assert analise.data_publicacao is None


def test_listar_com_colecao_vazia_nao_e_erro():
    corpo = {"itens": [], "pagina": 1, "tamanho": 20, "total": 0}
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    assert fonte.listar(FiltrosAnalises()).itens == []


def test_resumir_converte_contagens():
    corpo = {
        "total": 3,
        "por_sentimento": {"positivo": 1, "neutro": 1, "negativo": 1},
        "sem_data_publicacao": 2,
    }
    fonte, sessao = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    resumo = fonte.resumir(FiltrosAnalises(inicio=date(2026, 10, 1)))
    assert sessao.chamadas[0]["url"] == "http://api/analises/resumo"
    assert resumo.total == 3
    assert resumo.sem_data_publicacao == 2


@pytest.mark.parametrize(
    ("resposta", "trecho"),
    [
        (RespostaFalsa(400), "recusou os filtros"),
        (RespostaFalsa(422), "recusou os filtros"),
        (RespostaFalsa(404), "não oferece a rota"),
        (RespostaFalsa(500), "HTTP 500"),
        (RespostaFalsa(200, None), "resposta inválida"),
        (RespostaFalsa(200, {"total": 1}), "não segue o contrato"),
    ],
)
def test_respostas_com_problema_viram_mensagem_clara(resposta, trecho):
    fonte, _ = criar_fonte(resposta=resposta)
    with pytest.raises(ErroFonteDados, match=trecho):
        fonte.resumir(FiltrosAnalises())


def test_listagem_fora_do_contrato_vira_mensagem_clara():
    corpo = {"itens": [{"id_origem": "x"}], "pagina": 1, "tamanho": 20, "total": 1}
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        fonte.listar(FiltrosAnalises())


@pytest.mark.parametrize(
    ("excecao", "trecho"),
    [
        (requests.ConnectionError(), "Não foi possível conectar"),
        (requests.Timeout(), "demorou demais"),
    ],
)
def test_falhas_de_rede_viram_mensagem_clara(excecao, trecho):
    fonte, _ = criar_fonte(excecao=excecao)
    with pytest.raises(ErroFonteDados, match=trecho):
        fonte.listar(FiltrosAnalises())


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("total", "3"),
        ("total", -1),
        ("total", True),
        ("total", 3.0),
        ("total", 17),
        ("por_sentimento", {"positivo": -1, "neutro": 2, "negativo": 2}),
        ("por_sentimento", {"positivo": True, "neutro": 1, "negativo": 1}),
        ("por_sentimento", {"positivo": "1", "neutro": 1, "negativo": 1}),
        ("por_sentimento", {"positivo": 1.0, "neutro": 1, "negativo": 1}),
        ("por_sentimento", {"positivo": 1, "neutro": 1}),
        ("por_sentimento", {"positivo": 1, "neutro": 1, "negativo": 1, "feliz": 1}),
        ("por_sentimento", []),
        ("sem_data_publicacao", -1),
        ("sem_data_publicacao", True),
        ("sem_data_publicacao", "2"),
        ("sem_data_publicacao", 2.5),
        ("sem_data_publicacao", None),
    ],
)
def test_resumo_rejeita_tipos_classes_e_totais_invalidos(campo, valor):
    corpo = {"total": 3, "por_sentimento": {"positivo": 1, "neutro": 1, "negativo": 1}}
    corpo[campo] = valor
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        fonte.resumir(FiltrosAnalises(inicio=date(2026, 10, 1)))


def test_sem_filtro_de_periodo_nao_pode_haver_excluidos_sem_data():
    corpo = {
        "total": 0,
        "por_sentimento": {"positivo": 0, "neutro": 0, "negativo": 0},
        "sem_data_publicacao": 1,
    }
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        fonte.resumir(FiltrosAnalises())


@pytest.mark.parametrize("sem_data", [None, 0, 10])
def test_resumo_vazio_e_excluidos_separados_do_total(sem_data):
    corpo = {"total": 0, "por_sentimento": {"positivo": 0, "neutro": 0, "negativo": 0}}
    if sem_data is not None:
        corpo["sem_data_publicacao"] = sem_data
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    resumo = fonte.resumir(FiltrosAnalises(fim=date(2026, 10, 31)))
    assert resumo.total == 0
    assert resumo.sem_data_publicacao == (sem_data or 0)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("id_origem", 123),
        ("id_origem", ""),
        ("id_origem", "  "),
        ("fonte", None),
        ("fonte", False),
        ("texto_original", 123),
        ("texto_original", []),
        ("sentimento", "feliz"),
        ("sentimento", ["positivo"]),
        ("modelo", {"nome": ""}),
        ("modelo", {"nome": "  "}),
        ("modelo", {"nome": 123}),
        ("modelo", None),
        ("data_processamento", "2026-10-29T14:30:05"),
        ("data_processamento", "2026-10-29"),
        ("data_processamento", "2026-02-30T14:30:05Z"),
        ("data_processamento", None),
        ("data_publicacao", "2026-10-29T14:30:05"),
        ("data_publicacao", ""),
        ("data_publicacao", "invalida"),
        ("data_publicacao", False),
    ],
)
def test_analise_incompativel_e_rejeitada(campo, valor):
    item = deepcopy(ANALISE_JSON)
    item[campo] = valor
    corpo = {"itens": [item], "pagina": 1, "tamanho": 20, "total": 1}
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        fonte.listar(FiltrosAnalises())


@pytest.mark.parametrize("publicacao", [None, "2026-10-29T17:30:05+03:00"])
def test_datas_validas_sao_normalizadas_para_utc_sem_inventar_publicacao(publicacao):
    item = deepcopy(ANALISE_JSON)
    item["data_processamento"] = "2026-10-29T11:30:05-03:00"
    item["data_publicacao"] = publicacao
    fonte, _ = criar_fonte(
        resposta=RespostaFalsa(
            corpo={"itens": [item], "pagina": 1, "tamanho": 20, "total": 1}
        )
    )
    analise = fonte.listar(FiltrosAnalises()).itens[0]
    assert analise.data_processamento == datetime(2026, 10, 29, 14, 30, 5, tzinfo=UTC)
    assert analise.data_processamento.tzinfo is UTC
    if publicacao is None:
        assert analise.data_publicacao is None
    else:
        assert analise.data_publicacao == analise.data_processamento
        assert analise.data_publicacao.tzinfo is UTC


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("pagina", 0),
        ("pagina", -1),
        ("pagina", True),
        ("pagina", "1"),
        ("tamanho", 0),
        ("tamanho", -1),
        ("tamanho", False),
        ("tamanho", 20.0),
        ("total", -1),
        ("total", True),
        ("total", "1"),
        ("itens", {}),
        ("itens", None),
        ("itens", [None]),
    ],
)
def test_paginacao_da_resposta_deve_seguir_o_contrato(campo, valor):
    corpo = {"itens": [ANALISE_JSON], "pagina": 1, "tamanho": 20, "total": 1}
    corpo[campo] = valor
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        fonte.listar(FiltrosAnalises())


@pytest.mark.parametrize(
    ("pagina", "tamanho", "total", "quantidade"),
    [(1, 1, 3, 2), (1, 20, 0, 1), (2, 10, 11, 2), (2, 10, 10, 1)],
)
def test_itens_nao_podem_superar_tamanho_ou_total_restante(
    pagina, tamanho, total, quantidade
):
    corpo = {
        "itens": [ANALISE_JSON] * quantidade,
        "pagina": pagina,
        "tamanho": tamanho,
        "total": total,
    }
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        fonte.listar(FiltrosAnalises(), pagina=pagina, tamanho=tamanho)


def test_pagina_vazia_depois_do_fim_e_valida():
    fonte, _ = criar_fonte(
        resposta=RespostaFalsa(
            corpo={"itens": [], "pagina": 2, "tamanho": 20, "total": 1}
        )
    )
    assert fonte.listar(FiltrosAnalises(), pagina=2).itens == []


@pytest.mark.parametrize("corpo", [[], "texto", 1, True])
@pytest.mark.parametrize("metodo", ["listar", "resumir", "verificar_saude"])
def test_raiz_json_incompativel_vira_erro_da_fonte(corpo, metodo):
    fonte, _ = criar_fonte(resposta=RespostaFalsa(corpo=corpo))
    with pytest.raises(ErroFonteDados, match="não segue o contrato"):
        if metodo == "verificar_saude":
            fonte.verificar_saude()
        else:
            getattr(fonte, metodo)(FiltrosAnalises())


@pytest.mark.parametrize(
    "parametros", [{"pagina": 0}, {"pagina": True}, {"tamanho": -1}, {"tamanho": "20"}]
)
def test_paginacao_invalida_na_requisicao_nao_acessa_http(parametros):
    fonte, sessao = criar_fonte()
    with pytest.raises(ErroFonteDados, match="inteiros positivos"):
        fonte.listar(FiltrosAnalises(), **parametros)
    assert sessao.chamadas == []
