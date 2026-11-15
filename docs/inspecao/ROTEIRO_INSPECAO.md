# Roteiro da Inspeção Cruzada — SentIA (LAMPORT → LISKOV)

- **Disciplina:** Métodos de Desenvolvimento de Software (MDS) — UnB/FGA, 2026.2
- **Mapeamento oficial (T03):** **LAMPORT inspeciona LISKOV** (`LISKOV` inspeciona `PERLMAN`)
- **Linha de base apresentada (`developer`):** [`1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920) (`13/11/2026`)
- **Objetivo:** Guiar a condução técnica e documental da sessão de inspeção em **5 a 10 minutos**, oferecendo ao grupo **LAMPORT** rastreabilidade completa de critérios, evidências, limitações honestas e PRs pendentes — **sem atribuir notas prévias**.

---

## 1. Roteiro Consolidado por Critério do Formulário

| Critério do Formulário | Evidência Principal no Projeto | Frente / Responsável | Pendência Conhecida no Corte | Link Direto |
| --- | --- | --- | --- | --- |
| **3.1 Formatos ABNT (`i–vi`, 10%)** — Quadro 5 | Auditoria ABNT, checklist ida-e-volta de referências e modelos revisados no PR `#90` (integrado) | Documentação / Acadêmica (`#86`, Héllen & equipe) | PDFs v1.0.0 originais contêm citações ausentes (`COHN, 2005`), bibliografia não citada (4 itens), `Acesso em: __ 2026` e sumário p. 30 em 29 pp.; PDFs brutos retidos por LGPD | [MATRIZ_EVIDENCIAS.md](MATRIZ_EVIDENCIAS.md#1-seção-31--quadro-5--formatos-abnt-aplicados-a-visão-e-arquitetura-10) · [REVISAO_ABNT.md](../revisao-academica/REVISAO_ABNT.md) |
| **3.2 Planejamento (30%) & Quadro 7 (`iii–iv`)** | Visão v1.0.0 Tabela 2.3.1 vs. Sprints 1–7 executadas, DoD, 4 eventos de replanejamento e reconciliação `C01–C06` | SM / PO (Renato & Héllen) | `SP`, velocidade e *burndown* = `N/D`; acesso `gh project` sem escopo `read:project`; incoerências `C01/C04/C05/C06` e conflito `RF02`/`RNF02` na US18 aguardando `#86` | [PLANEJAMENTO_E_REPLANEJAMENTOS.md](../gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md) · [REGISTRO_PRE_INSPECAO.md](REGISTRO_PRE_INSPECAO.md) |
| **Quadro 7 — Visão (`i`, `i-bis`, `ii`, `v`)** | Proposta de Visão atualizada (`1723a7d`), matriz de divergências Visão × código e pauta PO (`#90`, integrado) | PO / Equipe (Héllen & frentes) | Falta ratificar `ADR-001` (`RF03–RF06`), definir fontes/temas conforme feedback docente, retirar menção não comprovada a TDD e publicar versão final sem matrículas (`#86`) | [VISAO_ATUALIZADA_RASCUNHO.md](../revisao-academica/VISAO_ATUALIZADA_RASCUNHO.md) · [DECISOES_PENDENTES_PO.md](../revisao-academica/DECISOES_PENDENTES_PO.md) |
| **3.3 Gestão de Configuração (`i–ii`, 10%)** — Quadro 5-GC | Catálogo `IC-01..IC-09`, branches (`developer`/`main`/`docs`/`gh-pages`), 88/95 (92,6%) Conventional Commits, proteção GitHub e `.github/workflows/ci.yml` | Coordenação / Infra (Renato & equipe) | `enforce_admins: false` permitiu 24/28 merges em `developer` sem `APPROVED`; `checks: []` em branch protection; PR `#81` mesclado com aviso *"Não mesclar ainda"*; *Apêndice A* ausente na Arquitetura PDF | [GESTAO_CONFIGURACAO.md](../gestao/GESTAO_CONFIGURACAO.md) · [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) |
| **3.4 Métricas (`i–iv`, 25%)** — Quadro 6 | Plano GQM vigente (`O1–O3`, integrado pelo `#91` e atualizado pelo `#94` com a *Mini-tarefa GQM*), medições de cobertura/experimentos e análise crítica | Métricas / QA (Renato & equipe ML) | Falta ratificar ajustes docentes (`O2 Q4`, `O3 Q2`), regras `F1 < 60%`/`M3`/`R21–R22` e fronteiras de acurácia (`PO-12`); usabilidade (`#63`) não executada (Sprint 7); PR `#89` ainda aberto e não reproduzido | [PLANO_GQM_VIGENTE.md](../metricas/PLANO_GQM_VIGENTE.md) · [REGISTRO_E_ANALISE.md](../metricas/REGISTRO_E_ANALISE.md) |
| **3.5 Testes de Software (25%)** | Plano de testes, matriz `T01–T18`, relatório no SHA `1723a7d` (CI `43503741871`: 814 passed, 0 skipped, 93%; local sem Mongo: 789 passed, 25 skipped, 92%) | QA / Desenvolvedores | BERTweet, XFetch e UI HTTP usam dublês na suíte offline; `T14` parcial, `T15–T17` pendentes (Sprint 6), `T18` visual em navegador atual não reexecutado | [PLANO_TESTES_ATUAL.md](../qa/inspecao/PLANO_TESTES_ATUAL.md) · [MATRIZ_RASTREABILIDADE.md](../qa/inspecao/MATRIZ_RASTREABILIDADE.md) · [RELATORIO_EXECUCAO.md](../qa/inspecao/RELATORIO_EXECUCAO.md) |
| **Quadro 8 — Arquitetura (`i–iv`)** | Minuta atualizada (`ARQUITETURA_ATUALIZADA_RASCUNHO.md`), arquitetura técnica, contrato único `#19`, esquema MongoDB e `CONTRATO-API.md` | Arquitetura / Frentes (Julia, Maria Eduarda, Gabriel, Ricardo, Héllen, Juliana, Breno, Renato) | v1.0.0 PDF descreve `scikit-learn`/`.pkl`/`requirements.txt`/`main`; `ADR-001` sem ratificação PO; administração/pesquisa ainda em RAM; `/analises` sem login obrigatório | [ARQUITETURA_ATUALIZADA_RASCUNHO.md](../revisao-academica/ARQUITETURA_ATUALIZADA_RASCUNHO.md) · [../contratos-dados.md](../contratos-dados.md) · [../arquitetura.md](../arquitetura.md) |
| **Quadro 9 — Defeitos pré-mapeados** | Catálogo explícito de não conformidades técnicas, testes e pauta unificada `PO-01..PO-14 ↔ PO01..PO14` | Toda a equipe / PO | Itens abertos priorizados para correção nas Sprints 6 e 7 e deliberação pós-inspeção; conciliação inter-PRs registrada | [DEFEITOS_E_CORRECOES.md](../qa/inspecao/DEFEITOS_E_CORRECOES.md) · [MATRIZ_DIVERGENCIAS.md](../revisao-academica/MATRIZ_DIVERGENCIAS.md) · [PLANO_REGULARIZACAO.md](PLANO_REGULARIZACAO.md) |

---

## 2. Demonstração Técnica Ao Vivo (5 a 10 minutos)

O objetivo da demonstração na inspeção é provar ao grupo **LAMPORT** que os artefatos descritos correspondem fielmente ao código integrado em `developer` (`1723a7d`), distinguindo ambiente local simulado, testes com `mongo:7` na CI e funcionalidades ainda abertas.

### Etapa 1 (0:00 – 1:30) — Linha de base Git, CI e transparência de pré-inspeção
1. Conferir commit de base técnica na `developer` e merges documentais subsequentes:
   ```bash
   git log -6 --oneline origin/developer
   ```
   *(Linha de base técnica do código: `1723a7d` — Merge PR `#81`; documentação consolidada sobre ela pelos PRs integrados `#91`, `#94`, `#90` e `#92`.)*
2. Mostrar no GitHub a execução verde da CI no SHA técnico `1723a7d` ([run `43503741871`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871)) com o serviço `mongo:7`, os PRs documentais já integrados (`#90`, `#91`, `#92`, `#94`) e os PRs paralelos ainda abertos (`#93` na `docs`; `#83` e `#89` na `developer`).
3. Destacar explicitamente os dois pontos de governança já registrados pela própria equipe: o merge prematuro do PR `#81` (`GESTAO_CONFIGURACAO.md`) e o bloqueio de publicação dos PDFs brutos por conterem matrículas (`REGISTRO_PRE_INSPECAO.md`).

### Etapa 2 (1:30 – 4:00) — Verificação automatizada (`lint`, `lock`, `pytest` e pipeline BSON offline)
1. Executar verificações estáticas e lockfile:
   ```bash
   make lint && uv lock --check
   ```
2. Executar a suíte de testes local e explicar os skips esperados sem MongoDB ativo:
   ```bash
   make test
   ```
   - **Sem MongoDB local:** `789 passed, 0 failed, 25 skipped` (os 25 *skips* em `test_persistencia_leitura.py` e `test_repositorio.py` requerem `MONGODB_URI_TESTE` acessível).
   - **Na CI (`mongo:7`):** `814 passed, 0 failed, 0 skipped` (`93%` de cobertura).
3. Executar a demonstração de contrato do pipeline offline (usa analisador determinístico simulado):
   ```bash
   make demo
   ```
   *(Mostrar preservação de `texto_original`, separação de `rotulo_padronizado` vs. `sentimento`, datas UTC e estrutura BSON.)*

### Etapa 3 (4:00 – 7:30) — Execução da API FastAPI + Painel Streamlit (API local vs. Mock)
1. **Subir API FastAPI** (usando `SENTIA_ARMAZENAMENTO=memoria` caso não haja MongoDB local disponível durante a apresentação; deixar claro ao inspetor quando estiver usando banco real vs. memória):
   ```bash
   SENTIA_ARMAZENAMENTO=memoria uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
   ```
2. **Testar endpoints reais:**
   ```bash
   curl --fail http://127.0.0.1:8000/health
   curl --fail -X POST http://127.0.0.1:8000/analises \
     -H "Content-Type: application/json" \
     -d '{"registros":[{"id_origem":"demo-1","fonte":"inspecao","texto_original":"Excelente atendimento e entrega rápida"}]}'
   curl --fail http://127.0.0.1:8000/analises/resumo
   ```
   *(Em ambiente sem `--group ml` e pesos carregados, `POST /analises` retornará `503` com `"Serviço de classificação indisponível."` — comportamento esperado e testado em `test_api.py`; com `--group ml` instalado, classifica e persiste.)*
3. **Abrir o painel Streamlit** (`make run` em modo `mock` para demonstrar navegação e estados UI `normal`/`vazio`/`erro` com `admin` / `senha-de-exemplo`, ou `SENTIA_FONTE_DADOS=api` apontando para `http://127.0.0.1:8000`):
   - Demonstrar **Dashboard**: filtros de período e sentimento + indicadores + aviso de exclusão de registros sem `data_publicacao`; apontar abertamente que listagem, gráficos e resumo narrativo são entregas da Sprint 6 (`#27–#29`).
   - Demonstrar **Administração**: fluxo de login, importação CSV, coleta e a aba experimental **Pesquisar assunto** (`PR #81`), reforçando que suas tabelas operam em RAM e aguardam ratificação PO (**PO-05** a **PO-08**).

### Etapa 4 (7:30 – 9:30) — Revisão documental integrada e encerramento com pauta PO
1. Navegar diretamente na `developer` pelos arquivos de `docs/inspecao/`, `docs/gestao/`, `docs/revisao-academica/` (integrado via PR `#90`), `docs/metricas/` (integrado via PRs `#91` e `#94`) e `docs/qa/inspecao/` (PR `#91`), além do PR aberto `#89` (`feat/issue-85-avaliacao-bertweet`).
2. Confirmar com o grupo **LAMPORT** quaisquer novos defeitos identificados na inspeção para inclusão na pauta de reparos pós-inspeção (Sprint 7).

---

## 3. Consolidação Final dos PRs e Estado de Integração

> [!CAUTION]
> **Política de revisão e integração:** os PRs `#91`, `#94`, `#90` e `#92` já integram a `developer`; qualquer PR ainda aberto (micro-PR pós-merge, `#93` na `docs` e `#89`) exige revisão humana `APPROVED` (por revisor diferente do autor), CI verde no último commit e decisão explícita dos responsáveis.

### Lista de verificação de consolidação

| PR / Branch | Destino | Estado / Pré-condições | Sequência |
| --- | --- | --- | --- |
| PR [`#91`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91) (`inspecao/sol-medium`) | `developer` | **`MERGED`** (`c47ceab`) — `docs/metricas/*` e `docs/qa/inspecao/*` | Concluído (1º) |
| PR [`#94`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/94) (`gqm/regularizacao-pos-inspecao`) | `developer` | **`MERGED`** (`e64eea7`) — regularizou `PLANO_GQM_VIGENTE.md` e `REGISTRO_E_ANALISE.md` (*Mini-tarefa GQM*) | Concluído (2º) |
| PR [`#90`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90) (`inspecao/sol-high`) | `developer` | **`MERGED`** (`6bc1c17`, reconciliado em `6aa6a38`) — `docs/revisao-academica/*` | Concluído (3º) |
| PR [`#92`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/92) (`chore/inspecao-argon`) | `developer` | **`MERGED`** (`95438fd`) — `README.md`, `docs/README.md`, `docs/gestao/*`, `docs/inspecao/*` | Concluído (4º) |
| Micro-PR pós-merge (`chore/consolidacao-pos-merge`) | `developer` | **`OPEN` (em revisão)** — converte links temporários em caminhos relativos locais e aponta GQM ao estado pós-`#94` (`B-06`) | Em execução (5º) |
| PR [`#93`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/93) (`chore/inspecao-mkdocs`) | **`docs`** | **`OPEN`** — revisar e integrar após micro-PR pós-merge; links canônicos em `blob/developer/docs/...` já apontam para caminhos válidos (`B-06`) | Próximo (6º) |
| PR `#83` (`docs-qa-walkthrough-testes`) | `developer` | **`OPEN`** — fechar como superado por `#91` ou atualizar integralmente para `1723a7d` (`B-04`) | Higiene pendente |
| PR [`#89`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89) (`feat/issue-85-avaliacao-bertweet`) | `developer` | **`OPEN`** — reprodução empírica independente com `--group ml` + decisão **PO-02** sobre `RNF01` (`B-05`) | Trilha ML separada |

---

## 4. Checklist Executável de Inspeção e Publicação Pós-Merge

Use os comandos e verificações abaixo na ordem exata antes de cada etapa:

### 4.1 Verificação pós-merge na `developer` e estado do `#93`
- [x] **Confirmar integração das frentes documentais (`#91`, `#94`, `#90`, `#92`) em `origin/developer`.**
- [x] **Executar limpeza de links temporários (`B-06`)** convertendo URLs `blob/inspecao/sol-high/...`, `blob/inspecao/sol-medium/...` e SHAs de PRs em caminhos relativos locais e confirmando referência à versão GQM atualizada pelo PR `#94`.
- [ ] **Conferir PRs ainda abertos antes da inspeção:**
  ```bash
  git fetch origin && git log -1 --oneline origin/developer
  gh pr list --repo FGA0138-MDS-Ajax/2026.2-T03-Liskov --state open \
    --json number,title,headRefName,baseRefName,reviewDecision
  ```
  *Critério de aceite:* micro-PR pós-merge e PR `#93` (`→ docs`) com mínimo `1` revisão humana `APPROVED` externa ao autor (`B-01`) e ausência de dados sensíveis (`B-02`); deliberar fechamento/atualização do PR `#83` (`B-04`) e manter `#89` isolado (`B-05`).

### 4.2 Fase Demonstração Técnica na Sessão (`LAMPORT → LISKOV`, 5–10 min)
- [ ] **Validar ambiente, lockfile e lint:** `uv sync --locked && uv lock --check && make lint` (saída `0`).
- [ ] **Validar suíte automatizada local + apontar CI `mongo:7` (`43503741871`):**
  `make test` → esperado local sem MongoDB: `789 passed, 0 failed, 25 skipped (92% src)`; na CI (`mongo:7`): `814 passed, 0 failed, 0 skipped (93% src)`.
- [ ] **Validar pipeline BSON offline:** `make demo` (conferir preservação de `texto_original`, UTC e formato BSON sem credenciais).
- [ ] **Demonstrar API real em memória + Painel UI:** iniciar API (`SENTIA_ARMAZENAMENTO=memoria uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000`), consultar `GET /health` e `GET /analises/resumo`, e exibir Streamlit (`make run` modo `mock`) deixando explícito o que falta na Sprint 6 (`#27–#30`) e Sprint 7 (`#62`, `#63`, `#86`).
- [ ] **Percorrer evidências por critério (`MATRIZ_EVIDENCIAS.md §9` e `PLANO_REGULARIZACAO.md §2`):** apontar separação **Completo / Parcial / Pendente** e registrar novos achados da equipe inspetora **LAMPORT**.

### 4.3 Fase Final de Publicação (portal `docs` e higiene pós-inspeção)
- [ ] **Integrar o micro-PR pós-merge em `developer`** (com revisão `APPROVED` externa ao autor e CI verde).
- [ ] **Integrar o PR [`#93`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/93) na branch `docs`** e conferir o deploy gerado na branch `gh-pages`.
- [ ] **Avaliar limpeza segura das branches temporárias já integradas** (`inspecao/sol-high`, `inspecao/sol-medium`, `gqm/regularizacao-pos-inspecao`, `chore/inspecao-argon`) após confirmar aprovação do `#93`, preservando histórico em `git log` e nos PRs `#90`, `#91`, `#92` e `#94`.
