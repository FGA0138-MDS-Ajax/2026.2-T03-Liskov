# Gestão de Configuração e Auditoria de Governança — SentIA

- **Projeto:** SentIA — Análise de Sentimentos em Português
- **Grupo:** Liskov — Turma 03 (MDS — UnB/FGA, 2026.2)
- **Corte auditado:** `origin/developer` @ `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920` (`13/11/2026`), `origin/main` @ `c72faebf84e760e1fb704f19d7a05ca8c510d71d`, `origin/docs` @ `0433a5545628c3de58c247c43012a3cdbd52d93c`, `origin/gh-pages` @ `e80ba9ffca7d7dc3b8fe6a62bd69c76f6b58d68d` (auditado em **14/11/2026**).
- **Referência no Formulário de Inspeção:** **Quadro 5 — Gestão de Configuração** (subseção `3.2` no corpo e item `3.3 - GC (10%)` nos pesos da Seção 5; critérios *i*: definição de ICs e políticas de branches/commits; *ii*: cumprimento efetivo pelo grupo).

---

## 1. Catálogo de Itens de Configuração (ICs)

A tabela abaixo formaliza os Itens de Configuração identificados no repositório e em artefatos correlatos, substituindo a lacuna do *Apêndice A* citado na p. 16 do *Documento de Arquitetura v1.0.0* (que não constava nas páginas finais do PDF original).

