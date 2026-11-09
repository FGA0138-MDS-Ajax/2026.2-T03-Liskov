# Status das entregas — PC1

Corte: **09/11/2026**. Cenário principal: integração experimental
`bfaf7da4437493f5ee9b44022d4979623b232add`, com preparação #69 (`b9d8326`),
frontend #70 (`61926fe`) e correção #71 (`bcd75e7`). Branch documental:
`docs-pc1-documentacao-consolidada`. `developer` remota consultada: `c6fc535`.
Os PRs #69/#70/#71 continuam abertos, sem integração oficial a developer.

## Concluído tecnicamente no escopo delimitado

- Importação CSV e adaptadores locais TweetSentBR/BPSAD, auditoria e validação de entradas.
- Pipeline em lote que preserva identidade/texto/anotações e produz documentos BSON em memória.
- Adaptador BERTweet e baseline isolado; funcionamento de contrato testado, sem nova inferência real.
- FastAPI básico com `GET /health`; dependências uv/lock, Makefile e CI configurados.
- Estrutura Streamlit, fontes desacopladas e documentação do esquema MongoDB.

Esses incrementos não representam conclusão de todos os RFs, da integração ponta
a ponta ou do aceite da PO. [Matriz por issue](MATRIZ_RASTREABILIDADE.md).

## Testado em mock

Dashboard, filtros, indicadores e estados vazio/erro; login e sessão/logout;
importação com contagens/descartes; coleta e atualização simuladas; clientes HTTP;
conexão/ping/fechamento MongoDB; analisador da demo. O upload não salva dados, a
coleta usa fonte fixa e o dashboard não recebe as linhas recém-enviadas.

Resultado desta referência em 09/11: **461 passed, 0 failed, 0 skipped**, cobertura
`src` **94%**. [Log](evidencias/documentacao/suite.txt) e [ensaio](RELATORIO_ENSAIO_FINAL.md).
É validação offline de software, não acurácia do modelo nem indicador GQM.

## Em PR aberto e aguardando revisão

| PR | Destino | Presente em `bfaf7da`? | Escopo / pendência |
|---|---|---|---|
| [#69](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/69) | `developer` | Sim | Preparação offline; revisão/aceite e promoção pendentes |
| [#70](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/70) | `developer` | Sim | Novo frontend simulado; CI verde em `61926fe`, sem review submetido na consulta inicial |
| [#71](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/71) | `feat/painel-frontend` | Sim | Correção do parser CSV/labels em tablet e regressões isoladas; revisão pendente |
| [#64](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/64) | `developer` | Não | Experimentos BPSAD e preservação; métricas reais não reproduzidas nesta revisão |
| [#65](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/65) | `developer` | Não | XFetch; testes sintéticos não certificam provedor pago |

#67/#68 corrigiram #64/#65 e já foram incorporados às branches dos autores no
inventário consultado. #66 foi fechado sem merge, substituído por #70; não é
implementação atual nem fonte de endpoints administrativos nesta referência.

## Aguardando aceite da PO / revisão acadêmica

Não se presume aceite a partir de código ou CI: atualização RF03–RF06/T04–T07,
contrato #19, data/fuso dos filtros #24, escopo RF02, avaliação independente
#17/RNF01, interface e requisitos #13/#14/#59–#61, licença/redistribuição de
TweetSentBR e política de privacidade, pesquisa temática e metas GQM.
Os documentos oficiais completos ainda precisam ser disponibilizados.

## Não implementado nesta referência

CRUD e consultas de análises MongoDB (#20), API de análises/listagem/filtros
(#21/#23–#25), autenticação/autorização real (#58), dashboard integrado/listagem
(#27), gráficos (#28), resumo textual (#29), nuvem de palavras (#30), busca
híbrida/semântica e orquestração XFetch + banco + ML + painel.

## Não verificado

Nova conexão Atlas/servidor MongoDB, XFetch real, inferência BERTweet atual,
reprodução das métricas BPSAD, independência de pré-treinamento, publicação HTTPS
integrada (#62), estudo de usabilidade (#63), conclusão integral T01–T17 e aceite
acadêmico do PC1. O ensaio visual em mock é evidência limitada de aparência,
sem substituir estudo com usuários ou aceite de #31/#63.

O GitHub mostra #17 fechada, mas o aceite científico não foi verificado. #3 também
está fechada e ainda há lacunas de licença/proveniência. Esses estados são
preservados no [snapshot](evidencias/documentacao/issues.json), sem reabrir/encerrar
issues nesta tarefa. A [matriz](MATRIZ_RASTREABILIDADE.md) registra cada diferença.
