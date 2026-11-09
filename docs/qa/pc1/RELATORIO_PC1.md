# Relatório PC1 — SentIA

Data: 09/11/2026. Base auditada: `c6fc53561055178085edcbc123fc86166edf89fa`
(`origin/developer`). As correções propostas estão em branches próprias; nenhuma
integração oficial foi realizada. Consulte o relatório final para SHAs e PRs novos.

## Git e estado das entregas

A cópia local da developer estava em `e2a3ff0`, 19 commits atrás da remota.
A main (`c72faeb`) é ancestral da developer, com 47 commits de diferença.
O diretório local não rastreado `docs/auditorias/` foi preservado integralmente.
PR #64: aberto, head `0e19b6b`, dois commits, três arquivos; sem revisão submetida.
PR #65: aberto, head `63f3ce5`, um commit, quatro arquivos; sem revisão submetida.
Ambos tinham check `test` verde na consulta inicial.

## Funcionalidades e limites

| Componente | Evidência e situação |
|---|---|
| Aquisição CSV/TweetSentBR/BPSAD | Implementada e testada com fixtures sintéticas |
| Pipeline | Classificação em lote, preservação de texto/IDs/fontes, rótulos e probabilidades; testes com analisador simulado |
| BERTweet | Adaptador existente e testado; nenhuma nova inferência real nesta auditoria, sem pesos no ambiente |
| MongoDB | Conexão explícita, tratamento seguro de erros e esquema; sem persistência de análises implementada |
| API | `/health` real responde 200 e `{"status":"ok"}`; análises, filtros e autenticação pendentes |
| Dashboard | Indicadores mock com aviso de dados fictícios, estados vazio/erro e navegação; administração é placeholder |
| Cliente HTTP do painel | Contrato proposto testado com mocks, ainda sem endpoints correspondentes na API |
| XFetch | PR #65; testes offline não comprovam serviço externo |
| Busca híbrida/semântica | Proposta documental, sem orquestração ou embeddings implementados |
| Datasets | BPSAD completo não disponível; TweetSentBR legado preservado por pendência de redistribuição/licença |

## Validação P0

- Python 3.11.18, uv 0.13.7, `uv sync --locked` bem-sucedido sem grupo ML.
- `uv run pytest -v -ra`: **394 passed, 0 failed, 0 skipped**.
- `uv run pytest --cov=src --cov-report=term-missing`: **394 passed; 96%**.
- Ruff do frontend e `git diff --check`: aprovados.
- Servidores reais em localhost: FastAPI `/health` e Streamlit `/_stcore/health`, ambos 200.
- Interface exercitada por Streamlit AppTest: normal, vazio, erro, configuração e HTTP inválidos.
- Demo sintética: cinco registros, analisador simulado, BSON serializável, sem gravação no banco.
- [CI da base](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42425474655): success no SHA auditado.

[Evidência da suíte](evidencias/base-pytest.txt),
[cobertura](evidencias/base-cobertura.txt), [demo](evidencias/demo-pipeline.txt).
Um aviso de depreciação de Starlette/httpx apareceu; não provocou falhas.
O sandbox bloqueou bind local e a primeira execução ASGI; a execução válida foi
repetida fora do sandbox com timeout. Não foi necessário modificar a aplicação.
Não houve inspeção visual em navegador: AppTest verifica a árvore de componentes.

## Evidências acadêmicas e aceite

Foram consultados o esquema MongoDB, documentação de classificação/frontend,
issues abertas e a ata 02 na branch `docs` (04/11/2026, SHA `0433a55`). A ata
sustenta a demonstração com mocks, mas explicita que a lembrança sobre avaliação
não é regra oficial. Visão, Arquitetura e GQM são citados no índice daquela branch,
porém seus documentos completos e os critérios oficiais do PC1 não foram
localizados nos arquivos inspecionados. Não se certificam critérios acadêmicos
não fornecidos. Aceites da PO, usabilidade (#63), contratos (#19), persistência
(#20), API (#21) e integração frontend (#27) continuam sujeitos a homologação.

## Demonstração segura e riscos

Demonstrar painel mock, navegação/indicadores, `/health`, importação de fixture,
pipeline simulado e testes. Usar o [roteiro](ROTEIRO_DEMONSTRACAO.md).
Não depender de Atlas, XFetch, pesos de modelos, autenticação ou datasets reais.
Preparar dependências antes da aula, pois a instalação inicial exige rede.
Não apresentar o fluxo completo como integrado. Não há correção funcional
indispensável na base para essa demonstração; as correções dos PRs precisam ser
revisadas antes de qualquer merge.
