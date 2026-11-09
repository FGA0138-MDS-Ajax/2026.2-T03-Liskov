# Status Final do PC1 — SentIA

Data: **09/11/2026**
Repositório: `FGA0138-MDS-Ajax/2026.2-T03-Liskov`
Base `origin/developer`: `66c22ce` (já inclui o PR #65 — XFetch e o PR #64 — Experimentos BPSAD).
Branch de integração testada: `test/pc1-integracao-frontend-atualizado` (`origin/developer` + #69 + #70 + #71 + #72).

---

## 1. Resumo das Correções de Organização

1. **PR #71 (`fix/pr70-ensaio-pc1` → `feat/painel-frontend`)**: revisado e validado sobre o PR #70 da Clicia; workflow `.github/workflows/ci.yml` alinhado com o PR #69 para evitar conflito quando o #70 for integrado na `developer`.
2. **PR #69 (`chore/pc1-estabilizacao-organizacao` → `developer`)**: atualizado com `origin/developer` (`66c22ce`, após os merges dos PRs #65 e #64) e limpo de 18 arquivos de logs/evidências brutas, ficando restrito a **6 arquivos de infraestrutura e demonstração offline** (`.env.example`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/workflows/ci.yml`, `.gitignore`, `Makefile`, `scripts/demonstrar_pipeline.py`).
3. **PR #72 (`chore/pc1-ensaio-relatorios` → `developer`)**: redirecionado para `developer` (eliminando a cadeia de PRs), limpo de 44 arquivos de capturas PNG e logs brutos, e consolidado como **PR documental pequeno (8 arquivos Markdown)**: `README.md`, `docs/README.md`, `docs/arquitetura.md`, `docs/contratos-dados.md`, `docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md`, `docs/qa/pc1/MATRIZ_RASTREABILIDADE.md`, `docs/qa/pc1/VALIDACAO_FRONTEND_CLICIA.md` e `docs/qa/pc1/STATUS_FINAL.md`.
4. **PR #73 (`docs-pc1-documentacao-consolidada` → `developer`)**: redirecionado da branch experimental `test/pc1-base-documentacao` para `developer`, limpo dos 61 arquivos de evidências brutas e revertidas todas as edições em documentos acadêmicos/técnicos dos colegas (preservando autoria original). Seu conteúdo útil foi consolidado no #72.

---

## 2. Resultados dos Testes e Validações Executadas

| Verificação | Comando | Resultado |
|---|---|---|
| Dependências e lockfile | `uv sync --locked && uv lock --check` | **OK** (ambiente Python 3.11 íntegro) |
| Suíte completa de testes | `uv run pytest -v -ra` | **538 passed, 0 failed, 0 skipped** (cobertura `src/`: **94%**) |
| Lint do painel | `uv run ruff check src/apresentacao tests/test_painel_*.py` | **OK** (`All checks passed!`) |
| Lint incremental geral | `uv run ruff check --isolated --select F,E9 .` | **OK** (`All checks passed!`) |
| Smoke test FastAPI | `GET http://127.0.0.1:8000/health` | **OK** (`HTTP 200`, `{"status":"ok"}`) |
| Smoke test Streamlit | `streamlit run src/apresentacao/app.py --server.headless=true` | **OK** (Dashboard e Administração renderizados sem erros) |
| Fluxos do painel (mock) | Filtros (`De`/`Até`, sentimento, `Limpar`), login (`admin`/`senha-de-exemplo`), upload CSV e coleta | **OK** (17 registros iniciais → 5 negativos → 5 em ago/2026 com 4 sem data → 17 após `Limpar`; CSV válido importa 5; CSV malformado tratado) |
| Pipeline offline | `uv run python -m scripts.demonstrar_pipeline` | **OK** (5 registros importados de CSV, classificados via mock e serializados em BSON) |

---

## 3. O que Funciona, o que é Mock e o que Continua Pendente

- **Funciona com código de produção**:
  - Importação CSV estrita/tolerante (`csv_importer.py`), adaptadores TweetSentBR (`tweetsentbr.py`) e BPSAD (`bpsad_adapter.py`), coleta XFetch com controle de paginação (`xfetch.py`, PR #65) e auditoria de datasets (`auditoria_datasets.py`).
  - `ClassificadorBertweet`, baseline TF-IDF + Regressão Logística, métricas de avaliação e `PipelineClassificacao` em lote com validação e serialização BSON.
  - Gerenciamento explícito de conexão MongoDB (`src/dados/database.py`) e endpoint `GET /health` no FastAPI (`src/servico/main.py`).
  - Estrutura, filtros, telas administrativas e clientes HTTP do painel Streamlit (`src/apresentacao/`).
- **Opera em modo Mock na demonstração do PC1**:
  - Os 17 registros exibidos no dashboard (`src/apresentacao/fontes/mock.py`).
  - Autenticação (`admin` / `senha-de-exemplo`), contagem de linhas no upload CSV pela tela e acompanhamento de coleta (`src/apresentacao/fontes/administracao_mock.py`).
  - O analisador injetado em `scripts/demonstrar_pipeline.py` (evita download de pesos pesados durante a apresentação ao vivo).
- **Continua pendente para as próximas entregas**:
  - Persistência CRUD e criação automática de índices no MongoDB (Issue #20).
  - Endpoints reais de análises, resumo, filtros e administração no FastAPI (Issues #19, #21, #23–#25, #58).
  - Gráficos de distribuição, resumo textual estatístico e nuvem de palavras no dashboard (Issues #28–#30).
  - Reprodução independente em corpus completo dos experimentos exploratórios BPSAD (integrados pelo PR #64).

---

## 4. Ordem Recomendada de Revisão e Merge

1. **PR #69** (`chore/pc1-estabilizacao-organizacao` → `developer`) — *Preparação técnica do PC1 (6 arquivos, `MERGEABLE`)*.
2. **PR #71** (`fix/pr70-ensaio-pc1` → `feat/painel-frontend`) — *Correções de CSV, botão Limpar e CI direcionadas ao PR #70 (5 arquivos, `MERGEABLE`)*.
3. **PR #70** (`feat/painel-frontend` → `developer`) — *Frontend da Clicia já com as correções do #71 incorporadas (`MERGEABLE`)*.
4. **PR #72** (`chore/pc1-ensaio-relatorios` → `developer`) — *Documentação consolidada do PC1, roteiro, matriz de rastreabilidade e status final (8 arquivos Markdown, `MERGEABLE`)*.
5. **PR #73** (`docs-pc1-documentacao-consolidada` → `developer`) — *Redirecionado da branch experimental para `developer` e limpo; pode ser fechado após o merge do #72*.
