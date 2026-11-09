# Auditoria da documentação — SentIA PC1

Data: **09/11/2026**. Escopo: documentação, sem alterações funcionais, refatoração,
remoção de material acadêmico, mudança de requisitos, merge oficial ou reescrita
de histórico. Referência técnica e resultado final: [ensaio](RELATORIO_ENSAIO_FINAL.md).
A branch documental deriva do código validado da integração PC1, não da developer
local antiga. O [status](STATUS_ENTREGAS.md) discrimina entregas em PR aberto.

## Inventário de alterações

| Documento | Estado anterior | Alteração realizada | Status |
|---|---|---|---|
| `README.md` | Guia da preparação anterior, citava #66 e administração placeholder | Produto, contexto UnB/FGA/T03, estados das funcionalidades, arquitetura, instalação, execução, fluxo de desenvolvimento, índice e limitações | Revisado contra referência selecionada |
| `CHANGELOG.md` | Misturava placeholder, administração nova e preparação “proposta” | Consolidação sem duplicação; presença na integração distinta de merge em developer; #64/#65 fora da referência | Revisado; sem versão/release inventada |
| `docs/README.md` | Ausente | Índice por produto, arquitetura, dados, ML, banco, frontend, QA, reuniões e experimentos | Criado |
| `docs/fontes-academicas.md` | Ausente | Inventário de fontes, indisponibilidades, requisitos e decisões pendentes | Criado; validação acadêmica pendente |
| `docs/arquitetura.md` | Ausente | Retrato do código, camadas e fronteiras ainda não integradas | Criado; não substitui DA oficial |
| `docs/contratos-dados.md` | Contratos dispersos | Entrada/saída, rótulos humanos versus previsão, datas, metadados, limites de cada fluxo | Criado; aceite #19 pendente |
| `docs/frontend/README.md` | Já descrevia #70, mas afirmava acesso só pela API e citava remissões acadêmicas não conferidas | Fontes mock/API, navegação, sessão/logout, importação/coleta simuladas, estados de erro, testes existentes e distinção interface/backend | Revisado |
| `docs/frontend/CONTRATO-API.md` | Proposta correta no topo, mas usava presente para gravação/token e atribuições PO sem fonte direta | Status por rota, administração futura, sessão Streamlit, semântica de dados e referências de testes | Revisado; rotas propostas continuam propostas |
| `docs/frontend/WIREFRAMES.md` | Imagens históricas e alegação de decisão PO sem artefato localizado | Estado por componente, administração sem wireframe, percentuais vazios, limites visuais e fonte da decisão a confirmar | Revisado; imagens originais preservadas |
| `docs/banco/esquema-mongodb.md` | Descrevia persistência/consultas no presente e atribuía conversões à persistência | Esquema previsto, pipeline já converte datas/rótulos e cria processamento, índices ainda propostos, metadados sem sanitização garantida | Revisado; JSON históricos preservados |
| `docs/mongodb_setup.md` | Instruções transitórias de #47/#48 como se abertos | Instalação uv atual; ping/testes e limites; histórico de integração por link fixo | Revisado |
| `docs/classificacao.md` | Misturava 126 testes/14 skips sem SHA suficiente e pendências já implementadas | Uso/contratos atuais, ML opcional, pipeline existente, evidências antigas identificadas e aceite científico pendente | Revisado; histórico acessível |
| `docs/tweetsentbr.md` | “Uso autorizado” confundia escopo técnico com licença | Escopo técnico, licença/redistribuição pendente, comandos de módulo e separação de rótulos | Revisado; dataset intacto |
| `docs/bpsad.md` | Afirmava que mudança de domínio evitava vazamento | Fonte candidata, independência não comprovada, comandos e contrato do adaptador | Revisado; números do autor preservados como declarados |
| `docs/integracao_xfetch.md` | Ausente neste checkout, disponível no #65 | Estado externo por SHA, contrato resumido e link à fonte completa | Criado; não apresenta módulo como local |
| `docs/pesquisa_hibrida_mongodb_xfetch.md` | Ausente neste checkout, proposta na branch XFetch | Fluxo conceitual, responsabilidades e decisões ainda não aprovadas | Criado; não implementado |
| `docs/experimentos_bpsad.md` | Ausente neste checkout, guia no #64 | Comandos só para checkout separado; métricas declaradas, não reproduzidas | Criado; aceite científico pendente |
| `tests/README.md` | Guia parcial de dados, título “Contrato Homologado” sem comprovação de aceite | Escopo da suíte, testes atuais/ausentes, mocks, histórico das contagens e contrato implementado | Revisado |
| `docs/qa/pc1/RELATORIO_PC1.md` | Retrato anterior ao frontend #70 | Aviso de registro histórico, SHAs/data e ligação ao estado atual | Preservado com contexto |
| `docs/qa/pc1/RELATORIO_FINAL_CODEX.md` | Auditoria anterior com #66 aberto e contagens antigas | Aviso histórico; texto e evidências anteriores mantidos | Preservado com contexto |
| `docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md` | Apenas cenário A sem login/filtros novos | Cenário principal B, comandos/resultados e contingência A delimitada | Atualizado |
| `docs/qa/pc1/ROTEIRO_PC1_ATUALIZADO.md` | Ausente no checkout inicial; disponibilizado pelo ensaio | Referência ao roteiro canônico e procedência do roteiro validado | Consultado; entrada de navegação sem duplicar roteiro ativo |
| `docs/qa/pc1/VALIDACAO_FRONTEND_CLICIA.md` | Ausente no checkout inicial; disponibilizado pelo ensaio | Incorporado com origem, falhas/correções e limites do frontend | Consultado e preservado |
| `docs/qa/pc1/RELATORIO_ENSAIO_FINAL.md` | Ausente no checkout inicial; disponibilizado pelo ensaio | Incorporado e ligado às verificações desta revisão | Consultado e atualizado com procedência |
| `docs/qa/pc1/MATRIZ_RASTREABILIDADE.md` | Ausente | Issue/RF/US/T, implementação, teste, evidência, estado e pendência | Criado |
| `docs/qa/pc1/STATUS_ENTREGAS.md` | Ausente | Conclusão técnica, mock, PR/revisão, PO, ausências e não verificados | Criado |
| `docs/qa/pc1/RESUMO_APRESENTACAO.md` | Ausente | Fala comum, arquitetura, ordem de demo, resultados, limites e próximos passos | Criado |
| `docs/qa/pc1/evidencias/README.md` | Evidências sem índice único | Identificação de coleções por origem/SHA/data e comandos válidos | Criado; logs antigos preservados |
| Este relatório | Ausente | Inventário, fontes, verificações, contradições e pendências | Criado |

