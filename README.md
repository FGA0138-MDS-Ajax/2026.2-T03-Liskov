# SentIA — Análise de Sentimentos

Plataforma web para análise de sentimentos em textos em português, desenvolvida pelo grupo **Liskov — T03**, na disciplina de **Métodos de Desenvolvimento de Software (MDS)** da Universidade de Brasília — Faculdade do Gama.

O SentIA organiza a aquisição de textos, classificação em sentimentos **positivo**, **negativo** e **neutro**, persistência e consulta de resultados por meio de uma API REST e de um painel web.

## Funcionalidades

- Importação e normalização de datasets CSV.
- Adaptadores para TweetSentBR e BPSAD.
- Coleta opcional de textos via XFetch, mediante configuração de credencial.
- Classificação de sentimentos com `pysentimiento/bertweet-pt-sentiment`.
- Baseline experimental TF-IDF + Regressão Logística e rotinas de avaliação.
- Persistência e consulta de análises, registros, datasets e pesquisas no MongoDB.
- API REST com FastAPI para processamento, consulta, resumo e operações administrativas.
- Painel Streamlit com dashboard, filtros e área administrativa; modo mock disponível para demonstração.

> O modo mock utiliza dados fictícios e não representa resultados persistidos no banco. Recursos experimentais ou ainda pendentes devem ser identificados como tais nos documentos de status e planejamento.

## Arquitetura

```text
Usuário
  ↓
Apresentação — Streamlit (src/apresentacao)
  ↓ HTTP/JSON
Serviço — FastAPI (src/servico)
  ↓
Processamento — Aquisição + Pipeline + Classificação (src/processamento)
  ↓
Dados — MongoDB / PyMongo (src/dados)
```

A API integra a camada de serviço; não há uma camada `src/api/` separada. A persistência MongoDB está centralizada em `src/dados/`.

## Tecnologias

| Responsabilidade | Tecnologias |
|---|---|
| Linguagem e ambiente | Python 3.11+, `uv` |
| Interface | Streamlit |
| API | FastAPI, Uvicorn |
| Persistência | MongoDB, PyMongo |
| Processamento | pandas, NLTK, scikit-learn |
| Classificação principal | PySentimiento / PyTorch (`bertweet-pt-sentiment`) |
| Qualidade | Pytest, pytest-cov, Ruff, GitHub Actions |
| Documentação | Markdown, MkDocs Material (portal mantido na branch `docs`) |

## Instalação

Pré-requisitos: Git, Python 3.11 ou compatível com `pyproject.toml`, `uv` e MongoDB para executar a API conectada.

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov.git
cd 2026.2-T03-Liskov
```

Instale as dependências fixadas:

```bash
uv sync --locked
```

Para instalar também as dependências pesadas necessárias à inferência real do BERTweet:

```bash
uv sync --locked --group ml
```

Crie o arquivo local de configuração a partir do exemplo, sem sobrescrever um `.env` já existente:

```bash
cp .env.example .env
```

No PowerShell, use `Copy-Item .env.example .env` caso o arquivo ainda não exista. Configure `MONGODB_URI` para uma instância MongoDB disponível. Não versione credenciais nem tokens.

## Execução

### Painel em modo de demonstração (mock)

```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run streamlit run src/apresentacao/app.py
```

Acesse `http://localhost:8501`. Os cenários mock aceitos são `normal`, `vazio` e `erro`.

No PowerShell:

```powershell
$env:SENTIA_FONTE_DADOS = "mock"
$env:SENTIA_MOCK_CENARIO = "normal"
uv run streamlit run src/apresentacao/app.py
```

### API FastAPI

Com `MONGODB_URI` configurado:

```bash
uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000 --reload
```

Verifique a disponibilidade em `http://127.0.0.1:8000/health` e consulte a documentação OpenAPI em `http://127.0.0.1:8000/docs`.

### Painel conectado à API

Em outro terminal:

```bash
SENTIA_FONTE_DADOS=api SENTIA_API_URL=http://127.0.0.1:8000 uv run streamlit run src/apresentacao/app.py
```

No PowerShell:

```powershell
$env:SENTIA_FONTE_DADOS = "api"
$env:SENTIA_API_URL = "http://127.0.0.1:8000"
uv run streamlit run src/apresentacao/app.py
```

As rotas administrativas também exigem as configurações de usuário e hash de senha descritas em `.env.example`. Gere o hash pelo comando documentado nesse arquivo; não registre senhas reais na documentação.

## Testes e qualidade

```bash
uv run ruff check src/apresentacao tests/test_painel_*.py
uv run ruff check --isolated --select F,E9 .
uv run pytest -ra --cov=src --cov-report=term-missing
uv lock --check
```

A CI executa os testes com um serviço MongoDB `mongo:7`. Para reproduzir localmente os testes que dependem do banco, configure `MONGODB_URI_TESTE`.

## Estrutura do projeto

```text
.
├── .github/workflows/   # CI do código
├── Datasets/            # Corpora e CSVs de demonstração
├── docs/                # Documentação técnica, QA, métricas e gestão
├── scripts/             # Scripts operacionais e experimentais
├── src/
│   ├── apresentacao/    # Streamlit
│   ├── servico/         # FastAPI e coordenação
│   ├── processamento/  # Aquisição, pipeline e classificação
│   └── dados/           # MongoDB e repositório
├── tests/               # Suíte automatizada e fixtures
├── Makefile
├── pyproject.toml
└── uv.lock
```

## Documentação

- [Índice da documentação técnica](docs/README.md)
- [Arquitetura atual](docs/arquitetura.md)
- [Contrato de dados](docs/contratos-dados.md)
- [Contrato da API e painel](docs/frontend/CONTRATO-API.md)
- [Guia da suíte de testes](tests/README.md)
- [Diagnóstico do repositório](docs/relatorios/diagnostico-repositorio.md)
- [Portal de documentação](https://fga0138-mds-ajax.github.io/2026.2-T03-Liskov/)

Os documentos de Visão do Produto, Arquitetura acadêmica e GQM são artefatos formais. Rascunhos e relatórios de revisão devem permanecer identificados como tais e não substituem versões aprovadas.

## Equipe

Projeto desenvolvido pelo grupo **Liskov — T03**, na disciplina de Métodos de Desenvolvimento de Software (MDS), UnB/FGA. A relação nominal dos integrantes e suas responsabilidades deve ser mantida conforme o registro oficial da equipe, sem atribuir contribuições não documentadas.
