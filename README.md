# SentIA

Plataforma em desenvolvimento para análise de sentimentos em textos em português.
Projeto acadêmico da equipe **T03 — Liskov**, Métodos de Desenvolvimento de
Software, UnB/FGA, 2026.2.

## O que existe

- Importação CSV, adaptadores TweetSentBR/BPSAD e auditoria de datasets.
- Classificador BERTweet com analisador injetável, normalização de rótulos e
  pipeline em lote que preserva texto, identificadores e metadados.
- Baseline TF-IDF + regressão logística e ferramentas de avaliação.
- API FastAPI com `GET /health`.
- Painel Streamlit com navegação, indicadores e estados normal/vazio/erro em mock.
- Conexão explícita ao MongoDB e esquema documentado; persistência de análises
  e integração ponta a ponta ainda não implementadas.

O painel usa **dados fictícios identificados na tela**. O cliente HTTP representa
um contrato proposto; a API ainda não fornece os endpoints de análises/resumo.
XFetch e avaliação exploratória BPSAD estão nos PRs #65 e #64, respectivamente.
O PR #70 propõe filtros e administração mock e substitui o #66, fechado sem merge.
O [roteiro atualizado do PC1](docs/qa/pc1/ROTEIRO_PC1_ATUALIZADO.md) distingue
a reserva desta branch (cenário A) da integração experimental corrigida (cenário B).

## Arquitetura e tecnologias

`src/apresentacao` (Streamlit) → `src/servico` (FastAPI) →
`src/processamento` (aquisição/classificação) → `src/dados` (MongoDB).
As camadas existem, mas esse fluxo completo ainda depende de integração.
Python, uv, pandas, scikit-learn, requests, PyMongo, pytest e GitHub Actions
compõem a base. PySentimiento/PyTorch são opcionais para ML real.

## Preparação

Requisitos: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/)
e Python 3.11 (o uv pode provisioná-lo). Execute na raiz da branch de trabalho:

```bash
uv sync --locked
make env
```

`make env` copia `.env.example` somente se `.env` não existir. O exemplo unificado
inclui painel, API, MongoDB e XFetch; `.env.frontend.example` continua disponível
para compatibilidade. Variáveis já exportadas têm precedência sobre `.env`.
Não é necessário configurar banco ou credenciais para a apresentação offline.

## Executar

Painel, em um terminal:

```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run streamlit run src/apresentacao/app.py
```

API, em outro terminal:

```bash
uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
curl --fail http://127.0.0.1:8000/health
```

Resposta esperada: `{"status":"ok"}`. Abra o painel em
`http://localhost:8501`. Os atalhos `make run` e `make api` também estão disponíveis.

## Testes e demonstração

```bash
uv run pytest -v -ra
uv run pytest --cov=src --cov-report=term-missing
make lint
uv lock --check
git diff --check
uv run python -m scripts.demonstrar_pipeline
```

O último comando importa uma fixture sintética, usa um analisador **simulado** e
serializa documentos BSON sem conexão ao MongoDB. Não mede acurácia do BERTweet.
Consulte o [roteiro do PC1](docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md),
o [relatório PC1](docs/qa/pc1/RELATORIO_PC1.md) e o
[relatório final da auditoria](docs/qa/pc1/RELATORIO_FINAL_CODEX.md).

Para ML real, `uv sync --locked --group ml` instala dependências grandes e a
primeira inferência pode baixar pesos. Prepare isso antes; não é requisito da demo.

## Estrutura e documentação

| Caminho | Conteúdo |
|---|---|
| `src/` | Apresentação, serviço, processamento e dados |
| `tests/fixtures/` | Dados sintéticos dos testes |
| `scripts/` | Auditoria, comparação e demonstração |
| `docs/frontend/` | [Painel](docs/frontend/README.md) e contrato proposto |
| `docs/banco/` | [Esquema MongoDB](docs/banco/esquema-mongodb.md) |
| `docs/qa/` | Evidências de testes e homologação |
| `data/`, `models/` | Dados e modelos locais; não versionar artefatos grandes |
| `Datasets/` | Dataset legado; redistribuição/licença pendente de decisão própria |

Veja [classificação](docs/classificacao.md), [BPSAD](docs/bpsad.md),
[TweetSentBR](docs/tweetsentbr.md) e [configuração MongoDB](docs/mongodb_setup.md).
Atas e documentação acadêmica também existem na
[branch docs](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/docs).

## Contribuição e limitações

`main` guarda a versão estável de entrega; `developer` é integração.
Use branches próprias: `feat/`, `fix/`, `test/`, `docs/`, `chore/`.
Abra PR revisável, informe testes, contratos e pendências; não faça merge sem revisão.
Alterações de escopo, privacidade e licença precisam do aceite pertinente da PO/equipe.

Login, importação/coleta pelo painel, persistência, consultas/filtros na API,
gráficos completos e busca híbrida permanecem em desenvolvimento ou planejamento.
O smoke `/health` não comprova MongoDB, XFetch ou inferência real. A CI executa
testes offline; Ruff mantém o escopo existente do frontend e adiciona `F,E9`
em todas as camadas, sem formatação massiva do código legado.
