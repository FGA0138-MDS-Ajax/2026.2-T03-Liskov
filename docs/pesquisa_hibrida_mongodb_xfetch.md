# Pesquisa híbrida MongoDB + XFetch — proposta

**Não implementada na referência PC1 `bfaf7da` nem comprovada como integração
real pelo PR #65.** Documento de planejamento, 09/11/2026. A ata 02 registra
consulta por palavra-chave e reaproveitamento do banco; não aprova algoritmo,
limites, embeddings ou Vector Search. Ver [fontes acadêmicas](fontes-academicas.md).

Fluxo proposto: receber termo → consultar banco → avaliar suficiência → consultar
provedor externo quando necessário → deduplicar → classificar/persistir → apresentar.
A ordem entre classificação e gravação, reanálises e política de cache ainda
precisa ser decidida no contrato único. Não há orquestrador implementado.

| Camada | Responsabilidade proposta | Pendência |
|---|---|---|
| Serviço | Coordenar consulta e complemento externo | API e contrato de busca |
| Dados | Recuperar/gravar registros por fonte/ID | CRUD, índices, cache e política de retenção |
| Aquisição | Consultar XFetch e normalizar | Homologação do #65 e serviço externo |
| ML | Classificar e identificar checkpoint | Avaliação e custo de inferência |
| Painel | Receber termo e apresentar dados | Busca temática e integração real |

Pesquisa lexical e semântica são alternativas futuras. Embeddings, índice
vetorial, relevância mínima, quantidade de resultados, orçamento e consentimento
de coleta não estão aprovados neste documento. A sugestão histórica de 100 textos
não é amostra representativa nem critério oficial do PC1. Nenhum código de busca
semântica ou Vector Search é apresentado como entregue.

O [documento original da proposta](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/2dfa96f47f08da723590a15aa7f2abf77c7ae8e9/docs/pesquisa_hibrida_mongodb_xfetch.md)
permanece na branch do #65, sem alteração de requisitos. Próximo passo: PO/equipe
refinarem backlog e critérios antes da implementação. [Estado XFetch](integracao_xfetch.md).
