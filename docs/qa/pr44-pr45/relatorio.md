# Homologação conjunta dos PRs #44 e #45

Data: 06/11/2026. Decisão para os PRs originais: **APROVAR #45 PRIMEIRO, SOLICITAR ATUALIZAÇÃO DO #44**.

Os testes foram executados. A integração é viável após resolução manual de conflitos e correções de contrato demonstradas neste PR de atualização. Nenhum PR oficial foi integrado, nenhuma branch de autor foi alterada diretamente e nenhum dado foi gravado no MongoDB. O PR #41 permanece fechado sem merge.

## Referências exatas

- `origin/developer`: `6c6fe2e3156e61da048e609f635b3a6c8e8bddb9`.
- PR #45, `origin/fix/classificador-revisao`: `e561da419e6355f39bf65c4a2fcb58e3807028ec`.
- PR #44, `origin/feat/integrar-classificador`: `3ba2f4f3302fd694e54e083027aea4cfa7514375`.
- Cenário A: developer → #45 → #44; cenário B: developer → #44 → #45.
- Os dois cenários foram criados em worktrees próprias, com branches experimentais. A reinicialização apagou a primeira área em `/tmp`; os experimentos foram recuperados em disco persistente e as suítes foram repetidas com logs.

## Comparação e conflitos

Cada PR entra isoladamente na developer sem conflito. O segundo merge apresenta os mesmos cinco conflitos nas duas ordens:

| Arquivo | Diferença | Resolução validada |
|---|---|---|
| `requirements.txt` | #44 exige ML na instalação geral; #45 separa ML e limita joblib | Manter dependências gerais do #45 e `requirements-ml.txt` opcional |
| `scripts/comparar_modelos.py` | #45 usa importador SentIA/BPSAD; #44 acrescenta `--dataset` e divisão agrupada | Manter `ler()` pelo importador e rejeição sem rótulo; acrescentar agrupamento Unicode, exclusão de conflitos e CLI do #44; a divisão também usa o importador |
| `classificacao/avaliacao.py` | #44 calcula diretamente; #45 valida tipos, tamanhos e normaliza rótulos | Preservar `avaliar()` do #45 e as métricas/ordem das classes |
| `classificacao/bertweet.py` | #45 rejeita Mapping e explicita checkpoint/lote | Preservar validação e parâmetros do #45, mantendo inferência em lotes |
| `tests/test_classificacao.py` | #45 inclui três casos adicionais | Preservar todos os testes, sem retirar os originais |

Os caminhos de classificação são relativos a `src/processamento/`. `rotulos.py` e `baseline.py` são idênticos nos dois PRs; não apresentam conflito. O pipeline e sua suíte vêm do #44. As suítes de avaliação e leitura de datasets vêm do #45. Não foi usado `--ours` ou `--theirs`.

A ordem inversa não elimina conflitos. Com as mesmas decisões de resolução, as árvores de código dos dois merges são idênticas. Recomenda-se #45 primeiro porque estabelece as validações e a leitura oficial que o #44 deve consumir.

## Resultados executados

| Etapa | PASSED | FAILED | SKIPPED | ERROR |
|---|---:|---:|---:|---:|
| Developer + #45, isolado | 178 | 0 | 0 | 0 |
| Developer + #44, isolado | 172 | 0 | 0 | 0 |
| Cenário A, união das suítes existentes | 196 | 0 | 0 | 0 |
| Cenário B, união das suítes existentes | 196 | 0 | 0 | 0 |
| Dez testes adicionais, antes dos ajustes, em cada cenário | 3 | 7 | 0 | 0 |
| Cenário A corrigido, suíte completa | 206 | 0 | 0 | 0 |
| Cenário B corrigido, suíte completa | 206 | 0 | 0 | 0 |

Os comandos individuais também foram executados nos dois cenários finais: classificação **12**, avaliação **16**, pipeline **18**, comparação **5**, todos aprovados. Os dez testes adicionais estão em `tests/test_integracao_conjunta.py`. A suíte isolada do #45 não tem `test_pipeline.py`; a do #44 não tem `test_avaliacao.py` nem `test_comparar_modelos.py`. Ausência não foi contabilizada como aprovação.

O health check bloqueou sob o sandbox de execução; passou fora dessa restrição, assim como as suítes completas. Nenhum teste foi marcado como ignorado para contornar esse problema. O aviso de depreciação entre Starlette e httpx é não bloqueante.

### Falhas de contrato reproduzidas e corrigidas

