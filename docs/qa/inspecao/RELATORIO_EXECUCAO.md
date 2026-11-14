# Relatório de execução e consulta de evidências

Inspeção: **14/11/2026**. Branch de entrega: **`inspecao/sol-medium`**, destino
`developer`. Base de código B: **`1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`**,
confirmada por `git fetch origin` antes das edições. As mudanças de entrega são
documentais em `docs/metricas/` e `docs/qa/inspecao/`; nenhum código/teste/workflow
foi alterado. Não há merge, deploy ou homologação nesta entrega.

## Resultado principal

| Evidência | Ambiente | Resultado observado | Alcance |
|---|---|---|---|
| Local E2, 14/11/2026 19:00:37−03:00 (início no JUnit) | Linux Fedora, kernel 7.3.3-300.fc45.x86_64, x86_64; Python 3.11.17; uv 0.13.5; pytest 9.2.0; pytest-cov 7.1.0; coverage 7.17.2; Ruff 0.17.4; dependências de uv.lock | **814 coletados; 789 PASS, 0 FAIL, 0 ERROR, 25 SKIP, 10 warnings; 39,10 s; cobertura src 92%** (2699 statements, 212 missing) | Banco real indisponível localmente; mocks de ML/HTTP externo; sem pesos BERTweet nem XFetch real. Código de saída 0 da suíte não transforma SKIP em aprovação. |
| CI E1, execução em 13/11/2026, consultada em 14/11 | SHA B, ubuntu-latest, CPython 3.11.18, uv.lock, serviço mongo:7 | **814 PASS, 0 FAIL, 0 ERROR, 0 SKIP, 10 warnings; 21,40 s; cobertura src 93%** (2699 statements, 176 missing) | Integração real com banco nos testes que usam fixture de coleção; ML e XFetch simulados. Evidência remota consultada, não execução local. |
| Primeira tentativa local restrita | Mesmo código e ambiente de dependências; sandbox | 814 coletados, cinco casos iniciais concluídos; interrupção por timeout de 120 s, saída **124**, parada observada em test_api.py; **sem resultado final nem JUnit** | Causa exata não diagnosticada; repetição fora da restrição concluiu. Não classificar tentativa como falha funcional, PASS ou suíte completa. |

Fontes: [log local](evidencias/pytest-local.txt), [resumo estruturado derivado do
JUnit](evidencias/resumo-local.json), [tentativa restrita](evidencias/pytest-tentativa-restrita.txt),
[extrato do log do CI](evidencias/ci-base-extrato.txt),
[run remoto](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871)
e [job test](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920).
Os logs locais substituem o caminho absoluto da worktree por `<REPO>` e
removem espaços finais de linhas da tentativa interrompida.
O JSON omite hostname e contém o hash SHA-256 do JUnit original temporário.
Contagens por arquivo abaixo foram derivadas do JUnit, sem substituir dados de
execução por quantidades históricas.

## Comandos efetivamente executados

O `.python-version` pede 3.11, ausente inicialmente no ambiente de execução.
O Python foi instalado e o ambiente virtual/cache mantidos fora do código:

```bash
UV_CACHE_DIR=/tmp/sentia-sol-medium-cache \
UV_PYTHON_INSTALL_DIR=/tmp/sentia-sol-medium-python \
uv python install 3.11

export UV_CACHE_DIR=/tmp/sentia-sol-medium-cache
export UV_PYTHON_INSTALL_DIR=/tmp/sentia-sol-medium-python
export UV_PROJECT_ENVIRONMENT=/tmp/sentia-sol-medium-venv
uv sync --locked
uv lock --check
make lint

COVERAGE_FILE=/tmp/sentia-sol-medium.coverage timeout 120s \
  uv run pytest -ra --cov=src --cov-report=term-missing \
  --junitxml=/tmp/sentia-sol-medium-pytest.xml \
  > /tmp/sentia-sol-medium-pytest-completo.txt 2>&1
```

