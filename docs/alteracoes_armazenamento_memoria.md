# Unificação da persistência de análises, datasets e pesquisas no MongoDB

## Contexto histórico

Em uma etapa intermediária do projeto, foi introduzido o modo alternativo em memória selecionado pela variável `SENTIA_ARMAZENAMENTO=memoria`, além do módulo auxiliar `src/persistencia/leitura.py` duplicando funções de consulta que já pertenciam ao repositório principal. Anteriormente também os datasets CSV importados e o histórico do `TweetSentBR`/pesquisas híbridas dependiam do estado em memória do processo.

Essa bifurcação criava fluxos desconectados entre a API principal (`src/servico/main.py`) e a administração (`src/servico/administracao.py`), fazendo com que datasets, cache de pesquisas e análises se perdessem ou divergissem após reinícios.

## Estado atual (canônico)

- **Implementação única de persistência:** [`src/dados/repositorio.py`](../src/dados/repositorio.py) (`RepositorioAnalises` e funções associadas) concentra gravação, deduplicação `(fonte, id_origem)`, busca pontual, listagem paginada, resumo por sentimento e listagem de base sobre as coleções MongoDB `analises`, `registros`, `datasets` e `pesquisas`.
- **Remoção do modo em memória para análises e do módulo duplicado:**
  - `src/persistencia/leitura.py` foi removido; todas as consultas e integrações com MongoDB passam diretamente por `src/dados/repositorio.py`.
  - A variável `SENTIA_ARMAZENAMENTO` e os helpers `*_memoria` em `src/dados/repositorio.py` foram removidos de `src/servico/dependencias.py` e `src/servico/main.py`.
- **Integração completa com a administração:**
  - `POST /datasets` persiste os registros normalizados e os metadados do dataset no MongoDB (`registros` e `datasets`) de forma síncrona antes de retornar HTTP `201` (ou `503` se o banco estiver indisponível).
  - O corpus `TweetSentBR` é carregado e persistido de forma idempotente em `datasets`/`registros` (`id_dataset="tweetsentbr"`) e permanece acessível mesmo após reinício sem depender do CSV local.
  - A pesquisa híbrida (`_registros_da_coleta()` + `pesquisar()`) reutiliza a base unificada (`registros` + `analises`) e o cache persistente da coleção `pesquisas` (sem colidir em substrings parciais, sem gravar cache quando o `XFetch` falha e respeitando `forcar_atualizacao=True` sem apagar o histórico).
  - `executar_coleta()` em [`src/servico/administracao.py`](../src/servico/administracao.py) verifica análises já persistidas em `analises` (`obter_analises_por_chaves`) antes de enviar registros ao pipeline, evitando reclassificação redundante, e grava novos lotes via `RepositorioAnalises` na mesma coleção lida pelo dashboard.
  - `RepositorioAdministracao` preserva em RAM apenas o controle transitório dos jobs `coletas` em andamento e sessões autenticadas (`Autenticador`).

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
