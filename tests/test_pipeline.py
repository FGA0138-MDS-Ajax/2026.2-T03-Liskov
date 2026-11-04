import csv
from datetime import datetime, timezone

import pytest

from src.processamento.pipeline import ErroPipeline, PipelineClassificacao


class ClassificadorFalso:
    nome_modelo = "modelo-teste"

    def __init__(self):
        self.lotes = []

    def prever_com_probabilidades(self, textos):
        self.lotes.append(list(textos))
        return [
            {
                "sentimento": "POS",
                "probabilidades": {
                    "positivo": 0.8,
                    "negativo": 0.1,
                    "neutro": 0.1,
                },
            }
            for _ in textos
        ]


def registro(texto="Texto de teste", **extras):
    base = {
        "id_origem": "tweet-1",
        "fonte": "TweetSentBR",
        "texto_original": texto,
        "rotulo_original": "positivo",
        "rotulo_padronizado": "POS",
        "data_publicacao": None,
        "metadados": {"idioma": "pt"},
    }
    base.update(extras)
    return base


def test_preserva_dados_e_associa_previsao():
    classificador = ClassificadorFalso()
    pipeline = PipelineClassificacao(classificador=classificador)

    resultado = pipeline.processar_registros([registro()])

    assert len(resultado) == 1
    documento = resultado[0]
    assert documento["id_origem"] == "tweet-1"
    assert documento["fonte"] == "TweetSentBR"
    assert documento["texto_original"] == "Texto de teste"
    assert documento["rotulo_original"] == "positivo"
    assert documento["rotulo_padronizado"] == "positivo"
    assert documento["sentimento"] == "positivo"
    assert documento["modelo"]["nome"] == "modelo-teste"
    assert documento["metadados"] == {"idioma": "pt"}
    assert documento["data_processamento"].tzinfo is not None


def test_processa_em_lotes_preservando_ordem():
    classificador = ClassificadorFalso()
    pipeline = PipelineClassificacao(
        classificador=classificador,
        tamanho_lote=2,
    )

    registros = [
        registro(texto="primeiro", id_origem="1"),
        registro(texto="segundo", id_origem="2"),
        registro(texto="terceiro", id_origem="3"),
    ]

    resultado = pipeline.processar_registros(registros)

    assert [item["id_origem"] for item in resultado] == ["1", "2", "3"]
    assert classificador.lotes == [["primeiro", "segundo"], ["terceiro"]]


def test_omite_campos_opcionais_ausentes():
    pipeline = PipelineClassificacao(classificador=ClassificadorFalso())

    resultado = pipeline.processar_registros([
        registro(
            rotulo_original=None,
            rotulo_padronizado=None,
            data_publicacao=None,
            metadados=None,
        )
    ])

    documento = resultado[0]
    assert "rotulo_original" not in documento
    assert "rotulo_padronizado" not in documento
    assert "data_publicacao" not in documento
    assert "metadados" not in documento


def test_converte_data_publicacao_para_utc():
    pipeline = PipelineClassificacao(classificador=ClassificadorFalso())
    data = "2026-11-03T12:00:00-03:00"

    resultado = pipeline.processar_registros([
        registro(data_publicacao=data)
    ])

    assert resultado[0]["data_publicacao"] == datetime(
        2026, 11, 3, 15, 0, tzinfo=timezone.utc
    )


def test_rejeita_data_sem_fuso_horario():
    pipeline = PipelineClassificacao(classificador=ClassificadorFalso())

    with pytest.raises(ErroPipeline, match="fuso horário"):
        pipeline.processar_registros([
            registro(data_publicacao="2026-11-03T12:00:00")
        ])


def test_rejeita_lote_com_quantidade_incorreta():
    classificador = ClassificadorFalso()

    def previsao_incompleta(textos):
        return []

    classificador.prever_com_probabilidades = previsao_incompleta
    pipeline = PipelineClassificacao(classificador=classificador)

    with pytest.raises(ErroPipeline, match="quantidade de previsões"):
        pipeline.processar_registros([registro()])


def test_rejeita_registros_vazios():
    pipeline = PipelineClassificacao(classificador=ClassificadorFalso())

    with pytest.raises(ErroPipeline, match="Nenhum registro"):
        pipeline.processar_registros([])