| Comando | Saída e resultado |
|---|---|
| `git fetch origin` | Concluído após autorização para gravar metadados Git fora da worktree; `HEAD` e `origin/developer` em B. |
| `uv python install 3.11` | Instalado CPython 3.11.17. |
| `uv sync --locked` | Primeira tentativa sem intérprete; tentativa seguinte falhou por DNS no sandbox; repetição autorizada concluiu: 139 pacotes resolvidos, **62 instalados**, sem grupos ml/experimentos. Não alterou uv.lock. |
| `uv lock --check` | Saída 0: `Resolved 139 packages`. |
| `make lint` | Saída 0; `uv run ruff check src/apresentacao tests/test_painel_*.py` e `uv run ruff check --isolated --select F,E9 .`: `All checks passed!` em ambos. |
| pytest, primeira tentativa restrita | Arquivo de saída `/tmp/sentia-sol-medium-pytest.txt`; saída 124 após 120 s, sem resumo final. |
| pytest, repetição autorizada fora do sandbox | Saída 0, resumo local da tabela acima. Nenhum teste removido ou alterado. |
| Conferência aritmética do PR #89 | Python padrão somou matrizes e calculou acurácia/F1; valores coincidentes com JSON. Não é reprodução de inferência nem verificação do hash do CSV. Fórmula e resultados no [registro](../../metricas/REGISTRO_E_ANALISE.md). |

O timeout apenas limita a execução; a repetição terminou antes desse limite.
Não foram definidos `CI`, `SENTIA_TESTES_SEM_MONGODB`, URI de produção, chave
XFetch ou credenciais locais para forçar aprovação. Não foi criado `.env`.
SHA-256 de uv.lock inspecionado:
`2381e8b78eee786bdfd2ca0d2f087d88b48ac467d08f66c56c9975b951a8517a`.

## Skips, avisos e dependências reais

Os **25 SKIP** locais são: **17** em `test_persistencia_leitura.py` e **8** em
`test_repositorio.py`. Motivos literais: MongoDB de teste indisponível e MongoDB
local indisponível. O JSON contém os 25 node IDs/motivos; o log contém as linhas.
O arquivo de leitura tem 25 itens, dos quais oito testes unitários passam sem
banco; sete era a seleção histórica reportada no PR #88, não a contagem atual
de todos os testes sem banco.

`test_persistencia_leitura.py` usa `MONGODB_URI_TESTE` (padrão localhost), banco
aleatório e exige falha se `CI` estiver definido e o banco não responder.
`test_repositorio.py` usa URI localhost e banco fixo de teste, apaga esse banco
antes/depois e pula quando indisponível, inclusive no CI. Não confundir os
comportamentos. O workflow de B fornece `mongo:7`, healthcheck e
`MONGODB_URI_TESTE=mongodb://127.0.0.1:27017`; no log E1 não há skips.

Os dez avisos locais são de depreciação Starlette/httpx: uso de httpx no TestClient
e argumento timeout nesse cliente. Não foram suprimidos; não são falhas funcionais.
A atualização dessas dependências não pertence ao escopo documental.

**BERTweet real: NÃO EXECUTADO** nesta inspeção. O grupo ml não foi instalado;
analisadores/pipelines são substituídos nas suítes. Há baseline sklearn treinado
em corpus sintético pequeno, que não mede qualidade no corpus real. A inferência
de três exemplos em `docs/qa/pr44-pr45/` é evidência histórica, sem reexecução
atual e sem comprovar generalização.

**XFetch real: NÃO EXECUTADO**. Os testes usam requisições/respostas simuladas;
não houve consumo de crédito nem chamada à API paga. **Navegador + API + MongoDB
+ pesos reais em conjunto: NÃO EXECUTADO**. AppTest e TestClient exercitam
integrações em processo com substitutos. Avaliação BPSAD completa: **NÃO
EXECUTADA**, PR #89 segue em revisão; ver limites no registro de métricas.

## Inspeção das fontes e governança

Antes das edições foram consultados Git e GitHub (API do plugin GitHub e gh):

