# Plano de testes atual para inspeção

Data: **14/11/2026**. Base B: `developer`,
`1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. Plano proposto para revisão da
equipe/PO; resultados são os do [relatório de execução](RELATORIO_EXECUCAO.md).
Não constitui encerramento de Sprint nem homologação do produto.

## 5W1H e sincronização com o planejamento

| Pergunta | Definição operacional |
|---|---|
| What / o quê | Verificar contratos, aquisição/importação, classificação/pipeline, banco, API, autenticação/administração e UI; manter T01–T18 com RF/US, nível, limitações e execução na [matriz](MATRIZ_RASTREABILIDADE.md). |
| Why / por quê | Detectar defeitos antes da integração; demonstrar critérios aplicáveis sem apresentar mock como serviço externo nem cobertura de código como qualidade do modelo. Atende aos itens de definição/execução/correção da seção de testes do formulário do professor. |
| Who / quem | Autor mantém testes de unidade; QA Renato/Figueirin revisa evidências (#4/#10/#22/#26/#32); ML Ricardo/Gabriel prepara pesos e avaliação (#85); banco Maria/Julia (#20); frontend Juliana com revisão de Hellen (#27/#31). Dono de API e responsáveis não definidos nas issues devem ser ratificados no Planning; PO aceita funcionalidade/escopo. |
| When / quando | Em cada PR e push em main/developer, conforme CI. Antes da Review, executar cenários integrados disponíveis; repetir área afetada por correção. ML real em candidato de modelo/amostra; inspeção visual em versão de UI. Não encerrar Sprint 5 (10–16/11) em 14/11; T11–T13 estão nessa Sprint (#26). T14–T17 pertencem à Sprint 6 (17–23/11), conforme #32. |
| Where / onde | Local Linux, Python 3.11, uv.lock; CI ubuntu-latest com mongo:7 descartável. ML real exige grupo ml/pesos, hardware e versões registrados; XFetch vivo exige autorização de custo. Serviço de teste nunca deve apontar a banco de produção. |
| How / como | pytest, pytest-cov, Ruff, FastAPI TestClient, Streamlit AppTest, mocks/fixtures e MongoDB isolado; cenários manuais para navegador/serviços reais. Guardar SHA, comando, ambiente e PASS/FAIL/ERROR/SKIP; obter revisão antes de qualquer decisão de integração. |

Esforço/custo de execução planejado: **N/D** (sem estimativa aprovada). Tempo de
suíte é uma observação de execução, não uma estimativa de trabalho. Nenhuma coleta
paga ou deploy público faz parte desta execução.

## Níveis, tipos, técnicas e limites

| Grupo | Nível / tipo | Técnica e ferramentas | Oráculo e limite |
|---|---|---|---|
| Aquisição/CSV/adaptadores | Unidade e integração local de módulos; funcional/robustez | Partições de equivalência, limites, tabelas de decisão para rótulos, pytest parametrizado e tmp_path | Fixtures UTF-8 válidas/vazias/corrompidas, campos e descartes conhecidos; não comprova upload por UI nem corpus completo. |
| Classificador/pipeline | Unidade/contrato e integração de módulos; funcional/regressão | Analisador espião, injeção de falhas, testes de propriedades específicas (ordem/lote/preservação), BSON.encode | Texto, probabilidades, identidade, datas e saída esperados; o analisador falso não mede acurácia nem tokenizador real. |
| Experimentos/baseline | Unidade e integração offline; reprodutibilidade | Corpus sintético, seed, diferentes blocos, CLI, deduplicação, teste negativo de vazamento | Cotas exatas e partições disjuntas; treina baseline real pequeno, sem avaliação de generalização no BPSAD completo. |
| MongoDB | Unidade de validação + integração real de persistência | Fixtures de coleção/banco descartáveis, inserção/leitura, duplicação, filtros e erros | Documentos conhecidos e índices consultáveis; BSON.encode sozinho não substitui CRUD/validator do servidor. |
| API | Integração em processo/contrato; funcional, tratamento de erros e autenticação | TestClient contra app real, dependências substituídas, limites e combinações de filtros | Códigos HTTP, OpenAPI e JSON; coleção/pipeline simulados não comprovam servidor HTTP separado nem caminho completo com ML/MongoDB. |
| Administração/UI | Componente e integração em processo; funcional/negativo | AppTest, cliente real conectado ao TestClient em alguns cenários, HTTP falso nos demais | Login, sessão, upload/coleta, estados e indicadores; servidor/pipeline/banco têm substitutos. Não é teste em navegador nem auditoria completa de segurança. |
| ML real | Avaliação empírica em dataset identificado e smoke de inferência | Scripts versionados, partição congelada, matriz e medidas por classe, reprodução independente | Rótulo humano como referência; calcular acurácia/F1 separadamente. Sem dados/modelo reais, marcar NÃO EXECUTADO. |
| Ponta a ponta / usabilidade | Sistema e aceitação; funcional/visual/responsividade | Navegador, API em processo separado, banco isolado, pesos reais e cenários conhecidos | PO compara resultados e usabilidade; exigir evidências e registro de dados/ambiente. Não inferir de AppTest. |

A cobertura de linhas limita-se a `src`. Scripts de experimento têm testes, mas
não estão incluídos no denominador `--cov=src`. Nenhum limiar de cobertura novo é
criado neste documento. Falhas, erros e skips são classificados individualmente.

## Reconciliação de T04–T08 com o modelo adotado

A [issue #10](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/10)
e a [#86](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86)
registram que T04–T07 e RF03–RF06 devem acompanhar o replanejamento de 29/10.
A proposta abaixo não altera retroativamente os PDFs históricos:

- **T04 / RF03:** validar que o texto original chega intacto ao adaptador,
  inclusive URLs, menções, emojis, acentos e pontuação. A limpeza mínima do
  baseline é testada separadamente, sem impor a transformação ao BERTweet.
- **T05 / RF04:** preservar stopwords/negações no caminho BERTweet; há teste
  explícito de negações. A decisão da [ADR-001](../../decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md)
  precisa de conciliação/ratificação acadêmica; não declarar aprovação inexistente.
- **T06 / RF05:** verificar ausência de stemming externo no BERTweet. Os testes
  de preservação com espião cobrem o encaminhamento do texto; não executam o
  tokenizador do checkpoint real.
- **T07 / RF06:** a representação do BERTweet é interna ao modelo. TF-IDF é
  usado no baseline com treino e teste separados; não é etapa obrigatória antes
  do BERTweet. Testes de configuração/lote simulam `create_analyzer`.
- **T08 / RF07 / US07:** a Visão v1.0.0, p. 37, confirma classificação de
  sentimentos com pré-condição histórica de modelo .pkl e texto vetorial. O
  adaptador atual usa checkpoint BERTweet. Verificar rótulos e probabilidades
  com espião testa software; avaliação independente RNF01/US08 testa qualidade
  real. A migração de pré-condição precisa de revisão formal, sem converter
  exemplos sintéticos em comprovação de acurácia.

T01–T18 têm uma linha própria na matriz, confrontada com a Visão v1.0.0,
seção 6.2, pp. 35–39: **T01 coleta**, **T02 importação**, T08 classificação
e T18 responsividade. T18 usa C06/RNF02 no roteiro, mas C06/RF02 no backlog
(p. 27); confirmar a divergência com PO. T11–T13 históricos requerem observação
pela UI; contratos de API isolados são cobertura parcial, não aceite integral.
A estratégia histórica (pp. 33–34) chama streamlit.testing de end-to-end e
prevê PR para main; este plano distingue AppTest de navegador/serviços reais e
registra o workflow observado em B: qualquer pull_request e pushes main/developer.

## Ambiente e reprodução

Na raiz, com Python da `.python-version` e uv instalado:

```bash
uv sync --locked
uv lock --check
make lint
uv run pytest -ra --cov=src --cov-report=term-missing
```

O [relatório](RELATORIO_EXECUCAO.md) registra os prefixos UV usados para isolar
cache e ambiente em `/tmp`, sem modificar dependências. Não foi criado `.env`.
As suítes reais de banco têm comportamento distinto:

- `tests/test_repositorio.py` usa `mongodb://localhost:27017`, banco fixo
  `sentia_teste_repositorio`, apagado antes/depois. `SENTIA_TESTES_SEM_MONGODB=1`
  pula esses testes; sem banco também pula, inclusive se CI estiver definido.
