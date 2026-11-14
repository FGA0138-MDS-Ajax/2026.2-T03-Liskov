# SentIA — Documento de Visão: rascunho de revisão

**Instituição:** Universidade de Brasília; MDS, turma T03, equipe Liskov, 2026.2. **Data:** 14/11/2026. **Estado:** minuta 0.2 para a issue [#86][I86], sem substituir v1.0.0. **Base técnica:** `developer`, `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`.

## 1. Identificação, propósito e organização

Esta minuta reconcilia o código e as issues com a leitura direta integral do texto da Visão v1.0.0 (30/09/2026, 41 páginas) e da Arquitetura v1.0.0 (07/10, 29 páginas). A identificação por hash e o alcance visual estão na [auditoria ABNT](REVISAO_ABNT.md#1-fontes-e-alcance-da-leitura-direta). Supera a ressalva de indisponibilidade do primeiro envio do PR #90, conforme I-01 do [Argon][A1]. O GQM histórico foi lido nas pp. 28–32 da Visão; a Mini-tarefa GQM separada e o ZIP de pré-inspeção ainda não foram recuperados nesta sessão.

A organização temática abaixo conserva a cobertura das seções originais, com rastreio explícito de suas divergências. Não reproduz nomes associados a matrículas, pontuações de participação ou anotações docentes. A revisão factual/textual integral dos dois documentos não equivale a PDF final normalizado, revisão humana ou aprovação da PO.

Os estados aqui descritos são técnicos. Critérios marcados ou issues fechadas no GitHub não constituem, isoladamente, homologação. As divergências e fontes estão na [matriz](MATRIZ_DIVERGENCIAS.md); as propostas dependentes de ratificação estão na [pauta da PO](DECISOES_PENDENTES_PO.md).

**Quadro 1 — Controle de revisão**

| Identificação | Data | Responsabilidade | Situação |
| --- | --- | --- | --- |
| v1.0.0 histórica, p. 1 | 30/09/2026 | Autoria coletiva registrada como “Todos” | Original preservado; 41 páginas |
| Minuta 0.1 → 0.2 | 14/11/2026 | Codex, frente Sol High; revisão humana pendente | 0.2 reconcilia PDFs, CI e IDs canônicos; base `1723a7d` |
| Próxima versão acadêmica | N/D | Héllen e equipe, conforme #86 | Somente após reconciliação, revisão e aceite |

Fonte: esta revisão e [#86][I86]. O quadro distingue minuta de versão publicada.

### 1.1 Correspondência com a estrutura original

| Seção original / páginas | Cobertura nesta minuta |
| --- | --- |
| 1.1–1.4, pp. 3–8: problema, posição, objetivos e tecnologias | §§2–3; objetivos preservados; pipeline técnico atualizado |
| 2.1–2.2, pp. 8–11: ciclo, equipe e coordenação | §5; funções sem matrículas; práticas previstas separadas de execução comprovada |
| 2.3–2.4, pp. 11–14: calendário e comunicação | §§5–6; Teams para reuniões, GitHub para decisões técnicas e Aprender3 para entregas formais; reuniões semanais e Planning por ciclo são o plano histórico |
| 2.5–2.6, pp. 14–17: riscos e replanejamento | §§6–7; preservar eventos de atraso, fonte, modelo e integração |
| 3, pp. 17–20: processo e DoD | §5 e §8; cinco critérios cumulativos preservados |
| 4.1–4.4, pp. 20–27: épicos, perfis, cenários e backlog | §4 e conciliação C01–C06 no §6 |
| 5.1, pp. 28–32: GQM | §8; manter limiares até PO-02/PO-12 |
| 6.1–6.2, pp. 33–39: estratégia e T01–T18 | §8; mocks/CI/banco real separados; alterações de testes dependem de ratificação |
| 7, pp. 40–41: bibliografia | §9 e auditoria ABNT, sem apagar entradas históricas |

Fonte: leitura direta da Visão identificada na revisão ABNT. A numeração temática desta minuta é própria; a tabela conserva a ligação com o original.

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

O Quadro 3 concilia identificadores encontrados nas issues com a evidência atual. Prioridades RF01–RF16/RNF01 e US18 foram conferidas diretamente nas pp. 25–27 da Visão original; os acréscimos administrativos são posteriores. RF03–RF07 preservam a identificação histórica, mas a nova redação exige ratificação formal. Um requisito pode ter código e continuar com critérios/DoD pendentes.

**Quadro 3 — Backlog e critérios para revisão**

| RF / US / issue | Prioridade registrada | Situação técnica e critério de aceite a demonstrar |
| --- | --- | --- |
| RF01 / US01, US22 / #2, #60 | Should | Importador e upload existentes; validar CSV válido/inválido/vazio, preservação de campos e contagem de descartes [C5][C5] |
| RF02 / US02, US23 / #1, #61 | Must em #61 | Adaptadores, coleta e acompanhamento existentes; demonstrar fonte disponível, progresso e erros; coleta externa não equivale a corpus local [C5][C5], [C12][C12], [C13][C13] |
| RF03 / US03 / #5 | Must | Texto original validado e preservado na via BERTweet; propor aceite de entradas com negação, acento e pontuação [C1][C1], [C3][C3] |
| RF04 / US04 / #6 | Must | Sem remoção externa de stopwords; revisar requisito histórico e T05, sem marcar remoção antiga como executada [C11][C11] |
| RF05 / US05 / #7 | Should | Sem stemming externo; revisar requisito e T06; baseline atual também não contém stemming explícito [C1][C1], [C2][C2] |
| RF06 / US06 / #8 | Must | Sem TF-IDF no BERTweet; baseline isolado; revisar T07 [C2][C2], [I8][I8] |
| RF07 / US07 / #16 | Must | Wrapper e pipeline existentes; demonstrar modelo real, ordem, probabilidades e identificação da revisão [C1][C1], [I16][I16] |
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
| Responsividade / US18 / #31 | Should | Backlog p. 27 registra C06/RF02 (não funcional), colidindo com coleta; T18 p. 39 registra C06/RNF02. Proposta RNF02 depende de PO-10; validação visual pendente |
| Administração / US21 / #58, #59 | Must | Login/token no backend e navegação no painel; verificar expiração, logout e recusa sem autenticação [C5][C5], [C8][C8] |
| US19/US20, menções posteriores / #86 | N/D | Não constam do backlog original US01–US18 (pp. 25–27). Landing page/exportação são decisões posteriores; exportar resumos aparece apenas como permissão P1 na Arquitetura §2.7, p. 27. Deliberação PO-11b |

Fonte: Visão v1.0.0 pp. 25–27, Arquitetura v1.0.0 p. 27, issues #1–#32, #58–#63, #85/#86 consultadas em 14/11/2026 e fontes técnicas citadas. Links individuais das issues podem ser obtidos em `https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/<número>`; o relatório registra a consulta. A ausência de evidência nesta revisão não prova ausência de implementação.

Os seis épicos originais (pp. 20–21) são E01 Aquisição, E02 Preparação, E03 Análise de sentimentos, E04 Persistência/disponibilização, E05 Consulta/filtragem e E06 Visualização. Os perfis P1 (consulta, filtros, gráficos e resumo) e P2 (fontes, coleta e processamento) estão nas pp. 21–22. Login administrativo e US21–US23 foram acrescentados posteriormente nas issues #58–#61; não pertencem ao backlog original US01–US18.

## 5. Organização, processo e responsabilidades

O processo original (Visão pp. 8–10 e 17–20) prevê Scrum com práticas XP/PBL, iterações de cerca de sete dias, refinamento, Planning, desenvolvimento, acompanhamento, revisão de código, integração contínua, Review, Retrospectiva e replanejamento. A DoD da p. 20 exige cumulativamente testes unitários aprovados, CI sem falhas, revisão por pares via PR, critérios validados pela PO e documentação atualizada. A menção original a integração em `main` (p. 19) deve ser contextualizada: a base técnica atual de integração é `developer`, sem promover branches nesta revisão. As issues registram sprints e DoD; isso não comprova execução de todas as cerimônias. Mudanças que alterem requisitos devem vincular decisão, testes afetados, versão documental e aceite ([#5][I5], [#20][I20], [#86][I86]).

**Quadro 4 — Responsabilidades documentadas, sujeitas à reconciliação cadastral**

| Frente | Responsabilidade encontrada | Fonte / limite |
| --- | --- | --- |
| Produto/documentos | Héllen / equipe | Visão p. 1 e Tabela 2.2.1 p. 10; #86 |
| Coordenação/auditoria | Renato; QA referido como Figueirin | #3, #17, #19, #22, #85; confirmar nomes/atribuições finais |
| Aquisição | Breno; apoio Renato | #1–#3 |
| ML | Ricardo e Gabriel | #5–#10, #16/#17/#85 |
| Dados | Maria Eduarda e Julia | #11/#12/#20 |
| Interface | Juliana, com Héllen na revisão | #13/#14/#27/#31 |
| API, publicação e usabilidade | Responsável ainda a definir em issues específicas | #21/#58/#62/#63; não atribuir por omissão ao QA |

Fonte: Visão pp. 1 e 10–11, Arquitetura p. 2 e issues consultadas. A equipe original tem oito integrantes, correspondentes às frentes listadas; a Arquitetura explicita Ricardo/Gabriel em ML. Matrículas e pontos de participação não são reproduzidos. A atribuição funcional não significa aprovação desta minuta.

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

Fonte: leitura direta da Tabela 2.3.1 da Visão pp. 11–12, conferida com milestones e #1/#5/#16/#20/#23/#27/#62. Os percentuais de 0% do plano histórico não são medidas atuais. A diferença entre datas originais e prazos de regularização do GitHub permanece registrada.

A conciliação dos cenários históricos é proposta, não mudança de plano retroativa: C01 consta como S2 na p. 23, mas RF01/RF02 e o calendário preveem S1; C02→S2 e C03→S3 são coerentes; C04 consta S3, mas a Tabela 2.3.1 prevê persistência/API na S4; C05/C06 constam S4, enquanto backlog e calendário preveem S5/S6. A linha RF08 da p. 26 também registra S3, contradizendo a Tabela 2.3.1; propõe-se C04/RF08→S4 em **PO-13**. Essa precisão complementa a síntese do [Argon][A1], que generaliza RF08/RF09 como S4.

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

Fonte: componentes citados e matriz de divergências. O quadro registra riscos atuais, sem estimar probabilidades novas. A tabela histórica pp. 14–16 qualifica dataset/qualidade textual/desempenho do modelo como alta probabilidade e alto impacto; desbalanceamento, integração e inspeção como média/alto; APIs/scraping, atrasos de iteração, indisponibilidade de integrantes, Git e orientações docentes como média/médio; atraso avaliativo como média/alto. Preservam-se ações de fonte alternativa, revisão da amostra/modelo, integração incremental, redistribuição, controle de versão e priorização das entregas. Essas são avaliações históricas, não medições atualizadas.

## 8. Métricas, testes e critérios de aceite

Qualidade do modelo: preservar RNF01 (~80%) até decisão formal; relatar acurácia, F1 macro e por classe, matriz de confusão, tamanho/distribuição da amostra, domínio, hash do CSV, seed, separação por grupos e revisão do modelo. Os scripts existentes sustentam coleta reprodutível, mas esta revisão não executou inferência real. O [PR #89][P89] está aberto; seus resultados são declarados pelo autor, não reproduzidos aqui ([C10][C10], [H4][H4]).

O GQM original (pp. 28–32) contém O1 (burndown diário em Story Points, mas atualização semanal indicada no 5W1H; velocidade por Sprint com variação de até 20%), O2 (acurácia ~80%, densidade de defeitos por história concluída e contagem de débito técnico) e O3 (sucesso de tarefas ≥85% no total e ≥70% por tarefa). O2/Q4 pergunta sobre cobertura e O3/Q2 sobre concordância usuário/sistema, sem métrica específica correspondente no original. O [plano GQM do #91][Q1] mapeia O1→G2, O2→G1/G3 e O3→G4; sua ratificação e a justificativa dos limiares dependem de **PO-12**. A Meta 3.1 da p. 32 e [#63][I63] coincidem; as sessões continuam pendentes. SP, velocidade e burndown atuais permanecem N/D sem histórico verificável; denominadores nulos não geram médias válidas.

A evidência remota [E1][E1] confirma CI verde em `1723a7d`: run `43503741871`, job `132155891920`, **814 PASS, 0 FAIL, 0 SKIP, 93% de cobertura**, com `mongo:7`. Logs e conclusão foram consultados diretamente nesta retomada; não é execução local desta frente. ML/XFetch permanecem simulados, sem comprovar E2E real ou acurácia ([QA #91][Q2]).

O roteiro original pp. 35–39 contém T01 coleta (RF02), T02 importação (RF01), T03 perfis, T04 limpeza, T05 stopwords, T06 stemming, T07 TF-IDF, T08 classificação com `.pkl`, T09 banco, T10 API, T11 histórico na UI, T12 período, T13 sentimento, T14 dashboard, T15 gráficos, T16 resumo, T17 nuvem e T18 responsividade. A proposta mantém IDs: T04–T07 passam a verificar preservação/contrato da via BERTweet após PO-01a, T08 separa inferência de avaliação global após PO-01b; T18 mantém o vínculo RNF02 proposto em PO-10. Dublês não atendem automaticamente aos testes de sistema descritos no original.

Critério proposto para aceite do incremento: requisito/US e dados conhecidos → cenário e resultado esperado → execução com SHA, ambiente e dependências explícitos → revisão técnica → decisão da PO. Não aprovar requisito antigo de remoção de palavras com teste de preservação de palavras; registrar alteração de requisito antes. Para release/publicação, exigir configuração de acesso, segredos fora do Git, fluxos reais validados e autorização específica ([#58][I58], [#62][I62], [#86][I86]).

## 9. Referências e pendências de publicação

As referências técnicas fixam o código do corte. A bibliografia original das pp. 40–41 foi inventariada com conferência de citações na [revisão ABNT](REVISAO_ABNT.md), incluindo Cohn ausente, obras sem chamada localizada e datas em branco. A leitura factual/textual dos dois PDFs está concluída; publicação final ainda exige decisões da PO, revisão humana, testes/medições faltantes e diagramação/exportação sem dados pessoais. A Mini-tarefa GQM separada e o pacote de pré-inspeção não foram recuperados nesta sessão; isso não invalida a leitura do GQM incluído na Visão.

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
[A1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/25f258786981f29552d2df2f1b4597ab7ef01c44/docs/inspecao/PLANO_REGULARIZACAO.md
[E1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920
[Q1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/84530e4b3d0ac1762b9100c4c728e6208ffca810/docs/metricas/PLANO_GQM_VIGENTE.md
[Q2]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/84530e4b3d0ac1762b9100c4c728e6208ffca810/docs/qa/inspecao/RELATORIO_EXECUCAO.md
