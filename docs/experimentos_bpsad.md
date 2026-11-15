# Reprodução exploratória BPSAD — correção do PR #64 e avaliação da issue #85

Os scripts estão em `scripts/experimentos/`. As entradas antigas `amostrar_bpsad.py` e `scripts/validar_bpsad.py` são wrappers de compatibilidade.

O histórico desta correção antecede a migração para `uv`. Os arquivos
`pyproject.toml`, `uv.lock` e `.python-version` foram trazidos da versão
`developer` auditada, acrescentando o grupo opcional `experimentos` com
psutil. Os arquivos antigos de requirements foram preservados na branch
histórica; na integração com `developer`, prevalece o gerenciamento `uv`.

O gerenciamento de dependências é feito por `uv`. Para preparar o ambiente:

```bash
uv sync --locked --group experimentos --group ml
```

## Reprodução

A amostragem foi executada com seed 42, 10.000 registros, bloco de 50.000 e divisão de 80% para treino e 20% para teste:

```bash
uv run --group experimentos python -m scripts.experimentos.amostrar_bpsad \
  --entrada data/BPSAD/concatenated.csv \
  --saida data/BPSAD/amostra_pc1.csv \
  --relatorio data/BPSAD/relatorio_amostragem_pc1.json \
  --tamanho 10000 \
  --semente 42 \
  --tamanho-bloco 50000 \
  --fracao-teste 0.2
```

A avaliação com BERTweet e baseline:

```bash
uv run --group experimentos --group ml python -m scripts.experimentos.validar_bpsad \
  --entrada data/BPSAD/amostra_pc1.csv \
  --saida data/BPSAD/avaliacao_pc1_final.json \
  --bertweet
```

Os diretórios de saída devem existir; arquivos existentes e caminhos coincidentes são recusados. Não há opção de sobrescrita. A amostragem usa SQLite em diretório exclusivo e o limpa mesmo se a leitura falhar.

Textos completos ficam somente em arquivos locais. Não publicar o corpus original, amostras com textos reais ou respostas de avaliações como evidência de QA. Os JSONs de resultados publicados nesta documentação contêm parâmetros e métricas, não o conteúdo textual das avaliações.

## Metodologia e integridade dos dados

Padrões utilizados: seed 42, amostra de 10.000 registros, bloco de 50.000 e teste de 20%.

O processamento do BPSAD registrou:

- 2.786.092 linhas processadas;
- 19 linhas descartadas;
- 373.143 duplicatas agrupadas;
- 9.744 grupos com rótulos conflitantes excluídos.

Distribuição da amostra:

| Classe | Total | Treino | Teste |
|---|---:|---:|---:|
| Positivo | 6.856 | 5.485 | 1.371 |
| Negativo | 1.594 | 1.275 | 319 |
| Neutro | 1.550 | 1.240 | 310 |
| **Total** | **10.000** | **8.000** | **2.000** |

A amostra possui predominância da classe positiva (68,56%). Por isso, a acurácia deve ser analisada junto com o F1 macro e as métricas individuais por classe.

O agrupamento utiliza NFKC, casefold e normalização de espaços. Grupos com rótulos conflitantes são excluídos. A divisão é estratificada e não permite sobreposição entre treino e teste.

O JSON registra parâmetros, versões, distribuições, descartes, conflitos e hash SHA-256. A seed não pode ser deduzida do CSV: preservar o relatório de amostragem junto com o arquivo.

**Hashes SHA-256:**

- BPSAD original: `732A32CC7AB88F3DB1186A4EDB3D290935E2C30684A0EA4F8AE0AB4C5E2013FE`
- Amostra: `607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6`

## Resultados da avaliação

A avaliação foi executada em processador (CPU), utilizando o baseline TF-IDF + Logistic Regression e o modelo `pysentimiento/bertweet-pt-sentiment`.

| Métrica | Baseline TF-IDF + LogReg | BERTweet |
|---|---:|---:|
| Acurácia | 70,10% | 67,70% |
| F1 macro | 59,65% | 55,43% |
| Tempo registrado | 0,64 s | 148,53 s |
| RSS após execução | 0,192 GB | 1,078 GB |

Em relação ao baseline, o BERTweet apresentou redução de 2,40 pontos percentuais na acurácia e aproximadamente 4,22 pontos percentuais no F1 macro.

### Métricas por classe

