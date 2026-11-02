
import csv
import uuid

from collections import defaultdict
from pathlib import Path
from typing import Iterator

from .csv_importer import (
    normalizar_rotulo,
    _normalizar_fonte_para_id,
)


def iterar_bpsad(
    caminho_arquivo: str | Path,
    delimitador: str = ",",
) -> Iterator[dict[str, str]]:
    
    """
    Lê o BPSAD original e converte seus registros
    para o formato padronizado do SentIA.

    Campos utilizados:
        review_text -> texto_original
        rating      -> rotulo_original
        dataset     -> fonte
    """

    caminho = Path(caminho_arquivo)

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    csv.field_size_limit(2**31 - 1)

    campos_obrigatorios = {
        "dataset",
        "review_text",
        "rating",
    }

    lote_id = uuid.uuid4().hex
    contadores_por_fonte = defaultdict(int)

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

        if len(cabecalhos) != len(set(cabecalhos)):
            raise ValueError("O CSV possui colunas duplicadas.")

        leitor.fieldnames = cabecalhos

        ausentes = campos_obrigatorios - set(cabecalhos)

        if ausentes:
            raise ValueError(
                "Colunas obrigatórias ausentes no BPSAD: "
                + ", ".join(sorted(ausentes))
            )

        for numero_linha, linha in enumerate(leitor, start=2):

            if None in linha:
                raise ValueError(
                    f"Linha {numero_linha}: "
                    "quantidade de valores maior que a de colunas."
                )

            texto = linha.get("review_text")
            rotulo = linha.get("rating")
            fonte = linha.get("dataset")

            if (
                texto is None or not texto.strip()
                or rotulo is None or not rotulo.strip()
                or fonte is None or not fonte.strip()
            ):
                continue

            try:
                rotulo_padronizado = normalizar_rotulo(rotulo)
            except ValueError as erro:
                raise ValueError(
                    f"Linha {numero_linha}: {erro}"
                ) from erro

            fonte = fonte.strip()

            contadores_por_fonte[fonte] += 1
            fonte_id = _normalizar_fonte_para_id(fonte)

            identificador = (
                f"{fonte_id}_{lote_id}_"
                f"{contadores_por_fonte[fonte]:06d}"
            )

            yield {
                "id": identificador,
                "texto_original": texto,
                "rotulo_original": rotulo,
                "rotulo_padronizado": rotulo_padronizado,
                "fonte": fonte,
            }
