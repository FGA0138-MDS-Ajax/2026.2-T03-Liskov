"""Testes da gravação de análises no MongoDB.

Os testes de validação rodam sem banco. Os que usam o MongoDB local são
pulados quando ele não está disponível (por exemplo, no CI do GitHub).
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from src.dados.database import ErroConexaoMongoDB, connect_to_mongodb
from src.dados.repositorio import (
    ErroAnaliseInvalida,
    criar_indices,
    obter_colecao,
    salvar_analise,
    salvar_analises,
    validar_analise,
)

URI_TESTE = "mongodb://localhost:27017"
BANCO_TESTE = "sentia_teste_repositorio"


def criar_documento(id_origem="teste_001", **mudancas):
    """Monta uma análise válida; mudancas troca ou acrescenta campos."""
    documento = {
        "id_origem": id_origem,
        "fonte": "teste",
        "texto_original": "Gostei muito do atendimento.",
        "sentimento": "positivo",
        "modelo": {"nome": "pysentimiento/bertweet-pt-sentiment"},
        "data_processamento": datetime(2026, 11, 10, 12, 0, tzinfo=UTC),
    }
    documento.update(mudancas)
    return documento


@pytest.fixture
def colecao():
    """Coleção num banco de teste separado, apagado antes e depois de cada teste."""
    try:
        client = connect_to_mongodb(URI_TESTE, timeout_ms=1000)
    except ErroConexaoMongoDB:
        pytest.skip("MongoDB local indisponível; ligue o Docker para rodar este teste.")
    client.drop_database(BANCO_TESTE)
    colecao_teste = obter_colecao(client, BANCO_TESTE)
    criar_indices(colecao_teste)
    yield colecao_teste
    client.drop_database(BANCO_TESTE)
    client.close()



def test_documento_valido_passa_na_validacao():
    validar_analise(criar_documento())


@pytest.mark.parametrize("campo", ["id_origem", "fonte", "texto_original"])
@pytest.mark.parametrize("valor", [None, "", "   ", 123])
def test_campo_de_texto_obrigatorio_ausente_ou_vazio_e_recusado(campo, valor):
    with pytest.raises(ErroAnaliseInvalida, match=campo):
        validar_analise(criar_documento(**{campo: valor}))


def test_sentimento_fora_da_lista_e_recusado():
    with pytest.raises(ErroAnaliseInvalida):
        validar_analise(criar_documento(sentimento="feliz"))


@pytest.mark.parametrize("modelo", [None, {}, {"nome": ""}, "bertweet"])
def test_modelo_sem_nome_e_recusado(modelo):
    with pytest.raises(ErroAnaliseInvalida, match="modelo"):
        validar_analise(criar_documento(modelo=modelo))


def test_sem_data_processamento_e_recusado():
    documento = criar_documento()
    del documento["data_processamento"]
    with pytest.raises(ErroAnaliseInvalida, match="data_processamento"):
        validar_analise(documento)


@pytest.mark.parametrize("campo", ["data_processamento", "data_publicacao"])
@pytest.mark.parametrize("valor", ["2026-11-10", datetime(2026, 11, 10), None])
def test_data_como_texto_sem_fuso_ou_nula_e_recusada(campo, valor):
    with pytest.raises(ErroAnaliseInvalida, match=campo):
        validar_analise(criar_documento(**{campo: valor}))


def test_documento_invalido_nao_chega_ao_banco():
    colecao_falsa = Mock()
    with pytest.raises(ErroAnaliseInvalida):
        salvar_analise(colecao_falsa, criar_documento(sentimento="feliz"))
    colecao_falsa.insert_one.assert_not_called()


def test_lote_vazio_nao_chama_o_banco():
    colecao_falsa = Mock()
    assert salvar_analises(colecao_falsa, []) == {"inseridos": 0, "duplicados": 0}
    colecao_falsa.insert_many.assert_not_called()



def test_cria_os_quatro_indices_do_esquema(colecao):
    indices = {indice["name"]: indice for indice in colecao.list_indexes()}
    assert set(indices) == {
        "_id_",
        "uq_fonte_id_origem",
        "idx_sentimento_data_publicacao",
        "idx_data_publicacao",
        "idx_data_processamento",
    }
    assert indices["uq_fonte_id_origem"]["unique"] is True


def test_criar_indices_de_novo_nao_da_erro(colecao):
    criar_indices(colecao)


def test_salvar_analise_grava_e_nao_duplica(colecao):
    documento = criar_documento()
    assert salvar_analise(colecao, documento) is True
    assert salvar_analise(colecao, documento) is False
    assert colecao.count_documents({}) == 1


def test_mesmo_id_em_fontes_diferentes_nao_e_duplicata(colecao):
    assert salvar_analise(colecao, criar_documento(fonte="bpsad")) is True
    assert salvar_analise(colecao, criar_documento(fonte="X")) is True
    assert colecao.count_documents({}) == 2


def test_salvar_analise_nao_altera_o_dicionario_original(colecao):
    documento = criar_documento()
    salvar_analise(colecao, documento)
    assert "_id" not in documento


def test_datas_sao_gravadas_como_data_e_publicacao_ausente_e_omitida(colecao):
    salvar_analise(colecao, criar_documento())
    gravado = colecao.find_one({"id_origem": "teste_001"})
    assert isinstance(gravado["data_processamento"], datetime)
    assert "data_publicacao" not in gravado


def test_salvar_analises_conta_inseridos_e_duplicados(colecao):
    assert salvar_analises(colecao, [criar_documento("a"), criar_documento("b")]) == {
        "inseridos": 2,
        "duplicados": 0,
    }
    lote = [criar_documento("b"), criar_documento("c"), criar_documento("c"), criar_documento("d")]
    assert salvar_analises(colecao, lote) == {"inseridos": 2, "duplicados": 2}
    assert colecao.count_documents({}) == 4


def test_lote_com_um_invalido_nao_grava_nada(colecao):
    lote = [criar_documento("a"), criar_documento("b", sentimento="feliz")]
    with pytest.raises(ErroAnaliseInvalida):
        salvar_analises(colecao, lote)
    assert colecao.count_documents({}) == 0
