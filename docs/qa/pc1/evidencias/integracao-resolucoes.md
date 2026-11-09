# Integração experimental

Branch local: `test/pc1-integracao`, worktree `/tmp/sentia-pc1/integracao`.
Base: `c6fc53561055178085edcbc123fc86166edf89fa`.

1. Fast-forward da entrega A, `8806bfa`.
2. Merge da correção #64 `1cd636e`: conflitos em `.github/workflows/ci.yml`,
   `pyproject.toml`, `uv.lock` por origens anteriores à migração uv.
   Preservado workflow incremental da entrega A; pyproject/lock da correção #64
   (mesma base travada + grupo opcional experimentos). Resolução: `c368b1d`.
3. Merge da correção #65 `4507aac`: conflito somente em workflow;
   preservado workflow incremental de A, que executa em todos os destinos de PR.
   Resolução: `480ecf1ff03d69518e7771c4278772ac44e9a3b2`.
4. O teste conjunto recebeu três cenários: CSV, TweetSentBR sintético e
   BPSAD sintético, além do caminho XFetch mock → pipeline → BSON.

Comando: `uv run pytest tests docs/qa/pc1/evidencias/test_integracao_prs.py -v -ra --cov=src --cov-report=term-missing`.
Resultado: **471 passed, 0 failed, 0 skipped; 96% cobertura de src**.
`uv sync --locked`, `uv lock --check`, Ruff frontend e Ruff F,E9 em todas as
camadas, `git diff --check` e demonstração offline também aprovados.

Parecer: **COMPATÍVEL** para contratos verificados com mocks/fixtures, datas UTC,
IDs/fontes/textos/rótulos/probabilidades, metadados permitidos e serialização BSON.
MongoDB real, persistência, inferência real e endpoints futuros: **NÃO VERIFICADO**.
Não foi realizada consulta XFetch nem conexão Atlas. Não houve merge oficial.
