
import csv
import re
import uuid

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator


def normalizar_rotulo(rotulo: object) -> str:
    rotulo_str = str(rotulo).strip().lower()

    mapeamento = {
        "negativo": "NEG",
        "negative": "NEG",
        "neg": "NEG",
        "neutro": "NEU",
        "neutral": "NEU",
        "neu": "NEU",
        "positivo": "POS",
        "positive": "POS",
        "pos": "POS",
    }

    if rotulo_str in mapeamento:
        return mapeamento[rotulo_str]

    try:
        nota = Decimal(rotulo_str)
    except InvalidOperation:
        raise ValueError(f"Rótulo inválido: {rotulo}")

    if not nota.is_finite() or nota < 1 or nota > 5:
        raise ValueError(f"Nota fora do intervalo de 1 a 5: {rotulo}")

    if nota < Decimal("2.5"):
        return "NEG"

    if nota < Decimal("3.5"):
        return "NEU"

    return "POS"


def _normalizar_fonte_para_id(fonte: str) -> str:
    fonte_id = re.sub(r"[^A-Za-z0-9_-]+", "_", fonte.strip())
    return fonte_id.strip("_-") or "FONTE"


def _iterar_csv_padrao(
    caminho: Path,
    delimitador: str,
) -> Iterator[dict[str, str]]:
    """Lê CSVs que já utilizam o padrão de entrada do SentIA."""

    campos_obrigatorios = {"texto", "rotulo", "fonte"}
    contadores_por_fonte = defaultdict(int)
    lote_id = uuid.uuid4().hex
    total = 0

    with caminho.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:

        leitor = csv.DictReader(
            arquivo,
            delimiter=delimitador,
            strict=True,
        )

        if leitor.fieldnames is None:
            raise ValueError("O arquivo CSV está vazio.")

        cabecalhos = [
            nome.strip().lower() if nome else ""
            for nome in leitor.fieldnames
        ]

        if "" in cabecalhos:
            raise ValueError("O CSV possui uma coluna sem nome.")

        if len(cabecalhos) != len(set(cabecalhos)):
            raise ValueError("O CSV possui nomes de colunas duplicados.")

        leitor.fieldnames = cabecalhos

        ausentes = campos_obrigatorios - set(cabecalhos)

        if ausentes:
            raise ValueError(
                "Colunas obrigatórias ausentes: "
                + ", ".join(sorted(ausentes))
            )

        for numero, linha in enumerate(leitor, start=2):

            if None in linha:
                raise ValueError(
                    f"Registro {numero}: quantidade de valores "
                    "maior que a de colunas."
                )

            texto = linha.get("texto")
            rotulo = linha.get("rotulo")
            fonte = linha.get("fonte")

            if (
                texto is None or not texto.strip()
                or rotulo is None or not rotulo.strip()
                or fonte is None or not fonte.strip()
            ):
                raise ValueError(
                    f"Registro {numero}: texto, rotulo e fonte "
                    "não podem estar vazios."
                )

            try:
                rotulo_padronizado = normalizar_rotulo(rotulo)
            except ValueError as erro:
                raise ValueError(
                    f"Registro {numero}: {erro}"
                ) from erro

            fonte = fonte.strip()
            contadores_por_fonte[fonte] += 1

            identificador = (
                f"{_normalizar_fonte_para_id(fonte)}_"
                f"{lote_id}_"
                f"{contadores_por_fonte[fonte]:06d}"
            )

            total += 1

            yield {
                "id": identificador,
                "texto_original": texto,
                "rotulo_original": rotulo,
                "rotulo_padronizado": rotulo_padronizado,
                "fonte": fonte,
            }

    if total == 0:
        raise ValueError("O CSV não possui registros para importar.")


def iterar_dataset_csv(
    caminho_arquivo: str | Path,
    delimitador: str = ",",
) -> Iterator[dict[str, str]]:
    """
    Identifica automaticamente o formato do CSV e importa
    os registros em fluxo.

    Formatos aceitos:
        SentIA: texto, rotulo, fonte
        BPSAD: review_text, rating, dataset
    """

    caminho = Path(caminho_arquivo)

    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if len(delimitador) != 1:
        raise ValueError(
            "O delimitador deve possuir apenas um caractere."
        )

    try:
        with caminho.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as arquivo:

            leitor = csv.reader(
                arquivo,
                delimiter=delimitador,
                strict=True,
            )

            cabecalhos = next(leitor, None)

            if cabecalhos is None:
                raise ValueError("O arquivo CSV está vazio.")

            cabecalhos = [
                nome.strip().lower() if nome else ""
                for nome in cabecalhos
            ]

        if len(cabecalhos) != len(set(cabecalhos)):
            raise ValueError("O CSV possui nomes de colunas duplicados.")

        # Identifica automaticamente o formato.
        campos = set(cabecalhos)

        if {"review_text", "rating", "dataset"}.issubset(campos):
            from .bpsad_adapter import iterar_bpsad

            yield from iterar_bpsad(
                caminho,
                delimitador=delimitador,
            )

        else:
            yield from _iterar_csv_padrao(
                caminho,
                delimitador,
            )

    except UnicodeDecodeError as erro:
        raise ValueError(
            "Não foi possível ler o arquivo. "
            "Verifique se ele está codificado em UTF-8."
        ) from erro

    except csv.Error as erro:
        raise ValueError(
            f"Erro na estrutura do CSV: {erro}"
        ) from erro


def importar_dataset_csv(
    caminho_arquivo: str | Path,
    delimitador: str = ",",
) -> list[dict[str, str]]:
    """
    Importa o CSV e retorna todos os registros em uma lista.

    Para arquivos grandes, prefira iterar_dataset_csv().
    """

    registros = list(
        iterar_dataset_csv(caminho_arquivo, delimitador)
    )

    if not registros:
        raise ValueError("O CSV não possui registros para importar.")

    return registros
