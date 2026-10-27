"""Baseline em scikit-learn: TF-IDF + Regressão Logística (RF05/RF06/RF07).

Quando o pipeline de pré-processamento da Sprint 2 estiver pronto, passe-o em
`preprocessador` para que treino e classificação usem exatamente o mesmo tratamento.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def limpeza_minima(texto: str) -> str:
    texto = str(texto).lower()
    texto = re.sub(r"https?://\S+|@\w+", " ", texto)
    texto = re.sub(r"[^\w\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def criar_baseline(preprocessador: Callable[[str], str] = limpeza_minima) -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(preprocessor=preprocessador, ngram_range=(1, 2), min_df=2, sublinear_tf=True),
            ),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def salvar(modelo: Pipeline, caminho: str | Path = "modelos/baseline.pkl") -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, caminho)

def carregar(caminho: str | Path = "modelos/baseline.pkl") -> Pipeline:
    return joblib.load(caminho)
