# Esquema de documentos do MongoDB - SentIA


### Histórico de revisões

| Data | Versão | Descrição | Autor(a) |
|---|---|---|---|
| 27/10/2026 | 1.0 | Estrutura inicial, visão geral, convenções e decisões de modelagem | Maria Eduarda |


## 1. Visão geral

Este documento define o formato dos documentos que o SentIA armazena no
MongoDB. Cada texto analisado (por exemplo, um tweet) é salvo como um
documento contendo o texto, seus metadados e o resultado da classificação
de sentimento.

O banco é acessado somente pelo módulo de Persistência (pymongo), conforme a
seção 2.4.2 do Documento de Arquitetura. A API consulta esses documentos para
alimentar o dashboard, aplicando os filtros por período (RF11) e por
sentimento (RF12) diretamente na consulta ao banco.

Este documento é uma preparação para a Sprint 4, quando a persistência será
implementada. Ele serve como contrato entre as frentes de Banco, Machine
Learning e API.

| Item | Valor |
|---|---|
| Banco de dados | `sentia` |
| Collection | `analises` |
| Um documento representa | um texto analisado |

### 1.1 Onde o banco entra no fluxo

```
Dataset / coleta ─► Aquisição ─► Pré-processamento ─► Classificação ─► Persistência ─► MongoDB
                                                                                          │
                                         Dashboard (Streamlit) ◄─ API (FastAPI) ◄─────────┘
```

- **Quem grava:** somente o módulo de Persistência, ao receber o resultado da
  Classificação (texto, metadados e sentimento).
- **Quem lê:** somente o módulo de Persistência, a pedido da API. A interface
  nunca acessa o banco diretamente.

### 1.2 Requisitos atendidos

| Requisito | Como o esquema atende |
|---|---|
| RF07 – Classificação em três classes | O campo de sentimento aceita apenas `positivo`, `negativo` ou `neutro` |
| RF08 – Persistência das análises | Cada documento guarda o texto, seus metadados e o resultado da análise |
| RF10 – Consulta das análises | Os documentos ficam em uma única collection, consultada pela API |
| RF11 – Filtro por período | As datas são armazenadas no tipo `Date`, permitindo consultas por intervalo |
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
- **Metadados variáveis no próprio documento.** Fontes diferentes podem trazer
  informações diferentes; o modelo de documentos do MongoDB permite isso sem
  alterar a estrutura existente (meta de escalabilidade da arquitetura).
- **Privacidade (LGPD).** Não são armazenados dados que identifiquem o autor
  do texto, como nome de usuário ou perfil, pois não são necessários para a
  análise de sentimentos.

### 2.2 Ambiente

A configuração do MongoDB (local ou Atlas) e o teste de conexão via pymongo
são tratados na issue #12. Este esquema vale para os dois ambientes.

## 3. Campos do documento

Campos marcados com dependem de confirmação das demais frentes
(ver seção 6) e podem mudar de obrigatórios para opcionais, ou vice-versa.

### 3.1 Identificação e origem

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `_id` | ObjectId | Sim (automático) | Identificador único do documento, gerado pelo MongoDB |
| `id_origem` | String | Sim | Identificador do texto na fonte original (ex.: `tw_001`, coluna `id` do CSV). Junto com `fonte`, evita que o mesmo texto seja gravado duas vezes |
| `fonte` | String | Sim | Origem do texto (ex.: `TweetSentBR`). Exigido pela arquitetura (RF08) |

### 3.2 Texto

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `texto_original` | String | Sim | Texto exatamente como foi obtido da fonte (coluna `texto` do CSV) |
| `texto_tratado` | String | ⏳ Não | Texto após o pré-processamento do projeto (RF03 a RF05). Opcional porque o classificador BERTweet realiza o próprio tratamento do texto |

