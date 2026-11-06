"""Compara o baseline TF-IDF + LogReg com o BERTweet-PT.

TweetSentBR:
    python -m scripts.comparar_modelos --dataset Datasets/tweetsent.csv

Formato tradicional:
    python -m scripts.comparar_modelos --treino dados/treino.csv --teste dados/teste.csv
"""
import argparse
import time
import unicodedata

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from src.processamento.classificacao import baseline
from src.processamento.classificacao.avaliacao import avaliar
from src.processamento.classificacao.bertweet import ClassificadorBertweet
from src.processamento.classificacao.rotulos import normalizar_rotulo


def ler(caminho: str, coluna_rotulo: str = "sentimento"):
    df = pd.read_csv(caminho).dropna(subset=["texto", coluna_rotulo])
    textos = df["texto"].astype(str).tolist()
    rotulos = [normalizar_rotulo(s) for s in df[coluna_rotulo]]
    return textos, rotulos


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", str(texto))
    return " ".join(texto.casefold().split())


def dividir_tweetsentbr(caminho: str, semente: int = 42):
    df = pd.read_csv(caminho).dropna(subset=["texto", "rotulo"]).copy()
    df["texto"] = df["texto"].astype(str)
    df["rotulo"] = df["rotulo"].map(normalizar_rotulo)
    df["_grupo"] = df["texto"].map(normalizar_texto)

    # Grupos com rótulos conflitantes não entram na avaliação.
    conflitos = df.groupby("_grupo")["rotulo"].nunique()
    grupos_conflitantes = set(conflitos[conflitos > 1].index)
    df = df[~df["_grupo"].isin(grupos_conflitantes)].copy()

    # Mantém todas as ocorrências de um mesmo texto no mesmo conjunto.
    divisor = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=semente)
    indices_treino, indices_teste = next(
        divisor.split(df, df["rotulo"], groups=df["_grupo"])
    )
    treino = df.iloc[indices_treino]
    teste = df.iloc[indices_teste]

    print("\n=== Preparação do TweetSentBR ===")
    print(f"Registros originais: {pd.read_csv(caminho).shape[0]}")
    print(f"Grupos com rótulos conflitantes excluídos: {len(grupos_conflitantes)}")
    print(f"Registros utilizáveis: {len(df)}")
    print(f"Treino: {len(treino)} | Teste: {len(teste)}")
    print(f"Textos distintos no teste: {teste['_grupo'].nunique()}")

    return (
        treino["texto"].tolist(),
        treino["rotulo"].tolist(),
        teste["texto"].tolist(),
        teste["rotulo"].tolist(),
    )


def mostrar(nome: str, resultado: dict, segundos: float) -> None:
    print(f"\n=== {nome} ({segundos:.1f}s) ===")
    print(f"Acurácia: {resultado['acuracia']:.4f} | F1 macro: {resultado['f1_macro']:.4f}")
    print(resultado["relatorio"])
    print("Matriz de confusão (positivo, negativo, neutro):", resultado["matriz_confusao"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--treino")
    ap.add_argument("--teste")
    ap.add_argument("--dataset", help="TweetSentBR com colunas texto e rotulo")
    ap.add_argument("--saida-baseline", default="modelos/baseline.pkl")
    ap.add_argument("--sem-bertweet", action="store_true")
    args = ap.parse_args()

    if args.dataset:
        if args.treino or args.teste:
            ap.error("Use --dataset ou --treino/--teste, não ambos.")
        x_treino, y_treino, x_teste, y_teste = dividir_tweetsentbr(args.dataset)
    else:
        if not args.treino or not args.teste:
            ap.error("Informe --dataset ou os dois argumentos --treino e --teste.")
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
