# Registro de Pré-Inspeção — SentIA (Grupo Liskov, T03)

- **Data da auditoria:** 14/11/2026
- **Repositório:** [`FGA0138-MDS-Ajax/2026.2-T03-Liskov`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov)
- **Linha de base (`developer`):** `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920` (`13/11/2026`)
- **Objetivo:** Registrar de forma reproduzível o estado exato de branches, Pull Requests, Issues, proteções do GitHub, workflows de CI, recuperação dos documentos acadêmicos originais e desvios detectados antes da entrega ao grupo inspetor (**LAMPORT**).

---

## 1. Inventário de Branches e Proteções (Git + GitHub API)

### 1.1 Branches principais e de publicação

| Branch | SHA no corte (14/11/2026) | Data do último commit | Proteção verificada (`gh api`) | Papel e Observação |
| --- | --- | --- | --- | --- |
| `developer` | `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920` | 13/11/2026 | **Protegida** (`enforce_admins: false`, `required_approving_review_count: 1`, `dismiss_stale_reviews: true`, `require_last_push_approval: true`, `strict: true`, `checks: []`) | Branch ativa de integração contínua das Sprints. |
| `main` | `c72faebf84e760e1fb704f19d7a05ca8c510d71d` | 02/11/2026 | **Protegida** (mesma configuração de `developer`) | Congelada na estrutura pré-`uv`/pré-PC1 (`PR #39`); receberá `developer` apenas após regularização e aceite na Sprint 7. |
| `docs` | `0433a5545628c3de58c247c43012a3cdbd52d93c` | 05/11/2026 | **Sem proteção** (`HTTP 404: Branch not protected`) | Fonte do MkDocs Material (`mkdocs.yml`, `docs/index.md`, atas 1 e 2); disparam deploy em `gh-pages`. |
| `gh-pages` | `e80ba9ffca7d7dc3b8fe6a62bd69c76f6b58d68d` | 05/11/2026 | **Sem proteção** (`HTTP 404: Branch not protected`) | Publicação estática gerada pelo GitHub Actions (MkDocs 1.6.1). |

### 1.2 Branches remotas abertas ou legadas observadas (`git branch -r`)

- **Abertas com PR ativo em 14/11/2026:**
  - `origin/docs-qa-walkthrough-testes` (`7009500`, PR `#83` aberto em 11/11);
  - `origin/feat/issue-85-avaliacao-bertweet` (`4a0e338`, PR `#89` aberto em 14/11);
  - `origin/inspecao/sol-high` (`d645d75`, PR `#90` aberto em 14/11);
  - `origin/inspecao/sol-medium` (`84530e4`, PR `#91` aberto em 14/11).
- **Branches antigas já integradas ou históricas não removidas no remoto:** `origin/feat/23-24-25-consultas-filtros-api`, `origin/feat/issue-21-adaptador-ml`, `origin/feat/issue-21-api-analises`, `origin/feat/pages`, `origin/feat/sentia-modelo`, `origin/fix/84-imports-testes-branch-julia`, `origin/xfetch`. Recomenda-se limpeza após encerramento da inspeção (mantendo histórico rastreável via PRs).

---

## 2. Inventário de Pull Requests (`#15` a `#91`)

Foram recuperados **45 Pull Requests** no repositório (`#15`, `#33–#48`, `#55–#56`, `#64–#84`, `#87–#91`; os números faltantes na sequência correspondem às *Issues*, já que o contador no GitHub é compartilhado): **38 `MERGED`**, **3 `CLOSED` sem merge** (`#33`, `#41`, `#66`) e **4 `OPEN`** (`#83`, `#89`, `#90`, `#91`).

### 2.1 PRs integrados por fase (`MERGED`, 38 PRs)

