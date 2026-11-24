# Análise da regressão do BERTweet após fine-tuning — Issue #103

## 1. Objetivo

Documentar a comparação entre o BERTweet original (`pysentimiento/bertweet-pt-sentiment`) e a versão ajustada durante os experimentos da Issue #103.

O objetivo foi verificar se o fine-tuning realizado com uma amostra do BPSAD melhorou o desempenho do modelo em relação ao modelo original.

## 2. Metodologia

Os dois modelos foram avaliados sobre os mesmos 8.530 exemplos do TweetSentBR, utilizando:

- O mesmo conjunto de textos e rótulos.
- O mesmo tokenizer do BERTweet.
- O mesmo pré-processamento com `preprocess_tweet`, do pysentimiento.
- Comprimento máximo de sequência de 128 tokens.
- Inferência em lotes de 16 exemplos.

A comparação utilizou as métricas de acurácia, F1 macro, F1 por classe, log loss, Brier score e Expected Calibration Error (ECE).

**Limitação metodológica:** o arquivo local do TweetSentBR não contém os identificadores originais dos tweets nem informações sobre a divisão oficial dos dados. Além disso, o modelo original foi treinado com o TweetSentBR. Portanto, esta avaliação é exploratória e não representa uma medição independente de generalização.

## 3. Resultados

| Métrica | BERTweet original | BERTweet ajustado |
|---|---:|---:|
| Acurácia | 83,90% | 64,87% |
| F1 macro | 82,70% | 54,48% |
| F1 negativo | 85,11% | 71,28% |
| F1 neutro | 74,14% | 18,08% |
| F1 positivo | 88,83% | 74,07% |
| Log loss | 0,4262 | 0,7170 |
| Brier score | 0,2345 | 0,4295 |
| ECE (15 bins) | 0,0184 | 0,0842 |

A versão ajustada apresentou redução de 19,04 pontos percentuais na acurácia e de 28,22 pontos no F1 macro.

## 4. Principal problema observado: classe neutra

A maior regressão ocorreu na identificação de exemplos neutros.

| Indicador | Original | Ajustado |
|---|---:|---:|
| Recall neutro | 77,41% | 10,86% |
| Exemplos neutros corretamente classificados | 1.683 | 236 |
| Neutros classificados incorretamente como positivos | 294 | 1.840 |

O modelo ajustado passou a classificar uma parcela muito grande dos exemplos como positivos:

- Exemplos realmente positivos: 3.953 (46,34%).
- Previsões positivas do modelo original: 3.898.
- Previsões positivas do modelo ajustado: 6.583 (77,17%).

Esse comportamento indica um forte viés de previsão para a classe positiva, acompanhado de perda expressiva da capacidade de distinguir sentimentos neutros.

## 5. Possíveis causas da regressão

Os resultados permitem levantar algumas hipóteses. As causas abaixo são interpretações técnicas plausíveis, não conclusões comprovadas por experimentos de ablação.

### 5.1. Diferença entre os critérios de rotulagem

O fine-tuning utilizou dados do BPSAD, cujos rótulos são derivados de avaliações por estrelas. Já o TweetSentBR utiliza anotações de sentimento textual.

Esses critérios não representam necessariamente a mesma coisa. Uma avaliação positiva pode acompanhar um texto com críticas, ressalvas, ironia ou linguagem aparentemente neutra. Da mesma forma, uma avaliação intermediária não implica obrigatoriamente neutralidade textual.

O ajuste pode ter ensinado ao modelo associações entre padrões linguísticos e avaliações dos usuários que não correspondem diretamente à polaridade expressa no texto.

### 5.2. Deslocamento das previsões para a classe positiva

A versão ajustada passou a prever a classe positiva em 77,17% dos exemplos, embora essa classe represente 46,34% do conjunto avaliado.

Esse deslocamento sugere que o fine-tuning alterou as fronteiras de decisão do modelo, favorecendo excessivamente a classe positiva.

### 5.3. Possível esquecimento catastrófico

O fine-tuning modifica os pesos do modelo original. Durante esse processo, o modelo pode perder parte de distinções que havia aprendido anteriormente.

Uma possibilidade é que o ajuste tenha enfraquecido a separação entre as classes neutra e positiva. A queda acentuada no recall e no F1 da classe neutra é compatível com essa hipótese, mas não comprova, isoladamente, a ocorrência de esquecimento catastrófico.

