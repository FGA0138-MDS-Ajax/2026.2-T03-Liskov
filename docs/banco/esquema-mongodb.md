# Esquema de documentos do MongoDB - SentIA



## 1. Visão geral

Referência: integração PC1 `bfaf7da`, 09/11/2026. Este documento define o
formato **previsto** para armazenamento no MongoDB; CRUD de análises ainda não
está implementado. O pipeline já produz documentos em memória. Cada texto
analisado deverá ser salvo como um documento contendo o texto,
seus metadados e o resultado da classificação de sentimento. Serve como contrato entre as frentes de Banco, Dados, Machine
Learning e API.

A arquitetura prevista reserva o acesso ao banco para a camada de dados (PyMongo).
A referência herdada à seção 2.4.2 do Documento de Arquitetura não foi conferida
no artefato completo. A API **deverá** consultar os documentos e aplicar filtros
por período (RF11) e sentimento (RF12); hoje fornece apenas `/health`.



**Escopo:** apenas documenta e define o esquema. A
implementação da persistência (pymongo, gravação e consultas) pertence à
Sprint 4, e a configuração do ambiente e da conexão pertence à issue #12.

| Item | Valor |
|---|---|
| Banco de dados | `sentia` |
| Collection | `analises` |
| Um documento representa | um texto analisado |

### 1.1 Onde o banco entra no fluxo

```
Datasets / coletas ─► Aquisição e importação ─► Classificação ─► Persistência ─► MongoDB
                                                                                    │
                                   Dashboard (Streamlit) ◄─ API (FastAPI) ◄─────────┘
```

- **Quem deverá gravar:** somente o módulo de Persistência, ao receber o resultado da
  Classificação (texto, metadados, sentimento e identificação do modelo).
- **Quem deverá ler:** somente o módulo de Persistência, a pedido da API. A interface
  nunca acessa o banco diretamente.
- **Preparação do texto:** o classificador BERTweet realiza a própria
  tokenização. Um pré-processamento externo (limpeza, stopwords, stemming,
  TF-IDF) só existe em modelos alternativos, como o baseline.

### 1.2 Requisitos apoiados pelo esquema (sem comprovar implementação)

| Requisito | Como o esquema atende |
|---|---|
| RF07 – Classificação em três classes | O campo de sentimento aceita apenas `positivo`, `negativo` ou `neutro` |
| RF08 – Persistência das análises | Cada documento guarda o texto, seus metadados e o resultado da análise |
| RF10 – Consulta das análises | Os documentos ficam em uma única collection, consultada pela API |
| RF11 – Filtro por período | As datas são armazenadas no tipo `Date`, e cada consulta declara qual data utiliza (seção 4.7) |
| RF12 – Filtro por sentimento | O sentimento é um campo próprio, com valores padronizados |

### 1.3 Glossário

| Termo | Significado |
|---|---|
| Banco de dados (database) | Conjunto de collections do sistema (`sentia`) |
| Collection | Grupo de documentos do mesmo tipo, equivalente a uma tabela (`analises`) |
| Documento | Um registro no formato JSON/BSON, equivalente a uma linha de tabela |
| Campo | Uma informação dentro do documento, equivalente a uma coluna |
| `_id` | Identificador único gerado automaticamente pelo MongoDB (`ObjectId`) |
| Índice | Estrutura que acelera consultas por um campo, como a data |
| Fonte | Dataset ou coleta de onde o texto veio |

## 2. Convenções de nomes

- Nomes de campos em português, letras minúsculas e palavras separadas por
  `_` (snake_case), seguindo a PEP 8 adotada pelo projeto. Ex.: `texto_original`.
- Nomes de collections no plural, coerentes com os endpoints da API
  (ex.: collection `analises` ↔ `GET /analises`).
- Valores de sentimento sempre em minúsculas: `positivo`, `negativo` ou
  `neutro` (RF07), iguais aos usados pelo módulo de classificação.
- Datas armazenadas no tipo `Date` do MongoDB (nunca como texto), em UTC,
  para que os filtros por período funcionem corretamente.

### 2.1 Decisões de modelagem

- **Uma única collection (`analises`).** O texto e o resultado da sua análise
  são sempre consultados juntos pelo dashboard; guardá-los no mesmo documento
  evita junções entre collections e mantém as consultas simples.
- **Datasets heterogêneos.** Fontes diferentes podem trazer informações
  diferentes (com ou sem data, com ou sem rótulo). Os campos comuns a todas as
  fontes são obrigatórios; os que dependem da fonte são opcionais, e
  informações específicas ficam em `metadados`. Assim, novas fontes podem ser
  adicionadas sem alterar a estrutura (meta de escalabilidade da arquitetura).