| Categoria de IC | Localização / Artefatos | Responsável Principal | Controle de Versão / Local |
| --- | --- | --- | --- |
| **IC-01 Código-fonte da aplicação** | [`src/`](../../src/) (`apresentacao/`, `servico/`, `processamento/`, `dados/`, `persistencia/`) | Equipe por frente (UI, API, ML, Banco, Dados) | Git (`developer` / `main`) via PR |
| **IC-02 Scripts operacionais e experimentos** | [`scripts/`](../../scripts/) (`analisar_em_lotes.py`, `auditar_datasets.py`, `comparar_modelos.py`, `demonstrar_pipeline.py`, `experimentos/`) | ML / Dados / QA | Git (`developer`) via PR |
| **IC-03 Suíte de testes e *fixtures*** | [`tests/`](../../tests/) (`test_*.py`, `conftest.py`, `fixtures/`) | QA / Desenvolvedores | Git (`developer` / `main`) + execução no CI |
| **IC-04 Ambiente e dependências** | [`pyproject.toml`](../../pyproject.toml), `uv.lock`, `.python-version`, [`Makefile`](../../Makefile), [`.env.example`](../../.env.example), [`.gitignore`](../../.gitignore) | Infra / Coordenação (`developer`); legado `requirements*.txt` em `main` | Git (`developer`); `uv lock --check` no CI |
| **IC-05 Automação CI e governança de PR** | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), [`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md) | Coordenação / QA | Git (`developer` / `main`; deploy MkDocs em `docs`) |
| **IC-06 Documentação técnica e QA** | [`README.md`](../../README.md), [`CHANGELOG.md`](../../CHANGELOG.md), [`docs/`](../README.md) (`decisoes/`, `banco/`, `frontend/`, `qa/`, `gestao/`, `inspecao/`) | Coordenação / Frentes técnicas | Git (`developer` via PR) |
| **IC-07 Portal MkDocs e atas** | `mkdocs.yml`, `docs/index.md`, `docs/atas-reuniao/ata-reuniao-{1,2}.md` | Coordenação / Documentação | Branch [`docs`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/docs) → deploy automático em `gh-pages` |
| **IC-08 Documentos acadêmicos base** | *Visão v1.0.0* (30/09, 41 pp.) e *Arquitetura v1.0.0* (07/10, 29 pp.), mais propostas em revisão | Equipe / PO / Acadêmica | PDFs fora do Git (contêm matrículas e notas docentes); revisões rastreáveis em Markdown no Git |
| **IC-09 Artefatos ignorados / locais** | `.env`, `data/`, `models/*.pkl`, `modelos/*.pkl`, `.venv/`, `.pytest_cache/` | Desenvolvedores (local) | Excluídos por `.gitignore`; **proibido** versionar segredos ou corpora não licenciados |

---

## 2. Política de Branches, Proteções e Fluxo de Integração

### 2.1 Estrutura de branches no repositório

| Branch | SHA no corte (14/11) | Papel vigente | Proteção GitHub verificada via API (`gh api`) |
| --- | --- | --- | --- |
| **`main`** | `c72faeb` (02/11/2026, PR `#39`) | Linha estável inicial (ainda pré-`uv` / pré-PC1); destino final de release | **Protegida:** exige 1 revisão (`required_approving_review_count: 1`), `dismiss_stale_reviews: true`, `require_last_push_approval: true`, `strict: true` em status checks, `allow_force_pushes: true`, `allow_deletions: false`, `enforce_admins: false`, `checks: []`. |
| **`developer`** | `1723a7d` (13/11/2026, PR `#81`) | Branch principal de integração contínua das Sprints | **Protegida:** regras idênticas à `main` (1 revisão exigida, `dismiss_stale_reviews: true`, `require_last_push_approval: true`, `strict: true`, `enforce_admins: false`, **`checks: []` / `contexts: []`**). |
| **`docs`** | `0433a55` (05/11/2026) | Fonte do site MkDocs Material e atas; workflow dispara deploy para `gh-pages` | **Sem proteção (`HTTP 404: Branch not protected`).** |
| **`gh-pages`** | `e80ba9f` (05/11/2026) | Artefato estático gerado por `mkdocs gh-deploy --force` (MkDocs 1.6.1) | **Sem proteção (`HTTP 404: Branch not protected`).** Não editar manualmente. |
| **Branches de trabalho** | `feat/*`, `fix/*`, `test/*`, `chore/*`, `docs-*`, `inspecao/*` | Desenvolvimento isolado por issue/frente antes de PR para `developer` (ou `chore/*` para `docs`) | Integração via Pull Request preenchido com [`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md). |

> [!NOTE]
> **Restrição técnica de nomenclatura no Git (`refs/heads/docs`):** como a branch `docs` existe no repositório remoto e local como arquivo de referência (`refs/heads/docs` / `refs/remotes/origin/docs`), o Git **impede** criar qualquer branch nomeada sob o prefixo `docs/...` (por exemplo `docs/inspecao-mkdocs` ou `docs/algo`), devido à colisão entre arquivo e diretório no sistema de referências. Por essa razão, branches documentais para `developer` usam prefixo `docs-...` ou `chore/...`, e a atualização do portal MkDocs para a branch `docs` utiliza `chore/inspecao-mkdocs`.

### 2.2 Divergência entre o plano original e a prática vigente

No *Documento de Arquitetura v1.0.0* (pp. 16 e 28), o grupo previa `requirements.txt` e Pull Requests direcionados diretamente à `main`. Após o replanejamento iniciado entre **29/10 e 02/11/2026** (PR `#34`) e consolidado antes do PC1 (PRs `#48` e `#69`), a política real migrou para:

- **`developer` como eixo de integração** (deixando `main` congelada em `02/11`);
- **`uv` + `pyproject.toml` + `uv.lock`** com Python fixado em `.python-version` (`3.11`), em vez de `requirements.txt`;
- **Conventional Commits** no padrão `<tipo>(<escopo-opcional>): <descrição>` (`feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `ci`);
- **Workflow único de CI (`.github/workflows/ci.yml`)** disparado em `push` para `main`/`developer` e em todo `pull_request`, rodando:
  1. `uv sync --locked`
  2. `uv lock --check`
  3. `uv run ruff check src/apresentacao tests/test_painel_*.py`
  4. `uv run ruff check --isolated --select F,E9 .`
  5. `uv run pytest -ra --cov=src --cov-report=term-missing` (com serviço `mongo:7` e `MONGODB_URI_TESTE=mongodb://127.0.0.1:27017`).

---

## 3. Auditoria de Cumprimento das Políticas (Critério *ii* do Quadro 5 — GC)

Os dados a seguir foram extraídos diretamente de `git log origin/developer`, da lista completa de 45 Pull Requests (`#15` a `#91`) e da API de proteção de branches do GitHub em **14/11/2026**.

### 3.1 Conformidade de Commits (Critério *ii*)

- **Universo auditado:** 95 commits não-merge no histórico de `origin/developer`.
- **Aderentes ao padrão Conventional Commits:** **88 de 95 (`92,6%`)** seguem rigorosamente `feat|fix|docs|chore|test|refactor|ci...`.
- **Exceções observadas (7 de 95):**
  - 2 commits iniciais do repositório em `07/09/2026` (`87ad596 Initial commit`, `e72a609 Initialize developer`);
  - 4 commits iniciais de funcionalidades sem prefixo convencional (`e056f42`, `3af20a4`, `844265c`, `63f3ce5`);
  - 1 commit de consolidação com dois tipos separados por vírgula (`ab2ddbe docs,test: ...`, seguido pelo padrão nos commits posteriores).

### 3.2 Conformidade de Pull Requests, Revisões e CI (Critério *ii*)

| Indicador Auditado | Resultado Observado | Interpretação Técnica / Risco de Governança |
| --- | --- | --- |
| **Total de PRs analisados (`#15`–`#91`)** | **45 PRs** (`38 MERGED`, `3 CLOSED`, `4 OPEN`: `#83`, `#89`, `#90`, `#91`) | Todo código relevante ingressou por PR; não foram identificados commits diretos fora de PRs após 02/11. |
| **CI na ponta atual da `developer` (`1723a7d`)** | **`SUCCESS`** (run [`43503741871`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871), job `132155891920`, `mongo:7`) | Suíte completa e lint aprovados no corte (`814 passed, 0 skipped, 93% cobertura` conforme relatório QA). |
| **PRs com `APPROVED` ativo antes do merge** | **5 de 38** `MERGED` no total; **4 de 28** direcionados à `developer` (`#65`, `#69`, `#71`, `#76`, além de `#15` na `main`) | **Achado relevante de GC:** em 24 dos 28 merges para `developer`, o merge ocorreu sem aprovação formal `APPROVED` vigente na interface do GitHub (`#72` e `#73` perderam aprovação por `dismiss_stale_reviews` após sync). |
| **Bypass administrativo (`enforce_admins: false`)** | **`enabled: false`** em `developer` e `main` | Permitiu ao mantenedor (`Figueirin`) concluir **13 merges de PRs de outros autores** sem clicar em *Approve* e **11 merges próprios** sem revisão externa registrada (acelerando a entrega na semana do PC1 e pós-PC1, mas enfraquecendo a rastreabilidade de dupla revisão prevista na DoD). |
| **Status check obrigatório na regra de proteção** | `strict: true`, porém **`checks: []` e `contexts: []`** | A proteção pede branch atualizada se houver check exigido, mas **nenhum job específico (`test`) está listado como obrigatório** na configuração do GitHub. |
| **Uso do Template de PR** | Adotado após PR `#69` (09/11) | PRs antigos (`#15–#48`) anteriores à criação do template são heterogêneos; PRs recentes (`#69+`, `#81`, `#89`, `#90`, `#91`) seguem o template. |
| **Nomenclatura de branches** | Majoritariamente aderente após 02/11 (`feat/*`, `fix/*`, `chore/*`, `inspecao/*`) | Exceções legadas mantidas no histórico: `Datasets`, `xfetch`, `feature/config-mongodb-pymongo`, `issue-2-csv-importer`. |

### 3.3 Desvio específico documentado: Merge prematuro do PR `#81`

O **PR `#81`** (`feat/pesquisa-hibrida-admin → developer`, autoria `Cliciah`, ajustes `Brenowr`, merge em `1723a7d` por `Figueirin` em `13/11/2026T20:40:34Z`) apresenta três fatos objetivos que devem ser expostos com transparência na inspeção:

1. **Aviso explícito no corpo do PR:** a primeira frase registrava **`"**Não mesclar ainda.**"`**, explicando que faltavam abrir a *issue* correspondente, definir o limite financeiro de uso do XFetch, validar o critério de relevância da busca e obter **aceite da PO**.
2. **Condição de merge no GitHub:** o workflow de CI estava verde (`43503741871`), mas `reviewDecision` permanecia `REVIEW_REQUIRED` com zero revisões (`reviews: []`), sendo o merge executado via prerrogativa administrativa (`enforce_admins: false`).
3. **Conduta adotada neste dossiê:** o código de `src/servico/pesquisa.py` existe no corte `1723a7d` e compõe a base testada, porém é tratado explicitamente como **incremento experimental integrado antes da homologação**, sem presunção de aceite da PO e sem reversão unilateral sem decisão formal da equipe/PO.

### 3.4 Privacidade, segredos e integridade de artefatos

- **Segredos:** [`.env.example`](../../.env.example) contém apenas chaves vazias e valores padrão seguros (`mock`); `.gitignore` impede commit de `.env`, `data/` e `*.pkl`. Nenhuma credencial do MongoDB Atlas, hash de senha administrativa real ou `XFETCH_API_KEY` está versionada na árvore atual.
- **Corpora externos:** o arquivo legado `Datasets/tweetsent.csv` foi auditado e removido da árvore ativa (pendência de licença documentada na issue `#3` e em [`docs/tweetsentbr.md`](../tweetsentbr.md)).
- **Dados acadêmicos pessoais (LGPD):** os PDFs originais de *Visão v1.0.0* e *Arquitetura v1.0.0* contêm matrículas universitárias completas de toda a equipe e anotações de correção docente; por isso, **não foram commitados** no repositório público (detalhado em [`REGISTRO_PRE_INSPECAO.md`](../inspecao/REGISTRO_PRE_INSPECAO.md)).

---

## 4. Ações Recomendadas para Regularização de GC (Pré-Promoção à `main`)

1. **Fixar o job `test` do workflow `CI` em `required_status_checks` (`contexts`/`checks`)** nas regras de proteção das branches `developer` e `main`.
2. **Ativar `enforce_admins: true`** após a conclusão da janela de regularização da inspeção (ou exigir ao menos 1 revisão `APPROVED` de par diferente do autor para qualquer merge, inclusive de mantenedores).
3. **Proteger a branch `docs`** (ao menos contra deleção e *force push*, com revisão em PR), evitando alterações diretas que disparem publicação automática em `gh-pages` sem conferência.
4. **Adotar GitHub *Draft PR*** sempre que um PR trouxer aviso de *"não mesclar"*, impedindo tecnicamente o merge acidental (caso `#81`).
5. **Reconciliar a documentação de arquitetura (`#86`)** com o processo real (`developer`, `uv.lock`, `pyproject.toml`, políticas de GC formalizadas neste arquivo e remoção da referência fantasma ao *Apêndice A*).
6. **Planejar a sincronização `developer → main` na Sprint 7**, somente após ratificação das pendências pela PO e execução completa da lista de verificação pré-release.
