# SentIA

Plataforma em desenvolvimento para análise de sentimentos em textos em português. Projeto acadêmico da equipe **T03 — Liskov**, Métodos de Desenvolvimento de Software (MDS), UnB/FGA, 2026.2.

- **Linha de base técnica (`developer`):** `1723a7d` (`13/11/2026`, pós-PC1 — **Sprint 5 em andamento**).
- **Inspeção cruzada (`LAMPORT → LISKOV`):** ponto de entrada em [`docs/inspecao/README.md`](docs/inspecao/README.md) e [`docs/inspecao/ROTEIRO_INSPECAO.md`](docs/inspecao/ROTEIRO_INSPECAO.md).
- **Índice completo de documentação:** [`docs/README.md`](docs/README.md).

---

## Estado atual do projeto (corte de 14/11/2026)

### 1. O que já está implementado e integrado na `developer`

- **Aquisição e auditoria de dados (`src/processamento/aquisicao/`):**
  - Importador CSV estrito e tolerante com relatório de descartes (`csv_importer.py`).
  - Adaptadores para **TweetSentBR** (`tweetsentbr.py`), **BPSAD** (`bpsad_adapter.py`) e auditoria SHA-256 (`auditoria_datasets.py`).
  - Coleta paginada via **XFetch** (`xfetch.py`, PR `#65`), com allowlist de metadados e validação com cliente HTTP simulado.
- **Processamento e classificação (`src/processamento/classificacao/` e `pipeline.py`):**
  - Adaptador `ClassificadorBertweet` para `pysentimiento/bertweet-pt-sentiment` preservando texto bruto (decisão arquitetural proposta em [`docs/decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md`](docs/decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md)), além do baseline isolado TF-IDF + Regressão Logística (`baseline.py`) e métricas (`avaliacao.py`).
  - `PipelineClassificacao` em lote preservando `texto_original`, `id_origem`, `fonte`, separando anotação humana da classe prevista (`sentimento`) e emitindo documentos compatíveis com BSON.
- **Persistência e leitura MongoDB (`src/dados/` e `src/persistencia/leitura.py`, PRs `#43`, `#47`, `#78`, `#84`, `#87`):**
  - Conexão PyMongo explícita (`database.py`), índices únicos e compostos (`uq_fonte_id_origem`, `idx_sentimento_data_publicacao`, `idx_data_publicacao`, `idx_data_processamento`), inserção em lote com deduplicação (`repositorio.py`), consultas pontuais, paginação e agregação por sentimento (`leitura.py`).
  - Integrado com o serviço `mongo:7` na CI; para desenvolvimento isolado, `SENTIA_ARMAZENAMENTO=memoria` oferece alternativa em RAM (`dependencias.py`).
- **Serviço HTTP FastAPI (`src/servico/main.py`, `administracao.py`, `autenticacao.py`, `pesquisa.py`):**
  - **Rotas de análise (`main.py`):** `GET /health`, `POST /analises` (201, classifica lote via pipeline e persiste), `GET /analises` (paginado e filtrado por `inicio`, `fim`, `sentimento`) e `GET /analises/resumo` (totais e `sem_data_publicacao`). *Observação: essas rotas não exigem login administrativo.*
  - **Rotas administrativas autenticadas (`administracao.py`, token `Bearer` com hash `scrypt`, expiração e bloqueio por tentativas):** `POST /auth/login`, `POST /auth/logout` (204), `POST /datasets` (upload CSV, 201), `GET /coletas/fontes`, `POST /coletas` (processamento em segundo plano, 202) e `GET /coletas/{id_coleta}`.
- **Painel web Streamlit (`src/apresentacao/`):**
  - Navegação entre **Dashboard** (filtros de período/sentimento, indicadores numéricos e aviso de textos sem data) e **Administração** (login, importação de CSV, **Pesquisar assunto** e acompanhamento de coleta).
  - Clientes HTTP reais (`fontes/api.py`, `fontes/administracao_api.py`) alinhados a [`docs/frontend/CONTRATO-API.md`](docs/frontend/CONTRATO-API.md), além de modos simulados (`mock.py`, `administracao_mock.py`).

### 2. O que opera em modo mock, em memória ou em caráter experimental

- **Modo padrão do painel (`SENTIA_FONTE_DADOS=mock`):** sem configurar `SENTIA_FONTE_DADOS=api`, o Streamlit usa `17` análises fictícias (`FonteMock`) e administração simulada (`admin` / `senha-de-exemplo` em `AdministracaoMock`).
- **Estado administrativo em memória (`RepositorioAdministracao`):** mesmo quando `/analises*` usa MongoDB, **sessões ativas, datasets CSV importados via painel, jobs de coleta e o índice da pesquisa híbrida ficam apenas na RAM do processo** (reiniciar a API encerra sessões e apaga esse estado).
- **Pesquisa híbrida por assunto (`src/servico/pesquisa.py`, PR `#81`):** implementa busca lexical normalizada com radical de 5 caracteres sobre textos em memória e complemento opcional pago via XFetch (`POST /coletas` com `fonte="pesquisa"`). Não utiliza Vector Search nem embeddings no MongoDB (`docs/pesquisa_hibrida_mongodb_xfetch.md` permanece proposta) e **ainda aguarda ratificação formal da PO**, definição de teto financeiro do XFetch e criação de issue dedicada.
- **Testes automatizados sem dependências externas reais:** na CI, MongoDB roda contra `mongo:7` real, enquanto inferência do `ClassificadorBertweet`, API XFetch e chamadas HTTP nos testes do painel usam dublês/mocks em processo.

### 3. O que segue pendente (Sprints 5–7 e decisões abertas)

