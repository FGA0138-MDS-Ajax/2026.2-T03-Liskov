# Contrato Único de Dados — Aquisição, Pipeline ML, MongoDB, API e Painel

Referência canônica do contrato de dados do SentIA entre as camadas de **Dados (Aquisição)**, **ML (Classificação/Pipeline)**, **Banco (MongoDB)**, **Serviço (FastAPI)** e **Apresentação (Streamlit)** ([issue #19](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/19)).

---

## 1. Visão Geral por Frente (Revisão de Integração)

| Frente | Módulo / Referência | Entrada | Saída | Estado na `developer` |
|---|---|---|---|---|
| **Dados (Aquisição)** | [`src/processamento/aquisicao/`](../src/processamento/aquisicao/) (`csv_importer.py`, `tweetsentbr.py`, `bpsad_adapter.py`, `xfetch.py`) | Arquivos CSV/TSV locais ou respostas paginadas da API XFetch | `dict[str, Any]` padronizado sem inferência de modelo | Implementado e testado |
| **ML (Classificação e Pipeline)** | [`src/processamento/classificacao/`](../src/processamento/classificacao/) e [`src/processamento/pipeline.py`](../src/processamento/pipeline.py) | `Iterable[dict[str, Any]]` da aquisição | Documento `dict[str, Any]` pronto para BSON (`sentimento`, `probabilidades`, `modelo`, datas UTC) | Implementado e testado |
| **Banco (MongoDB)** | [`src/dados/database.py`](../src/dados/database.py) e [`docs/banco/esquema-mongodb.md`](banco/esquema-mongodb.md) | Conexão via `MONGODB_URI` e documento BSON da coleção `analises` | Persistência validada e indexada (`uq_fonte_id_origem`) | Conexão/esquema prontos; CRUD em revisão (#20) |
| **Serviço (API FastAPI)** | [`src/servico/main.py`](../src/servico/main.py) e [`docs/frontend/CONTRATO-API.md`](frontend/CONTRATO-API.md) | Documentos do MongoDB / requisições HTTP | JSON UTF-8 sobre HTTP (`GET /health` ativo; demais rotas propostas) | `GET /health` implementado; rotas de negócio pendentes (#21, #23–#25, #58) |
| **Apresentação (Painel)** | [`src/apresentacao/contrato.py`](../src/apresentacao/contrato.py) e [`src/apresentacao/fontes/`](../src/apresentacao/fontes/) | Respostas JSON da API (`FonteApi`, `AdministracaoApi`) ou dados simulados (`FonteMock`, `AdministracaoMock`) | Dataclasses imutáveis (`Analise`, `PaginaAnalises`, `ResumoAnalises`, `FiltrosAnalises`, `Coleta`) | Implementado e testado |

---

## 2. Contrato de Campos por Etapa

Os adaptadores de aquisição alimentam `PipelineClassificacao.processar_registros()`, cujo documento de saída segue o esquema da coleção `analises` no MongoDB ([`docs/banco/esquema-mongodb.md`](banco/esquema-mongodb.md)) e o item de `GET /analises` ([`docs/frontend/CONTRATO-API.md`](frontend/CONTRATO-API.md)).

| Campo | Aquisição (`dict`) | Pipeline / MongoDB (`analises`) | API HTTP (`GET /analises`) | Responsável | Regra de Contrato e Validação |
|---|---|---|---|---|---|
| `_id` | *Ausente* | `ObjectId` (gerado pelo MongoDB) | *Omitido ou ignorado pelo painel* | Banco | Chave técnica interna do MongoDB; a chave de negócio é `(fonte, id_origem)` |
| `id_origem` | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | Aquisição → Pipeline → Banco → API | ID nativo do registro na origem ou hash determinístico SHA-256 (`{fonte}_{pos:06d}_{sha256[:12]}`) |
| `fonte` | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str`) | Aquisição → Pipeline → Banco → API | Proveniência do texto (`"TweetSentBR"`, `"b2w"`, `"olist"`, `"X"`, etc.) |
| `texto_original` | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str` não vazia) | **Obrigatório** (`str`) | Aquisição → Pipeline → Banco → API | Texto bruto preservado; enviado ao BERTweet sem remoção de stopwords ou stemming ([ADR-001](decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md)) |
| `texto_tratado` | *Ausente* | Opcional (`str`, omitido se ausente) | Opcional (*não consumido pelo painel*) | ML (apenas baseline clássico) | Exclusivo para experimentos com modelos clássicos (`baseline.py`); **nunca** exigido no fluxo BERTweet |
| `rotulo_original` | Opcional (`str \| None`) | Opcional (`str`, **omitido** se `None`) | Opcional | Aquisição → Pipeline | Rótulo humano bruto ou nota original do dataset (ex.: `"5"`, `"1"`, `"positivo"`). **Nunca** recebe previsão do modelo |
| `rotulo_padronizado` | Opcional (`"POS" \| "NEG" \| "NEU" \| None`) | Opcional (`"positivo" \| "negativo" \| "neutro"`, **omitido** se `None`) | Opcional | Aquisição → Pipeline | Rótulo humano convertido por `converter_rotulo_para_sentia()`; ausente em textos não rotulados (como coletas do X) |
| `sentimento` | *Não criado na aquisição* | **Obrigatório** (`"positivo" \| "negativo" \| "neutro"`) | **Obrigatório** (`"positivo" \| "negativo" \| "neutro"`) | ML → Pipeline → Banco → API | Classe prevista pelo modelo em português e minúsculas |
| `probabilidades` | *Não criado na aquisição* | **Obrigatório no pipeline** (`dict[str, float]`) | Opcional no painel (`dict[str, float]`) | ML → Pipeline → Banco | Chaves exatas `positivo`, `negativo` e `neutro`; floats finitos em `[0, 1]` com soma `1.0 ± 0.001` |
| `modelo` | *Não criado na aquisição* | **Obrigatório** (`{"nome": str, "versao"?: str}`) | **Obrigatório** (`{"nome": str, ...}`) | ML → Pipeline → Banco → API | Objeto com `modelo.nome` (`str` não vazia) obrigatório; `modelo.versao` incluído quando informado |
| `data_publicacao` | Opcional (`str \| None`) | Opcional (BSON `Date` UTC, **omitido** se `None`) | Opcional (`str` ISO 8601 com fuso ou `null`) | Aquisição → Pipeline → Banco → API | Data real da publicação na origem; **jamais** inventada quando ausente |
| `data_processamento` | *Não criado na aquisição* | **Obrigatório** (BSON `Date` UTC) | **Obrigatório** (`str` ISO 8601 com fuso) | Pipeline → Banco → API | Instante UTC em que o pipeline classificou o registro (`datetime.now(timezone.utc)`) |
| `metadados` | Opcional (`dict \| None`) | Opcional (`dict`, **omitido** se vazio/`None`) | Opcional (`dict`) | Aquisição → Pipeline | Atributos auxiliares da fonte sem dados pessoais de autor |

---

## 3. Regras de Metadados e Privacidade por Fonte (Correção `XFetch`)

- **XFetch (`src/processamento/aquisicao/xfetch.py` — `buscar_tweets_xfetch`)**:
  - Por conformidade com privacidade/LGPD, a função `_normalizar_tweet` aplica uma lista de permissão estrita e **proíbe/descarta explicitamente** identificadores de conta ou conversa: `author_id`, `autor_id`, `user`, `username`, `author`, `user_id`, `screen_name` e `conversa_id` **nunca** são incluídos no registro nem em `metadados`.
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

---

## 4. Datas e Fuso Horário (UTC)

1. **`data_publicacao` ausente**:
   - Quando a fonte não possui data de publicação (`None` ou string vazia), o pipeline mantém `None` e **omite** a chave `data_publicacao` no documento BSON (não grava `null` no MongoDB e nunca usa `data_processamento` como substituta).
   - Na API HTTP (`GET /analises`), a ausência é representada por `"data_publicacao": null` (ou chave omitida), que o cliente `FonteApi` converte para `Analise.data_publicacao = None`.
   - Em consultas com filtro de período (`inicio` e/ou `fim`), registros sem `data_publicacao` ficam fora do recorte temporal e sua quantidade é informada em `sem_data_publicacao` no endpoint `GET /analises/resumo`. Sem filtro de período ativo (`inicio=None` e `fim=None`), `sem_data_publicacao` é obrigatoriamente `0`.
2. **`data_publicacao` apenas com data de calendário (`YYYY-MM-DD`)**:
   - Aceita pelo pipeline para compatibilidade com datasets como BPSAD e convertida para meia-noite UTC (`datetime(ano, mes, dia, 0, 0, tzinfo=timezone.utc)`).
3. **`data_publicacao` e `data_processamento` com data e hora**:
   - Devem estar em formato ISO 8601 com **fuso horário explícito** (`Z` ou deslocamento `±HH:MM`, ex.: `2026-11-03T12:00:00-03:00`) e são convertidas para UTC (`timezone.utc`).
   - Strings de data-hora sem fuso horário (ex.: `2026-11-03T12:00:00`) ou formatos locais (`29/10/2026`) são rejeitados pelo pipeline (`ErroPipeline`), pelo esquema do banco e pelo cliente HTTP (`ErroFonteDados`).

---

## 5. Identificação e Regra de Duplicação

1. **Na aquisição (`csv_importer.py` e `tweetsentbr.py`)**:
   - Se `id_origem` vier preenchido na fonte, é preservado (`str.strip()`).
   - Se `id_origem` estiver ausente, é gerado de forma determinística via SHA-256 sobre `fonte`, posição (base 1), `texto_original` e `data_publicacao`:
     `"{fonte}_{posicao:06d}_{sha256[:12]}"` (ex.: `"TweetSentBR_000001_0a1b2c3d4e5f"`).
2. **Na coleta paginada (`xfetch.py`)**:
   - `id_origem` é obrigatório em cada item retornado pela API externa. Itens repetidos com o mesmo `id_origem` na mesma execução paginada são descartados em memória, preservando a primeira ocorrência.
3. **No MongoDB (`coleção analises`)**:
   - A unicidade é imposta pelo índice único composto `uq_fonte_id_origem` em `{"fonte": 1, "id_origem": 1}` (`unique: true`).
   - Dois documentos com o mesmo `id_origem` e a mesma `fonte` configuram duplicata (erro `11000` / `DuplicateKeyError` no PyMongo) e não devem gerar segunda gravação.
   - O mesmo `id_origem` em fontes distintas (ex.: `fonte="b2w"` e `fonte="X"`) é válido e permitido.

---

## 6. Formatos e Contratos de Erro por Camada

| Camada | Exceção / Código | Condições de Disparo | Comportamento / Mensagem |
|---|---|---|---|
| **Aquisição CSV** (`csv_importer.py`) | `ErroImportacaoCSV` | Arquivo inexistente/diretório, bytes fora de UTF-8, colunas `texto`/`fonte` ausentes, ou registro inválido em `modo_estrito=True` | Em `modo_estrito=False`, linhas inválidas não abortam o lote e são somadas em `RelatorioImportacao.descartes_por_motivo` (`texto_vazio`, `fonte_vazia`, `rotulo_invalido`, `data_invalida`) |
| **Aquisição XFetch** (`xfetch.py`) | `ErroXFetch`, `ValueError`, `TypeError` | `XFETCH_API_KEY` ausente, parâmetros fora dos limites (`quantidade` 1..100, `limite_por_pagina` 1..20, `max_paginas`), falha HTTP/rede, JSON inválido ou `data` não lista | Mensagens sanitizadas que nunca expõem URL/consulta, cabeçalhos ou chave da API |
| **Pipeline ML** (`pipeline.py`) | `ErroPipeline` / `ValueError` | `tamanho_lote <= 0`, classificador sem `nome_modelo`, lote vazio, `id_origem`/`fonte`/`texto_original` vazios, `metadados` não `dict`, data inválida/sem fuso, probabilidades fora de `[0, 1]` ou soma `!= 1.0 ± 0.001` | Valida entradas antes da inferência e valida o contrato de saída antes de retornar os documentos BSON |
| **Conexão MongoDB** (`database.py`) | `ErroConfiguracaoMongoDB`, `ErroConexaoMongoDB` | `MONGODB_URI` ausente/vazia, `timeout_ms` não inteiro positivo, falha de DNS/URI, autenticação, rede ou `ping` | Fecha o cliente automaticamente se o `ping` falhar e **nunca** inclui `MONGODB_URI` ou credenciais na exceção/traceback |
| **Cliente HTTP — Painel** (`api.py`, `administracao_api.py`) | `ErroFonteDados`, `ErroAutenticacao` | `400`/`415`/`422` (dados/filtros recusados), `401` (credencial inválida ou sessão expirada), `403` (sem permissão), `404` (rota ausente), `413` (arquivo acima do limite), `429` (limite de tentativas), `5xx`/timeout/rede ou JSON fora do contrato | Converte falhas técnicas e respostas fora do esquema em mensagens claras para a interface; em `400`/`415`/`422` aproveita `{"mensagem": "..."}` se tiver até 300 caracteres |

---

## 7. Endpoints Implementados vs. Contratos Propostos

Conforme [`src/servico/main.py`](../src/servico/main.py), [`src/apresentacao/contrato.py`](../src/apresentacao/contrato.py) e [`docs/frontend/CONTRATO-API.md`](frontend/CONTRATO-API.md):

| Método e Rota | Status no Backend (`src/servico/`) | Status no Cliente (`src/apresentacao/fontes/`) | Código HTTP Esperado | Contrato de Resposta / Observação |
|---|---|---|---|---|
| `GET /health` | **Implementado** (`src/servico/main.py`) | **Implementado** (`FonteApi.verificar_saude`) | `200 OK` | `{"status": "ok"}` |
| `GET /analises` | **Proposto** (pendente #21) | **Implementado** (`FonteApi.listar`) | `200 OK` (`400`/`422` se filtro inválido) | `PaginaAnalises`: `{"itens": [...], "pagina": int >= 1, "tamanho": int >= 1, "total": int >= 0}` com filtros `inicio`, `fim`, `sentimento` |
| `GET /analises/resumo` | **Proposto** (pendente #21) | **Implementado** (`FonteApi.resumir`) | `200 OK` (`400`/`422` se filtro inválido) | `ResumoAnalises`: `{"total": int, "por_sentimento": {"positivo": int, "neutro": int, "negativo": int}, "sem_data_publicacao": int}` |
| `POST /auth/login` | **Proposto** (pendente #58) | **Implementado** (`AdministracaoApi.entrar`) | `200 OK` (`401` credencial inválida, `429` bloqueio) | `SessaoAdministrador`: `{"token": str, "usuario": str, "expira_em": str ISO 8601 UTC}` (`token` oculto no `repr`) |
| `POST /auth/logout` | **Proposto** (pendente #58) | **Implementado** (`AdministracaoApi.sair`) | `204 No Content` ou `200 OK` | Encerra a sessão administrativa enviada em `Authorization: Bearer <token>` |
| `POST /datasets` | **Proposto** (pendente #21 / #58) | **Implementado** (`AdministracaoApi.importar_dataset`) | `201 Created` (`400`/`413`/`415`/`422`) | `ResultadoImportacao`: `id_dataset`, `nome_arquivo`, `registros_lidos == registros_importados + registros_descartados`, `descartes_por_motivo` |
| `GET /coletas/fontes` | **Proposto** (pendente #21 / #58) | **Implementado** (`AdministracaoApi.listar_fontes_coleta`) | `200 OK` (`401`/`403`) | `{"fontes": [{"id": str, "nome": str}, ...]}` |
| `POST /coletas` | **Proposto** (pendente #21 / #58) | **Implementado** (`AdministracaoApi.iniciar_coleta`) | `202 Accepted` (`400`/`422`) | `Coleta`: `{"id": str, "fonte": str, "situacao": "pendente" \| "em_andamento" \| "concluida" \| "falhou", "textos_coletados": int, "textos_analisados": int, "mensagem"?: str}` |
| `GET /coletas/{id}` | **Proposto** (pendente #21 / #58) | **Implementado** (`AdministracaoApi.consultar_coleta`) | `200 OK` (`404` se inexistente) | Mesmo contrato de `Coleta`, garantindo `textos_analisados <= textos_coletados` |

---

## 8. Exemplo Ponta a Ponta do Contrato

### 8.1 Saída da Aquisição (`src/processamento/aquisicao/xfetch.py`)
```python
{
    "id_origem": "1899990001",
    "texto_original": "Atendimento rápido e eficiente no aplicativo!",
    "fonte": "X",
    "rotulo_original": None,
    "rotulo_padronizado": None,
    "data_publicacao": "2026-11-03T12:00:00-03:00",
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

### 8.3 Item Serializado na API Proposta (`GET /analises` → `FonteApi.listar`)
```json
{
  "id_origem": "1899990001",
  "fonte": "X",
  "texto_original": "Atendimento rápido e eficiente no aplicativo!",
  "sentimento": "positivo",
  "probabilidades": { "positivo": 0.92, "negativo": 0.02, "neutro": 0.06 },
  "modelo": { "nome": "pysentimiento/bertweet-pt-sentiment", "versao": "commit-abc123" },
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

## 9. Estado de Verificação na Sprint 4 (#18, #19 e #22)

| Issue | O que está concluído e validado na `developer` | O que depende de entregas dos colegas |
|---|---|---|
| **#18 (Infraestrutura e CI)** | `developer` alinhada ao histórico da `main` (`c72faeb`) sem *force push* e sem `requirements*.txt`; `pyproject.toml` + `uv.lock` íntegros; `Makefile`, `.github/workflows/ci.yml` e `README.md` sincronizados (`make check`, `ruff`, `pytest`). | Nenhuma pendência (pronta para encerrar). |
| **#19 (Contrato único)** | Contrato unificado entre aquisição, pipeline ML, MongoDB, FastAPI e painel; privacidade do XFetch (`sem autor_id/conversa_id`) corrigida; regras de datas UTC, índice único `(fonte, id_origem)` e erros por camada documentados. | Revisão/aceite das frentes de Dados, ML, Banco e API no PR (pronta para encerrar após aprovação). |
| **#22 (QA T09/T10)** | Suíte independente [`tests/test_qa_t09_t10.py`](../tests/test_qa_t09_t10.py) validando exemplos válidos/inválidos do esquema MongoDB, serialização BSON real, fluxo `PipelineClassificacao → BSON → FonteApi`, chave `(fonte, id_origem)`, `GET /health` (`200`/`405`) e comportamento real `404` das rotas ainda não publicadas no FastAPI. | Execução ponta a ponta de escrita/leitura real na coleção `analises` e respostas `200`/`201`/`202` das rotas `/analises*`, `/auth/*`, `/datasets` e `/coletas*` aguardam o merge das issues **#20** (CRUD MongoDB) e **#21** (rotas de análises na FastAPI). |
