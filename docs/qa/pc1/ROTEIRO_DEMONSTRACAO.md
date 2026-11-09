# Roteiro de Demonstração — PC1 (5–8 minutos)

Data de referência: **09/11/2026**
Branch de integração validada: `test/pc1-integracao-frontend-atualizado` (`developer` com PR #65 integrado + PRs #69, #70, #71 e #72).

---

## 0. Preparação (antes de iniciar a apresentação)

Na raiz do repositório:

```bash
uv sync --locked
make env
```

> **Nota:** toda a demonstração roda 100% offline. Não é necessário subir MongoDB, configurar `XFETCH_API_KEY` nem baixar pesos reais do BERTweet durante a apresentação.

---

## 1. Abertura e Arquitetura (1 min)

1. Apresentar o objetivo do **SentIA**: plataforma para análise de sentimentos em textos em português (datasets rotulados e publicações em redes sociais).
2. Mostrar a estrutura em quatro camadas ([`docs/arquitetura.md`](../../arquitetura.md)):
   - `src/processamento/aquisicao`: importador CSV, adaptadores TweetSentBR e BPSAD, módulo XFetch (#65) e auditoria de datasets.
   - `src/processamento/classificacao` e `pipeline.py`: adaptador `ClassificadorBertweet`, baseline TF-IDF + Regressão Logística e geração de documentos BSON.
   - `src/dados`: conexão explícita ao MongoDB (`database.py`) e esquema lógico (`docs/banco/esquema-mongodb.md`).
   - `src/servico` e `src/apresentacao`: API FastAPI (`GET /health`) e painel Streamlit (Dashboard + Administração).
3. Deixar claro o escopo do PC1: **aquisição, pipeline de classificação em lote e interface funcional com dados de exemplo estão prontos e testados; persistência no MongoDB e rotas HTTP de negócio serão conectadas na próxima entrega**.

---

## 2. Demonstração do Painel Streamlit: Dashboard e Filtros (2 min)

Em um terminal (Terminal A):

```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run streamlit run src/apresentacao/app.py --browser.gatherUsageStats=false
```

Abrir `http://localhost:8501` no navegador:

1. **Visão geral (sem filtros)**:
   - Apontar o aviso explícito de **dados de exemplo** na tela.
   - Mostrar os indicadores iniciais: **17 textos analisados**, **47% Positivo** (8), **24% Neutro** (4) e **29% Negativo** (5).
2. **Filtro por sentimento**:
   - Selecionar **Negativo** e clicar em **Aplicar filtros** → total muda para **5** (`100% Negativo`).
3. **Filtro por período e tratamento de datas**:
   - Preencher `De: 2026-08-01` e `Até: 2026-08-31` com sentimento **Todos** e clicar em **Aplicar filtros** → exibe **5 análises** no período e o aviso informativo de que **4 textos sem data de publicação** ficaram fora do filtro temporal.
   - Testar validação de intervalo invertido (`De: 2026-09-01`, `Até: 2026-08-01`) → exibe mensagem de erro amigável preservando o último resultado válido.
4. **Limpeza de filtros**:
   - Clicar em **Limpar** → os campos de data e sentimento são restaurados no navegador e o dashboard volta aos **17 textos analisados**.

---

## 3. Demonstração de Login, Importação CSV e Coleta Simulada (2 min)

Ainda no painel (`http://localhost:8501`):

1. **Login administrativo (mock)**:
   - Mostrar que, sem sessão ativa, o menu lateral exibe apenas **Dashboard** e **Entrar**.
   - Clicar em **Entrar** e autenticar com:
     - Usuário: `admin`
     - Senha: `senha-de-exemplo`
   - Após o login, o menu passa a exibir **Administração** e o botão **Sair**.
2. **Importação de dataset CSV**:
   - Na seção **Importar dataset (CSV)**, enviar o arquivo `tests/fixtures/dataset_valido.csv` e clicar em **Importar arquivo**.
   - Mostrar o relatório exibido na tela: **5 registros lidos, 5 importados, 0 descartados**.
   - *(Opcional)* Enviar `tests/fixtures/dataset_vazio.csv` ou `tests/fixtures/dataset_invalido.csv` para demonstrar o tratamento de erro amigável na interface.
3. **Coleta e análise simulada**:
   - Na seção **Coleta e análise**, selecionar a fonte **TweetSentBR**, clicar em **Iniciar coleta** (situação `Em andamento`) e em seguida clicar em **Atualizar situação** (situação `Concluída`, com **17 coletados / 17 analisados**).
4. **Encerrar sessão**:
   - Clicar em **Sair** no menu lateral e mostrar o retorno ao estado não autenticado.
   - **Explicitar na fala**: login, importação e coleta operam sobre `AdministracaoMock` para validar os fluxos de tela e contratos propostos; ainda não persistem no MongoDB nem alteram o resumo fixo do dashboard.

---

## 4. API FastAPI e Pipeline Offline (1–2 min)

Em um segundo terminal (Terminal B):

```bash
# 1. Smoke test da API FastAPI (em paralelo ou via TestClient/uvicorn)
uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
```

Em outro terminal (Terminal C):

```bash
curl --fail http://127.0.0.1:8000/health
```
- Mostrar a resposta `{"status":"ok"}`.

Em seguida, executar a demonstração do pipeline offline:

```bash
uv run python -m scripts.demonstrar_pipeline
```
- Mostrar que o script importa os **5 registros** de `tests/fixtures/dataset_valido.csv`, executa `PipelineClassificacao` com `ClassificadorBertweet` (usando analisador simulado determinístico), preserva `texto_original` e `id_origem`, separa `rotulo_padronizado` (anotação humana) de `sentimento` (previsão do modelo) e valida a serialização **BSON** de todos os documentos.

---

## 5. Suíte de Testes e Qualidade (1 min)

Executar ou exibir o resultado da suíte automatizada:

```bash
uv run pytest -v -ra
uv run ruff check src/apresentacao tests/test_painel_*.py
uv lock --check
```

- **Resultado na branch de integração**: **522 testes aprovados (`522 passed, 0 failed, 0 skipped`)** e **94% de cobertura** em `src/`, cobrindo aquisição (CSV, TweetSentBR, BPSAD, XFetch), classificador BERTweet, baseline, pipeline BSON, banco MongoDB, API `/health` e painel Streamlit (filtros, administração e contratos HTTP).