- **Independência do modelo.** O documento registra o nome e a versão do modelo
  que classificou o texto, e nenhum campo obrigatório depende de um modelo
  específico. Trocar o BERTweet por outro classificador não exige mudar o
  esquema.
- **Datas nunca são inventadas.** `data_publicacao` só é preenchida quando a
  fonte informa a data real de publicação. Ela nunca é substituída pela data
  de importação ou de processamento.
- **Campos ausentes são omitidos.** Quando um campo opcional não se aplica, ele
  não aparece no documento (em vez de ser gravado como `null`). Para encontrar
  documentos sem o campo, usa-se `$exists: false` (seção 4.7). O importador
  entrega ausências como `None`; o pipeline já as omite no documento em memória.
- **Privacidade (LGPD).** A política proposta não prevê armazenar campos que identifiquem o autor
  do texto, como nome de usuário ou perfil, pois não são necessários para a
  análise de sentimentos.  O `texto_original` do TweetSentBR contém
  `@menções` de usuários; a anonimização desses textos depende de decisão da
  Product Owner (ver [`docs/tweetsentbr.md`](../tweetsentbr.md), seção 6).

### 2.2 Ambiente

A configuração do MongoDB (local ou Atlas) e o teste de conexão via pymongo
são tratados na issue #12. Este esquema vale para os dois ambientes.

## 3. Campos do documento

### 3.1 Identificação e origem

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | Sim (automático) | Identificador único do documento, gerado pelo MongoDB |
| `id_origem` | String | Sim | Identificador do texto na fonte original (ex.: `review_id` do BPSAD). Quando a fonte não possui identificador, como o TweetSentBR, o importador gera um identificador determinístico (ex.: `TweetSentBR_000263_813e105164b8`). Com `fonte`, identifica a origem; unicidade depende do índice futuro e não deduplica conteúdo reordenado |
| `fonte` | String | Sim | Nome do dataset ou da coleta de onde o texto veio, conforme entregue pelo importador (ex.: `TweetSentBR`; no BPSAD, a plataforma de origem, como `b2w` ou `olist`). Exigido pela arquitetura (RF08) |

### 3.2 Texto

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `texto_original` | String | Sim | Texto exatamente como foi obtido da fonte |
| `texto_tratado` | String | Não | Texto após um pré-processamento externo, preenchido somente quando o modelo utilizado depende dele (ex.: baseline TF-IDF). Na via BERTweet, que usa tokenização própria, o campo é omitido |

### 3.3 Resultado da classificação

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `sentimento` | String | Sim | Sentimento **previsto pelo modelo**. Valores aceitos: `positivo`, `negativo`, `neutro` (RF07) |
| `probabilidades` | Object | Não | Probabilidade de cada classe, quando o modelo a fornece |
| `probabilidades.positivo` | Double | Sim, se `probabilidades` existir | Valor entre 0 e 1 |
| `probabilidades.negativo` | Double | Sim, se `probabilidades` existir | Valor entre 0 e 1 |
| `probabilidades.neutro` | Double | Sim, se `probabilidades` existir | Valor entre 0 e 1 |
| `modelo` | Object | Sim | Identificação do modelo que realizou a classificação. Permite rastrear qual modelo gerou cada resultado caso ele seja trocado |
| `modelo.nome` | String | Sim | Nome do modelo (ex.: `pysentimiento/bertweet-pt-sentiment`) |
| `modelo.versao` | String |  Não | Versão do modelo ou do checkpoint utilizado, a ser definida na issue #16 |
| `rotulo_original` | String | Não | Rótulo **humano** exatamente como veio da fonte, sem conversão (ex.: `positivo` no TweetSentBR, nota `5` no BPSAD). Preserva a informação original para auditoria. Nunca é preenchido com a previsão do modelo |
| `rotulo_padronizado` | String | Não | O rótulo humano convertido para os mesmos valores de `sentimento` (`positivo`, `negativo`, `neutro`), pela função `converter_rotulo_para_sentia()` usada pelo pipeline. Os importadores atuais geram ambos quando há anotação; o pipeline não exige sua presença em pares para registros arbitrários. Permite medir a acurácia comparando-o diretamente com `sentimento`. Formato a confirmar na issue #19 |

