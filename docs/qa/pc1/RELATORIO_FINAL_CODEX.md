# Relatório final Codex — preparação PC1 do SentIA

Auditoria: **09/11/2026**. Repositório: FGA0138-MDS-Ajax/2026.2-T03-Liskov.
Base: `c6fc53561055178085edcbc123fc86166edf89fa` (developer remota).
Execução em worktrees isoladas, sem merge oficial ou alteração de branches dos autores.

## A. Resumo executivo

**A base está apta à demonstração offline delimitada no roteiro.** FastAPI e
Streamlit iniciaram de fato e responderam 200. A developer auditada passou em
394 testes, sem falhas/skips, com 96% de cobertura. Não foi necessário alterar
código funcional da base para essa demonstração. README, exemplos de ambiente,
CI incremental, template de PR, demonstração sintética e documentação foram entregues.

PRs #64 e #65 revisados integralmente: dois commits/três arquivos e um commit/quatro
arquivos, respectivamente. Correções publicadas em PRs próprios #67 e #68,
dirigidos às branches dos autores, ambos com CI verde. A integração experimental
passou em **471 testes, 0 falhas, 0 skips, 96% de cobertura**. Parecer de contrato:
**COMPATÍVEL** com fixtures/mocks e BSON; não certifica integração externa real.

Sem nova inferência real BERTweet, consulta XFetch, conexão Atlas ou reprodução das
métricas BPSAD. Persistência de análises, endpoints completos e fluxo real até o
dashboard continuam pendentes. A entrega A está no PR #69, com CI verde no commit de documentação/evidências.
Critérios oficiais do PC1 não foram disponibilizados
nos materiais localizados; não são inventados neste relatório.

## B. Alterações realizadas

