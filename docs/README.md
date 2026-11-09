# Documentação do SentIA

Referência PC1 de 09/11/2026: integração experimental `bfaf7da`, com #69 e #70,
ambos ainda em PR aberto. Para executar, comece no [README do produto](../README.md).
Para apresentar, use o [resumo](qa/pc1/RESUMO_APRESENTACAO.md).

## Produto e projeto

- [Fontes acadêmicas, requisitos e pendências de aceite](fontes-academicas.md).
- [Índice acadêmico na revisão consultada](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/docs/index.md).
- [Backlog de issues](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues).
- [Changelog da referência selecionada](../CHANGELOG.md).
- [Guia de versionamento da equipe](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/instrucoes/instrucoes.md).

Os documentos completos de Visão, Arquitetura e GQM não foram localizados;
o inventário de fontes explicita o alcance da revisão.

## Arquitetura

- [Arquitetura observada no código](arquitetura.md).
- [Contratos de dados e fronteiras](contratos-dados.md).
- [Contrato HTTP proposto e rotas existentes](frontend/CONTRATO-API.md).

## Dados

- [TweetSentBR: aquisição, auditoria e pendência de licença](tweetsentbr.md).
- [BPSAD: adaptador e amostra sintética](bpsad.md).
- [XFetch: entrega em PR aberto, ausente da referência](integracao_xfetch.md).
- [Pesquisa híbrida: proposta não implementada](pesquisa_hibrida_mongodb_xfetch.md).

## ML

- [Classificador BERTweet, baseline e avaliação](classificacao.md).
- [Homologação histórica #44/#45](qa/pr44-pr45/relatorio.md).
- [Resultados históricos de inferência](qa/pr44-pr45/inferencia-real.json) e [baseline](qa/pr44-pr45/avaliacao-baseline.json); não são nova avaliação independente.

## Banco

- [Configuração e verificação MongoDB](mongodb_setup.md).
- [Esquema e exemplos de consultas propostas](banco/esquema-mongodb.md).
- Exemplos sintéticos: [mínimo](banco/exemplos/analise-minima.json), [completo](banco/exemplos/analise-completa.json), [baseline](banco/exemplos/analise-baseline.json), [TweetSentBR](banco/exemplos/analise-tweetsentbr.json) e [inválidos](banco/exemplos/analises-invalidas.json).

## Frontend

- [Guia do painel e distinção interface/backend](frontend/README.md).
- [Contrato API](frontend/CONTRATO-API.md).
- [Wireframes e estado dos componentes](frontend/WIREFRAMES.md).
- [Validação da Clicia no SHA selecionado](qa/pc1/VALIDACAO_FRONTEND_CLICIA.md).

## QA e apresentação

- [Guia da suíte](../tests/README.md).
- [Matriz de rastreabilidade](qa/pc1/MATRIZ_RASTREABILIDADE.md).
- [Status das entregas](qa/pc1/STATUS_ENTREGAS.md).
- [Ensaio da revisão documental](qa/pc1/RELATORIO_ENSAIO_FINAL.md).
- [Roteiro principal e contingência](qa/pc1/ROTEIRO_DEMONSTRACAO.md).
- [Entrada do roteiro atualizado](qa/pc1/ROTEIRO_PC1_ATUALIZADO.md).
- [Resumo para consulta na apresentação](qa/pc1/RESUMO_APRESENTACAO.md).
- [Auditoria documental](qa/pc1/AUDITORIA_DOCUMENTACAO.md).
- Históricos preservados: [Relatório PC1](qa/pc1/RELATORIO_PC1.md), [relatório final Codex](qa/pc1/RELATORIO_FINAL_CODEX.md) e [inventário das evidências](qa/pc1/evidencias/README.md).

## Reuniões

- [Ata 01 — 25/09/2026](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/docs/atas-reuniao/ata-reuniao-1.md).
- [Ata 02 — 04/11/2026](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0433a5545628c3de58c247c43012a3cdbd52d93c/docs/atas-reuniao/ata-reuniao-2.md).

## Experimentos

- [Experimentos BPSAD: PR #64, comandos em outra branch e limites científicos](experimentos_bpsad.md).
- [Comparação de modelos disponível nesta referência](../scripts/comparar_modelos.py); execução real pode exigir corpus local/pesos, conforme o guia de classificação.
