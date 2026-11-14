# Matriz de divergências — revisão acadêmica do SentIA

**Corte:** 14/11/2026; `origin/developer` após fetch: `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. **Estado:** proposta para revisão; não homologa requisitos nem substitui os originais v1.0.0.

## 1. Método e limites

Precedência: código, configuração, testes e histórico Git; decisões/PRs/issues; documentos acadêmicos históricos. “Implementado” significa encontrado na base indicada; “simulado” significa uso de dublê; “declarado” identifica relato de terceiros; “aceito” exige registro da PO. Fechamento de issue ou merge não basta para este último estado.

Foram lidos o formulário completo do professor (PDF local, 17 páginas) e as fontes técnicas abaixo. Não foram localizados os PDFs de Visão, Arquitetura e Mini-tarefa GQM, nem `PACOTE_PRE_INSPECAO_LISKOV.zip`. Também não existem na base os arquivos `docs/inspecao/REGISTRO_PRE_INSPECAO.md`, `MATRIZ_EVIDENCIAS.md` e `PLANO_REGULARIZACAO.md`. Localização solicitada ao usuário. Assim, as afirmações históricas abaixo são **transcrições indiretas da issue #86/ADR**, ou trechos de Markdown efetivamente inspecionados; não são citações conferidas dos PDFs. Página histórica: N/D. A comparação integral e a preservação exata de todas as seções dos originais permanecem pendentes.

## 2. Divergências e propostas

O Quadro 1 separa o problema documental da proposta de reparo. Seus IDs permitem encaminhamento ao Quadro 9 do formulário, após confirmação pelo grupo inspetor; as prioridades abaixo não são notas ou severidades atribuídas pelo inspetor.

**Quadro 1 — Afirmações, evidências, decisões e redação proposta**

| ID / prioridade | Afirmação antiga e localização | Evidência no código/PR | Situação no corte | Decisão formal pendente | Proposta de redação |
| --- | --- | --- | --- | --- | --- |
| D01 / alta | Visão §§1.3, 3, 4.4 e 5 e Arquitetura §§2.4/2.6: pipeline scikit-learn/TF-IDF, conforme [#86][I86]; PDF não conferido | [Classificador][C1] e [baseline][C2]; [#16][I16] | Caminho padrão instancia BERTweet; baseline separado | Ratificar RF03–RF07 e T04–T08 | O SentIA usa inferência do checkpoint português via PySentimiento; TF-IDF/LogReg é comparador experimental. |
| D02 / alta | Treinamento próprio em Jupyter/Colab, relatado por [#86][I86] | [Pipeline][C3], [scripts][C10], `notebooks/.gitkeep` | Scripts versionados de avaliação; não há demonstração de treinamento próprio do Transformer | Atualizar ambiente e Métrica 2.1 | Inferência com modelo pré-treinado; avaliação por scripts. Treino do baseline fica restrito ao experimento. |
| D03 / alta | Remoção externa de stopwords e stemming como etapas obrigatórias, conforme [ADR-001][C11] e [#86][I86] | [C1][C1], [C3][C3], [teste de negação][T1] | Wrapper recebe texto preservado; teste usa analisador falso | Aprovar ADR-001 e revisar RF04/RF05 | Não aplicar essas operações externas na via BERTweet; comportamento interno da biblioteca exige verificação própria. |
| D04 / alta | TF-IDF obrigatório antes do BERTweet, conforme [#8][I8] | [C2][C2] e [C3][C3] | Não faz parte do caminho padrão | Ratificar RF06/T07 | A representação da via BERTweet pertence ao modelo/biblioteca; TF-IDF é exclusivo do baseline. |
| D05 / média | ADR-001 §4: criação do analisador sem checkpoint explícito | [C1][C1] e [T1][T1] | `model_name` e `batch_size` explícitos no HEAD; revisão dos pesos não fixada ali | Atualizar ADR por seu responsável; definir rastreio da revisão | O wrapper solicita `pysentimiento/bertweet-pt-sentiment`; revisão efetivamente carregada ainda precisa ser registrada. |
| D06 / alta | “Rotas de negócio pendentes”, [arquitetura PC1][H1] | [API][C4], [administração][C5] | Análise, consulta, resumo, importação e coleta existem no código | Aceite por fluxo; issues #21/#23–#25/#58 seguem abertas | Essas rotas estão integradas; homologação e execução real têm evidências separadas. |
| D07 / alta | “Repositório CRUD pendente”, [H1][H1] | [repositório][C6], [dependências][C7]; PRs #84/#87 no histórico da base | Inserção, deduplicação, índices e leitura integrados; não comprova CRUD completo de atualização/exclusão | Aceite RF08 e execução isolada com MongoDB | A API de análises dispõe de persistência e consulta MongoDB; não declarar operações ausentes como entregues. |
| D08 / alta | “Login apenas mock” como retrato atual; [README PC1][H2] | [autenticação][C8] e [administração][C5] | scrypt, tokens opacos, expiração, revogação e limitação de falhas implementados | Confirmar política de acesso e publicação | Administração tem autenticação na API; rotas `/analises` não usam a dependência de Administrador neste HEAD. |
| D09 / alta | Pesquisa híbrida “NÃO IMPLEMENTADO”, [proposta histórica][H3] | [pesquisa][C9], [C5][C5], [PR #81][P81] | Versão lexical em memória mesclada; MongoDB/Vector Search não participam dessa busca | PO: escopo, relevância, custo e autorização do merge anterior | Existe versão de teste que reutiliza registros em memória e pode complementar via XFetch; busca semântica segue proposta. |
| D10 / alta | Mesclagem tomada como aprovação da busca | [P81][P81]: descrição restringe merge e aponta falta de aceite, mas `merged_at` é 13/11/2026 20:40:34 UTC | Merge `1723a7d`; anuência formal não demonstrada pelas fontes consultadas | Solicitar registro de decisão humana; não reverter automaticamente | Integrado tecnicamente, com pendências de governança/aceite. |
| D11 / alta | XFetch tratado como integração real homologada | [aquisição][C12], [teste][T3], [P81][P81] | Cliente real implementado; testes inspecionados simulam HTTP; nenhuma coleta real nesta revisão | Aprovar orçamento e ambiente de teste | Aquisição disponível sob chave/configuração; sem evidência nova de operação real. |
| D12 / alta | TweetSentBR presumido completo ou equivalente a coleta ao vivo | [adaptador][C13], [#3][I3], [C5][C5] | Leitura condicionada a corpus local; disponibilidade de texto precisa de auditoria | Confirmar fonte e licença; não presumir tamanho útil | TweetSentBR é fonte de aquisição quando disponível; BPSAD é corpus de avaliação de outro domínio. |
| D13 / alta | RNF01 aproximadamente 80% tratado como atingido ou reduzido informalmente | [#85][I85], [PR #89][P89], [experimentos][H4] | #89 aberto, head `4a0e338`; relata 67,70%/70,10% de acurácia e 55,43%/59,65% F1 macro; sem reprodução nesta revisão | Reproduzir e deliberar sobre meta/domínio | Preservar meta original; resultados declarados abaixo dela não comprovam aceite ou generalização a tweets. |
| D14 / alta | Walkthrough/contagens históricas usados como CI do HEAD | [PR #83][P83], [workflow][C14] | #83 aberto, referência `fe83ad0`; workflow atual prevê MongoDB `mongo:7` | QA verificar run do SHA, skips e serviços | Identificar sempre SHA/ambiente/execução; números históricos não representam o corte atual. |
| D15 / média | Modo de demonstração tomado como produto real | [configuração][C15], [app][C16], [testes de integração][T2] | Painel inicia em `mock`; há cliente API e testes com dependências substituídas | Homologar painel/API/modelo/banco reais | Escolher modo explicitamente e identificar dados fictícios; integração simulada não demonstra implantação. |
| D16 / alta | Publicação web apresentada como realizada | [#62][I62], [#86][I86] | Intenção de hospedagem registrada; issue aberta; nenhuma implantação demonstrada nesta revisão | Escolher infraestrutura/responsável e autorizar publicação | Publicação é entrega planejada, condicionada à configuração e validação. |
| D17 / média | Correspondência bibliográfica/ABNT supostamente concluída | Formulário §3.1 e Quadro 5; PDFs acadêmicos indisponíveis | Só checklist e referências novas verificáveis | Fornecer originais e template normativo adotado | Conferência visual e auditoria bibliográfica integral pendentes; não declarar conformidade ABNT. |
| D18 / média | Nome “BERTweet” associado automaticamente ao artigo inglês | [ficha do checkpoint][R1] e [artigo inglês][R3] | Ficha portuguesa identifica base BERTabaporu; nome no projeto é mantido por rastreabilidade | Revisar precisão terminológica e bibliografia | Identificar checkpoint completo; artigo inglês não comprova proveniência do modelo português. |

Fonte: elaboração desta revisão a partir das fontes fixadas abaixo e das consultas GitHub de 14/11/2026. D01–D04 não atestam leitura dos originais.

## 3. Encaminhamento e cobertura

Visão: [rascunho](VISAO_ATUALIZADA_RASCUNHO.md). Arquitetura: [rascunho](ARQUITETURA_ATUALIZADA_RASCUNHO.md). Formatos: [checklist](REVISAO_ABNT.md). Decisões: [pauta para a PO](DECISOES_PENDENTES_PO.md). Execução e limites: [relatório](RELATORIO_ENTREGA.md).

O Quadro 7 exige identidade/versões, problema/contexto, ciclo/processo, backlog/planejamento e métricas/testes. O Quadro 8 exige identidade/versões, propósito/escopo, definições e visões arquiteturais. As seções propostas cobrem esses temas; a equivalência integral com os PDFs permanece bloqueada pela ausência das fontes. Não preencher notas do formulário: atribuição do grupo inspetor.

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
