# Plano de Regularização, Consolidação e Decisões Pendentes — SentIA

- **Data:** 14/11/2026
- **Linha de base (`developer`):** `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`
- **Finalidade:** Coordenar a consolidação sem conflitos das três frentes de preparação para a inspeção (**LAMPORT → LISKOV**), registrar a pauta completa de decisões pendentes da Product Owner (PO) sem presumir aceite e definir o roteiro de regularização até a Sprint 7.

---

## 1. Consolidação entre Frentes (Sem Sobreposição de Arquivos)

A regularização pré-inspeção foi organizada em três entregas complementares para `developer` e uma entrega específica para o portal MkDocs (`docs`):

| Frente | Branch / PR | Arquivos sob Responsabilidade | Sobreposição / Conflito |
| --- | --- | --- | --- |
| **Frente 1 — Revisão Acadêmica e ABNT** | `inspecao/sol-high` ([PR `#90`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90), CI `SUCCESS`) | `docs/revisao-academica/` (`VISAO_ATUALIZADA_RASCUNHO.md`, `ARQUITETURA_ATUALIZADA_RASCUNHO.md`, `MATRIZ_DIVERGENCIAS.md`, `REVISAO_ABNT.md`, `DECISOES_PENDENTES_PO.md`, `RELATORIO_ENTREGA.md`) | **Zero conflito** com as demais frentes |
| **Frente 2 — Métricas GQM e QA / Testes** | `inspecao/sol-medium` ([PR `#91`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91)) | `docs/metricas/` (`PLANO_GQM_VIGENTE.md`, `REGISTRO_E_ANALISE.md`) e `docs/qa/inspecao/` (`PLANO_TESTES_ATUAL.md`, `MATRIZ_RASTREABILIDADE.md`, `RELATORIO_EXECUCAO.md`, `DEFEITOS_E_CORRECOES.md`, `evidencias/*`) | **Zero conflito** com as demais frentes |
| **Frente 3 — Orquestração, Gestão e Dossiê** | `chore/inspecao-argon` (PR para `developer`) | `README.md`, `docs/README.md`, `docs/gestao/` (`PLANEJAMENTO_E_REPLANEJAMENTOS.md`, `GESTAO_CONFIGURACAO.md`), `docs/inspecao/` (`README.md`, `REGISTRO_PRE_INSPECAO.md`, `MATRIZ_EVIDENCIAS.md`, `PLANO_REGULARIZACAO.md`, `ROTEIRO_INSPECAO.md`) | **Zero conflito** com PRs `#90` e `#91` |
| **Frente 4 — Portal MkDocs** | `chore/inspecao-mkdocs` (PR para `docs`) | `docs/index.md`, `mkdocs.yml` (preservando Atas 1 e 2 e workflow `gh-pages`) | Isolado na branch `docs` |

---

## 2. Pauta Consolidada de Decisões Pendentes da PO (`PO-01` a `PO-14`)

Nenhuma destas decisões foi presumida ou encerrada neste dossiê; todas exigem posicionamento formal da Product Owner (Héllen Clícia) e da equipe antes do fechamento da Sprint 7 e da promoção para `main`:

