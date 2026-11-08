import json
import random
import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ARQUIVO = Path("data/BPSAD/concatenated.csv")
PASTA = Path("data/BPSAD")
BANCO = PASTA / "bpsad_grupos_temp.sqlite"
SAIDA = PASTA / "amostra_exploratoria_10k.csv"
RELATORIO = PASTA / "amostra_exploratoria_10k.json"

TAMANHO = 10_000
SEMENTE = 42
TAMANHO_BLOCO = 50_000


def normalizar(texto):
    texto = unicodedata.normalize("NFKC", str(texto)).casefold()
    return re.sub(r"\s+", " ", texto).strip()


def rotulo(rating):
    if 1 <= rating <= 2:
        return "negativo"
    if rating == 3:
        return "neutro"
    if 4 <= rating <= 5:
        return "positivo"
    return None


def main():
    if not ARQUIVO.exists():
        raise FileNotFoundError(ARQUIVO)

    if BANCO.exists():
        BANCO.unlink()

    conexao = sqlite3.connect(BANCO)
    conexao.execute("""
        CREATE TABLE grupos (
            texto_normalizado TEXT PRIMARY KEY,
            texto_original TEXT NOT NULL,
            rotulo TEXT NOT NULL
        )
    """)

    total_linhas = 0
    descartadas = 0

    leitor = pd.read_csv(
        ARQUIVO,
        usecols=["review_text", "rating"],
        chunksize=TAMANHO_BLOCO,
    )

    for numero, bloco in enumerate(leitor, start=1):
        registros = []

        for texto, rating in bloco.itertuples(index=False, name=None):
            if pd.isna(texto) or pd.isna(rating):
                descartadas += 1
                continue

            texto = str(texto).strip()
            classe = rotulo(float(rating))
            chave = normalizar(texto)

            if not texto or not chave or classe is None:
                descartadas += 1
                continue

            registros.append((chave, texto, classe))

        conexao.executemany("""
            INSERT INTO grupos VALUES (?, ?, ?)
            ON CONFLICT(texto_normalizado) DO UPDATE SET
                rotulo = CASE
                    WHEN grupos.rotulo = excluded.rotulo
                    THEN grupos.rotulo
                    ELSE 'conflito'
                END
        """, registros)

        conexao.commit()
        total_linhas += len(bloco)
        print(f"Bloco {numero}: {total_linhas:,} linhas processadas")

    contagens = dict(conexao.execute("""
        SELECT rotulo, COUNT(*)
        FROM grupos
        WHERE rotulo != 'conflito'
        GROUP BY rotulo
    """).fetchall())

    conflitos = conexao.execute("""
        SELECT COUNT(*) FROM grupos WHERE rotulo = 'conflito'
    """).fetchone()[0]

    total_validos = sum(contagens.values())

    if total_validos < TAMANHO:
        raise RuntimeError(
            f"Há somente {total_validos} grupos válidos; "
            f"não é possível selecionar {TAMANHO}."
        )

    rng = random.Random(SEMENTE)
    amostra = []

    for classe, quantidade in contagens.items():
        limite = round(TAMANHO * quantidade / total_validos)
        reservatorio = []

        cursor = conexao.execute("""
            SELECT texto_original FROM grupos WHERE rotulo = ?
        """, (classe,))

        vistos = 0
        for (texto,) in cursor:
            vistos += 1
            item = (texto, classe)

            if len(reservatorio) < limite:
                reservatorio.append(item)
            else:
                posicao = rng.randrange(vistos)
                if posicao < limite:
                    reservatorio[posicao] = item

        amostra.extend(reservatorio)

    rng.shuffle(amostra)

    df = pd.DataFrame(amostra, columns=["review_text", "rotulo"])

    treino, teste = train_test_split(
        df,
        test_size=0.20,
        random_state=SEMENTE,
        stratify=df["rotulo"],
    )

    df["divisao"] = "treino"
    df.loc[teste.index, "divisao"] = "teste"

    df.to_csv(SAIDA, index=False, encoding="utf-8-sig")

    relatorio = {
        "arquivo_origem": str(ARQUIVO),
        "linhas_processadas": total_linhas,
        "linhas_descartadas": descartadas,
        "grupos_com_rotulos_conflitantes": conflitos,
        "grupos_validos_por_classe": contagens,
        "amostra_total": len(df),
        "treino": len(treino),
        "teste": len(teste),
        "distribuicao_amostra": df["rotulo"].value_counts().to_dict(),
        "distribuicao_treino": treino["rotulo"].value_counts().to_dict(),
        "distribuicao_teste": teste["rotulo"].value_counts().to_dict(),
        "semente": SEMENTE,
    }

    RELATORIO.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    conexao.close()
    BANCO.unlink(missing_ok=True)

    print("\nAMOSTRAGEM CONCLUÍDA")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    print(f"\nCSV: {SAIDA}")
    print(f"Relatório: {RELATORIO}")


if __name__ == "__main__":
    main()
