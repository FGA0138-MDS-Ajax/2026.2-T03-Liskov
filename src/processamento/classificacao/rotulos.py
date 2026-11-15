"""Rótulos padronizados do SentIA (RF07): somente positivo, negativo ou neutro."""

ROTULOS = ("positivo", "negativo", "neutro")

# Saída do pysentimiento -> rótulo do SentIA
MAPA_PYSENTIMIENTO = {"POS": "positivo", "NEG": "negativo", "NEU": "neutro"}


def normalizar_rotulo(valor: str) -> str:
    """Converte POS/NEG/NEU ou variações de caixa para o padrão do SentIA."""
    v = str(valor).strip()
    if v.upper() in MAPA_PYSENTIMIENTO:
        return MAPA_PYSENTIMIENTO[v.upper()]
    v = v.lower()
    if v in ROTULOS:
        return v
    raise ValueError(f"Rótulo desconhecido: {valor!r}")
