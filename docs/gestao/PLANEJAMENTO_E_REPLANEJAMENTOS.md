# Planejamento, Acompanhamento de Sprints e Replanejamentos — SentIA

- **Projeto:** SentIA — Análise de Sentimentos em Português
- **Grupo:** Liskov — Turma 03 (MDS — UnB/FGA, 2026.2)
- **Corte de referência:** `origin/developer` @ `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920` (**13/11/2026**, auditado em **14/11/2026**)
- **Finalidade:** Registrar o ciclo de vida adotado, o confronto entre o planejamento original (*Documento de Visão v1.0.0*, 30/09/2026) e a execução observada no GitHub, os eventos formais de replanejamento e as incoerências documentais em aberto para avaliação e correção antes da inspeção cruzada (**LAMPORT → LISKOV**).

> [!IMPORTANT]
> Este documento **não fabrica** Story Points, velocidade histórica ou série diária de *burndown* retroativamente. Quando a evidência não existe nos registros do projeto, o campo aparece explicitamente como **`N/D`**. O término técnico ou merge de código antecipado também **não** equivale ao encerramento formal da Sprint nem ao aceite da Product Owner (PO).

---

## 1. Ciclo de Vida, Ritos e Critério de Pronto (DoD)

O processo definido no *Documento de Visão v1.0.0* (seções 2.1 e 3) combina **Scrum** com práticas de **Extreme Programming (XP)**:

- **Cadência:** Sprints semanais (7 dias) divididas em **7 Sprints** no período de **13/10/2026 a 30/11/2026** (Tabela 2.3.1 da Visão v1.0.0, pp. 11–12).
- **Ritos e papéis:**
  - *Product Owner (PO):* Héllen Clícia Barros Rêgo (refinamento, priorização de backlog e homologação funcional).
  - *Scrum Master (SM) / Coordenação de Qualidade e Testes:* Renato Rodrigues Campos Filho (facilitação, revisão de fluxo, automação QA/CI).
  - *Desenvolvimento por frentes:* Dados/Aquisição, Machine Learning, Persistência MongoDB, API FastAPI e Frontend Streamlit.
  - Atas formais registradas na branch `docs` ([Ata 1 — 25/09/2026](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/docs/docs/atas-reuniao/ata-reuniao-1.md) e [Ata 2 — Daily](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/docs/docs/atas-reuniao/ata-reuniao-2.md)).
- **Critério de Pronto (*Definition of Done*, Visão v1.0.0, p. 19):** um item do backlog só deve ser considerado pronto quando atender cumulativamente a:
  1. testes unitários implementados e aprovados;
  2. integração contínua (CI) executada sem falhas;
  3. revisão por pares aprovada em Pull Request;
  4. critérios de aceitação validados pela Product Owner;
  5. documentação técnica atualizada no GitHub quando aplicável.

### Ajustes de processo pendentes apontados pela revisão docente

Na revisão da Visão v1.0.0 (anotações no PDF original), o docente destacou dois ajustes metodológicos obrigatórios que permanecem pendentes de incorporação na versão acadêmica:

1. **Incluir marcos formais da disciplina no cronograma:** explicitar no planejamento as datas de entrega do **Ponto de Controle 1 (PC1)** (executado em **09/11/2026**), da **execução das inspeções cruzadas** (`LAMPORT` inspeciona `LISKOV`; `LISKOV` inspeciona `PERLMAN`) e da **janela de reparos pós-inspeção**.
2. **Retirar ou comprovar TDD estrito:** remover a menção genérica a *Test-Driven Development* (TDD) na Figura 3 da Visão v1.0.0 caso a equipe não adote e evidencie formalmente o ciclo *Red → Green → Refactor* nos commits/PRs (como ocorre hoje).

---

## 2. Planejamento Original vs. Execução por Sprint (Corte 14/11/2026)

A tabela abaixo confronta o plano original da **Tabela 2.3.1** (*Documento de Visão v1.0.0*, pp. 11–12), os **Milestones do GitHub** observados nas issues `#1` a `#86`, os entregáveis e a situação real em `origin/developer` (`1723a7d`).

