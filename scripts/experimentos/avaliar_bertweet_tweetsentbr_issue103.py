#!/usr/bin/env python3
"""Compara BERTweet original e ajustado no TweetSentBR, sem treinamento."""

import gc
import hashlib
import json
import platform
import runpy
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
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
)
from pysentimiento.preprocessing import preprocess_tweet


RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_DADOS = RAIZ / "Datasets/tweetsent.csv"
DIRETORIO_RELATORIOS = RAIZ / "docs/resultados_bpsad/issue103"

SHA256_ESPERADO = (
    "8b7be5d0a6bb982c99bf0613ac71f9f8eed49849586a5019b2db2094a6136060"
)

# Temperatura estimada exclusivamente na calibração interna do BPSAD.
TEMPERATURA_C = 0.951787

# Reutiliza a implementação já validada na Issue #103.
AVALIADOR = RAIZ / "scripts/experimentos/avaliar_bertweet_issue103.py"
ctx = runpy.run_path(str(AVALIADOR), run_name="avaliador_issue103_tweetsent")

DatasetInferencia = ctx["DatasetInferencia"]
calcular_ece = ctx["calcular_ece"]
MODELO_BASE = ctx["MODELO_BASE"]
MODELO_C_COMPLETO = ctx["MODELO_C_COMPLETO"]
MAX_LENGTH = ctx["MAX_LENGTH"]
BATCH_SIZE = ctx["BATCH_SIZE"]
CLASSES = ctx["CLASSES"]
NOMES_CLASSES = ctx["NOMES_CLASSES"]


def sha256_arquivo(caminho):
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def carregar_tweetsentbr():
    if not ARQUIVO_DADOS.is_file():
        raise FileNotFoundError(ARQUIVO_DADOS)

    sha = sha256_arquivo(ARQUIVO_DADOS)
    if sha != SHA256_ESPERADO:
        raise ValueError(
            f"SHA256 inesperado no TweetSentBR: {sha}. "
            "A avaliação foi interrompida."
        )

    df = pd.read_csv(ARQUIVO_DADOS, encoding="utf-8-sig")

    if not {"texto", "rotulo"}.issubset(df.columns):
        raise ValueError("O CSV precisa conter texto e rotulo.")

    if len(df) != 8530:
        raise ValueError(
            f"Esperados 8530 registros; encontrados {len(df)}."
        )

    if df[["texto", "rotulo"]].isna().any().any():
        raise ValueError("Há textos ou rótulos ausentes.")

    if not set(df["rotulo"].unique()).issubset(CLASSES):
        raise ValueError("Há rótulos desconhecidos.")

    textos = [
        preprocess_tweet(str(texto), lang="pt")
        for texto in df["texto"].tolist()
    ]

    if any(not texto for texto in textos):
        raise ValueError("Há textos vazios após o pré-processamento.")

    alvos = np.asarray(
        [CLASSES[rotulo] for rotulo in df["rotulo"].tolist()],
        dtype=np.int64,
    )

    return textos, alvos, sha


def inferir_logits(nome, origem, tokenizer, textos, dispositivo):
    print(f"\nCarregando modelo: {nome}")
    modelo = AutoModelForSequenceClassification.from_pretrained(
        origem,
        local_files_only=True,
    )

    if modelo.config.num_labels != 3:
        raise ValueError(f"{nome}: esperado modelo com três classes.")

    modelo.to(dispositivo)
    modelo.eval()

    dataset = DatasetInferencia(textos, tokenizer)
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=DataCollatorWithPadding(tokenizer=tokenizer),
        num_workers=0,
    )

    partes = []
    with torch.inference_mode():
        for lote in loader:
            lote = {
                chave: valor.to(dispositivo)
                for chave, valor in lote.items()
            }
            saida = modelo(**lote)
            partes.append(saida.logits.float().cpu().numpy())

    logits = np.concatenate(partes, axis=0)

    del modelo, dataset, loader, partes
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return logits


def calcular_brier(probabilidades, alvos):
    one_hot = np.eye(3, dtype=np.float64)[alvos]
    return float(np.mean(np.sum((probabilidades - one_hot) ** 2, axis=1)))


