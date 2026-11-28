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
    ResumoAnalises,
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
    inicio: date | None,
    fim: date | None,
    sentimento: Sentimento | None,
    assunto: str | None = None,
) -> FiltrosAnalises:
    """Valida a entrada do usuário antes de consultar a fonte de dados.

    Levanta ValueError com uma mensagem para o usuário se o período ou o assunto
    forem inválidos. Espaços repetidos no assunto viram um só; vazio é "sem filtro".
    """
    if inicio is not None and fim is not None and inicio > fim:
        raise ValueError("A data inicial deve ser anterior ou igual à data final.")
    if sentimento is not None and sentimento not in SENTIMENTOS:
        raise ValueError("Sentimento inválido.")
    assunto = " ".join((assunto or "").split()) or None
    if assunto is not None and len(assunto) > TAMANHO_MAXIMO_TERMO:
        raise ValueError(f"Use no máximo {TAMANHO_MAXIMO_TERMO} caracteres no assunto.")
    return FiltrosAnalises(inicio=inicio, fim=fim, sentimento=sentimento, assunto=assunto)


def _partes_dos_filtros(filtros: FiltrosAnalises, rotulos: dict[Sentimento, str]) -> list[str]:
    partes = []
    if filtros.assunto:
        partes.append(f"sobre “{filtros.assunto}”")
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
    return partes


def descrever_selecao(filtros: FiltrosAnalises, rotulos: dict[Sentimento, str]) -> str:
    """Descreve a seleção atual, por exemplo "análises publicadas de 01/10/2026 a 31/10/2026"."""
    partes = _partes_dos_filtros(filtros, rotulos)
    return "análises " + ", ".join(partes) if partes else "todas as análises"


def descrever_filtros(filtros: FiltrosAnalises, rotulos: dict[Sentimento, str]) -> str:
    """Resume os filtros em texto, para quem não enxerga os campos do formulário."""
    return f"Exibindo {descrever_selecao(filtros, rotulos)}."


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
    "Publicado em (UTC)",
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
            "Publicado em (UTC)": (
                formatar_data(analise.data_publicacao.date())
                if analise.data_publicacao is not None
                else SEM_DATA
            ),
            "Processado em (UTC)": analise.data_processamento.strftime("%d/%m/%Y %H:%M"),
            "Modelo": analise.modelo_nome,
        }
        for analise in analises
    ]


# --- Distribuição dos sentimentos (RF14, US15) -------------------------------------


def montar_distribuicao(
    resumo: ResumoAnalises, rotulos: dict[Sentimento, str]
) -> list[dict[str, str | int]]:
    """Uma linha por sentimento, sempre na ordem positivo, neutro, negativo.

    Todas as classes aparecem, mesmo com zero, para o gráfico não esconder o que não
    existe. As quantidades são as do resumo e os percentuais somam exatamente 100.
    """
    percentuais = calcular_percentuais(resumo.por_sentimento)
    return [
        {
            "Sentimento": rotulos[s],
            "Quantidade": resumo.por_sentimento.get(s, 0),
            "Percentual": percentuais[s],
            "Rótulo": (
                f"{formatar_inteiro(resumo.por_sentimento.get(s, 0))} ({percentuais[s]}%)"
            ),
        }
        for s in SENTIMENTOS
    ]


# --- Resumo textual (RF15, US16) ---------------------------------------------------

# Abaixo disso a proporção muda muito com poucos textos novos; o resumo avisa.
BASE_PEQUENA = 10


def _plural(quantidade: int, singular: str, plural: str) -> str:
    return singular if quantidade == 1 else plural


def _lista_em_texto(itens: list[str]) -> str:
    if len(itens) <= 2:
        return " e ".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def montar_resumo_textual(
    resumo: ResumoAnalises, filtros: FiltrosAnalises, rotulos: dict[Sentimento, str]
) -> str:
    """Síntese em linguagem natural do resumo e dos filtros aplicados (RF15).

    É um texto montado por regras a partir das contagens da API, não gerado por modelo:
    só afirma o que os números sustentam. Sem registros, não cita distribuição nem
    sentimento predominante. Com empate no topo, informa o empate. Com filtro de
    sentimento, não declara predominância, porque só uma classe foi selecionada.
    """
    partes = _partes_dos_filtros(filtros, rotulos)
    filtros_em_texto = ", ".join(partes)
    if resumo.total == 0:
        onde = f" para os filtros aplicados ({filtros_em_texto})" if partes else ""
        return (
            f"Nenhuma análise encontrada{onde}. Sem registros, não há "
            "distribuição nem sentimento predominante a informar."
        )

    percentuais = calcular_percentuais(resumo.por_sentimento)
    contagens = {s: resumo.por_sentimento.get(s, 0) for s in SENTIMENTOS}
    total = formatar_inteiro(resumo.total)
    distribuicao = ", ".join(
        f"{rotulos[s]} {formatar_inteiro(contagens[s])} ({percentuais[s]}%)"
        for s in SENTIMENTOS
    )
    frases = [
        f"Total de {total} {_plural(resumo.total, 'análise', 'análises')}"
        + (f", considerando os filtros: {filtros_em_texto}." if partes else ", sem filtros."),
        f"Distribuição: {distribuicao}.",
    ]

    if filtros.sentimento is not None:
        frases.append(
            f"Como o filtro seleciona só o sentimento {rotulos[filtros.sentimento].lower()}, "
            "não há comparação entre sentimentos a destacar."
        )
    else:
        maior = max(contagens.values())
        lideres = [s for s in SENTIMENTOS if contagens[s] == maior]
        if len(lideres) == 1:
            lider = lideres[0]
            frases.append(
                f"Sentimento predominante: {rotulos[lider].lower()}, com "
                f"{percentuais[lider]}% das análises."
            )
        else:
            nomes = _lista_em_texto([rotulos[s].lower() for s in lideres])
            frases.append(
                f"Empate entre {nomes}, com {formatar_inteiro(maior)} "
                f"{_plural(maior, 'análise', 'análises')} cada; nenhum sentimento predomina."
            )

    if resumo.total < BASE_PEQUENA:
        frases.append(
            f"A base é pequena (menos de {BASE_PEQUENA} análises); os percentuais podem "
            "mudar bastante com novos textos."
        )
    return " ".join(frases)
