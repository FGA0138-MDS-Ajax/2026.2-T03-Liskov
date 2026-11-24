#!/usr/bin/env python3
"""Calibração experimental do BERTweet original e modelo C, sem treinamento."""

import gc
import json
import platform
import runpy
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
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

RAIZ = Path(__file__).resolve().parents[2]
DIRETORIO_RELATORIOS = RAIZ / "docs/resultados_bpsad/issue103"
AVALIADOR = RAIZ / "scripts/experimentos/avaliar_bertweet_issue103.py"

# Reaproveita a validação, o pré-processamento e o Dataset já verificados.
ctx = runpy.run_path(str(AVALIADOR), run_name="avaliador_issue103")

carregar_validacao = ctx["carregar_validacao"]
DatasetInferencia = ctx["DatasetInferencia"]
calcular_ece = ctx["calcular_ece"]
MODELO_BASE = ctx["MODELO_BASE"]
MODELOS = ctx["MODELOS"]
BATCH_SIZE = ctx["BATCH_SIZE"]
NOMES_CLASSES = ctx["NOMES_CLASSES"]

SEMENTE = 103
FRACAO_CALIBRACAO = 0.5
MODELO_C_COMPLETO = (
    Path.home()
    / "models/sentia/issue-103-bertweet-ft-v3-raiz-pesos"
    / "melhor_modelo"
)

MODELOS_ALVO = [
    ("Original", MODELO_BASE),
    ("C completo - 3 épocas", str(MODELO_C_COMPLETO)),
]


def separar_dados(alvos):
    from sklearn.model_selection import train_test_split

    indices = np.arange(len(alvos))
    calibracao, avaliacao = train_test_split(
        indices,
        test_size=1.0 - FRACAO_CALIBRACAO,
        random_state=SEMENTE,
        stratify=alvos,
    )
    return calibracao, avaliacao


def obter_logits(nome, caminho, tokenizer, textos, dispositivo):
    caminho_local = Path(caminho).expanduser()
    origem = (
        MODELO_BASE
        if nome == "Original"
        else str(caminho_local)
    )

    if nome != "Original" and not caminho_local.is_dir():
        raise FileNotFoundError(caminho_local)

    print(f"\nCarregando {nome}: {origem}")
    modelo = AutoModelForSequenceClassification.from_pretrained(
        origem,
        local_files_only=True,
    )

    if modelo.config.num_labels != 3:
        raise ValueError(f"{nome}: esperado modelo com três classes")

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


def ajustar_temperatura(logits, alvos):
    logits_t = torch.tensor(logits, dtype=torch.float32)
    alvos_t = torch.tensor(alvos, dtype=torch.long)

    log_temp = torch.nn.Parameter(torch.zeros(1))
    otimizador = torch.optim.LBFGS(
        [log_temp],
        lr=0.1,
        max_iter=100,
        line_search_fn="strong_wolfe",
    )

    def fechamento():
        otimizador.zero_grad()
        temperatura = log_temp.clamp(-3.0, 3.0).exp()
        perda = F.cross_entropy(logits_t / temperatura, alvos_t)
        perda.backward()
        return perda

    otimizador.step(fechamento)
    return float(log_temp.detach().clamp(-3.0, 3.0).exp().item())


def prever_com_limiar(probabilidades, limiar_neutro):
    # Se neutro ultrapassa o limiar, prevalece.
    # Caso contrário, decide entre negativo e positivo.
    previstos = np.where(
        probabilidades[:, 1] >= limiar_neutro,
        1,
        np.where(
            probabilidades[:, 0] >= probabilidades[:, 2],
            0,
            2,
        ),
    )
    return previstos.astype(np.int64)


def ajustar_limiar(probabilidades, alvos):
    melhor_f1 = -1.0
    melhor_limiar = None

    for limiar in np.arange(0.05, 0.951, 0.005):
        previstos = prever_com_limiar(probabilidades, limiar)
        valor = f1_score(
            alvos,
            previstos,
            labels=[0, 1, 2],
            average="macro",
            zero_division=0,
        )

        # Em empate, prefere limiar mais próximo de 1/3.
        if (
            valor > melhor_f1 + 1e-12
            or (
                abs(valor - melhor_f1) <= 1e-12
                and (
                    melhor_limiar is None
                    or abs(limiar - 1 / 3)
                    < abs(melhor_limiar - 1 / 3)
                )
            )
        ):
            melhor_f1 = float(valor)
            melhor_limiar = float(limiar)

    return melhor_limiar, melhor_f1


