# Relatório da frente Sol High — revisão acadêmica

**Data:** 14/11/2026. **Branch:** `inspecao/sol-high`. **Base após `git fetch origin`:** `developer`, `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`.

## 1. Entrega e alcance

Foram preparados os cinco artefatos pedidos: [matriz](MATRIZ_DIVERGENCIAS.md), [Visão](VISAO_ATUALIZADA_RASCUNHO.md), [Arquitetura](ARQUITETURA_ATUALIZADA_RASCUNHO.md), [ABNT](REVISAO_ABNT.md) e [decisões da PO](DECISOES_PENDENTES_PO.md), além deste relatório. Todas as alterações estão em `docs/revisao-academica/`. Código, índices, outros diretórios documentais e PDFs originais foram preservados; arquivos de instrução não integram a entrega.

O nome prescrito `docs/inspecao-sol-high` foi recusado pelo Git porque a referência local `docs` já existe e impede criar referência subordinada. Foi mantida a branch exclusiva já preparada `inspecao/sol-high`, cujo HEAD inicial coincide com `origin/developer`. Não houve exclusão/renomeação da branch `docs`, alteração de histórico nem merge.

**Limite material:** os PDFs de Visão, Arquitetura e Mini-tarefa GQM e o ZIP de pré-inspeção não foram localizados em workspace, Downloads ou demais arquivos acessíveis pesquisados. Os três registros esperados de `docs/inspecao/` também não estão na base. Sua localização foi solicitada ao usuário durante o trabalho. Assim, as minutas são propostas técnicas substanciais, mas a revisão integral dos originais, a preservação exata de suas seções e a auditoria bibliográfica/visual completa **não estão concluídas**. Esse limite deve permanecer no PR até acesso às fontes e reconciliação.

## 2. Evidências principais

