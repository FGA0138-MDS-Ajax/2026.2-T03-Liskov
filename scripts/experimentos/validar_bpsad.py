"""Avaliação BPSAD. O BERTweet real é opcional e exige preparação explícita."""
import argparse
import hashlib
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from scripts.experimentos.amostrar_bpsad import CLASSES, normalizar, validar_destinos
from src.processamento.classificacao import baseline
from src.processamento.classificacao.avaliacao import avaliar


def ler_amostra(entrada):
    df = pd.read_csv(entrada, keep_default_na=False)
    if not {"review_text", "rotulo", "divisao"}.issubset(df.columns):
        raise ValueError("Amostra precisa de review_text, rotulo e divisao.")
    if df.empty or not df.review_text.map(lambda t: isinstance(t, str) and bool(t.strip())).all():
        raise ValueError("Amostra vazia ou texto inválido.")
    if not set(df.rotulo) <= set(CLASSES) or set(df.divisao) != {"treino", "teste"}:
        raise ValueError("Classes ou divisões inválidas.")
    # Rejeita vazamento e duplicatas em vez de alterar silenciosamente o experimento.
    if df.review_text.map(normalizar).duplicated().any():
        raise ValueError("Textos duplicados/conflitantes na amostra; gere nova amostra por grupos.")
    for divisao in ("treino", "teste"):
        if set(df.loc[df.divisao == divisao, "rotulo"]) != set(CLASSES):
            raise ValueError("Cada divisão deve conter as três classes.")
    return df[df.divisao == "treino"], df[df.divisao == "teste"]


def executar(entrada, *, incluir_bertweet=False, tamanho_lote=32):
    if tamanho_lote <= 0:
        raise ValueError("O tamanho de lote deve ser positivo.")
    treino, teste = ler_amostra(entrada)
    # Dependência experimental isolada; importação do módulo e --help não exigem psutil.
    import psutil

    resultado = {
        "dataset": "BPSAD", "arquivo": str(Path(entrada).resolve()),
        "sha256_amostra": hashlib.sha256(Path(entrada).read_bytes()).hexdigest(),
        "treino": len(treino), "teste": len(teste),
        "distribuicao_treino": treino.rotulo.value_counts().to_dict(),
        "distribuicao_teste": teste.rotulo.value_counts().to_dict(),
        "tamanho_lote": tamanho_lote,
        "semente_particao": "consultar JSON da amostragem; não inferida do CSV",
        "versoes": {"python": platform.python_version(), **{
            nome: version(nome) for nome in ("pandas", "scikit-learn", "psutil")}},
        "independencia_pre_treinamento": "não comprovada",
        "tempos": "wall clock inclui treino ou carregamento; comparação não controlada",
        "modelos": {},
    }
    inicio = time.perf_counter()
    modelo = baseline.criar_baseline()
    modelo.fit(treino.review_text.tolist(), treino.rotulo.tolist())
    previsto = modelo.predict(teste.review_text.tolist()).tolist()

    def registrar(nome, previsoes, inicio):
        resultado["modelos"][nome] = {
            **avaliar(teste.rotulo.tolist(), previsoes),
            "tempo_segundos": time.perf_counter() - inicio,
            "memoria_rss_gb_apos_execucao": psutil.Process().memory_info().rss / 1024**3,
        }

    registrar("baseline", previsto, inicio)
    if incluir_bertweet:
        from src.processamento.classificacao.bertweet import ClassificadorBertweet

        resultado["versoes"].update({n: version(n) for n in ("pysentimiento", "torch")})
        inicio = time.perf_counter()
        classificador = ClassificadorBertweet(tamanho_lote=tamanho_lote)
        registrar(classificador.nome_modelo, classificador.prever(teste.review_text.tolist()), inicio)
    return resultado


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=Path("data/BPSAD/amostra_exploratoria_10k.csv"))
    parser.add_argument("--saida", type=Path, default=Path("data/BPSAD/resultados_validacao_bpsad.json"))
    parser.add_argument("--bertweet", action="store_true", help="Executa modelo real; pode baixar pesos.")
    parser.add_argument("--tamanho-lote", type=int, default=32)
    args = parser.parse_args(argv)
    try:
        validar_destinos(args.entrada, args.saida)
        resultado = executar(args.entrada, incluir_bertweet=args.bertweet, tamanho_lote=args.tamanho_lote)
        with args.saida.open("x", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, ensure_ascii=False, indent=2)
    except (OSError, ValueError, ImportError) as erro:
        parser.error(f"{erro}. Dependências: uv sync --locked --group experimentos; ML: --group ml.")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