| Fase / Marco | PRs Mesclados | Destino Principal | Resumo das Entregas Integradas |
| --- | --- | --- | --- |
| **Inicialização e Sprint 1** (28/10 – 03/11) | `#15`, `#34–#39`, `#40`, `#42` | `main` (`#15`, `#37`, `#39`) e `developer` | Estrutura inicial (`#15`), abertura da `developer` (`#34`), importador CSV e adaptador BPSAD (`#35`, `#36`), testes iniciais (`#37`, `#38`), docs e auditoria TweetSentBR/datasets (`#40`, `#42`). |
| **Sprint 2 / 3 — ML, Banco e Fundação UI** (04/11 – 08/11) | `#43–#48`, `#55`, `#56` | `developer` e branches de PR | Esquema MongoDB (`#43`), adaptador BERTweet + comparação TF-IDF (`#44–#46`), conexão `pymongo` + QA (`#47`, `#56`), fundação Streamlit mock + QA (`#48`, `#55`). |
| **Entrega PC1** (08/11 – 09/11) | `#64`, `#65`, `#67–#73` | `developer` (exceto `#67`→`#64`, `#68`→`#65`) | Experimentos BPSAD + preservação BERTweet (`#64`, `#67`), XFetch (`#65`, `#68`), `uv`/`Makefile`/CI/Template (`#69`), painel filtros/admin mock (`#70`, `#71`), consolidação documental PC1 (`#72`, `#73`). |
| **Integração Pós-PC1** (10/11 – 13/11) | `#74–#82`, `#84`, `#87`, `#88` | `developer` (exceto `#79`→#21, `#88`→`#84`) | Testes de negação BERTweet (`#74`), API administrativa + auth (`#75`), contrato único + CI `mongo:7` + T09/T10 (`#76`, `#77`, `#82`), `POST /analises` + MongoDB (`#78`, `#79`), `GET /analises` e `/resumo` (`#80`), leitura/filtros/contagem MongoDB (`#84`, `#87`, `#88`) e pesquisa híbrida experimental (`#81`, ver Seção 4). |

### 2.2 PRs fechados sem merge (`CLOSED`, 3 PRs) e PRs abertos (`OPEN`, 4 PRs)

| PR | Estado | Branch (`head → base`) | Autor | Observação de Governança / CI no Corte |
| --- | --- | --- | --- | --- |
| `#33` | `CLOSED` | `feature/issue-2-csv-importer → main` | `Brenowr` | Substituído pelo fluxo em `developer` (`#35`/`#36`). |
| `#41` | `CLOSED` | `feat/integrar-classificador → developer` | `Gabriel-Ma7os` | Substituído pela sequência `#44`/`#45`/`#46`. |
| `#66` | `CLOSED` | `feat/painel-filtros-admin → developer` | `Cliciah` | Versão WIP substituída pelos PRs `#70` e `#71`. |
| **`#83`** | **`OPEN`** | `docs-qa-walkthrough-testes → developer` | `Figueirin` | Aberto em 11/11 sobre `fe83ad0` (707 testes); **sem conclusão de check registrada** no rollup e **superado pelo PR `#91`**. |
| **`#89`** | **`OPEN`** | `feat/issue-85-avaliacao-bertweet → developer` | `Ricardo-909-Leal` | Aberto em 14/11 (`18:58 UTC`); CI **`SUCCESS`** (run `43629551002`). Traz resultados declarados no BPSAD (10k amostra: BERTweet 67,70% acc vs. baseline 70,10% acc); **aguarda reprodução independente e decisão da PO sobre `RNF01`**. |
| **`#90`** | **`OPEN`** | `inspecao/sol-high → developer` | `Figueirin` | Aberto em 14/11 (`22:04 UTC`); CI **`SUCCESS`** (run `43646136042`). Frente acadêmica/ABNT (`docs/revisao-academica/`). |
| **`#91`** | **`OPEN`** | `inspecao/sol-medium → developer` | `Figueirin` | Aberto em 14/11 (`22:18 UTC`); frente GQM/métricas e QA (`docs/metricas/` e `docs/qa/inspecao/`). |

---

## 3. Inventário de Issues e Lacunas de Quadro (`#1` a `#86`)

Foram recuperadas **46 issues** cadastradas no GitHub (`#1–#4`, `#5–#14`, `#16–#32`, `#49–#54`, `#57–#63`, `#85–#86`), com **25 `CLOSED`** e **21 `OPEN`**.

> [!NOTE]
> **Limite de acesso ao quadro Kanban (GitHub Projects):** a consulta ao *GitHub Projects* via CLI local (`gh project`) exige o escopo de autenticação `read:project`, ausente no token da sessão atual. Portanto, o acompanhamento por colunas do quadro Kanban fica registrado como **`N/D`** neste corte, usando-se as **Issues, Milestones e Pull Requests** como fonte auditável.

### 3.1 Classificação real das Issues no corte de 14/11/2026

| Grupo de Situação | Issues | Quantidade | Leitura Técnica e Governança |
| --- | --- | --- | --- |
| **Fechadas (`CLOSED`)** | `#1–#4` (S1), `#5–#14` (S2), `#16–#17` (S3), `#19` (S4, contrato único), `#31` (S6, UI responsividade), `#49–#51` e `#57` (Épicos), `#59` (S6, login UI), `#60` (S5, importação UI) | **25** | `#1–#17` encerram S1–S3 operacionais (ainda pendentes de ratificação acadêmica `#86` e licença `#3`). **Ressalva em `#31`, `#57` e `#59`:** foram fechadas mesmo com `#58` (auth API ainda `OPEN`), sem evidência visual atualizada pós-PC1 de `T18` (`#31`), devendo constar na revisão de aceite da PO. |
| **Abertas com código principal já integrado na `developer` (S4 e S5)** | `#18` (infra/CI), `#20` (persistência MongoDB), `#21` (`POST /analises`), `#22` (QA T09–T10), `#23` (`GET /analises`), `#24` (filtro temporal), `#25` (filtro sentimento), `#58` (auth admin API) | **8** | **Implementadas e testadas em `1723a7d`** pelos PRs `#69`, `#75–#80`, `#84`, `#87`, porém **mantidas `OPEN`** por transparência até que haja execução integrada ao vivo, verificação de `T11–T13` completos e aceite formal da PO. |
| **Épicos abertos (`OPEN`)** | `#52` (`E04`), `#53` (`E05`), `#54` (`E06`) | **3** | Acompanhamento macro das Sprints 4, 5 e 6. |
| **Abertas em andamento / futuras / documentação (`OPEN`)** | `#26` (QA T11–T13), `#27` (UI listagem/API), `#28` (UI gráficos), `#29` (UI resumo textual), `#30` (UI nuvem opcional), `#32` (QA T14–T17), `#61` (UI coleta real), `#62` (publicação web), `#63` (teste usabilidade), `#85` (reprodução BPSAD por classe — PR `#89`), `#86` (atualização Visão/Arquitetura) | **10** | Escopo legítimo remanescente da Sprint 5 (`#26`, `#85`), Sprint 6 (`#27–#30`, `#32`, `#61`) e Sprint 7 (`#62`, `#63`, `#86`). |

*(Total conferido: 25 + 8 + 3 + 10 = 46 issues.)*

---

## 4. Auditoria de Workflows (CI) e Caso Crítico do PR `#81`

### 4.1 Execuções recentes do workflow `CI`

- **`1723a7d` (`push` em `developer`, 13/11/2026):** Run [`43503741871`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871) — **`success`** (executa `uv sync --locked`, `uv lock --check`, Ruff e `pytest` com `mongo:7`).
- **`936728d`, `29f2996`, `fe83ad0`, `a1c62fe`, `81f552c` (`push` em `developer`, 11–13/11):** todos **`success`**.
- **Falhas anteriores registradas em PRs antes de correção:** PR `#84` (`43100185858`, 11/11 — corrigida em `#88`/`#87` em 13/11) e PR `#81` (`43126136575`, 12/11 — corrigida em `8afed74` no run `43129680851`).
- **PRs abertos no corte:** PR `#89` (`43629551002` **`success`**), PR `#90` (`43646136042` **`success`**), PR `#83` (`43098475188` sem conclusão no rollup).

### 4.2 Registro detalhado do merge prematuro do PR `#81`

| Atributo Verificado (`gh pr view 81`) | Dado Observado |
| --- | --- |
| **Título / Branch** | `feat(administracao): pesquisa híbrida por assunto (versão de teste)` (`feat/pesquisa-hibrida-admin → developer`) |
| **Autora / Integrador** | Aberto por `Cliciah` (11/11/2026); correções de memória por `Brenowr`; mesclado por `Figueirin` em `2026-11-13T20:40:34Z` (`1723a7d`) |
| **Revisões no momento do merge** | `reviewDecision: REVIEW_REQUIRED`, `reviews: []` (possibilitado por `enforce_admins: false` na proteção da branch) |
| **Aviso na descrição do PR** | **`"**Não mesclar ainda.** ... Ainda falta abrir a issue, definir o limite de gasto no XFetch e ter o aceite da PO."`** |
| **Estado técnico em `1723a7d`** | Funcional e coberto por testes com dublês (`src/servico/pesquisa.py`, `tests/test_pesquisa_hibrida.py`), porém opera **sobre textos em memória** (`RepositorioAdministracao`), usa busca **lexical normalizada/radical 5 chars** (não Vector Search / MongoDB) e depende de deliberação da PO antes de ir para produção. |

---

## 5. Artefatos Acadêmicos Originais e Política de Privacidade (LGPD)

### 5.1 Situação do pacote `PACOTE_PRE_INSPECAO_LISKOV.zip` e documentos recuperados

1. O arquivo consolidado `PACOTE_PRE_INSPECAO_LISKOV.zip` **não foi localizado** em disco nem no repositório.
2. Entretanto, os **três PDFs originais oficiais** da disciplina estavam disponíveis localmente no ambiente de trabalho e foram auditados diretamente em texto extraído nesta etapa:
   - **`Formulario Inspeçao_professor.pdf`** (17 páginas): confirma os pesos oficiais (`3.1 Formatos 10%`, `3.2 Planejamento 30%`, `3.3 GC 10%`, `3.4 Métricas 25%`, `3.5 Testes 25%`), os Quadros 5 a 9, a escala de severidade (`Crítica 20%`, `Alta 15%`, `Média 10%`, `Baixa 5%`) e o mapeamento da Turma 03 (`LAMPORT inspeciona LISKOV`, `LISKOV inspeciona PERLMAN`).
   - **`T03_Liskov -Documento de Visao do Produto e Projeto Escopo.pdf`** (Versão `1.0.0`, `30/09/2026`, 41 páginas — incluindo cópia anotada com comentários do professor em PDF corrigido): permitiu conferir integralmente integrantes, Tabela 2.3.1 (Sprints 1–7), Seção 2.6 (replanejamento), DoD (Seção 3), Cenários C01–C06, Backlog RF01–RF16/RNF01–RNF02, GQM (Seção 5.1), Roteiro de Testes `T01–T18` (Seção 6.2), referências ABNT (Seção 7) e todos os comentários docentes.
   - **`T03_Liskov - Documento de Arquitetura-1.pdf`** (Versão `1.0.0`, `07/10`, 29 páginas): permitiu conferir metas/restrições, casos de uso `UC01–UC11`, fluxo originalmente planejado (`scikit-learn`, `.pkl`, `TF-IDF`, `requirements.txt`, PRs direto na `main`), divisão do `TweetSentBR` (15.000 tweets: 6.648 pos, 4.426 neg, 3.926 neu; 12.999 treino / 2.001 teste), ausência real do *Apêndice A* citado na p. 16 e discrepância de numeração no sumário (p. 30 vs. 29 páginas).

### 5.2 Bloqueio deliberado de commit dos PDFs brutos (`docs/referencias/`)

> [!CAUTION]
> Os arquivos `.pdf` originais recuperados localmente **não foram commitados** no repositório público nem em `docs/referencias/` por duas razões objetivas de privacidade e governança:
> 1. **Proteção de dados pessoais (LGPD):** as páginas iniciais da *Visão v1.0.0* e da *Arquitetura v1.0.0* listam nomes completos associados às **matrículas universitárias completas** dos 8 integrantes da equipe.
> 2. **Anotações docentes internas:** o PDF recuperado de Visão e o arquivo compactado de correções trazem comentários avaliativos e pontuações internas do professor sem autorização expressa de publicação aberta em repositório público.

**Solução adotada:** todas as informações técnicas, métricas originais, incoerências de requisitos e melhorias estruturais apontadas nesses documentos foram extraídas, sintetizadas sem matrículas e registradas de maneira transparente neste dossiê (`docs/inspecao/` e `docs/gestao/`). Caso os documentos originais precisem ser consultados durante a sessão síncrona de inspeção com o grupo **LAMPORT**, recomenda-se apresentá-los via canal institucional restrito ou após remoção prévia das matrículas pela equipe.