- **Avaliação empírica BPSAD por classe (`#85` / PR `#89` aberto):** reproduzir métricas por classe do BERTweet no BPSAD (o PR `#89` relata 67,70% de acurácia e 0,5543 F1-macro em amostra de 10k textos, abaixo dos ~80% de `RNF01`) e deliberar critério com a PO.
- **Dashboard integrado completo (Sprint 6 — `#27–#30`, `#32`, `#61`):** renderização da listagem paginada de análises, gráficos de distribuição por sentimento, resumo textual estatístico e eventual nuvem de palavras opcional no Streamlit, além de validação visual atual (`T18`).
- **Finalização, usabilidade e entrega (Sprint 7 — `#62`, `#63`, `#86`):** teste de usabilidade, publicação web segura (definindo autenticação para `/analises` e persistência administrativa), atualização formal dos documentos acadêmicos *Visão* e *Arquitetura* após decisões da PO e sincronização controlada `developer → main` (`main` segue na versão inicial de `02/11`, `c72faeb`).

---

## Arquitetura resumida

`src/apresentacao` (Streamlit) → `src/servico` (FastAPI) → `src/processamento` (aquisição, pipeline e classificação) → `src/dados` & `src/persistencia` (MongoDB / repositório em memória).

Detalhes completos em [`docs/arquitetura.md`](docs/arquitetura.md) e [`docs/contratos-dados.md`](docs/contratos-dados.md).

---

## Preparação do ambiente

Requisitos: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) e Python 3.11 (`.python-version`).

```bash
uv sync --locked
make env
```

Para instalar também as dependências pesadas opcionais do classificador BERTweet real (`pysentimiento` e `torch`):

```bash
uv sync --locked --group ml
# ou: make setup-ml
```

`make env` cria `.env` a partir de [`.env.example`](.env.example) sem sobrescrever um arquivo existente. O modo `mock` do painel e o roteiro offline não exigem MongoDB nem `XFETCH_API_KEY`.

---

## Execução

### 1. Painel Streamlit em modo demonstração offline (`mock`)

```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run streamlit run src/apresentacao/app.py
```

Acesse `http://localhost:8501` (ou execute `make run`). Os cenários simulados aceitam `normal`, `vazio` ou `erro`.

### 2. API FastAPI (análises e administração)

Com `MONGODB_URI` configurado (ou usando `SENTIA_ARMAZENAMENTO=memoria` para testes locais sem banco):

```bash
# Modo com armazenamento em memória (sem MongoDB local):
SENTIA_ARMAZENAMENTO=memoria uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000

# Verificação de saúde:
curl --fail http://127.0.0.1:8000/health
```

Resposta esperada: `{"status":"ok"}`. Para habilitar as rotas `/auth/login`, `/datasets` e `/coletas*`, configure `SENTIA_ADMIN_USUARIO` e `SENTIA_ADMIN_SENHA_HASH` no `.env` (`uv run python -m src.servico.autenticacao`).

### 3. Painel conectado à API local

```bash
SENTIA_FONTE_DADOS=api SENTIA_API_URL=http://127.0.0.1:8000 uv run streamlit run src/apresentacao/app.py
```

### 4. Pipeline offline (`CSV → Classificador simulado → BSON`)

```bash
make demo
# ou: uv run python -m scripts.demonstrar_pipeline
```

---

## Validação, lint e CI

```bash
make check
# equivalente a:
uv run ruff check src/apresentacao tests/test_painel_*.py
uv run ruff check --isolated --select F,E9 .
uv run pytest --cov=src -q
uv lock --check
```

- **Na CI (`.github/workflows/ci.yml`):** o job `test` provisiona `mongo:7` em `mongodb://127.0.0.1:27017` (`MONGODB_URI_TESTE`), executando os testes reais de persistência MongoDB juntamente com a suíte unitária/de integração.
- **Localmente sem MongoDB:** os testes marcados para MongoDB (`test_persistencia_leitura.py` e parte de `test_repositorio.py`) são ignorados (`skipped`) quando `MONGODB_URI_TESTE` não está acessível.

---

## Documentação e Inspeção

Consulte o índice completo em [`docs/README.md`](docs/README.md):

- **Inspeção e Gestão:** [Dossiê de Inspeção](docs/inspecao/README.md) · [Roteiro da Inspeção](docs/inspecao/ROTEIRO_INSPECAO.md) · [Matriz de Evidências](docs/inspecao/MATRIZ_EVIDENCIAS.md) · [Registro Pré-Inspeção](docs/inspecao/REGISTRO_PRE_INSPECAO.md) · [Plano de Regularização](docs/inspecao/PLANO_REGULARIZACAO.md) · [Planejamento e Replanejamentos](docs/gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md) · [Gestão de Configuração](docs/gestao/GESTAO_CONFIGURACAO.md)
- **Arquitetura e Contratos:** [Arquitetura](docs/arquitetura.md) · [Contratos de dados](docs/contratos-dados.md) · [Contrato da API](docs/frontend/CONTRATO-API.md) · [ADR-001 (proposta stopwords/BERTweet)](docs/decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md)
- **Frontend, ML, Dados e Banco:** [Guia do painel](docs/frontend/README.md) · [Wireframes](docs/frontend/WIREFRAMES.md) · [Classificação](docs/classificacao.md) · [TweetSentBR](docs/tweetsentbr.md) · [BPSAD](docs/bpsad.md) · [Experimentos BPSAD](docs/experimentos_bpsad.md) · [XFetch](docs/integracao_xfetch.md) · [Esquema MongoDB](docs/banco/esquema-mongodb.md)
- **Marco histórico PC1 (09/11/2026):** [Status PC1](docs/qa/pc1/STATUS_FINAL.md) · [Roteiro PC1](docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md) · [Matriz PC1](docs/qa/pc1/MATRIZ_RASTREABILIDADE.md)
