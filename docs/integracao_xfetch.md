# XFetch — estado da entrega e contrato

**09/11/2026: implementação no [PR #65](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/65), aberto para `developer`.**
Head consultado: `2dfa96f47f08da723590a15aa7f2abf77c7ae8e9`, branch `xfetch`,
com a correção #68 incorporada. O módulo **não existe na referência PC1 `bfaf7da`**.
Este documento registra a fronteira da entrega externa, sem alegar integração.

Fonte técnica lida: [guia completo no SHA do PR](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/2dfa96f47f08da723590a15aa7f2abf77c7ae8e9/docs/integracao_xfetch.md).

`buscar_tweets_xfetch` faz busca paginada, normaliza e deduplica por ID; não
classifica nem persiste. Retorna `id_origem`, `texto_original`, `fonte="X"`,
rótulos ausentes, `data_publicacao` ISO UTC ou `None` e metadados permitidos.
Texto é preservado. `author_id`, perfis e objetos arbitrários são excluídos
pela correção. O pipeline futuro acrescentará previsão e datas de processamento.

O guia do PR registra: quantidade 1–100, página 1–20, teto local absoluto de
dez requisições (pode ser reduzido), timeout por requisição e ausência de retries.
Tokens são opacos; `limit` permanece constante entre páginas. O teto não garante
custo fixo nem quantidade completa de resultados. Erros públicos não devem
expor chave, consulta ou erro bruto do driver.

Os testes `tests/test_xfetch.py` estão naquela branch e usam respostas sintéticas;
não executar esse caminho neste checkout, onde não existe. A revisão histórica
de 09/11 no SHA `4507aac` registrou 58 testes XFetch; isso não é contagem da
referência atual nem validação do serviço pago. Ver
[relatório histórico](qa/pc1/RELATORIO_FINAL_CODEX.md).

Nenhuma consulta paga foi feita nesta tarefa. Custos/termos, licença, privacidade,
autenticação e integração com banco/API exigem homologação da equipe/PO.
Não é necessário configurar `XFETCH_API_KEY` para demonstrar o PC1.
A [pesquisa híbrida](pesquisa_hibrida_mongodb_xfetch.md) continua proposta.
