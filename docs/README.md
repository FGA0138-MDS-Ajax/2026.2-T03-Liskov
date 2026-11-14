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

### Entregas paralelas em revisão (PRs abertos na `developer`)

- **Revisão Acadêmica e ABNT ([PR `#90`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90), `inspecao/sol-high`):** rascunhos rastreáveis de Visão e Arquitetura, matriz de divergências, revisão ABNT e decisões PO em [`docs/revisao-academica/`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/inspecao/sol-high/docs/revisao-academica) *(a integrar em `docs/revisao-academica/`)*.
- **Métricas GQM e QA / Testes ([PR `#91`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91), `inspecao/sol-medium`):** plano GQM vigente, medições e análises, plano de testes atual, matriz `T01–T18`, relatório de execução em `1723a7d` e registro de defeitos em [`docs/metricas/`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/inspecao/sol-medium/docs/metricas) e [`docs/qa/inspecao/`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/inspecao/sol-medium/docs/qa/inspecao) *(a integrar após merge do `#91`)*.

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
