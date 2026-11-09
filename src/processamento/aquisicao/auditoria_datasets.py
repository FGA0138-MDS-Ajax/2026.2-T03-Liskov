"""Auditoria reprodutível de datasets de aquisição e avaliação (Issue #3 / Issue #4).

Executa inspeção programática em fluxo (streaming) sobre arquivos CSV compatíveis
com o SentIA (padrão TweetSentBR ou BPSAD), calculando:
- Hash SHA-256, tamanho em bytes e codificação UTF-8 / UTF-8-SIG (BOM);
- Total de registros lidos, importados e descartados (por motivo);
- Contagem e proporção percentual por classe (`POS`, `NEG`, `NEU` e não rotulados);
- Presença de IDs originais na fonte e datas de publicação;
- Duplicatas exatas e normalizadas, destacando grupos com rótulos conflitantes
  por meio de `id_origem` estável e hash curto do texto (sem expor textos brutos
  de usuários em relatórios públicos).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .csv_importer import (
     _COLUNAS_DATA,
    _COLUNAS_ID,
    RelatorioImportacao,
    iterar_dataset_csv,
)
from .tweetsentbr import CAMINHO_PADRAO_TWEETSENTBR, resolver_caminho_tweetsentbr

_COLUNAS_ID_TODAS: set[str] = set(_COLUNAS_ID) | {"review_id"}
_COLUNAS_DATA_TODAS: set[str] = set(_COLUNAS_DATA) | {"review_date"}


@dataclass
class ResumoDuplicatas:
    """Métricas agregadas e identificação estável de duplicatas e conflitos."""

    textos_unicos: int = 0
    grupos_duplicados: int = 0
    ocorrencias_excedentes: int = 0
    registros_envolvidos: int = 0
    grupos_conflitantes: int = 0
    conflitos: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RelatorioAuditoriaDataset:
    """Resultado completo e auditável da inspeção de um dataset CSV."""

    caminho: str
    nome_arquivo: str
    tamanho_bytes: int
    sha256: str
    codificacao: str
    colunas: list[str]
    possui_coluna_id_original: bool
    possui_coluna_data: bool
    possui_coluna_split: bool
    total_lidos: int
    total_importados: int
    total_descartados: int
    descartes_por_motivo: dict[str, int]
    contagem_por_classe: dict[str, int]
    proporcao_por_classe: dict[str, float]
    contagem_rotulo_original: dict[str, int]
    datas_preenchidas: int
    duplicatas_exatas: ResumoDuplicatas
    duplicatas_normalizadas: ResumoDuplicatas

    def para_dict(self) -> dict[str, Any]:
        """Converte o relatório para dicionário serializável em JSON."""
        return asdict(self)


def calcular_sha256_arquivo(caminho: str | Path, tamanho_bloco: int = 65536) -> str:
    """Calcula o digest SHA-256 de um arquivo em blocos sem carregá-lo inteiro em RAM."""
    caminho_path = Path(caminho)
    hasher = hashlib.sha256()
    with caminho_path.open("rb") as arquivo:
        while bloco := arquivo.read(tamanho_bloco):
            hasher.update(bloco)
    return hasher.hexdigest()


def detectar_codificacao_utf8(caminho: str | Path) -> str:
    """Detecta se o arquivo está em UTF-8 puro ou UTF-8-SIG (com BOM)."""
    caminho_path = Path(caminho)
    with caminho_path.open("rb") as arquivo:
        prefixo = arquivo.read(3)
    return "UTF-8-SIG" if prefixo == b"\xef\xbb\xbf" else "UTF-8"


def _normalizar_texto_para_duplicata(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.strip().lower())


def _hash_curto_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def _inspecionar_cabecalho(caminho: Path, delimitador: str = ",") -> list[str]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo, delimiter=delimitador, strict=True)
        cabecalhos = next(leitor, None)
        if not cabecalhos:
            return []
        return [col.strip().lower() for col in cabecalhos if col is not None]


def _consolidar_duplicatas(
    mapa_ocorrencias: dict[str, list[tuple[int, str, str | None]]],
) -> ResumoDuplicatas:
    grupos_dup = {k: v for k, v in mapa_ocorrencias.items() if len(v) > 1}
    ocorrencias_excedentes = sum(len(v) - 1 for v in grupos_dup.values())
    registros_envolvidos = sum(len(v) for v in grupos_dup.values())

    conflitos: list[dict[str, Any]] = []
    for hash_texto, ocorrencias in grupos_dup.items():
        rotulos = sorted({rot or "SEM_ROTULO" for _, _, rot in ocorrencias})
        if len(rotulos) > 1:
            conflitos.append(
                {
                    "hash_texto": hash_texto,
                    "rotulos_distintos": rotulos,
                    "ocorrencias": [
                        {
                            "posicao": pos,
                            "id_origem": id_orig,
                            "rotulo_padronizado": rot,
                        }
                        for pos, id_orig, rot in ocorrencias
                    ],
                }
            )

    return ResumoDuplicatas(
        textos_unicos=len(mapa_ocorrencias),
        grupos_duplicados=len(grupos_dup),
        ocorrencias_excedentes=ocorrencias_excedentes,
        registros_envolvidos=registros_envolvidos,
        grupos_conflitantes=len(conflitos),
        conflitos=conflitos,
    )


def auditar_dataset_csv(
    caminho: str | Path | None = None,
    *,
    delimitador: str = ",",
    rastrear_duplicatas: bool = True,
) -> RelatorioAuditoriaDataset:
    """Executa auditoria completa e em streaming sobre um arquivo CSV."""
    caminho_resolvido = resolver_caminho_tweetsentbr(
        caminho,
        permitir_none=True,
    )
    sha256 = calcular_sha256_arquivo(caminho_resolvido)
    codificacao = detectar_codificacao_utf8(caminho_resolvido)
    tamanho_bytes = caminho_resolvido.stat().st_size
    colunas = _inspecionar_cabecalho(caminho_resolvido, delimitador=delimitador)
    conjunto_colunas = set(colunas)

    relatorio_importacao = RelatorioImportacao()
    contagem_classe: Counter[str] = Counter()
    contagem_original: Counter[str] = Counter()
    datas_preenchidas = 0

    mapa_exato: dict[str, list[tuple[int, str, str | None]]] = defaultdict(list)
    mapa_norm: dict[str, list[tuple[int, str, str | None]]] = defaultdict(list)

    for indice, registro in enumerate(
        iterar_dataset_csv(
            caminho_resolvido,
            delimitador=delimitador,
            modo_estrito=False,
            relatorio=relatorio_importacao,
        ),
        start=1,
    ):
        rotulo_pad = registro.get("rotulo_padronizado") or "SEM_ROTULO"
        rotulo_orig = registro.get("rotulo_original") or "SEM_ROTULO"
        contagem_classe[rotulo_pad] += 1
        contagem_original[rotulo_orig] += 1

        if registro.get("data_publicacao") is not None:
            datas_preenchidas += 1

        if rastrear_duplicatas:
            texto = registro["texto_original"]
            id_origem = registro["id_origem"]
            hash_exato = _hash_curto_texto(texto)
            hash_norm = _hash_curto_texto(_normalizar_texto_para_duplicata(texto))
            mapa_exato[hash_exato].append((indice, id_origem, registro.get("rotulo_padronizado")))
            mapa_norm[hash_norm].append((indice, id_origem, registro.get("rotulo_padronizado")))

    total_imp = relatorio_importacao.total_importados
    proporcao_por_classe = {
        classe: round((qtd / total_imp) * 100.0, 2) if total_imp > 0 else 0.0
        for classe, qtd in contagem_classe.items()
    }

    resumo_exatas = (
        _consolidar_duplicatas(mapa_exato)
        if rastrear_duplicatas
        else ResumoDuplicatas()
    )
    resumo_norm = (
        _consolidar_duplicatas(mapa_norm)
        if rastrear_duplicatas
        else ResumoDuplicatas()
    )

    return RelatorioAuditoriaDataset(
        caminho=str(caminho_resolvido),
        nome_arquivo=caminho_resolvido.name,
        tamanho_bytes=tamanho_bytes,
        sha256=sha256,
        codificacao=codificacao,
        colunas=colunas,
        possui_coluna_id_original=bool(conjunto_colunas & _COLUNAS_ID_TODAS),
        possui_coluna_data=bool(conjunto_colunas & _COLUNAS_DATA_TODAS),
        possui_coluna_split="split" in conjunto_colunas or "particao" in conjunto_colunas,
        total_lidos=relatorio_importacao.total_lidos,
        total_importados=relatorio_importacao.total_importados,
        total_descartados=relatorio_importacao.total_descartados,
        descartes_por_motivo=dict(relatorio_importacao.descartes_por_motivo),
        contagem_por_classe=dict(contagem_classe),
        proporcao_por_classe=proporcao_por_classe,
        contagem_rotulo_original=dict(contagem_original),
        datas_preenchidas=datas_preenchidas,
        duplicatas_exatas=resumo_exatas,
        duplicatas_normalizadas=resumo_norm,
    )


def main(argv: list[str] | None = None) -> int:
    """Interface de linha de comando para auditoria reprodutível de datasets."""
    parser = argparse.ArgumentParser(
        description="Auditoria reprodutível de datasets CSV do SentIA (TweetSentBR / BPSAD)."
    )
    parser.add_argument(
        "caminho",
        nargs="?",
        default=str(CAMINHO_PADRAO_TWEETSENTBR),
        help="Caminho para o arquivo CSV a auditar (padrão: Datasets/tweetsent.csv).",
    )
    parser.add_argument(
        "--delimitador",
        default=",",
        help="Delimitador de colunas do CSV (padrão: ',').",
    )
    parser.add_argument(
        "--sem-duplicatas",
        action="store_true",
        help="Desativa rastreamento de duplicatas em memória para arquivos gigantes.",
    )
    args = parser.parse_args(argv)

    relatorio = auditar_dataset_csv(
        args.caminho,
        delimitador=args.delimitador,
        rastrear_duplicatas=not args.sem_duplicatas,
    )
    print(json.dumps(relatorio.para_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
