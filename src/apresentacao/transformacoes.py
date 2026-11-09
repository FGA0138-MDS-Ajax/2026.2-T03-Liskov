"""Cálculos de apresentação, sem dependência do Streamlit para facilitar testes."""

from src.apresentacao.contrato import SENTIMENTOS, Sentimento


def calcular_percentuais(por_sentimento: dict[Sentimento, int]) -> dict[Sentimento, int]:
    """Converte contagens em percentuais inteiros que somam exatamente 100.

    Usa o método dos maiores restos: arredonda para baixo e distribui os pontos
    que faltam às classes com maior parte decimal. Sem registros, tudo é zero.
    """
    contagens = {s: por_sentimento.get(s, 0) for s in SENTIMENTOS}
    total = sum(contagens.values())
    if total == 0:
        return {s: 0 for s in SENTIMENTOS}

    percentuais = {s: contagens[s] * 100 // total for s in SENTIMENTOS}
    faltam = 100 - sum(percentuais.values())
    por_maior_resto = sorted(
        SENTIMENTOS, key=lambda s: contagens[s] * 100 % total, reverse=True
    )
    for sentimento in por_maior_resto[:faltam]:
        percentuais[sentimento] += 1
    return percentuais


def formatar_inteiro(valor: int) -> str:
    """Formata no padrão brasileiro: 1568 vira "1.568"."""
    return f"{valor:,}".replace(",", ".")