### 3.4 Datas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `data_publicacao` | Date | Não | Data real em que o texto foi publicado, quando a fonte a informa (ex.: `review_date` do BPSAD). O TweetSentBR não possui data em nenhum registro. Nunca é substituída por outra data |
| `data_processamento` | Date | Sim | Data e hora da classificação, preenchida pelo pipeline. Não comprova gravação no banco |

### 3.5 Metadados adicionais

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `metadados` | Object | Não | Informações extras específicas de cada fonte. O importador coloca aqui, como texto, as colunas do arquivo que não correspondem a nenhum outro campo (ex.: `category` do BPSAD). O conteúdo varia conforme a fonte. Não deve conter dados que identifiquem o autor (ver seção 2.1) |

## 4. Exemplos JSON

Os exemplos usam o formato *Extended JSON* do MongoDB, no qual as datas são
escritas como `{ "$date": "..." }` para indicar que são do tipo `Date`, e não
texto. Os mesmos exemplos estão na pasta [`exemplos/`](exemplos/) e podem ser
importados no MongoDB Compass (*ADD DATA → Import JSON or CSV file*).

Os registros do BPSAD (seções 4.1 e 4.2) seguem a amostra sintética do projeto
([`tests/fixtures/bpsad_sample.csv`](../../tests/fixtures/bpsad_sample.csv)).
O texto e o `id_origem` do TweetSentBR (4.3) são sintéticos, seguindo o formato
gerado pelo importador, para não redistribuir textos reais de usuários. O
documento mínimo (4.4) é inteiramente ilustrativo. As probabilidades, o `texto_tratado` e o nome do modelo baseline
(`baseline-tfidf-logreg`) são ilustrativos; o nome e a versão dos modelos
serão definidos na issue #16. O campo `_id` não aparece porque é gerado pelo
MongoDB no momento da gravação.

### 4.1 Documento completo (BPSAD + BERTweet)

Avaliação do BPSAD com nota, data e categoria, classificada pelo BERTweet
([`exemplos/analise-completa.json`](exemplos/analise-completa.json)).
A nota `5` fica preservada em `rotulo_original` e convertida em
`rotulo_padronizado`. Não possui `texto_tratado`, pois o BERTweet usa
tokenização própria:

```json
{
  "id_origem": "bpsad_syn_001",
  "fonte": "b2w",
  "texto_original": "Excelente produto! A entrega foi rápida e superou minhas expectativas na conferência.",
  "sentimento": "positivo",
  "probabilidades": { "positivo": 0.91, "negativo": 0.03, "neutro": 0.06 },
  "modelo": { "nome": "pysentimiento/bertweet-pt-sentiment", "versao": "a-definir" },
  "rotulo_original": "5",
  "rotulo_padronizado": "positivo",
  "data_publicacao": { "$date": "2026-10-01T00:00:00Z" },
  "data_processamento": { "$date": "2026-11-03T14:30:00Z" },
  "metadados": { "category": "eletronicos" }
}
```

### 4.2 Documento classificado por outro modelo (baseline)

O mesmo esquema atende a um modelo diferente. O baseline TF-IDF usa
pré-processamento externo, por isso `texto_tratado` aparece
([`exemplos/analise-baseline.json`](exemplos/analise-baseline.json)):

```json
{
  "id_origem": "bpsad_syn_003",
  "fonte": "olist",
  "texto_original": "O item cumpre o básico esperado pelo preço, sem grandes destaques.",
  "texto_tratado": "item cumpre básico esperado preço grandes destaques",
  "sentimento": "neutro",
  "probabilidades": { "positivo": 0.12, "negativo": 0.08, "neutro": 0.80 },
  "modelo": { "nome": "baseline-tfidf-logreg", "versao": "a-definir" },
  "rotulo_original": "3",
  "rotulo_padronizado": "neutro",
  "data_publicacao": { "$date": "2026-10-03T00:00:00Z" },
  "data_processamento": { "$date": "2026-11-03T14:31:00Z" },
  "metadados": { "category": "utilidades" }
}
```

### 4.3 Documento do TweetSentBR (sem data)

O TweetSentBR não possui identificador original nem data de publicação. O
`id_origem` é gerado pelo importador e `data_publicacao` é omitida
([`exemplos/analise-tweetsentbr.json`](exemplos/analise-tweetsentbr.json)):