def avaliar(nome, probabilidades, alvos):
    previstos = probabilidades.argmax(axis=1)

    precisao, recall, f1, suporte = precision_recall_fscore_support(
        alvos,
        previstos,
        labels=[0, 1, 2],
        zero_division=0,
    )

    matriz = confusion_matrix(alvos, previstos, labels=[0, 1, 2])

    por_classe = {
        NOMES_CLASSES[i]: {
            "precision": float(precisao[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "suporte": int(suporte[i]),
        }
        for i in range(3)
    }

    distribuicao = {
        NOMES_CLASSES[i]: {
            "quantidade": int(np.sum(previstos == i)),
            "percentual": float(np.mean(previstos == i) * 100),
        }
        for i in range(3)
    }

    return {
        "modelo": nome,
        "accuracy": float(accuracy_score(alvos, previstos)),
        "f1_macro": float(f1_score(
            alvos, previstos, labels=[0, 1, 2],
            average="macro", zero_division=0
        )),
        "metricas_por_classe": por_classe,
        "log_loss": float(log_loss(alvos, probabilidades, labels=[0, 1, 2])),
        "brier": calcular_brier(probabilidades, alvos),
        "ece_15_bins": calcular_ece(probabilidades, previstos, alvos),
        "matriz_confusao": matriz.tolist(),
        "distribuicao_prevista": distribuicao,
        "neutros_como_positivos": int(
            np.sum((alvos == 1) & (previstos == 2))
        ),
    }


def versao_pacote(nome):
    try:
        return version(nome)
    except PackageNotFoundError:
        return None


def main():
    print("ISSUE #103 - AVALIAÇÃO EXPLORATÓRIA NO TWEETSENTBR")
    print("Somente inferência: nenhum treinamento ou ajuste será realizado.")

    textos, alvos, sha = carregar_tweetsentbr()

    print(f"\nRegistros: {len(textos)}")
    print(f"SHA256: {sha}")
    print("Distribuição real:")
    for nome, indice in CLASSES.items():
        print(f"  {nome}: {int(np.sum(alvos == indice))}")

    dispositivo = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    print(f"\nDispositivo: {dispositivo}")

    tokenizer = AutoTokenizer.from_pretrained(
        MODELO_BASE,
        local_files_only=True,
    )

    modelos = [
        ("Original - sem calibração", MODELO_BASE, 1.0),
        ("C completo - sem calibração", MODELO_C_COMPLETO, 1.0),
        ("C completo - temperatura fixa", MODELO_C_COMPLETO, TEMPERATURA_C),
    ]

    resultados = []

    for nome, origem, temperatura in modelos:
        logits = inferir_logits(
            nome, origem, tokenizer, textos, dispositivo
        )

        probabilidades = torch.softmax(
            torch.tensor(logits / temperatura, dtype=torch.float32),
            dim=-1,
        ).numpy()

        resultado = avaliar(nome, probabilidades, alvos)
        resultado["temperatura_aplicada"] = temperatura
        resultados.append(resultado)

        print("\n" + "=" * 72)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))

        del logits, probabilidades
        gc.collect()

    print("\n=== RESUMO COMPARATIVO ===")
    print(
        f"{'Modelo':<34} {'Accuracy':>10} {'F1 macro':>10} "
        f"{'F1 neutro':>10} {'ECE':>10}"
    )
    for resultado in resultados:
        f1_neutro = resultado["metricas_por_classe"]["neutro"]["f1"]
        print(
            f"{resultado['modelo']:<34} "
            f"{resultado['accuracy']:>10.4f} "
            f"{resultado['f1_macro']:>10.4f} "
            f"{f1_neutro:>10.4f} "
            f"{resultado['ece_15_bins']:>10.4f}"
        )

    DIRETORIO_RELATORIOS.mkdir(parents=True, exist_ok=True)
    caminho_saida = (
        DIRETORIO_RELATORIOS
        / "tweetsentbr_comparacao_issue103.json"
    )

    relatorio = {
        "experimento": "tweetsentbr_comparacao_issue103",
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "dados": {
            "arquivo": str(ARQUIVO_DADOS.relative_to(RAIZ)),
            "sha256": sha,
            "quantidade": len(textos),
            "distribuicao_real": {
                nome: int(np.sum(alvos == indice))
                for nome, indice in CLASSES.items()
            },
            "ressalva": (
                "Avaliação exploratória. O modelo original foi treinado "
                "com TweetSentBR; portanto, os resultados não constituem "
                "evidência independente de generalização."
            ),
        },
        "configuracao": {
            "max_length": MAX_LENGTH,
            "batch_size": BATCH_SIZE,
            "classes": NOMES_CLASSES,
            "preprocessamento": "preprocess_tweet(lang='pt')",
            "temperatura_c": TEMPERATURA_C,
            "temperatura_estimativa": (
                "Estimativa obtida exclusivamente na calibração interna "
                "do BPSAD; não reajustada no TweetSentBR."
            ),
            "modelos": [
                {
                    "nome": nome,
                    "origem": origem,
                    "temperatura": temperatura,
                }
                for nome, origem, temperatura in modelos
            ],
        },
        "ambiente": {
            "python": platform.python_version(),
            "plataforma": platform.platform(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "transformers": versao_pacote("transformers"),
            "pysentimiento": versao_pacote("pysentimiento"),
            "scikit_learn": versao_pacote("scikit-learn"),
            "dispositivo": str(dispositivo),
        },
        "resultados": resultados,
    }

    caminho_saida.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nRelatório salvo em: {caminho_saida}")


if __name__ == "__main__":
    main()
