# Esquema de documentos do MongoDB - SentIA



## 1. Visão geral

Este documento define o formato dos documentos que o SentIA armazena no
MongoDB. Cada texto analisado é salvo como um documento contendo o texto,
seus metadados e o resultado da classificação de sentimento. Serve como contrato entre as frentes de Banco, Dados, Machine
Learning e API.

O banco é acessado somente pelo módulo de Persistência (pymongo), conforme a
seção 2.4.2 do Documento de Arquitetura. A API consulta esses documentos para
alimentar o dashboard, aplicando os filtros por período (RF11) e por
sentimento (RF12) diretamente na consulta ao banco.



**Escopo:** apenas documenta e definev o esquema. A
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

- **Quem grava:** somente o módulo de Persistência, ao receber o resultado da
  Classificação (texto, metadados, sentimento e identificação do modelo).
- **Quem lê:** somente o módulo de Persistência, a pedido da API. A interface
  nunca acessa o banco diretamente.
- **Preparação do texto:** o classificador BERTweet realiza a própria
  tokenização. Um pré-processamento externo (limpeza, stopwords, stemming,
  TF-IDF) só existe em modelos alternativos, como o baseline.

### 1.2 Requisitos atendidos

| Requisito | Como o esquema atende |
|---|---|
| RF07 – Classificação em três classes | O campo de sentimento aceita apenas `positivo`, `negativo` ou `neutro` |
| RF08 – Persistência das análises | Cada documento guarda o texto, seus metadados e o resultado da análise |
| RF10 – Consulta das análises | Os documentos ficam em uma única collection, consultada pela API |
| RF11 – Filtro por período | As datas são armazenadas no tipo `Date`, e cada consulta declara qual data utiliza (seção 4.6) |
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
  documentos sem o campo, usa-se `$exists: false` (seção 4.6).
- **Privacidade (LGPD).** Não são armazenados dados que identifiquem o autor
  do texto, como nome de usuário ou perfil, pois não são necessários para a
  análise de sentimentos.

### 2.2 Ambiente

A configuração do MongoDB (local ou Atlas) e o teste de conexão via pymongo
são tratados na issue #12. Este esquema vale para os dois ambientes.

## 3. Campos do documento

### 3.1 Identificação e origem

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | Sim (automático) | Identificador único do documento, gerado pelo MongoDB |
| `id_origem` | String | Sim | Identificador do texto na fonte original. Junto com `fonte`, evita que o mesmo texto seja gravado duas vezes |
| `fonte` | String | Sim | Nome do dataset ou da coleta de onde o texto veio, conforme definido na issue #3. Exigido pela arquitetura (RF08) |

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
| `modelo.versao` | String | ⏳ Não | Versão do modelo ou do checkpoint utilizado, a ser definida na issue #16 |
| `rotulo_original` | String | Não | Sentimento **anotado manualmente** na fonte, quando existir. Mesmos valores de `sentimento`. Permite comparar a previsão com o rótulo humano e medir a acurácia. Nunca é preenchido com a previsão do modelo |

### 3.4 Datas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `data_publicacao` | Date | Não | Data real em que o texto foi publicado, quando a fonte a informa. Nunca é substituída por outra data |
| `data_processamento` | Date | Sim | Data e hora em que o texto foi classificado e gravado. Preenchida pelo próprio sistema, por isso sempre existe |

### 3.5 Metadados adicionais

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `metadados` | Object | Não | Informações extras específicas de cada fonte (ex.: categoria ou tema do texto). O conteúdo varia conforme a fonte. Não deve conter dados que identifiquem o autor (ver seção 2.1) |

## 4. Exemplos JSON

Os exemplos usam o formato *Extended JSON* do MongoDB, no qual as datas são
escritas como `{ "$date": "..." }` para indicar que são do tipo `Date`, e não
texto. Os mesmos exemplos estão na pasta [`exemplos/`](exemplos/) e podem ser
importados no MongoDB Compass (*ADD DATA → Import JSON or CSV file*).

Os nomes de fontes, os textos, as probabilidades e o nome do modelo baseline
(`baseline-tfidf-logreg`) são ilustrativos; as fontes reais serão definidas na
issue #3, e o nome e a versão dos modelos, na issue #16. O campo `_id` não aparece porque é gerado pelo MongoDB
no momento da gravação.

### 4.1 Documento completo (BERTweet)

Fonte com data de publicação e rótulo original, classificada pelo BERTweet
([`exemplos/analise-completa.json`](exemplos/analise-completa.json)).
Não possui `texto_tratado`, pois o BERTweet usa tokenização própria:

```json
{
  "id_origem": "a_001",
  "fonte": "exemplo_dataset_rotulado",
  "texto_original": "A programação da conferência foi ótima e trouxe inovação ao país!",
  "sentimento": "positivo",
  "probabilidades": { "positivo": 0.91, "negativo": 0.03, "neutro": 0.06 },
  "modelo": { "nome": "pysentimiento/bertweet-pt-sentiment", "versao": "a-definir" },
  "rotulo_original": "positivo",
  "data_publicacao": { "$date": "2026-10-01T00:00:00Z" },
  "data_processamento": { "$date": "2026-10-29T14:30:00Z" },
  "metadados": { "categoria": "eventos" }
}
```

### 4.2 Documento classificado por outro modelo (baseline)

O mesmo esquema atende a um modelo diferente. O baseline TF-IDF usa
pré-processamento externo, por isso `texto_tratado` aparece
([`exemplos/analise-baseline.json`](exemplos/analise-baseline.json)):

```json
{
  "id_origem": "a_002",
  "fonte": "exemplo_dataset_rotulado",
  "texto_original": "O relatório técnico sobre inteligência artificial foi publicado hoje.",
  "texto_tratado": "relatório técnico inteligência artificial publicado hoje",
  "sentimento": "neutro",
  "probabilidades": { "positivo": 0.12, "negativo": 0.08, "neutro": 0.80 },
  "modelo": { "nome": "baseline-tfidf-logreg", "versao": "a-definir" },
  "rotulo_original": "neutro",
  "data_publicacao": { "$date": "2026-10-03T00:00:00Z" },
  "data_processamento": { "$date": "2026-10-29T14:31:00Z" }
}
```

### 4.3 Documento mínimo

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

### 4.4 Documentos inválidos

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

### 4.5 Correspondência com os dados de entrada

O contrato de registros da issue #3 entrega os campos abaixo, que são
convertidos da seguinte forma:

| Campo de entrada (#3) | Campo no MongoDB | Observação |
|---|---|---|
| `id_origem` | `id_origem` | |
| `texto` | `texto_original` | |
| `fonte` | `fonte` | |
| rótulo original, quando houver | `rotulo_original` | Rótulo humano, não a previsão do modelo. Omitido se a fonte não tiver rótulo |
| `data_publicacao`, quando existir | `data_publicacao` | Convertida de texto para `Date`. Omitida se a fonte não tiver data |

O CSV usado nos testes da issue #4 (colunas `id`, `texto`, `sentimento`,
`fonte`, `data`) segue a mesma correspondência: `id` → `id_origem`,
`sentimento` → `rotulo_original` e `data` → `data_publicacao`.

Os demais campos são preenchidos pelo sistema: `sentimento`,
`probabilidades` e `modelo` pela Classificação (issues #9 e #16), e
`data_processamento` pela Persistência.

### 4.6 Consultas de exemplo

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
não foram incluídos").

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

Índices aceleram as consultas da seção 4.6 e garantem a unicidade dos textos.

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

