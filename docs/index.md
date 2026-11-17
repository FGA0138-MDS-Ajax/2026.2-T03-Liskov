# SentIA — Análise de Sentimentos

O **SentIA** é uma plataforma web de análise de sentimentos em português desenvolvida pelo grupo **Liskov — Turma 03**, na disciplina de **Métodos de Desenvolvimento de Software (MDS)** da Universidade de Brasília — Faculdade do Gama.

O sistema classifica textos em três polaridades — `positivo`, `negativo` e `neutro` — e oferece aquisição de dados, processamento, persistência e consulta por API REST e painel web.

**Referência técnica desta página:** branch `developer`, commit `b91c7a5e4af972d98da6e5ded70b2243d60f5513`, após o merge do PR #96 (15/11/2026). Os documentos de inspeção, gestão, revisão acadêmica, métricas e QA estão mantidos na branch `developer`; este portal e as atas são mantidos na branch `docs`.

## Documentos do projeto

Os Documentos de Visão e de Arquitetura, na versão inicial (1.0.0) e na atualizada (1.1.0), estão em [Documentos do projeto](documentos.md). A documentação técnica do código está na [pasta `docs` do repositório](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/main/docs).

## Estado do produto no corte de 15/11/2026

### Implementado na branch `developer`

- Importação CSV, adaptadores TweetSentBR/BPSAD e auditoria de datasets.
- Aquisição opcional paginada por XFetch, mediante configuração.
- Pipeline de classificação em lote, classificador `pysentimiento/bertweet-pt-sentiment` e baseline experimental TF-IDF + Regressão Logística.
- Persistência e consulta MongoDB de análises, registros, datasets/corpus e cache de pesquisas, centralizadas em `src/dados/database.py` e `src/dados/repositorio.py` após o PR #96.
- API FastAPI com `/health`, `/analises`, `/analises/resumo` e rotas administrativas para autenticação, datasets e coletas.
- Painel Streamlit com Dashboard e Administração, clientes HTTP e modo offline mock.

### Limites e pendências

- O modo padrão do painel pode ser `mock`; os 17 registros de demonstração são fictícios e não devem ser confundidos com dados reais.
- Sessões administrativas e estados transitórios de jobs de coleta são mantidos na memória do processo; os dados funcionais de datasets, registros, análises e pesquisas são persistidos no MongoDB.
- A pesquisa por assunto existente é lexical e não equivale a busca vetorial/embeddings.
- A avaliação BPSAD, visualização completa do dashboard, validação de usabilidade, publicação web e decisões formais da Product Owner permanecem sujeitas aos respectivos registros de planejamento/aceite. Consulte as issues e relatórios atuais antes de declarar qualquer item concluído.

## Arquitetura implementada

```text
Usuário
  ↓
Apresentação — Streamlit (src/apresentacao)
  ↓ HTTP/JSON
Serviço — FastAPI (src/servico)
  ↓
Processamento — Aquisição + Pipeline + Classificação (src/processamento)
  ↓
Dados — MongoDB / PyMongo (src/dados)
```

A API pertence à camada `servico`. A persistência está centralizada em `src/dados/`; não há um pacote `src/persistencia/` na revisão técnica citada.

Consulte a [arquitetura técnica](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/metricas/arquitetura.md) e o [contrato único de dados](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/contratos-dados.md).

## Tecnologias

- **Linguagem e ambiente:** Python 3.11+ e `uv`.
- **Painel:** Streamlit.
- **API:** FastAPI e Uvicorn.
- **Banco:** MongoDB e PyMongo.
- **Processamento:** pandas, NLTK e scikit-learn.
- **Classificação:** PySentimiento e PyTorch para o classificador BERTweet.
- **Qualidade:** Pytest, pytest-cov, Ruff e GitHub Actions.
- **Documentação:** MkDocs Material.

## Documentação consolidada na branch `developer`

O portal mantém as atas de reunião e o guia de publicação. A documentação técnica e os registros de engenharia são mantidos na branch `developer`:

| Área | Documentos principais |
|---|---|
| Documentos de Visão e de Arquitetura | [Versões 1.0.0 e 1.1.0](documentos.md), [pasta `docs` do repositório](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/main/docs) |
| Entrada e arquitetura | [README do projeto](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/README.md), [índice técnico](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/README.md), [arquitetura](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/metricas/arquitetura.md) |
| Desenvolvimento e contratos | [Contrato de dados](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/contratos-dados.md), [contrato API ↔ painel](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/frontend/CONTRATO-API.md), [guia do painel](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/frontend/README.md) |
| Inspeção e gestão | [Dossiê de inspeção](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/inspecao/README.md), [plano de regularização](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/inspecao/PLANO_REGULARIZACAO.md), [planejamento](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md) |
| Revisão acadêmica | [Matriz de divergências](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/revisao-academica/MATRIZ_DIVERGENCIAS.md), [decisões pendentes da PO](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/revisao-academica/DECISOES_PENDENTES_PO.md) |
| Métricas e QA | [Plano GQM](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/metricas/PLANO_GQM_VIGENTE.md), [plano de testes](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/qa/inspecao/PLANO_TESTES_ATUAL.md), [relatório de execução](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/qa/inspecao/RELATORIO_EXECUCAO.md) |
| Aquisição e ML | [TweetSentBR](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/tweetsentbr.md), [BPSAD](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/bpsad.md), [XFetch](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/integracao_xfetch.md), [classificação](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/classificacao.md) |

## Histórico do portal

O [PR #93 — Portal MkDocs](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/93) foi integrado à branch `docs`. A branch `docs` possui um workflow próprio para publicar o portal em `gh-pages`; ela não deve ser mesclada integralmente em `developer` sem reconciliar o arquivo `.github/workflows/ci.yml`, que tem finalidades diferentes nas duas branches.

## Equipe

Projeto desenvolvido pelo grupo **Liskov — T03**, na disciplina MDS, UnB/FGA.
