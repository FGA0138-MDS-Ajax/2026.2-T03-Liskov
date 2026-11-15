# Matriz de divergências — revisão acadêmica do SentIA

**Corte:** 14/11/2026; `origin/developer` após fetch: `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. **Estado:** proposta para revisão; não homologa requisitos nem substitui os originais v1.0.0.

## 1. Método e limites

Precedência: código, configuração, testes e histórico Git; decisões/PRs/issues; documentos acadêmicos históricos. “Implementado” significa encontrado na base indicada; “simulado” significa uso de dublê; “declarado” identifica relato de terceiros; “aceito” exige registro da PO. Fechamento de issue ou merge não basta para este último estado.

**Reconciliação I-01–I-03 do PR #92:** os PDFs foram recuperados e agora lidos diretamente nesta frente: Visão v1.0.0, 30/09/2026, 41 páginas, e Arquitetura v1.0.0, histórico de 07/10 sem ano, 29 páginas. Identidades SHA-256, locais privados de leitura, páginas e limites visuais estão na [revisão ABNT](REVISAO_ABNT.md#1-fontes-e-alcance-da-leitura-direta). A indisponibilidade registrada no primeiro envio do #90 está superada. O GQM incorporado à Visão (pp. 28–32) e a Mini-tarefa GQM separada (14 páginas), fornecida posteriormente pelo usuário, foram lidos integralmente. A [auditoria da Mini-tarefa](REVISAO_ABNT.md#31-mini-tarefa-gqm-separada) fixa hash, páginas e limites. Apenas o ZIP `PACOTE_PRE_INSPECAO_LISKOV.zip` continua sem recuperação nesta sessão, sem afirmar inexistência.

Os três registros `REGISTRO_PRE_INSPECAO.md`, `MATRIZ_EVIDENCIAS.md` e `PLANO_REGULARIZACAO.md`, originalmente entregues no [PR #92 / Argon][A1] (commit `25f2587`), encontram-se agora integrados na `developer` junto às entregas de `#90`, `#91` e `#94`. As decisões seguem a [equivalência canônica do Argon][A1], preservando aliases PO01–PO14. Os IDs D01–D18 abaixo pertencem ao PR #90, distintos dos D01–D04 do PR #91.

## 2. Divergências e propostas

O Quadro 1 separa o problema documental da proposta de reparo. Seus IDs permitem encaminhamento ao Quadro 9 do formulário, após confirmação pelo grupo inspetor; as prioridades abaixo não são notas ou severidades atribuídas pelo inspetor.

**Quadro 1 — Afirmações, evidências, decisões e redação proposta**

