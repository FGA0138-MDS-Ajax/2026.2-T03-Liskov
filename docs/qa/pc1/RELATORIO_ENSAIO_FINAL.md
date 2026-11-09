# Ensaio final SentIA — PC1

**09/11/2026. Recomendação: cenário B corrigido, com cenário A preparado como reserva.**
O B passou na suíte atual, no servidor real e no roteiro do Chrome. A recomendação
vale para a worktree integrada com #71; não presume que os PRs já foram mesclados.

## Ambiente e referências realmente executadas

| Item | Valor |
|---|---|
| Base remota developer | `c6fc53561055178085edcbc123fc86166edf89fa` |
| #69 / cenário A | `b9d832669e7f49b7a09ef8ad0be6e55959d4c135` |
| #70 / Clicia | `61926febc667fb669130469adeceddf971983b6b` |
| Correção #71 | `bcd75e7b06a004c5d8a0609896bd4714636a3743` |
| Integração original #69+#70 | `ca25e1223564f55b2465f9de87672cfae878df07` |
| Integração final testada | `bfaf7da4437493f5ee9b44022d4979623b232add` |
| #64 com #67 incorporado | `3da81d5e65a1850374145741a62106aafd531ea0` |
| #65 com #68 incorporado | `2dfa96f47f08da723590a15aa7f2abf77c7ae8e9` |
| #66 | Fechado sem merge; não reutilizado |
| Python / uv | 3.11.18 / 0.13.7 |
| Streamlit / FastAPI | 1.67.0 / 0.162.1, conforme uv.lock |
| Navegador / automação | Chrome 157.0.8103.38 / Playwright 1.64.1 |

Worktree B: `/tmp/sentia-ensaio/integracao`, branch
`test/pc1-integracao-frontend-atualizado`. Reserva A: `/tmp/sentia-pc1/base`.
Correções: `/tmp/sentia-ensaio/pr70`, branch `fix/pr70-ensaio-pc1`.
Relatórios: `/tmp/sentia-ensaio/relatorios`, branch `docs/pc1-ensaio-final`.
Playwright está isolado em `/tmp/sentia-ensaio/browser-env`; não entrou no lockfile.
Nenhum modelo, dataset grande ou serviço externo foi usado no ensaio.

## Comandos e evidências

Inspeção inicial executada (consultas de rede repetidas fora do sandbox quando necessário):

```bash
git status --short --branch
git fetch origin --prune
git worktree list --porcelain
gh pr list --state all --limit 100
gh pr view 69
gh pr view 70
gh pr checks 69
gh pr checks 70
git diff origin/developer...origin/feat/painel-frontend
git log --oneline origin/developer..origin/feat/painel-frontend
```

Validação B na raiz da worktree integrada, com uv instalado em
`/tmp/sentia-pc1/tooling/bin/uv`, cache/Python em `/tmp/sentia-pc1/`:

```bash
uv sync --locked
uv lock --check
uv run ruff check src/apresentacao tests/test_painel_*.py
uv run ruff check --isolated --select F,E9 src tests scripts test_mongo.py
uv run pytest -v -ra
uv run pytest --cov=src --cov-report=term-missing
git diff --check
uv run pytest tests/test_painel_administracao.py tests/test_painel_filtros.py -v -ra
uv run python -m scripts.demonstrar_pipeline
```

As suítes usaram timeout externo de 120 s e saídas em arquivos; foram executadas
fora do sandbox porque ASGI e bind de servidores locais são restringidos nele.
Sync também foi confirmado sem `--offline`, usando o cache travado disponível.

Serviços reais iniciados pelo ensaio, encerrados em `finally`:

```bash
uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
uv run streamlit run src/apresentacao/app.py --server.address 127.0.0.1 --server.port 18570 --server.headless=true --browser.gatherUsageStats=false
```

HTTP local verificou `/health`, `/_stcore/health`, `/openapi.json` e ausência das
rotas de administração/análises. Chrome usou contexto novo por largura, sem perfil
pessoal. Estados vazio/erro/api indisponível usaram portas 18571/18572/18573;
reserva A usou 18569. API e frontend não foram ligados por endpoints fictícios.

Roteiro de navegador preservado em
`evidencias/ensaio-final/ensaio_navegador.py`. Reprodução opcional (não necessária
para apresentar): instalar Playwright em ambiente separado, usar Chrome instalado,
e executar com `--raiz-b`, `--raiz-a`, `--evidencias` e `--chrome` quando preciso.

## Resultados atuais

| Execução | Passed | Failed | Skipped | Errors | Cobertura src |
|---|---:|---:|---:|---:|---:|
| Cenário A reexecutado no head atual #69 | 394 | 0 | 0 | 0 | Não medida nesta rodada A |
| #69+#70 originais, execução nova | 458 | 0 | 0 | 0 | 94% |
| Administração/filtros corrigidos | 62 | 0 | 0 | 0 | Não medida nesta rodada focada |
| Integração final com #71 | **461** | **0** | **0** | **0** | **94%** |
| #64+#65, worktree separada | 468 | 0 | 0 | 0 | Não medida nesta rodada |

A diferença 458→461 corresponde a duas regressões de CSV e um teste do ciclo
Limpar/reaplicar. As contagens não foram copiadas de auditorias anteriores.
Ruff e lock check: aprovados. Um aviso de depreciação Starlette/httpx permanece.
Cobertura arredondada de src: 1462 statements, 90 misses. Scripts e navegador não
estão incluídos no denominador de `--cov=src`.

