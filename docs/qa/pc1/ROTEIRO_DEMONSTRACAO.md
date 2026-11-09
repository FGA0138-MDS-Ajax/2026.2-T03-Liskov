# Roteiro de demonstração — PC1, 09/11/2026

Duração sugerida: 5–8 minutos. Executar na raiz da entrega A ou da worktree
experimental já preparada. A entrega A funciona sem integrar os PRs #64/#65.

## 1. Preparar antes da apresentação

```bash
uv sync --locked
make env
uv run pytest -v -ra
uv run python -m scripts.demonstrar_pipeline
```

Não instalar o grupo ML. Não configurar Atlas ou chave XFetch. A instalação inicial
exige internet; depois do sync, os comandos abaixo usam dependências locais.
`make env` preserva um `.env` existente. Não compartilhar seu conteúdo na tela.

Neste computador a entrega está em `/tmp/sentia-pc1/base` e o uv foi instalado em
`/tmp/sentia-pc1/tooling/bin/uv`. Se o comando uv não estiver no PATH:

```bash
export PATH=/tmp/sentia-pc1/tooling/bin:$PATH
export UV_CACHE_DIR=/tmp/sentia-pc1/cache
export UV_PYTHON_INSTALL_DIR=/tmp/sentia-pc1/python
cd /tmp/sentia-pc1/base
```

## 2. Mostrar o painel

Terminal A:

```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run --offline streamlit run src/apresentacao/app.py --browser.gatherUsageStats=false
```

Abrir `http://localhost:8501`. Mostrar aviso de **dados fictícios**, total analisado
e percentuais positivo/neutro/negativo. Navegar para Administração e explicar o
placeholder. Não apresentar autenticação, gráficos/filtros futuros ou coleta como
entregues. O painel mock independe do servidor FastAPI.

Opcional: encerrar com Ctrl+C e repetir trocando `SENTIA_MOCK_CENARIO` por `vazio`
ou `erro`, demonstrando as mensagens sem exceção.

## 3. Mostrar a API

Terminal B:

```bash
uv run --offline uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
```

Terminal C:

```bash
curl --fail http://127.0.0.1:8000/health
```

Esperado: `{"status":"ok"}`. Esse endpoint confirma apenas o serviço em execução.
O cliente HTTP do painel ainda depende de endpoints futuros de análises/resumo.

## 4. Importação e pipeline offline

```bash
uv run --offline python -m scripts.demonstrar_pipeline
```

O script lê `tests/fixtures/dataset_valido.csv`, importa cinco registros sintéticos,
usa `ClassificadorBertweet` com **analisador simulado constante** e imprime o
resultado estruturado. Mostrar `texto_original`, `id_origem`, `fonte`, rótulo
humano separado da previsão, probabilidades e datas UTC. O script verifica
serialização BSON; não grava nem consulta MongoDB e não mede acurácia real.

## 5. Testes e decisões arquiteturais

```bash
uv run --offline pytest -v -ra
uv run --offline pytest --cov=src --cov-report=term-missing
make lint
```

Base auditada: 394 testes aprovados, nenhum ignorado e 96% de cobertura.
Resultados das branches corrigidas estão no relatório final; não misturar contagens.
Explicar separação entre aquisição, processamento, serviço, dados e apresentação;
texto preservado antes do BERTweet e baseline clássico separado.

## 6. Encerrar com o estado real

Em desenvolvimento: persistência, consultas/filtros/autenticação na API,
importação/coleta pelo painel, gráficos completos e integração de resultados reais.
Busca híbrida é proposta. Métricas BPSAD do autor não foram reproduzidas aqui.
Pesos BERTweet e API externa não foram exercitados ao vivo nesta auditoria.

## Alternativa de contingência

Se o uv não estiver no PATH mas a `.venv` estiver pronta, usar
`.venv/bin/python -m streamlit run src/apresentacao/app.py`,
`.venv/bin/python -m uvicorn src.servico.main:app` e
`.venv/bin/python -m scripts.demonstrar_pipeline`.
Se a porta estiver ocupada, usar `--server.port 8502` ou `--port 8001` e ajustar URL.
Sem ambiente preparado ou rede para instalar dependências, apresentar as evidências
salvas em `docs/qa/pc1/evidencias/` e o código; declarar que não é execução ao vivo.
Não afirmar que um ambiente sem dependências executa a aplicação.
