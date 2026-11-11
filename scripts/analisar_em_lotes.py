"""Analisa um dataset CSV com o BERTweet lendo de 100 em 100 linhas.

Serve para testar a análise em máquinas com pouca memória: cada lote é lido,
classificado, gravado no CSV de saída e descartado antes do próximo. Por padrão
roda no processador (CPU), que usa menos memória que a placa de vídeo.

    uv run python scripts/analisar_em_lotes.py ../csv-teste/comentarios_teste.csv
    uv run python scripts/analisar_em_lotes.py dados.csv --limite 300 --saida resultado.csv

Requer as dependências do modelo (make setup-ml). O primeiro uso baixa o modelo.
"""

from __future__ import annotations

import argparse
import csv
import gc
import os
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from itertools import islice
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.processamento.aquisicao import RelatorioImportacao, iterar_dataset_csv
from src.processamento.classificacao.rotulos import ROTULOS

TAMANHO_LOTE = 100
COLUNAS_SAIDA = [
    "id_origem",
    "fonte",
    "texto",
    "sentimento",
    *(f"prob_{rotulo}" for rotulo in ROTULOS),
    "data_publicacao",
]


@dataclass
class Resumo:
    lotes: int = 0
    analisados: int = 0
    por_sentimento: Counter = field(default_factory=Counter)


def lotes(
    registros: Iterable[dict[str, Any]], tamanho: int
) -> Iterator[list[dict[str, Any]]]:
    """Agrupa os registros em listas de até ``tamanho`` itens, sem ler o resto do arquivo."""
    iterador = iter(registros)
    while lote := list(islice(iterador, tamanho)):
        yield lote


def _linha(documento: dict[str, Any]) -> list[Any]:
    data = documento.get("data_publicacao")
    probabilidades = documento["probabilidades"]
    return [
        documento["id_origem"],
        documento["fonte"],
        documento["texto_original"],
        documento["sentimento"],
        *(f"{probabilidades[rotulo]:.4f}" for rotulo in ROTULOS),
        data.isoformat() if data else "",
    ]


def analisar_em_lotes(
    registros: Iterable[dict[str, Any]],
    pipeline: Any,
    saida: Path,
    *,
    tamanho_lote: int = TAMANHO_LOTE,
    limite: int | None = None,
    ao_concluir_lote: Callable[[int, int, Counter], None] | None = None,
) -> Resumo:
    """Classifica os registros lote a lote e grava cada lote em ``saida`` assim que termina."""
    if tamanho_lote <= 0:
        raise ValueError("O tamanho do lote deve ser maior que zero.")
    if limite is not None:
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")
        registros = islice(registros, limite)

    resumo = Resumo()
    with saida.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(COLUNAS_SAIDA)
        for lote in lotes(registros, tamanho_lote):
            documentos = pipeline.processar_registros(lote)
            contagem = Counter(d["sentimento"] for d in documentos)
            escritor.writerows(_linha(d) for d in documentos)
            arquivo.flush()

            resumo.lotes += 1
            resumo.analisados += len(documentos)
            resumo.por_sentimento.update(contagem)
            if ao_concluir_lote:
                ao_concluir_lote(resumo.lotes, resumo.analisados, contagem)
            del lote, documentos
            gc.collect()
    return resumo


def memoria_do_processo_mb() -> int | None:
    """Memória usada agora pelo processo (Linux); None quando não dá para medir."""
    try:
        with open("/proc/self/status", encoding="utf-8") as status:
            for linha in status:
                if linha.startswith("VmRSS:"):
                    return int(linha.split()[1]) // 1024
    except OSError:
        return None
    return None


def _descrever(contagem: Counter) -> str:
    return " · ".join(f"{rotulo} {contagem.get(rotulo, 0)}" for rotulo in ROTULOS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analisa um CSV com o BERTweet, de 100 em 100 linhas."
    )
    parser.add_argument(
        "csv", type=Path, help="dataset CSV no formato do importador do SentIA"
    )
    parser.add_argument(
        "--saida", type=Path, help="CSV de resultado (padrão: <nome>_analisado.csv)"
    )
    parser.add_argument(
        "--lote",
        type=int,
        default=TAMANHO_LOTE,
        help="linhas lidas por vez (padrão: 100)",
    )
    parser.add_argument(
        "--lote-modelo",
        type=int,
        default=8,
        help="textos enviados juntos ao modelo; menor usa menos memória (padrão: 8)",
    )
    parser.add_argument(
        "--limite", type=int, help="para depois de N linhas (padrão: o arquivo todo)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=2,
        help="núcleos do processador usados pelo modelo (padrão: 2)",
    )
    parser.add_argument(
        "--delimitador", default=",", help="separador de colunas (padrão: ,)"
    )
    parser.add_argument(
        "--estrito",
        action="store_true",
        help="para na primeira linha inválida, em vez de descartá-la",
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="usa a placa de vídeo; com 4 GB ou menos pode faltar memória",
    )
    args = parser.parse_args()

    if not args.gpu:
        # Precisa vir antes de importar o torch, que o modelo carrega.
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    saida = args.saida or args.csv.with_name(f"{args.csv.stem}_analisado.csv")
    if saida.resolve() == args.csv.resolve():
        print("Erro: o arquivo de saída não pode ser o próprio CSV.", file=sys.stderr)
        return 1

    try:
        import torch

        from src.processamento.pipeline import PipelineClassificacao
    except ImportError:
        print(
            "Erro: faltam as dependências do modelo. Rode: make setup-ml",
            file=sys.stderr,
        )
        return 1
    torch.set_num_threads(max(1, args.threads))

    print(
        f"Carregando o BERTweet ({'GPU' if args.gpu else 'CPU'}, {args.threads} thread(s))..."
    )
    inicio = time.monotonic()
    try:
        pipeline = PipelineClassificacao(tamanho_lote=args.lote_modelo)
    except (OSError, RuntimeError, ValueError) as erro:  # download ou carga do modelo
        print(f"Erro ao carregar o modelo: {erro}", file=sys.stderr)
        return 1
    print(
        f"Modelo pronto em {time.monotonic() - inicio:.0f} s. Memória: {memoria_do_processo_mb()} MB\n"
    )

    def mostrar(numero: int, total: int, contagem: Counter) -> None:
        print(
            f"Lote {numero}: {total} texto(s) analisado(s) | {_descrever(contagem)} "
            f"| memória {memoria_do_processo_mb()} MB"
        )

    relatorio = RelatorioImportacao()
    registros = iterar_dataset_csv(
        args.csv, args.delimitador, modo_estrito=args.estrito, relatorio=relatorio
    )
    try:
        resumo = analisar_em_lotes(
            registros,
            pipeline,
            saida,
            tamanho_lote=args.lote,
            limite=args.limite,
            ao_concluir_lote=mostrar,
        )
    except (OSError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"\nInterrompido. O que já foi analisado está em {saida}.")
        return 130

    if resumo.analisados == 0:
        print("Nenhum texto válido para analisar.")
        return 1
    print(
        f"\nConcluído em {time.monotonic() - inicio:.0f} s: {resumo.analisados} texto(s) "
        f"em {resumo.lotes} lote(s) | {_descrever(resumo.por_sentimento)}"
    )
    if relatorio.total_descartados:
        print(
            f"{relatorio.total_descartados} linha(s) descartada(s) por serem inválidas."
        )
    print(f"Resultado salvo em {saida}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
