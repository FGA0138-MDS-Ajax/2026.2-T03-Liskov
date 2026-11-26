"""Regra de busca por palavras, a mesma em todo o SentIA.

Usada pela pesquisa do Administrador (``src/servico/pesquisa.py``), pelo filtro por
assunto da consulta (``src/dados/repositorio.py``, #113) e pelo modo de demonstração
do painel. Uma regra só evita que o mesmo assunto encontre textos diferentes em
cada lugar.

A regra:
- maiúsculas e acentos não importam ("Vacinação" = "vacinacao");
- palavras vazias ("de", "o", "para"...) são ignoradas;
- cada termo é comparado pelo radical, os 5 primeiros caracteres: "vacina" encontra
  "vacinação" e "vacinas". Termos com menos de 5 letras precisam da palavra inteira:
  "gol" encontra "gol", mas não "golpe";
- consultas com até 3 termos exigem todos no texto; com mais, pelo menos 2/3.
"""

from __future__ import annotations

import re
import unicodedata

# Palavras muito comuns que não ajudam a encontrar o assunto. Já sem acentos.
PALAVRAS_VAZIAS = frozenset(
    {
        "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos",
        "em", "na", "no", "nas", "nos", "por", "para", "pra", "com", "sem", "que", "e",
        "ou", "mas", "se", "ao", "aos", "sao", "foi", "ser", "ter", "tem", "como",
        "mais", "menos", "muito", "muita", "isso", "isto", "esse", "essa", "este", "esta",
        "eu", "tu", "ele", "ela", "vos", "eles", "elas", "me", "te", "lhe", "ja",
        "nao", "sim",
    }
)  # fmt: skip
TAMANHO_RADICAL = 5

# Letras que podem aparecer acentuadas no texto original. O padrão aceita todas as
# formas, em maiúscula e minúscula, porque o texto guardado não é normalizado.
_VARIANTES = {
    "a": "aàáâãäAÀÁÂÃÄ",
    "e": "eèéêëEÈÉÊË",
    "i": "iìíîïIÌÍÎÏ",
    "o": "oòóôõöOÒÓÔÕÖ",
    "u": "uùúûüUÙÚÛÜ",
    "c": "cçCÇ",
    "n": "nñNÑ",
    "y": "yýÿYÝ",
}
# O que conta como letra de palavra no texto original: ASCII, dígitos, "_" e as
# letras acentuadas do Latin-1. Funciona igual no Python e no MongoDB (PCRE).
_LETRA = "0-9A-Za-z_À-ÖØ-öø-ÿ"
_INICIO_DE_PALAVRA = f"(?<![{_LETRA}])"
_FIM_DE_PALAVRA = f"(?![{_LETRA}])"


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos: "Vacinação" vira "vacinacao"."""
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def palavras(texto: str) -> list[str]:
    return re.findall(r"\w+", normalizar(texto))


def termos_da_consulta(consulta: str) -> list[str]:
    """Palavras que importam na consulta, sem repetição e na ordem digitada."""
    todas = palavras(consulta)
    termos = [
        p for p in todas if p not in PALAVRAS_VAZIAS and (len(p) > 2 or p.isdigit())
    ]
    return list(dict.fromkeys(termos or todas))


def radical(palavra: str) -> str:
    return palavra[:TAMANHO_RADICAL]


def relevancia_minima(termos: list[str]) -> float:
    """Consultas curtas exigem todos os termos no texto; longas, 2/3 deles."""
    return 1.0 if len(termos) <= 3 else 2 / 3


def minimo_de_termos(termos: list[str]) -> int:
    """Quantos termos precisam aparecer no texto (a relevância mínima, em inteiro)."""
    total = len(termos)
    return total if total <= 3 else -(-2 * total // 3)


def pontuar(termos: list[str], texto: str) -> float:
    """Fração dos termos da consulta que aparecem no texto (0 a 1)."""
    if not termos:
        return 0.0
    radicais_do_texto = {radical(p) for p in palavras(texto)}
    encontrados = sum(radical(t) in radicais_do_texto for t in termos)
    return encontrados / len(termos)


def corresponde(consulta: str, texto: str) -> bool:
    """O texto é sobre o assunto? Mesma decisão do filtro no MongoDB."""
    termos = termos_da_consulta(consulta)
    return bool(termos) and pontuar(termos, texto) >= relevancia_minima(termos)


def padrao_do_termo(termo: str) -> str:
    """Expressão regular que encontra o termo no texto original, sem normalizar.

    Equivale a ``radical(termo) in {radical(p) for p in palavras(texto)}``. O texto
    digitado nunca vira expressão regular: cada caractere é escapado ou trocado por
    uma classe fechada de variantes acentuadas.
    """
    trecho = radical(normalizar(termo))
    partes = []
    for caractere in trecho:
        variantes = _VARIANTES.get(caractere)
        if variantes:
            partes.append(f"[{variantes}]")
        elif caractere.isascii() and caractere.isalpha():
            partes.append(f"[{caractere}{caractere.upper()}]")
        else:
            partes.append(re.escape(caractere))
    padrao = _INICIO_DE_PALAVRA + "".join(partes)
    # Radical incompleto (termo curto) só vale para a palavra inteira.
    return padrao if len(trecho) == TAMANHO_RADICAL else padrao + _FIM_DE_PALAVRA
