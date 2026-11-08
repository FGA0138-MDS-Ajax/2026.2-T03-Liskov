import json
import time
from pathlib import Path

import pandas as pd
import psutil

from src.processamento.classificacao import baseline
from src.processamento.classificacao.avaliacao import avaliar
from src.processamento.classificacao.bertweet import ClassificadorBertweet

ARQUIVO = Path("data/BPSAD/amostra_exploratoria_10k.csv")
SAIDA = Path("data/BPSAD/resultados_validacao_bpsad.json")

processo = psutil.Process()


def memoria_gb():
    return round(processo.memory_info().rss / (1024 ** 3), 3)


def executar():
    df = pd.read_csv(ARQUIVO)

    treino = df[df["divisao"] == "treino"]
    teste = df[df["divisao"] == "teste"]

    x_treino = treino["review_text"].tolist()
    y_treino = treino["rotulo"].tolist()
    x_teste = teste["review_text"].tolist()
    y_teste = teste["rotulo"].tolist()

    print("=== DADOS ===")
    print(f"Treino: {len(x_treino)}")
    print(f"Teste: {len(x_teste)}")
    print("Classes de teste:")
    print(teste["rotulo"].value_counts().to_string())

    resultados = {
        "dataset": "BPSAD",
        "amostra": len(df),
        "treino": len(treino),
        "teste": len(teste),
        "semente": 42,
        "modelos": {},
    }

    print("\n=== BASELINE TF-IDF + LOGREG ===")
    inicio = time.perf_counter()

    modelo = baseline.criar_baseline()
    modelo.fit(x_treino, y_treino)
    previsto = modelo.predict(x_teste).tolist()

    segundos = time.perf_counter() - inicio
    metricas = avaliar(y_teste, previsto)

    resultados["modelos"]["baseline"] = {
        "tempo_segundos": round(segundos, 3),
        "memoria_rss_gb_apos_execucao": memoria_gb(),
        "acuracia": float(metricas["acuracia"]),
        "f1_macro": float(metricas["f1_macro"]),
        "matriz_confusao": metricas["matriz_confusao"],
        "relatorio": metricas["relatorio"],
    }

    print(f"Tempo: {segundos:.2f} segundos")
    print(f"Memória RSS: {memoria_gb():.3f} GB")
    print(f"Acurácia: {metricas['acuracia']:.4f}")
    print(f"F1 macro: {metricas['f1_macro']:.4f}")
    print(metricas["relatorio"])
    print("Matriz:", metricas["matriz_confusao"])

    del modelo
    del previsto

    print("\n=== BERTWEET ===")
    print("Carregando modelo e executando inferência...")
    inicio = time.perf_counter()

    classificador = ClassificadorBertweet(tamanho_lote=32)
    previsto = classificador.prever(x_teste)

    segundos = time.perf_counter() - inicio
    metricas = avaliar(y_teste, previsto)

    resultados["modelos"]["bertweet"] = {
        "tempo_segundos": round(segundos, 3),
        "memoria_rss_gb_apos_execucao": memoria_gb(),
        "acuracia": float(metricas["acuracia"]),
        "f1_macro": float(metricas["f1_macro"]),
        "matriz_confusao": metricas["matriz_confusao"],
        "relatorio": metricas["relatorio"],
    }

    print(f"Tempo: {segundos:.2f} segundos")
    print(f"Memória RSS: {memoria_gb():.3f} GB")
    print(f"Acurácia: {metricas['acuracia']:.4f}")
    print(f"F1 macro: {metricas['f1_macro']:.4f}")
    print(metricas["relatorio"])
    print("Matriz:", metricas["matriz_confusao"])

    SAIDA.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n=== EXPERIMENTO CONCLUÍDO ===")
    print(f"Resultados salvos em: {SAIDA}")


if __name__ == "__main__":
    executar()
