# Relatório da frente Sol High — reconciliação do PR #90

**Data de referência:** 14/11/2026; adendo posterior com a Mini-tarefa GQM fornecida pelo usuário e consolidação pós-merge. **Branch de origem:** `inspecao/sol-high`. **Base técnica:** `developer`, `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`, reconfirmada por fetch na retomada. **PR:** [#90](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/90), destino `developer` (**integrado**).

## 1. Entrega atual e histórico

Os cinco documentos pedidos e este relatório estão em `docs/revisao-academica/`: [matriz](MATRIZ_DIVERGENCIAS.md), [Visão](VISAO_ATUALIZADA_RASCUNHO.md), [Arquitetura](ARQUITETURA_ATUALIZADA_RASCUNHO.md), [ABNT](REVISAO_ABNT.md) e [decisões da PO](DECISOES_PENDENTES_PO.md). Os seis foram atualizados diretamente nesta branch; nenhum arquivo de outra frente foi incorporado ou editado. Não houve merge, publicação de PDF, dados pessoais, corpus, credenciais ou instruções.

O envio inicial (`ad1eebd`, `d645d75`) registrou falta de acesso às fontes acadêmicas e não consultou os logs de CI. Essas ressalvas foram **superadas nesta retomada**, sem apagar o histórico Git. O nome `docs/inspecao-sol-high` continuou inviável por já existir a referência `docs`; preservada a branch exclusiva `inspecao/sol-high`, sem renomear ou excluir branches.

Foram consultados originalmente na retomada os três registros de inspeção do Argon e a tabela de equivalência (commit `25f258786981f29552d2df2f1b4597ab7ef01c44` do [PR #92][A1]), e a evidência QA (commit `84530e4b3d0ac1762b9100c4c728e6208ffca810` do [PR #91][Q2]). Na consolidação pós-merge, `#90`, `#91`, `#92` e `#94` encontram-se integrados à `developer`, e as referências locais apontam diretamente para os arquivos vigentes na branch.

## 2. Reconciliação factual concluída

| Item solicitado | Conferência direta e alteração |
| --- | --- |
| I-01: fontes originais | Lidos todos os textos dos PDFs de Visão (41 páginas) e Arquitetura (29), com hashes e páginas na [auditoria ABNT](REVISAO_ABNT.md#1-fontes-e-alcance-da-leitura-direta). Criadas tabelas de correspondência de todas as seções originais nas minutas; GQM da Visão pp. 28–32 e T01–T18 pp. 35–39 incluídos |
| I-02: US19/US20 | Backlog original pp. 25–27 contém US01–US18, sem US19/US20; US21–US23 são posteriores. Permissão de exportação P1 fica na Arquitetura §2.7 **p. 27**, sem identificador US20; não atribuir remoção de US19/US20 à v1.0.0 |
| I-03: CI com MongoDB | Consultados job e log do run [43503741871][E1], SHA `1723a7d`: success, `mongo:7`, 814 PASS, 0 FAIL, 0 SKIP, cobertura 93%; separado de reexecução local e ML/XFetch reais |
| IDs da PO | Aplicado o catálogo canônico PO-01a/b a PO-14a/b, com 18 subitens e tabela de todos os 14 aliases PO01–PO14. PO09 desdobrado em PO-03/04 e PO12 em PO-09/10/11a/13 |
| ABNT e histórico | Inventário de todas as referências originais, Cohn sem entrada, acessos em branco, citações em imagens, figuras/tabelas, sumário e Apêndice A auditados com localização; sem editar/publicar os originais |
| Precisões sobre o dossiê Argon | Bibliografia de Arquitetura é p. 29; exportação é p. 27; RF08 consta na Sprint 3 na linha do backlog p. 26, contradizendo o calendário S4; Beck (2000) está na imagem da Figura 2.1 p. 9 da Visão. São refinamentos de fonte primária, sem alterar arquivos do Argon |

Fonte: PDFs identificados por hash na revisão ABNT, [plano do Argon][A1], [QA #91][Q2] e logs de CI. Não se usa anotação avaliativa docente ou matrícula como evidência publicada.

### 2.1 Evidência remota de CI e seus limites

Run em 13/11/2026: [43503741871](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871), [job test 132155891920][E1]. Consulta nesta sessão retornou `completed/success` para todas as etapas, inclusive lock, Ruff e pytest. O log confirma checkout de `1723a7d`, criação de container `mongo:7`, `TOTAL 2699 176 93%` e `814 passed, 10 warnings in 21.40s`, sem itens pulados ou falhas.

Esse resultado prova execução da suíte com banco de teste real nos testes que usam a coleção. O classificador e XFetch usam dublês; não é reprodução do modelo real, chamada paga, benchmark ou fluxo navegador→API→banco→pesos reais. Esta frente **não reexecutou localmente** a suíte do produto. A execução local do Sol Medium é distinta (789 PASS, 25 SKIP e 92%), não deve substituir os números remotos. A CI do primeiro envio do PR #90 também consta verde em `43646136042`; o status do novo head deve ser conferido no próprio PR após o push.

## 3. Exame dos artefatos do PR #89 (envio inicial)

Foram lidos os JSONs [avaliação](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/4a0e338c2a4f919b7095c3821339228b9a7c620b/docs/resultados_bpsad/avaliacao_pc1_final.json) e [amostragem](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/4a0e338c2a4f919b7095c3821339228b9a7c620b/docs/resultados_bpsad/relatorio_amostragem_pc1.json), sem corpus textual. Eles informam amostra 10.000, treino 8.000, teste 2.000, seed 42 no relatório de amostragem, versões, distribuição e hash SHA-256 da amostra na avaliação (`607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6`).

Uma checagem aritmética em JavaScript recalculou `acurácia = soma(diagonal)/total` e `F1 macro = média(2*diagonal/(soma_linha+soma_coluna))` a partir das duas matrizes: baseline `0,701` e `0,5964593556860648`; modelo português `0,677` e `0,5543063931312299`. As duas matrizes totalizam 2.000 e os resultados coincidem com os campos JSON (tolerância `1e-12`). Treino + teste coincide com amostra 10.000; hash tem formato hexadecimal de 64 caracteres.

Isso confirma **consistência interna dos números recebidos**, sem verificar o hash contra o CSV, a execução relatada, a origem das previsões, independência do pré-treinamento ou a revisão efetivamente carregada. Não houve reprodução de inferência, benchmark controlado ou aceite da PO nesta frente. O tempo registrado inclui treino/carregamento e RSS após execução não é pico. Resultados abaixo da referência de ~80% continuam assunto de decisão formal, sem revisão unilateral da meta.

## 4. Operações e validações desta retomada

| Operação / comando | Resultado e limite |
| --- | --- |
| `git fetch origin`; `git rev-parse origin/developer origin/chore/inspecao-argon origin/inspecao/sol-medium` | Fontes atualizadas; base técnica e fontes de reconciliação fixadas nos SHAs citados |
| `git show <SHA>:docs/inspecao/{PLANO_REGULARIZACAO,REGISTRO_PRE_INSPECAO,MATRIZ_EVIDENCIAS}.md` e relatório QA | Conteúdo das outras frentes consultado sem merge/cópia na branch High |
| `pdftotext -layout` nos dois PDFs originais; leitura de todas as páginas extraídas | Visão 1–41 e Arquitetura 1–29, incluindo identificação/histórico, backlog, requisitos, processo, restrições, GQM/testes e bibliografia |
| `pdfinfo`, `hashlib.sha256` e renderização seletiva com `pdftoppm`/visualização | Hashes/paginação conferidos; imagens das pp. 4/9/18 da Visão e 8/19/20/21/24/25/26 da Arquitetura inspecionadas; sem inferir medição integral de margens |
| Conector GitHub: metadados PR #90/#92; jobs do run 43503741871; log do job 132155891920 | Estados remotos/logs consultados diretamente, não inferidos de YAML |
| `python3 /tmp/sol-high-validar-reconciliacao.py` | Aprovado após a Mini-tarefa: 6 Markdown, 135 referências nomeadas, 180 links, 99 fontes Git fixadas, 18 IDs/14 aliases, hashes de 3 PDFs, tabelas, escopo e rastreio de matrículas; zero PDFs rastreados/preparados; sem validação HTTP externa ou conformidade visual integral |
| `git diff --check`; `git diff --cached --check`; `git diff --name-only` | Conferência de whitespace e escopo limitado aos seis documentos, antes dos commits |

A verificação aritmética BPSAD do §3 é do envio inicial e continua identificada como tal; nesta retomada não foi necessário repetir inferência ou suíte sem mudança de código. Não houve acesso XFetch real, deploy ou publicação dos arquivos privados. A conferência visual dos Mermaid novos continua pendente de renderização final.

### 4.1 Adendo — Mini-tarefa GQM fornecida pelo usuário

Lido diretamente `T03_Liskov - Tarefa GQM.pdf`, **14 páginas**, SHA-256 `ecb629621eb253d4b85f78aa17f42db1012b4498369268681595782fc6cda0d4`, mantido na raiz local sem rastreamento pelo Git. Comandos: `pdftotext -layout`, `pdfinfo`, SHA-256 com hashlib; leitura de todas as páginas e inspeção de imagens das pp. 3/9/13. Não foram publicados PDF, matrículas ou cópia integral da extração.

Confronto com Visão pp. 28–32, Arquitetura e plano GQM do #91: recuperados limiares de F1 por classe <60%, auditoria >90%, faixas de acurácia, M3 temporal e gatilhos ±20%/duas Sprints da velocidade. A Mini-tarefa identifica Cohn (2005) como Agile Estimating and Planning. Novos achados D26–D29 e Quadro 7 da Visão preservam esses critérios como históricos a ratificar, sem criar dados ou mudar requisitos.

**Estado histórico no corte `#90` vs. regularização pós-merge no `#94`:** no corte inicial do `#90`, faltava conciliar essas regras no plano `#91`; em seguida, o [PR #94](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/94) incorporou tecnicamente em [`PLANO_GQM_VIGENTE.md`](../metricas/PLANO_GQM_VIGENTE.md) e [`REGISTRO_E_ANALISE.md`](../metricas/REGISTRO_E_ANALISE.md) (`R17–R22`) o limiar de `F1 < 60%` por classe, `M3` (`G1/Q1.7`), as faixas e a regra `±20%` (`R21`). Permanecem abertas a resolução final de fronteiras/prioridades pela PO, adaptação de treinamento/notebook ao BERTweet e correção de títulos/sumário/quadros do documento acadêmico (`PO-01a/b`, `PO-02`, `PO-12` e `PO-14b`). Os destinos CSV citados pelo PDF são planejamento, não prova de coleta; SP e série temporal continuam N/D.

Somente os seis Markdown desta frente foram atualizados. A validação documental foi repetida, incluindo hash/14 páginas da Mini-tarefa, integridade das faixas/IDs e verificação explícita de que **nenhum PDF está rastreado ou preparado para commit**. Não houve reexecução de ML, XFetch ou suíte do produto, pois não houve mudança de código.

## 5. Material ainda não recuperado e aceite

**Material específico ainda não acessado nesta sessão:** `PACOTE_PRE_INSPECAO_LISKOV.zip`, sem afirmar inexistência. A Mini-tarefa GQM independente foi fornecida depois pelo usuário e lida integralmente, além do GQM incorporado à Visão; a ressalva anterior sobre esse PDF está superada. A cópia anotada da Visão tem auditoria de outra frente; a presente leitura direta é do original identificado, sem declaração de auditoria visual integral das anotações.

**Estado da reconciliação:** I-01/I-02/I-03 e equivalência da PO resolvidos nos seis Markdown; leitura factual/textual integral de Visão/Arquitetura concluída. Edição final ABNT, margens, bibliografia final (incluindo a referência de Cohn recuperada na Mini-tarefa e os acessos reais), revisão por outro integrante, aceite da PO e homologação do produto continuam pendentes e não são apresentados como concluídos.

**Draft (registro histórico do envio do `#90`, posteriormente integrado em `developer`):** o PR deixou o estado de revisão para análise técnica da proposta reconciliada e foi integrado à `developer` em `6bc1c17`; os arquivos faltantes acima não impediram revisar os fatos já verificados. Isso não autoriza publicação final automática sem revisão da nova edição e decisão da PO.

**Decisões ainda sem resposta datada:** PO-01a/b (modelo, ADR e testes), PO-02 (meta RNF01/reprodução), PO-03/04 (domínio/licença), PO-05a/b (pesquisa e governança #81), PO-06 (custos), PO-07/08 (acesso/persistência), PO-09/10 (datas/RNF02/T18), PO-11a/b (nuvem e propostas US19/US20), PO-12 (GQM/usabilidade), PO-13 (cenários e aceite por SHA) e PO-14a/b (deploy e publicação acadêmica/governança). Aliases e evidências estão na [pauta](DECISOES_PENDENTES_PO.md).

[A1]: ../inspecao/PLANO_REGULARIZACAO.md
[Q2]: ../qa/inspecao/RELATORIO_EXECUCAO.md
[E1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920