```json
{
  "id_origem": "TweetSentBR_000001_0a1b2c3d4e5f",
  "fonte": "TweetSentBR",
  "texto_original": "Adorei o programa de hoje, muito divertido!",
  "sentimento": "positivo",
  "probabilidades": { "positivo": 0.88, "negativo": 0.02, "neutro": 0.10 },
  "modelo": { "nome": "pysentimiento/bertweet-pt-sentiment", "versao": "a-definir" },
  "rotulo_original": "positivo",
  "rotulo_padronizado": "positivo",
  "data_processamento": { "$date": "2026-11-03T14:32:00Z" }
}
```

### 4.4 Documento mínimo

Fonte sem data de publicação e sem rótulo, apenas com os campos obrigatórios
([`exemplos/analise-minima.json`](exemplos/analise-minima.json)):

```json
{
  "id_origem": "c_001",
  "fonte": "exemplo_coleta",
  "texto_original": "Péssimo serviço de atenção ao usuário, não recomendo de jeito nenhum.",
  "sentimento": "negativo",
  "modelo": { "nome": "pysentimiento/bertweet-pt-sentiment" },
  "data_processamento": { "$date": "2026-10-29T14:30:05Z" }
}
```

### 4.5 Documentos inválidos

Exemplos que **não** obedecem ao esquema e devem ser recusados pela
Persistência quando ela for implementada na Sprint 4
([`exemplos/analises-invalidas.json`](exemplos/analises-invalidas.json)):

| Problema | Trecho | Regra violada |
|---|---|---|
| Sentimento fora dos valores aceitos | `"sentimento": "feliz"` | Seção 2 e RF07 |
| Sentimento com letra maiúscula | `"sentimento": "POS"` | Seção 2 |
| Data gravada como texto | `"data_processamento": "29/10/2026"` | Seção 2 (datas no tipo `Date`) |
| Campo obrigatório ausente | documento sem `texto_original` | Seção 3.2 |
| Probabilidade fora do intervalo | `"positivo": 1.7` | Seção 3.3 (valor entre 0 e 1) |
| Modelo sem nome | `"modelo": { "versao": "1.0" }` | Seção 3.3 (`modelo.nome` obrigatório) |
| Modelo como texto | `"modelo": "pysentimiento/bertweet-pt-sentiment"` | Seção 3.3 (`modelo` é um objeto) |
| Rótulo padronizado na sigla do importador | `"rotulo_padronizado": "POS"` | Seção 3.3 (convertido para `positivo`, `negativo` ou `neutro`) |

### 4.6 Correspondência com os dados de entrada