### 5.4. Diferença entre validação interna e avaliação em outro conjunto

O modelo ajustado apresentou resultados satisfatórios na validação interna do BPSAD. Entretanto, essa validação mede o desempenho dentro da distribuição e do critério de rotulagem daquele conjunto.

Um bom resultado na validação interna não garante transferência para outro conjunto de dados, especialmente quando os critérios de anotação são diferentes.

## 6. Verificações técnicas realizadas

Foram verificadas as correspondências entre as classes dos modelos:

- Modelo original: `NEG`, `NEU`, `POS`.
- Modelo ajustado: `negativo`, `neutro`, `positivo`.

A ordem das classes foi compatibilizada na avaliação.

Também foram utilizados o mesmo tokenizer e o mesmo pré-processamento para os dois modelos. Assim, diferenças evidentes de mapeamento de classes ou de preparação dos textos tornam-se explicações menos prováveis para a regressão observada.

Essas verificações não eliminam a possibilidade de outros problemas técnicos, mas dão maior consistência à comparação realizada.

## 7. Decisão técnica

Com base nos resultados desta avaliação exploratória:

- Manter o BERTweet original como modelo de referência da pipeline.
- Não promover a versão ajustada da Issue #103 para substituir o modelo original.
- Preservar o checkpoint ajustado como resultado experimental.
- Registrar a regressão e suas possíveis explicações para orientar decisões futuras.

A decisão não significa que o fine-tuning seja necessariamente inadequado. Significa que, nas condições avaliadas, a versão ajustada não demonstrou desempenho suficiente para substituir o modelo original.

## 8. Conclusão

O fine-tuning com a amostra do BPSAD apresentou bom desempenho na validação interna, mas teve uma regressão expressiva na avaliação exploratória com o TweetSentBR.

O principal problema foi a perda da capacidade de identificar sentimentos neutros, acompanhada de um forte aumento nas previsões positivas.

A diferença entre os critérios de rotulagem do BPSAD e do TweetSentBR, o deslocamento das previsões e a possibilidade de esquecimento de distinções aprendidas anteriormente são explicações plausíveis para o comportamento observado.

Como a avaliação não constitui um teste independente de generalização, os resultados devem ser interpretados com essa limitação. Ainda assim, são suficientes para justificar a decisão de não substituir o BERTweet original pela versão ajustada neste momento.

## 9. Reexecução reproduzível da comparação no TweetSentBR

Em 23/11/2026, foi executado o script
`scripts/experimentos/avaliar_bertweet_tweetsentbr_issue103.py`.

A execução realizou somente inferência, sem treinamento ou ajuste de
parâmetros no TweetSentBR. Foram avaliados 8.530 registros do arquivo
`Datasets/tweetsent.csv`, cuja integridade foi confirmada pelo SHA256:

`8b7be5d0a6bb982c99bf0613ac71f9f8eed49849586a5019b2db2094a6136060`

Foi aplicada a mesma configuração de pré-processamento e inferência
aos três cenários: BERTweet original sem calibração, modelo C completo
sem calibração e modelo C completo com temperatura fixa de 0,951787.
A temperatura foi estimada anteriormente na calibração interna do
BPSAD e não foi reajustada com dados do TweetSentBR.

### 8.1 Resultados reproduzidos

| Métrica | Original | C completo | C + temperatura |
|---|---:|---:|---:|
| Acurácia | 0,8390 | 0,6487 | 0,6487 |
| F1 macro | 0,8270 | 0,5448 | 0,5448 |
| F1 negativo | 0,8511 | 0,7128 | 0,7128 |
| F1 neutro | 0,7414 | 0,1808 | 0,1808 |
| F1 positivo | 0,8883 | 0,7407 | 0,7407 |
| Log loss | 0,4262 | 0,7170 | 0,7209 |
| Brier | 0,2345 | 0,4295 | 0,4324 |
| ECE (15 bins) | 0,0184 | 0,0842 | 0,0913 |

A temperatura fixa não alterou as classes previstas pelo modelo C.
Entretanto, piorou log loss, Brier e ECE nessa avaliação exploratória.

### 8.2 Análise dos erros da classe neutra