### 3.3 Resultado da classificação

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `sentimento` | String | Sim | Sentimento previsto pelo modelo. Valores aceitos: `positivo`, `negativo`, `neutro` (RF07) |
| `probabilidades` | Object | Não | Probabilidade de cada classe, como devolvida pelo módulo de classificação |
| `probabilidades.positivo` | Double | Sim, se `probabilidades` existir | Valor entre 0 e 1 |
| `probabilidades.negativo` | Double | Sim, se `probabilidades` existir | Valor entre 0 e 1 |
| `probabilidades.neutro` | Double | Sim, se `probabilidades` existir | Valor entre 0 e 1 |
| `modelo` | String | Sim | Modelo que realizou a classificação (ex.: `pysentimiento/bertweet-pt-sentiment`). Permite rastrear qual modelo gerou cada resultado caso ele seja trocado |
| `rotulo_original` | String | Não | Sentimento anotado manualmente no dataset, quando existir (coluna `sentimento` do CSV). Mesmos valores de `sentimento`. Permite comparar a previsão com o rótulo humano e medir a acurácia |

### 3.4 Datas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `data_publicacao` | Date |  Não | Data em que o texto foi publicado na fonte (coluna `data` do CSV). Base do filtro por período (RF11) quando disponível |
| `data_processamento` | Date | Sim | Data e hora em que o texto foi classificado e gravado. Preenchida pelo próprio sistema, por isso sempre existe |

### 3.5 Metadados adicionais

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `metadados` | Object | Não | Informações extras específicas de cada fonte (ex.: programa de TV relacionado ao tweet). Não deve conter dados que identifiquem o autor (ver seção 2.1) |

## 4. Exemplo JSON

Os exemplos usam o formato *Extended JSON* do MongoDB, no qual as datas são
escritas como `{ "$date": "..." }` para indicar que são do tipo `Date`, e não
texto. Os mesmos exemplos estão na pasta [`exemplos/`](exemplos/) e podem ser
importados no MongoDB Compass (*ADD DATA → Import JSON or CSV file*).

### 4.1 Documento completo

Todos os campos preenchidos ([`exemplos/analise-completa.json`](exemplos/analise-completa.json)):

```json
{
  "id_origem": "tw_001",
  "fonte": "TweetSentBR",
  "texto_original": "A programação da conferência foi ótima e trouxe inovação ao país!",
  "texto_tratado": "programação conferência ótima trouxe inovação país",
  "sentimento": "positivo",
  "probabilidades": { "positivo": 0.91, "negativo": 0.03, "neutro": 0.06 },
  "modelo": "pysentimiento/bertweet-pt-sentiment",
  "rotulo_original": "positivo",
  "data_publicacao": { "$date": "2026-10-01T00:00:00Z" },
  "data_processamento": { "$date": "2026-10-27T14:30:00Z" },
  "metadados": { "programa": "exemplo" }
}
```

O campo `_id` não aparece porque é gerado pelo MongoDB no momento da gravação.

### 4.2 Documento mínimo

Somente os campos obrigatórios ([`exemplos/analise-minima.json`](exemplos/analise-minima.json)):

```json
{
  "id_origem": "tw_002",
  "fonte": "TweetSentBR",
  "texto_original": "Péssimo serviço de atenção ao usuário, não recomendo de jeito nenhum.",
  "sentimento": "negativo",
  "modelo": "pysentimiento/bertweet-pt-sentiment",
  "data_processamento": { "$date": "2026-10-27T14:30:05Z" }
}
```

### 4.3 Documentos inválidos

Exemplos que **não** obedecem ao esquema e devem ser recusados
([`exemplos/analises-invalidas.json`](exemplos/analises-invalidas.json)):

| Problema | Trecho | Regra violada |
|---|---|---|
| Sentimento fora dos valores aceitos | `"sentimento": "feliz"` | Seção 2 e RF07 |
| Sentimento com letra maiúscula | `"sentimento": "POS"` | Seção 2 |
| Data gravada como texto | `"data_processamento": "27/10/2026"` | Seção 2 (datas no tipo `Date`) |
| Campo obrigatório ausente | documento sem `texto_original` | Seção 3.2 |
| Probabilidade fora do intervalo | `"positivo": 1.7` | Seção 3.3 (valor entre 0 e 1) |

