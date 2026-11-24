from __future__ import annotations

import argparse
import hashlib
import json
import platform
import unicodedata
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "BPSAD" / "amostra_pc1.csv"
SAIDA = RAIZ / "data" / "BPSAD" / "calibracao_pc1"

SHA256_PC1_ESPERADO = (
    "607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6"
)

HASHES_SIMULACAO = {
    "desenvolvimento": (
        "693192731106f2dc55c005d69e7efee77637ee275698a55043a4bf5b69308742"
    ),
    "validacao": (
        "4dc9c1a1ad5a6232eeaf1c51b7fecb36c0dbe65fdb287f687f9f4cad8c277881"
    ),
}

SEMENTE = 42
PARTICOES = 5
INDICE_VALIDACAO = 0

CLASSES = ("negativo", "neutro", "positivo")


def sha256_bytes(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def sha256_arquivo(caminho: Path) -> str:
    return sha256_bytes(caminho.read_bytes())


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", str(texto))
    return " ".join(texto.casefold().split())


def hash_dataframe(df: pd.DataFrame) -> str:
    conteudo = df[["review_text", "rotulo"]].to_csv(
        index=False
    ).encode("utf-8")
    return sha256_bytes(conteudo)


def distribuicao(df: pd.DataFrame) -> dict[str, int]:
    contagem = df["rotulo"].value_counts()
    return {
        classe: int(contagem.get(classe, 0))
        for classe in CLASSES
    }


def preparar(forcar: bool = False) -> None:
    if not ENTRADA.is_file():
        raise FileNotFoundError(f"PC1 não encontrada: {ENTRADA}")

    hash_entrada = sha256_arquivo(ENTRADA)

    if hash_entrada != SHA256_PC1_ESPERADO:
        raise ValueError(
            "Hash da PC1 diferente do esperado. "
            "Amostra não será processada."
        )

    arquivos_saida = [
        SAIDA / "desenvolvimento.csv",
        SAIDA / "validacao.csv",
        SAIDA / "relatorio_calibracao.json",
    ]

    existentes = [p for p in arquivos_saida if p.exists()]

    if existentes and not forcar:
        nomes = ", ".join(p.name for p in existentes)
        raise FileExistsError(
            f"Saídas já existentes ({nomes}). "
            "Inspecione-as antes de executar novamente. "
            "Use --forcar somente se autorizar sobrescrevê-las."
        )

    df = pd.read_csv(ENTRADA)

    colunas = {"review_text", "rotulo", "divisao"}
    if not colunas.issubset(df.columns):
        raise ValueError(f"Colunas obrigatórias ausentes: {colunas}")

    if len(df) != 10000:
        raise ValueError(f"Esperados 10.000 registros; encontrados {len(df)}")

    if set(df["divisao"].unique()) != {"treino", "teste"}:
        raise ValueError("Divisões originais inesperadas.")

    treino = df.loc[df["divisao"] == "treino"].copy()

    # Não utilizamos textos nem rótulos do teste na divisão.
    quantidade_teste = int((df["divisao"] == "teste").sum())

    if len(treino) != 8000 or quantidade_teste != 2000:
        raise ValueError("Tamanhos originais de treino/teste divergentes.")

    if treino[["review_text", "rotulo"]].isna().any().any():
        raise ValueError("Há textos ou rótulos ausentes no treino.")

    if not set(treino["rotulo"].unique()).issubset(CLASSES):
        raise ValueError("Há rótulos desconhecidos no treino.")

    treino["_grupo"] = treino["review_text"].map(normalizar)

    if (treino["_grupo"] == "").any():
        raise ValueError("Há textos vazios após normalização.")

    conflitos = treino.groupby("_grupo")["rotulo"].nunique()
    conflitos = conflitos[conflitos > 1]

    if len(conflitos):
        raise ValueError(
            f"Foram encontrados {len(conflitos)} grupos conflitantes."
        )

    grupos_distintos = treino["_grupo"].nunique()

    if grupos_distintos != len(treino):
        raise ValueError(
            "Foram encontradas duplicatas normalizadas no treino. "
            "A divisão foi interrompida para revisão."
        )

    divisor = StratifiedGroupKFold(
        n_splits=PARTICOES,
        shuffle=True,
        random_state=SEMENTE,
    )

    indices_dev, indices_val = next(
        divisor.split(
            treino,
            y=treino["rotulo"],
            groups=treino["_grupo"],
        )
    )

    desenvolvimento = treino.iloc[indices_dev][
        ["review_text", "rotulo"]
    ].copy()

    validacao = treino.iloc[indices_val][
        ["review_text", "rotulo"]
    ].copy()

    if len(desenvolvimento) != 6400 or len(validacao) != 1600:
        raise ValueError("Tamanhos inesperados na divisão.")

    grupos_dev = set(treino.iloc[indices_dev]["_grupo"])
    grupos_val = set(treino.iloc[indices_val]["_grupo"])

    if grupos_dev & grupos_val:
        raise ValueError("Vazamento de grupos entre desenvolvimento e validação.")

    dist_dev = distribuicao(desenvolvimento)
    dist_val = distribuicao(validacao)

    hash_dev = hash_dataframe(desenvolvimento)
    hash_val = hash_dataframe(validacao)

    if hash_dev != HASHES_SIMULACAO["desenvolvimento"]:
        raise ValueError(
            "Hash de desenvolvimento divergiu da simulação aprovada."
        )

    if hash_val != HASHES_SIMULACAO["validacao"]:
        raise ValueError(
            "Hash de validação divergiu da simulação aprovada."
        )

    SAIDA.mkdir(parents=True, exist_ok=True)

    caminho_dev = SAIDA / "desenvolvimento.csv"
    caminho_val = SAIDA / "validacao.csv"

    desenvolvimento.to_csv(caminho_dev, index=False)
    validacao.to_csv(caminho_val, index=False)

    relatorio = {
        "experimento": "calibracao_bertweet_bpsad_pc1",
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "origem": str(ENTRADA.relative_to(RAIZ)),
        "sha256_pc1": hash_entrada,
        "metodologia": {
            "algoritmo": "StratifiedGroupKFold",
            "n_splits": PARTICOES,
            "indice_validacao": INDICE_VALIDACAO,
            "random_state": SEMENTE,
            "normalizacao": "Unicode NFKC + casefold + espaços colapsados",
            "agrupamento": "texto normalizado",
            "conflitos": "rejeitar se encontrados",
            "teste_utilizado": False,
        },
        "quantidades": {
            "amostra_total": len(df),
            "treino_original": len(treino),
            "teste_original_preservado": quantidade_teste,
            "desenvolvimento": len(desenvolvimento),
            "validacao": len(validacao),
            "grupos_distintos_treino": grupos_distintos,
            "grupos_compartilhados": 0,
            "grupos_conflitantes": len(conflitos),
        },
        "distribuicao": {
            "desenvolvimento": dist_dev,
            "validacao": dist_val,
        },
        "arquivos": {
            "desenvolvimento": {
                "caminho": caminho_dev.name,
                "sha256": sha256_arquivo(caminho_dev),
            },
            "validacao": {
                "caminho": caminho_val.name,
                "sha256": sha256_arquivo(caminho_val),
            },
        },
        "versoes": {
            "python": platform.python_version(),
            "pandas": version("pandas"),
            "scikit_learn": version("scikit-learn"),
            "numpy": version("numpy"),
        },
    }

    caminho_relatorio = SAIDA / "relatorio_calibracao.json"
    caminho_relatorio.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== DIVISÃO CONGELADA ===")
    print(f"Desenvolvimento: {len(desenvolvimento)}")
    print(f"Validação: {len(validacao)}")
    print(f"Teste original preservado: {quantidade_teste}")
    print("\nDistribuição desenvolvimento:", dist_dev)
    print("Distribuição validação:", dist_val)
    print("\nSHA-256 desenvolvimento:", hash_dev)
    print("SHA-256 validação:", hash_val)
    print("\nSHA-256 PC1:", hash_entrada)
    print("\nRelatório:", caminho_relatorio)
    print("Divisão validada e salva com sucesso.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Autoriza sobrescrever as saídas existentes.",
    )
    args = parser.parse_args()
    preparar(forcar=args.forcar)
