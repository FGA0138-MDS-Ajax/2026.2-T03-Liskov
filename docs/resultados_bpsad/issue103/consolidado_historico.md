# Issue #103 — Consolidação histórica dos experimentos BERTweet

**Status:** consolidação documental de resultados já existentes
**Data:** 2026-11-23
**Escopo:** avaliação do BERTweet original, fine-tuning do modelo C e calibração pós-treinamento.

> Este documento foi elaborado a partir dos resultados históricos disponíveis. Nenhum treinamento, inferência, calibração ou acesso ao conjunto reservado de teste foi executado para produzi-lo.

## 1. Resumo executivo

O fine-tuning do modelo C melhorou o desempenho sobre o BERTweet original na validação de 1.600 exemplos. O F1 macro passou de **0,538720** para **0,645087**, com melhora nas três classes. A classe neutra continua sendo o principal ponto fraco, embora seu F1 tenha aumentado de **0,184426** para **0,357143**.

Na calibração histórica do modelo C, o ajuste de temperatura reduziu o ECE de **0,0389** para **0,0280**, sem alterar as classes preditas. O ajuste adicional do limiar neutro elevou a acurácia de **0,7638** para **0,7800**, mas reduziu o F1 macro de **0,6554** para **0,6428** e o F1 neutro de **0,3557** para **0,2981**. Os dados disponíveis favorecem considerar a temperatura isoladamente; o limiar neutro não demonstrou melhoria geral.

**Conclusão provisória:** o modelo C é o candidato tecnicamente mais forte entre os avaliados nesta validação. A adoção final do modelo e sua integração à API permanecem decisões do PO, após a auditoria de reprodutibilidade de Renato.

## 2. Dados e protocolo

A divisão do BPSAD está documentada em `data/BPSAD/calibracao_pc1/relatorio_calibracao.json`.

| Partição | Quantidade | Observação |
|---|---:|---|
| Amostra total | 10.000 | Amostra de trabalho |
| Desenvolvimento | 6.400 | Usado no treinamento |
| Validação | 1.600 | Avaliação e seleção de checkpoint |
| Teste reservado | 2.000 | Não utilizado |

Foi utilizado `StratifiedGroupKFold`, 5 partições, índice de validação 0 e `random_state=42`. O agrupamento foi baseado no texto normalizado (Unicode NFKC, `casefold` e espaços colapsados). O relatório registra zero grupos compartilhados entre desenvolvimento e validação e zero conflitos detectados.

Distribuição de classes:

| Partição | Negativa | Neutra | Positiva |
|---|---:|---:|---:|
| Desenvolvimento (6.400) | 1.020 | 992 | 4.388 |
| Validação (1.600) | 255 | 248 | 1.097 |

Hashes SHA-256 conhecidos:

| Artefato | SHA-256 |
|---|---|
| Amostra `amostra_pc1.csv` | `607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6` |
| `desenvolvimento.csv` | `693192731106f2dc55c005d69e7efee77637ee275698a55043a4bf5b69308742` |
| `validacao.csv` | `4dc9c1a1ad5a6232eeaf1c51b7fecb36c0dbe65fdb287f687f9f4cad8c277881` |
| Predições da avaliação original | `a6acd1c2bd46cbf2077cccacc188eed6e29f068fe4c9580cad4312ca49fe8a87` |

**Limitação dos rótulos:** os rótulos do BPSAD são derivados de avaliações por estrelas e não necessariamente representam o sentimento expresso no texto. Os resultados devem ser interpretados considerando essa diferença.

## 3. Avaliação na validação completa

| Métrica | BERTweet original | Modelo C fine-tuned |
|---|---:|---:|
| Acurácia | 0,67625 | 0,765625 |
| F1 macro | 0,538720 | 0,645087 |
| F1 negativa | 0,625806 | 0,707889 |
| F1 neutra | 0,184426 | 0,357143 |
| F1 positiva | 0,805927 | 0,870229 |

O modelo C melhorou as métricas agregadas e o F1 de cada classe. A classe neutra permanece abaixo das demais.

### 3.1 BERTweet original

