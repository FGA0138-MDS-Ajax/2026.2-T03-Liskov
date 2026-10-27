"""Classificador principal: pysentimiento/bertweet-pt-sentiment.

O modelo é carregado uma única vez (na inicialização da API) e reutilizado.
O pré-processamento de tweets (menções, URLs, emojis) já é feito pela biblioteca,
portanto NÃO aplicar stemming/stopwords/TF-IDF antes deste modelo.
"""
from __future__ import annotations

from typing import Iterable

from .rotulos import normalizar_rotulo

NOME_MODELO = "pysentimiento/bertweet-pt-sentiment"


class ClassificadorBertweet:
    def __init__(self, analisador=None, tamanho_lote: int = 32):
        # `analisador` pode ser injetado nos testes para evitar baixar 540 MB.
        if analisador is None:
            from pysentimiento import create_analyzer  # import tardio (pesado)

            analisador = create_analyzer(task="sentiment", lang="pt")
        self._analisador = analisador
        self.tamanho_lote = tamanho_lote
        self.nome_modelo = NOME_MODELO

    def prever(self, textos: Iterable[str]) -> list[str]:
        return [r["sentimento"] for r in self.prever_com_probabilidades(textos)]

    def prever_com_probabilidades(self, textos: Iterable[str]) -> list[dict]:
        textos = [str(t) for t in textos]
        saidas: list[dict] = []
        for i in range(0, len(textos), self.tamanho_lote):
            lote = textos[i : i + self.tamanho_lote]
            for r in self._analisador.predict(lote):
                saidas.append(
                    {
                        "sentimento": normalizar_rotulo(r.output),
                        "probabilidades": {
                            normalizar_rotulo(k): float(v) for k, v in r.probas.items()
                        },
                    }
                )
        return saidas