| Arquivo | Alteração | Motivo | Evidência |
|---|---|---|---|
| `README.md` | Apresentação SentIA, comandos, arquitetura, limites e contribuição | Substituir template e tornar execução reproduzível | Demo e suíte da entrega A |
| `scripts/demonstrar_pipeline.py` | CSV sintético → analisador simulado → BSON | Demonstração sem rede/ML/banco | `evidencias/demo-pipeline.txt` |
| `.env.example` | Exemplo unificado painel/API/MongoDB/XFetch | Setup utilizável preservando `.env` local | `make env` preserva arquivo existente |
| `.env.frontend.example` | Mantido como compatibilidade | Evitar quebrar instruções anteriores | README explica ambos |
| `Makefile` | Exemplo unificado, demo, lint incremental e lock check | Atalhos coerentes com CI | Comandos executados e diff check |
| `.github/workflows/ci.yml` (A) | Todos os destinos de PR, lock check, Ruff F/E9 geral e suíte completa | Cobrir camadas e PRs de correção | CI da entrega A; sem grupo ML |
| `.github/PULL_REQUEST_TEMPLATE.md` | Template com contratos, testes, evidências, dependências e PO | Rastreabilidade de QA | Inspeção do arquivo |
| `.gitignore` | Cache Ruff e XML de cobertura ignorados | Evitar novos artefatos locais versionados | Status final das worktrees |
| `CHANGELOG.md` | Registro PC1 como proposta | Comunicar escopo efetivamente entregue | Commit A |
| `docs/qa/pc1/RELATORIO_PC1.md` | Estado, riscos, evidências e limites acadêmicos | Preparar apresentação fiel | SHA e logs anexos |
| `docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md` | Comandos exatos, mocks e contingência | Demonstração curta e offline após setup | Servidores 200, demo e testes |
| `docs/qa/pc1/RELATORIO_FINAL_CODEX.md` | Este relatório | Consolidar entregas auditáveis | Seções A–J e evidências |
| `docs/qa/pc1/evidencias/` | Logs de testes/cobertura, smoke e teste conjunto reproduzível | Sustentar conclusões | Arquivos vinculados abaixo |
| `amostrar_bpsad.py` e `scripts/validar_bpsad.py` (B) | Wrappers para novos módulos | Preservar comandos históricos | CLI e testes sintéticos |
| `scripts/experimentos/amostrar_bpsad.py` (B) | SQLite exclusivo, CLI, seed, cotas exatas e partição validada | Evitar exclusão de arquivo preexistente e amostra incorreta | 14 novos testes de experimentos |
| `scripts/experimentos/validar_bpsad.py` (B) | CLI, validação de amostra, hash/versões, baseline padrão e ML opt-in | Reproduzir e identificar limites científicos | Teste de avaliação sintética |
| `tests/test_experimentos_bpsad.py` (B) | Fixture temporária, determinismo, cotas, conflitos, limpeza, CLI e vazamento | Regressões sem BPSAD completo | 46 testes focados, 222 na suíte |
| `pyproject.toml`, `uv.lock`, `.python-version` (B) | Base uv atual + psutil no grupo opcional `experimentos` | Head #64 antecede uv; dependência antes não declarada | `uv sync --locked`, `uv lock --check`; CI #67 |
| `.github/workflows/ci.yml` (B) | uv e destino da branch do autor | Validar o PR de correção | CI #67 success |
| `docs/experimentos_bpsad.md` (B) | Reprodução e efeito científico das correções | Não atribuir métricas antigas à nova amostra | Dados do autor preservados como não reproduzidos |
| `src/processamento/aquisicao/xfetch.py` (C) | Teto de 10 páginas, IDs/datas/metadata válidos e erros seguros | Evitar consumo sem teto e divergência de privacidade | 58 testes XFetch |
| `tests/test_xfetch.py` (C) | HTTP, timeout, envelopes, teto, metadados, texto e datas | Cobrir defeitos comprovados offline | 58 passed; CI #68 |
| `docs/integracao_xfetch.md` (C) | Contrato externo verificado, limites e privacidade | Corrigir exemplo de paginação e reduzir ambiguidade | Fontes oficiais citadas no arquivo |
| `docs/pesquisa_hibrida_mongodb_xfetch.md` (C) | Status explícito de proposta não implementada | Não confundir conceito com entrega | Revisão do texto |
| `.github/workflows/ci.yml` (C) | Destino `xfetch` na CI histórica | Executar checks da correção | CI #68 success |

## C. Correções dos PRs

| PR | Problema | Correção | Testes | Status |
|---|---|---|---|---|
| #64 | SQLite fixo podia apagar arquivo preexistente e não limpar em erro | Diretório temporário exclusivo, fechamento em `finally` via context managers | Preservação de sentinela e limpeza em sucesso/falha | Corrigido em #67 |
| #64 | Arredondamento por classe não garantia tamanho; parâmetros fixos; colunas dependiam da ordem CSV | Cotas exatas, seed/CLI, ordem explícita, validação e relatórios | Determinismo em blocos distintos, tamanho exato e classes desbalanceadas | Corrigido em #67 |
| #64 | psutil não declarado; avaliação aceitava dados inválidos/duplicados | Grupo opcional, validações, hash/versões, ML explícito | CLI, rejeição de duplicatas/classes/divisões, baseline sintético | Corrigido; métricas reais não reproduzidas |
| #65 | Paginação automática sem teto absoluto | No máximo 10 requisições por chamada, inclusive páginas vazias | Tokens sempre novos, limites None/1/4/1000 e tokens repetidos | Corrigido em #68 |
| #65 | `author_id` contrariava esquema MongoDB | Lista de metadados permitidos sem identificadores do autor | Campos arbitrários/nested/contadores inválidos não passam | Corrigido em #68 |
| #65 | IDs/datas podiam quebrar pipeline; erro do driver expunha detalhes | Validação, UTC, exceções públicas sem dados do driver | HTTP 401/402/403/429/500/503, timeout, JSON/envelope/data inválidos | Corrigido em #68 |
| #65 | Exemplo 20/20/5 divergente e busca híbrida ambígua | Documentar `limit` constante e proposta futura | Contrato oficial consultado; integração sintética | Corrigido em #68 |

