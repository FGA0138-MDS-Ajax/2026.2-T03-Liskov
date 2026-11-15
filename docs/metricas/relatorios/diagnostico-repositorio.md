# Diagnóstico estrutural do repositório SentIA

**Projeto:** SentIA — Grupo Liskov, T03, MDS/UnB-FGA  
**Branch analisada:** `developer`  
**Commit de referência:** `b91c7a5e4af972d98da6e5ded70b2243d60f5513` (merge do PR #96)  
**Data do corte:** 15/11/2026  
**Escopo:** organização estrutural e documental. O PR #96 foi considerado concluído e está fora do escopo de alteração.

> Este diagnóstico foi elaborado a partir da árvore Git e da leitura dos arquivos disponíveis remotamente na branch indicada. Não foi feito checkout nem execução local do projeto. Portanto, referências a uso dinâmico, estado local, dependências de ambiente e resultados de testes precisam ser confirmadas no clone antes de qualquer exclusão ou declaração de conclusão.

## 1. Inventário resumido

A árvore recursiva da branch `developer` contém **212 entradas** (arquivos e diretórios), sem truncamento na resposta do GitHub.

| Área | Conteúdo observado | Avaliação inicial |
|---|---|---|
| `.github/` | Template de PR e workflow `ci.yml` | Estrutura pequena e objetiva; preservar o workflow de testes. |
| `.streamlit/` | `config.toml` | Configuração específica da interface; localização apropriada. |
| `Datasets/` | `tweetsent.csv` e cinco CSVs de demonstração em `datasets_demo/` | Dados versionados com propósito aparente de aquisição/demonstração. Não remover nem mover sem verificar tamanho, licença, uso e fluxo de execução. |
| `docs/` | 65 arquivos, entre Markdown, JSON, TXT e PNG, distribuídos em áreas de banco, decisões, frontend, gestão, inspeção, métricas, QA, revisão acadêmica e resultados BPSAD | Há uma hierarquia temática existente. O problema principal é atualização e descoberta, não ausência de organização. As imagens existentes estão em `docs/frontend/wireframes/` e são wireframes; não foram confirmadas capturas de tela atuais da aplicação. |
| `models/` e `notebooks/` | Diretórios sem arquivos listados na árvore analisada | Verificar se são placeholders intencionais. Não criar conteúdo vazio nem removê-los sem confirmação da equipe. |
| `scripts/` | Scripts operacionais e experimentais; experimentos BPSAD agrupados em `scripts/experimentos/` | Organização razoável. Há wrappers de compatibilidade na raiz/nível superior. |
| `src/apresentacao/` | Aplicação Streamlit, páginas, seções, componentes, clientes HTTP e fontes mock | Responsabilidade bem delimitada. |
| `src/servico/` | FastAPI, administração, autenticação, dependências, esquemas e pesquisa | Responsabilidade bem delimitada; API permanece na camada de serviço. |
| `src/processamento/` | Aquisição, classificação e pipeline | Separação funcional adequada. O pacote `preprocessamento/` contém somente `__init__.py`, sem implementação própria visível. |
| `src/dados/` | `database.py` e `repositorio.py` | Camada de dados centralizada. `repositorio.py` concentra muitas operações (1.219 linhas) e merece atenção futura, mas dividi-lo não é uma limpeza documental simples. |
| `tests/` | `conftest.py`, fixtures e 29 módulos `test_*.py` | Testes estão agrupados por assunto no nome, mas permanecem em um único diretório. Não há subpastas unitários/integração/sistema. |
| Raiz | `README.md`, `CHANGELOG.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `pytest.ini`, exemplos de ambiente e `.gitignore` | Configuração principal usa `uv`; não há `requirements.txt`/`requirements-dev.txt` na branch analisada. |

## 2. Estrutura de código observada

A organização física atual já representa as quatro camadas do produto, sem exigir uma nova camada `src/api/`:

```text
src/
├── apresentacao/                 # Streamlit
│   ├── fontes/                   # Clientes API e implementações mock
│   ├── paginas/                  # Dashboard e Administração
│   └── secoes/                   # Partes reutilizáveis da interface
├── servico/                      # FastAPI, rotas, autenticação e coordenação
├── processamento/
│   ├── aquisicao/                # CSV, TweetSentBR, BPSAD, XFetch e auditoria
│   ├── classificacao/            # BERTweet, baseline, rótulos e avaliação
│   └── pipeline.py               # Orquestra o processamento em lote
└── dados/                        # Conexão MongoDB e repositório
```

A API é parte da camada `servico` (`src/servico/main.py`), não um pacote independente. A persistência posterior ao PR #96 está concentrada em `src/dados/database.py` e `src/dados/repositorio.py`; não foi encontrada uma camada física `src/persistencia/` na árvore atual.

### Responsabilidades confirmadas pelos caminhos e código consultados

- **Apresentação:** `src/apresentacao/app.py` monta a navegação Streamlit e seleciona os modos `mock` ou `api`. Os clientes HTTP estão em `fontes/`; páginas e seções não devem importar a camada de dados diretamente.
- **Serviço:** `src/servico/main.py` expõe `/health`, `/analises` e `/analises/resumo`, além de incluir o roteador administrativo. Coordena pipeline e repositório por dependências.
- **Processamento:** `src/processamento/aquisicao/` reúne adaptadores/importadores e coleta; `pipeline.py` coordena classificação; `classificacao/` reúne BERTweet, baseline, avaliação e rótulos.
- **Dados:** `RepositorioAnalises` centraliza leitura/gravação de análises, registros, datasets e cache de pesquisas no MongoDB.

## 3. Configuração, execução e automação

| Elemento | Estado observado |
|---|---|
| Python | `.python-version` e `pyproject.toml`; o README declara Python 3.11. |
| Dependências | `pyproject.toml` + `uv.lock`; grupos `dev`, `ml` e `experimentos`. |
| Ambiente | `.env.example` e `.env.frontend.example`; não inserir segredos nos exemplos. O segundo repete um subconjunto de variáveis do primeiro e pode ser mantido como exemplo específico do frontend, desde que seu uso seja documentado. |
| Testes | `pytest.ini` define `testpaths = tests` e `pythonpath = .`. |
| Atalhos | `Makefile` oferece setup, execução do painel, API, lint, testes, check e demo. |
| CI de `developer` | `.github/workflows/ci.yml` provisiona `mongo:7`, executa `uv sync --locked`, verifica lock, Ruff e Pytest com cobertura. |
| MkDocs | **Não existe `mkdocs.yml` na branch `developer` analisada.** A configuração está na branch separada `docs`. |
| Infraestrutura Docker | Não foram encontrados `Dockerfile` nem `docker-compose.yml` na árvore de `developer`. A CI usa um serviço MongoDB declarado no próprio workflow. |
| PDFs | Não foram encontrados arquivos `.pdf` rastreados na branch `developer` nem na árvore consultada da branch `docs`. |

## 4. Problemas e divergências identificados

### 4.1 Documentação técnica defasada

1. `docs/arquitetura.md` se intitula **“Arquitetura Observada no PC1”** e descreve um estado antigo: API limitada a `/health`, rotas de análises pendentes e persistência CRUD pendente. Isso contradiz o código atual, o README da branch e a integração pós-PR #96.
2. `tests/README.md` ainda se apresenta como documentação da suíte da Sprint 1 / Issue #4, descreve apenas um subconjunto antigo de arquivos e afirma execução 100% offline. A suíte atual contém 29 módulos de teste e a CI provisiona MongoDB real para os testes que dependem do banco.
3. A página inicial do portal (`docs/index.md`, branch `docs`) contém afirmações anteriores ao PR #96: diz que datasets, corpus e pesquisa híbrida operam em memória e referencia `src/persistencia`, caminho ausente da árvore atual. Após o PR #96, a persistência de datasets, registros e pesquisas está concentrada no repositório MongoDB; sessões e estados transitórios de jobs continuam em memória.
4. `docs/README.md` e a navegação do MkDocs ainda identificam o PR #93 como aberto, embora ele esteja integrado à branch `docs` (merge commit `d7b90ee2b1eb2e68845b21c875db4dac390ee06c`).
5. O README principal já descreve o estado pós-PR #96, mas ainda apresenta uma linha de base histórica `1723a7d` e um corte de 14/11. Deve-se distinguir explicitamente a data do retrato documental do HEAD mais recente (`b91c7a5`).
6. `docs/gestao/GESTAO_CONFIGURACAO.md` ainda lista `src/persistencia/` como parte de `src/` na tabela IC-01 e usa o corte `1723a7d`/`0433a55` anterior aos merges mais recentes. O catálogo de itens de configuração precisa ser atualizado para refletir `src/dados/` como camada de persistência atual e a situação mais recente das branches.
7. `docs/alteracoes_armazenamento_memoria.md` já documenta corretamente a transição histórica e o estado canônico pós-PR #96. É material explicativo útil e deve ser mantido, não removido como obsoleto.

### 4.2 Documentos concorrentes ou sobrepostos

- `README.md` é a entrada principal e `docs/README.md` funciona como índice técnico. Essa dupla é válida, desde que o primeiro apresente e o segundo catalogue; não são duplicatas a excluir.
- `docs/inspecao/MATRIZ_EVIDENCIAS.md` e `docs/revisao-academica/MATRIZ_DIVERGENCIAS.md` têm formato de matriz, mas finalidades distintas (evidência de inspeção versus divergências entre documentos acadêmicos). Não consolidar automaticamente.
- `docs/frontend/README.md`, `tests/README.md` e `docs/README.md` possuem escopos diferentes. O README de testes precisa de atualização, não de exclusão.
- Os documentos acadêmicos em `docs/revisao-academica/` são explicitamente rascunhos/reconciliações. Não substituem os PDFs acadêmicos formais aprovados, que a gestão do projeto registra como externos ao Git público por conterem dados pessoais/anotações docentes.

### 4.3 Duplicidade exata confirmada

- `docs/qa/pr44-pr45/merge-a.txt` e `docs/qa/pr44-pr45/merge-b.txt` têm conteúdo byte a byte idêntico na branch analisada.
- `docs/qa/pr44-pr45/suite-final-a.txt` e `suite-final-b.txt` têm o mesmo tamanho, mas **não** são idênticos; manter separados até compreender sua proveniência.

A igualdade de dois arquivos de evidência não prova, sozinha, que uma das cópias possa ser apagada: os sufixos `a` e `b` podem representar execuções/participantes distintos. Conferir referências e significado histórico antes de consolidar.

### 4.4 Arquivos que parecem redundantes, mas possuem função

- `amostrar_bpsad.py` na raiz delega para `scripts.experimentos.amostrar_bpsad.main` e declara compatibilidade. Não é uma segunda implementação.
- `scripts/validar_bpsad.py` também funciona como wrapper para `scripts/experimentos/validar_bpsad.py`.
- Os scripts experimentais usam caminhos padrão relativos ao diretório de trabalho, por exemplo `data/BPSAD/...`; seus comandos devem ser documentados a partir da raiz do repositório ou os caminhos devem ser resolvidos explicitamente em uma tarefa posterior. Não é necessário alterar isso nesta entrega documental.
- `test_mongo.py` é um utilitário manual de verificação de conexão/ping MongoDB; não equivale aos testes automatizados `tests/test_database.py`, `tests/test_repositorio.py` e `tests/test_persistencia_leitura.py`.

Esses arquivos devem ser mantidos até que se decida descontinuar os comandos antigos e se confirme que não há consumidores externos.

## 5. Documentação acadêmica e artefatos

A árvore atual contém uma frente de revisão acadêmica em Markdown (`VISAO_ATUALIZADA_RASCUNHO.md`, `ARQUITETURA_ATUALIZADA_RASCUNHO.md`, matriz de divergências, revisão ABNT, decisões da PO e relatório). A árvore examinada não contém os PDFs formais da Visão e da Arquitetura. A própria `docs/gestao/GESTAO_CONFIGURACAO.md` registra que os PDFs acadêmicos base ficam **fora do Git público** porque contêm matrículas universitárias completas e anotações de correção docente; as revisões rastreáveis ficam em Markdown no repositório. Portanto:

- Essa ausência é intencional e alinhada à proteção de dados, não um arquivo esquecido a ser adicionado ao repositório público.
- Não criar PDFs substitutos nem tratar os rascunhos Markdown como versões aprovadas.
- Não versionar PDFs com matrículas ou anotações pessoais/docentes.
- Preservar os relatórios de avaliação, matrizes, evidências e resultados históricos; seus valores estão vinculados a datas, datasets e SHAs específicos.

A documentação consultada não fornece uma lista nominal única e atualizada de integrantes com responsabilidades individuais verificáveis. Os registros usam responsabilidades por frente (UI, API, ML, Banco, Dados, QA e coordenação). O README preparado mantém, portanto, apenas a identificação institucional do grupo; não atribui cargos nem contribuições individuais sem evidência.

## 6. Estrutura proposta

A recomendação é **manter quase toda a estrutura física atual** e melhorar os pontos de entrada e documentação desatualizada. Uma reorganização ampla de `src/` ou `tests/` não apresenta benefício proporcional ao risco.

```text
SentIA/
├── .github/workflows/ci.yml
├── .streamlit/
├── Datasets/
├── docs/
│   ├── README.md                 # índice técnico completo
│   ├── arquitetura.md            # arquitetura atual, não fotografia PC1
│   ├── banco/
│   ├── decisoes/
│   ├── frontend/
│   ├── gestao/
│   ├── inspecao/
│   ├── metricas/
│   ├── qa/
│   ├── resultados_bpsad/
│   ├── revisao-academica/
│   └── relatorios/
│       ├── diagnostico-repositorio.md
│       └── plano-de-organizacao.md
├── scripts/
│   └── experimentos/
├── src/
│   ├── apresentacao/
│   ├── servico/
│   ├── processamento/
│   └── dados/
├── tests/
│   ├── fixtures/
│   └── test_*.py
├── Makefile
├── pyproject.toml
├── pytest.ini
├── README.md
└── uv.lock
```

Essa proposta não cria `src/api/`, `src/persistencia/`, subpastas artificiais de testes ou pastas documentais vazias. O portal MkDocs segue na branch `docs` até que a equipe decida unificar os fluxos.

## 7. Recomendações por prioridade

| Prioridade | Ação | Motivo | Risco |
|---|---|---|---|
| Alta | Atualizar `docs/arquitetura.md` para o estado pós-PR #96, preservando a fotografia do PC1 como histórico | Hoje o documento contradiz a implementação | Médio; links e alegações precisam ser conferidos. |
| Alta | Atualizar `tests/README.md` para a suíte atual | A descrição não representa os testes atuais nem o requisito MongoDB da CI | Baixo a médio. |
| Alta | Corrigir `docs/index.md` e status do PR #93 na branch `docs` | Portal publicado está desatualizado em relação a `developer` | Médio; push em `docs` dispara `mkdocs gh-deploy --force`. |
| Alta | Criar este diagnóstico e o plano em `docs/relatorios/` | Entrega explicitamente pedida na tarefa | Baixo. |
| Média | Enxugar o README principal e manter o catálogo detalhado em `docs/README.md` | Separar apresentação de navegação documental | Médio; preservar links e comandos reais. |
| Média | Avaliar a consolidação de `merge-a.txt`/`merge-b.txt` | Duplicidade byte a byte confirmada | Médio; conferir proveniência antes da remoção. |
| Baixa | Avaliar diretórios sem conteúdo e pacote `preprocessamento/` | Podem ser placeholders | Baixo, desde que não sejam usados por ferramentas externas. |
| Fora desta tarefa | Dividir `src/dados/repositorio.py` ou `src/servico/administracao.py` | Seria refatoração de código e aumentaria o escopo | Alto. |

## 8. Riscos e cuidados de movimentação

1. **Duas branches de finalidade diferente:** `developer` contém a CI de testes do produto em `.github/workflows/ci.yml`; `docs` contém um workflow com o mesmo caminho, mas que publica MkDocs em `gh-pages`. Não mesclar integralmente uma branch na outra sem reconciliar esse arquivo.
2. **MkDocs não faz parte da árvore de `developer`:** validar o portal na branch `docs`, não presumir que `mkdocs build` funcionará a partir do checkout de `developer` sem trazer deliberadamente a configuração e as páginas necessárias.
3. **Testes:** `pytest.ini` aponta para `tests`. Mover arquivos pode alterar descoberta, imports, fixtures e configuração; preservar a estrutura plana nesta etapa.
4. **Caminhos dos datasets:** `Datasets/` (D maiúsculo) é rastreado, enquanto `data/` minúsculo é ignorado pelo `.gitignore` e usado como destino local/experimental. Não normalizar a capitalização sem atualizar scripts e referências.
5. **Wrappers de compatibilidade:** remover ou mover exige manter comandos documentados e consumidores externos.
6. **Evidências:** arquivos TXT/JSON de QA e BPSAD fazem parte da rastreabilidade de execuções. Tamanho, idade ou semelhança de nome não justificam exclusão.
7. **Persistência:** não tocar na camada unificada introduzida pelo PR #96.

## 9. Validações ainda necessárias no clone

As seguintes ações não foram executadas nesta análise remota e devem ser realizadas depois de aplicar as alterações na branch nova:

```powershell
uv sync --locked
uv run ruff check src/apresentacao tests/test_painel_*.py
uv run ruff check --isolated --select F,E9 .
uv run pytest -ra --cov=src --cov-report=term-missing
uv lock --check
git diff --check
git status
git diff --stat
```

Para testes que dependem do MongoDB, configurar `MONGODB_URI_TESTE` e executar com um MongoDB compatível. A CI da branch `developer` provisiona `mongo:7`.

No checkout da branch `docs`, validar separadamente a configuração e as páginas MkDocs; lembrar que o workflow dessa branch publica em `gh-pages` quando há push.

## 10. Conclusão

A base de código está mais organizada do que a documentação sugere. As quatro camadas principais já estão representadas; a tarefa deve priorizar a atualização dos documentos que ficaram para trás, a criação do diagnóstico formal, o fortalecimento do README e a atualização do portal. Não há evidência suficiente para justificar exclusões amplas ou movimentações de módulos Python. A recomendação é uma entrega incremental, sem alterações funcionais e com preservação das evidências históricas.