A distribuição real contém 2.174 exemplos neutros. O modelo C completo
classificou corretamente apenas 236 deles e classificou 1.840 como
positivos.

Isso corresponde a aproximadamente 84,6% dos exemplos neutros sendo
classificados incorretamente como positivos. O modelo C previu a classe
positiva em 77,17% de todos os exemplos, embora ela represente 46,34%
da distribuição real.

A regressão da classe neutra é, portanto, especialmente expressiva e
não pode ser considerada aceitável para substituir o modelo original.

### 8.3 Limitação metodológica

Esta comparação é exploratória, não uma avaliação independente de
generalização: o BERTweet original foi treinado com o TweetSentBR.
Consequentemente, seu desempenho nesse conjunto não deve ser interpretado
como evidência de desempenho em dados externos não vistos.

A comparação continua sendo útil para identificar regressões introduzidas
pelo ajuste fino no BPSAD. Os resultados indicam que o modelo C apresenta
forte viés de predição para a classe positiva nesse conjunto.

### 8.4 Decisão técnica

- Não promover o modelo C para a API.
- Não adotar a temperatura 0,951787 como solução geral.
- Manter o BERTweet original como referência operacional atual.
- Preservar o conjunto oficial de teste de 2.000 exemplos do BPSAD para
  a avaliação final, sem utilizá-lo para treinamento ou calibração.
- Exigir nova evidência de melhoria equilibrada entre as classes antes
  de considerar outra versão ajustada.

Relatório completo da execução:

`docs/resultados_bpsad/issue103/tweetsentbr_comparacao_issue103.json`

Script de reprodução:

`scripts/experimentos/avaliar_bertweet_tweetsentbr_issue103.py`


## 10. Avaliação comparativa final no teste PC1

### 10.1. Procedimento

Foi realizada uma avaliação comparativa do BERTweet original e do modelo C
(com ajuste fino de três épocas) sobre os 2.000 registros da divisão de teste
da amostra PC1 do BPSAD.

O avaliador utilizado foi:

`scripts/experimentos/avaliar_bertweet_teste_pc1_issue103.py`

O procedimento conferiu o SHA-256 da amostra PC1
(`607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6`),
selecionou exclusivamente os registros com `divisao == "teste"` e verificou
a distribuição esperada: 1.371 positivos, 319 negativos e 310 neutros.

Foram avaliadas quatro variantes:
- BERTweet original, sem calibração;
- BERTweet original, com temperatura 2.081848;
- Modelo C completo, sem calibração;
- Modelo C completo, com temperatura 0.951787.

As temperaturas foram estimadas anteriormente usando dados de validação,
não usando os 2.000 registros do teste PC1. Nenhum treinamento ou ajuste de
parâmetros foi realizado sobre esse conjunto durante esta avaliação.

### 10.2. Resultados gerais

| Variante | Acurácia | F1 macro | Log loss | Brier | ECE |
|---|---:|---:|---:|---:|---:|
| Original, sem calibração | 0,6770 | 0,5543 | 0,9685 | 0,4975 | 0,1882 |
| Original, temperatura 2.081848 | 0,6770 | 0,5543 | 0,7593 | 0,4350 | 0,0490 |
| Modelo C, sem calibração | **0,7780** | **0,6726** | 0,5561 | 0,3148 | 0,0292 |
| Modelo C, temperatura 0.951787 | **0,7780** | **0,6726** | **0,5552** | **0,3143** | **0,0235** |

O modelo C obteve aumento de 10,10 pontos percentuais em acurácia e de
0,1183 em F1 macro em relação ao BERTweet original.

A temperatura não alterou as classes previstas nem as métricas de
classificação. No modelo C, melhorou as métricas de qualidade das
probabilidades: o ECE caiu de 0,0292 para 0,0235, enquanto log loss e
Brier também apresentaram pequenas reduções.

### 10.3. Métricas por classe

| Modelo | Classe | Precisão | Recall | F1 |
|---|---|---:|---:|---:|
| Original | Negativo | 0,5242 | 0,7806 | 0,6272 |
| Original | Neutro | 0,2349 | 0,2387 | 0,2368 |
| Original | Positivo | 0,8521 | 0,7520 | 0,7989 |
| Modelo C | Negativo | 0,7432 | 0,6803 | 0,7103 |
| Modelo C | Neutro | 0,4212 | 0,4484 | 0,4344 |
| Modelo C | Positivo | 0,8708 | 0,8753 | 0,8730 |

