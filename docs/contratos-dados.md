# Contrato Único de Dados — Aquisição, Pipeline ML, MongoDB, API e Painel

Referência canônica do contrato de dados do SentIA entre as camadas de **Dados (Aquisição)**, **ML (Classificação/Pipeline)**, **Banco (MongoDB)**, **Serviço (FastAPI)** e **Apresentação (Streamlit)** ([issue #19](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/19)).

Revisão documental sobre `origin/developer` após os PRs [#75](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/75), [#78](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/78) e [#80](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/80). O estado implementado abaixo não representa homologação das frentes nem aceite da Product Owner; ambos permanecem pendentes (seção 10).

---

## 1. Visão Geral por Frente (Revisão de Integração)

| Frente | Módulo / Referência | Entrada | Saída | Estado na `developer` |
|---|---|---|---|---|
| **Dados (Aquisição)** | [`src/processamento/aquisicao/`](../src/processamento/aquisicao/) (`csv_importer.py`, `tweetsentbr.py`, `bpsad_adapter.py`, `xfetch.py`) | Arquivos CSV/TSV locais ou respostas paginadas da API XFetch | `dict[str, Any]` padronizado sem inferência de modelo | Implementado e testado |
| **ML (Classificação e Pipeline)** | [`src/processamento/classificacao/`](../src/processamento/classificacao/) e [`src/processamento/pipeline.py`](../src/processamento/pipeline.py) | `Iterable[dict[str, Any]]` da aquisição | Documento `dict[str, Any]` pronto para BSON (`sentimento`, `probabilidades`, `modelo`, datas UTC) | Implementado e testado |
| **Banco (MongoDB)** | [`src/dados/database.py`](../src/dados/database.py), [`src/dados/repositorio.py`](../src/dados/repositorio.py) e [`docs/banco/esquema-mongodb.md`](banco/esquema-mongodb.md) | Conexão via `MONGODB_URI` e documentos do pipeline | Inserção unitária/em lote, índices, deduplicação, consultas paginadas e agregação | Implementado (#20, #23–#25); não há atualização/exclusão de análises nem persistência da Administração |
| **Serviço (API FastAPI)** | [`src/servico/main.py`](../src/servico/main.py), [`src/servico/administracao.py`](../src/servico/administracao.py) e [`docs/frontend/CONTRATO-API.md`](frontend/CONTRATO-API.md) | Lotes de registros, consultas MongoDB e requisições administrativas | JSON HTTP com esquemas Pydantic e respostas administrativas | Health, POST/GET de análises, resumo e Administração implementados (PRs #75, #78 e #80) |
| **Apresentação (Painel)** | [`src/apresentacao/contrato.py`](../src/apresentacao/contrato.py) e [`src/apresentacao/fontes/`](../src/apresentacao/fontes/) | Respostas JSON da API (`FonteApi`, `AdministracaoApi`) ou dados simulados (`FonteMock`, `AdministracaoMock`) | Dataclasses imutáveis (`Analise`, `PaginaAnalises`, `ResumoAnalises`, `FiltrosAnalises`, `Coleta`) | Implementado e testado |

---

## 2. Contrato de Campos por Etapa

Os adaptadores de aquisição alimentam `PipelineClassificacao.processar_registros()`, cujo documento de saída segue o esquema da coleção `analises` no MongoDB ([`docs/banco/esquema-mongodb.md`](banco/esquema-mongodb.md)) e o item de `GET /analises` ([`docs/frontend/CONTRATO-API.md`](frontend/CONTRATO-API.md)).

| Campo | Aquisição (`dict`) | Pipeline / MongoDB (`analises`) | API HTTP (`GET /analises`) | Responsável | Regra de Contrato e Validação |
|---|---|---|---|---|---|
| `_id` | *Ausente* | `ObjectId` (gerado pelo MongoDB) | **Não exposto** | Banco | Chave técnica interna; a consulta projeta `_id: 0` e o modelo de resposta não inclui esse campo; chave de negócio `(fonte, id_origem)` |
| `id_origem` | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | Aquisição → Pipeline → Banco → API | ID nativo do registro na origem ou hash determinístico SHA-256 (`{fonte}_{pos:06d}_{sha256[:12]}`) |
| `fonte` | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str`) | Aquisição → Pipeline → Banco → API | Proveniência do texto (`"TweetSentBR"`, `"b2w"`, `"olist"`, `"X"`, etc.) |
| `texto_original` | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str`) | Aquisição → Pipeline → Banco → API | Texto bruto preservado; enviado ao BERTweet sem remoção de stopwords ou stemming ([ADR-001](decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md)) |
| `texto_tratado` | *Ausente* | Opcional no esquema (`str`); não gerado pelo pipeline BERTweet | Não incluído no modelo de resposta atual | ML (apenas baseline clássico) | Exclusivo para experimentos com modelos clássicos (`baseline.py`); **nunca** exigido no fluxo BERTweet |
| `rotulo_original` | Opcional (`str \| None`) | Opcional (`str`, **omitido** se `None`) | Opcional | Aquisição → Pipeline | Rótulo humano bruto ou nota original do dataset (ex.: `"5"`, `"1"`, `"positivo"`). **Nunca** recebe previsão do modelo |
| `rotulo_padronizado` | Opcional (`"POS" \| "NEG" \| "NEU" \| None`) | Opcional (`"positivo" \| "negativo" \| "neutro"`, **omitido** se `None`) | Opcional | Aquisição → Pipeline | Rótulo humano convertido por `converter_rotulo_para_sentia()`; ausente em textos não rotulados (como coletas do X) |
| `sentimento` | *Não criado na aquisição* | **Obrigatório** (`"positivo" \| "negativo" \| "neutro"`) | **Obrigatório** (`"positivo" \| "negativo" \| "neutro"`) | ML → Pipeline → Banco → API | Classe prevista pelo modelo em português e minúsculas |
| `probabilidades` | *Não criado na aquisição* | **Obrigatório no pipeline**; opcional no esquema MongoDB (`dict[str, float]`) | `dict[str, float]` ou `null`; não consumido por `FonteApi` | ML → Pipeline → Banco | Pipeline valida chaves exatas `positivo`, `negativo` e `neutro`, valores numéricos finitos em `[0, 1]` com soma `1.0 ± 0.001` |
| `modelo` | *Não criado na aquisição* | **Obrigatório** (`{"nome": str, "versao"?: str}`) | **Obrigatório** (`{"nome": str, ...}`) | ML → Pipeline → Banco → API | Objeto com `modelo.nome` (`str` não vazia) obrigatório; `modelo.versao` incluído quando informado |
| `data_publicacao` | Opcional (`str \| None`) | Opcional (BSON `Date` UTC, **omitido** se `None`) | Opcional (`str` ISO 8601 com fuso ou `null`) | Aquisição → Pipeline → Banco → API | Data real da publicação na origem; **jamais** inventada quando ausente |
| `data_processamento` | *Não criado na aquisição* | **Obrigatório** (BSON `Date` UTC) | **Obrigatório** (`str` ISO 8601 com fuso) | Pipeline → Banco → API | Instante UTC em que o pipeline classificou o registro (`datetime.now(timezone.utc)`) |
| `metadados` | Opcional (`dict \| None`) | Opcional (`dict`, **omitido** se vazio/`None`) | `dict` ou `null` | Aquisição → Pipeline | Atributos auxiliares; a regra de não incluir identificadores de autor tem proteção específica no adaptador XFetch (seção 3) |

**Validações efetivas e limites:** [`validar_analise`](../src/dados/repositorio.py) verifica os três textos obrigatórios, sentimento canônico, objeto `modelo` com `nome` preenchido e datas `datetime` com fuso. Não implementa um validador MongoDB `$jsonSchema` nem repete toda a validação de probabilidades/rótulos do pipeline. Em particular, a verificação de `modelo.nome` no repositório é de preenchimento; a exigência de string não vazia é validada pelo pipeline e pelo cliente `FonteApi`. Estas diferenças não alteram o contrato esperado e precisam ser revistas pelas frentes.

[`RegistroEntrada`](../src/servico/esquemas.py) recebe `id_origem`, `fonte`, `texto_original` e os opcionais de aquisição; proíbe campos extras (incluindo `sentimento`, `probabilidades` e `data_processamento`, gerados pelo sistema). `LoteEntrada.registros` aceita de 1 a 1000 itens. Na leitura, `AnaliseSaida` preenche opcionais ausentes com `null`, inclusive os rótulos humanos e `data_publicacao`; o documento BSON gerado pelo pipeline os omite quando ausentes.

---

## 3. Regras de Metadados e Privacidade por Fonte (Correção `XFetch`)

- **XFetch (`src/processamento/aquisicao/xfetch.py` — `buscar_tweets_xfetch`)**:
  - Como proteção de privacidade, a função `_normalizar_tweet` aplica uma lista de permissão estrita: `author_id`, `autor_id`, `user`, `username`, `author`, `user_id`, `screen_name` e `conversa_id` do payload não são copiados como campos estruturados para o registro nem para `metadados`. Isso não representa, isoladamente, homologação de conformidade com a LGPD ou anonimização de `texto_original`.
  - O campo `metadados` do XFetch (`dict[str, str | int]`) aceita **exclusivamente** a allowlist documentada no código:
    - `provedor`: sempre `"XFetch"`;
    - `lang`: código de idioma (`str` não vazia), quando informado pelo payload;
    - métricas públicas inteiras não negativas: `like_count`, `retweet_count`, `reply_count` e `quote_count`.
  - Registros do XFetch sempre saem da aquisição com `fonte="X"`, `rotulo_original=None` e `rotulo_padronizado=None`.
- **CSV Genérico (`src/processamento/aquisicao/csv_importer.py`)**:
  - Exige colunas `texto` (ou `texto_original`) e `fonte` em UTF-8 (com ou sem BOM).
  - Colunas extras com valor não vazio são copiadas para `metadados` como `dict[str, str]`; quando não há colunas extras preenchidas, `metadados` é `None` na aquisição e omitido no documento BSON.
- **BPSAD (`src/processamento/aquisicao/bpsad_adapter.py`)**:
  - Mapeia `review_text` → `texto_original`, `rating` → `rotulo_original` e converte notas de 1 a 5 para `rotulo_padronizado` (`< 2.5` → `"NEG"`, `< 3.5` → `"NEU"`, `>= 3.5` → `"POS"`), preservando atributos extras (como `category`, `polarity`) em `metadados`.
- **TweetSentBR (`src/processamento/aquisicao/tweetsentbr.py`)**:
  - Lê o corpus local com `fonte="TweetSentBR"`, normaliza rótulos para `"POS"`, `"NEG"` ou `"NEU"` e mantém `data_publicacao=None` quando o corpus não fornece timestamp de publicação.

**Limite da proteção:** CSV/BPSAD copiam colunas extras, e `POST /analises` aceita um dicionário arbitrário em `metadados`; pipeline e repositório não aplicam a allowlist do XFetch a essas entradas. O texto original é preservado, inclusive possíveis `@menções`. A regra de não armazenar identificadores de autor continua vigente; curadoria, anonimização e aceite de privacidade dependem de Dados e da PO, conforme as pendências de [`docs/tweetsentbr.md`](tweetsentbr.md).

---

## 4. Datas e Fuso Horário (UTC)

1. **`data_publicacao` ausente**:
   - Quando a fonte não possui data de publicação (`None` ou string vazia), o pipeline **omite** a chave `data_publicacao` no documento BSON (não grava `null` nesse fluxo e nunca usa `data_processamento` como substituta).
   - Na API HTTP (`GET /analises`), a ausência é representada por `"data_publicacao": null`, que o cliente `FonteApi` converte para `Analise.data_publicacao = None` (o cliente também aceita a chave omitida).
   - Em consultas com filtro de período (`inicio` e/ou `fim`), registros sem `data_publicacao` ficam fora do recorte temporal e sua quantidade é informada em `sem_data_publicacao` no endpoint `GET /analises/resumo`. Sem filtro de período ativo (`inicio=None` e `fim=None`), `sem_data_publicacao` é obrigatoriamente `0`.
2. **`data_publicacao` apenas com data de calendário (`YYYY-MM-DD`)**:
   - Aceita pelo pipeline para compatibilidade com datasets como BPSAD e convertida para meia-noite UTC (`datetime(ano, mes, dia, 0, 0, tzinfo=timezone.utc)`).
3. **`data_publicacao` e `data_processamento` com data e hora**:
   - Devem estar em formato ISO 8601 com **fuso horário explícito** (`Z` ou deslocamento `±HH:MM`, ex.: `2026-11-03T12:00:00-03:00`) e são convertidas para UTC (`timezone.utc`).
   - O pipeline rejeita strings de data-hora sem fuso (ex.: `2026-11-03T12:00:00`) e formatos locais (`29/10/2026`). O repositório exige `datetime` com fuso, não strings; `FonteApi` exige ISO 8601 com horário e fuso (`ErroFonteDados`).
   - BSON `Date` armazena instantes UTC com precisão de milissegundos. O driver retorna `datetime` sem `tzinfo` por padrão; `AnaliseSaida` atribui UTC a esses valores de leitura e normaliza offsets antes de serializar. Isso não autoriza datas sem fuso na entrada do pipeline.
4. **Filtros implementados (PR #80)**:
   - `inicio` e `fim` exigem `AAAA-MM-DD` e usam `data_publicacao`, de 00:00:00 UTC no primeiro dia até o final do último dia, inclusive. Intervalos invertidos ou inválidos retornam `422`.
   - `sem_data_publicacao` conta campos ausentes ou nulos excluídos pelo período, respeitando o filtro de sentimento. Sem período, vale zero; os excluídos não entram no total filtrado.
   - **Pendente de validação da PO:** confirmar a escolha de `data_publicacao` como referência temporal. A implementação existente não equivale a aprovação dessa decisão.

---

## 5. Identificação e Regra de Duplicação

1. **Na aquisição (`csv_importer.py` e `tweetsentbr.py`)**:
   - Se `id_origem` vier preenchido na fonte, é preservado (`str.strip()`).
   - Se `id_origem` estiver ausente, é gerado de forma determinística via SHA-256 sobre fonte, posição dentro da fonte (base 1), texto, rótulo humano bruto e data de publicação, com as strings aparadas:
     `"{fonte_normalizada}_{posicao:06d}_{sha256[:12]}"` (ex.: `"TweetSentBR_000001_0a1b2c3d4e5f"`).
2. **Na coleta paginada (`xfetch.py`)**:
   - `id_origem` é obrigatório em cada item retornado pela API externa. Itens repetidos com o mesmo `id_origem` na mesma execução paginada são descartados em memória, preservando a primeira ocorrência.
3. **No MongoDB (`coleção analises`)**:
   - A unicidade é imposta pelo índice único composto `uq_fonte_id_origem` em `{"fonte": 1, "id_origem": 1}` (`unique: true`).
   - Dois documentos com o mesmo `id_origem` e a mesma `fonte` configuram duplicata (erro `11000` / `DuplicateKeyError` no PyMongo) e não devem gerar segunda gravação.
   - O mesmo `id_origem` em fontes distintas (ex.: `fonte="b2w"` e `fonte="X"`) é válido e permitido.
   - [`salvar_analise`](../src/dados/repositorio.py) retorna `True` para inserção e `False` para duplicata. `salvar_analises` valida todo o lote antes da escrita, usa `insert_many(..., ordered=False)` e retorna `inseridos` e `duplicados`; não atualiza documentos existentes. Falhas de escrita que não são duplicatas e erros de confirmação (`writeConcernErrors`) são propagados, podendo haver inserção parcial.
   - Os quatro índices da seção 5 do esquema MongoDB são criados por `criar_indices`, chamada pela dependência [`obter_colecao_analises`](../src/servico/dependencias.py). A configuração do banco usa o banco padrão da URI ou `sentia`, e a coleção é `analises`.

---

## 6. Formatos e Contratos de Erro por Camada

| Camada | Exceção / Código | Condições de Disparo | Comportamento / Mensagem |
|---|---|---|---|
| **Aquisição CSV** (`csv_importer.py`) | `ErroImportacaoCSV` | Arquivo inexistente/diretório, bytes fora de UTF-8, colunas `texto`/`fonte` ausentes, ou registro inválido em `modo_estrito=True` | Em `modo_estrito=False`, linhas inválidas não abortam o lote e são somadas em `RelatorioImportacao.descartes_por_motivo` (`texto_vazio`, `fonte_vazia`, `rotulo_invalido`, `data_invalida`) |
| **Aquisição XFetch** (`xfetch.py`) | `ErroXFetch`, `ValueError`, `TypeError` | `XFETCH_API_KEY` ausente, parâmetros fora dos limites (`quantidade` 1..100, `limite_por_pagina` 1..20, `max_paginas`), falha HTTP/rede, JSON inválido ou `data` não lista | Mensagens sanitizadas que nunca expõem URL/consulta, cabeçalhos ou chave da API |
| **Pipeline ML** (`pipeline.py`) | `ErroPipeline` / `ValueError`; `ErroInferencia` em falha operacional do classificador | Configuração, entradas ou previsões inválidas; exceção durante inferência | Valida textos/identificação/metadados antes da inferência; rótulos, datas e previsões durante a montagem da saída. A API distingue entrada inválida (`400`) de falha operacional de inferência (`503`) |
| **Conexão MongoDB** (`database.py`) | `ErroConfiguracaoMongoDB`, `ErroConexaoMongoDB` | `MONGODB_URI` ausente/vazia, `timeout_ms` não inteiro positivo, falha de DNS/URI, autenticação, rede ou `ping` | Fecha o cliente automaticamente se o `ping` falhar e **nunca** inclui `MONGODB_URI` ou credenciais na exceção/traceback |
| **Persistência e API de análises** (`repositorio.py`, `dependencias.py`, `main.py`) | `ErroAnaliseInvalida`, `PyMongoError`; HTTP `400`/`422`/`503` | Documento inválido, filtros/Pydantic inválidos ou indisponibilidade de banco/modelo | Erros de banco e falhas operacionais de inferência viram `503` com `{"detail": "..."}` genérico; validação do pipeline/repositório retorna `400`, Pydantic retorna `422` |
| **Cliente HTTP — Painel** (`api.py`, `administracao_api.py`) | `ErroFonteDados`, `ErroAutenticacao` | `400`/`415`/`422`, `401`/`403`, `404`, `413`, `429`, `5xx`/timeout/rede ou JSON fora do contrato | `FonteApi` usa mensagem genérica para filtros recusados (`400`/`422`) e demais erros HTTP. `AdministracaoApi` pode aproveitar `mensagem` de até 300 caracteres em `400`/`415`/`422`/`404`/`503`; `401`/`403` viram `ErroAutenticacao` |

---

## 7. Endpoints Implementados e Integrações Pendentes

Conforme [`src/servico/main.py`](../src/servico/main.py), [`src/apresentacao/contrato.py`](../src/apresentacao/contrato.py) e [`docs/frontend/CONTRATO-API.md`](frontend/CONTRATO-API.md):

| Método e Rota | Status no Backend (`src/servico/`) | Status no Cliente (`src/apresentacao/fontes/`) | Código HTTP Esperado | Contrato de Resposta / Observação |
|---|---|---|---|---|
| `GET /health` | **Implementado** (`src/servico/main.py`) | **Implementado** (`FonteApi.verificar_saude`) | `200 OK` | `{"status": "ok"}` |
| `POST /analises` | **Implementado** (PR #78, #21) | Sem método correspondente em `FonteApi` | `201 Created`; `400`/`422` entrada inválida, `503` indisponibilidade | `{"recebidos": int, "inseridos": int, "duplicados": int}`; classifica registros e grava na coleção MongoDB `analises` |
| `GET /analises` | **Implementado** (PR #80, #23–#25) | **Implementado** (`FonteApi.listar`) | `200 OK`; `422` filtro/paginação inválidos, `503` banco indisponível | `{"itens": [...], "pagina": int >= 1, "tamanho": int de 1 a 100, "total": int >= 0}`; coleção vazia retorna lista vazia |
| `GET /analises/resumo` | **Implementado** (PR #80) | **Implementado** (`FonteApi.resumir`) | `200 OK`; `422` filtros inválidos, `503` banco indisponível | `{"total": int, "por_sentimento": {"positivo": int, "neutro": int, "negativo": int}, "sem_data_publicacao": int}`; agregação no banco sobre o conjunto filtrado |
| `POST /auth/login` | **Implementado** (PR #75) | **Implementado** (`AdministracaoApi.entrar`) | `200 OK`; `401` credencial inválida, `429` bloqueio, `503` sem configuração | `{"token": str, "usuario": str, "expira_em": str ISO 8601 UTC}`; token opaco com expiração |
| `POST /auth/logout` | **Implementado** (PR #75) | **Implementado** (`AdministracaoApi.sair`) | `204 No Content`; `401` sessão inválida | Revoga a sessão enviada em `Authorization: Bearer <token>`; o cliente também aceita `200` |
| `POST /datasets` | **Implementado** (PR #75) | **Implementado** (`AdministracaoApi.importar_dataset`) | `201 Created`; `401`/`413`/`415`/`422` | `id_dataset`, `nome_arquivo`, `registros_lidos == registros_importados + registros_descartados`, `descartes_por_motivo`; registros ficam em memória |
| `GET /coletas/fontes` | **Implementado** (PR #75) | **Implementado** (`AdministracaoApi.listar_fontes_coleta`) | `200 OK`; `401` | `{"fontes": [{"id": str, "nome": str}, ...]}`; TweetSentBR local, quando disponível, e datasets importados |
| `POST /coletas` | **Implementado** (PR #75) | **Implementado** (`AdministracaoApi.iniciar_coleta`) | `202 Accepted`; `401`/`422` (inclui fonte desconhecida) | Coleta em segundo plano, com ID, fonte, situação, contagens, mensagem, `por_sentimento` e `exemplos` |
| `GET /coletas/{id_coleta}` | **Implementado** (PR #75) | **Implementado** (`AdministracaoApi.consultar_coleta`) | `200 OK`; `401`, `404` coleta inexistente | Mesmo contrato de coleta, com `textos_analisados <= textos_coletados` |

`GET /analises` aceita `pagina=1` e `tamanho=20` por padrão, com máximo 100. A ordenação é `data_processamento` decrescente, seguida de `fonte` e `id_origem` crescentes. Os filtros combináveis `inicio`, `fim` e `sentimento` são aplicados no banco; somente `positivo`, `negativo` e `neutro` são aceitos. O resumo independe da paginação e suas três contagens somam o total filtrado. Não há snapshot entre requisições: escritas concorrentes podem alterar páginas e contagens.

**Integrações existentes e limite da Administração:** `POST /analises` usa pipeline → repositório → MongoDB; as duas rotas GET leem essa coleção. Já [`RepositorioAdministracao`](../src/servico/administracao.py) mantém datasets, coletas e análises administrativas em memória; as sessões também são mantidas em memória. Esses registros se perdem ao reiniciar e não alimentam automaticamente o Dashboard via MongoDB. Integrar a Administração ao MongoDB e conectar sua coleta ao XFetch continuam pendentes; não são efeitos dos PRs #78/#80.

O painel continua com `SENTIA_FONTE_DADOS=mock` por padrão; o modo HTTP é selecionado por `SENTIA_FONTE_DADOS=api` e `SENTIA_API_URL`, conforme [`src/apresentacao/config.py`](../src/apresentacao/config.py). A existência dos clientes e das rotas não comprova um ensaio integrado com MongoDB e classificador reais.

---

## 8. Exemplo Ponta a Ponta do Contrato

Exemplo ilustrativo de formatos entre camadas, não evidência de execução com serviços reais.

### 8.1 Saída da Aquisição (`src/processamento/aquisicao/xfetch.py`)
```python
{
    "id_origem": "1899990001",
    "texto_original": "Atendimento rápido e eficiente no aplicativo!",
    "fonte": "X",
    "rotulo_original": None,
    "rotulo_padronizado": None,
    "data_publicacao": "2026-11-03T15:00:00Z",
    "metadados": {
        "provedor": "XFetch",
        "lang": "pt",
        "like_count": 12,
        "retweet_count": 3,
    },
}
```

### 8.2 Saída do Pipeline / Documento BSON (`src/processamento/pipeline.py` → MongoDB `analises`)
```python
{
    "id_origem": "1899990001",
    "fonte": "X",
    "texto_original": "Atendimento rápido e eficiente no aplicativo!",
    "sentimento": "positivo",
    "probabilidades": {"positivo": 0.92, "negativo": 0.02, "neutro": 0.06},
    "modelo": {"nome": "pysentimiento/bertweet-pt-sentiment", "versao": "commit-abc123"},
    "data_publicacao": datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc),
    "data_processamento": datetime(2026, 11, 3, 15, 5, tzinfo=timezone.utc),
    "metadados": {
        "provedor": "XFetch",
        "lang": "pt",
        "like_count": 12,
        "retweet_count": 3,
    },
}
```
*(Nota: `rotulo_original` e `rotulo_padronizado` são omitidos porque eram `None` na aquisição.)*

### 8.3 Item Serializado na API Implementada (`GET /analises` → `FonteApi.listar`)
```json
{
  "id_origem": "1899990001",
  "fonte": "X",
  "texto_original": "Atendimento rápido e eficiente no aplicativo!",
  "sentimento": "positivo",
  "probabilidades": { "positivo": 0.92, "negativo": 0.02, "neutro": 0.06 },
  "modelo": { "nome": "pysentimiento/bertweet-pt-sentiment", "versao": "commit-abc123" },
  "rotulo_original": null,
  "rotulo_padronizado": null,
  "data_publicacao": "2026-11-03T15:00:00Z",
  "data_processamento": "2026-11-03T15:05:00Z",
  "metadados": {
    "provedor": "XFetch",
    "lang": "pt",
    "like_count": 12,
    "retweet_count": 3
  }
}
```

---

## 9. Estado de Verificação e Limites das Evidências

| Issue | Implementação / evidência disponível | Pendência ou limite |
|---|---|---|
| **#18 (Infraestrutura e CI)** | Arquivos de infraestrutura e CI existentes; esta revisão não os altera. | Nenhuma nova execução de CI ou decisão de encerramento é afirmada por esta revisão documental. |
| **#19 (Contrato único)** | Campos, separação entre rótulo humano e predição, UTC, duplicatas, privacidade e rotas conferidos contra o código atual. | Homologação de Dados, ML, Banco, API e PO permanece **pendente**, incluindo data de referência temporal e limites de privacidade. |
| **#22 (QA T09/T10)** | [`tests/test_qa_t09_t10.py`](../tests/test_qa_t09_t10.py) cobre exemplos válidos/inválidos, BSON real, pipeline com classificador determinístico, cliente HTTP sobre ASGI e consultas com coleção simulada. [`tests/test_api.py`](../tests/test_api.py), [`tests/test_consultas_api.py`](../tests/test_consultas_api.py) e [`tests/test_api_administracao.py`](../tests/test_api_administracao.py) cobrem os contratos HTTP com dependências controladas. | Serializar BSON ou usar `TestClient` não valida uma instância MongoDB nem inferência com modelo real. Os merges #20/#21 já ocorreram; o ensaio integrado real continua sendo uma verificação separada. |

[`tests/test_repositorio.py`](../tests/test_repositorio.py) contém testes unitários com mocks e testes opcionais com MongoDB local, ignorados quando o servidor está indisponível. Um teste ignorado não é validação de persistência real. Esta revisão documental não executa smoke com banco, modelo ou XFetch reais e não registra homologação a partir de mocks.

---

## 10. Homologação do Contrato — Pendente

Responsáveis de revisão conforme a [issue #19](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/19) e as atribuições atuais das issues [#20](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/20) e [#21](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/21). A atribuição de uma issue ou o merge de um PR não é aprovação deste contrato.

| Frente | Responsáveis / referência | Aprovação |
|---|---|---|
| Dados | Breno (revisão exigida na #19) | **Pendente** |
| ML | Ricardo e Gabriel (revisão exigida na #19) | **Pendente** |
| Banco | MariaEduarda-jg e lianeiv (atribuídos na #20); a #19 também exige revisão de Maria/Julia, cuja correspondência nominal deve ser confirmada | **Pendente** |
| API | MariaEduarda-jg, Ricardo-909-Leal, Gabriel-Ma7os e lianeiv (atribuídos na #21; o texto histórico ainda diz “a definir”) | **Pendente** |
| Product Owner | PO do projeto; identificação nominal a confirmar nas fontes de homologação | **Pendente** |

Figueirin coordena a decisão conforme a #19. Solicitar confirmação explícita das frentes sobre campos, exemplos e testes de contrato, e da PO sobre o contrato e as decisões pendentes de período/privacidade. Registrar o link da confirmação no PR ou na issue antes de alterar qualquer estado de aprovação; esta revisão não fecha a #19 nem declara seu aceite.