O importador (`src/processamento/aquisicao/`, issues #1 e #2) entrega cada
registro com os campos abaixo. **Hoje o pipeline**, antes da persistência futura,
faz as conversões a seguir:

| Campo entregue pelo importador | Campo no MongoDB | Conversão |
|---|---|---|
| `id_origem` | `id_origem` | Nenhuma |
| `texto_original` | `texto_original` | Nenhuma |
| `fonte` | `fonte` | Nenhuma |
| `rotulo_original` | `rotulo_original` | Nenhuma. Omitido quando `None` |
| `rotulo_padronizado` (`POS`, `NEG`, `NEU`) | `rotulo_padronizado` | Convertido para `positivo`, `negativo` ou `neutro` com `converter_rotulo_para_sentia()`. Omitido quando `None` |
| `data_publicacao` (texto, ex.: `2026-10-01`) | `data_publicacao` | Convertida para `Date` em UTC. Omitida quando `None` |
| `metadados` | `metadados` | Nenhuma. Omitido quando o importador não o entrega |

O importador aceita nomes alternativos de colunas e os converte antes da
Persistência. Por exemplo, no CSV padrão `id` → `id_origem`, `texto` →
`texto_original`, `rotulo` ou `sentimento` → `rotulo_original` e `data` →
`data_publicacao`; no BPSAD, `review_id` → `id_origem`, `review_text` →
`texto_original`, `rating` → `rotulo_original`, `dataset` → `fonte` e
`review_date` → `data_publicacao`.

Os demais campos são preenchidos pelo sistema: `sentimento`,
`probabilidades` e `modelo` pela Classificação (issues #9 e #16), e
`data_processamento` por `PipelineClassificacao`, antes de qualquer gravação.
A camada de persistência futura deverá preservar esses valores e os tipos BSON.

### 4.7 Consultas de exemplo

Consultas que a API deverá fazer para atender ao dashboard. Os filtros são
aplicados no próprio banco, conforme a meta de desempenho da arquitetura.
**Todo filtro por período declara qual data utiliza.**

| Necessidade | Data usada | Consulta (filtro do Compass / mongosh) |
|---|---|---|
| Todas as análises (RF10) | - | `{}` |
| Por sentimento (RF12) | - | `{ "sentimento": "positivo" }` |
| Por período de publicação (RF11) | `data_publicacao` | `{ "data_publicacao": { "$gte": ISODate("2026-10-01"), "$lt": ISODate("2026-11-01") } }` |
| Por período de processamento | `data_processamento` | `{ "data_processamento": { "$gte": ISODate("2026-10-01"), "$lt": ISODate("2026-11-01") } }` |
| Sentimento + período de publicação | `data_publicacao` | `{ "sentimento": "negativo", "data_publicacao": { "$gte": ISODate("2026-10-01"), "$lt": ISODate("2026-11-01") } }` |
| Textos sem data de publicação | - | `{ "data_publicacao": { "$exists": false } }` |
| Por modelo | - | `{ "modelo.nome": "pysentimiento/bertweet-pt-sentiment" }` |

No filtro por período de publicação, documentos sem `data_publicacao` **não
aparecem no resultado**, pois não há data real para compará-los. Recomenda-se
que o dashboard informe isso ao usuário (ex.: "N textos sem data de publicação
não foram incluídos").  Como nenhum registro do TweetSentBR tem data, o filtro
por período de publicação não retorna nenhum tweet; a data usada por padrão
no dashboard (RF11) ainda precisa ser decidida pela equipe e pela Product Owner.

Contagem por sentimento, usada no gráfico de distribuição do dashboard:

```javascript
db.analises.aggregate([
  { $group: { _id: "$sentimento", total: { $sum: 1 } } }
])
```

Equivalente em Python (pymongo), como deverá ser usado pelo módulo de
Persistência na Sprint 4:

```python
from datetime import datetime, timezone

filtro = {
    "sentimento": "negativo",
    "data_publicacao": {
        "$gte": datetime(2026, 10, 1, tzinfo=timezone.utc),
        "$lt": datetime(2026, 11, 1, tzinfo=timezone.utc),
    },
}
analises = colecao.find(filtro)
```

## 5. Índices

Índices propostos acelerariam consultas da seção 4.7 e garantiriam unicidade
do par fonte/ID. Não foram criados automaticamente nesta referência. IDs
gerados incluem posição: não garantem deduplicação de conteúdo após reordenação.

| Nome | Campos | Tipo | Motivo |
|---|---|---|---|
| `uq_fonte_id_origem` | `fonte` + `id_origem` | Único | Impede gravar o mesmo texto da mesma fonte duas vezes (ex.: importar o mesmo dataset de novo) |
| `idx_sentimento_data_publicacao` | `sentimento` + `data_publicacao` | Composto | Filtro por sentimento (RF12) e por sentimento + período de publicação |
| `idx_data_publicacao` | `data_publicacao` | Simples | Filtro somente por período de publicação (RF11) |
| `idx_data_processamento` | `data_processamento` | Simples | Filtro por período de processamento |

Criação no mongosh (a ser automatizada no código da Persistência, na Sprint 4):

```javascript
db.analises.createIndex({ fonte: 1, id_origem: 1 }, { unique: true, name: "uq_fonte_id_origem" })
db.analises.createIndex({ sentimento: 1, data_publicacao: 1 }, { name: "idx_sentimento_data_publicacao" })
db.analises.createIndex({ data_publicacao: 1 }, { name: "idx_data_publicacao" })
db.analises.createIndex({ data_processamento: 1 }, { name: "idx_data_processamento" })
```

O `1` indica ordem crescente. O campo `_id` já possui índice automático.


## 6. Limites de implementação e validação no PC1

Os JSON são exemplos sintéticos, não resultados de inserção. `texto_tratado`
do exemplo baseline é ilustrativo; não comprova stemming/stopwords no baseline
atual. `probabilidades` é opcional no esquema geral, mas o pipeline atual exige
as três probabilidades do classificador. As consultas e índices acima são
propostas para #20/#23–#25, não rotinas disponíveis na API.

A regra de metadados sem identificação de autores é política documental. O
importador aceita colunas extras e o pipeline copia o dicionário; não há
sanitização automática que garanta essa regra para CSV arbitrário. A coleta
XFetch do #65 tem contrato próprio e está ausente desta referência.
O filtro temporal do mock usa publicação provisoriamente; decisão oficial e
fuso continuam pendentes em #24.

Ver [contratos observados](../contratos-dados.md),
[testes do pipeline](../../tests/test_pipeline.py) e
[ensaio atual](../qa/pc1/RELATORIO_ENSAIO_FINAL.md).
