# SentIA — Documento de Visão: rascunho de revisão

**Instituição:** Universidade de Brasília; MDS, turma T03, equipe Liskov, 2026.2. **Data:** 14/11/2026. **Estado:** minuta 0.1 para a issue [#86][I86], sem substituir v1.0.0. **Base técnica:** `developer`, `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`.

## 1. Identificação, propósito e organização

Esta minuta reúne a visão do produto e do projeto com base no código e nas issues atuais. A organização temática contempla identificação, contexto, produto, escopo, processo, equipe, backlog, planejamento, riscos, métricas, testes e aceite. Os PDFs de Visão/Arquitetura/GQM e o pacote de pré-inspeção não foram disponibilizados no ambiente. Portanto, **não é possível garantir a preservação integral da organização, redação, requisitos e tabelas originais**. A reconciliação seção a seção com esses documentos é condição para publicar uma nova versão acadêmica.

Os estados aqui descritos são técnicos. Critérios marcados ou issues fechadas no GitHub não constituem, isoladamente, homologação. As divergências e fontes estão na [matriz](MATRIZ_DIVERGENCIAS.md); as propostas dependentes de ratificação estão na [pauta da PO](DECISOES_PENDENTES_PO.md).

**Quadro 1 — Controle de revisão**

| Identificação | Data | Responsabilidade | Situação |
| --- | --- | --- | --- |
| v1.0.0 histórica, conforme ordem de trabalho | N/D sem PDF | Autoria e revisão originais a conferir | Preservar sem sobrescrita |
| Minuta 0.1 | 14/11/2026 | Preparação técnica: Codex, frente Sol High; revisão humana pendente | Proposta; base `1723a7d` |
| Próxima versão acadêmica | N/D | Héllen e equipe, conforme #86 | Somente após reconciliação, revisão e aceite |

Fonte: esta revisão e [#86][I86]. O quadro distingue minuta de versão publicada.

## 2. Problema, contexto e partes interessadas

O projeto pretende apoiar a interpretação de sentimentos em textos em português, especialmente publicações de redes sociais relacionadas a temas. O volume de textos exige aquisição, classificação e apresentação de resultados de forma compreensível. A proposta é acadêmica e experimental; classificações e amostras coletadas não autorizam inferências sobre toda a população. A diferença entre o domínio de redes sociais e avaliações de produtos deve acompanhar qualquer resultado no BPSAD ([#3][I3], [#85][I85], [H4][H4]).

**Quadro 2 — Posicionamento proposto do produto**

| Aspecto | Declaração para revisão |
| --- | --- |
| Público | Usuários que desejam explorar distribuições de sentimentos; Administrador que opera entradas e coletas |
| Necessidade | Organizar textos e visualizar classificações e filtros com origem e limites explícitos |
| Produto | SentIA, painel Streamlit com serviço FastAPI e componentes de aquisição/classificação/dados |
| Benefício esperado | Reduzir leitura manual e tornar resultados consultáveis e auditáveis |
| Limites | Inferência automática pode errar; corpus pode ser incompleto; busca lexical pode ser irrelevante; uso de serviço externo tem custo |

Fonte: síntese proposta a partir de [#16][I16], [#27][I27], [#58][I58] e [PR #81][P81]. O benefício é objetivo do produto, sem medição nova nesta revisão.

Partes interessadas: PO (priorização e aceite), Scrum Master (coordenação), equipe técnica (implementação e revisão), usuário/administrador (uso e avaliação), professor e grupo inspetor (avaliação acadêmica). Identificações completas da equipe devem ser reconciliadas com o quadro original antes da publicação.

## 3. Escopo e comportamento do produto

O caminho principal inspecionado é aquisição/importação → validação de registros → inferência do checkpoint `pysentimiento/bertweet-pt-sentiment` → documento com sentimento/probabilidades/modelo/datas → persistência ou armazenamento em memória conforme o fluxo → API/painel. O modelo é pré-treinado; o projeto não demonstra treinamento próprio do Transformer. O baseline TF-IDF com regressão logística é um comparador isolado ([C1][C1], [C2][C2], [C3][C3], [C10][C10]).

A configuração padrão do painel é `mock`. O modo `api` dispõe de clientes HTTP; a API possui rotas de análise, consulta, resumo e administração. A persistência de `/analises` pode usar MongoDB ou memória, enquanto datasets, sessões, coletas administrativas e pesquisa do PR #81 ficam em memória no processo. Não tratar todos os caminhos como persistentes ([C4][C4]–[C9][C9], [C15][C15], [C16][C16]).

A pesquisa experimental reutiliza registros disponíveis em memória por palavras normalizadas/radicais e pode completar a meta via XFetch. Não realiza Vector Search nem consulta semântica ao MongoDB. A existência de tratamento de palavras na **pesquisa** não implica esse tratamento antes do **classificador** ([C9][C9]). O merge do [PR #81][P81] não elimina suas pendências de custo e aceite.

Publicação web, revisão de metas, busca semântica, exportação de resumos e mudanças de escopo dependem das decisões registradas na [#86][I86] e na [pauta da PO](DECISOES_PENDENTES_PO.md). Não incluir novas funcionalidades no escopo aprovado por simples atualização desta minuta.

## 4. Requisitos e backlog rastreável

O Quadro 3 concilia identificadores encontrados nas issues com a evidência atual. É uma reconstrução documental provisória; prioridades não explicitadas são N/D. RF03–RF07 preservam a identificação histórica, mas a nova redação exige ratificação formal. Um requisito pode ter código e continuar com critérios/DoD pendentes.

**Quadro 3 — Backlog e critérios para revisão**

| RF / US / issue | Prioridade registrada | Situação técnica e critério de aceite a demonstrar |
| --- | --- | --- |
| RF01 / US01, US22 / #2, #60 | Should | Importador e upload existentes; validar CSV válido/inválido/vazio, preservação de campos e contagem de descartes [C5][C5] |
| RF02 / US02, US23 / #1, #61 | Must em #61 | Adaptadores, coleta e acompanhamento existentes; demonstrar fonte disponível, progresso e erros; coleta externa não equivale a corpus local [C5][C5], [C12][C12], [C13][C13] |
| RF03 / US03 / #5 | N/D | Texto original validado e preservado na via BERTweet; propor aceite de entradas com negação, acento e pontuação [C1][C1], [C3][C3] |
| RF04 / US04 / #6 | N/D | Sem remoção externa de stopwords; revisar requisito histórico e T05, sem marcar remoção antiga como executada [C11][C11] |
| RF05 / US05 / #7 | N/D | Sem stemming externo; revisar requisito e T06; baseline atual também não contém stemming explícito [C1][C1], [C2][C2] |
| RF06 / US06 / #8 | N/D | Sem TF-IDF no BERTweet; baseline isolado; revisar T07 [C2][C2], [I8][I8] |
| RF07 / US07 / #16 | N/D | Wrapper e pipeline existentes; demonstrar modelo real, ordem, probabilidades e identificação da revisão [C1][C1], [I16][I16] |
| RNF01 / US08 / #17, #85 | Must em #85 | Meta original aproximadamente 80% preservada; medir acurácia e F1 separadamente, com hashes, amostragem e limites; #89 em revisão [I85][I85], [P89][P89] |
| RF08 / US09 / #20 | Must | Inserção, índices, deduplicação e leitura integrados; demonstrar banco isolado e tratamento de falhas [C6][C6] |
| RF09 / US10 / #21 | Must | Rotas FastAPI implementadas; conferir contrato, erros e smoke real; `/health` sozinho não atende [C4][C4] |
| RF10 / US11 / #23 | Must | Consulta paginada na API; validar ordem, limite e vazio; listagem integral na UI exige aceite próprio [C4][C4], [C6][C6] |
| RF11 / US12 / #24 | Must | Filtro temporal implementado; confirmar uso de publicação, limites UTC e ausência de data [C6][C6] |
| RF12 / US13 / #25 | Should | Filtro por três sentimentos; validar combinação com paginação e datas [C4][C4] |
| RF13 / US14 / #27 | Must | Painel com fontes mock/API; demonstrar consumo real e estados de erro/vazio; issue aberta [C15][C15], [I27][I27] |
| RF14 / US15 / #28 | Must | Não declarar gráfico aceito com base apenas em indicadores; conferir visualização requerida e contagens na homologação |
| RF15 / US16 / #29 | Should | Resumo estatístico é requisito registrado; validar texto e filtros; não pressupõe LLM nem exportação |
| RF16 / US17 / #30 | Could | Nuvem de palavras opcional, sem impor pré-processamento à via BERTweet; não demonstrada nesta revisão |
| Responsividade / US18 / #31 | Should | Identificador RF/RNF original a conferir; resoluções e aceite visual pendentes de reconciliação |
| Administração / US21 / #58, #59 | Must | Login/token no backend e navegação no painel; verificar expiração, logout e recusa sem autenticação [C5][C5], [C8][C8] |
| US19/US20 e T18 históricos | N/D | Texto e mapeamento original indisponíveis; não suprimir nem renumerar antes de ler os PDFs |

Fonte: issues #1–#32, #58–#63, #85/#86 consultadas em 14/11/2026 e fontes técnicas citadas. Links individuais das issues podem ser obtidos em `https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/<número>`; o relatório registra a consulta. A ausência de evidência nesta revisão não prova ausência de implementação.

## 5. Organização, processo e responsabilidades

Proposta de processo: desenvolvimento iterativo por sprints, com refinamento do backlog, planejamento pela equipe, implementação em branches, revisão por PR, verificação automatizada e revisão do incremento pela PO. As issues registram sprints e DoD; isso não comprova execução de todas as cerimônias. Mudanças que alterem requisitos devem vincular decisão, testes afetados, versão documental e aceite ([#5][I5], [#20][I20], [#86][I86]).

**Quadro 4 — Responsabilidades documentadas, sujeitas à reconciliação cadastral**

| Frente | Responsabilidade encontrada | Fonte / limite |
| --- | --- | --- |
| Produto/documentos | Héllen (Hellen Clicia na ata) / equipe | #86; tabela de integrantes do PDF indisponível |
| Coordenação/auditoria | Renato; QA referido como Figueirin | #3, #17, #19, #22, #85; confirmar nomes/atribuições finais |
| Aquisição | Breno; apoio Renato | #1–#3 |
| ML | Ricardo e Gabriel | #5–#10, #16/#17/#85 |
| Dados | Maria Eduarda e Julia | #11/#12/#20 |
| Interface | Juliana, com Héllen na revisão | #13/#14/#27/#31 |
| API, publicação e usabilidade | Responsável ainda a definir em issues específicas | #21/#58/#62/#63; não atribuir por omissão ao QA |

Fonte: issues consultadas; nomes, matrículas e quadro completo de autoria devem ser conferidos no original. Evitar republicar dados pessoais desnecessários. A atribuição funcional acima não é lista de autoria/aprovação desta minuta.

## 6. Planejamento e replanejamento

**Quadro 5 — Calendário planejado recuperado das issues e milestones**

| Sprint | Período original referido | Foco | Leitura no corte de 14/11 |
| --- | --- | --- | --- |
| 1 | 13–19/10/2026 | Aquisição | Período passado; issues relatam carry-over; não declarar entrega pontual |
| 2 | 20–26/10/2026 | Preparação; antecipação de banco/UI | Replanejamento de 29/10 registrado nas issues; preservar o plano original |
| 3 | 27/10–02/11/2026 | Inferência e avaliação | Uso de BERTweet; avaliação continua em #85/#89 |
| 4 | 03–09/11/2026 | Persistência e API | Código integrado posteriormente; critérios de aceite ainda precisam de evidência |
| 5 | 10–16/11/2026 | Consultas e filtros; #85/#58 | Em curso no corte; não declarar encerramento |
| 6 | 17–23/11/2026 | Dashboard e integração | Futura no calendário; código antecipado não equivale a aceite de sprint |
| 7 | 24–30/11/2026 | Correções, publicação e documentos | Futura; #62/#63/#86 abertas |

Fonte: descrições de milestones e corpos de #1/#5/#16/#20/#23/#27/#62. Datas ainda precisam de cotejo direto com a Tabela 2.3.1 do PDF. A diferença entre datas originais e prazos de regularização do GitHub deve permanecer registrada.

Story Points, velocidade e série diária de burndown: **N/D nesta revisão**. Não calcular velocidade por quantidade de PRs nem preencher estimativas retroativas. Critérios propostos de replanejamento: dependência indisponível, falha nos critérios de aceite, custo externo sem autorização, métrica insuficiente ou mudança de escopo. A equipe registra causa, itens movidos, nova previsão, responsável e decisão da PO, mantendo datas e resultados históricos. A frente de gestão deve consolidar esse registro; esta minuta não altera o calendário.

## 7. Riscos, restrições e mitigação proposta

**Quadro 6 — Riscos e ações**

| Risco / evidência | Impacto | Ação proposta e responsável funcional |
| --- | --- | --- |
| Disponibilidade/licença dos corpora [I3][I3] | Entrada incompleta e publicação indevida | Dados: inventariar licença, hashes, volume útil e acesso; publicar somente artefatos permitidos |
| Mudança de domínio BPSAD → tweets [I85][I85] | Resultado não generalizável | ML/QA: separar domínio e independência; revisar meta com PO |
| Revisão do checkpoint não fixada [C1][C1] | Reprodução frágil | ML: registrar artefato/revisão/versões efetivos |
| Administração/pesquisa em memória [C5][C5] | Perda após reinício e inconsistência entre processos | Backend/PO: delimitar uso local e decidir persistência |
| Rotas de análise sem dependência de autenticação [C4][C4] | Exposição ou consumo indevido se publicadas | Backend/PO: definir acesso e limites antes de publicar |
| Custo/limites XFetch [P81][P81] | Despesa e coleta incompleta | PO: orçamento e responsável; sem chamada real nesta revisão |
| Mocks confundidos com resultado real [C15][C15] | Aceite inválido | UI/QA: identificar modo e registrar dependências em cada execução |
| Datas ausentes [C3][C3] | Filtros temporais enganosos | Dados/UI: omitir publicação ausente e informar exclusões |

Fonte: componentes citados e matriz de divergências. Probabilidades e impacto quantitativo: N/D.

## 8. Métricas, testes e critérios de aceite

Qualidade do modelo: preservar RNF01 (~80%) até decisão formal; relatar acurácia, F1 macro e por classe, matriz de confusão, tamanho/distribuição da amostra, domínio, hash do CSV, seed, separação por grupos e revisão do modelo. Os scripts existentes sustentam coleta reprodutível, mas esta revisão não executou inferência real. O [PR #89][P89] está aberto; seus resultados são declarados pelo autor, não reproduzidos aqui ([C10][C10], [H4][H4]).

Usabilidade: [#63][I63] registra meta de pelo menos 85% de sucesso total e nenhuma tarefa abaixo de 70%, com sessões ainda pendentes. Conferir a Métrica 3.1 no PDF antes de ratificar. Projeto: velocidade/burndown dependem de estimativas e histórico reais; N/D no presente recorte. O plano GQM detalhado pertence à frente de métricas; não há cópia do GQM histórico para validar sua completude.

Testes existentes incluem contratos do wrapper, pipeline, API, persistência e arquitetura do painel. Dublês de analisador e HTTP não medem acurácia; testes reais de MongoDB requerem instância isolada; o workflow prevê `mongo:7`, mas sua configuração não prova uma execução verde ([T1][T1]–[T4][T4], [C14][C14]). T04–T08 devem ser reconciliados com o caminho BERTweet; T01–T18 completos dependem do PDF e da frente QA.

Critério proposto para aceite do incremento: requisito/US e dados conhecidos → cenário e resultado esperado → execução com SHA, ambiente e dependências explícitos → revisão técnica → decisão da PO. Não aprovar requisito antigo de remoção de palavras com teste de preservação de palavras; registrar alteração de requisito antes. Para release/publicação, exigir configuração de acesso, segredos fora do Git, fluxos reais validados e autorização específica ([#58][I58], [#62][I62], [#86][I86]).

## 9. Referências e pendências de publicação

As referências técnicas a seguir fixam o código do corte. A bibliografia original e a correspondência com citações dos PDFs permanecem N/D. Para publicar a revisão: obter originais/pacote; reconciliar seções e integrantes; deliberar sobre a pauta da PO; executar validações faltantes; revisar apresentação no editor e exportar PDF com nova versão e histórico, preservando v1.0.0.

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
[C8]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/autenticacao.py#L1
[C9]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/pesquisa.py#L1
[H4]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/experimentos_bpsad.md#L1
[I16]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/16
[I20]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/20
[I27]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/27
[I3]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/3
[I5]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/5
[I58]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/58
[I62]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/62
[I63]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/63
[I8]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/8
[I85]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/85
[I86]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86
[P81]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/81
[P89]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89
[T1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/tests/test_classificacao.py#L94
[T4]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/tests/test_painel_arquitetura.py#L1
