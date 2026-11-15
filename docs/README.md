# Documentação do SentIA

Índice consolidado da documentação técnica, gerencial, acadêmica e de qualidade (QA) do projeto **SentIA** (Grupo **Liskov — T03**, MDS — UnB/FGA, 2026.2) na linha de base `origin/developer` @ `1723a7d` (**14/11/2026**). Para instalação e comandos de execução, consulte o [`README.md`](../README.md).

---

## Inspeção Cruzada (LAMPORT → LISKOV) e Gestão

- [Dossiê de Inspeção — Ponto de entrada](inspecao/README.md)
- [Roteiro da Inspeção e Demonstração Técnica](inspecao/ROTEIRO_INSPECAO.md)
- [Matriz de Evidências por Critério do Formulário](inspecao/MATRIZ_EVIDENCIAS.md)
- [Registro de Pré-Inspeção (Branches, PRs, Issues, Caso #81 e LGPD)](inspecao/REGISTRO_PRE_INSPECAO.md)
- [Plano de Regularização e Decisões Pendentes da PO](inspecao/PLANO_REGULARIZACAO.md)
- [Planejamento, Acompanhamento de Sprints e Replanejamentos](gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md)
- [Gestão de Configuração e Auditoria de Governança](gestao/GESTAO_CONFIGURACAO.md)

### Frentes de inspeção integradas na `developer` e portal MkDocs

- **Revisão Acadêmica e ABNT (integrada — [PR `#90`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90), `inspecao/sol-high`):** rascunhos rastreáveis de [Visão](revisao-academica/VISAO_ATUALIZADA_RASCUNHO.md) e [Arquitetura](revisao-academica/ARQUITETURA_ATUALIZADA_RASCUNHO.md), [matriz de divergências](revisao-academica/MATRIZ_DIVERGENCIAS.md), [revisão ABNT](revisao-academica/REVISAO_ABNT.md), [decisões PO](revisao-academica/DECISOES_PENDENTES_PO.md) e [relatório da frente](revisao-academica/RELATORIO_ENTREGA.md) *(ver conciliação em [`PLANO_REGULARIZACAO.md`](inspecao/PLANO_REGULARIZACAO.md))*.
- **Métricas GQM e QA / Testes (integrada — [PR `#91`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91) e [PR `#94`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/94)):** [plano GQM vigente](metricas/PLANO_GQM_VIGENTE.md) *(atualizado pelo PR `#94` com a Mini-tarefa GQM)*, [medições e análises](metricas/REGISTRO_E_ANALISE.md), [plano de testes atual](qa/inspecao/PLANO_TESTES_ATUAL.md), [matriz `T01–T18`](qa/inspecao/MATRIZ_RASTREABILIDADE.md), [relatório de execução em `1723a7d`](qa/inspecao/RELATORIO_EXECUCAO.md) e [registro de defeitos](qa/inspecao/DEFEITOS_E_CORRECOES.md).
- **Orquestração, Gestão e Dossiê (integrada — [PR `#92`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/92), `chore/inspecao-argon`):** documentos em [`docs/inspecao/`](inspecao/README.md), [`docs/gestao/`](gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md) e [`README.md`](../README.md), consolidados pós-merge na `developer`.
- **Portal MkDocs ([PR `#93`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/93), `chore/inspecao-mkdocs` → `docs`, aberto):** atualização da navegação e página inicial do portal com links canônicos pós-merge apontando para `developer`.

---

## Arquitetura, Decisões e Contratos

- [Arquitetura observada no código](arquitetura.md)
- [ADR-001 — Preservação de stopwords no BERTweet (proposta técnica)](decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md)
- [Contrato único de dados (Aquisição, Pipeline ML, MongoDB, API e Painel — `#19`)](contratos-dados.md)
- [Contrato HTTP entre o painel e a API](frontend/CONTRATO-API.md)

## Frontend (Streamlit)

- [Guia do módulo de apresentação](frontend/README.md)
- [Wireframes e estado dos componentes](frontend/WIREFRAMES.md)

## Aquisição de Dados

- [TweetSentBR: aquisição, auditoria e governança](tweetsentbr.md)
- [BPSAD: adaptador e mapeamento de avaliações](bpsad.md)
- [XFetch: módulo de coleta paginada (PR `#65`)](integracao_xfetch.md)
- [Proposta de pesquisa híbrida MongoDB + XFetch (busca semântica futura)](pesquisa_hibrida_mongodb_xfetch.md)

## Processamento e Machine Learning

- [Classificador BERTweet, baseline TF-IDF e pipeline](classificacao.md)
- [Experimentos exploratórios BPSAD (PR `#64`; reavaliação por classe em aberto no PR `#89`)](experimentos_bpsad.md)
- [Relatório de homologação dos PRs #44 e #45](qa/pr44-pr45/relatorio.md)

## Banco de Dados e Persistência

- [Configuração e validação de conexão com PyMongo](mongodb_setup.md)
- [Esquema lógico da coleção `analises`](banco/esquema-mongodb.md)
- [Alterações e limites do armazenamento em memória](alteracoes_armazenamento_memoria.md)
- Exemplos de documentos: [mínimo](banco/exemplos/analise-minima.json), [completo](banco/exemplos/analise-completa.json), [baseline](banco/exemplos/analise-baseline.json), [TweetSentBR](banco/exemplos/analise-tweetsentbr.json) e [inválidos](banco/exemplos/analises-invalidas.json)

## Marcos Históricos e Portal Acadêmico

- **Ponto de Controle 1 (09/11/2026 — arquivo histórico):**
  - [Roteiro de demonstração do PC1](qa/pc1/ROTEIRO_DEMONSTRACAO.md)
  - [Status final do PC1 e resultados daquela data](qa/pc1/STATUS_FINAL.md)
  - [Matriz de rastreabilidade do PC1](qa/pc1/MATRIZ_RASTREABILIDADE.md)
  - [Validação do frontend no PC1 (PR #70 + PR #71)](qa/pc1/VALIDACAO_FRONTEND_CLICIA.md)
- **Suíte de testes e metadados gerais:**
  - [Guia da suíte de testes](../tests/README.md)
  - [Branch `docs` (MkDocs e Atas de Reunião)](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/docs)
  - [Changelog do projeto](../CHANGELOG.md)