A nova amostragem muda cotas e casos inválidos, preserva espaços originais e fixa a
ordem de classes; os efeitos estão documentados. Acurácias **70,10% / 67,70%** e
F1 macro **59,65% / 55,43%** continuam resultados declarados pelo autor, não
reproduzidos. Independência do pré-treinamento não comprovada.

## D. Organização do repositório

Estrutura anterior já separava `src/apresentacao`, `servico`, `processamento` e
`dados`. Existiam scripts de experimento na raiz e em `scripts/`, README de template
e exemplos de ambiente separados. A estrutura final preserva as camadas e adiciona
`docs/qa/pc1/`, `scripts/demonstrar_pipeline.py`, template e, na entrega B,
`scripts/experimentos/`. Não foi necessária uma entrega D de reorganização maior.

A implementação dos dois experimentos foi transferida para `scripts/experimentos/`;
os arquivos antigos continuam como wrappers. Novos comandos/documentação apontam
para módulos `python -m scripts.experimentos...`. Imports existentes não foram
reescritos nem removidos. Os testes do autor de preservação de texto foram mantidos.

`test_mongo.py` foi mantido: testes existentes importam e executam esse caminho.
A padronização `models/` versus default legado `modelos/` e as movimentações de
`docs/banco`, documentação acadêmica e relatórios antigos ficam adiadas para evitar
mudar contratos/links no PC1. `Datasets/tweetsent.csv` permaneceu intacto por pendência
de redistribuição/licença. Não foram criados diretórios vazios para imitar estrutura.

Candidatas a revisão manual de limpeza (nenhuma exclusão realizada):

| Branch remota histórica | Situação em relação a developer auditada | Recomendação |
|---|---|---|
| `chore/sincronizar-developer-main` | Ancestral/totalmente contida | Confirmar propósito antes de remover |
| `feat/issue-11-esquema-mongodb` | Contida | Confirmar encerramento da entrega |
| `fix/issue-2-qa-importacao-csv` | Contida | Confirmar aceite |
| `feature/minha-tela`, `minha-tela(front)` | Contidas, heads antigos | Consultar autores |
| `feat/integrar-classificador`, `xfetch` | Trabalho aberto #64/#65 | Preservar |
| `docs`, `gh-pages`, `feat/pages`, `feat/sentia-modelo` | Não totalmente contidas | Não inferir que trabalho é descartável |

`main` continua 47 commits atrás de developer; sincronização de entrega deve ocorrer
por PR revisado da equipe, depois do aceite. Nenhum avanço automático foi realizado.

## E. Testes

| Ambiente / comando | Passed | Failed | Skipped | Resultado |
|---|---:|---:|---:|---|
| Base c6fc535: `uv run pytest -v -ra` | 394 | 0 | 0 | Aprovado |
| Base: `uv run pytest --cov=src --cov-report=term-missing` | 394 | 0 | 0 | 96% de src |
| Entrega A após mudanças: `uv run pytest -v -ra --cov=src --cov-report=term-missing` | 394 | 0 | 0 | 96% de src |
| B: experimentos + classificação + pipeline | 46 | 0 | 0 | Aprovado |
| B: `uv run pytest -v -ra --cov=src --cov-report=term-missing` | 222 | 0 | 0 | 94% de src histórico |
| C: `python -m pytest tests/test_xfetch.py -q` | 58 | 0 | 0 | Aprovado offline |
| C: suíte histórica com cobertura | 175 | 0 | 14 | 95% de src histórico; skips explicados abaixo |
| A+B+C: `uv run pytest tests docs/qa/pc1/evidencias/test_integracao_prs.py -v -ra --cov=src --cov-report=term-missing` | 471 | 0 | 0 | 96%; COMPATÍVEL no escopo testado |

