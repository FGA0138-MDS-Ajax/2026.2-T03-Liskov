"""Métricas para avaliação da classificação de sentimentos."""

from collections.abc import Mapping

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from .rotulos import ROTULOS, normalizar_rotulo


def avaliar(y_real: list[str], y_previsto: list[str]) -> dict:
    # Guarda as entradas depois que for feito a validação/padronização dos rótulos
    entradas = []

    #Valida e normaliza as respostas corretas e tbm as previsões com a mesma regra
    for nome, valores in (("y_real", y_real), ("y_previsto", y_previsto)):
        # Strings isoladas ou dicionários não é aceito como lista de rótulos
        if isinstance(valores, (str, bytes, Mapping)):
            raise TypeError(f"{nome} deve ser uma coleção de rótulos")

        # Converte outros iteráveis como tuplas, em listas.
        # Se o valor não puder ser percorrido, informa que a entrada é inválida

        try:
            valores = list(valores)
        except TypeError as exc:
            raise TypeError(
                f"{nome} deve ser uma coleção de rótulos"
            ) from exc


        # Se não tiver rótulos não há dados pra calcular as métricas
        if not valores:
            raise ValueError(f"{nome} não pode ser vazio")

        if any(not isinstance(valor, str) for valor in valores):
            raise TypeError(f"{nome} deve conter somente strings")

        # Unifica formatos como "POS" e "positivo"
        entradas.append([
            normalizar_rotulo(valor) for valor in valores
        ])

    y_real, y_previsto = entradas

    # Cada resposta coreta vai ter uma previsão correspodente
    if len(y_real) != len(y_previsto):
        raise ValueError(
            "y_real e y_previsto devem ter o mesmo tamanho"
        )
    
    relatorio_detalhado = classification_report(
        y_real,
        y_previsto,
        labels=list(ROTULOS),
        zero_division=0,
        output_dict=True,
    )

    metricas_por_classe = {
        rotulo: {
            metrica: relatorio_detalhado[rotulo][metrica]
            for metrica in ("precision", "recall", "f1-score", "support")
        }
        for rotulo in ROTULOS
    }

    return {
        "acuracia": accuracy_score(y_real, y_previsto),
        "f1_macro": f1_score(
            y_real,
            y_previsto,
            average="macro",
            labels=list(ROTULOS),
            zero_division=0,
        ),
        "matriz_confusao": confusion_matrix(
            y_real,
            y_previsto,
            labels=list(ROTULOS),
        ).tolist(),
        "metricas_por_classe": metricas_por_classe,
        "relatorio": classification_report(
            y_real,
            y_previsto,
            labels=list(ROTULOS),
            zero_division=0,
        ),
    }