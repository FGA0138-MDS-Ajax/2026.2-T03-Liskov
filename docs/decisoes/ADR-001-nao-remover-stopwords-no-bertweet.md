# ADR-001 — Não remover stopwords externamente no BERTweet

- **Status:** Proposta técnica — aguardando validação formal da equipe e da PO.
- **Data:** 10/11/2026
- **Contexto:** RF04/US04 — preparação textual e classificação de sentimentos.
- **Componente principal:** `src/processamento/classificacao/bertweet.py`

## 1. Contexto

O requisito original RF04/US04 previa operações de preparação textual associadas ao pipeline clássico de classificação, incluindo remoção de stopwords.

Posteriormente, o escopo técnico passou a considerar o uso do BERTweet por meio da biblioteca PySentimiento. Essa mudança exige reavaliar quais operações de pré-processamento são adequadas ao classificador adotado.

A remoção indiscriminada de palavras pode eliminar informações relevantes para a interpretação de sentimentos. Um caso importante é a negação: a palavra "não" pode alterar a polaridade de uma frase.

Esta decisão registra o comportamento adotado na implementação do BERTweet. Ela não representa, por si só, uma alteração formal do requisito original.

## 2. Decisão

**Não aplicar remoção externa de stopwords antes de encaminhar os textos ao BERTweet.**

Também não aplicar stemming ou vetorização TF-IDF como etapas externas desse caminho de classificação.

O texto original deve ser encaminhado ao analisador PySentimiento, sem que o código do projeto remova previamente palavras ou altere sua estrutura textual.

O pré-processamento específico do modelo permanece sob responsabilidade da biblioteca e de seus componentes internos.

## 3. Justificativa

A preservação do texto permite manter informações linguísticas potencialmente importantes para a classificação, especialmente negações, relações entre palavras e contexto.

Considere os exemplos ilustrativos:

| Frase | Informação relevante |
|---|---|
| Gostei do atendimento. | Sentimento positivo |
| Não gostei do atendimento. | Negação da avaliação positiva |

Se a palavra "não" fosse removida antes da classificação, a segunda frase poderia perder uma informação essencial para sua interpretação.

Esses exemplos ilustram o risco linguístico da remoção. Não representam resultados de uma avaliação experimental do modelo.

Além disso, o BERTweet utiliza seu próprio processo de tokenização e representação textual. Aplicar operações externas indiscriminadamente pode modificar a entrada antes que ela chegue a esses componentes.

## 4. Fluxo implementado

A inspeção do código identificou o seguinte fluxo:

1. `PipelineClassificacao` obtém o conteúdo de `texto_original`.
2. O pipeline reúne os textos para processamento em lotes.
3. `ClassificadorBertweet` valida os tipos e rejeita textos vazios.
4. O wrapper encaminha cada lote diretamente para `self._analisador.predict(lote)`.
5. As previsões são normalizadas e associadas aos respectivos textos na ordem de entrada.
6. O pipeline mantém o campo `texto_original` no registro de saída.

Arquivos envolvidos:

- `src/processamento/pipeline.py`
- `src/processamento/classificacao/bertweet.py`

Na implementação inspecionada, não foi identificada remoção externa de stopwords, stemming ou aplicação de TF-IDF nesse caminho.

O wrapper declara `pysentimiento/bertweet-pt-sentiment` como nome do modelo. A chamada de criação do analisador utiliza `create_analyzer(task="sentiment", lang="pt")`. A confirmação do checkpoint e de sua revisão efetivamente carregados permanece uma verificação separada.

## 5. Tratamento do baseline clássico

O baseline clássico está separado do classificador BERTweet em:

`src/processamento/classificacao/baseline.py`

A implementação inspecionada utiliza:

- conversão do texto para minúsculas;
- remoção de URLs;
- remoção de menções;
- remoção de pontuação;
- normalização de espaços;
- TF-IDF com n-gramas de tamanho 1 e 2;
- regressão logística.

**O baseline atual não realiza remoção explícita de stopwords nem stemming.**

Caso a equipe decida manter ou introduzir remoção de stopwords no baseline, essa operação deverá permanecer isolada do caminho BERTweet e ser avaliada separadamente.

Esta decisão não autoriza a introdução automática dessa etapa no baseline.

## 6. Evidências e limites

A inspeção do código confirma que:

- o pipeline utiliza `texto_original` como entrada;
- o wrapper valida os textos sem realizar limpeza textual;
- o analisador recebe os lotes encaminhados pelo wrapper;
- o pipeline preserva o texto original nos registros de saída.

Os testes de classificação foram executados em 10/11/2026 com o ambiente Python 3.12.10 e pytest 9.1.1. O resultado foi de 10 testes aprovados, sem falhas, em 18,07 segundos.

Entre eles, `test_bertweet_preserva_negacao_ao_encaminhar_ao_analisador` verifica especificamente que frases com negação são encaminhadas literalmente ao analisador. Essa evidência confirma o comportamento do código do projeto na fronteira do wrapper, mas não demonstra como o PySentimiento ou o tokenizer processam internamente cada palavra.

Também não foi demonstrado, por meio dessa inspeção, como cada operação interna do tokenizador ou do modelo trata individualmente as palavras recebidas.

Portanto, a evidência disponível sustenta a ausência de remoção externa no código do projeto, mas não substitui testes de integração ou avaliação experimental do modelo.

## 7. Consequências

### Positivas

- Preservação da negação e de outras informações presentes no texto original antes da chamada ao analisador.
- Separação entre a preparação do baseline clássico e o caminho BERTweet.
- Menor risco de alterar previamente a entrada esperada pelo modelo.

### Limitações e cuidados

- O comportamento interno do PySentimiento e do tokenizador precisa ser considerado separadamente.
- A decisão não demonstra, isoladamente, melhora de desempenho na classificação.
- A avaliação comparativa entre BERTweet e baseline continua necessária.

## 8. Pendências

As seguintes atividades permanecem abertas:

1. [Concluído] Criar e executar teste de contrato para confirmar o encaminhamento literal de frases com negação ao analisador. O teste `test_bertweet_preserva_negacao_ao_encaminhar_ao_analisador` passou em 10/11/2026.
2. Avaliar, quando aplicável, o comportamento do analisador com essas entradas.
3. Confirmar o checkpoint e a revisão efetivamente utilizados.
4. Solicitar à PO e à equipe a revisão formal do RF04/US04.
5. Revisar os critérios de aceitação relacionados à preparação textual.
6. Avaliar os impactos no roteiro de testes T05 e nos demais testes relacionados.
7. Registrar formalmente o aceite ou a rejeição da mudança de escopo.

A mudança de abordagem técnica não comprova que os critérios originais de remoção de stopwords foram executados ou atendidos.

## 9. Referências

- `docs/classificacao.md` — documentação do classificador e da preparação textual.
- `src/processamento/pipeline.py` — encaminhamento e preservação do texto original.
- `src/processamento/classificacao/bertweet.py` — validação e encaminhamento dos lotes ao analisador.
- `src/processamento/classificacao/baseline.py` — implementação do baseline clássico.
- Issue relacionada à revisão técnica do RF04/US04.

---

**Nota de governança:** este ADR registra a proposta técnica adotada na implementação. A revisão formal dos requisitos e dos critérios de aceitação depende de validação da equipe e da PO. Até essa validação, o requisito original não deve ser marcado como concluído com base apenas nesta decisão.
