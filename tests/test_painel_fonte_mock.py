"""A fonte de exemplo precisa se comportar como a API proposta, inclusive nos filtros."""

from datetime import date

from src.apresentacao.contrato import FiltrosAnalises
from src.apresentacao.fontes.mock import ANALISES_DE_EXEMPLO, FonteMock


def test_sem_filtros_retorna_todos_os_registros():
    assert FonteMock().resumir(FiltrosAnalises()).total == len(ANALISES_DE_EXEMPLO)


def test_filtro_de_sentimento_retorna_somente_a_classe_escolhida():
    pagina = FonteMock().listar(FiltrosAnalises(sentimento="negativo"), tamanho=100)
    assert pagina.total > 0
    assert {a.sentimento for a in pagina.itens} == {"negativo"}


def test_filtro_de_periodo_inclui_as_duas_extremidades():
    filtros = FiltrosAnalises(inicio=date(2026, 8, 3), fim=date(2026, 8, 12))
    pagina = FonteMock().listar(filtros, tamanho=100)
    datas = {a.data_publicacao.date() for a in pagina.itens}
    assert {date(2026, 8, 3), date(2026, 8, 12)} <= datas
    assert all(date(2026, 8, 3) <= d <= date(2026, 8, 12) for d in datas)


def test_filtro_de_periodo_exclui_e_conta_registros_sem_data():
    fonte = FonteMock()
    filtros = FiltrosAnalises(inicio=date(2000, 1, 1))
    sem_data = sum(a.data_publicacao is None for a in ANALISES_DE_EXEMPLO)
    assert sem_data > 0
    assert fonte.resumir(filtros).sem_data_publicacao == sem_data
    assert all(a.data_publicacao for a in fonte.listar(filtros, tamanho=100).itens)


def test_filtros_combinados_mantem_listagem_e_resumo_consistentes():
    fonte = FonteMock()
    filtros = FiltrosAnalises(inicio=date(2026, 9, 1), sentimento="positivo")
    pagina = fonte.listar(filtros, tamanho=100)
    resumo = fonte.resumir(filtros)
    assert pagina.total == resumo.total == resumo.por_sentimento["positivo"]
    assert resumo.por_sentimento["negativo"] == 0


def test_paginas_nao_repetem_nem_perdem_registros():
    fonte = FonteMock()
    ids = [
        a.id_origem
        for numero in (1, 2, 3, 4)
        for a in fonte.listar(FiltrosAnalises(), pagina=numero, tamanho=5).itens
    ]
    assert ids == [a.id_origem for a in ANALISES_DE_EXEMPLO]


def test_colecao_vazia_retorna_lista_vazia():
    fonte = FonteMock(analises=[])
    assert fonte.listar(FiltrosAnalises()).itens == []
    assert fonte.resumir(FiltrosAnalises()).total == 0


def test_filtro_de_assunto_usa_a_mesma_regra_da_api():
    from src.comum.busca_textual import corresponde

    fonte = FonteMock()
    filtros = FiltrosAnalises(assunto="ATENDIMENTO")
    pagina = fonte.listar(filtros, tamanho=100)

    esperados = [a for a in ANALISES_DE_EXEMPLO if corresponde("ATENDIMENTO", a.texto_original)]
    assert len(esperados) == 2
    assert [a.id_origem for a in pagina.itens] == [a.id_origem for a in esperados]
    assert fonte.resumir(filtros).total == 2


def test_filtro_de_assunto_combinado_com_periodo_conta_sem_data_so_do_assunto():
    fonte = FonteMock()
    # "programa" aparece em dois textos de exemplo, os dois sem data.
    resumo = fonte.resumir(FiltrosAnalises(inicio=date(2026, 8, 1), assunto="programa"))

    assert resumo.total == 0
    assert resumo.sem_data_publicacao == 2
