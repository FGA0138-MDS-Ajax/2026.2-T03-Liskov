#!/usr/bin/env python3
"""Avaliação comparativa final no teste PC1 da Issue #103, somente inferência."""

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
ARQUIVO_AMOSTRA = RAIZ / "data/BPSAD/amostra_pc1.csv"
DIRETORIO_RELATORIOS = RAIZ / "docs/resultados_bpsad/issue103"

SHA256_ESPERADO = (
    "607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6"
)

MODELO_BASE = "pysentimiento/bertweet-pt-sentiment"
MODELO_C = str(
    Path.home()
    / "models/sentia/issue-103-bertweet-ft-v3-raiz-pesos"
    / "melhor_modelo"
)

MAX_LENGTH = 128
BATCH_SIZE = 16
TEMPERATURAS = {
    "Original": 2.081848,
    "C completo - 3 épocas": 0.951787,
}

CLASSES = {"negativo": 0, "neutro": 1, "positivo": 2}
NOMES_CLASSES = ["negativo", "neutro", "positivo"]
DISTRIBUICAO_ESPERADA = {
    "positivo": 1371,
    "negativo": 319,
    "neutro": 310,
}


def sha256_arquivo(caminho):
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def carregar_teste():
    if not ARQUIVO_AMOSTRA.is_file():
        raise FileNotFoundError(ARQUIVO_AMOSTRA)

    sha = sha256_arquivo(ARQUIVO_AMOSTRA)
    if sha != SHA256_ESPERADO:
        raise ValueError(f"SHA256 inesperado na amostra PC1: {sha}")

    df = pd.read_csv(
        ARQUIVO_AMOSTRA,
        usecols=["review_text", "rotulo", "divisao"],
        encoding="utf-8-sig",
        keep_default_na=False,
    )

    if len(df) != 10000:
        raise ValueError(f"Esperadas 10000 linhas; encontradas {len(df)}")

    if set(df["divisao"].unique()) != {"treino", "teste"}:
        raise ValueError("As divisões da amostra são inválidas")

    teste = df.loc[df["divisao"] == "teste"].copy()

    if len(teste) != 2000:
        raise ValueError(f"Esperados 2000 exemplos de teste; encontrados {len(teste)}")

    if not teste["review_text"].map(
        lambda texto: isinstance(texto, str) and bool(texto.strip())
    ).all():
        raise ValueError("Há textos vazios ou inválidos no teste")

    if not set(teste["rotulo"].unique()).issubset(CLASSES):
        raise ValueError("O teste contém rótulos desconhecidos")

    distribuicao = teste["rotulo"].value_counts().to_dict()
    if distribuicao != DISTRIBUICAO_ESPERADA:
        raise ValueError(
            f"Distribuição inesperada no teste: {distribuicao}"
        )

    textos = [
        preprocess_tweet(texto, lang="pt")
        for texto in teste["review_text"].tolist()
    ]

    if any(not texto for texto in textos):
        raise ValueError("Há textos vazios após o pré-processamento")

    alvos = np.asarray(
        [CLASSES[rotulo] for rotulo in teste["rotulo"].tolist()],
        dtype=np.int64,
    )

    return textos, alvos, sha, distribuicao


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


