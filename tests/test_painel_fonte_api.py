"""Cliente HTTP: consome o contrato proposto e transforma falhas em mensagens claras.

As respostas são simuladas. Estes testes NÃO comprovam integração com o backend,
que ainda não oferece as rotas de análises.
"""

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
    assert analise.data_processamento == datetime(
        2026, 10, 29, 14, 30, 5, tzinfo=UTC
    )
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
    resumo = fonte.resumir(FiltrosAnalises())
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
