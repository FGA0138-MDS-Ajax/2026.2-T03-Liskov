# Decisões pendentes da Product Owner — SentIA

**Corte:** 14/11/2026, base `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. **Estado:** pauta proposta; nenhuma resposta, prazo, estimativa ou aprovação foi presumida. A [matriz de divergências](MATRIZ_DIVERGENCIAS.md) fundamenta as perguntas.

## 1. Perguntas e evidência necessária

O Quadro 1 permite registrar uma decisão por tema, preservando a diferença entre o comportamento já codificado e a autorização formal para mudar escopo ou publicar.

**Quadro 1 — Pauta para deliberação**

| ID / prioridade | Pergunta objetiva para a PO | Evidência e proposta submetida | Registro necessário para encerrar |
| --- | --- | --- | --- |
| PO01 / alta | Aprova o ADR-001 e a ausência de remoção externa de stopwords, stemming e TF-IDF antes do BERTweet? | [C1][C1], [C3][C3], [C11][C11], [T1][T1]; preservar negações no wrapper, sem alegar ganho experimental | Decisão sobre ADR e nova redação RF03–RF06; impacto nos critérios T04–T07; revisão técnica |
| PO02 / alta | Ratifica RF07 como integração de modelo português pré-treinado e o baseline como comparador separado? | [#16][I16], [#86][I86], [C1][C1], [C2][C2]; sem treinamento próprio em Colab/Jupyter demonstrado | Texto aprovado de RF07/US07 e T08; checkpoint/revisão e responsáveis por avaliação |
| PO03 / alta | Qual é o escopo aprovado da pesquisa do PR #81: teste local lexical em memória ou entrega com persistência MongoDB? | [P81][P81], [C5][C5], [C9][C9]; versão de teste já mesclada; sem busca semântica implementada | Issue/US e critérios, relevância mínima, meta/limites, persistência, responsável e aceite |
| PO04 / alta | Existe registro de anuência ao merge de #81, apesar da restrição na descrição? | PR mesclado em 13/11; descrição ainda diz que faltam issue, custo e aceite | Referência à decisão humana; se inexistente, registrar regularização e próximos passos, sem retrodatá-la |
| PO05 / alta | Qual teto financeiro e operacional autoriza para XFetch, por consulta e período, e quem controla os créditos? | [C12][C12], [P81][P81]; limites locais de páginas/quantidade não são orçamento | Valor e unidade aprovados, responsável, frequência, bloqueio ao exceder, ambiente e autorização explícita para teste real |
| PO06 / alta | Administração exige só o perfil atual? As rotas `/analises` devem permanecer acessíveis sem sessão? | [C4][C4], [C5][C5], [C8][C8], [#58][I58]; proteção administrativa já existe, sem proteção global | Matriz de acesso, limites de processamento, política de sessão e critérios de teste por rota |
| PO07 / alta | Aceita o armazenamento temporário de sessões, datasets e coletas ou exige durabilidade antes da entrega/publicação? | [C5][C5], [C7][C7]; reinício perde estado administrativo; `/analises` seleciona armazenamento separadamente | Política de persistência, retenção, reinício e múltiplos processos; requisitos e dono da mudança |
| PO08 / alta | Mantém RNF01 (~80%) para qual domínio/conjunto de teste, ou solicita revisão formal após reprodução? | [#85][I85], [P89][P89], [H4][H4]; PR aberto relata desempenho inferior ao baseline no BPSAD | Reprodução independente, métricas por classe, domínio e limitações; decisão de manter/rever meta com justificativa e versão |
| PO09 / média | Confirma TweetSentBR como fonte quando disponível e BPSAD como avaliação de outro domínio? | [#3][I3], [C13][C13], [I85][I85]; disponibilidade/licenças devem ser verificadas | Origem, licença, volume útil, responsável pela aquisição e critério de corpus de aceite |
| PO10 / alta | Qual infraestrutura, responsável e condição autorizam publicar painel e API? | [#62][I62] registra intenção de hospedagem; sem implantação comprovada nesta revisão | Arquitetura de publicação, acesso/HTTPS, segredos, recursos/custos, testes reais e autorização específica antes do deploy |
| PO11 / média | Ratifica ausência de landing page e de exportação de resumos, sem remover requisitos antigos silenciosamente? | [#86][I86] registra essas decisões a incorporar; PDFs ainda indisponíveis | Mapear US/RF originais afetados e decisão datada; preservar referências históricas |
| PO12 / média | Quais requisitos e fluxos podem ser aceitos agora e quais continuam experimentais? | Código integrado diverge do estado de issues abertas; dashboard exibe indicadores, não listagem/gráficos/resumo completos [C18][C18] | Aceite por requisito/cenário/SHA; distinguir mock, integração simulada e execução real |
| PO13 / média | Confirma a meta de usabilidade e quem realizará as sessões? | [#63][I63]: 85% total e mínimo de 70% por tarefa; GQM original ausente | Roteiro, participantes, denominador, responsável e resultados reais; cotejo com Métrica 3.1 |
| PO14 / alta | Autoriza consolidar nova versão de Visão/Arquitetura após recuperar e reconciliar PDFs/pacote? | [#86][I86]; ausência das fontes impede garantir preservação integral | Originais identificados, revisão bibliográfica/visual, autoria, revisão humana, versão e aprovação da PO |

Fonte: consultas de 14/11/2026 e arquivos fixados no SHA. Estas perguntas não alteram o backlog nem autorizam gastos, deploy ou merge.

## 2. Forma de registro proposta

Para cada ID, registrar: decisão (aprovada/rejeitada/adiada), justificativa, responsável decisor, data, link público apropriado, RF/US/testes/documentos afetados, executor e evidência de verificação. Não registrar senha, chave, corpus integral ou dados pessoais de participantes. As respostas atuais são **N/D**.

Questões técnicas devem ser instruídas pelas frentes correspondentes: ML para checkpoint e avaliação; backend/dados para autenticação e persistência; interface para comportamento visual; QA para execução; gestão para histórico de merge e calendário. Isso é encaminhamento proposto, não nova atribuição individual.

## 3. Sequência sugerida

Primeiro ratificar abordagem do modelo e escopo da pesquisa; em seguida definir acesso, durabilidade e custo; depois avaliar resultados reproduzidos e decidir metas; por fim consolidar documentos e condições de publicação. O trabalho documental pode ser revisado em PR antes dessas respostas, desde que mantenha as pendências explícitas e não seja apresentado como versão homologada.

<!-- Referências fixadas no corte; PRs e issues consultados em 14/11/2026. -->
[C1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/classificacao/bertweet.py#L15
[C11]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/decisoes/ADR-001-nao-remover-stopwords-no-bertweet.md#L1
[C12]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/aquisicao/xfetch.py#L1
[C13]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/aquisicao/tweetsentbr.py#L1
[C18]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/apresentacao/paginas/dashboard.py#L1
[C2]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/classificacao/baseline.py#L18
[C3]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/processamento/pipeline.py#L55
[C4]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/main.py#L39
[C5]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/administracao.py#L117
[C7]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/dependencias.py#L24
[C8]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/autenticacao.py#L1
[C9]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/pesquisa.py#L1
[H4]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/docs/experimentos_bpsad.md#L1
[I16]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/16
[I3]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/3
[I58]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/58
[I62]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/62
[I63]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/63
[I85]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/85
[I86]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86
[P81]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/81
[P89]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89
[T1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/tests/test_classificacao.py#L94