| Sprint | Período Visão v1.0.0 | Vencimento Milestone GitHub | Foco e Entregáveis Planejados (Visão / Backlog) | Execução Observada (Issues / PRs / Código em `1723a7d`) | Situação Formal no Corte (14/11) |
| --- | --- | --- | --- | --- | --- |
| **Sprint 1** | 13/10 – 19/10/2026 | 03/11/2026 | **Aquisição dos dados:** dataset inicial organizado e importação/coleta (`#1` RF02, `#2` RF01, `#3` auditoria, `#4` testes) | Entregue com reprogramação para 02–03/11: inicialização em `main` (`#15`, `#37`, `#39`), importador CSV/BPSAD (`#35`, `#36`), dataset/auditoria TweetSentBR (`#40`, `#42`) e posteriormente XFetch (`#65`, `#68`). **Issues `#1–#4`: `CLOSED` em 03/11.** | **Concluída com replanejamento** *(pendência residual de licença/redistribuição em `#3`)* |
| **Sprint 2** | 20/10 – 26/10/2026 | 03/11/2026 | **Preparação dos textos:** na Visão v1.0.0 previa limpeza clássica, remoção de *stopwords*, *stemming* e TF-IDF (`#5–#10`); no replanejamento passou a incluir bases de banco (`#11–#12`) e frontend (`#13–#14`) | Implementada preservação de texto para BERTweet + `ADR-001` proposto + pipeline em lote (`#44–#46`, `#64`, `#67`, `#74`); esquema e conexão MongoDB (`#43`, `#47`, `#56`); fundação Streamlit em mock (`#48`, `#55`). **Issues `#5–#14`: `CLOSED` entre 04/11 e 10/11.** | **Concluída com replanejamento arquitetural** *(ratificação formal da PO para ADR-001/RF03–RF06 pendente)* |
| **Sprint 3** | 27/10 – 02/11/2026 | 02/11/2026 | **Análise de sentimentos:** classificador e avaliação (`#16` RF07, `#17` RNF01/US08) | Adaptador `ClassificadorBertweet` e módulo `avaliacao.py` / `comparar_modelos.py` integrados (`#44`, `#45`, `#64`, `#74`). **Issues `#16–#17`: `CLOSED` em 09/11.** Porém avaliação completa no BPSAD por classe foi reaberta na `#85` (PR `#89` aberto). | **Concluída com ressalva** *(meta `RNF01 ~80%` e domínio TweetSentBR/BPSAD em reavaliação na `#85`/`#89`)* |
| **Sprint 4** | 03/11 – 09/11/2026 | 09/11/2026 | **Persistência e disponibilização:** MongoDB integrado + API FastAPI (`#18` infra/CI, `#19` contrato único, `#20` RF08, `#21` RF09, `#22` QA T09–T10) e marco **PC1 (09/11)** | **PC1 apresentado em 09/11** com pipeline offline e painel mock (`#69–#73`). Persistência MongoDB, `uv`, CI `mongo:7`, contrato único e rotas reais (`POST /analises`, administração) integrados entre **10/11 e 13/11** (`#75–#79`, `#82`, `#84`, `#87`, `#88`). **`#19` `CLOSED` (11/11); `#18`, `#20`, `#21`, `#22` ainda `OPEN`.** | **Carry-over / Parcialmente entregue** *(código principal em `developer`; pendente aceite de critérios, fluxo ao vivo completo e fechamento de `#18`, `#20–#22`)* |
| **Sprint 5** | 10/11 – 16/11/2026 | 16/11/2026 | **Consulta e filtragem + Administração:** paginação (`#23`), filtro temporal (`#24`), filtro por sentimento (`#25`), QA (`#26`), login API (`#58`), importação UI (`#60`) e reavaliação BPSAD (`#85`) | `GET /analises`, `GET /analises/resumo` e auth/admin API já integrados (`#75`, `#80`, `#84`, `#87`); pesquisa híbrida lexical+XFetch mesclada prematuramente (`#81`, 13/11); PR `#89` (`#85`) e PR `#83` abertos. **`#60` `CLOSED` (10/11); `#23–#26`, `#58`, `#85` `OPEN`.** | **Em andamento** *(sprint vigente até 16/11; `#81` requer ratificação da PO e `#23–#26`/`#58`/`#85` aguardam validação)* |
| **Sprint 6** | 17/11 – 23/11/2026 | 23/11/2026 | **Visualização e integração:** dashboard conectado à API com listagem (`#27`), gráficos (`#28`), resumo textual (`#29`), nuvem de palavras opcional (`#30`), responsividade (`#31`), QA T14–T17 (`#32`), login UI (`#59`), coleta UI (`#61`) | Parte do cliente HTTP, indicadores numéricos e tela admin já existe em `src/apresentacao/` (`#70`, `#71`, `#81`); **faltam no dashboard:** listagem paginada de textos, gráficos de distribuição, resumo textual narrativo e nuvem de palavras. **`#31` e `#59` marcados `CLOSED` (14/11); `#27–#30`, `#32`, `#61` `OPEN`.** | **Planejada (Futura)** *(código antecipado não conclui a Sprint 6 nem substitui testes visuais T14–T18 e aceite)* |
| **Sprint 7** | 24/11 – 30/11/2026 | 30/11/2026 | **Finalização e entrega:** implantação pública (`#62`), teste de usabilidade (`#63`), atualização acadêmica Visão/Arquitetura (`#86`), reparos da inspeção | Dossiê técnico e propostas de revisão em elaboração paralela (PRs `#90`, `#91` e este dossiê). **`#62`, `#63` e `#86` `OPEN`.** | **Planejada (Futura)** *(aguarda conclusão da Sprint 5–6, inspeção LAMPORT e reparos)* |