- `tests/test_persistencia_leitura.py` lê `MONGODB_URI_TESTE`, cria banco aleatório
  `sentia_teste_<id>` e o apaga ao final. Sem banco pula localmente, mas **falha
  se CI estiver definido**. A variável acima não desativa esta segunda suíte.
- O workflow configura `mongo:7` e `MONGODB_URI_TESTE` local. Para reprodução
  integrada, reservar instância descartável exclusivamente para testes; a fixture
  de repositório não consome a URI configurável da outra suíte.

ML real requer `uv sync --locked --group ml --group experimentos` e dados locais
com proveniência; consultar [experimentos](../../experimentos_bpsad.md). A opção
`--bertweet` habilita os pesos reais; sem ela o script avalia somente baseline.
A instalação padrão e CI não instalam o grupo ml. XFetch real não foi acionado;
os testes substituem HTTP e não usam créditos.

## Entrada, saída e tratamento de defeitos

**Entrada:** SHA/base identificados, dependências travadas, fixtures/dados conhecidos,
oráculos definidos, ambiente sem dados de produção, MongoDB disponível para os
casos reais. Mudanças de escopo T04–T08 e metas são propostas até ratificação.
Para avaliação científica, exigir hash/amostragem/revisões e autorização dos dados.

**Saída técnica por grupo:** nenhum FAIL/ERROR não resolvido; PASS/FAIL/ERROR/SKIP
publicados com ambiente e limitações; skips não contam como aprovação. Ausência
de serviço pode permitir concluir o grupo offline, mantendo integração pendente.
Saída de aceitação exige cenário real e aceite explícito da PO; não é consequência
automática de CI verde. T15–T17 não implementados não recebem PASS.

**Após defeito:** registrar cenário, saída observada, localização, teste e SHA;
vincular PR corretivo e repetir o teste relevante. Ampliar para suíte completa
quando integração justificar. Exemplos rastreáveis: [defeitos](DEFEITOS_E_CORRECOES.md).

**Critérios de suspensão/retomada:** ambiente incompatível, falha de coleta,
dados sem identificação ou serviço real indisponível suspendem somente os grupos
dependentes. Retomar após corrigir a causa e registrar novo comando/resultado,
preservando a tentativa anterior. Nenhuma evidência histórica substitui tentativa
local não executada.

## Pendências para o planejamento

Obter Mini-tarefa GQM separada e pacote de pré-inspeção; confirmar conflito RF02/RNF02 em T18; ratificar
roteiros T04–T07, meta RNF01 e responsáveis; revisar PRs #83/#89 ainda abertos;
reproduzir #85; demonstrar fluxo com MongoDB e pesos reais; concluir/revisar
T14–T17 conforme Sprint 6; executar inspeção visual/responsividade da #31.
Não alterar prioridade, Sprint ou requisito por inferência desta inspeção.
