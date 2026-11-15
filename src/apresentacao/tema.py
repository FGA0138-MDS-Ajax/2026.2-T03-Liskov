"""Tokens visuais de sentimento, usados por indicadores e gráficos.

As cores gerais ficam em .streamlit/config.toml. A identidade visual ainda é
provisória: os wireframes são de baixa fidelidade.
"""

from dataclasses import dataclass

from src.apresentacao.contrato import Sentimento


@dataclass(frozen=True)
class EstiloSentimento:
    rotulo: str
    icone: str  # ícone Material do Streamlit
    cor_markdown: str  # nome de cor aceito pelo Markdown do Streamlit
    cor_grafico: str  # contraste mínimo de 3:1 sobre fundo branco


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