Todas estão em `src/processamento/pipeline.py`, introduzido pelo #44:

1. `_processar_lote()`: aceitava `id_origem` e `fonte` ausentes ou vazios, gerando documentos incompatíveis com os campos obrigatórios do esquema. Quatro casos reprovados. Agora valida strings não vazias antes da inferência.
2. `_processar_lote()`: `converter_rotulo_para_sentia(None/"")` produzia sentimento nulo sem rejeição. Dois casos reprovados. Agora verifica pertencimento a `ROTULOS` para a previsão obrigatória.
3. `_normalizar_data_publicacao()`: rejeitava `YYYY-MM-DD`, formato entregue pelo importador e exemplificado no contrato. Um caso reprovado. A resolução experimental converte uma data de calendário para meia-noite UTC, como nos exemplos do #43; timestamps com horário sem fuso continuam inválidos, e ausência de data continua omitida. A convenção precisa do aceite da equipe/PO.

Não foram removidos testes para obter aprovação. O log `regressoes-antes.txt` preserva os sete casos reprovados.

## Fluxo sintético de ponta a ponta

O teste gera CSV UTF-8 com três textos sintéticos, IDs, fontes, `POS/NEG/NEU`, ausência de datas e metadados de categoria. Executa aquisição, classificador com analisador espião, pipeline, avaliação e serialização BSON.

Verifica: `texto_original` preservado; somente strings chegam ao analisador; ordem e quantidade mantidas; sentimentos em português; três probabilidades somando 1; IDs/fontes/metadados preservados; rótulo humano independente da previsão; conversão de siglas; acurácia/F1 macro/matriz de confusão; datas ausentes omitidas; tipos/campos obrigatórios e serialização BSON. Um caso altera o rótulo humano para discordar da previsão e confirma que ele não é sobrescrito.

Essa verificação é de contrato com o documento do #43 e serialização, sem conexão ao MongoDB. Não equivale a testar um validator de collection ou CRUD. Os casos com analisador espião não medem a qualidade do modelo real.

## Inferência real

- Python **3.13.5**, PySentimiento **0.7.3**, Torch **2.9.1+cpu**, Transformers **5.22.1**; CPU, sem CUDA.
- Checkpoint `pysentimiento/bertweet-pt-sentiment`; revisão obtida do cache do download: `726612815d49447cbfe3f55bbfc2993c1f5fad10`.
- Tokenizador: `BertweetTokenizer`. Inicialização: **49,13 s**; inferência de três textos: **3,13 s**.
- “Adorei o atendimento!” → positivo, **0,992056**.
- “A entrega atrasou muito.” → negativo, **0,932464**.
- “O produto chegou hoje.” → neutro, **0,878978**.

As três distribuições completas estão em `inferencia-real.json`. A execução usou a implementação do #45 preservada na integração; não se afirma uma segunda execução real isolada de cada PR. O tempo de inicialização inclui acesso/download do checkpoint. A revisão foi auditada no cache, mas ainda não está fixada no carregador do projeto. O nome do checkpoint contém “bertweet”; o cartão oficial identifica a base como BERTabaporu/RoBERTa.

## Validade científica da avaliação

Foi executado o código original de divisão e baseline do #44 sobre o arquivo local com SHA-256 `8b7be5d0a6bb982c99bf0613ac71f9f8eed49849586a5019b2db2094a6136060`:

- 8.530 registros originais; 12 grupos conflitantes excluídos; 8.500 utilizáveis.
- Treino: 6.804 registros/6.775 grupos; teste: 1.696 registros/1.694 grupos.
- **Zero grupos normalizados compartilhados** entre treino e teste.
- O TF-IDF e a regressão logística são ajustados apenas no treino e avaliados no teste.
- Baseline reproduzido: **62,2052% de acurácia**, **59,6324% de F1 macro**, compatível com 62,21%/59,63% relatados no #44.

O agrupamento usa NFKC, casefold e colapso de espaços. O split tem semente 42 e não é estratificado; ainda há ocorrências repetidas dentro de cada partição, influenciando a ponderação das métricas. A política de exclusão de conflitos deve ser documentada/aceita.

Os **83,37%/81,73% do BERTweet são resultados relatados no PR #44**; não foram recalculados nos 1.696 textos nesta homologação. A inferência de três exemplos confirma funcionamento, não esses percentuais.

