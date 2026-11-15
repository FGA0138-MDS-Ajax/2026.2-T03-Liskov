"""Análise de datasets de 100 em 100 linhas (scripts/analisar_em_lotes.py)."""

import csv

import pytest

from scripts.analisar_em_lotes import analisar_em_lotes, lotes
from src.processamento.pipeline import PipelineClassificacao


class ClassificadorFalso:
    nome_modelo = "falso"

    def __init__(self):
        self.chamadas = []

    def prever_com_probabilidades(self, textos):
        self.chamadas.append(len(textos))
        return [
            {
                "sentimento": "POS",
                "probabilidades": {"positivo": 0.8, "neutro": 0.1, "negativo": 0.1},
            }
            for _ in textos
        ]


def _registros(total):
    return (
        {"id_origem": str(i), "fonte": "teste", "texto_original": f"texto {i}"}
        for i in range(total)
    )


def test_lotes_agrupa_sem_perder_o_resto():
    assert [len(lote) for lote in lotes(range(250), 100)] == [100, 100, 50]


def test_analisa_de_100_em_100_e_grava_cada_lote(tmp_path):
    classificador = ClassificadorFalso()
    pipeline = PipelineClassificacao(classificador=classificador, tamanho_lote=100)
    saida = tmp_path / "resultado.csv"
    concluidos = []

    resumo = analisar_em_lotes(
        _registros(250),
        pipeline,
        saida,
        ao_concluir_lote=lambda numero, total, _: concluidos.append((numero, total)),
    )

    assert classificador.chamadas == [100, 100, 50]
    assert concluidos == [(1, 100), (2, 200), (3, 250)]
    assert resumo.por_sentimento == {"positivo": 250}
    with saida.open(encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert len(linhas) == 250
    assert linhas[0]["sentimento"] == "positivo"
    assert linhas[0]["prob_positivo"] == "0.8000"


def test_limite_para_de_ler_o_arquivo(tmp_path):
    lidos = []

    def registros():
        for registro in _registros(1000):
            lidos.append(registro)
            yield registro

    pipeline = PipelineClassificacao(
        classificador=ClassificadorFalso(), tamanho_lote=100
    )
    resumo = analisar_em_lotes(registros(), pipeline, tmp_path / "r.csv", limite=150)

    assert resumo.analisados == 150
    assert len(lidos) <= 200


@pytest.mark.parametrize("argumentos", [{"tamanho_lote": 0}, {"limite": 0}])
def test_rejeita_valores_invalidos(tmp_path, argumentos):
    pipeline = PipelineClassificacao(classificador=ClassificadorFalso())
    with pytest.raises(ValueError):
        analisar_em_lotes(_registros(1), pipeline, tmp_path / "r.csv", **argumentos)