| Fonte consultada em 14/11/2026 | Estado observado | Implicação |
| --- | --- | --- |
| [PR #81](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/81) | Mesclado em 13/11/2026 20:40:34 UTC; merge `1723a7d`; descrição ainda restringe merge e aponta falta de aceite/custo | Pesquisa lexical em memória implementada como teste; autorização/aceite não inferidos |
| [PR #83](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/83) | Aberto; head `7009500027fe1acfbe6dad997ef79730453c29b3`, referência histórica `fe83ad0` | Walkthrough não integrado; contagens não representam o HEAD atual |
| [Issue #85](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/85) | Aberta; pede reprodução e encaminhamento da meta à PO | RNF01 não foi alterado nem declarado atendido |
| [PR #89](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89) | Aberto; head `4a0e338c2a4f919b7095c3821339228b9a7c620b` | Artefatos examinados como evidência submetida pelo autor, sem reprodução da inferência |
| [Issue #86](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86) | Aberta; atualização documental planejada para Sprint 7 | Minutas antecipam proposta rastreável, sem publicar nova versão homologada |
| Código em `1723a7d` | Rotas, autenticação, persistência/consulta e pesquisa existem; limites discriminados na matriz | Não usar README/arquitetura PC1 como descrição atual sem contexto histórico |

Fonte: metadados via conector GitHub, issues via `gh`, arquivos locais e histórico da base. Cada fato técnico nas minutas aponta para fonte fixada no SHA ou issue/PR datado.

## 3. Exame dos artefatos do PR #89

Foram lidos os JSONs [avaliação](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/4a0e338c2a4f919b7095c3821339228b9a7c620b/docs/resultados_bpsad/avaliacao_pc1_final.json) e [amostragem](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/4a0e338c2a4f919b7095c3821339228b9a7c620b/docs/resultados_bpsad/relatorio_amostragem_pc1.json), sem corpus textual. Eles informam amostra 10.000, treino 8.000, teste 2.000, seed 42 no relatório de amostragem, versões, distribuição e hash SHA-256 da amostra na avaliação (`607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6`).

Uma checagem aritmética em JavaScript recalculou `acurácia = soma(diagonal)/total` e `F1 macro = média(2*diagonal/(soma_linha+soma_coluna))` a partir das duas matrizes: baseline `0,701` e `0,5964593556860648`; modelo português `0,677` e `0,5543063931312299`. As duas matrizes totalizam 2.000 e os resultados coincidem com os campos JSON (tolerância `1e-12`). Treino + teste coincide com amostra 10.000; hash tem formato hexadecimal de 64 caracteres.

Isso confirma **consistência interna dos números recebidos**, sem verificar o hash contra o CSV, a execução relatada, a origem das previsões, independência do pré-treinamento ou a revisão efetivamente carregada. Não houve reprodução de inferência, benchmark controlado ou aceite da PO nesta frente. O tempo registrado inclui treino/carregamento e RSS após execução não é pico. Resultados abaixo da referência de ~80% continuam assunto de decisão formal, sem revisão unilateral da meta.

## 4. Verificações efetivamente realizadas

| Comando / operação | Resultado e limite |
| --- | --- |
| `git fetch origin`; `git rev-parse origin/developer`; `git rev-parse HEAD` | Base e HEAD inicial coincidem em `1723a7d`; fetch precisou de acesso ao diretório Git compartilhado fora do worktree |
| `git log -8 --oneline`; `git ls-tree -r --name-only origin/docs` e `origin/main` | Histórico e árvores inspecionados; sem edição dessas branches |
| Conector GitHub: metadados #81/#83/#89 e issues #85/#86 | Estados descritos no Quadro de evidências; consulta não demonstra aceite nem checks verdes |
| `gh issue list --repo FGA0138-MDS-Ajax/2026.2-T03-Liskov --state all --limit 100 --json number,title,state,body,milestone` | Backlog e calendário recuperados; consulta de rede executada com permissão ampliada após falha no sandbox |
| `pdftotext -layout` e `pdfinfo` no formulário local | Extração integral de texto e identificação de 17 páginas A4; não valida margens visuais |
| Leitura de código, testes, ADR, documentos e páginas primárias do checkpoint/artigos | Referências ligadas a caminhos/linhas e consulta bibliográfica datada; nenhum treinamento presumido |
| Recalcular métricas dos JSONs de #89 em JavaScript | Consistência aritmética aprovada, conforme §3; sem modelo ou corpus |
| `python3 /tmp/sentia-sol-high-validar.py` | Aprovado: 6 Markdown, 122 referências nomeadas, 149 links e 81 fontes com caminho/linha válidos; não verifica disponibilidade HTTP externa nem renderização |
| `git diff --check` e conferência do diff preparado | Sem erros de whitespace; conferir novamente antes dos commits |

Suíte do produto, MongoDB real, download/inferência BERTweet, XFetch real, CI remota deste PR e renderização visual de Mermaid/PDF: **NÃO EXECUTADOS nesta frente documental**. Nenhum resultado de teste do produto foi inferido de contagens históricas. Mermaid recebeu conferência textual, sem atestar renderização.

Também foram consultadas as reviews e a discussão do PR #81 via conector: ambas retornaram listas vazias. Isso não demonstra inexistência de decisões em outros canais; não foi localizada nessas fontes evidência de aceite formal da PO para a pesquisa.

## 5. Pendências e handoff

Para concluir a missão integral: obter PDFs/pacote e reconciliar conteúdo; revisar bibliografia e apresentação final no editor; obter decisões da [pauta da PO](DECISOES_PENDENTES_PO.md); revisar por outro integrante e registrar nova versão apenas depois do aceite. Estado do critério de pronto: **parcial, bloqueado especificamente quanto às fontes históricas ausentes**; não há impedimento à revisão das propostas técnicas já entregues.

PR dirigido a `developer`, com o título prescrito `docs(visao-arquitetura): proposta de atualização rastreável para inspeção`, deve permanecer rascunho enquanto faltarem as fontes. O link efetivo é informado na entrega ao usuário. Na ausência de escrita remota, gerar patch somente destes arquivos e registrar o impedimento. Nenhum merge ou deploy integra esta entrega.
