"""Importação padronizada de arquivos CSV para o pipeline do SentIA.

Implementa o contrato canônico de entrada de dados alinhado às Issues #2, #4, #11 e #19:
- Preserva identificadores originais (`id_origem`, `id`, `identificador`) quando fornecidos;
- Gera identificadores determinísticos baseados em SHA-256 e posição por fonte quando ausentes;
- Normaliza rótulos humanos/de datasets para `positivo`, `negativo` e `neutro` em `rotulo_original`;
- Suporta datasets não rotulados (`rotulo_original = None`), sem atribuir `sentimento` previsto;
- Oferece modo estrito (padrão) e modo tolerante com contabilização auditável de descartes.
"""

from __future__ import annotations

import csv
import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

ROTULOS_PADRONIZADOS: tuple[str, ...] = ("positivo", "negativo", "neutro")

_COLUNAS_ID: tuple[str, ...] = ("id_origem", "id", "identificador")
_COLUNAS_TEXTO: tuple[str, ...] = ("texto_original", "texto")
_COLUNAS_FONTE: tuple[str, ...] = ("fonte",)
_COLUNAS_ROTULO: tuple[str, ...] = ("rotulo_original", "rotulo", "sentimento")
_COLUNAS_DATA: tuple[str, ...] = ("data_publicacao", "data")


@dataclass
class RelatorioImportacao:
    """Contabiliza registros lidos, importados e descartados durante a importação."""

    total_lidos: int = 0
    total_importados: int = 0
    total_descartados: int = 0
    descartes_por_motivo: dict[str, int] = field(default_factory=dict)
    detalhes_descartes: list[dict[str, Any]] = field(default_factory=list)

    def registrar_descarte(self, linha: int, motivo: str, mensagem: str) -> None:
        """Registra um descarte em modo tolerante com número da linha, categoria e detalhe."""
        self.total_descartados += 1
        self.descartes_por_motivo[motivo] = (
            self.descartes_por_motivo.get(motivo, 0) + 1
        )
        self.detalhes_descartes.append(
            {
                "linha": linha,
                "motivo": motivo,
                "mensagem": mensagem,
            }
        )


def normalizar_rotulo(rotulo: object) -> str:
    """Converte rótulos textuais (PT/EN/siglas) ou notas de 1 a 5 para o padrão do SentIA.

    Retorna exclusivamente ``"positivo"``, ``"negativo"`` ou ``"neutro"``.
    """
    if rotulo is None or isinstance(rotulo, bool):
        raise ValueError(f"Rótulo inválido: {rotulo!r}")

    rotulo_str = str(rotulo).strip().lower()
    if not rotulo_str:
        raise ValueError(f"Rótulo inválido: {rotulo!r}")

    mapeamento = {
        "negativo": "negativo",
        "negative": "negativo",
        "neg": "negativo",
        "neutro": "neutro",
        "neutral": "neutro",
        "neu": "neutro",
        "positivo": "positivo",
        "positive": "positivo",
        "pos": "positivo",
    }

    if rotulo_str in mapeamento:
        return mapeamento[rotulo_str]

    try:
        nota = Decimal(rotulo_str)
    except InvalidOperation as erro:
        raise ValueError(f"Rótulo inválido: {rotulo}") from erro

    if not nota.is_finite() or nota < 1 or nota > 5:
        raise ValueError(f"Nota fora do intervalo de 1 a 5: {rotulo}")

    if nota < Decimal("2.5"):
        return "negativo"

    if nota < Decimal("3.5"):
        return "neutro"

    return "positivo"


def _normalizar_fonte_para_id(fonte: str) -> str:
    fonte_id = re.sub(r"[^A-Za-z0-9_-]+", "_", fonte.strip())
    return fonte_id.strip("_-") or "FONTE"