A separação local comprova isolamento do baseline, mas não comprova independência em relação ao ajuste fino do checkpoint. O artigo do PySentimiento descreve o corpus de tweets brasileiros sobre TV de Brum e Nunes na tarefa em português. Sem IDs/splits oficiais e proveniência que permitam excluir sobreposição, os resultados do BERTweet são exploratórios e não demonstram generalização independente. A pendência continua na **Issue #17**. Não foi baixado BPSAD completo.

Fontes primárias: [cartão do checkpoint](https://huggingface.co/pysentimiento/bertweet-pt-sentiment), [artigo do PySentimiento, seção 3](https://arxiv.org/html/2106.09462v3).

## Cobertura

Cobertura de linhas, medida por `pytest --cov=src --cov-report=term-missing` na suíte corrigida, igual nos dois cenários:

| Módulo | Cobertura |
|---|---:|
| Total `src` | 94,45% |
| `classificacao/avaliacao.py` | 100% |
| `classificacao/rotulos.py` | 100% |
| `classificacao/baseline.py` | 100% |
| `classificacao/bertweet.py` | 91,67% |
| `processamento/pipeline.py` | 86,26% |

Os scripts fora de `src` não estão incluídos no total de cobertura; o split tem teste adicional específico. Inferência real foi executada separadamente e não está incluída nessa cobertura.

## Matriz de decisão

| Verificação | PR #44 original | PR #45 original | Integração conjunta corrigida |
|---|---|---|---|
| Merge sem conflitos | Sim, isolado | Sim, isolado | Não; cinco conflitos resolvidos nas duas ordens |
| Testes automatizados | 172 aprovados | 178 aprovados | 206 aprovados em A e B |
| Contrato de rótulos | Classificação converte; avaliação não normaliza siglas | Avaliação normaliza e valida | Preservado; sentimento obrigatório validado no pipeline |
| BERTweet | Invoca padrão pt | Explicita checkpoint/lote; rejeita Mapping | Proteções do #45 mantidas |
| Avaliação | Split agrupado; baseline reproduzido | Validação e leitura SentIA/BPSAD | Leitura oficial + split agrupado + métricas validadas |
| Pipeline | Implementado; sete casos adicionais falharam | Não inclui pipeline | Casos corrigidos e fluxo sintético validado |
| Compatibilidade MongoDB | Lacunas em campos obrigatórios e datas | Não monta documento persistível | Contrato e BSON verificados; sem gravação |
| Inferência real | Não repetida isoladamente | Implementação usada na combinação | Três previsões verificadas em CPU |

## Encaminhamento aos autores

- **Gabriel / #45:** nenhuma alteração funcional bloqueante identificada na sua entrega isolada. Manter Mapping, validação/normalização em `avaliar()`, importador oficial em `ler()` e ML opcional. Fixar revisão e conjunto de dependências de execução é melhoria de reprodutibilidade, com evidência das versões testadas neste relatório.
- **Ricardo / #44:** atualizar a branch com developer e #45; resolver os cinco conflitos sem perder as proteções; aplicar as três correções do pipeline; manter os dez testes adicionais; atualizar documentação histórica de testes e pipeline; distinguir o experimento no TweetSentBR da avaliação independente pendente na #17.
- **Equipe/PO:** confirmar a conversão de datas de calendário para UTC e a data usada no filtro por período. Persistência MongoDB/API continuam fora desta homologação.

Os PRs originais não devem entrar juntos no estado observado sem resolução manual. Após revisar e incorporar esta atualização ao #44 e repetir a CI sobre a developer resultante, a combinação fica tecnicamente apta à integração. Este relatório não registra aceite da PO nem merge dos PRs.

## Reprodução e evidências

Em ambiente virtual com dependências de desenvolvimento:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v -ra
python -m pytest tests/test_classificacao.py -v -ra
python -m pytest tests/test_avaliacao.py -v -ra
python -m pytest tests/test_pipeline.py -v -ra
python -m pytest tests/test_comparar_modelos.py -v -ra
python -m pytest tests/test_integracao_conjunta.py -v -ra
python -m pytest --cov=src --cov-report=term-missing
```

Para ML, instalar `requirements-ml.txt`; nesta máquina foi escolhido Torch CPU 2.9.1+cpu antes de instalar PySentimiento, evitando bibliotecas CUDA. Os arquivos JSON contêm contagens, cobertura, métricas e probabilidades reais. Os arquivos TXT preservam os conflitos, as reprovações e as duas execuções finais. As evidências locais completas, XML e scripts do experimento ficam em `.qa-pr44-pr45/evidencias`, fora do versionamento do projeto.