### Indicadores quantitativos de Sprint

| Métrica de Planejamento | Valor Observado | Fonte / Observação |
| --- | --- | --- |
| Story Points planejados por Sprint | **`N/D`** | Não há estimativa de Story Points registrada no *Documento de Visão v1.0.0* nem nas issues. |
| Velocidade real (SP / Sprint) | **`N/D`** | Impossível calcular sem pontuação original; contagem de PRs **não** deve ser convertida em velocidade. |
| Série histórica diária de *Burndown* | **`N/D`** | Sem registro diário de esforço/pontos restantes. |
| GitHub Projects (quadro Kanban) | **Acesso externo indisponível** | Token local da CLI (`gh`) não possui escopo `read:project`; auditoria baseada em *Issues*, *Milestones* e *Pull Requests*. |
| Issues cadastradas no repositório | **46 issues** (`#1–#4`, `#5–#14`, `#16–#32`, `#49–#54`, `#57–#63`, `#85–#86`) | **25 fechadas** e **21 abertas** até 14/11/2026. |

---

## 3. Linha do Tempo dos Replanejamentos Documentados

A Seção 2.6 do *Documento de Visão v1.0.0* (p. 16) estabelece como gatilhos formais de replanejamento: alterações técnicas/arquiteturais, indisponibilidades, achados em inspeções, orientações docentes e prazos da disciplina. Entre **30/09/2026** e **14/11/2026**, quatro eventos principais alteraram o plano original:

### Replanejamento 1 — 29/10/2026: Troca para BERTweet pré-treinado, infraestrutura `uv` e ajuste de Sprints 1–2

- **Evidências:** criação das issues `#16` e `#17` (29/10/2026), extensão dos *Milestones* das Sprints 1 e 2 para **03/11/2026**, abertura da branch de integração `developer` (PR `#34`, 02/11), criação da branch `docs` com MkDocs (05/11), introdução proposta do [`ADR-001`](../decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md) e migração futura para `pyproject.toml` + `uv.lock` (PRs `#48` e `#69`).
- **O que mudou em relação à Visão/Arquitetura v1.0.0:**
  - Substituição do treinamento próprio em `scikit-learn` + remoção de *stopwords* + *stemming* + TF-IDF no fluxo principal (antes Sprints 2 e 3) pelo adaptador pré-treinado `pysentimiento/bertweet-pt-sentiment` preservando o texto bruto. O `baseline.py` (TF-IDF + Regressão Logística) foi mantido isolado apenas como referência comparativa.
  - Deslocamento do fechamento operacional das Sprints 1 e 2 de 19/10 e 26/10 para **02–03/11/2026**, antecipando fundação de MongoDB (`#11`, `#12`) e Streamlit (`#13`, `#14`).
  - Abandono do fluxo direto de PRs apenas em `main` (v1.0.0) em favor de `developer` para integração contínua e `main` congelada na versão estável inicial (`c72faeb`, 02/11).
- **Situação documental:** registrado na **issue `#86` (OPEN)** e proposto para revisão em `docs/revisao-academica/` (PR `#90`) e `docs/qa/inspecao/` (PR `#91`). Aguarda atualização formal dos PDFs acadêmicos após decisão da PO.

### Replanejamento 2 — 07/11 a 09/11/2026: Perfil Administrador, Épicos e Entrega do PC1