def _gerar_id_deterministico(
    fonte: str,
    posicao_na_fonte: int,
    texto: str,
    rotulo_bruto: str | None = None,
    data_publicacao: str | None = None,
) -> str:
    """Gera identificador estável sem usar UUID aleatório ou timestamps.

    Combina a fonte normalizada, o índice sequencial do registro dentro da fonte e
    um digest SHA-256 curto do conteúdo, garantindo reprodutibilidade entre
    importações repetidas e evitando colisão entre registros distintos com textos iguais.
    """
    fonte_id = _normalizar_fonte_para_id(fonte)
    base_hash = (
        f"{fonte.strip()}\x1f"
        f"{posicao_na_fonte}\x1f"
        f"{texto.strip()}\x1f"
        f"{(rotulo_bruto or '').strip()}\x1f"
        f"{(data_publicacao or '').strip()}"
    )
    digest = hashlib.sha256(base_hash.encode("utf-8")).hexdigest()[:12]
    return f"{fonte_id}_{posicao_na_fonte:06d}_{digest}"


def _localizar_coluna(
    cabecalhos: list[str],
    candidatas: tuple[str, ...],
) -> str | None:
    conjunto = set(cabecalhos)
    for nome in candidatas:
        if nome in conjunto:
            return nome
    return None


def _tratar_erro_registro(
    *,
    modo_estrito: bool,
    relatorio: RelatorioImportacao,
    linha: int,
    motivo: str,
    mensagem: str,
) -> None:
    if modo_estrito:
        raise ValueError(mensagem)
    relatorio.registrar_descarte(linha=linha, motivo=motivo, mensagem=mensagem)


