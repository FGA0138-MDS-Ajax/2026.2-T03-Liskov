"""Adaptador para importação de arquivos CSV no formato do corpus BPSAD.

Converte registros do BPSAD (Brazilian Portuguese Sentiment Analysis Dataset)
para o contrato canônico de entrada do SentIA (Issues #2, #4, #11 e #19),
com suporte a modo estrito (padrão) e modo tolerante auditável.
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

from .csv_importer import (
    RelatorioImportacao,
    _gerar_id_deterministico,
    _localizar_coluna,
    _tratar_erro_registro,
    normalizar_rotulo,
)

logger = logging.getLogger(__name__)

_COLUNAS_ID_BPSAD: tuple[str, ...] = (
    "id_origem",
    "id",
    "identificador",
    "review_id",
)
_COLUNAS_DATA_BPSAD: tuple[str, ...] = (
    "data_publicacao",
    "data",
    "review_date",
)


def iterar_bpsad(
    caminho_arquivo: str | Path,
    delimitador: str = ",",
    *,
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
) -> Iterator[dict[str, Any]]:
    """Lê um arquivo CSV no formato BPSAD e converte seus registros para o padrão SentIA.

    Mapeamento principal:
        - ``review_text`` -> ``texto_original``
        - ``rating``      -> ``rotulo_original`` (normalizado para ``positivo``/``negativo``/``neutro``)
        - ``dataset``     -> ``fonte``
        - ``id`` / ``review_id`` (se presente) -> ``id_origem`` (ou hash determinístico se ausente)

    Política de tratamento de registros incompletos/inválidos:
        - ``modo_estrito=True`` (padrão): levanta ``ValueError`` explicativo na primeira linha inválida.
        - ``modo_estrito=False`` (modo tolerante): descarta registros inválidos e contabiliza
          quantidade e motivos em ``relatorio`` (``RelatorioImportacao``) e no logger.
    """
    if relatorio is None:
        relatorio = RelatorioImportacao()

    caminho = Path(caminho_arquivo)

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    if not isinstance(delimitador, str) or len(delimitador) != 1:
        raise ValueError(
            "O delimitador deve possuir apenas um caractere."
        )

    csv.field_size_limit(2**31 - 1)

    campos_obrigatorios = {
        "dataset",
        "review_text",
    }

    contadores_por_fonte: dict[str, int] = defaultdict(int)
    ids_vistos_por_fonte: dict[str, set[str]] = defaultdict(set)

    try:
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
                raise ValueError("O CSV possui colunas duplicadas.")

            leitor.fieldnames = cabecalhos

            ausentes = campos_obrigatorios - set(cabecalhos)

            if ausentes:
                raise ValueError(
                    "Colunas obrigatórias ausentes no BPSAD: "
                    + ", ".join(sorted(ausentes))
                )

            possui_coluna_rating = "rating" in cabecalhos
            coluna_id = _localizar_coluna(cabecalhos, _COLUNAS_ID_BPSAD)
            coluna_data = _localizar_coluna(cabecalhos, _COLUNAS_DATA_BPSAD)

            colunas_mapeadas = {
                c
                for c in (
                    "dataset",
                    "review_text",
                    "rating" if possui_coluna_rating else None,
                    coluna_id,
                    coluna_data,
                )
                if c is not None
            }
            colunas_metadados = [
                c for c in cabecalhos if c not in colunas_mapeadas
            ]

            for numero_linha, linha in enumerate(leitor, start=2):
                relatorio.total_lidos += 1

                if None in linha:
                    _tratar_erro_registro(
                        modo_estrito=modo_estrito,
                        relatorio=relatorio,
                        linha=numero_linha,
                        motivo="colunas_excedentes",
                        mensagem=(
                            f"Linha {numero_linha}: "
                            "quantidade de valores maior que a de colunas."
                        ),
                    )
                    continue

                texto = linha.get("review_text")
                rotulo_bruto = (
                    linha.get("rating") if possui_coluna_rating else None
                )
                fonte = linha.get("dataset")

                if texto is None or not texto.strip():
                    _tratar_erro_registro(
                        modo_estrito=modo_estrito,
                        relatorio=relatorio,
                        linha=numero_linha,
                        motivo="texto_vazio",
                        mensagem=(
                            f"Linha {numero_linha}: o campo 'review_text' "
                            "não pode estar vazio."
                        ),
                    )
                    continue

                if fonte is None or not fonte.strip():
                    _tratar_erro_registro(
                        modo_estrito=modo_estrito,
                        relatorio=relatorio,
                        linha=numero_linha,
                        motivo="fonte_vazia",
                        mensagem=(
                            f"Linha {numero_linha}: o campo 'dataset' "
                            "não pode estar vazio."
                        ),
                    )
                    continue

                if possui_coluna_rating:
                    if rotulo_bruto is None or not rotulo_bruto.strip():
                        _tratar_erro_registro(
                            modo_estrito=modo_estrito,
                            relatorio=relatorio,
                            linha=numero_linha,
                            motivo="rotulo_vazio",
                            mensagem=(
                                f"Linha {numero_linha}: o campo 'rating' "
                                "está vazio em registro rotulado do BPSAD."
                            ),
                        )
                        continue

                    try:
                        rotulo_original: str | None = normalizar_rotulo(
                            rotulo_bruto
                        )
                    except ValueError as erro:
                        _tratar_erro_registro(
                            modo_estrito=modo_estrito,
                            relatorio=relatorio,
                            linha=numero_linha,
                            motivo="rotulo_invalido",
                            mensagem=f"Linha {numero_linha}: {erro}",
                        )
                        continue
                else:
                    rotulo_original = None

                data_bruta = (
                    linha.get(coluna_data) if coluna_data is not None else None
                )
                data_publicacao = (
                    data_bruta.strip()
                    if (data_bruta is not None and data_bruta.strip())
                    else None
                )

                fonte_limpa = fonte.strip()
                contadores_por_fonte[fonte_limpa] += 1
                posicao_na_fonte = contadores_por_fonte[fonte_limpa]

                id_bruto = (
                    linha.get(coluna_id) if coluna_id is not None else None
                )
                if id_bruto is not None and id_bruto.strip():
                    identificador = id_bruto.strip()
                    if identificador in ids_vistos_por_fonte[fonte_limpa]:
                        _tratar_erro_registro(
                            modo_estrito=modo_estrito,
                            relatorio=relatorio,
                            linha=numero_linha,
                            motivo="id_origem_duplicado",
                            mensagem=(
                                f"Linha {numero_linha}: identificador duplicado "
                                f"'{identificador}' para a fonte '{fonte_limpa}'."
                            ),
                        )
                        continue
                else:
                    identificador = _gerar_id_deterministico(
                        fonte=fonte_limpa,
                        posicao_na_fonte=posicao_na_fonte,
                        texto=texto,
                        rotulo_bruto=rotulo_bruto,
                        data_publicacao=data_publicacao,
                    )

                ids_vistos_por_fonte[fonte_limpa].add(identificador)

                registro: dict[str, Any] = {
                    "id_origem": identificador,
                    "texto_original": texto,
                    "fonte": fonte_limpa,
                    "rotulo_original": rotulo_original,
                    "data_publicacao": data_publicacao,
                }

                if colunas_metadados:
                    metadados = {
                        col: linha[col].strip()
                        for col in colunas_metadados
                        if linha.get(col) is not None and linha[col].strip()
                    }
                    if metadados:
                        registro["metadados"] = metadados

                relatorio.total_importados += 1
                yield registro

    except UnicodeDecodeError as erro:
        raise ValueError(
            "Não foi possível ler o arquivo BPSAD. "
            "Verifique se ele está codificado em UTF-8."
        ) from erro

    except csv.Error as erro:
        raise ValueError(
            f"Erro na estrutura do CSV BPSAD: {erro}"
        ) from erro

    if relatorio.total_descartados > 0:
        logger.warning(
            "Importação BPSAD (%s) concluída em modo tolerante: %d importados, "
            "%d descartados. Motivos: %s",
            caminho.name,
            relatorio.total_importados,
            relatorio.total_descartados,
            relatorio.descartes_por_motivo,
        )

    if relatorio.total_importados == 0:
        raise ValueError("O CSV BPSAD não possui registros válidos para importar.")