- Modelo-base: `pysentimiento/bertweet-pt-sentiment`.
- Sem fine-tuning e sem calibração.
- Validação: 1.600 exemplos.
- Acurácia: 0,67625; F1 macro: 0,538720.
- Log loss: 0,959896; Brier score: 0,502056; ECE (15 bins): 0,191337.
- Matriz de confusão (ordem negativa, neutra, positiva):

```text
[[194,  38,  23],
 [ 74,  45, 129],
 [ 97, 157, 843]]
```

### 3.2 Modelo C fine-tuned

- Modelo-base: `pysentimiento/bertweet-pt-sentiment`.
- Melhor checkpoint registrado: `checkpoint-400`.
- Melhor F1 macro durante seleção: 0,6450869969.
- Treinamento: 3 épocas configuradas, 1.200 passos globais.
- Tempo registrado: aproximadamente 281,90 segundos.
- SHA-256 dos pesos de `melhor_modelo` e `checkpoint-400`: `37116f5322c0f61f0456e47998730b06c799bf1b3234bc6bffc149b775174ea0`.

Os registros indicam `melhor_modelo` como artefato de entrega. O tokenizer desse diretório corresponde ao tokenizer-base conhecido; não substituir seus arquivos pelo tokenizer de `checkpoint-400` sem verificação específica.

## 4. Calibração histórica

A validação foi dividida em duas partes de 800 exemplos, com semente 42. Temperatura e limiar neutro foram ajustados somente na parte de calibração. Os valores abaixo são históricos e não resultam de uma nova execução.

### 4.1 Modelo C — subconjunto de avaliação (800 exemplos)

| Métrica | Sem calibração | Temperatura | Temperatura + limiar |
|---|---:|---:|---:|
| Acurácia | 0,7638 | 0,7638 | 0,7800 |
| F1 macro | 0,6554 | 0,6554 | 0,6428 |
| F1 negativa | 0,7511 | 0,7511 | 0,7581 |
| F1 neutra | 0,3557 | 0,3557 | 0,2981 |
| F1 positiva | 0,8595 | 0,8595 | 0,8724 |
| Log loss | 0,5682 | 0,5676 | Não disponível |
| Brier score | 0,3261 | 0,3257 | Não disponível |
| ECE | 0,0389 | 0,0280 | 0,0383 |
| Neutras previstas como positivas | 68 | 68 | 78 |

Temperatura registrada: **0,951590**. Limiar neutro: **0,515**.

A temperatura melhorou a calibração probabilística (ECE, log loss e Brier) sem mudar as classes previstas. O limiar neutro deslocou previsões neutras para positivas, elevando a acurácia, mas sacrificando F1 macro e, principalmente, F1 neutra.

### 4.2 BERTweet original — subconjunto de avaliação (800 exemplos)

Os registros históricos disponíveis são parciais:

| Métrica | Sem calibração | Temperatura | Temperatura + limiar |
|---|---:|---:|---:|
| Acurácia | 0,6663 | 0,6663 | 0,6200 |
| F1 macro | 0,5452 | 0,5452 | 0,5326 |
| F1 negativa | 0,6537 | 0,6537 | Não disponível |
| F1 neutra | 0,1923 | 0,1923 | 0,2282 |
| F1 positiva | 0,7895 | 0,7895 | Não disponível |
| Log loss | 1,0044 | 0,7764 | Não disponível |
| Brier score | 0,5229 | 0,4499 | Não disponível |
| ECE | 0,2075 | 0,0740 | Não disponível |

Temperatura registrada: **2,081545**. Limiar neutro: **0,310**.

Os valores indisponíveis não foram reconstruídos nem estimados. Os relatórios JSON gerados por uma futura execução autorizada poderão recuperar as métricas completas.

## 5. Ressalva metodológica essencial

O subconjunto de 800 exemplos chamado anteriormente de “avaliação independente” **não é um teste independente do treinamento**. O checkpoint foi selecionado usando a validação completa de 1.600 exemplos. Embora os 800 exemplos não tenham participado do ajuste da temperatura ou do limiar, participaram indiretamente da seleção do checkpoint.