def test_rejeita_texto_vazio():
    pipeline = PipelineClassificacao(classificador=ClassificadorFalso())

    with pytest.raises(ErroPipeline, match="texto_original"):
        pipeline.processar_registros([registro(texto="   ")])


def test_inclui_versao_quando_informada():
    pipeline = PipelineClassificacao(
        classificador=ClassificadorFalso(),
        versao_modelo="commit-abc123",
    )

    resultado = pipeline.processar_registros([registro()])

    assert resultado[0]["modelo"]["versao"] == "commit-abc123"


def test_rejeita_metadados_invalidos_antes_da_inferencia():
    classificador = ClassificadorFalso()
    pipeline = PipelineClassificacao(classificador=classificador)

    with pytest.raises(ErroPipeline, match="metadados"):
        pipeline.processar_registros([registro(metadados="invalido")])

    assert classificador.lotes == []


@pytest.mark.parametrize(
    "probabilidades",
    [
        {"positivo": 1.1, "negativo": 0.0, "neutro": 0.0},
        {"positivo": float("nan"), "negativo": 0.0, "neutro": 1.0},
        {"positivo": 0.8, "negativo": 0.1, "neutro": 0.2},
        {"positivo": 0.8, "negativo": 0.2},
        {"positivo": True, "negativo": 0.0, "neutro": 0.0},
        {"positivo": 0.8, "negativo": 0.1, "neutro": 0.1, "extra": 0.0},
    ],
)
def test_rejeita_probabilidades_invalidas(probabilidades):
    classificador = ClassificadorFalso()

    def previsao_invalida(textos):
        return [
            {
                "sentimento": "POS",
                "probabilidades": probabilidades,
            }
            for _ in textos
        ]

    classificador.prever_com_probabilidades = previsao_invalida
    pipeline = PipelineClassificacao(classificador=classificador)

    with pytest.raises(ErroPipeline, match="probabilidades|probabilidade"):
        pipeline.processar_registros([registro()])


def test_aceita_probabilidades_validas():
    pipeline = PipelineClassificacao(classificador=ClassificadorFalso())
    resultado = pipeline.processar_registros([registro()])

    assert resultado[0]["probabilidades"] == {
        "positivo": 0.8,
        "negativo": 0.1,
        "neutro": 0.1,
    }

def test_processa_csv_com_rotulos_metadados_e_registros_nao_rotulados(tmp_path):
    caminho = tmp_path / "entrada.csv"
    colunas = [
        "id_origem",
        "texto_original",
        "fonte",
        "rotulo_original",
        "data_publicacao",
        "idioma",
    ]

    linhas = [
        {
            "id_origem": "tweet-101",
            "texto_original": "Experiencia muito boa",
            "fonte": "TweetSentBR",
            "rotulo_original": "positivo",
            "data_publicacao": "2026-11-03T12:00:00-03:00",
            "idioma": "pt",
        },
        {
            "id_origem": "",
            "texto_original": "Servico dentro do esperado",
            "fonte": "TweetSentBR",
            "rotulo_original": "",
            "data_publicacao": "",
            "idioma": "pt",
        },
    ]

    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)

    classificador = ClassificadorFalso()
    pipeline = PipelineClassificacao(
        classificador=classificador,
        tamanho_lote=2,
    )

    resultado = pipeline.processar_csv(str(caminho))

    assert len(resultado) == 2
    assert [item["texto_original"] for item in resultado] == [
        "Experiencia muito boa",
        "Servico dentro do esperado",
    ]
    assert [item["fonte"] for item in resultado] == [
        "TweetSentBR",
        "TweetSentBR",
    ]

    assert resultado[0]["id_origem"] == "tweet-101"
    assert resultado[0]["rotulo_original"] == "positivo"
    assert resultado[0]["rotulo_padronizado"] == "positivo"
    assert resultado[0]["data_publicacao"] == datetime(
        2026, 11, 3, 15, 0, tzinfo=timezone.utc
    )

    assert resultado[1]["id_origem"].startswith("TweetSentBR_000002_")
    assert "rotulo_original" not in resultado[1]
    assert "rotulo_padronizado" not in resultado[1]
    assert "data_publicacao" not in resultado[1]

    assert resultado[0]["metadados"] == {"idioma": "pt"}
    assert resultado[1]["metadados"] == {"idioma": "pt"}
    assert classificador.lotes == [[
        "Experiencia muito boa",
        "Servico dentro do esperado",
    ]]
