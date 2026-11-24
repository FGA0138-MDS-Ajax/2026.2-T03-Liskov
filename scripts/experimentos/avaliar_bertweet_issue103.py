#!/usr/bin/env python3
"""Avaliação somente de inferência dos modelos da issue #103."""

import gc
import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
)
from pysentimiento.preprocessing import preprocess_tweet


RAIZ = Path(__file__).resolve().parents[2]
DIRETORIO_RELATORIOS = RAIZ / "docs/resultados_bpsad/issue103"
ARQUIVO_VALIDACAO = RAIZ / "data/BPSAD/calibracao_pc1/validacao.csv"
SHA256_ESPERADO = "4dc9c1a1ad5a6232eeaf1c51b7fecb36c0dbe65fdb287f687f9f4cad8c277881"
MODELO_BASE = "pysentimiento/bertweet-pt-sentiment"
MAX_LENGTH = 128
BATCH_SIZE = 16
CLASSES = {"negativo": 0, "neutro": 1, "positivo": 2}
NOMES_CLASSES = ["negativo", "neutro", "positivo"]

MODELO_C_COMPLETO = str(
    Path.home()
    / "models/sentia/issue-103-bertweet-ft-v3-raiz-pesos"
    / "melhor_modelo"
)

MODELOS = [
    ("Original", MODELO_BASE),
    ("C completo - 3 épocas", MODELO_C_COMPLETO),
]


def sha256_arquivo(caminho):
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def carregar_validacao():
    if not ARQUIVO_VALIDACAO.is_file():
        raise FileNotFoundError(ARQUIVO_VALIDACAO)

    sha = sha256_arquivo(ARQUIVO_VALIDACAO)
    if sha != SHA256_ESPERADO:
        raise ValueError(
            f"SHA256 inesperado na validação: {sha}"
        )

    df = pd.read_csv(ARQUIVO_VALIDACAO)

    if len(df) != 1600:
        raise ValueError(f"Esperados 1600 exemplos; encontrados {len(df)}")

    if not {"review_text", "rotulo"}.issubset(df.columns):
        raise ValueError("Colunas review_text e rotulo são obrigatórias")

    if df[["review_text", "rotulo"]].isna().any().any():
        raise ValueError("Há valores ausentes na validação")

    if not set(df["rotulo"].unique()).issubset(CLASSES):
        raise ValueError("A validação contém rótulos desconhecidos")

    textos = [
        preprocess_tweet(texto, lang="pt")
        for texto in df["review_text"].tolist()
    ]

    if any(not texto for texto in textos):
        raise ValueError("Há textos vazios após o pré-processamento")

    alvos = np.asarray(
        [CLASSES[rotulo] for rotulo in df["rotulo"].tolist()],
        dtype=np.int64,
    )

    return textos, alvos, sha


class DatasetInferencia(Dataset):
    def __init__(self, textos, tokenizer):
        self.tokens = tokenizer(
            textos,
            truncation=True,
            max_length=MAX_LENGTH,
            padding=False,
        )

    def __len__(self):
        return len(self.tokens["input_ids"])

    def __getitem__(self, indice):
        return {
            chave: valores[indice]
            for chave, valores in self.tokens.items()
        }


def calcular_ece(probabilidades, previstos, alvos, bins=15):
    confiancas = probabilidades.max(axis=1)
    corretos = (previstos == alvos).astype(np.float64)
    limites = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0

    for indice in range(bins):
        if indice == bins - 1:
            mascara = (
                (confiancas >= limites[indice])
                & (confiancas <= limites[indice + 1])
            )
        else:
            mascara = (
                (confiancas >= limites[indice])
                & (confiancas < limites[indice + 1])
            )

        if mascara.any():
            acuracia_bin = corretos[mascara].mean()
            confianca_bin = confiancas[mascara].mean()
            ece += mascara.mean() * abs(acuracia_bin - confianca_bin)

    return float(ece)