| ID | Tema / Origem | Evidência / Conflito Associado | Decisão Necessária da PO / Equipe |
| --- | --- | --- | --- |
| **PO-01** | **Estratégia BERTweet vs. pré-processamento clássico** (`RF03–RF06`, `#5–#8`, `#86`) | `ADR-001` proposto; Visão v1.0.0 ainda exige limpeza/*stopwords*/*stemming*/TF-IDF no fluxo principal | Ratificar formalmente o uso de `pysentimiento/bertweet-pt-sentiment` com texto bruto (mantendo `baseline.py` isolado) e aprovar a atualização de `RF03–RF06` e `T04–T07`. |
| **PO-02** | **Meta `RNF01 (~80%)` e avaliação por classe** (`#17`, `#85`, PR `#89`) | PR `#89` declara BERTweet em amostra 10k do BPSAD com acurácia `67,70%` e F1 macro `0,5543` (`0,2368` em neutro), abaixo de `~80%` | Reproduzir independentemente o PR `#89` e decidir se `RNF01` é recalibrada por classe/domínio, se há ajuste/seleção de modelo ou mudança de critério de aceite. |
| **PO-03** | **Separação de domínio (TweetSentBR vs. BPSAD)** (`#3`, `#85`, PR `#90`) | Modelo pré-treinado em tweets vs. avaliação em avaliações de e-commerce (`BPSAD`) | Definir formalmente na Visão qual corpus mede desempenho em redes sociais e qual mede robustez fora do domínio. |
| **PO-04** | **Licença e proveniência do TweetSentBR legado** (`#3`, `docs/tweetsentbr.md`) | `auditoria_datasets.py` valida hash/formato local, não licença jurídica | Definir origem/regras de redistribuição e bloquear qualquer subida de dados brutos sem permissão ao Git. |
| **PO-05** | **Pesquisa híbrida experimental (`PR #81`)** (`src/servico/pesquisa.py`) | Mesclada em `1723a7d` apesar de *"Não mesclar ainda"*; busca lexical em memória, sem Vector Search | Homologar se a aba **Pesquisar assunto** permanece no produto, definir critério mínimo de relevância e prazo para eventual busca semântica. |
| **PO-06** | **Orçamento e limite de chamadas pagas no XFetch** (`PR #81`, `#1`, `#61`) | Sem teto financeiro nem cota máxima por período configurada | Definir teto de gasto/consultas, responsável pela chave `XFETCH_API_KEY` e regra de fallback quando não configurada. |
| **PO-07** | **Autorização de escrita/leitura em `/analises`** (`src/servico/main.py`) | Rotas admin (`/auth/*`, `/datasets`, `/coletas`) exigem token; `POST /analises` e `GET /analises*` não exigem login | Decidir se `POST /analises` deve exigir autenticação de Administrador antes de implantação pública (`#62`). |
| **PO-08** | **Persistência administrativa em memória vs. MongoDB** (`src/servico/administracao.py`) | Sessões, datasets importados, histórico de coletas e base da pesquisa somem ao reiniciar | Definir se a persistência em MongoDB será estendida à administração na Sprint 6/7 ou se permanece em processo único apenas no escopo acadêmico. |
| **PO-09** | **Semântica temporal de `data_publicacao`** (`docs/contratos-dados.md`, `#24`) | Filtros `inicio`/`fim` usam `data_publicacao` UTC e excluem documentos sem data de origem | Ratificar que `data_publicacao` (e não `data_processamento`) é a referência oficial para recortes temporais no dashboard. |
| **PO-10** | **Código `C06/RNF02` vs. `C06/RF02` (US18) e teste visual `T18`** (`#31`) | Visão p. 27 traz `C06/RF02`; p. 39 traz `C06/RNF02`; `#31` foi fechada sem reexecução visual pós-PC1 | Ratificar o código `C06/RNF02`, definir larguras suportadas e agendar verificação visual atual em desktop/tablet/mobile. |
| **PO-11** | **Nuvem de palavras (`RF16 / US17`, `#30`)** | Prioridade `Could`, ainda não implementada; não pode alterar pré-processamento do BERTweet | Confirmar inclusão na Sprint 6 (se houver capacidade) ou adiamento formal. |
| **PO-12** | **Ajustes no GQM e protocolo de usabilidade (`#63`)** | Feedback docente em Visão p. 28 (O2 Q4 cobertura, O3 Q2 concordância, justificativa de `80%`/`20%`/`85%`) | Aprovar `PLANO_GQM_VIGENTE.md` (PR `#91`) e calendário de sessões de usabilidade na Sprint 7. |
| **PO-13** | **Conciliação de Sprints/Cenários e higiene de Issues** | Incoerências `C01/C04/C05/C06` vs. backlog; `#18, #20–#25, #58` abertas com código em `developer`; `#31, #57, #59` fechadas antes de validação completa | Reconciliar tabela cenários↔sprints↔backlog e padronizar encerramento das issues apenas após critério de pronto + aceite PO. |
| **PO-14** | **Publicação final acadêmica (`#86`) e promoção `developer → main`** | PDFs v1.0.0 possuem matrículas e notas docentes; `main` parada em `02/11` | Exportar novas versões Visão/Arquitetura sem dados sensíveis, definir `REQUIRED CHECKS` e `enforce_admins: true` e aprovar merge para `main`. |

