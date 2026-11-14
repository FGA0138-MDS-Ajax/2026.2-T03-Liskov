# Decisões pendentes da Product Owner — SentIA

**Corte:** 14/11/2026, base `1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`. **Estado:** pauta proposta; nenhuma resposta, prazo, estimativa ou aprovação foi presumida. A [matriz de divergências](MATRIZ_DIVERGENCIAS.md) fundamenta as perguntas.

## 1. Perguntas e evidência necessária

O Quadro 1 permite registrar uma decisão por tema, preservando a diferença entre o comportamento já codificado e a autorização formal para mudar escopo ou publicar.

**Quadro 1 — Pauta para deliberação**

| ID / prioridade | Pergunta objetiva para a PO | Evidência e proposta submetida | Registro necessário para encerrar |
| --- | --- | --- | --- |
| PO-01a (alias PO01) / alta | Aprova o ADR-001 e a ausência de remoção externa de stopwords, stemming e TF-IDF antes do BERTweet? | [C1][C1], [C3][C3], [C11][C11], [T1][T1]; preservar negações no wrapper, sem alegar ganho experimental | Decisão sobre ADR e nova redação RF03–RF06; impacto nos critérios T04–T07; revisão técnica |
| PO-01b (alias PO02) / alta | Ratifica RF07 como integração de modelo português pré-treinado e o baseline como comparador separado? | [#16][I16], [#86][I86], [C1][C1], [C2][C2]; sem treinamento próprio em Colab/Jupyter demonstrado | Texto aprovado de RF07/US07 e T08; checkpoint/revisão e responsáveis por avaliação |
| PO-05a (alias PO03) / alta | Qual é o escopo aprovado da pesquisa do PR #81: teste local lexical em memória ou entrega com persistência MongoDB? | [P81][P81], [C5][C5], [C9][C9]; versão de teste já mesclada; sem busca semântica implementada | Issue/US e critérios, relevância mínima, meta/limites, persistência, responsável e aceite |
| PO-05b (alias PO04) / alta | Existe registro de anuência ao merge de #81, apesar da restrição na descrição? | PR mesclado em 13/11; descrição ainda diz que faltam issue, custo e aceite | Referência à decisão humana; se inexistente, registrar regularização e próximos passos, sem retrodatá-la |
| PO-06 (alias PO05) / alta | Qual teto financeiro e operacional autoriza para XFetch, por consulta e período, e quem controla os créditos? | [C12][C12], [P81][P81]; limites locais de páginas/quantidade não são orçamento | Valor e unidade aprovados, responsável, frequência, bloqueio ao exceder, ambiente e autorização explícita para teste real |
| PO-07 (alias PO06) / alta | Administração exige só o perfil atual? As rotas `/analises` devem permanecer acessíveis sem sessão? | [C4][C4], [C5][C5], [C8][C8], [#58][I58]; proteção administrativa já existe, sem proteção global | Matriz de acesso, limites de processamento, política de sessão e critérios de teste por rota |
| PO-08 (alias PO07) / alta | Aceita o armazenamento temporário de sessões, datasets e coletas ou exige durabilidade antes da entrega/publicação? | [C5][C5], [C7][C7]; reinício perde estado administrativo; `/analises` seleciona armazenamento separadamente | Política de persistência, retenção, reinício e múltiplos processos; requisitos e dono da mudança |
| PO-02 (alias PO08) / alta | Mantém RNF01 (~80%) para qual domínio/conjunto de teste, ou solicita revisão formal após reprodução? | [#85][I85], [P89][P89], [H4][H4]; PR aberto relata desempenho inferior ao baseline no BPSAD | Reprodução independente, métricas por classe, domínio e limitações; decisão de manter/rever meta com justificativa e versão |
| PO-03 (alias PO09, domínio) / média | Qual corpus representa o domínio-alvo e qual mede robustez interdomínio? | Visão pp. 5–8; Arquitetura pp. 9–10; [#3][I3] e [#85][I85] | Fixar domínio-alvo de tweets e papel do BPSAD, sem generalizar métricas de produtos |
| PO-04 (alias PO09, licença) / alta | Confirma origem, licença e volume útil do TweetSentBR legado? | [C13][C13] e [#3][I3]; hash/schema não comprovam autorização de redistribuição | Procedência, termos e corpus autorizado, sem publicar textos brutos indevidamente |
| PO-14a (alias PO10) / alta | Qual infraestrutura, responsável e condição autorizam publicar painel e API? | [#62][I62] registra intenção de hospedagem; sem implantação comprovada nesta revisão | Arquitetura de publicação, acesso/HTTPS, segredos, recursos/custos, testes reais e autorização específica antes do deploy |
| PO-11b (alias PO11) / média | Ratifica US19/US20 como propostas posteriores, fora do backlog original, e decide incluir, adiar ou não adotar landing page/exportação? | Visão pp. 25–27 encerra em US18; Arquitetura §2.7 p. 27 menciona exportar resumos em P1, sem US20. A #86 não atribui por si US19/US20 à v1.0.0 | Registrar origem/identificador das propostas posteriores e decisão datada; não inventar exclusão de US19/US20 do original |
| PO-09 (alias PO12, datas) / média | Ratifica filtro por publicação UTC e tratamento dos textos sem data? | Arquitetura pp. 16/23 exigia data; contrato [C3][C3]/[C19][C19] aceita ausência; filtro atual usa publicação | Critérios de intervalo/fuso/exclusões e aceite de UI, sem inventar datas |
| PO-10 (alias PO12, T18) / média | Confirma C06/RNF02 para US18 e as resoluções mínimas de T18? | Visão p. 27 traz C06/RF02, p. 39 traz C06/RNF02; Arquitetura p. 14 usa RNF02 | Corrigir código sem renumeração silenciosa; executar inspeção visual atual em desktop/tablet/mobile |
| PO-11a (alias PO12, RF16) / média | Inclui ou adia a nuvem de palavras Could? | Visão p. 27 RF16/US17 e p. 39 T17; issue #30 | Decisão de escopo/prazo sem alterar entradas do BERTweet nem comprometer Musts |
| PO-13 (alias PO12, aceite) / alta | Quais requisitos/fluxos têm aceite por SHA e qual conciliação de C01–C06/Sprints aprova? | Visão pp. 11–12/23/25–27: divergências de Sprints, inclusive RF08→S3 no backlog; CI [E1][E1] verde não substitui DoD | Ratificar cenários/calendário e aceite por requisito/cenário/SHA; encaminhar higiene de issues sem fechamento automático |
| PO-12 (alias PO13) / média | Aprova a reconciliação GQM, a justificativa dos limiares e o protocolo de usabilidade? | Visão pp. 28–32: metas 80%, 20%, 85%/70%; O2/Q4 e O3/Q2 sem métricas próprias; [plano #91][Q1] e [#63][I63] | Ratificar métricas de cobertura/concordância, limiares e roteiro/participantes/denominadores; coletar resultados reais |
| PO-14b (alias PO14) / alta | Autoriza a edição final de Visão/Arquitetura sem matrículas/anotações e o plano de promoção controlada após revisão? | [#86][I86]; originais lidos diretamente, reconciliação textual concluída; [ABNT](REVISAO_ABNT.md) registra pendências de edição; [Argon][A1] inclui governança de promoção | Decidir exportação/autoria/versão, revisão humana e governança da promoção; merge/deploy continuam a exigir autorização do usuário |

Fonte: leitura direta dos originais, consultas de 14/11/2026, código fixado no SHA e catálogo canônico do [Argon][A1], §§2.1–2.2 (commit `25f2587`). Os IDs atuais são canônicos; aliases preservam a pauta inicial do #90. Estas perguntas não alteram o backlog nem autorizam gastos, deploy ou merge.

### 1.1 Equivalência preservada

| Alias original #90 | ID canônico #92 |
| --- | --- |
| PO01 | PO-01a |
| PO02 | PO-01b |
| PO03 | PO-05a |
| PO04 | PO-05b |
| PO05 | PO-06 |
| PO06 | PO-07 |
| PO07 | PO-08 |
| PO08 | PO-02 |
| PO09 | PO-03 e PO-04 |
| PO10 | PO-14a |
| PO11 | PO-11b |
| PO12 | PO-09, PO-10, PO-11a e PO-13 |
| PO13 | PO-12 |
| PO14 | PO-14b |

Fonte: tabela de equivalência do [Argon][A1]. A pauta inicial de 14 itens corresponde a 18 subitens canônicos, sem decisão presumida. Para as fontes diretas, a página de exportação é 27 e a bibliografia de Arquitetura é 29; essas localizações refinam a síntese do #92.

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
[A1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/25f258786981f29552d2df2f1b4597ab7ef01c44/docs/inspecao/PLANO_REGULARIZACAO.md
[C19]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/1723a7d62d55fa98fbf6eaf5cc9da80650dbe920/src/servico/esquemas.py#L8
[E1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920
[Q1]: https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/84530e4b3d0ac1762b9100c4c728e6208ffca810/docs/metricas/PLANO_GQM_VIGENTE.md
