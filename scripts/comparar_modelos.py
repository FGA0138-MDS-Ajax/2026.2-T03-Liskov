"""Compara o baseline TF-IDF com o BERTweet-PT.

Uso:
    python -m scripts.comparar_modelos --treino dados/treino.csv --teste dados/teste.csv

Formatos aceitos pelo importador:
- SentIA: texto, rotulo, fonte (sentimento é um alias de rotulo).
- BPSAD: review_text, rating, dataset.

Todos os registros devem estar rotulados para treino e avaliação.
"""

import argparse
import time

from src.processamento.aquisicao.csv_importer import iterar_dataset_csv
from src.processamento.classificacao import baseline
from src.processamento.classificacao.avaliacao import avaliar
from src.processamento.classificacao.bertweet import ClassificadorBertweet
from src.processamento.classificacao.rotulos import normalizar_rotulo


def ler(caminho: str) -> tuple[list[str], list[str]]:
    textos = []
    rotulos = []

    # Reutiliza o importador oficial, que reconhece SentIA e BPSAD
    # O modo estrito para a leitura se houver um registro inválido.
    for registro in iterar_dataset_csv(caminho, modo_estrito=True):
        rotulo = registro["rotulo_padronizado"]

        # A aquisição aceita dados sem rótulo, mas treino e avaliação
        # precisam de uma resposta conhecida para cada texto.
        if rotulo is None:
            raise ValueError(
                f"{caminho}: registro {registro['id_origem']} sem rótulo; "
                "treino e avaliação exigem todos os registros rotulados"
            )

        # Extrai os campos do contrato retornado pelo importador
        textos.append(registro["texto_original"])
        rotulos.append(normalizar_rotulo(rotulo))

    return textos, rotulos


def mostrar(nome: str, resultado: dict, segundos: float) -> None:
    """Exibe as métricas e o tempo da etapa medida."""
    print(f"\n=== {nome} ({segundos:.1f}s) ===")
    print(
        f"Acurácia: {resultado['acuracia']:.4f} | "
        f"F1 macro: {resultado['f1_macro']:.4f}"
    )
    print(resultado["relatorio"])
    print(
        "Matriz de confusão (positivo, negativo, neutro):",
        resultado["matriz_confusao"],
    )


def main() -> None:
    # Define as opções que podem ser informadas pelo terminal
    parser = argparse.ArgumentParser()
    parser.add_argument("--treino", required=True)
    parser.add_argument("--teste", required=True)
    parser.add_argument("--saida-baseline", default="modelos/baseline.pkl")
    parser.add_argument("--sem-bertweet", action="store_true")
    args = parser.parse_args()

    x_treino, y_treino = ler(args.treino)
    x_teste, y_teste = ler(args.teste)

    # Ajusta o TF-IDF e regressão logística somente com os dados de treino.
    inicio = time.perf_counter()
    modelo = baseline.criar_baseline().fit(x_treino, y_treino)

    # Avalia em dados de teste e salva o baseline treinado.
    previsto = modelo.predict(x_teste).tolist()
    segundos = time.perf_counter() - inicio
    mostrar("Baseline TF-IDF + LogReg", avaliar(y_teste, previsto), segundos)
    baseline.salvar(modelo, args.saida_baseline)

    # Usa o BERTweet pre-treinado nos mesmos textos de teste.
    # A opção --sem-bertweet vai executar somente o baseline.
    if not args.sem_bertweet:
        inicio = time.perf_counter()
        previsto = ClassificadorBertweet().prever(x_teste)
        segundos = time.perf_counter() - inicio
        mostrar("BERTweet-PT", avaliar(y_teste, previsto), segundos)


if __name__ == "__main__":
    main()