---

## 3. Ordem Recomendada de Revisão e Merge (Sem Conflitos)

> [!IMPORTANT]
> Todos os PRs abaixo aguardam **revisão por par humano (`APPROVED`) diferente do autor** e verificação de CI verde antes de qualquer merge — **nenhum merge deve ser feito automaticamente**.

1. **Higiene prévia — PR [`#83`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/83) (`docs-qa-walkthrough-testes`):** decidir pelo fechamento como superado pelo PR `#91` (ou atualizar para `1723a7d`).
2. **PR [`#90`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90) (`inspecao/sol-high` → `developer`):** revisar com apoio da PO (`DECISOES_PENDENTES_PO.md` e minutas em `docs/revisao-academica/`) e aprovar merge.
3. **PR [`#91`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91) (`inspecao/sol-medium` → `developer`):** revisar plano GQM, matriz T01–T18 e relatório de execução/defeitos (`docs/metricas/` e `docs/qa/inspecao/`) e aprovar merge.
4. **PR de Orquestração e Dossiê (`chore/inspecao-argon` → `developer`):** revisar `README.md`, `docs/README.md`, `docs/gestao/*` e `docs/inspecao/*` e aprovar merge (sem conflitos com `#90` e `#91`). *(Opcional após os três merges: ajustar em um micro-PR os links externos das frentes em `docs/inspecao/README.md` e `MATRIZ_EVIDENCIAS.md` para links relativos dentro da `developer`.)*
5. **PR do Portal MkDocs (`chore/inspecao-mkdocs` → `docs`):** revisar `docs/index.md` e `mkdocs.yml`; após o merge, o workflow da branch `docs` atualizará o site publicado em `gh-pages`.
6. **Trilha técnica paralela — PR [`#89`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89) (`feat/issue-85-avaliacao-bertweet` → `developer`):** reproduzir em ambiente com `uv sync --locked --group ml --group experimentos`, registrar decisão **PO-02** sobre `RNF01` e só então decidir pelo merge ou ajuste de experimentos.

---

## 4. Plano de Reparos Pós-Inspeção (Sprints 6 e 7)

Após a realização da inspeção cruzada pela **LAMPORT**:
1. **Triagem dos defeitos apontados pela LAMPORT** (classificação C/A/M/B no Quadro 9) junto aos itens já mapeados em `DEFEITOS_E_CORRECOES.md` (PR `#91`) e neste documento.
2. **Entrega funcional restante da Sprint 6 (`17–23/11`):** implementar listagem paginada, gráficos de distribuição e resumo narrativo no dashboard (`#27`, `#28`, `#29`), integrar coleta UI (`#61`), decidir nuvem de palavras (`#30`) e executar testes integrados `T14–T18` (`#32`) com API + MongoDB + BERTweet reais (não apenas mocks).
3. **Finalização na Sprint 7 (`24–30/11`):** executar teste de usabilidade (`#63`), definir implantação pública segura (`#62` — incluindo proteção de rotas, segredos e decisão de persistência administrativa), publicar versões finais sem matrículas de *Visão* e *Arquitetura* (`#86`), endurecer regras de GC (`checks` obrigatórios e `enforce_admins: true`) e promover `developer → main`.