| ID / prioridade | Afirmação antiga e localização | Evidência no código/PR | Situação no corte | Decisão formal pendente | Proposta de redação |
| --- | --- | --- | --- | --- | --- |
| D01 / alta | Visão pp. 5–8, 18, 25–26 e 30; Arquitetura pp. 10–16, 23 e 26: pipeline scikit-learn/TF-IDF (leitura direta) | [Classificador][C1] e [baseline][C2]; [#16][I16] | Caminho padrão instancia BERTweet; baseline separado | Ratificar RF03–RF07 e T04–T08 | O SentIA usa inferência do checkpoint português via PySentimiento; TF-IDF/LogReg é comparador experimental. |
| D02 / alta | Visão p. 8 (§1.4) e p. 30 (Métrica 2.1); Arquitetura p. 15 (§2.4.2): treinamento em Jupyter/Colab | [Pipeline][C3], [scripts][C10], `notebooks/.gitkeep` | Scripts versionados de avaliação; não há demonstração de treinamento próprio do Transformer | Atualizar ambiente e Métrica 2.1 | Inferência com modelo pré-treinado; avaliação por scripts. Treino do baseline fica restrito ao experimento. |
| D03 / alta | Visão p. 25 (RF04/RF05) e p. 36 (T05/T06); Arquitetura p. 16: remoção de stopwords e stemming | [C1][C1], [C3][C3], [teste de negação][T1] | Wrapper recebe texto preservado; teste usa analisador falso | Aprovar ADR-001 e revisar RF04/RF05 | Não aplicar essas operações externas na via BERTweet; comportamento interno da biblioteca exige verificação própria. |
| D04 / alta | Visão p. 36 (T07) e Arquitetura pp. 10–11: TF-IDF na entrada do classificador clássico histórico | [C2][C2] e [C3][C3] | Não faz parte do caminho padrão | Ratificar RF06/T07 | A representação da via BERTweet pertence ao modelo/biblioteca; TF-IDF é exclusivo do baseline. |
| D05 / média | ADR-001 §4: criação do analisador sem checkpoint explícito | [C1][C1] e [T1][T1] | `model_name` e `batch_size` explícitos no HEAD; revisão dos pesos não fixada ali | Atualizar ADR por seu responsável; definir rastreio da revisão | O wrapper solicita `pysentimiento/bertweet-pt-sentiment`; revisão efetivamente carregada ainda precisa ser registrada. |
| D06 / alta | “Rotas de negócio pendentes”, [arquitetura PC1][H1] | [API][C4], [administração][C5] | Análise, consulta, resumo, importação e coleta existem no código | Aceite por fluxo; issues #21/#23–#25/#58 seguem abertas | Essas rotas estão integradas; homologação e execução real têm evidências separadas. |
| D07 / alta | “Repositório CRUD pendente”, [H1][H1] | [repositório][C6], [dependências][C7]; PRs #84/#87 no histórico da base | Inserção, deduplicação, índices e leitura integrados; não comprova CRUD completo de atualização/exclusão | Aceite RF08; execução com MongoDB demonstrada no CI [E1][E1] | A API de análises dispõe de persistência e consulta MongoDB, testadas no CI; não declarar operações ausentes como entregues. |
| D08 / alta | “Login apenas mock” como retrato atual; [README PC1][H2] | [autenticação][C8] e [administração][C5] | scrypt, tokens opacos, expiração, revogação e limitação de falhas implementados | Confirmar política de acesso e publicação | Administração tem autenticação na API; rotas `/analises` não usam a dependência de Administrador neste HEAD. |
| D09 / alta | Pesquisa híbrida “NÃO IMPLEMENTADO”, [proposta histórica][H3] | [pesquisa][C9], [C5][C5], [PR #81][P81] | Versão lexical em memória mesclada; MongoDB/Vector Search não participam dessa busca | PO: escopo, relevância, custo e autorização do merge anterior | Existe versão de teste que reutiliza registros em memória e pode complementar via XFetch; busca semântica segue proposta. |
| D10 / alta | Mesclagem tomada como aprovação da busca | [P81][P81]: descrição restringe merge e aponta falta de aceite, mas `merged_at` é 13/11/2026 20:40:34 UTC | Merge `1723a7d`; anuência formal não demonstrada pelas fontes consultadas | Solicitar registro de decisão humana; não reverter automaticamente | Integrado tecnicamente, com pendências de governança/aceite. |
| D11 / alta | XFetch tratado como integração real homologada | [aquisição][C12], [teste][T3], [P81][P81] | Cliente real implementado; testes inspecionados simulam HTTP; nenhuma coleta real nesta revisão | Aprovar orçamento e ambiente de teste | Aquisição disponível sob chave/configuração; sem evidência nova de operação real. |
| D12 / alta | TweetSentBR presumido completo ou equivalente a coleta ao vivo | [adaptador][C13], [#3][I3], [C5][C5] | Leitura condicionada a corpus local; disponibilidade de texto precisa de auditoria | Confirmar fonte e licença; não presumir tamanho útil | TweetSentBR é fonte de aquisição quando disponível; BPSAD é corpus de avaliação de outro domínio. |
| D13 / alta | RNF01 aproximadamente 80% tratado como atingido ou reduzido informalmente | [#85][I85], [PR #89][P89], [experimentos][H4] | #89 aberto, head `4a0e338`; relata 67,70%/70,10% de acurácia e 55,43%/59,65% F1 macro; sem reprodução nesta revisão | Reproduzir e deliberar sobre meta/domínio | Preservar meta original; resultados declarados abaixo dela não comprovam aceite ou generalização a tweets. |
| D14 / alta | Walkthrough/contagens históricas usados como CI do HEAD; I-03 corrige insuficiência de evidência no primeiro envio do #90 | [PR #83][P83], [workflow][C14] | #83 aberto, referência `fe83ad0`; [E1][E1] confirma 814 PASS, 0 FAIL, 0 SKIP e 93% em `1723a7d`, com `mongo:7` | Aceite por requisito; não confundir CI com homologação | Identificar sempre SHA/ambiente/execução; números históricos não representam o corte atual. |
| D15 / média | Modo de demonstração tomado como produto real | [configuração][C15], [app][C16], [testes de integração][T2] | Painel inicia em `mock`; há cliente API e testes com dependências substituídas | Homologar painel/API/modelo/banco reais | Escolher modo explicitamente e identificar dados fictícios; integração simulada não demonstra implantação. |
| D16 / alta | Publicação web apresentada como realizada | [#62][I62], [#86][I86] | Intenção de hospedagem registrada; issue aberta; nenhuma implantação demonstrada nesta revisão | Escolher infraestrutura/responsável e autorizar publicação | Publicação é entrega planejada, condicionada à configuração e validação. |
| D17 / média | Visão pp. 28, 40–41; Arquitetura pp. 3, 16 e 29: bibliografia/sumário/apêndice | Leitura direta e [auditoria ABNT](REVISAO_ABNT.md) | Cohn citado sem referência; datas de acesso em branco; sumário remete a p. 30 inexistente; Apêndice A não incluído | PO-14b: normalização e exportação final | Corrigir referências verificadas e regenerar sumário; sem declarar conformidade visual final. |
| D18 / média | Nome “BERTweet” associado automaticamente ao artigo inglês | [ficha do checkpoint][R1] e [artigo inglês][R3] | Ficha portuguesa identifica base BERTabaporu; nome no projeto é mantido por rastreabilidade | Revisar precisão terminológica e bibliografia | Identificar checkpoint completo; artigo inglês não comprova proveniência do modelo português. |
| D19 / alta | Visão pp. 25–27 termina em US18; Arquitetura §2.7 p. 27 menciona exportar resumos sem US | I-02 e leitura direta dos dois PDFs | US19/US20 não pertencem à v1.0.0; US21–US23 são posteriores (#59–#61) | PO-11b | Registrar separadamente as propostas posteriores de landing page/exportação; não apresentá-las como requisitos removidos do backlog original. |
| D20 / alta | Visão p. 23: C01→S2, C04→S3, C05/C06→S4; p. 26: RF08→S3 | Tabela 2.3.1 pp. 11–12 prevê aquisição S1, persistência/API S4, consulta S5 e UI S6 | Conflitos internos do plano histórico, inclusive RF08; não os apagar | PO-13 | Propor C01→S1, C04/RF08→S4, C05→S5, C06→S6; C02→S2 e C03→S3 permanecem. |
| D21 / alta | Visão p. 27: US18 rotulada C06/RF02, tipo não funcional; T18 p. 39 e Arquitetura p. 14: RNF02 | Leitura direta; RF02 já identifica coleta | Colisão de identificador | PO-10 | Ratificar C06/RNF02 para responsividade, mantendo vínculo histórico com a linha incorreta. |
| D22 / média | Arquitetura p. 15 dispensa autenticação completa, mas p. 28 exige login/senha P2 | [C8][C8] e [C5][C5] implementam autenticação administrativa | Contradição interna histórica; controle de `/analises` continua decisão | PO-07 | Reconciliar acesso por rota e distinguir proteção implementada de segurança homologada. |
| D23 / média | Arquitetura pp. 16 e 23 exigem texto tratado e data de publicação | [C3][C3], [C19][C19] e contrato [H5][H5] | Texto original preservado; publicação opcional; processamento obrigatório | PO-09 | Não inventar publicação; aplicar filtro de publicação e informar excluídos; texto tratado não é pré-condição da via BERTweet. |
| D24 / média | Visão p. 30 O2/Q4 e p. 32 O3/Q2 sem métricas específicas correspondentes | [plano GQM vigente][Q1]; cobertura real no CI [E1][E1] | Lacunas do GQM histórico confirmadas; 93% cobre código, não concordância humana | PO-12 | Ratificar métricas de cobertura/concordância e justificar limiares; manter SP/burndown N/D quando sem dados. |
| D25 / média | Arquitetura p. 13: 95% das consultas ≤2 s; p. 28 lista navegadores; p. 28 FURPS | Leitura direta dos requisitos de qualidade | Metas históricas, sem benchmark/validação de navegador nesta revisão | PO-13 / PO-14a | Preservar requisitos e registrar verificação pendente; não declarar latência/compatibilidade comprovadas pelo CI. |
| D26 / alta | Mini-tarefa GQM pp. 8–9: acurácia ~80%, faixa esperada 75–90%, atenção 70–79%, crítico <70%, auditoria >90% e F1 de qualquer classe <60% | Leitura direta, [reconciliação GQM da Visão](VISAO_ATUALIZADA_RASCUNHO.md#81-reconciliação-da-mini-tarefa-gqm-separada); incorporado ao [plano GQM vigente][Q1] pelo [PR #94](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/94) | Limiar histórico de 60% e faixas foram conciliados tecnicamente no plano e registro (`R17`/`R19` pós-#94); >90% também satisfaz ≥80%, e a ratificação de fronteiras/arredondamento pela PO segue pendente | PO-02 / PO-12 | Preservar limiares como históricos a ratificar; auditoria precede aceite na proposta; F1 por classe não é F1 macro; não aprovar automaticamente por acurácia. |
| D27 / alta | Mini-tarefa pp. 6–8: scikit-learn, treinamento 80/20, notebook e M3 como variação entre treinamentos | [C1][C1], [C10][C10] e [Q1][Q1] (`G1/Q1.7` adicionado pelo PR #94); arquivos CSV de coleta são destinos planejados no PDF | BERTweet é pré-treinado; Δ temporal (`G1/Q1.7`) não equivale à diferença BERTweet/baseline da mesma execução (`G1/Q1.5`); nenhuma série temporal nova foi produzida (`R18`/`R22`) | PO-01a/b / PO-12 | Adaptar M3 para versões/avaliações comparáveis com mesmo teste identificado; manter N/D sem pares; treino só no baseline ou fine-tuning futuro aprovado; não criar CSV vazio como evidência. |
| D28 / média | Mini-tarefa pp. 10–13: M1/Q2 velocidade, M2/Q1 burndown, ±20% e duas Sprints abaixo de −20% acionam replanejamento | Leitura direta; coleta prospectiva e regra `R21` no [plano GQM vigente][Q1] (pós-PR #94) | Sem SP/aceite/snapshots não há velocidade demonstrável (`N/D`); definição de denominador positivo incorporada no plano `#94`; frequência do burndown permite registro só nas reuniões | PO-12 / PO-13 | Preservar regras históricas, definir média válida >0 e prioridade das faixas; propor snapshot diário e análise nas reuniões, sem retroestimativas. |
| D29 / média | Mini-tarefa pp. 3–14: §2.1 repetido, §3.3 duplicado no sumário, quadros negociais sem número e bibliografia com Cohn | [auditoria ABNT](REVISAO_ABNT.md#31-mini-tarefa-gqm-separada) | Cohn, Agile Estimating and Planning (2005), identificado na bibliografia p. 13; a omissão permanece na Visão original, não na Mini-tarefa | PO-14b | Normalizar títulos/quadros e usar a referência recuperada como proposta para completar a Visão; preservar a distinção entre os dois originais. |

Fonte: elaboração desta revisão a partir das fontes fixadas abaixo e das consultas GitHub de 14/11/2026. D01–D04 foram reconciliados com leitura direta dos originais; páginas referem o PDF identificado pelo hash, não uma cópia anotada.

## 3. Encaminhamento e cobertura

Visão: [rascunho](VISAO_ATUALIZADA_RASCUNHO.md). Arquitetura: [rascunho](ARQUITETURA_ATUALIZADA_RASCUNHO.md). Formatos: [checklist](REVISAO_ABNT.md). Decisões: [pauta para a PO](DECISOES_PENDENTES_PO.md). Execução e limites: [relatório](RELATORIO_ENTREGA.md).

O Quadro 7 exige identidade/versões, problema/contexto, ciclo/processo, backlog/planejamento e métricas/testes. O Quadro 8 exige identidade/versões, propósito/escopo, definições e visões arquiteturais. As seções propostas cobrem esses temas e têm correspondência com as seções originais nos rascunhos; a reconciliação factual/textual dos dois PDFs foi concluída, mantendo decisões e publicação final pendentes. Não preencher notas do formulário: atribuição do grupo inspetor.

<!-- Referências fixadas no corte; PRs e issues consultados em 14/11/2026. -->
[C1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/classificacao/bertweet.py#L15
[C10]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/scripts/experimentos/validar_bpsad.py#L1
[C11]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md#L1
[C12]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/aquisicao/xfetch.py#L1
[C13]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/aquisicao/tweetsentbr.py#L1
[C14]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/.github/workflows/ci.yml#L1
[C15]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/apresentacao/config.py#L21
[C16]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/apresentacao/app.py#L1
[C2]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/classificacao/baseline.py#L18
[C3]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/pipeline.py#L55
[C4]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/main.py#L39
[C5]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/administracao.py#L117
[C6]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/dados/repositorio.py#L65
[C7]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/dependencias.py#L24
[C8]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/autenticacao.py#L1
[C9]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/pesquisa.py#L1
[H1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/arquitetura.md#L1
[H2]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/README.md#L1
[H3]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/pesquisa_hibrida_mongodb_xfetch.md#L1
[H4]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/experimentos_bpsad.md#L1
[I16]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/16
[I3]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/3
[I62]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/62
[I8]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/8
[I85]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/85
[I86]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86
[P81]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/81
[P83]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/83
[P89]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89
[R1]: https://huggingface.co/pysentimiento/bertweet-pt-sentiment
[R3]: https://arxiv.org/abs/2005.10200v2
[T1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/tests/test_classificacao.py#L94
[T2]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/tests/test_api_administracao.py#L1
[T3]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/tests/test_xfetch.py#L1
[A1]: ../inspecao/PLANO_REGULARIZACAO.md
[C19]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/esquemas.py#L8
[E1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920
[H5]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/contratos-dados.md#L1
[Q1]: ../metricas/PLANO_GQM_VIGENTE.md
