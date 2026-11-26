# M-04 — Análise de erros do BERTweet



**Responsáveis:** Ricardo e Gabriel

**Escopo:** organização e análise dos resultados e artefatos de experimentos já realizados.

**Procedimento:** análise documental e de previsões previamente geradas. Não foram executados novos treinamentos, fine-tuning, calibração ou inferência para esta análise.


## 1. Objetivo


Analisar os erros do BERTweet identificados na avaliação do BPSAD, destacando o desempenho por classe, as confusões mais frequentes, exemplos qualitativos disponíveis e possíveis explicações para os resultados.



A análise busca demonstrar por que a acurácia isolada não é suficiente para avaliar o modelo, especialmente diante do baixo desempenho na classe neutra.



## 2. Resultado de referência — Issue #85



A avaliação histórica do BERTweet no teste PC1 contém 2.000 registros.



A matriz de confusão abaixo utiliza a ordem **positivo, negativo, neutro**, tanto nas linhas (rótulo real) quanto nas colunas (sentimento previsto).



| Rótulo real / previsto | Positivo | Negativo | Neutro | Suporte |

|---|---:|---:|---:|---:|

| Positivo | 1031 | 136 | 204 | 1371 |

| Negativo | 33 | 249 | 37 | 319 |

| Neutro | 146 | 90 | 74 | 310 |



Resultados:



| Métrica | Resultado |

|---|---:|

| Acurácia | 67,70% |

| F1 macro | 55,43% |

| F1 positivo | 79,89% |

| F1 negativo | 62,72% |

| F1 neutro | 23,68% |



A classe neutra apresenta o pior resultado. Dos 310 registros neutros, apenas 74 foram classificados corretamente. Os outros 236 foram classificados como positivos (146) ou negativos (90).



O conjunto também apresenta desbalanceamento: são 1.371 registros positivos, 319 negativos e 310 neutros. Portanto, a acurácia não representa adequadamente o comportamento do modelo em todas as classes.



## 3. Comparação quantitativa — Issue #103



A avaliação final da Issue #103 compara o BERTweet original com o Modelo C experimental no mesmo teste PC1 de 2.000 registros.



Nesta seção, as matrizes utilizam a ordem **negativo, neutro, positivo**.



### 3.1 BERTweet original



| Rótulo real / previsto | Negativo | Neutro | Positivo | Suporte |

|---|---:|---:|---:|---:|

| Negativo | 249 | 37 | 33 | 319 |

| Neutro | 90 | 74 | 146 | 310 |

| Positivo | 136 | 204 | 1031 | 1371 |



- Acurácia: 67,70%.

- F1 macro: 55,43%.

- F1 negativo: 62,72%.

- F1 neutro: 23,68%.

- F1 positivo: 79,89%.



### 3.2 Modelo C experimental



| Rótulo real / previsto | Negativo | Neutro | Positivo | Suporte |

|---|---:|---:|---:|---:|

| Negativo | 217 | 61 | 41 | 319 |

| Neutro | 34 | 139 | 137 | 310 |

| Positivo | 41 | 130 | 1200 | 1371 |



- Acurácia: 77,80%.

- F1 macro: 67,26%.

- F1 negativo: 71,03%.

- F1 neutro: 43,44%.

- F1 positivo: 87,30%.



### 3.3 Diferenças observadas



| Métrica | Original | Modelo C | Diferença |

|---|---:|---:|---:|

| Acurácia | 67,70% | 77,80% | +10,10 p.p. |

| F1 macro | 55,43% | 67,26% | +11,83 p.p. |

| F1 negativo | 62,72% | 71,03% | +8,31 p.p. |

| F1 neutro | 23,68% | 43,44% | +19,76 p.p. |

| F1 positivo | 79,89% | 87,30% | +7,41 p.p. |



Na classe neutra, o original acertou 74 registros, enquanto o Modelo C acertou 139. Os erros neutro → negativo passaram de 90 para 34. Os erros neutro → positivo passaram de 146 para 137.



A comparação demonstra melhora quantitativa do Modelo C nas métricas avaliadas, inclusive na classe neutra.



Entretanto, o F1 neutro permanece abaixo de 60%, e a acurácia de 77,80% permanece 2,20 pontos percentuais abaixo da referência de 80%.



O Modelo C permanece experimental. A melhora observada não representa, por si só, autorização para substituir o modelo operacional.



**Limitação:** os artefatos localizados para o teste PC1 contêm métricas e matrizes, mas não um CSV com previsões individuais e textos correspondentes. Portanto, não é possível apresentar exemplos qualitativos do teste nem comparar diretamente os textos classificados incorretamente pelos dois modelos.



## 4. Análise qualitativa complementar — validação original da Issue #103



Foi localizado o arquivo:



`data/BPSAD/calibracao_pc1/predicoes_validacao_original.csv`



O arquivo contém:

- Texto da avaliação (`review_text`);

- Rótulo real (`rotulo_real`);

- Sentimento previsto (`sentimento_previsto`);

- Probabilidades para cada classe.



Essas previsões pertencem à validação original de 1.600 registros, não ao teste PC1 de 2.000 registros.



### 4.1 Distribuição dos erros



A validação apresentou 518 erros em 1.600 registros.



| Rótulo real → previsto | Quantidade |

|---|---:|

