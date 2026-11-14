# SentIA — Análise de Sentimentos

O **SentIA** é uma plataforma web de análise de sentimentos em português desenvolvida pelo grupo **Liskov — Turma 03**, na disciplina de **Métodos de Desenvolvimento de Software (MDS)** da Universidade de Brasília — Faculdade do Gama (2026.2).

O projeto classifica textos de acordo com sua polaridade (`positivo`, `negativo`, `neutro`) e consolida métricas em painel web, seguindo o recorte da **Sprint 5 / preparação para inspeção cruzada (`LAMPORT → LISKOV`)** em `14/11/2026` sobre a branch [`developer`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/developer).

## Estado do produto no corte de 14/11/2026

- **Implementado e integrado (`developer` @ `1723a7d`):** importação CSV (`csv_importer.py`), adaptadores TweetSentBR/BPSAD, cliente XFetch (`xfetch.py`), pipeline em lote com preservação do texto original para `pysentimiento/bertweet-pt-sentiment` (proposta `ADR-001`) + baseline TF-IDF isolado (`baseline.py`), persistência/leitura e agregação MongoDB (`repositorio.py`, `leitura.py`), API FastAPI (`GET /health`, `POST /analises`, `GET /analises`, `GET /analises/resumo` e rotas administrativas autenticadas `/auth/login`, `/auth/logout`, `/datasets`, `/coletas*`) e painel Streamlit com clientes HTTP e modo offline (`mock`).
- **Em modo simulado, memória ou caráter experimental:** o dashboard inicia por padrão com `SENTIA_FONTE_DADOS=mock` (17 registros fictícios); sessões, datasets importados pelo painel, jobs de coleta e a pesquisa híbrida lexical (`pesquisa.py`, PR `#81`) operam na memória do processo e aguardam ratificação da Product Owner (PO).
- **Pendências das Sprints 5–7:** reprodução da avaliação BPSAD por classe (`#85` / PR `#89` aberto), listagem, gráficos de distribuição e resumo narrativo no dashboard (`#27–#30`, `#32`, `#61`), teste de usabilidade (`#63`), implantação web (`#62`) e publicação das versões revisadas dos documentos acadêmicos (`#86`).

## Tecnologias atuais

- **Linguagem e gerenciador de ambiente:** Python 3.11 + `uv` (`pyproject.toml` / `uv.lock`)
- **Backend e persistência:** FastAPI, Uvicorn, PyMongo, MongoDB (`mongo:7` na CI)
- **Painel:** Streamlit
- **Processamento / ML:** `pysentimiento` (`bertweet-pt-sentiment`), `torch`, `scikit-learn` + `NLTK` (experimentos/baseline)
- **Qualidade e entrega:** `pytest`, `pytest-cov`, `ruff`, GitHub Actions e MkDocs Material

## Arquitetura implementada

`src/apresentacao` (Streamlit) → `src/servico` (FastAPI) → `src/processamento` (Aquisição, Pipeline e Classificação) → `src/dados` & `src/persistencia` (MongoDB / memória)

*(Ver detalhes em [Arquitetura (`developer`)](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/arquitetura.md) e [Contrato único de dados](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/contratos-dados.md).)*

## Documentação na `developer` e PRs de Inspeção

Este portal na branch `docs` concentra as **Atas de Reunião** e o resumo institucional. Os documentos vivos de engenharia, gestão e preparação para inspeção estão versionados na branch **`developer`** e nos seguintes Pull Requests em revisão:

- **Portal de entrada e comandos:** [`README.md` (`developer`)](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/README.md) · [`docs/README.md` (`developer`)](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/developer/docs/README.md)
- **Dossiê de Inspeção, Gestão e Roteiro ([PR `#92`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/92), `chore/inspecao-argon`):** [`docs/inspecao/README.md`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/chore/inspecao-argon/docs/inspecao/README.md) · [`ROTEIRO_INSPECAO.md`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/chore/inspecao-argon/docs/inspecao/ROTEIRO_INSPECAO.md) · [`MATRIZ_EVIDENCIAS.md`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/chore/inspecao-argon/docs/inspecao/MATRIZ_EVIDENCIAS.md) · [`PLANEJAMENTO_E_REPLANEJAMENTOS.md`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/chore/inspecao-argon/docs/gestao/PLANEJAMENTO_E_REPLANEJAMENTOS.md) · [`GESTAO_CONFIGURACAO.md`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/chore/inspecao-argon/docs/gestao/GESTAO_CONFIGURACAO.md)
- **Revisão Acadêmica e ABNT ([PR `#90`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90), `inspecao/sol-high`):** rascunhos de Visão, Arquitetura, matriz de divergências e decisões pendentes da PO.
- **Métricas GQM e QA / Testes ([PR `#91`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91), `inspecao/sol-medium`):** plano GQM vigente, medições e análises, plano de testes atual e matriz `T01–T18`.
- **Registros locais deste portal:** [Ata de Reunião 1](atas-reuniao/ata-reuniao-1.md) · [Ata de Reunião 2](atas-reuniao/ata-reuniao-2.md)

## Equipe

Projeto desenvolvido pelo grupo **Liskov — T03**, na disciplina de Métodos de Desenvolvimento de Software (UnB/FGA).