def avaliar_modelo(nome, caminho, tokenizer, textos, alvos, dispositivo):
    caminho_local = Path(caminho).expanduser()

    if nome != "Original" and not caminho_local.is_dir():
        raise FileNotFoundError(
            f"Diretório do modelo não encontrado: {caminho_local}"
        )

    origem = MODELO_BASE if nome == "Original" else str(caminho_local)

    print(f"\n{'=' * 72}")
    print(f"AVALIANDO: {nome}")
    print(f"Origem: {origem}")
    print(f"Dispositivo: {dispositivo}")
    print("Carregando modelo...")

    modelo = AutoModelForSequenceClassification.from_pretrained(
        origem,
        local_files_only=True,
    )

    if modelo.config.num_labels != 3:
        raise ValueError(f"{nome}: modelo não possui três classes")

    modelo.to(dispositivo)
    modelo.eval()

    dataset = DatasetInferencia(textos, tokenizer)
    collator = DataCollatorWithPadding(tokenizer=tokenizer)
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=collator,
        num_workers=0,
    )

    lotes_probabilidades = []

    with torch.inference_mode():
        for lote in loader:
            lote = {
                chave: valor.to(dispositivo)
                for chave, valor in lote.items()
            }
            saida = modelo(**lote)
            probabilidades = torch.softmax(saida.logits, dim=-1)
            lotes_probabilidades.append(
                probabilidades.cpu().numpy()
            )

    probabilidades = np.concatenate(lotes_probabilidades, axis=0)
    previstos = probabilidades.argmax(axis=1)

    precisao, recall, f1, suporte = precision_recall_fscore_support(
        alvos,
        previstos,
        labels=[0, 1, 2],
        zero_division=0,
    )

    matriz = confusion_matrix(alvos, previstos, labels=[0, 1, 2])

    mascara_neutros = alvos == 1
    neutros_como_positivos = int(
        np.sum((alvos == 1) & (previstos == 2))
    )
    total_neutros = int(mascara_neutros.sum())

    distribuicao = {
        NOMES_CLASSES[i]: {
            "quantidade": int(np.sum(previstos == i)),
            "percentual": float(np.mean(previstos == i) * 100),
        }
        for i in range(3)
    }

    resultado = {
        "modelo": nome,
        "accuracy": float(accuracy_score(alvos, previstos)),
        "f1_macro": float(f1_score(
            alvos, previstos, labels=[0, 1, 2],
            average="macro", zero_division=0
        )),
        "log_loss": float(log_loss(
            alvos, probabilidades, labels=[0, 1, 2]
        )),
        "brier_multiclasse": float(np.mean(
            np.sum(
                (probabilidades - np.eye(3)[alvos]) ** 2,
                axis=1,
            )
        )),
        "ece_15_bins": calcular_ece(
            probabilidades, previstos, alvos
        ),
        "matriz_confusao": matriz.tolist(),
        "metricas_por_classe": {
            NOMES_CLASSES[i]: {
                "precision": float(precisao[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "suporte": int(suporte[i]),
            }
            for i in range(3)
        },
        "distribuicao_previsoes": distribuicao,
        "neutros_previstos_como_positivos": {
            "quantidade": neutros_como_positivos,
            "total_neutros": total_neutros,
            "taxa_percentual": (
                float(neutros_como_positivos / total_neutros * 100)
                if total_neutros else 0.0
            ),
        },
    }

    print(json.dumps(resultado, ensure_ascii=False, indent=2))

    del modelo, dataset, loader, lotes_probabilidades
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return resultado


def main():
    print("AVALIAÇÃO DA ISSUE #103 - SOMENTE INFERÊNCIA")
    print("Nenhum treinamento será realizado.")

    textos, alvos, sha = carregar_validacao()

    print(f"\nValidação: {len(textos)} exemplos")
    print(f"SHA256: {sha}")
    print("Distribuição real:")
    for nome, indice in CLASSES.items():
        print(f"  {nome}: {int(np.sum(alvos == indice))}")

    dispositivo = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    print(f"\nDispositivo selecionado: {dispositivo}")

    tokenizer = AutoTokenizer.from_pretrained(
        MODELO_BASE,
        local_files_only=True,
    )

    resultados = []
    for nome, caminho in MODELOS:
        resultado = avaliar_modelo(
            nome,
            caminho,
            tokenizer,
            textos,
            alvos,
            dispositivo,
        )
        resultados.append(resultado)

    print("\n" + "=" * 72)
    print("RESUMO COMPARATIVO")
    print(
        f"{'Modelo':<25} {'Accuracy':>10} {'F1 macro':>10} "
        f"{'F1 neutro':>10} {'F1 negativo':>12} {'ECE':>10}"
    )

    for resultado in resultados:
        classes = resultado["metricas_por_classe"]
        print(
            f"{resultado['modelo']:<25} "
            f"{resultado['accuracy']:>10.4f} "
            f"{resultado['f1_macro']:>10.4f} "
            f"{classes['neutro']['f1']:>10.4f} "
            f"{classes['negativo']['f1']:>12.4f} "
            f"{resultado['ece_15_bins']:>10.4f}"
        )

    def versao_pacote(nome):
        try:
            return version(nome)
        except PackageNotFoundError:
            return None

    relatorio = {
        "experimento": "avaliacao_bertweet_issue103",
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "dados": {
            "arquivo": str(ARQUIVO_VALIDACAO.relative_to(RAIZ)),
            "sha256": sha,
            "quantidade": len(textos),
            "distribuicao_real": {
                nome: int(np.sum(alvos == indice))
                for nome, indice in CLASSES.items()
            },
            "ressalva_metodologica": (
                "Os rótulos do BPSAD são derivados de avaliações por estrelas "
                "e não necessariamente representam o sentimento textual."
            ),
        },
        "configuracao": {
            "modelos": [
                {"nome": nome, "origem": caminho}
                for nome, caminho in MODELOS
            ],
            "max_length": MAX_LENGTH,
            "batch_size": BATCH_SIZE,
            "classes": NOMES_CLASSES,
            "ece_bins": 15,
        },
        "ambiente": {
            "python": platform.python_version(),
            "plataforma": platform.platform(),
            "torch": str(torch.__version__),
            "numpy": versao_pacote("numpy"),
            "pandas": versao_pacote("pandas"),
            "scikit_learn": versao_pacote("scikit-learn"),
            "transformers": versao_pacote("transformers"),
            "pysentimiento": versao_pacote("pysentimiento"),
            "dispositivo": str(dispositivo),
        },
        "resultados": resultados,
    }

    DIRETORIO_RELATORIOS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destino = DIRETORIO_RELATORIOS / f"avaliacao_{timestamp}.json"

    with destino.open("x", encoding="utf-8") as saida:
        json.dump(relatorio, saida, ensure_ascii=False, indent=2)
        saida.write("\n")

    print(f"\nRelatório JSON salvo em: {destino.relative_to(RAIZ)}")
    print("\nAvaliação concluída. Nenhum arquivo de modelo foi alterado.")


if __name__ == "__main__":
    main()