- #81 integrado em B; #83 aberto, head `7009500027fe1acfbe6dad997ef79730453c29b3`;
  #89 aberto, head `4a0e338c2a4f919b7095c3821339228b9a7c620b`; #85/#86 abertas.
- #45/#67/#77/#88 mesclados; #67 e #88 tiveram como destino branches de autores,
  não developer diretamente. Integração posterior é verificável no histórico
  de B. Detalhes no [registro de defeitos](DEFEITOS_E_CORRECOES.md).
- `gh project list --owner FGA0138-MDS-Ajax --format json`: falhou por ausência
  do escopo `read:project`. SP/velocidade/burndown ficam N/D, sem concluir
  inexistência de dados no board nem solicitar mudança automática de permissões.
- Tentativa de criar `docs/inspecao-sol-medium` a partir de origin/developer:
  Git recusou porque `refs/heads/docs` existe. Foi preservada a branch docs e
  usada a branch exclusiva da worktree `inspecao/sol-medium`, cujo HEAD inicial
  era exatamente B. Esse é o desvio de nome em relação à ordem de trabalho.

Material acadêmico consultado: formulário do professor, arquivo local
`Formulario Inspeção_professor.pdf`, SHA-256
`21ffd871e1ea8d2dc95f465ff481053afa2f1a78b03370537fb89225636438cc`.
Texto extraído por `pdftotext -layout`; conferidos Quadro 6 (plano/GQM/coleta/análise)
e seção 3.5 de testes (plano/teoria/5W1H/execução/correções). O formulário contém
também numeração/quadros repetidos; não se escolheu ou atribuiu nota de inspeção.
A Mini-tarefa GQM separada e `PACOTE_PRE_INSPECAO_LISKOV.zip` continuam não
localizados; sua localização foi solicitada ao usuário. O GQM da Visão e o
roteiro completo de testes foram recuperados antes da publicação, conforme a
identificação abaixo. Nenhum PDF ou arquivo de instrução foi republicado.

## Fonte histórica recuperada

Na conferência final dos arquivos ZIP locais, foi localizado o pacote
`Correções Doc_Visao.zip`, SHA-256
`c5949c0b6f9d5c51d7aec324e4e73e106e1114d1f6fe733a8309f0f21605eab6`.
Foram lidos somente os materiais Liskov relevantes, sem republicar o arquivo
contendo trabalhos de outras equipes:

- PDF original `T03_Liskov -Documento de Visao do Produto e Projeto Escopo.pdf`,
  dentro do ZIP Liskov interno; 41 páginas, v1.0.0 de 30/09/2026. SHA-256
  `9da7c31fa07a012bfa68e541dcbdc18453075256377737253a7a3b84506c7ccd`.
- PDF de mesmo nome, anotado pelo professor, no pacote externo. SHA-256
  `0233fc7f48d259e1a893c19fd9a67ee599b34f6c634348e6e29e5a8499bd24a6`.

Comandos: extração seletiva com `zipfile.ZipFile` para `/tmp`, sem gravar originais
na worktree; `pdftotext -layout` em ambos; `pdfinfo` e SHA-256 via hashlib.
A versão anotada produziu avisos de aparência/streams no pdftotext, mas a extração
do original concluiu sem esses erros. O confronto textual usou o original como
referência e os comentários legíveis da cópia anotada como observações de revisão;
validação visual integral das anotações NÃO EXECUTADA.

Seções confrontadas: 5.1 (pp. 28–32, GQM), 6.1 (pp. 33–34, estratégia), 6.2
(pp. 35–39, T01–T18) e backlog (pp. 25–27). A fonte confirma T01 coleta, T02
importação, T08 classificação e T18 responsividade; registra RNF02 no roteiro e
RF02 no backlog para responsividade. O plano mantém essa divergência para decisão
formal. A revisão GQM inclui as questões de cobertura e concordância sem medidas
correspondentes no histórico, apontadas pelo professor, e preserva limites
históricos de 80%, 20% e 85%/70% como referências a fundamentar, sem criar resultados.