## Fontes consultadas

Foram lidos integralmente os arquivos solicitados existentes na referência, os
três guias de XFetch/pesquisa/experimentos nas branches dos PRs, Makefile,
manifesto/lock/configuração de CI, exemplos de ambiente sem segredos e os módulos
de importação, pipeline, classificação, conexão, API e apresentação pertinentes.
Foram consultados testes reais, relatórios históricos e evidências recentes.

Git inicial: `developer` local `e2a3ff0`, 19 commits atrás da remota, com
`docs/auditorias/` não rastreado preservado. Foram executados `git status --short
--branch`, `git fetch origin --prune`, `gh pr list --state open` e
`git log --oneline -12`, além de inspeção de branches/worktrees e SHAs.

Fontes acadêmicas encontradas: índice da branch `docs`, atas 01/02 e guia de Git,
revisão `0433a5545628c3de58c247c43012a3cdbd52d93c`; backlog/aceitação nas issues,
descrições e estados dos PRs. Ver [inventário com links fixos](../../fontes-academicas.md).
Visão/Escopo completos, DA completo, Tarefa GQM, backlog acadêmico consolidado,
PDFs identificáveis do T03 e rubrica oficial do PC1 não foram encontrados. Não
havia sessão de documentos conectada. Não foram deduzidos critérios acadêmicos
de memória de reuniões ou de código parcial.

## Referências corrigidas e histórico

- #66 deixou de ser a referência atual do README/roteiro; está fechado sem merge,
  substituído por #70. Menções históricas foram mantidas, com aviso de contexto.
- #70 continua em PR aberto; login simulado não foi atribuído à developer nem
  usado para declarar #58 entregue. Correções de ensaio são identificadas à parte.
- `tests/test_api_administracao.py` não existe nesta entrega. O cabeçalho residual
  do #70 foi corrigido pelo PR #71; a documentação aponta para testes existentes.
- Links de atas/guias acadêmicos usam a revisão efetivamente lida. Novos links
  locais apontam para o índice, contratos, matriz, ensaio e roteiro canônico.
- Documentos dos PRs #64/#65 apontam para seus SHAs. Seus caminhos de scripts/testes
  não são apresentados como comandos executáveis no checkout PC1.