| Positivo → neutro | 157 |

| Neutro → positivo | 129 |

| Positivo → negativo | 97 |

| Neutro → negativo | 74 |

| Negativo → neutro | 38 |

| Negativo → positivo | 23 |

| **Total** | **518** |



As confusões mais frequentes envolveram as classes positiva e neutra, nos dois sentidos.



Também foram identificados 74 registros neutros classificados como negativos.



### 4.2 Exemplos de erros



A inspeção de quatro registros com rótulo real neutro e previsão divergente encontrou os seguintes exemplos:



| Rótulo real → previsto | Trecho do texto | Observação |

|---|---|---|

| Neutro → negativo | "só não gostei porque tem muito anúncios" | A expressão explícita de insatisfação pode favorecer a previsão negativa. |

| Neutro → positivo | Comentário sobre o idioma italiano, com avaliação desfavorável e observação contextual. | O texto apresenta sinais avaliativos que podem apontar em direções diferentes. |

| Neutro → negativo | Comentário dirigido à DC/Warner que menciona filmes sombrios e grandes enredos. | O vocabulário e o contexto podem ser interpretados como crítica ou elogio. |

| Neutro → positivo | "Filme lindo e bizarro..." | O elogio explícito pode favorecer a previsão positiva, apesar do rótulo real neutro. |



Os exemplos são ilustrativos. Eles não comprovam que os rótulos estejam incorretos ou que as previsões sejam semanticamente erradas. A interpretação depende do contexto completo e dos critérios de anotação do conjunto.



## 5. Causas prováveis



Com base nos resultados quantitativos e nos exemplos disponíveis, são levantadas as seguintes hipóteses:



1. **Desbalanceamento entre classes:** a quantidade de exemplos positivos é muito superior à das demais classes, o que pode favorecer padrões de decisão associados à classe majoritária.

2. **Ambiguidade entre neutralidade e polaridade:** comentários curtos ou mistos podem conter palavras positivas e negativas, dificultando a classificação em uma única classe.

3. **Diferença entre avaliação textual e rótulo derivado de nota:** no BPSAD, os rótulos estão associados a avaliações e notas. Uma avaliação neutra pode conter elogios ou críticas no texto. Essa diferença pode explicar parte das divergências, mas não comprova erro de anotação.

4. **Diferença entre domínios:** o BPSAD contém avaliações de produtos e filmes e não equivale a um conjunto de tweets. Os resultados não devem ser extrapolados diretamente para o domínio de tweets.



A melhora quantitativa do Modelo C indica redução de parte das confusões no teste PC1. Entretanto, sem previsões individuais comparáveis do Modelo C, não é possível afirmar quais tipos de texto explicam essa melhora.



## 6. Limitações da análise



- Os exemplos qualitativos disponíveis pertencem à validação original de 1.600 registros, não ao teste PC1 de 2.000 registros.

- Não foi localizado um arquivo de previsões individuais do teste PC1 com texto, rótulo real e previsão.

- Não foram localizados exemplos individuais do Modelo C para comparação qualitativa pareada.

- A inspeção de quatro exemplos é ilustrativa e não representa uma análise qualitativa abrangente.

- A hipótese de divergência entre nota e conteúdo textual não comprova erro de rotulagem.

- Os resultados dizem respeito ao BPSAD e não devem ser generalizados automaticamente para tweets.

- Esta análise reutiliza resultados e previsões existentes. Não houve nova inferência, treinamento, fine-tuning ou calibração.



## 7. Conclusão



A análise confirma que o principal ponto fraco do BERTweet original no teste PC1 é o reconhecimento da classe neutra, cujo F1 foi de 23,68%.



A comparação quantitativa da Issue #103 mostra melhora do Modelo C experimental, elevando o F1 neutro para 43,44% e a acurácia para 77,80%. Apesar da evolução, os resultados permanecem abaixo das referências de 60% para F1 por classe e 80% para acurácia.



A análise qualitativa complementar da validação original identificou confusões recorrentes entre neutro e positivo e entre neutro e negativo. Os exemplos sugerem que expressões avaliativas e comentários com sinais mistos podem contribuir para as previsões divergentes. Essa interpretação permanece como hipótese, especialmente porque os exemplos não pertencem ao teste PC1.



Os artefatos existentes permitem documentar a análise quantitativa do teste e uma análise qualitativa complementar da validação, mas não sustentam uma comparação qualitativa pareada entre o original e o Modelo C no teste.



Nenhuma nova execução de modelo foi necessária para produzir este registro.



## 8. Artefatos utilizados



- `docs/metricas/REGISTRO_E_ANALISE.md` — registro de métricas, matrizes, métricas por classe e limitações históricas.

- `docs/analise_regressao_bertweet_issue_103.md` — análise de regressão e comparação de resultados da Issue #103.

- `docs/resultados_bpsad/issue103/avaliacao_teste_pc1_20261124T004234133293Z.json` — avaliação comparativa final no teste PC1.

- `data/BPSAD/calibracao_pc1/predicoes_validacao_original.csv` — previsões individuais da validação original utilizadas na análise qualitativa complementar.

- `docs/resultados_bpsad/issue103/tweetsentbr_comparacao_issue103.json` — comparação exploratória no TweetSentBR, utilizada como contexto de regressão entre domínios, não como evidência independente de generalização.
