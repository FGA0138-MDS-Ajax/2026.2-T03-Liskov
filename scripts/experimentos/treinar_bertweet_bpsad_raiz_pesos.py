from __future__ import annotations

import argparse
import hashlib
import math
import json
import platform
import shutil
from collections import Counter
from pathlib import Path
from importlib.metadata import version

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed,
)
from pysentimiento.preprocessing import preprocess_tweet


RAIZ = Path(__file__).resolve().parents[2]
CONFIG_PADRAO = (
    RAIZ / "scripts/experimentos/configs/issue103_bertweet_bpsad.json"
)


def sha256_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def carregar_config(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def validar_entrada(
    caminho: Path,
    sha_esperado: str,
    quantidade_esperada: int,
    classes: dict[str, int],
) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    sha_real = sha256_arquivo(caminho)
    if sha_real != sha_esperado:
        raise ValueError(
            f"SHA256 divergente em {caminho.name}: "
            f"esperado={sha_esperado}, obtido={sha_real}"
        )

    df = pd.read_csv(caminho)

    colunas = {"review_text", "rotulo"}
    if not colunas.issubset(df.columns):
        raise ValueError(
            f"{caminho.name} precisa conter as colunas {sorted(colunas)}"
        )

    if len(df) != quantidade_esperada:
        raise ValueError(
            f"Quantidade inesperada em {caminho.name}: "
            f"{len(df)} (esperado: {quantidade_esperada})"
        )

    if df[list(colunas)].isna().any().any():
        raise ValueError(f"Valores ausentes em {caminho.name}")

    if not df["review_text"].map(
        lambda valor: isinstance(valor, str) and bool(valor.strip())
    ).all():
        raise ValueError(f"Texto vazio ou inválido em {caminho.name}")

    rotulos_encontrados = set(df["rotulo"].unique())
    rotulos_esperados = set(classes)
    if rotulos_encontrados != rotulos_esperados:
        raise ValueError(
            f"Classes inesperadas em {caminho.name}: "
            f"{rotulos_encontrados}"
        )

    return df


class DatasetSentimento(torch.utils.data.Dataset):
    def __init__(self, df, tokenizer, classes, max_length):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.textos = df["review_text"].tolist()
        self.rotulos = [
            classes[rotulo] for rotulo in df["rotulo"].tolist()
        ]

    def __len__(self):
        return len(self.rotulos)

    def __getitem__(self, indice):
        texto = preprocess_tweet(
            self.textos[indice],
            lang="pt",
        )

        if not texto:
            raise ValueError(
                f"Texto vazio após pré-processamento, índice {indice}"
            )

        entradas = self.tokenizer(
            texto,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        entradas["labels"] = self.rotulos[indice]
        return entradas


class TrainerComPesos(Trainer):
    def __init__(self, *args, pesos_classes=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pesos_classes is None:
            raise ValueError("Pesos das classes não foram informados")
        self.pesos_classes = torch.tensor(
            pesos_classes,
            dtype=torch.float32,
        )

    def compute_loss(
        self,
        model,
        inputs,
        return_outputs=False,
        num_items_in_batch=None,
    ):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        loss = F.cross_entropy(
            logits,
            labels,
            weight=self.pesos_classes.to(logits.device),
        )

        return (loss, outputs) if return_outputs else loss


def calcular_metricas(predicao):
    logits = predicao.predictions
    rotulos = predicao.label_ids

    if isinstance(logits, tuple):
        logits = logits[0]

    logits = np.asarray(logits)
    rotulos = np.asarray(rotulos, dtype=np.int64)

    # Softmax numericamente estável.
    logits = logits - np.max(logits, axis=1, keepdims=True)
    exponenciais = np.exp(logits)
    probabilidades = exponenciais / exponenciais.sum(
        axis=1, keepdims=True
    )

    previstos = np.argmax(probabilidades, axis=-1)
    precisao, recall, f1, suporte = precision_recall_fscore_support(
        rotulos,
        previstos,
        labels=[0, 1, 2],
        zero_division=0,
    )

    # Brier multiclasses: soma dos erros quadráticos por exemplo.
    alvos = np.eye(3, dtype=np.float64)[rotulos]
    brier = float(
        np.mean(np.sum((probabilidades - alvos) ** 2, axis=1))
    )

    # ECE top-label com 15 intervalos de confiança.
    confiancas = np.max(probabilidades, axis=1)
    acertos = (previstos == rotulos).astype(np.float64)
    ece = 0.0
    limites = np.linspace(0.0, 1.0, 16)

    for indice in range(15):
        if indice == 14:
            mascara = (
                (confiancas >= limites[indice])
                & (confiancas <= limites[indice + 1])
            )
        else:
            mascara = (
                (confiancas >= limites[indice])
                & (confiancas < limites[indice + 1])
            )

        if np.any(mascara):
            diferenca = abs(
                np.mean(acertos[mascara])
                - np.mean(confiancas[mascara])
            )
            ece += np.mean(mascara) * diferenca

    metricas = {
        "accuracy": float(accuracy_score(rotulos, previstos)),
        "f1_macro": float(
            f1_score(
                rotulos,
                previstos,
                labels=[0, 1, 2],
                average="macro",
                zero_division=0,
            )
        ),
        "log_loss": float(
            log_loss(rotulos, probabilidades, labels=[0, 1, 2])
        ),
        "brier_multiclass": brier,
        "ece_top_label_15_bins": float(ece),
    }

    nomes = ["negativo", "neutro", "positivo"]
    for indice, nome in enumerate(nomes):
        metricas[f"precision_{nome}"] = float(precisao[indice])
        metricas[f"recall_{nome}"] = float(recall[indice])
        metricas[f"f1_{nome}"] = float(f1[indice])
        metricas[f"support_{nome}"] = int(suporte[indice])

    return metricas


def main():
    parser = argparse.ArgumentParser(
        description="Ajuste fino experimental do BERTweet no BPSAD."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PADRAO,
    )
    parser.add_argument(
        "--piloto",
        action="store_true",
        help="Executa um piloto controlado de 20 passos.",
    )
    args = parser.parse_args()

    config = carregar_config(args.config)
    classes = config["classes"]
    quantidade_classes = len(classes)

    if classes != {"negativo": 0, "neutro": 1, "positivo": 2}:
        raise ValueError("Mapeamento de classes diferente do esperado")

    if quantidade_classes != 3:
        raise ValueError("Este experimento exige exatamente três classes")

    treinamento = config["treinamento"]
    saida = Path(config["saida"]).expanduser().resolve()

    max_steps_piloto = 20
    if args.piloto:
        saida = saida.with_name(saida.name + "-piloto-20-passos")

    if RAIZ == saida or RAIZ in saida.parents:
        raise ValueError("A saída dos pesos precisa ficar fora do repositório")

    if saida.exists() and any(saida.iterdir()):
        raise FileExistsError(
            f"A pasta de saída já contém arquivos: {saida}"
        )

    set_seed(treinamento["seed"])

    caminhos = config["arquivos"]
    hashes = config["sha256"]
    quantidades = config["quantidades"]

    df_treino = validar_entrada(
        RAIZ / caminhos["desenvolvimento"],
        hashes["desenvolvimento"],
        quantidades["desenvolvimento"],
        classes,
    )
    df_validacao = validar_entrada(
        RAIZ / caminhos["validacao"],
        hashes["validacao"],
        quantidades["validacao"],
        classes,
    )

    print("========== DISTRIBUIÇÃO DE CLASSES ==========")
    contagem = Counter(df_treino["rotulo"])
    for classe in classes:
        print(f"{classe}: {contagem[classe]}")

    total = len(df_treino)
    pesos = [
        math.sqrt(
            total / (quantidade_classes * contagem[classe])
        )
        for classe, _ in sorted(classes.items(), key=lambda item: item[1])
    ]

    print("\nPesos da função de perda (raiz inversa):", pesos)

    nome_modelo = config["modelo_base"]
    max_length = config["tokenizacao"]["max_length"]

    print("\n========== CARREGANDO MODELO LOCAL ==========")
    tokenizer = AutoTokenizer.from_pretrained(
        nome_modelo,
        local_files_only=True,
    )
    model_config = AutoConfig.from_pretrained(
        nome_modelo,
        local_files_only=True,
    )

    if model_config.num_labels != 3:
        raise ValueError("O modelo base não possui três classes")

    if model_config.id2label != {0: "NEG", 1: "NEU", 2: "POS"}:
        raise ValueError(
            f"Mapeamento original inesperado: {model_config.id2label}"
        )

    model_config.label2id = {
        "negativo": 0,
        "neutro": 1,
        "positivo": 2,
    }
    model_config.id2label = {
        0: "negativo",
        1: "neutro",
        2: "positivo",
    }

    modelo = AutoModelForSequenceClassification.from_pretrained(
        nome_modelo,
        config=model_config,
        local_files_only=True,
    )

    dataset_treino = DatasetSentimento(
        df_treino, tokenizer, classes, max_length
    )
    dataset_validacao = DatasetSentimento(
        df_validacao, tokenizer, classes, max_length
    )

    batch_treino = treinamento["per_device_train_batch_size"]
    acumulacao = treinamento["gradient_accumulation_steps"]
    micro_lotes_por_epoca = math.ceil(len(dataset_treino) / batch_treino)
    passos_por_epoca = math.ceil(micro_lotes_por_epoca / acumulacao)
    passos_totais = passos_por_epoca * treinamento["num_train_epochs"]

    if args.piloto:
        passos_totais = max_steps_piloto

    warmup_steps = math.ceil(
        passos_totais * treinamento["warmup_ratio"]
    )

    print(f"Passos totais: {passos_totais}")
    print(f"Passos de aquecimento (10%): {warmup_steps}")
    print("Modo:", "PILOTO" if args.piloto else "TREINAMENTO COMPLETO")

    argumentos = TrainingArguments(
        output_dir=str(saida),
        eval_strategy="steps" if args.piloto else "epoch",
        save_strategy="steps" if args.piloto else "epoch",
        max_steps=max_steps_piloto if args.piloto else -1,
        eval_steps=max_steps_piloto if args.piloto else None,
        save_steps=max_steps_piloto if args.piloto else None,
        logging_strategy="steps",
        logging_steps=5 if args.piloto else 25,
        learning_rate=treinamento["learning_rate"],
        per_device_train_batch_size=(
            treinamento["per_device_train_batch_size"]
        ),
        per_device_eval_batch_size=(
            treinamento["per_device_eval_batch_size"]
        ),
        gradient_accumulation_steps=(
            treinamento["gradient_accumulation_steps"]
        ),
        num_train_epochs=treinamento["num_train_epochs"],
        weight_decay=treinamento["weight_decay"],
        warmup_steps=warmup_steps,
        max_grad_norm=treinamento["max_grad_norm"],
        fp16=treinamento["fp16"],
        bf16=treinamento["bf16"],
        gradient_checkpointing=(
            treinamento["gradient_checkpointing"]
        ),
        dataloader_num_workers=(
            treinamento["dataloader_num_workers"]
        ),
        dataloader_pin_memory=False,
        save_total_limit=treinamento["save_total_limit"],
        load_best_model_at_end=True,
        metric_for_best_model=(
            treinamento["metric_for_best_model"]
        ),
        greater_is_better=True,
        report_to="none",
        seed=treinamento["seed"],
        data_seed=treinamento["seed"],
        optim="adamw_torch",
    )

    collator = DataCollatorWithPadding(
        tokenizer=tokenizer,
        pad_to_multiple_of=None,
    )

    trainer = TrainerComPesos(
        model=modelo,
        args=argumentos,
        train_dataset=dataset_treino,
        eval_dataset=dataset_validacao,
        data_collator=collator,
        compute_metrics=calcular_metricas,
        processing_class=tokenizer,
        pesos_classes=pesos,
    )

    print("\n========== AMBIENTE ==========")
    print("Python:", platform.python_version())
    print("PyTorch:", torch.__version__)
    print("HIP:", torch.version.hip)
    print("GPU disponível:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
    else:
        raise RuntimeError("GPU ROCm não está disponível; treinamento cancelado")

    print("\n========== INÍCIO DO TREINAMENTO ==========")
    resultado = trainer.train()

    print("\n========== SALVANDO MELHOR MODELO ==========")
    diretorio_modelo = saida / "melhor_modelo"
    trainer.save_model(str(diretorio_modelo))
    tokenizer.save_pretrained(str(diretorio_modelo))

    # Transformers pode serializar incorretamente o BPE do
    # BertweetTokenizer. Restauramos os arquivos da origem carregada.
    for atributo, nome_arquivo in (
        ("vocab_file", "vocab.txt"),
        ("merges_file", "bpe.codes"),
    ):
        origem = Path(getattr(tokenizer, atributo)).resolve()
        destino = diretorio_modelo / nome_arquivo

        if not origem.is_file():
            raise FileNotFoundError(
                f"Arquivo original do tokenizador não encontrado: {origem}"
            )

        shutil.copy2(origem, destino)

        if sha256_arquivo(origem) != sha256_arquivo(destino):
            raise RuntimeError(
                f"Falha ao preservar o arquivo do tokenizador: {nome_arquivo}"
            )

        print(
            f"Tokenizador preservado: {nome_arquivo} "
            f"(SHA256: {sha256_arquivo(destino)})"
        )

    metricas_finais = trainer.evaluate()

    arquivos_pesos = sorted(
        list(diretorio_modelo.glob("model*.safetensors"))
        + list(diretorio_modelo.glob("pytorch_model*.bin"))
    )
    if not arquivos_pesos:
        raise RuntimeError("Nenhum arquivo de pesos foi salvo.")

    selecao_modelo = {
        "checkpoint": trainer.state.best_model_checkpoint,
        "metrica": treinamento["metric_for_best_model"],
        "melhor_valor": trainer.state.best_metric,
        "passo_final": trainer.state.global_step,
        "sha256_pesos": {
            arquivo.relative_to(diretorio_modelo).as_posix():
                sha256_arquivo(arquivo)
            for arquivo in arquivos_pesos
        },
    }

    if not selecao_modelo["checkpoint"]:
        raise RuntimeError("Trainer não registrou o melhor checkpoint.")

    relatorio = {
        "experimento": config["experimento"],
        "modo_execucao": (
            "piloto_20_passos" if args.piloto else "treinamento_completo"
        ),
        "limite_passos": max_steps_piloto if args.piloto else None,
        "modelo_base": nome_modelo,
        "saida": str(saida),
        "selecao_modelo": selecao_modelo,
        "sha256_entrada": hashes,
        "quantidades": quantidades,
        "configuracao_treinamento": {
            **treinamento,
            "warmup_steps_efetivos": warmup_steps,
        },
        "ambiente": {
            "gpu": torch.cuda.get_device_name(0),
            "hip": torch.version.hip,
        },
        "ponderacao_classes": "raiz_inversa_frequencia",
        "pesos_classes": pesos,
        "metricas_treinamento": resultado.metrics,
        "metricas_validacao_final": metricas_finais,
        "versoes": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": version("transformers"),
            "pysentimiento": version("pysentimiento"),
            "pandas": version("pandas"),
            "scikit_learn": version("scikit-learn"),
        },
    }

    saida.mkdir(parents=True, exist_ok=True)
    (saida / "relatorio_treinamento.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n========== CONCLUÍDO ==========")
    print("Melhor modelo:", saida / "melhor_modelo")
    print("Relatório:", saida / "relatorio_treinamento.json")
    print("F1 macro validação:", metricas_finais.get("eval_f1_macro"))
    print("Accuracy validação:", metricas_finais.get("eval_accuracy"))


if __name__ == "__main__":
    main()