A terminologia correta é **subconjunto de avaliação da validação** ou **avaliação interna da validação**. Não apresentar esses resultados como desempenho em teste independente ou estimativa final de generalização.

O conjunto reservado de 2.000 exemplos não foi utilizado. Qualquer avaliação oficial nele deve seguir o protocolo acordado pela equipe e ocorrer somente com autorização explícita.

## 6. Configuração e ambiente

Configuração de fine-tuning registrada:

- `max_length=128`, seed 42, learning rate `2e-5`, 3 épocas.
- Batch de treinamento 4, batch de avaliação 8, acumulação de gradiente 4.
- Weight decay 0,01; warmup ratio 0,1 (120 passos); clipping de gradiente 1,0.
- Seleção pelo F1 macro; `load_best_model_at_end=True`.

Ambientes históricos:

| Etapa | Python | PyTorch | Dispositivo |
|---|---|---|---|
| Avaliação original | 3.12.10 | 2.15.0+cpu | CPU |
| Treinamento do modelo C | 3.14.10 | 2.13.0+rocm10.1.0 | AMD Radeon RX 9070 (HIP) |

Versões adicionais registradas incluem `pysentimiento 0.7.3`, `transformers 5.22.2`, `pandas 3.1.1`, `scikit-learn 1.9.1` e `numpy 2.5.4`. Diferenças de ambiente devem ser consideradas na auditoria de reprodutibilidade.

## 7. Artefatos e rastreabilidade

- `data/BPSAD/calibracao_pc1/relatorio_calibracao.json` — protocolo e divisão dos dados.
- `data/BPSAD/calibracao_pc1/metricas_validacao_original.json` — avaliação original na validação completa.
- `data/BPSAD/calibracao_pc1/predicoes_validacao_original.csv` — predições do modelo original.
- `scripts/experimentos/configs/issue103_bertweet_bpsad_raiz_pesos.json` — configuração de treinamento.
- Relatório de treinamento do modelo C: `/home/ricar/models/sentia/issue-103-bertweet-ft-v3-raiz-pesos/relatorio_treinamento.json`.
- Pesos do modelo C: `/home/ricar/models/sentia/issue-103-bertweet-ft-v3-raiz-pesos/melhor_modelo`.

Os caminhos `/home/ricar/...` são locais ao ambiente de treinamento e podem não existir em outro computador. Os dados sob `data/` permanecem locais/ignorados pelo Git conforme a configuração atual do repositório.

## 8. Scripts preparados para relatórios futuros

Foram preparados, mas **não executados nesta etapa**:

- `scripts/experimentos/avaliar_bertweet_issue103.py` — grava dados, configuração, ambiente e resultados por modelo em JSON.
- `scripts/experimentos/calibrar_bertweet_issue103.py` — grava divisão, metodologia, ambiente, parâmetros de calibração e métricas por cenário em JSON.

Os nomes dos arquivos usam timestamp UTC e a abertura em modo exclusivo (`x`) evita sobrescrever arquivos existentes. A compilação sintática dos dois scripts foi verificada com sucesso; a geração dos relatórios ainda não foi testada por execução, pois nenhum experimento foi reexecutado.

## 9. Conclusões e responsabilidades

1. O modelo C melhora o BERTweet original na validação completa e em todas as classes.
2. A temperatura isolada é a alternativa de calibração mais promissora entre os resultados históricos apresentados. O limiar neutro reduz F1 macro e F1 neutra.
3. Limitações: rótulos derivados de estrelas; ausência de teste independente nesta etapa; histórico de calibração parcialmente disponível; diferenças de ambiente entre treinamento e avaliação.
4. Esta etapa organiza experimentos, métricas e artefatos. A auditoria de reprodutibilidade cabe a Renato; a decisão final do modelo e a integração à API cabem ao PO.
5. Após revisão/auditoria e autorização, os scripts preparados poderão ser executados para gerar os JSONs completos, sem confundir essa execução com uso do teste reservado.

---

**Estado:** documento histórico; não substitui os relatórios brutos nem constitui validação independente. Nenhum novo experimento foi realizado para produzi-lo.
