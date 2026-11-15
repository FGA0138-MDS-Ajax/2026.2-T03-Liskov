# Unificação da persistência de análises no MongoDB

## Contexto histórico

Em uma etapa intermediária do projeto, foi introduzido o modo alternativo em memória selecionado pela variável `SENTIA_ARMAZENAMENTO=memoria`, além do módulo auxiliar `src/persistencia/leitura.py` duplicando funções de consulta que já pertenciam ao repositório principal.

Essa bifurcação criava dois fluxos distintos entre a API principal (`src/servico/main.py`) e a administração (`src/servico/administracao.py`), fazendo com que análises processadas por coletas administrativas não fossem gravadas na coleção `analises` consultada pelo dashboard.

## Estado atual (canônico)

- **Implementação única de persistência:** [`src/dados/repositorio.py`](../src/dados/repositorio.py) (`RepositorioAnalises` e funções associadas) concentra gravação, deduplicação, busca pontual, listagem paginada, resumo por sentimento e listagem de registros base sobre a coleção MongoDB `analises`.
- **Remoção do modo em memória para análises e do módulo duplicado:**
  - `src/persistencia/leitura.py` foi removido; todas as consultas e integrações com MongoDB passam diretamente por `src/dados/repositorio.py`.
  - A variável `SENTIA_ARMAZENAMENTO` e os helpers `*_memoria` em `src/dados/repositorio.py` foram removidos de `src/servico/dependencias.py` e `src/servico/main.py`.
- **Integração com a administração:**
  - `executar_coleta()` em [`src/servico/administracao.py`](../src/servico/administracao.py) persiste os lotes classificados via `ContextoAdministracao.salvar_analises()` → `RepositorioAnalises` na mesma coleção `analises` lida por `GET /analises` e `GET /analises/resumo`.
  - `ContextoAdministracao.registros_da_base()` também consulta `RepositorioAnalises.listar_registros_base()`, preservando o histórico da base após reinícios do servidor.
  - `RepositorioAdministracao` preserva em RAM apenas o estado operacional transitório do processo (`datasets` CSV importados como *staging*, status de execução de `coletas` e sessões autenticadas).

## Como executar localmente

1. Inicie uma instância do MongoDB 7 (por exemplo, `docker run -d --rm -p 27017:27017 mongo:7`) e configure `MONGODB_URI` no `.env` ou ambiente.
2. Inicie a API:

   ```bash
   uv run uvicorn src.servico.main:app --reload
   ```

3. Inicie o painel em outro terminal:

   ```bash
   SENTIA_FONTE_DADOS=api SENTIA_API_URL=http://127.0.0.1:8000 uv run streamlit run src/apresentacao/app.py
   ```