| Modelo | Classe | Precisão | Recall | F1-score | Suporte |
|---|---|---:|---:|---:|---:|
| Baseline | Positivo | 85,61% | 77,68% | 81,45% | 1.371 |
| Baseline | Negativo | 56,64% | 65,52% | 60,76% | 319 |
| Baseline | Neutro | 33,07% | 41,29% | 36,73% | 310 |
| BERTweet | Positivo | 85,21% | 75,20% | 79,89% | 1.371 |
| BERTweet | Negativo | 52,42% | 78,06% | 62,72% | 319 |
| BERTweet | Neutro | 23,49% | 23,87% | 23,68% | 310 |

### Matrizes de confusão

A ordem das classes nas linhas e colunas é: **positivo, negativo, neutro**. As linhas representam os rótulos reais e as colunas as previsões.

**Baseline TF-IDF + Logistic Regression:**

```text
[[1065, 101, 205],
 [  56, 209,  54],
 [ 123,  59, 128]]
```

**BERTweet:**

```text
[[1031, 136, 204],
 [  33, 249,  37],
 [ 146,  90,  74]]
```

O BERTweet apresentou recall maior para a classe negativa, mas desempenho inferior para a classe neutra. Na classe neutra, acertou 74 dos 310 registros de teste. Esse resultado contribui para a redução do F1 macro.

### Tempo e memória

Os tempos registrados foram aproximadamente 0,64 segundo para o baseline e 148,53 segundos para o BERTweet. O RSS registrado após a execução foi aproximadamente 0,192 GB e 1,078 GB, respectivamente.

Esses valores são registros exploratórios, não benchmarks controlados. O tempo de parede pode incluir carregamento ou treinamento, e o RSS posterior não representa o pico de memória. A execução foi feita em CPU, portanto os tempos não devem ser comparados diretamente com execuções em GPU.

## Ambiente de execução

Versões registradas:

- Python 3.12.10
- pandas 3.1.1
- scikit-learn 1.9.1
- psutil 7.2.2
- pysentimiento 0.7.3
- PyTorch 2.15.0+cpu

A independência dos dados de avaliação em relação ao pré-treinamento do BERTweet não foi comprovada.

## Mudanças com efeito científico

Mantidos: agrupamento NFKC/casefold/espaços, exclusão total de grupos com rótulos conflitantes, reservatório por classe e divisão estratificada sem sobreposição.

Corrigidos: arredondamento independente (podia produzir tamanho diferente), ordem das colunas de entrada, cotas com mínimo de dois grupos, validação de notas inteiras 1–5 e preservação de espaços do texto original. Classes são percorridas em ordem explícita.

As cotas mínimas podem alterar a proporção de classes raras; por isso, resultados anteriores não são diretamente atribuíveis à nova amostra.

## Análise da meta RNF01

A meta de aproximadamente 80% de acurácia não foi atingida nesta avaliação: o BERTweet obteve 67,70% e o baseline 70,10%.

É necessário considerar a diferença entre os domínios. O BERTweet foi pré-treinado para linguagem de redes sociais, enquanto o BPSAD contém avaliações de produtos, nas quais notas são convertidas em rótulos de sentimento. Essa diferença pode afetar a capacidade de generalização do modelo.

Os resultados também mostram dificuldade relevante na identificação da classe neutra. A distribuição desbalanceada da amostra reforça a necessidade de avaliar o F1 macro e as métricas por classe, em vez de considerar somente a acurácia.

**Encaminhamento recomendado:** submeter ao Product Owner a análise da meta RNF01, considerando a diferença de domínio, o desempenho por classe e a comparação com o baseline. A meta não deve ser alterada unilateralmente pela equipe de ML.

## Artefatos de reprodução

Os resultados sanitizados estão disponíveis em:

- `docs/resultados_bpsad/relatorio_amostragem_pc1.json`
- `docs/resultados_bpsad/avaliacao_pc1_final.json`

Os arquivos preservam os parâmetros, versões, hashes e métricas necessários à auditoria. A amostra CSV e o corpus completo permanecem locais e não devem ser publicados.

## Testes

Os testes obrigatórios usam corpus sintético temporário e não exigem psutil ou dependências de ML:

```bash
uv run pytest tests/test_experimentos_bpsad.py tests/test_classificacao.py tests/test_pipeline.py -v -ra
```

Na execução local desta avaliação, os testes direcionados passaram: **48 testes aprovados**.
