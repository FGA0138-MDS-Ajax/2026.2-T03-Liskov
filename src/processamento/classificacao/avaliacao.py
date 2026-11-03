"""Métricas da Métrica 2.1 (acurácia) e complementares."""
from __future__ import annotations

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from .rotulos import ROTULOS


def avaliar(y_real: list[str], y_previsto: list[str]) -> dict:
    return {
        "acuracia": accuracy_score(y_real, y_previsto),
        "f1_macro": f1_score(y_real, y_previsto, average="macro", labels=list(ROTULOS), zero_division=0),
        "matriz_confusao": confusion_matrix(y_real, y_previsto, labels=list(ROTULOS)).tolist(),
        "relatorio": classification_report(y_real, y_previsto, labels=list(ROTULOS), zero_division=0),
    }
