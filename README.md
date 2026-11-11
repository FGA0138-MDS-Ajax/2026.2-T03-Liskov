# SentIA

Plataforma em desenvolvimento para análise de sentimentos em textos em português.
Projeto acadêmico da equipe **T03 — Liskov**, Métodos de Desenvolvimento de
Software (MDS), UnB/FGA, 2026.2.

## Estado atual no PC1

### O que já está implementado e testado
- **Aquisição e auditoria de dados (`src/processamento/aquisicao/`)**:
  - Importador CSV estrito e tolerante com relatório de descartes (`csv_importer.py`).
  - Adaptadores para **TweetSentBR** (`tweetsentbr.py`) e **BPSAD** (`bpsad_adapter.py`).
  - Coleta paginada via **XFetch** (`xfetch.py`, integrado pelo PR #65 na `developer`), validada em suíte com cliente HTTP simulado.
  - Auditoria e cálculo de SHA-256 de datasets (`auditoria_datasets.py`).
- **Processamento e classificação (`src/processamento/classificacao/` e `pipeline.py`)**:
  - Adaptador `ClassificadorBertweet` com analisador injetável, normalização de rótulos (`positivo`, `negativo`, `neutro`) e validação de probabilidades.
  - Baseline clássico TF-IDF + Regressão Logística (`baseline.py`) e métricas de avaliação (`avaliacao.py`).
  - `PipelineClassificacao` em lote que preserva `texto_original`, `id_origem`, `fonte`, separa anotação humana (`rotulo_original`/`rotulo_padronizado`) da inferência (`sentimento`) e gera documentos compatíveis com BSON.
- **Banco de dados (`src/dados/database.py`)**:
  - Gerenciamento explícito de conexão e verificação (`ping`) com PyMongo e esquema lógico documentado em [`docs/banco/esquema-mongodb.md`](docs/banco/esquema-mongodb.md).
- **Serviço HTTP (`src/servico/main.py`)**:
  - Aplicação FastAPI com rota `GET /health` (`{"status": "ok"}`).
- **Painel web (`src/apresentacao/`, PRs #48, #70 e #71)**:
  - Aplicação Streamlit com navegação entre **Dashboard** e **Administração**.
  - Indicadores de total analisado e distribuição percentual por sentimento.
  - Filtros de período (`De` / `Até`) e de sentimento com botão **Limpar** e aviso de textos sem data excluídos do recorte temporal.
  - Fluxo administrativo com login (`Entrar` / `Sair`), upload de CSV com contagem de importados/descartados e acompanhamento de coleta.
  - Clientes HTTP (`fontes/api.py` e `fontes/administracao_api.py`) prontos para o contrato proposto em [`docs/frontend/CONTRATO-API.md`](docs/frontend/CONTRATO-API.md).

### O que opera em modo mock na demonstração
- O painel Streamlit roda por padrão com `SENTIA_FONTE_DADOS=mock` sobre **17 análises fictícias** identificadas na interface (`8` positivas / `47%`, `4` neutras / `24%`, `5` negativas / `29%`).
- O login administrativo (`admin` / `senha-de-exemplo`), a importação de CSV pela tela e o início/consulta de coleta no painel utilizam `AdministracaoMock` (validam formato e contabilizam linhas em memória, sem gravar no MongoDB nem acionar o BERTweet real).
- O script `scripts/demonstrar_pipeline.py` usa um analisador simulado determinístico para demonstrar o contrato `CSV → PipelineClassificacao → BSON` offline.

### O que continua pendente para as próximas entregas
- Persistência CRUD no MongoDB e índices automáticos (#20).
- Rotas reais de análises, resumo, filtros e administração no FastAPI (#19, #21, #23–#25, #58).
- Integração ponta a ponta entre painel, API, classificador e banco (#22, #26, #27).
- Gráficos de distribuição, resumo textual estatístico e nuvem de palavras no dashboard (#28–#30).
- Reprodução independente em corpus completo dos experimentos exploratórios BPSAD ([`docs/experimentos_bpsad.md`](docs/experimentos_bpsad.md), integrados pelo PR #64).

## Arquitetura

`src/apresentacao` (Streamlit) → `src/servico` (FastAPI) → `src/processamento` (aquisição/classificação) → `src/dados` (MongoDB).
Consulte [`docs/arquitetura.md`](docs/arquitetura.md) e [`docs/contratos-dados.md`](docs/contratos-dados.md).

## Preparação do ambiente

Requisitos: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) e Python 3.11.

```bash
uv sync --locked
make env
```

Para instalar também as dependências pesadas opcionais do classificador real (`torch`, `transformers` e `pysentimiento`):

```bash
uv sync --locked --group ml
# ou: make setup-ml
```

`make env` cria `.env` a partir de `.env.example` sem sobrescrever um arquivo existente. Não é necessário configurar MongoDB ou `XFETCH_API_KEY` para a demonstração offline.

## Execução

### 1. Painel Streamlit (modo demonstração mock)
```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run streamlit run src/apresentacao/app.py
```
Acesse `http://localhost:8501` (ou use `make run`). Para simular outros estados da interface, altere `SENTIA_MOCK_CENARIO` para `vazio` ou `erro`.

### 2. API FastAPI
```bash
uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
curl --fail http://127.0.0.1:8000/health
```
Resposta esperada: `{"status":"ok"}`.

### 3. Pipeline offline (CSV → Classificador simulado → BSON)
```bash
uv run python -m scripts.demonstrar_pipeline
```

## Validação e testes

```bash
make check
# ou individualmente:
uv lock --check
uv run ruff check --isolated --select F,E9 .
uv run ruff check src/apresentacao tests/test_painel_*.py
uv run pytest -v -ra
```

### Escopo da CI e governança de branches (`main` e `developer`)
- **Fluxo de branches**: o trabalho de desenvolvimento converge via Pull Request na branch `developer`, que mantém no histórico o commit da `main` (`c72faeb`) sem *force push* e sem arquivos `requirements*.txt` legados (gerenciamento unificado em `pyproject.toml` + `uv.lock`).
- **O que a CI valida automaticamente (`.github/workflows/ci.yml`)**: integridade do lockfile (`uv lock --check`), lint de erros sintáticos/nomes indefinidos (`ruff check --isolated --select F,E9 .`) e suíte automatizada offline (`pytest -v`) com dublês/mocks para banco, rede e classificador.
- **O que depende de serviços ou artefatos externos**: conexão com instância real do MongoDB (`uv run python test_mongo.py` com `MONGODB_URI`), download dos pesos do modelo Hugging Face (`--group ml`) e coleta real na API XFetch (`XFETCH_API_KEY`).

## Documentação

Consulte o índice completo em [`docs/README.md`](docs/README.md):
- [Roteiro de demonstração do PC1 (5–8 min)](docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md)
- [Status final do PC1 e ordem de merge](docs/qa/pc1/STATUS_FINAL.md)
- [Matriz de rastreabilidade](docs/qa/pc1/MATRIZ_RASTREABILIDADE.md)
- [Validação do frontend (#70 + #71)](docs/qa/pc1/VALIDACAO_FRONTEND_CLICIA.md)
- [Arquitetura](docs/arquitetura.md) e [Contratos de dados](docs/contratos-dados.md)
- [Guia do painel](docs/frontend/README.md), [Contrato da API](docs/frontend/CONTRATO-API.md) e [Wireframes](docs/frontend/WIREFRAMES.md)
- [Classificação](docs/classificacao.md), [TweetSentBR](docs/tweetsentbr.md), [BPSAD](docs/bpsad.md), [XFetch](docs/integracao_xfetch.md) e [Esquema MongoDB](docs/banco/esquema-mongodb.md)