O modelo C apresentou aumento de F1 nas três classes. O ganho mais expressivo
ocorreu na classe neutra, cujo F1 passou de 0,2368 para 0,4344. Apesar da
melhora, a classe neutra continua sendo o principal ponto de atenção.

### 10.4. Matrizes de confusão

Ordem das classes nas linhas e colunas: negativo, neutro e positivo.
As linhas representam os rótulos reais e as colunas, as previsões.

**BERTweet original:**

| Real \ Previsto | Negativo | Neutro | Positivo |
|---|---:|---:|---:|
| Negativo | 249 | 37 | 33 |
| Neutro | 90 | 74 | 146 |
| Positivo | 136 | 204 | 1.031 |

**Modelo C:**

| Real \ Previsto | Negativo | Neutro | Positivo |
|---|---:|---:|---:|
| Negativo | 217 | 61 | 41 |
| Neutro | 34 | 139 | 137 |
| Positivo | 41 | 130 | 1.200 |

O modelo C reduziu os erros de classificação da classe neutra como positiva:
foram 146 casos no original e 137 no modelo C. Também aumentou os acertos
da classe neutra de 74 para 139. Ainda há confusão relevante entre neutro
e positivo.

### 10.5. Comparação com o baseline histórico

Os resultados históricos do baseline TF-IDF + Logistic Regression no mesmo
teste PC1 foram:
- Acurácia: 0,7010;
- F1 macro: 0,5965.

O modelo C superou esses valores em 7,70 pontos percentuais de acurácia e
aproximadamente 0,0761 de F1 macro.

Essa comparação é contextual: os resultados do baseline são históricos e
não substituem uma nova avaliação independente.

### 10.6. Meta de 80%

O modelo C atingiu 77,80% de acurácia, ficando 2,20 pontos percentuais abaixo
da meta de 80% prevista na Issue #103.

Portanto, a meta não foi atingida. O resultado representa uma melhora
expressiva sobre o BERTweet original, mas não autoriza afirmar que o requisito
de 80% foi cumprido.

### 10.7. Limitações e ressalvas metodológicas

O conjunto de teste PC1 possui 2.000 registros separados do conjunto de
desenvolvimento. O ajuste fino e a calibração realizados nesta etapa não
utilizaram esses registros.

Entretanto, não foi possível comprovar a independência desses dados em
relação ao pré-treinamento do BERTweet. Além disso, o BERTweet original já
havia sido avaliado historicamente nesse mesmo teste. Assim, os resultados
devem ser interpretados como uma comparação experimental controlada entre
as variantes avaliadas, e não como uma estimativa comprovadamente
independente de generalização.

A comparação exploratória no TweetSentBR também precisa ser considerada:
o modelo C apresentou regressão importante nesse conjunto, especialmente
na classe neutra, enquanto o modelo original obteve desempenho superior.
Como o BERTweet original foi treinado com TweetSentBR, esse resultado não
constitui uma avaliação independente de generalização. Ainda assim, a
regressão é um alerta de possível adaptação excessiva ao domínio do BPSAD.

### 10.8. Conclusão e encaminhamento

Os resultados indicam que o ajuste fino do modelo C melhorou a acurácia,
o F1 macro e o desempenho individual das três classes no teste PC1.
A calibração por temperatura melhorou adicionalmente a qualidade das
probabilidades, sem alterar as classes previstas.

Por outro lado:
- A meta de 80% de acurácia não foi alcançada;
- A regressão observada no TweetSentBR impede tratar a melhora no BPSAD
  como evidência suficiente de generalização;
- A independência do teste em relação ao pré-treinamento não foi comprovada.

**Recomendação:** manter o modelo C como candidato experimental e não
substituir o modelo utilizado pela API até que o Product Owner avalie os
resultados e aprove explicitamente a eventual mudança. Não realizar novos
ajustes de limiar ou hiperparâmetros usando o teste PC1.

Relatório detalhado da avaliação:

`docs/resultados_bpsad/issue103/avaliacao_teste_pc1_20261124T004234133293Z.json`
