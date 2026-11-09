# Classificação de sentimentos

Referência: integração PC1 `bfaf7da`, 09/11/2026. O adaptador BERTweet, o baseline
e o pipeline estão implementados. A validação atual é de contrato com analisador
simulado; inferência real e acurácia independente não foram reproduzidas nesta revisão.

## BERTweet

Implementação: [`bertweet.py`](../src/processamento/classificacao/bertweet.py).
Modelo declarado: `pysentimiento/bertweet-pt-sentiment`; revisão exata do checkpoint
ainda não fixada. O wrapper PySentimiento normaliza a saída para as três classes.

Para preparar ML real, fora do roteiro offline:

```bash
uv sync --locked --group ml
```

```python
from src.processamento.classificacao.bertweet import ClassificadorBertweet

classificador = ClassificadorBertweet()
resultados = classificador.prever_com_probabilidades(
    ["Adorei o atendimento!", "A entrega atrasou muito."]
)
```

Reutilize a instância para evitar recarregar o modelo. A primeira criação pode
baixar pesos; não os publique no Git. O exemplo real acima não foi executado
nesta auditoria. Nos testes e na demo, o analisador é injetado e simulado.

A entrada aceita string ou coleção de strings não vazias, preservando ordem.
Coleção vazia no classificador retorna lista vazia; no pipeline, nenhuma entrada
é erro. Tipos inválidos, tamanho de lote não inteiro positivo e saída inesperada
são recusados. A saída é lista de dicionários com `sentimento` e `probabilidades`
para `positivo`, `negativo` e `neutro`.

## Pipeline e contratos

[`PipelineClassificacao`](../src/processamento/pipeline.py) recebe registros dos
importadores, classifica em lotes e devolve documentos Python preparados para
serialização BSON. Preserva texto, IDs, fonte e anotações humanas. Acrescenta
previsão, probabilidades, modelo e `data_processamento` UTC; converte publicação
quando informada. **Não grava no MongoDB e não expõe endpoint FastAPI.**
Detalhes: [contratos de dados](contratos-dados.md) e [esquema](banco/esquema-mongodb.md).

A via BERTweet não aplica limpeza clássica, remoção de stopwords, stemming nem
TF-IDF externamente. Negações, URLs, menções, emojis e acentuação são preservados
na fronteira do analisador. As normalizações internas do tokenizador não foram
auditadas integralmente. #5–#8 e T04–T07 requerem homologação formal da mudança
em relação ao planejamento original; esta decisão técnica não encerra esses requisitos.

## Baseline e avaliação

O baseline em [`baseline.py`](../src/processamento/classificacao/baseline.py) usa
TF-IDF + regressão logística. O vetorizador é ajustado apenas no treino. O
[`script de comparação`](../scripts/comparar_modelos.py) e os testes separam
anotações humanas de previsões e tratam duplicatas/conflitos.

```bash
uv run python -m scripts.comparar_modelos --help
uv run pytest tests/test_classificacao.py tests/test_pipeline.py tests/test_avaliacao.py tests/test_comparar_modelos.py -v -ra
uv run python -m scripts.demonstrar_pipeline
```

A demo usa fixture sintética e analisador constante; não mede desempenho do modelo.
`rotulo_original` é anotação da fonte; `rotulo_padronizado`, sua conversão;
`sentimento`, previsão. Probabilidade não é acurácia. O TweetSentBR local não tem
split/IDs originais necessários para atestar independência em relação ao ajuste
do checkpoint. BPSAD de outro domínio também exige auditoria de proveniência.
Os [experimentos do PR #64](experimentos_bpsad.md) não estão neste SHA.

## Evidências e histórico

Resultados atuais por SHA/data: [ensaio PC1](qa/pc1/RELATORIO_ENSAIO_FINAL.md).
A [homologação de 06/11/2026](qa/pr44-pr45/relatorio.md) preserva logs e uma
[inferência real histórica](qa/pr44-pr45/inferencia-real.json); não é avaliação
independente nem nova inferência nesta tarefa. O registro inicial de 126 testes,
14 skips e exemplos em Windows/Python 3.13.5 não identificava SHA/data suficientes
para ser usado como resultado atual; permanece consultável na
[versão anterior do documento](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/ca25e1223564f55b2465f9de87672cfae878df07/docs/classificacao.md).

Pendências: fixar revisão do checkpoint, reproduzir comparação independente (#17),
registrar ambiente/hash/partições, latência e consumo controlados, detalhar
normalizações internas, integrar API/banco e obter revisão/aceite ML/PO.