- **Evidências:** criação dos Épicos `#49–#54` e `#57` (07–08/11), criação das issues administrativas e operacionais `#58–#63` (08/11), e merge dos PRs `#64`, `#65`, `#69–#73` na entrega do **Ponto de Controle 1 (09/11/2026)**.
- **O que mudou:**
  - Formalização do escopo administrativo com autenticação (`#57`, `#58`, `#59`), importação via UI (`#60`) e disparo de coleta (`#61`), além da separação explícita entre **modo mock para demonstração (`SENTIA_FONTE_DADOS=mock`)** e integração real com API/MongoDB.
  - Explicitação de itens antes implícitos para a Sprint 7: publicação web (`#62`) e execução formal do teste de usabilidade (`#63`, Métrica 3.1).

### Replanejamento 3 — 10/11 a 13/11/2026: Integração backend pós-PC1 e pesquisa híbrida experimental (Ata 2)

- **Evidências:** PRs `#74–#80`, `#82`, `#84`, `#87`, `#88` e [Ata 2](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/docs/docs/atas-reuniao/ata-reuniao-2.md); PR `#81` (`feat/pesquisa-hibrida-admin`, mesclado em 13/11/2026 em `1723a7d`).
- **O que mudou:**
  - Integração das camadas de persistência MongoDB, contrato único de dados (`#19`, fechado em 11/11), autenticação administrativa (`/auth/login`, `/auth/logout`, `/datasets`, `/coletas`), análise via `POST /analises` e consultas paginadas/filtradas (`GET /analises`, `GET /analises/resumo`).
  - Surgimento de requisito emergente da Daily (Ata 2): **Pesquisa por assunto** (`src/servico/pesquisa.py`) combinando busca lexical em memória na base já carregada e complemento opcional pago via `XFetch` (complemento documentado em [`docs/pesquisa_hibrida_mongodb_xfetch.md`](../pesquisa_hibrida_mongodb_xfetch.md)).
- **Desvio de governança observado:** o PR `#81` indicava explicitamente *"Não mesclar ainda"* no corpo pela falta de issue dedicada, definição de limite de gasto no XFetch e aceite da PO, porém foi mesclado em `1723a7d` antes dessas validações (detalhado em [`GESTAO_CONFIGURACAO.md`](GESTAO_CONFIGURACAO.md) e [`REGISTRO_PRE_INSPECAO.md`](../inspecao/REGISTRO_PRE_INSPECAO.md)).

### Replanejamento 4 — 12/11 a 14/11/2026: Reavaliação BPSAD por classe e Preparação da Inspeção

- **Evidências:** issues `#85` e `#86` (12/11/2026), PR `#89` aberto em 14/11/2026, e abertura dos PRs de preparação à inspeção (`#90`, `#91` e esta frente de gestão/documentação).
- **O que mudou:**
  - Reconhecimento formal de que o desempenho por classe e a mudança de domínio (**TweetSentBR** → **BPSAD**) precisam de evidência reprodutível (`#85` / PR `#89`, ainda aberto com `67,70%` de acurácia e `0,5543` F1-macro reportados pelo autor para BERTweet em amostra de 10k textos, abaixo dos `~80%` de `RNF01`).
  - Organização do pacote de evidências auditáveis antes da entrega ao grupo inspetor (**LAMPORT**), separando rigorosamente o que está integrado em `1723a7d`, o que opera apenas em memória/mock e o que depende de deliberação da PO.

---

## 4. Reconciliação de Inconsistências do Planejamento na Visão v1.0.0

A análise direta do PDF *Visão v1.0.0* (30/09/2026) e do *Documento de Arquitetura v1.0.0* (07/10/2026), cruzada com os apontamentos da avaliação docente, confirma as inconsistências estruturais abaixo, que devem permanecer rastreadas até a publicação da nova versão (`#86`):

