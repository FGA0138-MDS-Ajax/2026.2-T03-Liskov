# SentIA

O SentIA é uma plataforma em desenvolvimento para analisar sentimentos em textos
em português e apoiar a compreensão de publicações sobre temas de interesse.
Classifica conteúdos como positivos, negativos ou neutros e prevê a apresentação
consolidada em um dashboard. Projeto da equipe **T03 Liskov**, disciplina de
Métodos de Desenvolvimento de Software (MDS), **UnB/FGA, 2026.2**.

**Referência deste PC1 — 09/11/2026:** esta documentação deriva da integração
experimental `test/pc1-integracao-frontend-atualizado`, SHA
`bfaf7da4437493f5ee9b44022d4979623b232add`. Ela combina a preparação do
[PR #69](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/69)
(`b9d8326`) e o frontend da Clicia do
[PR #70](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/70)
(`61926fe`), mais a correção de ensaio `bcd75e7`. Ambos estão abertos no corte consultado. **O frontend #70 existe
nesta integração, mas ainda não está integrado à `developer`**, cujo SHA remoto
consultado é `c6fc535`. A branch `docs-pc1-documentacao-consolidada` altera só documentação.

## Funcionalidades e estado real

| Situação | Entregas e limites |
|---|---|
| Implementadas e testadas na referência | Importador CSV, aquisição local TweetSentBR, adaptador BPSAD, auditoria de datasets, pipeline em lote, adaptador BERTweet, baseline TF-IDF + regressão logística e `GET /health` |
| Disponíveis com mocks | Dashboard, filtros de período/sentimento, indicadores, estados vazio/erro, login, sessão/logout e administração de exemplo; analisador da demo; testes de conexão MongoDB e clientes HTTP |
| Implementadas em PR aberto | #70: filtros e administração simulada, presentes nesta integração. #69: preparação offline, também presente. [#64](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/64): experimentos BPSAD; [#65](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/65): XFetch; os dois últimos **ausentes desta referência** |
| Em desenvolvimento no backlog | Contrato único #19, persistência #20, API #21/#23–#25, dashboard integrado/listagem #27, gráficos #28, resumo #29 e autenticação real #58; existência de issue não comprova progresso de implementação |
| Planejadas | Publicação #62, usabilidade #63, nuvem de palavras opcional #30 e pesquisa híbrida MongoDB + XFetch |

Código testado não encerra automaticamente requisitos nem comprova aceite da PO.
Veja a [matriz de rastreabilidade](docs/qa/pc1/MATRIZ_RASTREABILIDADE.md) e o
[status das entregas](docs/qa/pc1/STATUS_ENTREGAS.md).

## Arquitetura

| Camada | Implementação | Fronteira atual |
|---|---|---|
| Apresentação | Streamlit em `src/apresentacao/` | Fontes mock ou clientes HTTP; sem acesso direto ao banco/ML |
| Serviço | FastAPI em `src/servico/main.py` | Apenas `GET /health`; documentação OpenAPI automática |
| Processamento e aquisição | `src/processamento/` | CSV/TweetSentBR/BPSAD → `PipelineClassificacao` → documentos em memória |
| Classificação | BERTweet via PySentimiento | Preserva texto; tokenização do modelo; dependências ML opcionais |
| Baseline | TF-IDF + regressão logística | Alternativa isolada; ajuste do vetorizador só no treino |
| Dados | PyMongo em `src/dados/database.py` | Conectar, ping e fechar; esquema definido, sem CRUD de análises |

O fluxo pretendido é aquisição → classificação → MongoDB → API → dashboard.
Hoje, a demo do pipeline e o painel mock são fluxos separados. O contrato HTTP
preparado pelo frontend é uma **proposta**, não uma lista de rotas já entregues.
Detalhes: [arquitetura observada](docs/arquitetura.md),
[contratos de dados](docs/contratos-dados.md) e
[contrato HTTP](docs/frontend/CONTRATO-API.md).

## Instalação

Requisitos: Git, Python **3.11** para reproduzir o ambiente validado e
[uv](https://docs.astral.sh/uv/getting-started/installation/) instalado.
`.python-version` seleciona 3.11; `pyproject.toml` aceita Python >=3.11.

```bash
git clone https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov.git
cd 2026.2-T03-Liskov
git switch docs-pc1-documentacao-consolidada
uv sync --locked
make env
```

O `uv` pode provisionar o Python; o primeiro preparo requer rede ou cache completo.
`make env` cria `.env` a partir de `.env.example` e preserva arquivo existente.
Sem `make`, crie o arquivo com
`uv run python -c "from pathlib import Path; p=Path('.env'); p.exists() or p.write_bytes(Path('.env.example').read_bytes())"`.
Edite-o localmente sem publicar segredos. Variáveis exportadas prevalecem sobre
`.env`. `.env.frontend.example` é uma referência alternativa apenas do painel.
O modo offline de apresentação dispensa credenciais, MongoDB e pesos de ML.

## Execução

Na raiz, painel em um terminal:

```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run --offline streamlit run src/apresentacao/app.py
```

Abra `http://localhost:8501`. Para o login **simulado**, use `admin` /
`senha-de-exemplo`. A importação lê e contabiliza o CSV; a coleta devolve progresso
fictício. Nenhuma dessas operações persiste ou classifica dados reais.

API em outro terminal:

```bash
uv run --offline uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
curl --fail http://127.0.0.1:8000/health
```

Resposta: `{"status":"ok"}`. Isso comprova apenas a saúde do serviço.
Atalhos: `make run`, `make api`, `make demo`; `make` lista os alvos existentes.
As atribuições de variáveis acima usam sintaxe Bash; no PowerShell, use `$env:NOME="valor"`.

```bash
uv run --offline pytest -v -ra --cov=src --cov-report=term-missing
make lint
uv lock --check
git diff --check
uv run --offline python -m scripts.demonstrar_pipeline
```

A demo usa cinco registros sintéticos e analisador simulado; verifica BSON sem
fazê-los persistir. Os resultados datados estão no [ensaio atual](docs/qa/pc1/RELATORIO_ENSAIO_FINAL.md).
Para inferência real: `uv sync --locked --group ml` ou `make setup-ml`.
Essa instalação é grande; o primeiro carregamento pode baixar pesos. Não é
requisito do roteiro offline e não foi revalidada nesta revisão documental.

## Desenvolvimento

| Diretório | Conteúdo |
|---|---|
| `src/` | Camadas de apresentação, serviço, processamento e dados |
| `tests/` | Testes e fixtures sintéticas; [guia](tests/README.md) |
| `scripts/` | Auditoria, comparação de modelos e demo |
| `docs/` | Contratos, guias, fontes acadêmicas e QA |
| `Datasets/` | Arquivo legado TweetSentBR; licença/redistribuição pendente |
| `models/`, `notebooks/` | Reservas para artefatos locais; não publicar pesos/corpus grandes |

`main` é a referência de entrega estável; `developer`, a integração. `docs` mantém
materiais acadêmicos; `gh-pages`, arquivos de publicação. Use branches próprias
`feat/`, `fix/`, `test/`, `docs/` ou `chore/`, commits `tipo(escopo): descrição`
e PR com problema, comportamento, validação, contratos e pendências.
Esta documentação deve ser revisada contra a integração PC1 selecionada, sem
atribuir suas funcionalidades à `developer`. Não fazer merge automático.

A CI usa Python da `.python-version`, `uv sync --locked`, `uv lock --check`,
Ruff do frontend, verificação geral `F,E9` e pytest com cobertura.
`make check` reúne essas verificações. Testes offline não substituem validação
externa, revisão de outro integrante ou aceite da PO. Código e textos seguem
português, PEP 8 e type hints; dependências são alteradas por `uv add/remove`,
versionando manifesto e lock juntos.

## Documentação

O [índice completo](docs/README.md) organiza produto/projeto, arquitetura, dados,
ML, banco, frontend, QA, reuniões e experimentos. Entradas principais:

- [Fontes acadêmicas e lacunas](docs/fontes-academicas.md).
- [Frontend](docs/frontend/README.md), [contrato API](docs/frontend/CONTRATO-API.md) e [wireframes](docs/frontend/WIREFRAMES.md).
- [Dados e pipeline](docs/contratos-dados.md), [TweetSentBR](docs/tweetsentbr.md) e [BPSAD](docs/bpsad.md).
- [Classificação](docs/classificacao.md), [MongoDB](docs/mongodb_setup.md) e [esquema](docs/banco/esquema-mongodb.md).
- [Roteiro validado](docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md), [resumo para apresentação](docs/qa/pc1/RESUMO_APRESENTACAO.md) e [auditoria documental](docs/qa/pc1/AUDITORIA_DOCUMENTACAO.md).
- [Changelog](CHANGELOG.md).

## Limitações do PC1

- Painel e login do #70 usam dados/sessão de exemplo. Importação e coleta simuladas
  não alimentam o dashboard, não persistem e não classificam dados reais.
- MongoDB ainda depende das entregas de persistência e consultas. A conexão
  encapsulada foi testada com mocks; não há nova homologação Atlas nesta auditoria.
- As rotas de análises, filtros e administração são propostas. O modo API falha
  de forma controlada enquanto o backend não as fornecer; não troca para mock.
- Pesquisa híbrida e semântica são propostas. XFetch está no #65, fora deste SHA.
- Métricas exploratórias não reproduzidas não são validação independente do modelo.
  TweetSentBR local não tem partições/IDs originais suficientes para esse aceite;
  BPSAD de outro domínio também não garante ausência de sobreposição de pré-treino.
- Licença, redistribuição e tratamento de menções do TweetSentBR dependem de decisão
  da equipe/PO. Nenhum novo dado real é publicado nesta tarefa.
- Documentos completos de Visão, Arquitetura e GQM e a rubrica oficial PC1 não
  foram localizados. O material técnico não substitui sua validação acadêmica.