def metricas(nome, alvos, probabilidades, previstos):
    precisao, recall, f1, suporte = precision_recall_fscore_support(
        alvos,
        previstos,
        labels=[0, 1, 2],
        zero_division=0,
    )

    return {
        "modelo": nome,
        "accuracy": float(accuracy_score(alvos, previstos)),
        "f1_macro": float(f1_score(
            alvos, previstos, labels=[0, 1, 2],
            average="macro", zero_division=0,
        )),
        "log_loss": float(log_loss(
            alvos, probabilidades, labels=[0, 1, 2]
        )),
        "brier": float(np.mean(np.sum(
            (probabilidades - np.eye(3)[alvos]) ** 2,
            axis=1,
        ))),
        "ece": calcular_ece(probabilidades, previstos, alvos),
        "por_classe": {
            NOMES_CLASSES[i]: {
                "precision": float(precisao[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "suporte": int(suporte[i]),
            }
            for i in range(3)
        },
        "matriz_confusao": confusion_matrix(
            alvos, previstos, labels=[0, 1, 2]
        ).tolist(),
        "neutros_como_positivos": int(
            np.sum((alvos == 1) & (previstos == 2))
        ),
    }


def main():
    print("ISSUE #103 - CALIBRAÇÃO SEM TREINAMENTO")
    print("Nenhum peso será atualizado ou salvo.")
    print("Nenhum arquivo de modelo ou peso será alterado.")

    textos, alvos, sha = carregar_validacao()
    idx_cal, idx_eval = separar_dados(alvos)

    print(f"\nValidação total: {len(alvos)}")
    print(f"SHA256: {sha}")
    print(f"Parte de calibração: {len(idx_cal)}")
    print(f"Subconjunto de avaliação da validação: {len(idx_eval)}")
    print(f"Semente da divisão: {SEMENTE}")

    dispositivo = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    print(f"Dispositivo: {dispositivo}")

    tokenizer = AutoTokenizer.from_pretrained(
        MODELO_BASE,
        local_files_only=True,
    )

    resumo = []
    detalhes_modelos = []

    for nome, caminho in MODELOS_ALVO:
        logits = obter_logits(
            nome, caminho, tokenizer, textos, dispositivo
        )

        logits_cal = logits[idx_cal]
        y_cal = alvos[idx_cal]
        logits_eval = logits[idx_eval]
        y_eval = alvos[idx_eval]

        # Referência sem calibração.
        probs_raw = torch.softmax(
            torch.tensor(logits_eval), dim=-1
        ).numpy()
        pred_raw = probs_raw.argmax(axis=1)

        # Ajuste da temperatura exclusivamente na metade de calibração.
        temperatura = ajustar_temperatura(logits_cal, y_cal)

        probs_cal = torch.softmax(
            torch.tensor(logits_cal / temperatura), dim=-1
        ).numpy()
        probs_eval_temp = torch.softmax(
            torch.tensor(logits_eval / temperatura), dim=-1
        ).numpy()

        # Limiar neutro escolhido somente na metade de calibração.
        limiar, f1_cal = ajustar_limiar(probs_cal, y_cal)
        pred_calibrado = prever_com_limiar(
            probs_eval_temp, limiar
        )

        bruto = metricas(
            f"{nome} - original",
            y_eval,
            probs_raw,
            pred_raw,
        )
        temperatura_resultado = metricas(
            f"{nome} - temperatura",
            y_eval,
            probs_eval_temp,
            probs_eval_temp.argmax(axis=1),
        )
        final = metricas(
            f"{nome} - temperatura + limiar neutro",
            y_eval,
            probs_eval_temp,
            pred_calibrado,
        )

        detalhes_modelos.append({
            "modelo": nome,
            "origem": caminho,
            "temperatura": float(temperatura),
            "limiar_neutro": float(limiar),
            "f1_macro_na_parte_de_calibracao": float(f1_cal),
            "resultados": {
                "sem_calibracao": bruto,
                "temperatura": temperatura_resultado,
                "temperatura_e_limiar_neutro": final,
            },
        })

        print("\n" + "=" * 72)
        print(f"MODELO: {nome}")
        print(f"Temperatura ajustada: {temperatura:.6f}")
        print(f"Limiar neutro ajustado: {limiar:.3f}")
        print(f"F1 macro na parte de calibração: {f1_cal:.4f}")
        print("\nResultados no subconjunto de avaliação da validação:")
        for resultado in (bruto, temperatura_resultado, final):
            print(
                f"\n{resultado['modelo']}\n"
                f"  Accuracy: {resultado['accuracy']:.4f}\n"
                f"  F1 macro: {resultado['f1_macro']:.4f}\n"
                f"  F1 negativo: {resultado['por_classe']['negativo']['f1']:.4f}\n"
                f"  F1 neutro: {resultado['por_classe']['neutro']['f1']:.4f}\n"
                f"  F1 positivo: {resultado['por_classe']['positivo']['f1']:.4f}\n"
                f"  Log-loss: {resultado['log_loss']:.4f}\n"
                f"  Brier: {resultado['brier']:.4f}\n"
                f"  ECE: {resultado['ece']:.4f}\n"
                f"  Neutros previstos como positivos: "
                f"{resultado['neutros_como_positivos']}"
            )

        resumo.extend((bruto, temperatura_resultado, final))
        del logits
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    print("\n" + "=" * 72)
    print("RESUMO - AVALIAÇÃO INTERNA DA VALIDAÇÃO")
    print(
        f"{'Modelo':<43} {'Acc':>7} {'F1 macro':>9} "
        f"{'F1 neutro':>10} {'ECE':>8}"
    )
    for r in resumo:
        print(
            f"{r['modelo']:<43} "
            f"{r['accuracy']:>7.4f} "
            f"{r['f1_macro']:>9.4f} "
            f"{r['por_classe']['neutro']['f1']:>10.4f} "
            f"{r['ece']:>8.4f}"
        )

    def versao_pacote(nome):
        try:
            return version(nome)
        except PackageNotFoundError:
            return None

    relatorio = {
        "experimento": "calibracao_bertweet_issue103",
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "dados": {
            "arquivo_validacao": str(
                ctx["ARQUIVO_VALIDACAO"].relative_to(RAIZ)
            ),
            "sha256_validacao": sha,
            "total_validacao": int(len(alvos)),
            "quantidade_calibracao": int(len(idx_cal)),
            "quantidade_avaliacao": int(len(idx_eval)),
            "semente_divisao": SEMENTE,
            "fracao_calibracao": FRACAO_CALIBRACAO,
            "distribuicao_total": {
                nome: int(np.sum(alvos == indice))
                for nome, indice in ctx["CLASSES"].items()
            },
        },
        "metodologia": {
            "ajuste_temperatura": "somente na parte de calibracao",
            "ajuste_limiar_neutro": "somente na parte de calibracao",
            "checkpoint_selecionado_com_validacao_completa": True,
            "ressalva": (
                "O subconjunto de avaliacao nao participou do ajuste da "
                "temperatura ou do limiar. Entretanto, nao constitui teste "
                "independente do treinamento, pois a selecao do checkpoint "
                "utilizou a validacao completa de 1600 exemplos. "
                "Os rotulos BPSAD sao derivados de avaliacoes por estrelas."
            ),
        },
        "configuracao": {
            "modelos": [
                {"nome": nome, "origem": caminho}
                for nome, caminho in MODELOS_ALVO
            ],
            "max_length": ctx["MAX_LENGTH"],
            "batch_size": BATCH_SIZE,
            "classes": NOMES_CLASSES,
        },
        "ambiente": {
            "python": platform.python_version(),
            "plataforma": platform.platform(),
            "torch": str(torch.__version__),
            "numpy": versao_pacote("numpy"),
            "scikit_learn": versao_pacote("scikit-learn"),
            "transformers": versao_pacote("transformers"),
            "pysentimiento": versao_pacote("pysentimiento"),
            "dispositivo": str(dispositivo),
        },
        "modelos": detalhes_modelos,
    }

    DIRETORIO_RELATORIOS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destino = DIRETORIO_RELATORIOS / f"calibracao_{timestamp}.json"

    with destino.open("x", encoding="utf-8") as saida:
        json.dump(relatorio, saida, ensure_ascii=False, indent=2)
        saida.write("\n")

    print(f"\nRelatorio JSON salvo em: {destino.relative_to(RAIZ)}")
    print("\nExperimento concluido.")
    print("Nenhum treinamento ou peso foi alterado.")


if __name__ == "__main__":
    main()
