"""Tokens visuais: rótulos, ícones e cores de sentimento nos temas claro e escuro (#121).

As cores gerais (fundo, texto, botões) ficam em .streamlit/config.toml, que define os dois
temas. O que o Streamlit não pinta sozinho, como os gráficos Altair, lê a paleta do tema
ativo em `paleta()`. As seções nunca escrevem cores em hexadecimal: usam este módulo.

Contraste conferido (WCAG): texto com pelo menos 4,5:1 e marcas de gráfico com 3:1 sobre o
fundo de cada tema. No escuro, os tons são mais claros, porque os do claro ficariam abaixo
de 3:1 sobre #0E1117.
"""

from dataclasses import dataclass
from typing import Literal

import streamlit as st

from src.apresentacao.contrato import Sentimento

Tema = Literal["light", "dark"]


@dataclass(frozen=True)
class EstiloSentimento:
    rotulo: str
    icone: str  # ícone Material do Streamlit
    cor_markdown: str  # nome de cor do Markdown do Streamlit; o próprio tema ajusta o tom
    cor_grafico: str  # tema claro; para o escuro, use `paleta()`


ESTILOS_SENTIMENTO: dict[Sentimento, EstiloSentimento] = {
    "positivo": EstiloSentimento(
        "Positivo", ":material/sentiment_satisfied:", "green", "#1E7B4F"
    ),
    "neutro": EstiloSentimento(
        "Neutro", ":material/sentiment_neutral:", "orange", "#B7791F"
    ),
    "negativo": EstiloSentimento(
        "Negativo", ":material/sentiment_dissatisfied:", "red", "#C53030"
    ),
}


@dataclass(frozen=True)
class Paleta:
    primaria: str
    texto: str
    texto_secundario: str
    borda: str
    grafico: dict[Sentimento, str]
    # Etiqueta da tabela: (fundo, texto), com contraste de pelo menos 4,5:1.
    etiqueta: dict[Sentimento, tuple[str, str]]


PALETAS: dict[Tema, Paleta] = {
    "light": Paleta(
        primaria="#3B5BA5",
        texto="#1F2933",
        texto_secundario="#52606D",
        borda="#E4E7EB",
        grafico={s: e.cor_grafico for s, e in ESTILOS_SENTIMENTO.items()},
        etiqueta={
            "positivo": ("#E6F4EC", "#17603D"),
            "neutro": ("#FBF1E1", "#7A4E0E"),
            "negativo": ("#FDECEC", "#A12626"),
        },
    ),
    "dark": Paleta(
        # Azul mais claro que o do claro: #3B5BA5 fica com 2,9:1 sobre o fundo escuro.
        primaria="#5273C2",
        texto="#FAFAFA",
        texto_secundario="#A3ACB9",
        borda="#3A3D4A",
        grafico={"positivo": "#3DB77E", "neutro": "#D69E2E", "negativo": "#E05A5A"},
        etiqueta={
            "positivo": ("#163A2A", "#7FD9A8"),
            "neutro": ("#3D2E12", "#F2C46D"),
            "negativo": ("#4A1C1C", "#FF9C9C"),
        },
    ),
}


def tema_atual() -> Tema:
    """"light" ou "dark", conforme o tema escolhido no menu do Streamlit.

    Fora de uma execução do Streamlit (por exemplo, em testes) o tipo vem vazio e vale o
    claro. A página roda de novo quando a pessoa troca o tema.
    """
    return "dark" if st.context.theme.type == "dark" else "light"


def paleta(tema: Tema | None = None) -> Paleta:
    return PALETAS[tema or tema_atual()]
