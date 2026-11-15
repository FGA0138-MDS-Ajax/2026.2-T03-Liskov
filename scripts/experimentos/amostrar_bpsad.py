"""Amostragem exploratória por grupos únicos, sem carregar o corpus na memória.

Execute: uv run python -m scripts.experimentos.amostrar_bpsad --help
"""

import argparse
import json
import math
import platform
import random
import re
import sqlite3
import unicodedata
from contextlib import closing
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from sklearn.model_selection import train_test_split

CLASSES = ("negativo", "neutro", "positivo")


def normalizar(texto):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", texto).casefold()).strip()


def rotulo(rating):
    try:
        nota = float(rating)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(nota) or nota not in (1, 2, 3, 4, 5):
        return None
    return "negativo" if nota <= 2 else "neutro" if nota == 3 else "positivo"


def _cotas(contagens, tamanho):
    """Aproxima proporções com tamanho exato e ao menos dois grupos por classe."""
    if set(contagens) != set(CLASSES) or any(n < 2 for n in contagens.values()):
        raise ValueError("São necessários ao menos dois textos únicos por cada uma das três classes.")
    if tamanho < 6 or tamanho > sum(contagens.values()):
        raise ValueError("Tamanho deve estar entre 6 e o total de grupos válidos.")
    ideais = {c: tamanho * contagens[c] / sum(contagens.values()) for c in CLASSES}
    cotas = {c: min(contagens[c], max(2, math.floor(ideais[c]))) for c in CLASSES}
    while sum(cotas.values()) < tamanho:
        candidatas = [c for c in CLASSES if cotas[c] < contagens[c]]
        classe = max(candidatas, key=lambda c: ideais[c] - cotas[c])
        cotas[classe] += 1
    while sum(cotas.values()) > tamanho:
        classe = max((c for c in CLASSES if cotas[c] > 2), key=lambda c: cotas[c] - ideais[c])
        cotas[classe] -= 1
    return cotas


