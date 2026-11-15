"""Demo offline. Execute da raiz: uv run python -m scripts.demonstrar_pipeline."""

import json
from pathlib import Path
from types import SimpleNamespace

from bson import BSON

from src.processamento.aquisicao import importar_dataset_csv
from src.processamento.classificacao.bertweet import ClassificadorBertweet
from src.processamento.pipeline import PipelineClassificacao


class AnalisadorSimulado:
    """Saída constante para demonstrar contrato; não mede qualidade de ML."""

    def predict(self, textos):
        return [
            SimpleNamespace(output="NEU", probas={"POS": 0.1, "NEG": 0.1, "NEU": 0.8})
            for _ in textos
        ]


def main():
    caminho = Path(__file__).resolve().parents[1] / "tests/fixtures/dataset_valido.csv"
    registros = importar_dataset_csv(caminho)
    pipeline = PipelineClassificacao(
        classificador=ClassificadorBertweet(analisador=AnalisadorSimulado()),
        versao_modelo="SIMULADO-PC1",
    )
    documentos = pipeline.processar_registros(registros)
    for entrada, documento in zip(registros, documentos, strict=True):
        assert entrada["texto_original"] == documento["texto_original"]
        assert entrada["id_origem"] == documento["id_origem"]
        BSON.encode(documento)
    print("ANALISADOR SIMULADO. Sem inferência real ou gravação MongoDB.")
    print(json.dumps(documentos, ensure_ascii=False, indent=2, default=str))
    print(f"{len(documentos)} registros importados, classificados por mock e serializados em BSON.")


if __name__ == "__main__":
    main()