- Comandos antigos `python scripts/auditar_datasets.py` foram padronizados para
  `uv run python -m scripts.auditar_datasets`; instalação transitória #47/#48 foi
  contextualizada. O default legado `modelos/baseline.pkl` permanece no script de
  comparação; organização `models/` é uma pendência de código, sem alteração aqui.

## Verificações

Os resultados completos, SHA/data e limites estão no [ensaio](RELATORIO_ENSAIO_FINAL.md)
e no [inventário de evidências](evidencias/README.md). Verificação de Markdown em
[links.json](evidencias/documentacao/links.json): arquivos, links relativos,
âncoras, PRs/issues do inventário remoto e blobs Git fixos. Links externos de
fornecedores/Figma e runs históricos não receberam nova certificação HTTP.

Foram verificados: instalação locked com cache local, criação preservadora do
`.env`, alvos do Makefile, lint, lock, suíte com cobertura, demo do pipeline,
CLIs de auditoria/comparação (`--help`), auditoria de metadados TweetSentBR e
fixture BPSAD, servidores locais FastAPI/Streamlit, OpenAPI e diff check.
Não foram executados ML real, MongoDB externo, XFetch pago, publicação ou comandos
dependentes do corpus BPSAD completo. Nenhuma variável privada foi exibida.

O sandbox bloqueou TestClient/bind e consultas GitHub; as verificações necessárias
foram repetidas com autorização fora dele. Tentativa bloqueada não foi registrada
como aprovação. Não foram escritos novos testes no repositório nesta tarefa.

## Contradições e pendências de aceite

O [inventário acadêmico](../../fontes-academicas.md) e a [matriz](MATRIZ_RASTREABILIDADE.md)
registram cada divergência. Principais: RFs clássicos versus BERTweet; visão de
busca temática versus mock fixo; anotações humanas versus inferência; esquema
versus CRUD ausente; metadados livres versus política de privacidade; cliente HTTP
versus endpoints ausentes; #17 fechada versus avaliação independente não verificada;
contagens antigas de testes versus novo código.

PO/equipe precisam validar: mudanças de escopo/requisitos/roteiros de teste,
contrato único e data/fuso dos filtros, licença e redistribuição TweetSentBR,
curadoria/privacidade, independência da avaliação e aceite visual/funcional.
Não houve alteração silenciosa de requisito, prioridade, estimativa ou métrica GQM.

## Referência Git e entrega

Base congelada: `bfaf7da4437493f5ee9b44022d4979623b232add`, cenário B do
ensaio mais recente. Branch própria: `docs/pc1-documentacao-consolidada`.
O destino `test/pc1-base-documentacao` publica somente uma referência para esse
commit já existente, permitindo um PR com diff exclusivamente documental, sem
incorporar #70/#71 silenciosamente à developer e sem criar novo merge.

Commits usam autoria Codex definida por comando, sem alterar configuração global.
A árvore original em developer `e2a3ff0`, com `docs/auditorias/` não rastreado,
foi preservada. Branches dos integrantes, main/developer e arquivos acadêmicos
não foram alterados por esta tarefa. Os relatos de incidentes/merges no ensaio
importado pertencem à execução anterior e permanecem identificados como origem.

A auditoria final encontrou **31 arquivos Markdown, 299 links relativos e três
âncoras**, sem alvo/âncora ausente. Foram inventariadas 65 URLs únicas do GitHub: PRs/issues conferidos no snapshot
remoto e blobs fixos conferidos por objetos Git; runs históricos não foram
revalidados por HTTP. O limite externo está registrado em `links.json`. Os números identificam este corte, não uma ferramenta
permanente adicionada ao produto. Ver [resumo de execução](evidencias/documentacao/execucoes.json).

## Após o PC1

Disponibilizar/conciliar Visão, Arquitetura e GQM oficiais; atualizar #19 e
contratos quando API/banco forem implementados; revisar README/status/changelog
após merges oficiais; fixar checkpoint/metodologia de avaliação; resolver licença
do dataset legado; validar publicação/usabilidade; homologar XFetch e pesquisa
temática. Não foi removido arquivo acadêmico ou evidência histórica.

**Prontidão:** documentação adequada à demonstração técnica delimitada, com
referência congelada, principal/contingência e limitações explícitas. Não certifica
aceite da PO ou atendimento a rubrica acadêmica não disponibilizada.
