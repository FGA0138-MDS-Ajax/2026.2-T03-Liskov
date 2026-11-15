"""Módulo de aquisição automatizada do corpus inicial TweetSentBR (RF02 / US02 — Issue #1).

Implementa a interface oficial de aquisição de textos em português brasileiro
para o pipeline do SentIA, reutilizando o importador CSV homologado (Issue #2)
e garantindo:
- Resolução determinística do caminho padrão (`Datasets/tweetsent.csv`) em relação
  à raiz do repositório, independentemente do diretório de execução atual (`cwd`);
- Processamento em fluxo (`iterar_tweetsentbr` / `iterar_dados_aquisicao`) com
  suporte a `limite` para evitar leitura desnecessária de arquivos extensos;
- Preservação integral de `id_origem`, `texto_original`, `fonte`,
  `rotulo_original`, `rotulo_padronizado` (`POS`, `NEG`, `NEU`),
  `data_publicacao` e `metadados` opcionais;
- Ausência do campo `sentimento` (reservado exclusivamente à saída do classificador ML);
- Tratamento previsível de erros para caminhos inválidos, diretórios, falhas de
  permissão, arquivos vazios, esquemas incompatíveis e codificação incorreta.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, Iterator

from .csv_importer import RelatorioImportacao, iterar_dataset_csv

DIRETORIO_RAIZ_PROJETO: Path = Path(__file__).resolve().parents[3]
CAMINHO_PADRAO_TWEETSENTBR: Path = (
    DIRETORIO_RAIZ_PROJETO / "Datasets" / "tweetsent.csv"
)
FONTE_PADRAO_TWEETSENTBR: str = "TweetSentBR"


def _validar_limite(limite: int | None) -> None:
    """Valida o parâmetro opcional de limite de registros."""
    if limite is None:
        return
    if isinstance(limite, bool) or not isinstance(limite, int):
        raise TypeError("O parâmetro 'limite' deve ser um número inteiro positivo.")
    if limite <= 0:
        raise ValueError("O parâmetro 'limite' deve ser maior que zero.")


def resolver_caminho_tweetsentbr(
    caminho: str | Path | None = None,
    *,
    permitir_none: bool = True,
) -> Path:
    """Resolve e valida o caminho para o arquivo CSV de aquisição.

    Quando ``caminho`` é ``None`` (e ``permitir_none=True``), utiliza
    ``CAMINHO_PADRAO_TWEETSENTBR`` relativo à raiz do projeto, sem depender do
    diretório de trabalho atual. Caminhos relativos como ``Datasets/tweetsent.csv``
    ou ``datasets/tweetsent.csv`` também são resolvidos em relação à raiz do
    repositório caso não existam no diretório atual.
    """
    if caminho is None:
        if not permitir_none:
            raise ValueError(
                "O caminho da fonte de aquisição não pode ser None."
            )
        alvo = CAMINHO_PADRAO_TWEETSENTBR
    elif not isinstance(caminho, (str, Path)):
        raise TypeError(
            "O caminho da fonte de aquisição deve ser uma string ou Path."
        )
    else:
        if isinstance(caminho, str) and not caminho.strip():
            raise ValueError(
                "O caminho da fonte de aquisição não pode ser vazio."
            )
        alvo = Path(caminho)

    if alvo.exists():
        if alvo.is_dir():
            raise IsADirectoryError(
                f"O caminho informado é um diretório, não um arquivo: {alvo}"
            )
        return alvo.resolve()

    if not alvo.is_absolute():
        candidatos_raiz: list[Path] = [DIRETORIO_RAIZ_PROJETO / alvo]
        partes = alvo.parts
        if partes and partes[0].lower() == "datasets":
            nome_pasta_canonica = (
                "Datasets" if partes[0] != "Datasets" else "datasets"
            )
            candidatos_raiz.append(
                DIRETORIO_RAIZ_PROJETO
                / nome_pasta_canonica
                / Path(*partes[1:])
            )

        for candidato in candidatos_raiz:
            if candidato.exists():
                if candidato.is_dir():
                    raise IsADirectoryError(
                        "O caminho informado é um diretório, não um arquivo: "
                        f"{candidato}"
                    )
                return candidato.resolve()

    raise FileNotFoundError(
        f"Arquivo da fonte de aquisição não encontrado: {alvo}"
    )


def iterar_tweetsentbr(
    caminho: str | Path | None = None,
    *,
    delimitador: str = ",",
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
    limite: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Itera sobre registros do corpus TweetSentBR em modo streaming (RF02 / US02).

    Args:
        caminho: Caminho opcional para o arquivo CSV. Se ``None``, utiliza o
            corpus padrão do projeto (``Datasets/tweetsent.csv``).
        delimitador: Separador de colunas do CSV (padrão ``","``).
        modo_estrito: Se ``True`` (padrão), interrompe ao encontrar qualquer
            registro inválido. Se ``False``, ignora registros inválidos e os
            contabiliza em ``relatorio``.
        relatorio: Instância opcional de ``RelatorioImportacao`` para auditoria.
        limite: Quantidade máxima opcional de registros válidos a retornar.
    """
    _validar_limite(limite)
    caminho_resolvido = resolver_caminho_tweetsentbr(
        caminho,
        permitir_none=True,
    )
    fluxo = iterar_dataset_csv(
        caminho_resolvido,
        delimitador=delimitador,
        modo_estrito=modo_estrito,
        relatorio=relatorio,
    )
    if limite is not None:
        yield from itertools.islice(fluxo, limite)
    else:
        yield from fluxo


def carregar_tweetsentbr(
    caminho: str | Path | None = None,
    *,
    delimitador: str = ",",
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
    limite: int | None = None,
) -> list[dict[str, Any]]:
    """Carrega registros do corpus inicial TweetSentBR em uma lista padronizada."""
    return list(
        iterar_tweetsentbr(
            caminho=caminho,
            delimitador=delimitador,
            modo_estrito=modo_estrito,
            relatorio=relatorio,
            limite=limite,
        )
    )


def iterar_dados_aquisicao(
    caminho: str | Path = CAMINHO_PADRAO_TWEETSENTBR,
    *,
    delimitador: str = ",",
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
    limite: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Itera sobre registros de uma fonte de aquisição validando explicitamente a origem."""
    _validar_limite(limite)
    caminho_resolvido = resolver_caminho_tweetsentbr(
        caminho,
        permitir_none=False,
    )
    fluxo = iterar_dataset_csv(
        caminho_resolvido,
        delimitador=delimitador,
        modo_estrito=modo_estrito,
        relatorio=relatorio,
    )
    if limite is not None:
        yield from itertools.islice(fluxo, limite)
    else:
        yield from fluxo


def adquirir_dados(
    caminho: str | Path = CAMINHO_PADRAO_TWEETSENTBR,
    *,
    delimitador: str = ",",
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
    limite: int | None = None,
) -> list[dict[str, Any]]:
    """Executa a aquisição de textos da fonte inicial (RF02 / US02 — Issue #1).

    Quando chamado sem argumentos (``adquirir_dados()``), carrega automaticamente
    o corpus local padrão ``Datasets/tweetsent.csv`` relativo à raiz do projeto.
    Quando chamado com um caminho explícito, valida a origem e retorna os registros
    normalizados no contrato de aquisição do SentIA (rótulos ``POS``, ``NEG``, ``NEU``).
    """
    return list(
        iterar_dados_aquisicao(
            caminho=caminho,
            delimitador=delimitador,
            modo_estrito=modo_estrito,
            relatorio=relatorio,
            limite=limite,
        )
    )
