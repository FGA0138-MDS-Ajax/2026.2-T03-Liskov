# Plano de organização incremental do SentIA

**Base:** `developer` em `b91c7a5e4af972d98da6e5ded70b2243d60f5513`  
**Escopo:** documentação, navegabilidade e limpeza comprovada.  
**Fora do escopo:** alterações do PR #96, mudanças de comportamento da API, persistência, ML, pré-processamento e contratos de dados.

## Princípio

A estrutura atual de `src/` já expressa as quatro camadas. Não criar novas camadas e não movimentar módulos apenas por estética. O esforço deve se concentrar em corrigir a documentação defasada e em tornar a entrada do projeto mais simples.

## Etapa A — Diagnóstico

- [x] Inventariar a árvore Git de `developer`.
- [x] Identificar os diretórios de código, documentação, testes e configuração.
- [x] Conferir a branch `docs` e o papel separado do portal MkDocs.
- [x] Identificar divergências documentais conhecidas.
- [x] Identificar duplicidade exata em `merge-a.txt` e `merge-b.txt`.
- [ ] Confirmar no clone o uso externo dos wrappers e a proveniência dos arquivos de evidência.

**Entrega:** `docs/relatorios/diagnostico-repositorio.md`.

## Etapa B — Documentação técnica na branch `developer`

1. Substituir a fotografia antiga de PC1 em `docs/arquitetura.md` por uma descrição atual da arquitetura. Preservar o documento histórico de PC1 em uma cópia/arquivo próprio antes de substituí-lo, caso o histórico seja importante para a disciplina.
2. Atualizar `tests/README.md` para refletir os módulos existentes, fixtures, dependência de MongoDB e comandos da CI.
3. Revisar o `README.md` como porta de entrada: manter apresentação, funcionalidades, arquitetura resumida, instalação, execução e links; mover inventários extensos e histórico de inspeção para `docs/README.md`.
4. Acrescentar o diagnóstico e este plano ao índice `docs/README.md`.
5. Não alterar os documentos acadêmicos formais aprovados nem gerar versões PDF sem fontes e autorização.

## Etapa C — Portal MkDocs na branch `docs`

1. Atualizar `docs/index.md` para refletir a persistência pós-PR #96, removendo a afirmação de que datasets, corpus e pesquisas persistem apenas em memória.
2. Corrigir o diagrama/descrição arquitetural para apontar a camada de dados para `src/dados/`, sem citar `src/persistencia/`.
3. Corrigir o estado do PR #93 para integrado.
4. Manter a navegação e as atas de reunião existentes.
5. Não substituir o workflow `.github/workflows/ci.yml` da branch `docs` pelo workflow de testes de `developer`. O workflow de `docs` executa `mkdocs gh-deploy --force`.

## Etapa D — Limpeza comprovada

- Investigar `docs/qa/pr44-pr45/merge-a.txt` e `merge-b.txt`; se forem duplicatas sem valor de proveniência distinto, consolidar uma cópia e registrar o motivo.
- Manter `suite-final-a.txt` e `suite-final-b.txt`, pois não são idênticos.
- Manter `amostrar_bpsad.py` e `scripts/validar_bpsad.py` enquanto wrappers de compatibilidade; se a equipe quiser removê-los, anunciar a descontinuação e atualizar comandos/referências primeiro.
- Manter `test_mongo.py` como ferramenta manual até existir substituto equivalente documentado.
- Não excluir datasets, resultados, arquivos de evidência ou documentos históricos por serem antigos.
- Não mover testes nesta entrega.

## Etapa E — Validação e revisão

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

Executar os testes MongoDB com `MONGODB_URI_TESTE` configurado. Na CI, conferir a execução do workflow em `developer`.

No branch `docs`, validar o build MkDocs e conferir os links locais. Antes de qualquer push para essa branch, lembrar que o workflow dispara a publicação em `gh-pages`.

## Organização dos commits sugerida

1. `docs: adiciona diagnóstico e plano de organização`
2. `docs: atualiza arquitetura e guia da suíte de testes`
3. `docs: simplifica README e consolida índice documental`
4. `docs: sincroniza portal MkDocs com estado pós-PR96` (este último commit na branch `docs`, em PR separado se a política da equipe exigir)

Não agrupar alteração de documentação do portal com reestruturação de código. Não incluir commits do PR #96 nesta entrega.
