# Esquema de documentos do MongoDB - SentIA


### Histórico de revisões

| Data | Versão | Descrição | Autor(a) |
|---|---|---|---|
| 27/10/2026 | 0.1 | Estrutura inicial, visão geral, convenções e decisões de modelagem | Maria Eduarda |
| 27/10/2026 | 0.2 | Definição dos campos e tipos do documento | Maria Eduarda |

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

Campos marcados com ⏳ dependem de confirmação das demais frentes
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
| `data_publicacao` | Date | ⏳ Não | Data em que o texto foi publicado na fonte (coluna `data` do CSV). Base do filtro por período (RF11) quando disponível |
| `data_processamento` | Date | Sim | Data e hora em que o texto foi classificado e gravado. Preenchida pelo próprio sistema, por isso sempre existe |

### 3.5 Metadados adicionais

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `metadados` | Object | Não | Informações extras específicas de cada fonte (ex.: programa de TV relacionado ao tweet). Não deve conter dados que identifiquem o autor (ver seção 2.1) |

## 4. Exemplo JSON

## 5. Índices

## 6. Pendências e decisões em aberto