def _iterar_csv_padrao(
    caminho: Path,
    delimitador: str,
    *,
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
) -> Iterator[dict[str, Any]]:
    """Lê CSVs no padrão de entrada do SentIA em fluxo (streaming)."""
    if relatorio is None:
        relatorio = RelatorioImportacao()

    contadores_por_fonte: dict[str, int] = defaultdict(int)
    ids_vistos_por_fonte: dict[str, set[str]] = defaultdict(set)

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

        coluna_texto = _localizar_coluna(cabecalhos, _COLUNAS_TEXTO)
        coluna_fonte = _localizar_coluna(cabecalhos, _COLUNAS_FONTE)

        ausentes: list[str] = []
        if coluna_texto is None:
            ausentes.append("texto")
        if coluna_fonte is None:
            ausentes.append("fonte")

        if ausentes:
            raise ValueError(
                "Colunas obrigatórias ausentes: "
                + ", ".join(sorted(ausentes))
            )

        coluna_id = _localizar_coluna(cabecalhos, _COLUNAS_ID)
        coluna_rotulo = _localizar_coluna(cabecalhos, _COLUNAS_ROTULO)
        coluna_data = _localizar_coluna(cabecalhos, _COLUNAS_DATA)

        colunas_mapeadas = {
            c
            for c in (
                coluna_texto,
                coluna_fonte,
                coluna_id,
                coluna_rotulo,
                coluna_data,
            )
            if c is not None
        }
        colunas_metadados = [
            c for c in cabecalhos if c not in colunas_mapeadas
        ]

        for numero, linha in enumerate(leitor, start=2):
            relatorio.total_lidos += 1

            if None in linha:
                _tratar_erro_registro(
                    modo_estrito=modo_estrito,
                    relatorio=relatorio,
                    linha=numero,
                    motivo="colunas_excedentes",
                    mensagem=(
                        f"Registro {numero}: quantidade de valores "
                        "maior que a de colunas."
                    ),
                )
                continue

            texto = linha.get(coluna_texto) if coluna_texto else None
            fonte = linha.get(coluna_fonte) if coluna_fonte else None

            if (
                texto is None
                or not texto.strip()
                or fonte is None
                or not fonte.strip()
            ):
                motivo = (
                    "texto_vazio"
                    if (texto is None or not texto.strip())
                    else "fonte_vazia"
                )
                _tratar_erro_registro(
                    modo_estrito=modo_estrito,
                    relatorio=relatorio,
                    linha=numero,
                    motivo=motivo,
                    mensagem=(
                        f"Registro {numero}: texto e fonte "
                        "não podem estar vazios."
                    ),
                )
                continue

            rotulo_bruto = (
                linha.get(coluna_rotulo) if coluna_rotulo is not None else None
            )
            if rotulo_bruto is not None and rotulo_bruto.strip():
                try:
                    rotulo_original: str | None = normalizar_rotulo(rotulo_bruto)
                except ValueError as erro:
                    _tratar_erro_registro(
                        modo_estrito=modo_estrito,
                        relatorio=relatorio,
                        linha=numero,
                        motivo="rotulo_invalido",
                        mensagem=f"Registro {numero}: {erro}",
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

            id_bruto = linha.get(coluna_id) if coluna_id is not None else None
            if id_bruto is not None and id_bruto.strip():
                identificador = id_bruto.strip()
                if identificador in ids_vistos_por_fonte[fonte_limpa]:
                    _tratar_erro_registro(
                        modo_estrito=modo_estrito,
                        relatorio=relatorio,
                        linha=numero,
                        motivo="id_origem_duplicado",
                        mensagem=(
                            f"Registro {numero}: identificador duplicado "
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

    if relatorio.total_descartados > 0:
        logger.warning(
            "Importação CSV (%s) concluída em modo tolerante: %d importados, "
            "%d descartados. Motivos: %s",
            caminho.name,
            relatorio.total_importados,
            relatorio.total_descartados,
            relatorio.descartes_por_motivo,
        )

    if relatorio.total_importados == 0:
        raise ValueError("O CSV não possui registros para importar.")


def iterar_dataset_csv(
    caminho_arquivo: str | Path,
    delimitador: str = ",",
    *,
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
) -> Iterator[dict[str, Any]]:
    """Identifica automaticamente o formato do CSV e importa os registros em fluxo.

    Formatos aceitos:
        - SentIA: ``texto`` (ou ``texto_original``), ``fonte`` e colunas opcionais
          (``id_origem``/``id``/``identificador``, ``rotulo_original``/``rotulo``/``sentimento``,
          ``data_publicacao``/``data`` e metadados extras).
        - BPSAD: ``review_text``, ``dataset`` e ``rating`` (opcional para inferência).

    Args:
        caminho_arquivo: Caminho para o arquivo CSV codificado em UTF-8.
        delimitador: Caractere separador de colunas (padrão ``","``).
        modo_estrito: Se ``True`` (padrão), interrompe imediatamente com ``ValueError``
            ao encontrar qualquer registro inválido ou duplicado. Se ``False``,
            descarta registros inválidos contabilizando-os em ``relatorio``.
        relatorio: Objeto opcional ``RelatorioImportacao`` preenchido durante a leitura.
    """
    if caminho_arquivo is None or (
        isinstance(caminho_arquivo, str) and not caminho_arquivo.strip()
    ):
        raise ValueError("O caminho do arquivo CSV não pode ser vazio.")

    caminho = Path(caminho_arquivo)

    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if not isinstance(delimitador, str) or len(delimitador) != 1:
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

        if "" in cabecalhos:
            raise ValueError("O CSV possui uma coluna sem nome.")

        if len(cabecalhos) != len(set(cabecalhos)):
            raise ValueError("O CSV possui nomes de colunas duplicados.")

        campos = set(cabecalhos)

        if "review_text" in campos or "dataset" in campos:
            from .bpsad_adapter import iterar_bpsad

            yield from iterar_bpsad(
                caminho,
                delimitador=delimitador,
                modo_estrito=modo_estrito,
                relatorio=relatorio,
            )
        else:
            yield from _iterar_csv_padrao(
                caminho,
                delimitador,
                modo_estrito=modo_estrito,
                relatorio=relatorio,
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
    *,
    modo_estrito: bool = True,
    relatorio: RelatorioImportacao | None = None,
) -> list[dict[str, Any]]:
    """Importa o CSV e retorna todos os registros válidos em uma lista.

    Para arquivos grandes, prefira ``iterar_dataset_csv()``.
    """
    registros = list(
        iterar_dataset_csv(
            caminho_arquivo,
            delimitador,
            modo_estrito=modo_estrito,
            relatorio=relatorio,
        )
    )

    if not registros:
        raise ValueError("O CSV não possui registros para importar.")

    return registros


# Aliases de compatibilidade com a suíte de contrato da Issue #4
importar_csv = importar_dataset_csv
adquirir_dados = importar_dataset_csv
