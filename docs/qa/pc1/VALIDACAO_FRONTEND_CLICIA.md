# Validação do frontend da Clicia — PC1

Data: 09/11/2026. PR avaliado: [#70](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/70),
head `61926febc667fb669130469adeceddf971983b6b`, três commits, 21 arquivos
(17 arquivos textuais e quatro imagens). Substitui o #66, **fechado sem merge**.
Nenhum arquivo do backend do #66 foi reutilizado.

## Escopo inspecionado

Diff completo: navegação, contrato, fábrica de fontes, clientes administrativo HTTP/mock,
páginas, seções de filtros/indicadores, transformações, dois arquivos de testes,
CHANGELOG e documentação/wireframes. O #70 não modifica `src/servico`, `src/dados`,
Makefile, dependências uv ou workflow em relação à developer auditada.

O dashboard oferece Aplicar/Limpar, período com pontas opcionais, sentimento,
rejeição de intervalo invertido preservando o filtro anterior e aviso de exclusão
dos textos sem data. Os indicadores mock iniciam em 17 registros, com 47%, 24% e
29% (100%). Agosto retorna cinco registros e informa quatro textos sem data excluídos.
Login fictício habilita Administração; sem sessão há Entrar; expiração e logout
retornam ao login. Coletas apenas simulam andamento e conclusão.

## Contratos e limites

- `contrato.py`: sentimentos positivo/neutro/negativo, datas e contagens tipadas;
  sessão com token fora do repr, expiração UTC, importação e coleta separadas.
- `administracao_api.py`: valida JSON, campos obrigatórios, strings, inteiros
  (rejeita bool), contagens importados+descartados e analisados≤coletados, estados
  de coleta e datas com fuso. Envia Bearer somente às rotas protegidas.
- HTTP 401/403 tratam credencial/sessão; 404 informa rota ausente; 400/415/422,
  413, 429, timeout/conexão, 500 e JSON inválido têm mensagens públicas.
- `administracao_mock.py`: autenticação de exemplo, leitura/contagem local de CSV e
  coletas com números fixos; não persiste nem classifica o arquivo enviado.
- `CONTRATO-API.md` descreve rotas **propostas**, não existentes. FastAPI/OpenAPI
  real confirmou somente `/health`; rotas administrativas e análises retornam 404.
- A soma de motivos de descarte e políticas de limite/retentativa/token permanecem
  pontos de homologação do contrato real; não foi implementado backend nesta revisão.

## Problemas comprovados e correções

Correções em [PR #71](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/71),
branch própria `fix/pr70-ensaio-pc1`, derivada do head da autora:

| Problema | Evidência | Correção |
|---|---|---|
| CSV com campo >131.072 caracteres lançava `_csv.Error` sem tratamento; aspas malformadas não tinham erro de parse claro | Duas regressões falharam antes da correção | Leitura estrita e conversão de `csv.Error` para `ErroFonteDados`, sem alterar limite global |
| Aplicar filtros/Limpar truncados em 820 px com menu aberto | `tablet-antes.png` | Duas colunas para preservar rótulos dos botões |
| Limpar mudava resultados mas mantinha datas visíveis no navegador, prejudicando a próxima aplicação | Captura `limpar-antes.png` e ciclo real no Chrome; AppTest anterior não detectava a divergência cliente/servidor | Callback limpa o estado dos widgets antes de renderizá-los; novo teste de campos/reaplicação e ensaio real |
| Cabeçalho de teste citava `tests/test_api_administracao.py`, inexistente | Busca no diff e na árvore do #70 | Texto corrigido: são testes mock, sem backend administrativo integrado |
| PR de correção dirigido a `feat/painel-frontend` não recebia check | Consulta inicial de #71 sem checks | Destino acrescentado ao filtro do workflow existente |

Commits: `eb071a0` (correções), `e40acf3` (isolamento da regressão),
`222a498` (CI), `bcd75e7` (reset dos campos no navegador). Autoria/committer usam a identidade Git configurada pelo usuário.
O teste de campo longo fixa/restaura o limite global do módulo csv: a suíte de
importação de produção pode ampliá-lo em outro teste. Uma execução intermediária
falhou por esse acoplamento; o log foi preservado e o teste foi isolado, sem
relaxar a asserção ou mudar o comportamento para conseguir aprovação.

## Testes executados

| Ambiente | Passed | Failed | Skipped | Errors | Cobertura src |
|---|---:|---:|---:|---:|---:|
| #69+#70 originais (`ca25e12`) | 458 | 0 | 0 | 0 | 94% |
| Administração + filtros corrigidos | 62 | 0 | 0 | 0 | Não medida nesta execução |
| #69+#70+correção (código `bfaf7da`) | 461 | 0 | 0 | 0 | 94% |

As contagens foram obtidas em execuções novas, não reutilizadas de relatórios antigos.
Ruff frontend e F/E9 geral, `uv sync --locked`, `uv lock --check` e diff check aprovados.
Um aviso de depreciação Starlette/httpx não causou falhas.

## Integração com #69

Worktree `/tmp/sentia-ensaio/integracao`, branch
`test/pc1-integracao-frontend-atualizado`, base `c6fc535`.
#69 `b9d8326` + #70 `61926fe`: **sem conflitos**; CHANGELOG mesclado automaticamente.
Correções de código também mesclaram sem conflitos. A habilitação da CI em #71
produziu conflito somente em `.github/workflows/ci.yml`; preservado o workflow
mais abrangente do #69, que cobre todos os destinos de PR. Head dessa resolução:
`f3bfeeca8b173d794973bb10ea9895383bf8b3ce`. A correção posterior de Limpar foi
integrada em `bfaf7da4437493f5ee9b44022d4979623b232add`, SHA da suíte final.
Não houve alteração de dependências ou backend.

README do #69 continua descrevendo o cenário A; o roteiro novo distingue os cenários.
Os relatórios e o roteiro anteriores foram preservados como registros históricos.

## Evidências e parecer

Logs e capturas em [evidencias/ensaio-final/](evidencias/ensaio-final/).
Ver também [relatório do ensaio](RELATORIO_ENSAIO_FINAL.md) e
[roteiro atualizado](ROTEIRO_PC1_ATUALIZADO.md).

Parecer: **APROVAR COM RESSALVAS após incorporar/revisar #71**, limitado ao frontend
mock e ao cliente de contrato proposto. Não equivale ao aceite de autenticação,
persistência, coleta real, classificação BERTweet ou integração administrativa.
A apresentação deve declarar esses limites antes de mostrar a administração.

## Ensaio visual e funcional

Chrome 157.0.8103.38, automatizado com Playwright 1.64.1 instalado em ambiente
separado do projeto. Dashboard e Administração foram renderizados e inspecionados
em **1440, 820 e 390 px**, com capturas; sem rolagem horizontal do documento.
No celular o menu fica recolhido e a navegação exige rolagem vertical normal.
Em tablet com menu aberto o rótulo do indicador Analisados ainda pode abreviar;
recolher o menu dá mais espaço. Isso não é certificação completa de acessibilidade
nem teste em dispositivo físico.

Fluxos reais exercitados no navegador: período agosto/invertido, manutenção de
resultados anteriores, Limpar e reaplicação, sentimento, login mock, menu com/sem
sessão, importação válida, 1 importado/2 descartados, campo longo com erro tratado,
coleta simulada até conclusão, logout, estados vazio/erro e API indisponível.
Expiração de sessão é coberta por AppTest e pelo contrato; não se esperou uma hora
de sessão real. A rodada final concluiu com todos os checks do roteiro aprovados.

[Dashboard desktop](evidencias/ensaio-final/dashboard-1440.png),
[tablet](evidencias/ensaio-final/dashboard-820.png),
[celular](evidencias/ensaio-final/dashboard-390.png),
[administração celular](evidencias/ensaio-final/administracao-390.png),
[erro de CSV tratado](evidencias/ensaio-final/importacao-erro-tratado.png).
