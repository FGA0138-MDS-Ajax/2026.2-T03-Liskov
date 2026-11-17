"""Cálculos de apresentação, sem dependência do Streamlit para facilitar testes."""

import math
import re
from datetime import date

from src.apresentacao.contrato import (
    QUANTIDADE_BUSCA_MAXIMA,
    SENTIMENTOS,
    TAMANHO_MAXIMO_TERMO,
    Analise,
    FiltrosAnalises,
    Sentimento,
)


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


def validar_busca(termo: str, quantidade: int) -> tuple[str, int]:
    """Valida a busca por palavra-chave antes de chamar a API.

    Levanta ValueError com uma mensagem para o usuário. Espaços repetidos viram um só.
    """
    termo = " ".join(termo.split())
    if not termo:
        raise ValueError("Informe uma palavra ou frase para buscar.")
    if len(termo) > TAMANHO_MAXIMO_TERMO:
        raise ValueError(f"Use no máximo {TAMANHO_MAXIMO_TERMO} caracteres na busca.")
    if isinstance(quantidade, bool) or not 1 <= quantidade <= QUANTIDADE_BUSCA_MAXIMA:
        raise ValueError(
            f"A quantidade de tweets deve ficar entre 1 e {QUANTIDADE_BUSCA_MAXIMA}."
        )
    return termo, quantidade


_MENCAO = re.compile(r"(?<![\w@])@\w+")


def mascarar_mencoes(texto: str) -> str:
    """Troca `@perfil` por `@usuário`: o painel não identifica autores (decisão da PO)."""
    return _MENCAO.sub("@usuário", texto)


# --- Listagem de análises (RF10, RF13) -------------------------------------------

COLUNAS_LISTAGEM = (
    "Texto",
    "Sentimento",
    "Fonte",
    "Publicado em",
    "Processado em (UTC)",
    "Modelo",
)
SEM_DATA = "Sem data"


def total_de_paginas(total: int, tamanho: int) -> int:
    """Quantidade de páginas; sempre pelo menos 1, para a navegação nunca ficar em 0."""
    if tamanho < 1:
        raise ValueError("O tamanho da página deve ser positivo.")
    return max(1, math.ceil(max(total, 0) / tamanho))


def limitar_pagina(pagina: int, total: int, tamanho: int) -> int:
    """Mantém a página dentro de 1..última, por exemplo quando os filtros reduzem o total."""
    return min(max(pagina, 1), total_de_paginas(total, tamanho))


def descrever_intervalo(pagina: int, tamanho: int, total: int, exibidos: int) -> str:
    """Texto como "Exibindo 21 a 40 de 1.568 análises", sem inventar o que não veio."""
    if total == 0 or exibidos == 0:
        return "Nenhuma análise nesta página."
    primeiro = (pagina - 1) * tamanho + 1
    ultimo = primeiro + exibidos - 1
    return (
        f"Exibindo {formatar_inteiro(primeiro)} a {formatar_inteiro(ultimo)} "
        f"de {formatar_inteiro(total)} análises."
    )


def montar_linhas_listagem(
    analises: list[Analise], rotulos: dict[Sentimento, str]
) -> list[dict[str, str]]:
    """Converte análises em linhas de tabela, já no formato exibido ao usuário.

    `@perfil` vira `@usuário` (decisão da PO) e a data de publicação ausente aparece
    como "Sem data": datas nunca são inventadas. Datas chegam em UTC e assim são exibidas.
    """
    return [
        {
            "Texto": mascarar_mencoes(analise.texto_original),
            # O sentimento é texto, não só cor: leitores de tela e daltonismo.
            "Sentimento": rotulos[analise.sentimento],
            "Fonte": analise.fonte,
            "Publicado em": (
                formatar_data(analise.data_publicacao.date())
                if analise.data_publicacao is not None
                else SEM_DATA
            ),
            "Processado em (UTC)": analise.data_processamento.strftime("%d/%m/%Y %H:%M"),
            "Modelo": analise.modelo_nome,
        }
        for analise in analises
    ]