## Arquivos entregues e pendências

- `docs/metricas/PLANO_GQM_VIGENTE.md` e `REGISTRO_E_ANALISE.md`.
- Neste diretório: `PLANO_TESTES_ATUAL.md`, `MATRIZ_RASTREABILIDADE.md`,
  `RELATORIO_EXECUCAO.md`, `DEFEITOS_E_CORRECOES.md` e evidências textuais/JSON.

Pendências: revisão/aceite da PO; Mini-tarefa GQM separada/pacote de pré-inspeção;
conciliação RF02/RNF02 em T18 e novas pré-condições BERTweet de T04–T08;
reprodução independente da #85/PR #89; revisão do #83; coleta prospectiva de
SP/snapshots; aceite dos roteiros T04–T07 e decisões de meta/custo; testes reais
do fluxo completo; funcionalidades T14–T17 ainda incompletas conforme matriz.
O PR desta entrega é uma proposta para developer e **não representa homologação**.
Os seis documentos tiveram links relativos validados por script Python; contagens
por arquivo foram confrontadas com o JUnit. `git diff --cached --check` é a
verificação de espaços/formatação antes de cada commit. Alterações documentais
posteriores ao pytest não alteram o código B testado; não foi repetida a suíte
sem mudança de código.

## Contagens locais por arquivo

Fonte: JUnit da execução E2, agrupado pelo módulo de teste (classes parametrizadas
do mesmo módulo somadas). Cobertura detalhada por módulo de produção no log local.

| Arquivo em tests/ | Coletados | PASS | SKIP | FAIL/ERROR |
|---|---:|---:|---:|---:|
| `test_analisar_em_lotes.py` | 5 | 5 | 0 | 0 |
| `test_api.py` | 17 | 17 | 0 | 0 |
| `test_api_administracao.py` | 50 | 50 | 0 | 0 |
| `test_aquisicao.py` | 25 | 25 | 0 | 0 |
| `test_auditoria_datasets.py` | 3 | 3 | 0 | 0 |
| `test_avaliacao.py` | 16 | 16 | 0 | 0 |
| `test_classificacao.py` | 14 | 14 | 0 | 0 |
| `test_comparar_modelos.py` | 5 | 5 | 0 | 0 |
| `test_consultas_api.py` | 48 | 48 | 0 | 0 |
| `test_csv_importer.py` | 96 | 96 | 0 | 0 |
| `test_database.py` | 35 | 35 | 0 | 0 |
| `test_experimentos_bpsad.py` | 14 | 14 | 0 | 0 |
| `test_importacao.py` | 20 | 20 | 0 | 0 |
| `test_integracao_conjunta.py` | 10 | 10 | 0 | 0 |
| `test_painel_administracao.py` | 75 | 75 | 0 | 0 |
| `test_painel_arquitetura.py` | 18 | 18 | 0 | 0 |
| `test_painel_config.py` | 12 | 12 | 0 | 0 |
| `test_painel_filtros.py` | 18 | 18 | 0 | 0 |
| `test_painel_fonte_api.py` | 92 | 92 | 0 | 0 |
| `test_painel_fonte_mock.py` | 7 | 7 | 0 | 0 |
| `test_painel_transformacoes.py` | 11 | 11 | 0 | 0 |
| `test_painel_ui.py` | 18 | 18 | 0 | 0 |
| `test_persistencia_leitura.py` | 25 | 8 | 17 | 0 |
| `test_pesquisa_hibrida.py` | 9 | 9 | 0 | 0 |
| `test_pipeline.py` | 19 | 19 | 0 | 0 |
| `test_qa_t09_t10.py` | 19 | 19 | 0 | 0 |
| `test_repositorio.py` | 72 | 64 | 8 | 0 |
| `test_xfetch.py` | 58 | 58 | 0 | 0 |
| `test_xfetch_pipeline.py` | 3 | 3 | 0 | 0 |
| **Total (29 arquivos)** | **814** | **789** | **25** | **0** |
