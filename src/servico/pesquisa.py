"""Pesquisa híbrida: primeiro a base persistida no MongoDB, depois o XFetch para completar.

Combina a busca local na base persistida (CSV, TweetSentBR e coletas anteriores
armazenadas no MongoDB) com complemento sob demanda no XFetch e reutilização do
cache persistente da coleção ``pesquisas``.

A coordenação fica aqui, na camada de serviço; o módulo xfetch.py só adquire tweets.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from src.dados.repositorio import garantir_id_origem, normalizar_fonte

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
    """Identifica um texto pela fonte normalizada e pelo id de origem (ou hash)."""
    return (
        normalizar_fonte(registro.get("fonte")).casefold(),
        garantir_id_origem(registro),
    )


@dataclass
class ResultadoPesquisa:
    da_base: list[dict[str, Any]] = field(default_factory=list)
    do_x: list[dict[str, Any]] = field(default_factory=list)
    duplicatas: int = 0
    aviso: str | None = None
    consultou_x: bool = False
    quantidade_solicitada_x: int = 0
    esgotado_na_origem: bool = False
    cache_reutilizado: bool = False

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
    cache_pesquisa: Mapping[str, Any] | None = None,
    forcar_atualizacao: bool = False,
) -> ResultadoPesquisa:
    """Reaproveita a base/cache e só consulta o X para completar a meta ou atualizar."""
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
    if not forcar_atualizacao and faltam <= 0:
        resultado.cache_reutilizado = cache_pesquisa is not None
        return resultado
    if not complementar_com_x:
        if faltam > 0:
            resultado.aviso = (
                f"A base tem {len(resultado.da_base)} texto(s) sobre o assunto. Marque a opção "
                "de completar com o X para chegar à meta."
            )
        return resultado
    if not forcar_atualizacao and cache_pesquisa is not None:
        esgotado = bool(cache_pesquisa.get("esgotado_na_origem"))
        quantidade_em_cache = int(cache_pesquisa.get("quantidade_solicitada") or 0)
        if esgotado or quantidade_em_cache >= meta:
            resultado.cache_reutilizado = True
            resultado.esgotado_na_origem = esgotado
            if faltam > 0:
                resultado.aviso = (
                    "Resultado reaproveitado do cache persistente da pesquisa; "
                    "não foi necessária nova consulta ao X."
                )
            return resultado
    if buscar_x is None:
        if faltam > 0:
            resultado.aviso = "A busca no X não está configurada; o resultado usa só a base."
        return resultado

    quantidade_pedida = faltam if faltam > 0 else meta
    resultado.consultou_x = True
    resultado.quantidade_solicitada_x = quantidade_pedida

    escolhidos = {chave(r) for r in resultado.da_base}
    bruto = list(buscar_x(consulta, quantidade_pedida))
    resultado.esgotado_na_origem = len(bruto) < quantidade_pedida

    novos_do_x: list[dict[str, Any]] = []
    for registro in bruto:
        identificador = chave(registro)
        if not isinstance(registro.get("id_origem"), str) or registro["id_origem"] != identificador[1]:
            registro = {**registro, "id_origem": identificador[1]}
        if identificador in escolhidos:
            resultado.duplicatas += 1
            continue
        escolhidos.add(identificador)
        if identificador in conhecidos:
            if faltam > 0:
                # Já estava guardado, mas a busca por palavras não o achou: vem da base.
                resultado.da_base.append(conhecidos[identificador])
            else:
                resultado.duplicatas += 1
        else:
            novos_do_x.append(registro)

    if forcar_atualizacao and faltam <= 0 and novos_do_x:
        novos_do_x = novos_do_x[:meta]
        vagas_base = max(0, meta - len(novos_do_x))
        resultado.da_base = resultado.da_base[:vagas_base]

    resultado.do_x = novos_do_x
    return resultado
