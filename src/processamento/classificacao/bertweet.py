"""Classificador de sentimentos em português com BERTweet via PySentimiento.

O analisador é carregado uma vez e deve ser reutilizado pela aplicação. O
pré-processamento de texto adequado a tweets é feito pelo PySentimiento.
"""
from __future__ import annotations

from typing import Iterable

from .rotulos import ROTULOS, normalizar_rotulo

NOME_MODELO = "pysentimiento/bertweet-pt-sentiment"


class ClassificadorBertweet:
    """Classifica textos e devolve rótulos e probabilidades por texto.

    Args:
        analisador: analisador compatível com ``pysentimiento``. Injetável
            para testes ou integração com uma instância já carregada.
        tamanho_lote: número máximo de textos enviados em cada chamada.

    Entradas devem ser strings não vazias. Uma string isolada é tratada como
    um único texto; uma coleção vazia retorna uma lista vazia.
    """

    def __init__(self, analisador=None, tamanho_lote: int = 32):
        if isinstance(tamanho_lote, bool) or not isinstance(tamanho_lote, int):
            raise TypeError("tamanho_lote deve ser um número inteiro")
        if tamanho_lote <= 0:
            raise ValueError("tamanho_lote deve ser maior que zero")

        if analisador is None:
            from pysentimiento import create_analyzer  # import tardio (pesado)

            analisador = create_analyzer(task="sentiment", lang="pt")
        self._analisador = analisador
        self.tamanho_lote = tamanho_lote
        self.nome_modelo = NOME_MODELO

    @staticmethod
    def _validar_textos(textos: Iterable[str] | str) -> list[str]:
        if isinstance(textos, str):
            textos = [textos]
        else:
            try:
                textos = list(textos)
            except TypeError as exc:
                raise TypeError("textos deve ser uma string ou uma coleção de strings") from exc

        for indice, texto in enumerate(textos):
            if not isinstance(texto, str):
                raise TypeError(f"texto na posição {indice} deve ser uma string")
            if not texto.strip():
                raise ValueError(f"texto na posição {indice} não pode ser vazio")
        return textos

    def prever(self, textos: Iterable[str] | str) -> list[str]:
        """Retorna apenas os rótulos padronizados dos textos recebidos."""
        return [r["sentimento"] for r in self.prever_com_probabilidades(textos)]

    def prever_com_probabilidades(self, textos: Iterable[str] | str) -> list[dict]:
        """Retorna ``[{sentimento, probabilidades}, ...]`` na ordem de entrada."""
        textos = self._validar_textos(textos)
        saidas: list[dict] = []
        for i in range(0, len(textos), self.tamanho_lote):
            lote = textos[i : i + self.tamanho_lote]
            resultados = self._analisador.predict(lote)
            if len(resultados) != len(lote):
                raise RuntimeError("o analisador retornou quantidade inesperada de resultados")
            for resultado in resultados:
                probabilidades = {rotulo: 0.0 for rotulo in ROTULOS}
                for rotulo, valor in resultado.probas.items():
                    probabilidades[normalizar_rotulo(rotulo)] = float(valor)
                saidas.append(
                    {
                        "sentimento": normalizar_rotulo(resultado.output),
                        "probabilidades": probabilidades,
                    }
                )
        return saidas
