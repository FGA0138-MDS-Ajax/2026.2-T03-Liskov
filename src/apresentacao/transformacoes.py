"""Cálculos de apresentação, sem dependência do Streamlit para facilitar testes."""

from datetime import date

from src.apresentacao.contrato import SENTIMENTOS, FiltrosAnalises, Sentimento


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


def formatar_data(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


def montar_filtros(
    inicio: date | None, fim: date | None, sentimento: Sentimento | None
) -> FiltrosAnalises:
    """Valida a entrada do usuário antes de consultar a fonte de dados.

    Levanta ValueError com uma mensagem para o usuário se o período for inválido.
    """
    if inicio is not None and fim is not None and inicio > fim:
        raise ValueError("A data inicial deve ser anterior ou igual à data final.")
    if sentimento is not None and sentimento not in SENTIMENTOS:
        raise ValueError("Sentimento inválido.")
    return FiltrosAnalises(inicio=inicio, fim=fim, sentimento=sentimento)


def descrever_filtros(filtros: FiltrosAnalises, rotulos: dict[Sentimento, str]) -> str:
    """Resume os filtros em texto, para quem não enxerga os campos do formulário."""
    partes = []
    if filtros.inicio and filtros.fim:
        partes.append(
            f"publicadas de {formatar_data(filtros.inicio)} a {formatar_data(filtros.fim)}"
        )
    elif filtros.inicio:
        partes.append(f"publicadas a partir de {formatar_data(filtros.inicio)}")
    elif filtros.fim:
        partes.append(f"publicadas até {formatar_data(filtros.fim)}")
    if filtros.sentimento:
        partes.append(f"com sentimento {rotulos[filtros.sentimento].lower()}")
    if not partes:
        return "Exibindo todas as análises."
    return "Exibindo análises " + ", ".join(partes) + "."


def filtros_ativos(filtros: FiltrosAnalises) -> bool:
    return filtros != FiltrosAnalises()
