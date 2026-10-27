"""Compara o baseline (scikit-learn) com o BERTweet-PT.

Uso:
    python -m scripts.comparar_modelos --treino dados/treino.csv --teste dados/teste.csv

Os CSVs precisam das colunas `texto` e `sentimento` (positivo/negativo/neutro ou POS/NEG/NEU).
"""
import argparse
import time

import pandas as pd

from classificacao import baseline
from classificacao.avaliacao import avaliar
from classificacao.bertweet import ClassificadorBertweet
from classificacao.rotulos import normalizar_rotulo


def ler(caminho: str) -> tuple[list[str], list[str]]:
    df = pd.read_csv(caminho).dropna(subset=["texto", "sentimento"])
    return df["texto"].astype(str).tolist(), [normalizar_rotulo(s) for s in df["sentimento"]]


def mostrar(nome: str, resultado: dict, segundos: float) -> None:
    print(f"\n=== {nome} ({segundos:.1f}s) ===")
    print(f"Acurácia: {resultado['acuracia']:.4f} | F1 macro: {resultado['f1_macro']:.4f}")
    print(resultado["relatorio"])
    print("Matriz de confusão (positivo, negativo, neutro):", resultado["matriz_confusao"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--treino", required=True)
    ap.add_argument("--teste", required=True)
    ap.add_argument("--saida-baseline", default="modelos/baseline.pkl")
    ap.add_argument("--sem-bertweet", action="store_true")
    args = ap.parse_args()

    x_treino, y_treino = ler(args.treino)
    x_teste, y_teste = ler(args.teste)

    t = time.time()
    modelo = baseline.criar_baseline().fit(x_treino, y_treino)
    previsto = modelo.predict(x_teste).tolist()
    mostrar("Baseline TF-IDF + LogReg", avaliar(y_teste, previsto), time.time() - t)
    baseline.salvar(modelo, args.saida_baseline)

    if not args.sem_bertweet:
        t = time.time()
        previsto = ClassificadorBertweet().prever(x_teste)
        mostrar("BERTweet-PT (pysentimiento)", avaliar(y_teste, previsto), time.time() - t)


if __name__ == "__main__":
    main()
