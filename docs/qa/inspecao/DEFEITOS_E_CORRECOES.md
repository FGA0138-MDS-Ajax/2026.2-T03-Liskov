# Defeitos, correções e retestes rastreáveis

Consulta: **14/11/2026**. Base atual B:
`1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. Este é um registro técnico da equipe,
não o preenchimento do quadro oficial de defeitos/notas do grupo inspetor.
Os quatro casos partem dos PRs #45, #67, #77 e #88, incluindo a correção de
integração #46 relacionada ao #45. Não há nova alteração de produção nesta tarefa.

E1 = [CI de B](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920),
814 aprovados com MongoDB; E2 = [reteste local de B](RELATORIO_EXECUCAO.md),
789 aprovados/25 skips. Contagens por arquivo constam do
[JSON derivado de JUnit](evidencias/resumo-local.json).

## D01 — Contratos incompatíveis ao combinar classificador e pipeline (#45/#46)

**Defeito e impacto:** o pipeline do PR #44 aceitava `id_origem`/`fonte` vazios,
aceitava sentimento previsto ausente e rejeitava datas `YYYY-MM-DD` entregues
pelo importador. Gerava documentos incompatíveis com o contrato e bloqueava
entradas previstas. O #45 acrescentava validação/normalização na avaliação e
no adaptador; a união precisava preservar essas proteções e corrigir o pipeline.

**Antes, evidência real histórica:**
[`docs/qa/pr44-pr45/regressoes-antes.txt`](../pr44-pr45/regressoes-antes.txt)
preserva **7 FAILED / 3 PASSED** nos dez casos adicionais. Quatro falhas de
identificação, duas de sentimento ausente e uma de data. Mensagens incluem
`DID NOT RAISE ErroPipeline` e rejeição de data sem fuso. Não são falhas
reexecutadas nesta inspeção; são logs históricos versionados, contextualizados no
[`relatorio.md`](../pr44-pr45/relatorio.md), de 06/11/2026.

**Correção e integração:** [PR #45](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/45),
head `e561da419e6355f39bf65c4a2fcb58e3807028ec`, mesclado em developer como
`88bbec275bb268e5264b05bdd1cbbf31712b8837`, não incluía o pipeline. A correção
de integração é o [PR #46](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/46),
head `bb46139a0ffc46e214460ecafcd128ff34a31179`, destino
`feat/integrar-classificador`, merge `4c714c3ff8293e534e85c526c37ddf39b2759400`;
integração posterior aparece em B. Foram preservadas validações do #45, inseridas
checagens obrigatórias e conversão de data de calendário para meia-noite UTC;
timestamps sem fuso continuam rejeitados. Não atribuir as sete correções somente ao #45.

**Depois:** relatório histórico registra 206 aprovados por cenário corrigido.
No reteste atual E2, [`test_integracao_conjunta.py`](../../../tests/test_integracao_conjunta.py)
tem **10 PASS**, incluindo `test_pipeline_rejeita_identificacao_obrigatoria_invalida`,
`test_pipeline_rejeita_sentimento_ausente` e
`test_pipeline_aceita_data_calendario_prevista_no_contrato`.
`test_avaliacao.py` tem **16 PASS** e `test_classificacao.py` **14 PASS**, que
verificam também normalização/validação preservadas do #45. E1 aprova a suíte.

**Limite:** CSV, analisador espião e BSON em memória; não prova pesos reais nem
gravação no MongoDB nesse cenário. Conversão de data e atualização formal dos
documentos ainda exigem revisão/aceite conforme contrato. O relatório antigo
de inferência real não foi reexecutado aqui.

## D02 — Amostragem podia apagar arquivo SQLite preexistente (#67)

**Defeito e impacto:** a versão original do experimento usa caminho fixo
`data/BPSAD/bpsad_grupos_temp.sqlite` e, em `main`, executa `BANCO.unlink()`
se o arquivo existe. O risco de apagar arquivo preexistente é diretamente
verificável no [pai da correção](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/0e19b6bf1aa537dd7bed71247e6f1542d9c8ad2f/amostrar_bpsad.py).
O mesmo PR também trata cotas inexatas, validação e vazamento na amostragem.

**Antes:** defeito identificado por inspeção de código e descrito no
[PR #67](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/67).
Execução destrutiva anterior e log de teste vermelho: **N/D**; não se executou
o script antigo contra arquivos reais para produzir artificialmente uma falha.

**Correção:** head `1cd636e791529f987175355e2f10dbaeac264b2a`, merge
`3da81d5e65a1850374145741a62106aafd531ea0` na branch
`feat/integrar-classificador`, integrado posteriormente em B. O script atual
[`amostrar_bpsad.py`](../../../scripts/experimentos/amostrar_bpsad.py) usa
`TemporaryDirectory` exclusivo, com limpeza em falhas; não apaga o arquivo
preexistente. Também registra seed/cotas, valida classes e recusa sobrescrita.

**Depois:**
[`test_experimentos_bpsad.py`](../../../tests/test_experimentos_bpsad.py)::`test_limpeza_e_preservacao_sqlite_preexistente`
é parametrizado para sucesso e falha sintética. Cria conteúdo sentinela,
injeta erro de leitura e confere preservação/limpeza. `test_cotas_desbalanceadas_e_arredondamento`
e `test_cli_e_protecao_contra_sobrescrita` cobrem riscos correlatos.
E2 registra **14 PASS** nesse arquivo; E1 também passa. O
[CI histórico 42681909047](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42681909047)
do head corretivo foi consultado e concluiu `success`; não se deduz contagem sem log.

**Limite:** corpus sintético temporário; não comprova BPSAD completo, pesos,
métricas declaradas ou independência científica. Cadeia de evidência anterior
é inspeção de código, explicitamente distinta de teste vermelho executado.

## D03 — T10 esperava rotas antigas depois da administração (#77)

**Defeito e impacto:** após integrar #75, dois testes ainda esperavam somente
`/health` no OpenAPI e 404 para rotas administrativas implementadas. A suíte
de QA descrevia o estado anterior do backend e produzia falsas reprovações.

**Antes:** a [descrição do PR #77](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/77)
relata as expectativas inválidas. O diff do commit
[`8306eae`](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/commit/8306eaedcf93d5c330e3c33acd504d11b1821608)
mostra a troca da asserção de rotas e de 404 por erros de configuração/sessão.
Log anterior de execução com falha: **N/D nesta inspeção**; não se afirma uma
contagem de testes falhos com base apenas no diff.

**Correção:** head `8306eaedcf93d5c330e3c33acd504d11b1821608`, destino
developer, merge `87b80fd2d0c556859a46e58b3ae77663a67a045b`. Atualiza as rotas
esperadas e testa login sem configuração retornando 503 e token inválido
recusado. A configuração do teste é isolada para não depender de credenciais
locais. Alteração restrita aos testes; não foi correção da API de produção.

**Depois:** o PR declara 19 aprovados no arquivo e 609 na suíte da época;
essas contagens são históricas relatadas. O
[CI do head, 43081764169](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43081764169)
foi consultado e está `success`. E2 executou
[`test_qa_t09_t10.py`](../../../tests/test_qa_t09_t10.py): **19 PASS**; os cenários
`test_t10_health_contrato_http_cabecalhos_e_esquema_openapi` e
`test_t10_administracao_api_contra_fastapi_real_sinaliza_503_e_sessao_invalida`
permanecem. A lista OpenAPI evoluiu de novo com as rotas de análise/consulta;
o teste de B reflete essa evolução, não deve ser congelado na lista do #77.

**Limite:** TestClient/app real com dependências substituídas; não significa
autenticação de produção homologada nem conexão real de todos os serviços.

## D04 — Import inexistente impedia coletar testes de leitura (#88)

**Defeito e impacto:** o módulo e os testes importavam
`src.persistencia.escrita`/`conexao`, inexistentes naquela branch, impedindo
coleta do pytest. Mesmo após corrigir imports, os testes reais precisavam de
MongoDB na CI.

**Antes, log remoto consultado:**
[run 43100185858](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43100185858),
[job 130788984183](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43100185858/job/130788984183),
11/11/2026: `collected 715 items / 1 error`,
`ERROR collecting tests/test_persistencia_leitura.py`,
`ModuleNotFoundError: No module named 'src.persistencia.escrita'`.
Não eram 715 testes aprovados: houve interrupção da coleta.

**Correção:** [PR #88](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/88),
head `2047442e0f2577888eeed9ca25c745f6c435d7a4`, criado do
`e635fcc36261539cff3904d96842f17d2c1046f8` e mesclado como
`fa5c9c17d84c9358488a32850768cafac8200825` na branch
`feat/issue-20-persistencia-mongodb`. Corrige imports para
`src.dados.repositorio`/`database` e adiciona `mongo:7`/healthcheck/URI ao workflow.
O PR #84 integra essa branch e o #87 adapta buscas ao repositório; B inclui
essas mudanças. O #88 sozinho não deve receber crédito pelas adaptações do #87.

**Depois, log remoto consultado:**
[run 43502971956](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43502971956),
[job 132153235589](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43502971956/job/132153235589),
13/11: **598 coletados/aprovados, sem skips, 1 warning, 16,80 s, cobertura 94%**
(1756 statements, 99 missing), com container iniciado. Essa contagem pertence
à branch corretiva menor, não à developer atual. E1 de B aprova os 814; E2 de B
coleta todos os 25 itens de `test_persistencia_leitura.py`, **8 PASS / 17 SKIP**
pela ausência local do banco. Assim, o erro de importação não ocorre no reteste,
mas integração de leitura real local continua não executada.

**Limite:** os sete testes unitários selecionados na descrição original do #88
não representavam validação real de banco. O CI posterior fornece essa evidência
para os casos existentes; não comprova fluxo completo com BERTweet/UI reais.

## Uso para revisão

Os casos mostram correção de código, segurança de arquivo temporário, manutenção
do oráculo de teste e infraestrutura de CI. Lacunas de log anterior em D02/D03
ficam preservadas; D01/D04 têm falha anterior explicitamente registrada. Nenhuma
correção prova aceite da PO. As próximas ações são revisar as evidências, manter
testes de regressão e completar os cenários reais pendentes conforme o
[plano](PLANO_TESTES_ATUAL.md) e a [matriz](MATRIZ_RASTREABILIDADE.md).