def calcular_metricas(nome, probabilidades, alvos):
    previstos = probabilidades.argmax(axis=1)

    precisao, recall, f1, suporte = precision_recall_fscore_support(
        alvos,
        previstos,
        labels=[0, 1, 2],
        zero_division=0,
    )

    matriz = confusion_matrix(alvos, previstos, labels=[0, 1, 2])

    return {
        "variante": nome,
        "accuracy": float(accuracy_score(alvos, previstos)),
        "f1_macro": float(f1_score(
            alvos,
            previstos,
            labels=[0, 1, 2],
            average="macro",
            zero_division=0,
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
        "distribuicao_previsoes": {
            NOMES_CLASSES[i]: int(np.sum(previstos == i))
            for i in range(3)
        },
    }


def inferir_modelo(nome, origem, tokenizer, textos, alvos, dispositivo):
    caminho = Path(origem).expanduser()

    if nome != "Original" and not caminho.is_dir():
        raise FileNotFoundError(f"Modelo não encontrado: {caminho}")

    print(f"\nCarregando modelo: {nome}")
    modelo = AutoModelForSequenceClassification.from_pretrained(
        origem,
        local_files_only=True,
    )

    if modelo.config.num_labels != 3:
        raise ValueError(f"{nome}: esperado modelo com três classes")

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

    lotes_logits = []

    with torch.inference_mode():
        for lote in loader:
            lote = {
                chave: valor.to(dispositivo)
                for chave, valor in lote.items()
            }
            saida = modelo(**lote)
            lotes_logits.append(saida.logits.cpu())

    logits = torch.cat(lotes_logits, dim=0).numpy()

    if logits.shape != (len(alvos), 3):
        raise ValueError(f"{nome}: formato inesperado dos logits: {logits.shape}")

    temperatura = TEMPERATURAS[nome]

    probabilidades_originais = torch.softmax(
        torch.tensor(logits), dim=-1
    ).numpy()

    probabilidades_calibradas = torch.softmax(
        torch.tensor(logits / temperatura), dim=-1
    ).numpy()

    metricas_originais = calcular_metricas(
        f"{nome} - sem calibração",
        probabilidades_originais,
        alvos,
    )
    metricas_calibradas = calcular_metricas(
        f"{nome} - temperatura {temperatura}",
        probabilidades_calibradas,
        alvos,
    )

    if not np.array_equal(
        probabilidades_originais.argmax(axis=1),
        probabilidades_calibradas.argmax(axis=1),
    ):
        raise AssertionError(
            "A temperatura alterou as classes previstas; revisar implementação"
        )

    del modelo, dataset, loader, lotes_logits, logits
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return metricas_originais, metricas_calibradas


def versao_pacote(nome):
    try:
        return version(nome)
    except PackageNotFoundError:
        return None


def main():
    print("=" * 72)
    print("AVALIAÇÃO FINAL PC1 - ISSUE #103")
    print("Somente inferência. Nenhum treinamento ou ajuste de parâmetros.")
    print("=" * 72)

    textos, alvos, sha, distribuicao = carregar_teste()

    print(f"\nTeste: {len(textos)} exemplos")
    print(f"SHA256 da amostra: {sha}")
    print(f"Distribuição real: {distribuicao}")

    dispositivo = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    print(f"Dispositivo: {dispositivo}")

    tokenizer = AutoTokenizer.from_pretrained(
        MODELO_BASE,
        local_files_only=True,
    )

    configuracoes = [
        ("Original", MODELO_BASE),
        ("C completo - 3 épocas", MODELO_C),
    ]

    resultados = []

    for nome, origem in configuracoes:
        sem_calibracao, calibrado = inferir_modelo(
            nome,
            origem,
            tokenizer,
            textos,
            alvos,
            dispositivo,
        )
        resultados.extend([sem_calibracao, calibrado])

    print("\n" + "=" * 100)
    print("RESUMO COMPARATIVO")
    print(
        f"{'Variante':<42} {'Accuracy':>10} {'F1 macro':>10} "
        f"{'F1 neutro':>10} {'F1 negativo':>12} {'ECE':>10}"
    )

    for resultado in resultados:
        classes = resultado["metricas_por_classe"]
        print(
            f"{resultado['variante']:<42} "
            f"{resultado['accuracy']:>10.4f} "
            f"{resultado['f1_macro']:>10.4f} "
            f"{classes['neutro']['f1']:>10.4f} "
            f"{classes['negativo']['f1']:>12.4f} "
            f"{resultado['ece_15_bins']:>10.4f}"
        )

    relatorio = {
        "experimento": "avaliacao_teste_pc1_issue103",
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "dados": {
            "arquivo": str(ARQUIVO_AMOSTRA.relative_to(RAIZ)),
            "sha256_amostra": sha,
            "particao": "teste",
            "quantidade": len(textos),
            "distribuicao_real": distribuicao,
            "ressalva_metodologica": (
                "A divisão de teste foi preservada fora do ajuste fino e da "
                "calibração desta experiência. O BERTweet original já havia "
                "sido avaliado historicamente nesta partição. A independência "
                "dos dados em relação ao pré-treinamento do modelo não foi "
                "comprovada. Portanto, os resultados não constituem uma "
                "estimativa comprovadamente independente de generalização."
            ),
        },
        "configuracao": {
            "modelos": [
                {"nome": nome, "origem": origem}
                for nome, origem in configuracoes
            ],
            "temperaturas_definidas_na_validacao_interna": TEMPERATURAS,
            "max_length": MAX_LENGTH,
            "batch_size": BATCH_SIZE,
            "classes": NOMES_CLASSES,
            "ece_bins": 15,
            "nenhum_ajuste_no_teste": True,
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
    destino = DIRETORIO_RELATORIOS / f"avaliacao_teste_pc1_{timestamp}.json"

    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")

    print(f"\nRelatório salvo em: {destino.relative_to(RAIZ)}")
    print("Avaliação concluída. Nenhum modelo ou dado de origem foi alterado.")


if __name__ == "__main__":
    main()