def amostrar(entrada, *, tamanho=10_000, semente=42, tamanho_bloco=50_000, fracao_teste=0.2):
    entrada = Path(entrada)
    if not entrada.is_file():
        raise FileNotFoundError(entrada)
    if type(tamanho) is not int or type(tamanho_bloco) is not int or tamanho_bloco <= 0:
        raise ValueError("Tamanho e bloco devem ser inteiros; bloco deve ser positivo.")
    if not 0 < fracao_teste < 1:
        raise ValueError("A fração de teste deve estar entre zero e um.")
    total = descartadas = validas = 0
    # SQLite e diretório exclusivos; fechamento e limpeza inclusive quando ocorre erro.
    with TemporaryDirectory(prefix="sentia-bpsad-") as pasta:
        with closing(sqlite3.connect(Path(pasta) / "grupos.sqlite")) as conexao:
            conexao.execute("CREATE TABLE grupos (chave TEXT PRIMARY KEY, texto TEXT, rotulo TEXT)")
            with pd.read_csv(entrada, usecols=["review_text", "rating"],
                             dtype={"review_text": str}, chunksize=tamanho_bloco) as leitor:
                for bloco in leitor:
                    # Reordena explicitamente: usecols não garante a ordem das colunas do arquivo.
                    for texto, rating in bloco[["review_text", "rating"]].itertuples(index=False, name=None):
                        total += 1
                        classe = rotulo(rating)
                        if not isinstance(texto, str) or not texto.strip() or classe is None:
                            descartadas += 1
                            continue
                        validas += 1
                        conexao.execute("""
                            INSERT INTO grupos VALUES (?, ?, ?)
                            ON CONFLICT(chave) DO UPDATE SET rotulo = CASE
                                WHEN grupos.rotulo = excluded.rotulo THEN grupos.rotulo
                                ELSE 'conflito' END
                        """, (normalizar(texto), texto, classe))
                    conexao.commit()
            contagens = dict(conexao.execute("""
                SELECT rotulo, COUNT(*) FROM grupos WHERE rotulo != 'conflito' GROUP BY rotulo
            """))
            conflitos = conexao.execute("SELECT COUNT(*) FROM grupos WHERE rotulo='conflito'").fetchone()[0]
            grupos = conexao.execute("SELECT COUNT(*) FROM grupos").fetchone()[0]
            cotas = _cotas(contagens, tamanho)
            rng = random.Random(semente)
            amostra = []
            for classe in CLASSES:
                reservatorio = []
                for vistos, (texto,) in enumerate(conexao.execute(
                    "SELECT texto FROM grupos WHERE rotulo=? ORDER BY rowid", (classe,)
                ), start=1):
                    item = (texto, classe)
                    if len(reservatorio) < cotas[classe]:
                        reservatorio.append(item)
                    else:
                        posicao = rng.randrange(vistos)
                        if posicao < cotas[classe]:
                            reservatorio[posicao] = item
                amostra.extend(reservatorio)
    rng.shuffle(amostra)
    df = pd.DataFrame(amostra, columns=["review_text", "rotulo"])
    try:
        treino, teste = train_test_split(df, test_size=fracao_teste, random_state=semente,
                                        stratify=df["rotulo"])
    except ValueError as erro:
        raise ValueError("Não é possível estratificar esta amostra; aumente o tamanho ou ajuste a fração.") from erro
    if set(treino.rotulo) != set(CLASSES) or set(teste.rotulo) != set(CLASSES):
        raise ValueError("Treino e teste precisam das três classes; aumente a amostra ou a fração de teste.")
    df["divisao"] = "treino"
    df.loc[teste.index, "divisao"] = "teste"
    relatorio = {
        "arquivo_origem": str(entrada.resolve()), "linhas_processadas": total,
        "linhas_descartadas": descartadas, "duplicatas_agrupadas": validas - grupos,
        "grupos_com_rotulos_conflitantes": conflitos, "grupos_validos_por_classe": contagens,
        "amostra_total": len(df), "treino": len(treino), "teste": len(teste),
        "distribuicao_amostra": df.rotulo.value_counts().to_dict(),
        "distribuicao_treino": treino.rotulo.value_counts().to_dict(),
        "distribuicao_teste": teste.rotulo.value_counts().to_dict(),
        "semente": semente, "fracao_teste": fracao_teste, "tamanho_bloco": tamanho_bloco,
        "algoritmo": "grupos NFKC/casefold/espaços; conflitos excluídos; cotas exatas min2; reservatório v2",
        "versoes": {"python": platform.python_version(), "pandas": version("pandas"),
                    "scikit-learn": version("scikit-learn")},
        "independencia_pre_treinamento": "não comprovada",
    }
    return df, relatorio


def validar_destinos(entrada, *saidas):
    caminhos = [Path(p).resolve() for p in (entrada, *saidas)]
    if len(set(caminhos)) != len(caminhos):
        raise ValueError("Entrada e saídas devem ser caminhos distintos.")
    for caminho in caminhos[1:]:
        if caminho.exists():
            raise FileExistsError(f"Saída já existe: {caminho}")
        if not caminho.parent.is_dir():
            raise ValueError(f"Diretório de saída inexistente: {caminho.parent}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=Path("data/BPSAD/concatenated.csv"))
    parser.add_argument("--saida", type=Path, default=Path("data/BPSAD/amostra_exploratoria_10k.csv"))
    parser.add_argument("--relatorio", type=Path)
    parser.add_argument("--tamanho", type=int, default=10_000)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--tamanho-bloco", type=int, default=50_000)
    parser.add_argument("--fracao-teste", type=float, default=0.2)
    args = parser.parse_args(argv)
    relatorio = args.relatorio or args.saida.with_suffix(".json")
    try:
        validar_destinos(args.entrada, args.saida, relatorio)
        df, dados = amostrar(args.entrada, tamanho=args.tamanho, semente=args.semente,
                            tamanho_bloco=args.tamanho_bloco, fracao_teste=args.fracao_teste)
        # x impede sobrescrita inclusive se outro processo criar a saída após a validação.
        with args.saida.open("x", encoding="utf-8-sig", newline="") as arquivo:
            df.to_csv(arquivo, index=False)
        with relatorio.open("x", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    except (OSError, ValueError) as erro:
        parser.error(str(erro))
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
