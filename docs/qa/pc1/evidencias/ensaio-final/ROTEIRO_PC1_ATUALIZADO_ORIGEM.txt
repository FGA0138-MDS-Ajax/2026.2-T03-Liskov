# Roteiro atualizado do PC1 — 5 a 8 minutos

Data: 09/11/2026. O [roteiro anterior](ROTEIRO_DEMONSTRACAO.md) permanece como
registro do cenário A. Este roteiro distingue o frontend mock novo do backend.

## Preparar antes da aula

Neste computador, o uv está em `/tmp/sentia-pc1/tooling/bin/uv`. Abra os terminais:

```bash
export PATH=/tmp/sentia-pc1/tooling/bin:$PATH
export UV_CACHE_DIR=/tmp/sentia-pc1/cache
export UV_PYTHON_INSTALL_DIR=/tmp/sentia-pc1/python
```

Os diretórios `/tmp` são locais e temporários. Preserve-os até a apresentação;
as branches publicadas permitem reconstruí-los em outra máquina.

- **Cenário B:** `/tmp/sentia-ensaio/integracao`, branch
  `test/pc1-integracao-frontend-atualizado`, contém #69 + #70 + correção #71.
- **Cenário A, reserva independente:** `/tmp/sentia-pc1/base`, head #69 `b9d8326`.
  Para usá-lo, troque somente o `cd`; não tente mostrar filtros/login nessa versão.

No diretório escolhido, antes de começar:

```bash
uv sync --locked
uv lock --check
uv run pytest -v -ra
uv run python -m scripts.demonstrar_pipeline
```

Preparar dependências antes da aula: o primeiro sync pode exigir rede. Não instalar
`--group ml`; não configurar Atlas ou chave XFetch. Não mostrar `.env` na tela.
Os comandos abaixo funcionam offline após o sync.

## 0:00–0:45 — Apresentar o escopo

Explicar: “SentIA é uma plataforma em desenvolvimento para análise de sentimentos
em português. Hoje mostraremos a interface com **dados fictícios**, uma API de saúde
e um pipeline com **analisador simulado**. Importação/coleta no painel não persistem
os dados e não executam BERTweet real.”

## 0:45–3:00 — Dashboard e filtros, cenário B

Terminal A:

```bash
cd /tmp/sentia-ensaio/integracao
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run --offline streamlit run src/apresentacao/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats=false
```

Abrir `http://127.0.0.1:8501` em janela desktop (1440 px recomendado).

1. Mostrar o aviso de dados de exemplo, 17 registros e percentuais 47%/24%/29%.
2. Escolher **Negativo**, clicar **Aplicar filtros**: cinco registros, 100% negativos.
3. Clicar **Limpar**: campos vazios, sentimento Todos, 17 registros.
4. Informar 01/08/2026 a 31/08/2026, Aplicar: cinco registros, 60%/20%/20%;
   aviso de quatro textos sem data excluídos.
5. Opcional: trocar o início para 01/09/2026 e o fim para 01/08/2026. Aplicar
   mostra erro e mantém os resultados anteriores. Limpar restaura campos e dados.

Os campos de data aceitam dia/mês/ano ou calendário. Uma das pontas pode ficar
vazia. Em tablet, recolher o menu lateral se os rótulos ficarem apertados; no
celular a página exige rolagem vertical normal.

## 3:00–4:30 — Administração fictícia, cenário B

1. Sem sessão, mostrar o menu **Entrar**, sem Administração.
2. Entrar com **admin / senha-de-exemplo**; explicar que são credenciais públicas
   de mock e não representam proteção ou autenticação real do produto.
3. Importar `tests/fixtures/dataset_valido.csv`: relatório **5 de 5**.
4. Para demonstrar descartes, usar `tests/fixtures/pc1_importacao_descartes.csv`
   se estiver na worktree após integrar os relatórios: **1 de 3**, com dois motivos.
5. Escolher TweetSentBR e clicar **Iniciar coleta e análise**; mostrar em andamento.
   Clicar **Atualizar situação**: conclusão com 17 textos **simulados**.
6. Clicar **Sair**: menu volta a Entrar. Expiração de sessão foi verificada nos testes.

