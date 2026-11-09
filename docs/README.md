# Documentação do SentIA

Índice consolidado da documentação técnica, acadêmica e de qualidade (QA) do projeto **SentIA** para o Ponto de Controle 1 (PC1). Para instruções rápidas de instalação e execução, consulte o [`README.md`](../README.md) na raiz do repositório.

## Apresentação e QA do PC1

- [Roteiro de demonstração (5–8 minutos)](qa/pc1/ROTEIRO_DEMONSTRACAO.md)
- [Status final do PC1, resultados dos testes e ordem de merge](qa/pc1/STATUS_FINAL.md)
- [Matriz de rastreabilidade (Issues, Requisitos, Código e Testes)](qa/pc1/MATRIZ_RASTREABILIDADE.md)
- [Validação do frontend da Clicia (PR #70 + PR #71)](qa/pc1/VALIDACAO_FRONTEND_CLICIA.md)
- [Guia da suíte de testes de aquisição e importação](../tests/README.md)

## Arquitetura e Contratos

- [Arquitetura observada no código](arquitetura.md)
- [Contratos de dados (Aquisição, Pipeline ML, MongoDB e Painel)](contratos-dados.md)
- [Contrato HTTP proposto da API](frontend/CONTRATO-API.md)

## Frontend (Streamlit)

- [Guia do módulo de apresentação](frontend/README.md)
- [Wireframes e estado dos componentes](frontend/WIREFRAMES.md)

## Aquisição de Dados

- [TweetSentBR: aquisição, auditoria e governança](tweetsentbr.md)
- [BPSAD: adaptador e mapeamento de avaliações](bpsad.md)
- [XFetch: módulo de coleta paginada (integrado no PR #65)](integracao_xfetch.md)
- [Proposta de pesquisa híbrida MongoDB + XFetch](pesquisa_hibrida_mongodb_xfetch.md)

## Processamento e Machine Learning

- [Classificador BERTweet, baseline TF-IDF e pipeline](classificacao.md)
- [Relatório de homologação dos PRs #44 e #45](qa/pr44-pr45/relatorio.md)

## Banco de Dados (MongoDB)

- [Configuração e validação de conexão com PyMongo](mongodb_setup.md)
- [Esquema lógico da coleção `analises`](banco/esquema-mongodb.md)
- Exemplos de documentos: [mínimo](banco/exemplos/analise-minima.json), [completo](banco/exemplos/analise-completa.json), [baseline](banco/exemplos/analise-baseline.json), [TweetSentBR](banco/exemplos/analise-tweetsentbr.json) e [inválidos](banco/exemplos/analises-invalidas.json)

## Documentação Acadêmica e Reuniões

- [Branch `docs` (MkDocs e Atas de Reunião)](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/tree/docs)
- [Changelog do projeto](../CHANGELOG.md)
