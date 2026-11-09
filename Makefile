# Atalhos de desenvolvimento do SentIA. Execute `make` para ver os comandos.
# Requer o uv: https://docs.astral.sh/uv/getting-started/installation/
PORTA ?= 8501
PORTA_API ?= 8000

.DEFAULT_GOAL := help
.PHONY: help setup setup-ml env run api hash-senha lint test test-frontend check

help: ## Lista os comandos disponíveis
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 16

setup: env ## Instala as dependências exatas do uv.lock e prepara o .env
	uv sync --locked

setup-ml: env ## Também instala as dependências do BERTweet real (download grande)
	uv sync --locked --group ml

env: ## Cria o .env a partir do exemplo, sem sobrescrever um arquivo existente
	@if [ -e .env ]; then echo ".env já existe; nada foi alterado."; \
	else cp .env.frontend.example .env; echo ".env criado."; fi

run: ## Inicia o painel em http://localhost:8501 (PORTA=8501)
	uv run streamlit run src/apresentacao/app.py --server.port $(PORTA)

api: ## Inicia a API FastAPI (PORTA_API=8000)
	uv run uvicorn src.servico.main:app --reload --port $(PORTA_API)

hash-senha: ## Gera o SENTIA_ADMIN_SENHA_HASH do Administrador (a senha não aparece)
	uv run python -m src.servico.autenticacao

lint: ## Verifica o código do painel e da API com o ruff
	uv run ruff check src/apresentacao src/servico tests/test_painel_*.py tests/test_api_administracao.py

test-frontend: ## Executa somente os testes do frontend
	uv run pytest tests/test_painel_*.py -q

test: ## Executa todos os testes com cobertura, como na CI
	uv run pytest --cov=src -q

check: lint test ## Executa as mesmas verificações da CI