Explicar: “O mock lê e contabiliza o CSV, mas não armazena esse dataset. A coleta
usa uma quantidade de exemplo fixa e não analisa o CSV importado. O dashboard
continua com sua fonte fictícia; não há integração ponta a ponta com MongoDB.”

## 4:30–5:15 — API real, somente saúde

Terminal B, no mesmo diretório:

```bash
uv run --offline uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
```

Terminal C:

```bash
curl --fail http://127.0.0.1:8000/health
```

Esperado: `{"status":"ok"}`. As rotas administrativas do #66 não foram incluídas.
Não trocar o painel para `api` esperando que login/importação/coleta funcionem:
essas rotas ainda são propostas. O modo api informa a indisponibilidade.

## 5:15–6:15 — CSV, pipeline e BSON offline

```bash
uv run --offline python -m scripts.demonstrar_pipeline
```

Mostrar cinco registros da fixture, IDs/fontes/textos preservados, rótulo humano
separado da previsão neutra simulada, probabilidades e datas UTC. BSON é uma
serialização local real; **não houve gravação MongoDB nem inferência BERTweet real**.

## 6:15–7:30 — Evidências e próximos passos

Mostrar os resultados atuais em [RELATORIO_ENSAIO_FINAL.md](RELATORIO_ENSAIO_FINAL.md)
e as capturas de desktop/tablet/celular. Diferenciar testes de contrato com mocks
versus homologação de serviço externo. Explicar as camadas apresentação, serviço,
processamento e dados, sem afirmar que o fluxo inteiro já está integrado.

Pendências: API administrativa e de análises, persistência, integração real,
classificador/avaliação científica, gráficos/listagem e aceite dos contratos.
Não apresentar #64/#65 como dependências necessárias deste ensaio.

## Contingência: cenário A e falhas locais

Se a interface nova falhar, encerrar os servidores com Ctrl+C, trocar para:

```bash
cd /tmp/sentia-pc1/base
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run --offline streamlit run src/apresentacao/app.py --server.address 127.0.0.1 --server.port 8501
```

Mostrar dashboard básico, aviso mock, `/health`, pipeline e testes. Não mostrar
filtros ou login ausentes no cenário A. A API é iniciada pelo mesmo comando.

- Porta ocupada: usar `--server.port 8502` ou API `--port 8001` e ajustar URL.
- uv fora do PATH, mas ambiente pronto: `.venv/bin/python -m streamlit ...`,
  `.venv/bin/python -m uvicorn ...`, `.venv/bin/python -m scripts.demonstrar_pipeline`.
- Sem dependências/rede: apresentar evidências salvas e declarar que não é execução
  ao vivo. Não baixar modelos na aula.
- Para demonstrar vazio/erro, reiniciar o painel trocando `SENTIA_MOCK_CENARIO` por
  `vazio` ou `erro`; manter o aviso fictício visível.

Nenhum merge oficial, deploy ou aprovação automática faz parte deste roteiro.

## Reconstruir a integração em outra máquina

Os SHAs fixam o estado ensaiado, independentemente de mudanças futuras na developer.
Com identidade Git configurada, execute a partir de um clone atualizado:

```bash
git fetch origin --prune
git worktree add -b test/pc1-demo-local ../sentia-demo-pc1 c6fc53561055178085edcbc123fc86166edf89fa
cd ../sentia-demo-pc1
git merge --no-edit b9d832669e7f49b7a09ef8ad0be6e55959d4c135
git merge --no-edit 61926febc667fb669130469adeceddf971983b6b
git merge --no-edit bcd75e7b06a004c5d8a0609896bd4714636a3743
```

O último merge pode conflitar **somente** no workflow. Preserve o workflow abrangente
#69, sem substituir nenhum arquivo da interface:

```bash
git show b9d832669e7f49b7a09ef8ad0be6e55959d4c135:.github/workflows/ci.yml > .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "test(pc1): preservar workflow geral na integracao local"
uv sync --locked
uv run pytest -v -ra
```

Para trazer também relatórios e fixture de descartes, integre a branch publicada
`origin/docs/pc1-ensaio-final` **nesse ambiente local**, após conferir seu diff.
Não executar esses merges em developer/main nem tratá-los como autorização de merge oficial.