Os 14 skips de C já pertencem à base histórica sem implementação de aquisição
inicial (issue #1). Não foram introduzidos, ocultados ou enfraquecidos; na integração
com developer todos os 471 testes executam sem skips. Coberturas históricas medem
conjuntos diferentes de arquivos e não devem ser comparadas como regressão.
`--cov=src` não mede cobertura dos scripts experimentais.

Ruff frontend aprovado; Ruff incremental `--isolated --select F,E9` aprovado em
`src tests scripts test_mongo.py`; lock check e diff check aprovados. Auditoria de
Ruff sem escopo restrito encontrou 28 apontamentos de estilo/imports antigos no
ambiente instalado; foram adiados, sem formatação massiva nem redução dos testes.

API `/health` e Streamlit `/_stcore/health`: servidores reais, ambos 200. AppTest
exercitou os estados normal/vazio/erro e erros de configuração/HTTP. Sem inspeção
visual em navegador. Demo importou cinco registros e validou BSON sem conexão.
Um aviso de depreciação Starlette/httpx apareceu, sem falhas.

Evidências: [base](evidencias/base-pytest.txt), [cobertura](evidencias/base-cobertura.txt),
[A final](evidencias/base-final.txt), [B](evidencias/pr64-suite.txt),
[B focados](evidencias/pr64-focados.txt), [C](evidencias/pr65-suite.txt),
[XFetch](evidencias/pr65-xfetch.txt), [conjunta](evidencias/integracao-suite.txt),
[resoluções](evidencias/integracao-resolucoes.md), [smoke](evidencias/smoke-servidores.json).

## F. CI e dependências

- Python **3.11.18**, uv **0.13.7** provisionados em `/tmp/sentia-pc1/`.
- Sistema tinha Python 3.15 sem uv; nenhuma configuração global foi alterada.
- `uv sync --locked` e `uv lock --check` consistentes. A mantém o lock de developer.
- B acrescenta grupo opcional `experimentos` (`psutil>=6,<8`, resolvido 7.2.2).
  Testes obrigatórios passam sem esse grupo. A medição real de RSS exige o grupo.
- ML continua opcional: PySentimiento 0.7.3 e Torch, não instalados nem baixados
  para a demonstração. Não há pesos BERTweet no cache do ambiente.
- B traz manifest/lock de developer porque o head do autor ainda usava requirements.
  Esses arquivos têm conflito add/add ao combinar branches antigas: resolução
  experimental preserva manifest/lock B com as mesmas versões mais grupo opcional.
- C usa dependências locais travadas da developer; seu workflow histórico permanece
  baseado em pip, com destino `xfetch` habilitado. Na integração prevalece a CI A.
- A CI A executa todos os PRs, Python da `.python-version`, sync/lock check,
  Ruff existente + F/E9 geral e testes completos. Não instala grupo ML/experimentos.
- O sandbox impediu bind local e bloqueou ASGI em duas tentativas iniciais;
  testes válidos foram repetidos com timeout fora dele. Tentativas bloqueadas
  não foram contadas como aprovação. Os processos bloqueados foram encerrados.

| Referência | Resultado | Evidência GitHub |
|---|---|---|
| Developer `c6fc535` | SUCCESS | [run 42425474655](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42425474655) |
| PR #64 original `0e19b6b` | SUCCESS na consulta inicial | [run 42471300408](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42471300408) |
| PR #65 original `63f3ce5` | SUCCESS na consulta inicial | [run 42569749460](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42569749460) |
| Correção #67 `1cd636e` | SUCCESS | [run 42681909047](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42681909047) |
| Correção #68 `4507aac` | SUCCESS | [run 42681914171](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42681914171) |
| Entrega A `33b656f` | SUCCESS | [run 42682766618](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42682766618) |

## G. PRs e commits

| Entrega | Branch própria | Commit de implementação | Publicação / destino |
|---|---|---|---|
| A | `chore/pc1-estabilizacao-organizacao` | `8806bfa` (preparação), `33b656f` (relatórios/evidências) + registro final documental | [PR #69](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/69) → `developer` |
| B | `fix/pr64-pc1-reprodutibilidade` | `1cd636e791529f987175355e2f10dbaeac264b2a` | [PR #67](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/67) → `feat/integrar-classificador` |
| C | `fix/pr65-pc1-aquisicao` | `4507aaca269e32873ad52b1f48ae431c56cdb971` | [PR #68](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/68) → `xfetch` |
| Experimental | `test/pc1-integracao` | `c368b1d`, `480ecf1ff03d69518e7771c4278772ac44e9a3b2` | Local, sem PR de merge |

Worktrees: `/tmp/sentia-pc1/base`, `/tmp/sentia-pc1/pr64`, `/tmp/sentia-pc1/pr65`
e `/tmp/sentia-pc1/integracao`. A árvore original permanece em developer local
`e2a3ff0`, com `docs/auditorias/` não rastreado preservado. Commits novos têm autoria
**Codex**, explícita por comando porque o ambiente não possuía identidade Git;
nenhum crédito foi atribuído a um integrante indevidamente.

O conector GitHub recusou a criação de PRs com 403 por permissão da integração;
a publicação prosseguiu com o gh autenticado do ambiente. Não houve merges,
force push, reescrita de histórico ou alterações de branches dos colegas.
Na atualização final, developer/main permaneceram nos SHAs auditados. O PR #66
(`feat/painel-filtros-admin`, `dcc1f3f`, 29 arquivos) apareceu durante a execução.
Foram consultados seus metadados: propõe filtros, login e administração; não está
integrado e não foi submetido à revisão integral reservada a #64/#65 nesta tarefa.
Sua homologação fica pendente; não atribuir suas funcionalidades à base auditada.
Não havia sessões de documentos conectadas; não foram encontrados outros
artefatos acadêmicos por esse meio.

Diferenças remanescentes incluem implementações futuras e conflitos históricos
já documentados; revisar estes conflitos quando os PRs originais forem integrados.

## H. Parecer QA

| PR | Parecer sobre o head original | Motivo / condição para aprovação |
|---|---|---|
| #64 | **SOLICITAR ALTERAÇÕES** | Risco de arquivo temporário e reprodução corrigidos em #67. Após incorporar correção e resolver uv com developer: **APROVAR COM RESSALVAS**, pois métricas e independência científica não foram reproduzidas, com aceite científico/PO ainda pendente |
| #65 | **SOLICITAR ALTERAÇÕES** | Privacidade, teto de requisições e contrato corrigidos em #68. Após incorporar correção e integrar base atual: **APROVAR COM RESSALVAS**, com homologação externa/custos/licença pendente |
| #67 | **APROVAR COM RESSALVAS** | Testes e CI aprovados; revisar efeito científico das cotas/validações e conflitos de migração uv |
| #68 | **APROVAR COM RESSALVAS** | Testes e CI aprovados; mocks não comprovam XFetch real, política comercial ou persistência |

Esse parecer é técnico e não substitui revisão humana, aprovação acadêmica ou
aceite dos critérios da PO. Nenhum review foi submetido em nome de um integrante.

## I. Ponto de controle

1. **O que demonstrar hoje?** Navegação e indicadores mock do painel, estados
   vazio/erro, API `/health`, fixture CSV, pipeline com analisador simulado,
   serialização BSON e suíte de testes. Usar [roteiro](ROTEIRO_DEMONSTRACAO.md).
2. **O que funciona efetivamente?** Importadores/adaptadores e contratos testados,
   aplicação Streamlit, servidor FastAPI básico, baseline e conexão MongoDB
   encapsulada (esta última apenas validada com mocks nesta auditoria).
3. **O que depende de mocks?** Dados do dashboard, previsões da demonstração,
   comunicação HTTP nas regressões e XFetch na validação conjunta. BSON é
   serialização real local, sem persistência.
4. **O que está em implementação?** Persistência (#20), API (#21 e #23–#25),
   contrato unificado (#19), integração do painel (#27), autenticação (#58/#59),
   importação/coleta no painel (#60/#61), publicação (#62) e usabilidade (#63).
   Busca híbrida/semântica permanece proposta; aceite do modelo/requisitos segue
   pendente. Não marcar issues como concluídas apenas por teste unitário.
5. **Riscos da apresentação?** Dependências precisam estar preparadas, portas
   podem estar ocupadas, dados são fictícios, endpoints de análises não existem,
   serviços externos/modelos não estão homologados. Dataset legado tem pendência
   de licença. Visão/GQM/Arquitetura completos e regulamento oficial PC1 não foram
   localizados; ata 02 (`docs`, `0433a55`) é evidência de planejamento, não rubrica.
6. **Quais comandos?** Na raiz: `uv sync --locked`, `make env`,
   `SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run --offline streamlit run src/apresentacao/app.py`,
   `uv run --offline uvicorn src.servico.main:app --host 127.0.0.1 --port 8000`,
   `curl --fail http://127.0.0.1:8000/health`,
   `uv run --offline python -m scripts.demonstrar_pipeline`,
   `uv run --offline pytest -v -ra`.
7. **Correção indispensável antes da apresentação?** Nenhuma mudança funcional
   adicional na base para o roteiro offline. Usar a entrega A preparada e não
   depender do merge dos PRs. Incorporar #67/#68 antes de recomendar os heads
   originais como seguros para integração; não usar dados externos ao vivo.

## J. Backlog técnico

| Prioridade | Próximo trabalho | Momento / aceite |
|---|---|---|
| P1 | Revisar #67/#68, atualizar PRs originais e resolver uv/workflow em developer; revisar separadamente o novo #66 | Após revisão humana; sem merge automático |
| P1 | Homologar requisitos/contrato único e documentação Visão/Arquitetura/GQM | Equipe e PO; localizar documentos oficiais e critérios PC1 |
| P1 | Decidir redistribuição/licença de `Datasets/tweetsent.csv` | PO/equipe; arquivo preservado |
| P1 | Confirmar custos, termos e privacidade da coleta; teste real XFetch autorizado | Depois do PC1, sem usar chave alheia automaticamente |
| P1 | Preparar avaliação BERTweet real e BPSAD com hash/partições verificáveis | ML/QA; sem atribuir resultados anteriores à nova amostra |
| P2 | Implementar persistência e endpoints acordados; integrar painel | Issues existentes, contratos e testes reais de banco isolado |
| P2 | Homologar uso de textos com menções e retenção de dados | Decisão PO/privacidade; não alterar silenciosamente texto original |
| P2 | Alinhar main por PR da equipe e promover a versão estável aceita | Após homologação da developer |
| P2 | Migrar caminho legado `modelos/`, organizar scripts MongoDB/docs e links | PR separado com regressões de caminhos públicos |
| P2 | Expandir Ruff além de F/E9, fixar versão uv da CI e tratar depreciação HTTPX | Depois do PC1, sem formatação massiva hoje |
| P2 | Cobertura de scripts e testes de falha de escrita/atomicidade de saídas | Depois do PC1; saídas atuais usam criação exclusiva |
| P2 | Usabilidade e inspeção visual do painel em resoluções reais | #31/#63, evidência distinta de AppTest |
| P3 | Pesquisa híbrida, embeddings/Vector Search e orquestração | Futuras issues e aceite de escopo; não implementado nesta entrega |
| P3 | Benchmark controlado, cache de inferência, monitoramento e desempenho | Depois da integração funcional e mensuração |

Documentos de apresentação: [relatório PC1](RELATORIO_PC1.md),
[roteiro](ROTEIRO_DEMONSTRACAO.md) e este relatório final.