### 4.4 Correspondência com o CSV de entrada

As colunas do CSV de importação (usadas nos testes da issue #4) são
convertidas nos seguintes campos:

| Coluna do CSV | Campo no MongoDB | Observação |
|---|---|---|
| `id` | `id_origem` | |
| `texto` | `texto_original` | |
| `sentimento` | `rotulo_original` | Rótulo humano do dataset, não a previsão do modelo |
| `fonte` | `fonte` | |
| `data` | `data_publicacao` | Convertida de texto (`2026-10-01`) para `Date` |

Os campos `sentimento`, `probabilidades` e `modelo` são preenchidos pela
Classificação, e `data_processamento` pela Persistência.

### 4.5 Consultas de exemplo

Consultas que a API deverá fazer para atender ao dashboard. Os filtros são
aplicados no próprio banco, conforme a meta de desempenho da arquitetura.

| Necessidade | Consulta (filtro do Compass / mongosh) |
|---|---|
| Todas as análises (RF10) | `{}` |
| Por sentimento (RF12) | `{ "sentimento": "positivo" }` |
| Por período (RF11) | `{ "data_publicacao": { "$gte": ISODate("2026-10-01"), "$lt": ISODate("2026-11-01") } }` |
| Período + sentimento | `{ "sentimento": "negativo", "data_publicacao": { "$gte": ISODate("2026-10-01"), "$lt": ISODate("2026-11-01") } }` |

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

Índices aceleram as consultas da seção 4.5 e garantem a unicidade dos textos.

| Nome | Campos | Tipo | Motivo |
|---|---|---|---|
| `uq_fonte_id_origem` | `fonte` + `id_origem` | Único | Impede gravar o mesmo texto da mesma fonte duas vezes (ex.: importar o mesmo CSV de novo) |
| `idx_sentimento_data` | `sentimento` + `data_publicacao` | Composto | Filtro por sentimento (RF12) e por sentimento + período |
| `idx_data_publicacao` | `data_publicacao` | Simples | Filtro somente por período (RF11) |

Criação no mongosh (a ser automatizada no código da Persistência):

```javascript
db.analises.createIndex({ fonte: 1, id_origem: 1 }, { unique: true, name: "uq_fonte_id_origem" })
db.analises.createIndex({ sentimento: 1, data_publicacao: 1 }, { name: "idx_sentimento_data" })
db.analises.createIndex({ data_publicacao: 1 }, { name: "idx_data_publicacao" })
```

O `1` indica ordem crescente. O campo `_id` já possui índice automático.

## 6. Pendências e decisões em aberto

| # | Pendência | Decisão provisória | Depende de |
|---|---|---|---|
| P1 | O TweetSentBR possui data de publicação dos tweets? | `data_publicacao` opcional. Documentos sem data são gravados normalmente, mas não aparecem quando o filtro por período é aplicado | Ricardo e Gabriel (issue #3) |
| P2 | Se não houver data no dataset, como atender ao filtro por período (RF11)? | Em aberto. Opções: (a) filtrar por `data_processamento`; (b) usar outra fonte de dados com data; (c) aceitar o filtro apenas para dados coletados | Equipe e Product Owner |
| P3 | O classificador gera texto tratado para armazenar? | `texto_tratado` opcional, pois o BERTweet faz o próprio tratamento | Ricardo e Gabriel |
| P4 | As colunas do CSV de entrada serão `id, texto, sentimento, fonte, data`? | Mapeamento da seção 4.4, baseado nos testes da issue #4 | Breno |
| P5 | Ambiente do MongoDB (local ou Atlas) | Não afeta o esquema | Julia (issue #12) |


