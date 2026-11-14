# Dossiê de Inspeção Cruzada — SentIA (Grupo Liskov, T03)

- **Disciplina:** Métodos de Desenvolvimento de Software (MDS) — UnB/FGA, 2026.2
- **Mapeamento de inspeção:** **LAMPORT inspeciona LISKOV** (`LISKOV` inspeciona `PERLMAN`)
- **Linha de base técnica (`developer`):** [`1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920) (`13/11/2026`)
- **Status de CI na linha de base:** **`SUCCESS`** — workflow `CI`, execução [`43503741871`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871) / job [`132155891920`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920) com serviço `mongo:7` (**814 testes aprovados, 0 ignorados, 93% de cobertura**, segundo relatório QA).

Este diretório é o ponto de entrada único para preparar, auditar e conduzir a **inspeção do grupo Liskov pelo grupo Lamport**, consolidando rastreabilidade documental, evidências de gestão, métricas, qualidade e pendências em aberto sem ocultar desvios nem fabricar métricas inexistentes.

---

## 1. Mapa do Dossiê de Inspeção e Gestão (esta frente)

| Documento | Finalidade na Inspeção | Cobertura Principal |
| --- | --- | --- |
| [**`ROTEIRO_INSPECAO.md`**](ROTEIRO_INSPECAO.md) | Guia passo a passo para a apresentação/auditoria pelo grupo **LAMPORT** | Matriz `critério → evidência → responsável → pendência → link`, demonstração técnica de 5–10 min e consolidação dos PRs |
| [**`REGISTRO_PRE_INSPECAO.md`**](REGISTRO_PRE_INSPECAO.md) | Inventário auditável pré-inspeção em 14/11/2026 | Branches, PRs (`#15–#91`), Issues (`#1–#86`), proteção de branches, caso do PR `#81` e política de privacidade dos PDFs originais |
| [**`MATRIZ_EVIDENCIAS.md`**](MATRIZ_EVIDENCIAS.md) | Mapeamento item a item do *Formulário de Inspeção* (sem atribuir notas próprias) | Seções 3.1 (Quadro 5 ABNT), 3.2 (Planejamento), 3.3 (Quadro 5 GC), 3.4 (Quadro 6 Métricas), 3.5 (Testes), Quadro 7 (Visão), Quadro 8 (Arquitetura) |
| [**`PLANO_REGULARIZACAO.md`**](PLANO_REGULARIZACAO.md) | Coordenação de entregas e pendências pós-inspeção | Integração entre as 3 frentes documentais, lista `PO-01` a `PO-14` para decisão da PO e ordem de revisão/merge |
| [**`../gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md`**](../gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md) | Evidências de Planejamento (30%) | Sprints 1–7 (Visão v1.0.0 vs. execução), DoD, 4 eventos de replanejamento, reconciliação `C01–C06` / backlog e justificativa de `SP = N/D` |
| [**`../gestao/GESTAO_CONFIGURACAO.md`**](../gestao/GESTAO_CONFIGURACAO.md) | Evidências de Gestão de Configuração (10%) | Catálogo IC-01 a IC-09, política de branches (`main`/`developer`/`docs`/`gh-pages`), 92,6% Conventional Commits, análise de revisões e desvio `#81` |

---

## 2. Frentes Paralelas de Inspeção (PRs Abertos Relacionados)

Para evitar conflitos de arquivo, o levantamento técnico completo foi dividido em três áreas independentes. Os artefatos das duas frentes irmãs encontram-se abertos para revisão na `developer`:

| Frente / PR | Conteúdo Entregue | Destino pós-merge |
| --- | --- | --- |
| **Revisão Acadêmica e ABNT** — [PR `#90`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90) (`inspecao/sol-high`) | Propostas rastreáveis de atualização da [Visão](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-high/docs/revisao-academica/VISAO_ATUALIZADA_RASCUNHO.md) e [Arquitetura](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-high/docs/revisao-academica/ARQUITETURA_ATUALIZADA_RASCUNHO.md), [matriz de divergências](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-high/docs/revisao-academica/MATRIZ_DIVERGENCIAS.md), [revisão ABNT](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-high/docs/revisao-academica/REVISAO_ABNT.md) e [decisões PO](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-high/docs/revisao-academica/DECISOES_PENDENTES_PO.md) | `docs/revisao-academica/` |
| **Métricas GQM e QA / Testes** — [PR `#91`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91) (`inspecao/sol-medium`) | [Plano GQM vigente](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-medium/docs/metricas/PLANO_GQM_VIGENTE.md), [registro/análise de medições](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-medium/docs/metricas/REGISTRO_E_ANALISE.md), [plano de testes atual](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-medium/docs/qa/inspecao/PLANO_TESTES_ATUAL.md), [matriz T01–T18](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-medium/docs/qa/inspecao/MATRIZ_RASTREABILIDADE.md), [relatório de execução](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-medium/docs/qa/inspecao/RELATORIO_EXECUCAO.md) e [defeitos/correções](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/inspecao/sol-medium/docs/qa/inspecao/DEFEITOS_E_CORRECOES.md) | `docs/metricas/` e `docs/qa/inspecao/` |
| **Experimento BPSAD em avaliação** — [PR `#89`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89) (`feat/issue-85-avaliacao-bertweet`) | Execução declarada para issue `#85` (métricas por classe do BERTweet no BPSAD); **não integrado em `1723a7d`** e ainda não reproduzido neste ambiente | `scripts/experimentos/` e `docs/experimentos_bpsad.md` |
| **Walkthrough anterior de testes** — [PR `#83`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/83) (`docs-qa-walkthrough-testes`) | Registro técnico pré-`#84`/`#81` (`11/11/2026`, baseado em `fe83ad0` com 707 testes); **superado por PR `#91`** para fins de inspeção | Avaliar fechamento ou atualização |

---

## 3. Documentação Técnica Vigente e Arquivo Histórico

### Documentação técnica de referência (em `origin/developer`)

- [Arquitetura técnica e fluxo em camadas](../arquitetura.md)
- [Contrato único de dados entre frentes (`#19`)](../contratos-dados.md) e [Contrato HTTP painel ↔ API](../frontend/CONTRATO-API.md)
- [Esquema lógico MongoDB](../banco/esquema-mongodb.md), [Guia de setup MongoDB](../mongodb_setup.md) e [Alterações de armazenamento em memória](../alteracoes_armazenamento_memoria.md)
- [Classificação (BERTweet e baseline)](../classificacao.md), [ADR-001 (proposta de preservação de stopwords)](../decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md) e [Experimentos BPSAD](../experimentos_bpsad.md)
- [TweetSentBR](../tweetsentbr.md), [BPSAD](../bpsad.md), [Integração XFetch](../integracao_xfetch.md) e [Proposta de pesquisa híbrida](../pesquisa_hibrida_mongodb_xfetch.md)
- [Guia do painel Streamlit](../frontend/README.md) e [Wireframes](../frontend/WIREFRAMES.md)

### Registros históricos (não confundir com o estado em `1723a7d`)

- **Ponto de Controle 1 (09/11/2026):** [`docs/qa/pc1/STATUS_FINAL.md`](../qa/pc1/STATUS_FINAL.md), [`ROTEIRO_DEMONSTRACAO.md`](../qa/pc1/ROTEIRO_DEMONSTRACAO.md), [`MATRIZ_RASTREABILIDADE.md`](../qa/pc1/MATRIZ_RASTREABILIDADE.md) e [`VALIDACAO_FRONTEND_CLICIA.md`](../qa/pc1/VALIDACAO_FRONTEND_CLICIA.md) registram a foto de 09/11/2026 (538 testes offline).
- **Portal MkDocs (`docs` / `gh-pages`):** mantém atas de reunião ([Ata 1](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/docs/docs/atas-reuniao/ata-reuniao-1.md) e [Ata 2](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/docs/docs/atas-reuniao/ata-reuniao-2.md)) e página inicial estática; atualização encaminhada em PR separado para a branch `docs`.

---

## 4. Transparência Rápida para o Inspetor (Real vs. Simulado vs. Pendente)

- **Implementado na API (`src/servico/`):** `GET /health`, `POST /analises` (sem exigir login admin), `GET /analises`, `GET /analises/resumo`, além das rotas administrativas protegidas por token `Bearer` (`/auth/login`, `/auth/logout`, `/datasets`, `/coletas/fontes`, `/coletas`, `/coletas/{id_coleta}`).
- **Persistência em MongoDB vs. Memória:** `POST /analises`, `GET /analises` e `GET /analises/resumo` usam MongoDB por padrão (`SENTIA_ARMAZENAMENTO=mongodb`, testado com `mongo:7` no CI). Em contrapartida, **sessões, datasets importados, histórico de coletas e índice lexical da pesquisa (`src/servico/administracao.py` + `src/servico/pesquisa.py`) ainda residem na memória do processo**.
- **Limitação explícita do Dashboard (`src/apresentacao/paginas/dashboard.py`):** no corte `1723a7d`, o dashboard exibe filtros, indicadores numéricos e avisos de erro/vazio, mas **ainda não renderiza** listagem paginada de análises, gráfico de distribuição nem resumo narrativo (previstos para a Sprint 6, `#27–#30`).
- **O que não deve ser tratado como concluído:** `ADR-001` e `pesquisa.py` (PR `#81`, mesclado sem revisão formal e com pendência de teto de custo XFetch) aguardam ratificação da PO; os resultados BPSAD do PR `#89` aguardam reprodução e deliberação sobre `RNF01 (~80%)`.