| Origem no PDF v1.0.0 | Divergência Encontrada | Origem do Apontamento | Encaminhamento Recomendado |
| --- | --- | --- | --- |
| **Cenário C01** (p. 23) vs. **Backlog RF01/RF02** (pp. 25, 29–30) | `C01` (*Aquisição dos dados*) está associado à **Sprint 2** na Seção 4.3, mas `RF01` e `RF02` estão alocados na **Sprint 1** no Backlog (Tabela 4.4 / Tabela 2.3.1). | Feedback docente no PDF (p. 2) + auditoria | Alinhar `C01` à **Sprint 1** (ou explicitar extensão pela UI na Sprint 5–6 com US22/US23). |
| **Cenário C04** (p. 23) vs. **Backlog RF08/RF09** | `C04` (*Persistência e disponibilização*) aponta **Sprint 3**, enquanto `RF08` e `RF09` pertencem à **Sprint 4**. | Auditoria direta Visão v1.0.0 | Corrigir `C04` para **Sprint 4** na nova edição da Visão. |
| **Cenários C05 e C06** (p. 23) vs. **Backlog RF10–RF16** | `C05` (*Consulta/filtragem*) e `C06` (*Visualização*) apontam **Sprint 4**, mas `RF10–RF12` pertencem à **Sprint 5** e `RF13–RF16` à **Sprint 6**. | Feedback docente (p. 2) + auditoria | Atualizar `C05 → Sprint 5` e `C06 → Sprint 6`. |
| **Código de requisito da US18** (p. 27 vs. p. 39) | Na tabela de Backlog (p. 27), a US18 de responsividade aparece como `C06/RF02` (colidindo com Coleta `RF02`); no roteiro T18 (p. 39), aparece como `C06/RNF02`. | Auditoria cruzada (QA + Acadêmica) | Ratificar **`C06/RNF02`** com a PO e corrigir o backlog na `#86`. |
| **Ordem T01 vs. T02** (pp. 35–36) | `T01` valida coleta (`RF02/US02`) e `T02` valida importação CSV (`RF01/US01`), invertendo a numeração de RF01/RF02. | Matriz QA (`sol-medium`) | Preservar mapeamento explícito por ID sem inferir pela ordem numérica. |
| **T04–T07** (p. 36) e **RNF01 / T08** (p. 37) | T04–T07 ainda testam remoção de *stopwords*, *stemming* e TF-IDF (contrários ao BERTweet), e T08 mistura teste unitário de predição com pré-condição `.pkl` e acurácia global. | Feedback docente (p. 33) + `ADR-001` | Separar T08 (unidade/contrato de predição) de avaliação empírica `RNF01`; atualizar T04–T07 após aceite de `#86`. |
| **GQM e Usabilidade** (pp. 28–32) | Feedback docente pediu métrica específica para **O2 Q4** (cobertura de testes) e **O3 Q2** (concordância de usuário/sistema), além de justificativa explícita para limiares `~80%`, `20%` e `85%`. | Feedback docente no PDF (p. 28) | Conferir reconciliação proposta pela frente de métricas (`docs/metricas/PLANO_GQM_VIGENTE.md` no PR `#91`). |
| **Visão v1.0.0 — Escopo de fontes e temas** | Feedback docente (pp. 1–2) cobrou explicitar de quais redes/fontes vêm os dados, separar dados de treino/avaliação dos analisados e definir quem escolhe os temas. | Feedback docente + Ata 1/Ata 2 | Incorporar na Visão revisada: TweetSentBR/BPSAD (avaliação/referência) vs. CSV/XFetch/Pesquisa (operação) e escolha de assunto pelo Administrador. |
| **Arquitetura v1.0.0 — Apêndice A e Paginação** | O texto cita o *Apêndice A* (PEP 8, commits, ferramentas) na p. 16, mas o PDF termina na p. 29 na Bibliografia sem o apêndice; o sumário aponta página 30 para bibliografia em um PDF de 29 páginas. | Auditoria direta Arquitetura v1.0.0 | Incluir política real de commits/estilo na seção de GC e regenerar sumário ao publicar revisão (`#86`). |
| **Referências ABNT Visão v1.0.0** (pp. 40–41) | `SCHWABER; SUTHERLAND (2020)`, `BECK (2000)`, `SOMMERVILLE (2019)` e `KREKEL et al. (2004)` estão na bibliografia sem citação no corpo; `COHN (2005)` está citado na p. 28 mas ausente na bibliografia; `BRAND24`, `BRANDWATCH` e `SPRINKLR` trazem `Acesso em: __ 2026`. | Auditoria direta Visão v1.0.0 + `sol-high` | Corrigir citação ida e volta, preencher datas reais de acesso e revisar com apoio de `REVISAO_ABNT.md` (PR `#90`). |
| **Divergência `docs/` vs. `developer` vs. `main`** | `origin/main` permanece congelada em `02/11` (`c72faeb`); `origin/developer` acumula toda a evolução técnica; `origin/docs` mantém apenas MkDocs inicial (Início, Atas 1–2 e Instruções). | Inspeção Git (14/11) | Sincronizar documentação de gestão/inspeção em `developer`, atualizar portal `docs` separadamente e planejar promoção controlada para `main` na Sprint 7. |