Logs em [evidencias/ensaio-final/](evidencias/ensaio-final/): suíte original, final,
cobertura, testes focados, regressões anteriores, cenário A, pipeline e compatibilidade.
A execução intermediária com 459 aprovados/1 falha foi preservada: o importador de
produção alterava o limite global de csv, tornando a regressão dependente da ordem.
O teste agora fixa/restaura esse limite e mantém a asserção original de erro público.
O bug de Limpar foi revelado no navegador apesar de AppTest passar; a correção foi
validada pelo ciclo real de campos vazios e nova aplicação.

## CI consultada

| Referência | Resultado | Run |
|---|---|---|
| #69 `b9d8326` | SUCCESS | [42687887237](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42687887237) |
| #70 `61926fe` | SUCCESS | [42686384939](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42686384939) |
| Correção #71 `bcd75e7` | SUCCESS | [42693715742](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/42693715742) |
| #64 e #65 nos heads acima | CONFLICTING, sem checks reportados | Exigem resolver base histórica antes de merge |

Sem checks não significa CI verde. #71 inicialmente não tinha check porque o
workflow não incluía seu destino; a correção habilitou esse destino e a CI executou.
A integração B foi testada localmente; sua CI remota só existe se a branch de ensaio
for publicada em PR. Os links acima identificam os checks efetivamente consultados.

## Git, conflitos e segurança

#69+#70 não tiveram conflitos. CHANGELOG foi mesclado automaticamente, preservando
ambas as entregas; o frontend da Clicia foi mantido. Makefile, configurações uv e
workflow de #69 continuam válidos. A mudança posterior de CI em #71 conflitou
somente no workflow: resolução manteve o escopo geral do #69 (todos os destinos).
Nenhuma rota de `src/servico` foi adicionada.

Em `/tmp/sentia-ensaio/compatibilidade`, #64 conflitou em workflow, pyproject e lock;
foram preservados manifest/lock do autor com grupo opcional experimentos e workflow
abrangente. #65 conflitou apenas no workflow. Resolução local `9e2c2fa`, 468 testes
aprovados. Nenhuma dessas entregas foi incorporada ao cenário B.

Incidente local: um comando de merge de compatibilidade foi executado por engano
na árvore original. Sem publicação, foi imediatamente desfeito com
`git reset --merge e2a3ff0d7f88b437a7e43ee1888cdb49739f64da`. O status original
foi confirmado: developer local no SHA inicial e `docs/auditorias/` preservado.
Não houve `reset --hard`, limpeza, force push ou merge oficial nesta etapa.
As execuções posteriores usaram workdirs explícitos. Commits novos usam Figueirin.

## Interface, API e pipeline demonstrados

- Chrome real: dashboard/Administração em 1440/820/390 px, sem rolagem horizontal
  do documento; capturas inspecionadas. No celular há rolagem vertical. Em tablet
  com menu aberto, o indicador Analisados pode abreviar; o menu pode ser recolhido.
- Filtros: sentimento, agosto, período invertido, manutenção dos resultados,
  Limpar sincronizando campos e reaplicação. Pontas opcionais também em AppTest.
- Administração: menu Entrar/Administração, credenciais fictícias, upload 5/5,
  relatório sintético 1 importado/2 descartados, erro de CSV tratado, coleta mock,
  atualização e logout. Expiração: AppTest, sem esperar uma hora no navegador.
- Estados vazio/erro e API indisponível: mensagens claras, sem exceção de tela.
- FastAPI real: 200 com `{"status":"ok"}`; OpenAPI contém somente `/health`.
  Login, datasets, fontes de coleta e resumo não existem e responderam 404.
- Pipeline: cinco registros sintéticos, texto/ID/fonte/rótulo humano preservados,
  previsão neutra simulada, probabilidades válidas, UTC e BSON serializável.
  Sem inferência real ou gravação MongoDB.

A importação mock não guarda o dataset e a coleta não classifica seu conteúdo;
a conclusão usa 17 registros de exemplo. O dashboard mantém sua própria base
fictícia. Não apresentar esses passos como fluxo real ponta a ponta.

## Parecer e apresentação

| Cenário | Situação | Uso |
|---|---|---|
| A, somente #69 | Reexecutado e estável; 394 testes | Reserva independente |
| B, #69+#70+#71 | 461 testes, lint/lock e ensaio Chrome aprovados | **Recomendado**, em desktop, declarando mocks |

Antes da aula: usar a worktree corrigida ou incorporar #71 por revisão humana;
preparar dependências e deixar fixtures disponíveis. Para o roteiro validado não
é indispensável desenvolver backend, instalar ML ou integrar #64/#65. Sem #71,
o caminho Limpar/reaplicar pode reter datas e o upload inválido pode quebrar a tela.

Pendências: aceite dos contratos/requisitos pela equipe/PO, backend administrativo,
persistência, dados reais, modelo/avaliação científica, usabilidade em dispositivos
físicos e acessibilidade completa. Não foram localizadas novas regras oficiais
PC1 para transformar este ensaio em homologação acadêmica.

[Validação detalhada](VALIDACAO_FRONTEND_CLICIA.md) ·
[Roteiro de 5–8 minutos](ROTEIRO_PC1_ATUALIZADO.md).
