"""Pesquisa híbrida: primeiro a base do SentIA, depois o XFetch para completar.

Segue docs/pesquisa_hibrida_mongodb_xfetch.md. VERSÃO LOCAL DE TESTE:

- A "base" são os textos que a API tem em memória (CSVs importados, buscas anteriores
  no X e o TweetSentBR), no lugar do MongoDB (issue #20).
- A busca na base é por palavras (sem acento e por radical), no lugar da busca
  semântica com embeddings e Vector Search, que o documento deixa para depois.

A coordenação fica aqui, na camada de serviço; o módulo xfetch.py só adquire tweets.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

# Palavras muito comuns que não ajudam a encontrar o assunto.
_PALAVRAS_VAZIAS = frozenset(
    {
        "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos",
        "em", "na", "no", "nas", "nos", "por", "para", "pra", "com", "sem", "que", "e",
        "ou", "mas", "se", "ao", "aos", "sao", "foi", "ser", "ter", "tem", "como",
        "mais", "menos", "muito", "muita", "isso", "isto", "esse", "essa", "este", "esta",
        "eu", "tu", "ele", "ela", "vos", "eles", "elas", "me", "te", "lhe", "ja",
        "nao", "sim",
    }
)  # Já sem acentos, como as palavras comparadas.
_TAMANHO_RADICAL = 5


def relevancia_minima(termos: list[str]) -> float:
    """Critério de similaridade: consultas curtas exigem todos os termos no texto."""
    return 1.0 if len(termos) <= 3 else 2 / 3


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos: "Vacinação" vira "vacinacao"."""
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def _palavras(texto: str) -> list[str]:
    return re.findall(r"\w+", normalizar(texto))


def termos_da_consulta(consulta: str) -> list[str]:
    """Palavras que importam na consulta, sem repetição e na ordem digitada."""
    palavras = _palavras(consulta)
    termos = [p for p in palavras if p not in _PALAVRAS_VAZIAS and (len(p) > 2 or p.isdigit())]
    return list(dict.fromkeys(termos or palavras))


def _radical(palavra: str) -> str:
    # Busca "flexível": "vacina" encontra "vacinação" e "vacinas".
    return palavra[:_TAMANHO_RADICAL]


def pontuar(termos: list[str], texto: str) -> float:
    """Fração dos termos da consulta que aparecem no texto (0 a 1)."""
    if not termos:
        return 0.0
    radicais_do_texto = {_radical(p) for p in _palavras(texto)}
    encontrados = sum(_radical(t) in radicais_do_texto for t in termos)
    return encontrados / len(termos)


def chave(registro: dict[str, Any]) -> tuple[str, str]:
    """Identifica um texto pela fonte e pelo id de origem, para remover duplicatas."""
    return (str(registro.get("fonte", "")).casefold(), str(registro.get("id_origem", "")))


@dataclass
class ResultadoPesquisa:
    da_base: list[dict[str, Any]] = field(default_factory=list)
    do_x: list[dict[str, Any]] = field(default_factory=list)
    duplicatas: int = 0
    aviso: str | None = None

    @property
    def registros(self) -> list[dict[str, Any]]:
        return self.da_base + self.do_x

    @property
    def origens(self) -> list[str]:
        return ["base"] * len(self.da_base) + ["x"] * len(self.do_x)


def pesquisar(
    consulta: str,
    meta: int,
    base: Iterable[dict[str, Any]],
    *,
    buscar_x: Callable[[str, int], list[dict[str, Any]]] | None,
    complementar_com_x: bool,
) -> ResultadoPesquisa:
    """Reaproveita a base e só consulta o X para completar a meta."""
    termos = termos_da_consulta(consulta)
    minimo = relevancia_minima(termos)
    melhores: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
    conhecidos: dict[tuple[str, str], dict[str, Any]] = {}
    for registro in base:
        identificador = chave(registro)
        conhecidos.setdefault(identificador, registro)
        pontos = pontuar(termos, registro.get("texto_original", ""))
        if pontos >= minimo and pontos > melhores.get(identificador, (0.0, None))[0]:
            melhores[identificador] = (pontos, registro)

    ordenados = sorted(melhores.values(), key=lambda par: par[0], reverse=True)
    resultado = ResultadoPesquisa(da_base=[r for _, r in ordenados[:meta]])

    faltam = meta - len(resultado.da_base)
    if faltam <= 0:
        return resultado
    if not complementar_com_x:
        resultado.aviso = (
            f"A base tem {len(resultado.da_base)} texto(s) sobre o assunto. Marque a opção "
            "de completar com o X para chegar à meta."
        )
        return resultado
    if buscar_x is None:
        resultado.aviso = "A busca no X não está configurada; o resultado usa só a base."
        return resultado

    escolhidos = {chave(r) for r in resultado.da_base}
    for registro in buscar_x(consulta, faltam):
        identificador = chave(registro)
        if identificador in escolhidos:
            resultado.duplicatas += 1
            continue
        escolhidos.add(identificador)
        if identificador in conhecidos:
            # Já estava guardado, mas a busca por palavras não o achou: vem da base.
            resultado.da_base.append(conhecidos[identificador])
        else:
            resultado.do_x.append(registro)
    return resultado
