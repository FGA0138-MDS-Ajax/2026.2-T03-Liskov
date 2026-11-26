# Ata de Reunião 03 — Fechamento da Sprint 6 e planejamento da Sprint 7

## Informações gerais

| Campo | Informação |
| --- | --- |
| Projeto | SentIA — Análise de Sentimentos |
| Equipe | Liskov — Turma 03 |
| Disciplina | Métodos de Desenvolvimento de Software (MDS) — UnB/FGA, 2026.2 |
| Data | 23/11/2026 (segunda-feira) |
| Horário | Início às 19h11 (horário de Brasília) |
| Duração da gravação | Aproximadamente 36 minutos |
| Plataforma | Microsoft Teams |
| Condução | Hellen Clicia Barros Rego (Product Owner), com apoio de Renato Rodrigues Campos Filho (Scrum Master) |

**Participantes:** Hellen Clicia Barros Rego, Renato Rodrigues Campos Filho, Breno Weber Rabelo, Julia Neiva Lima, Maria Eduarda de Jezus Guimaraes e Juliana Silva Teixeira. Julia esteve presente, mas não tem falas na transcrição.

**Ausentes:** Ricardo Eduardo da Silva Leal e Gabriel Souza de Matos.

## 1. Objetivo da reunião

Fechar a Sprint 6 (17 a 23/11), confirmar as decisões de produto que travam a documentação final e planejar a Sprint 7 (24 a 30/11), última antes da entrega de 30/11/2026.

## 2. Fechamento da Sprint 6

Renato apresentou as issues da Sprint 6 no quadro, e a equipe revisou o que foi feito.

| Issue | Responsável | Situação relatada na reunião |
| --- | --- | --- |
| #61 Iniciar coleta e análise pelo painel | Hellen | Concluída. Fechada durante a reunião. |
| #28 Gráficos de distribuição dos sentimentos | Juliana | Critérios de aceitação conferidos na reunião; considerada feita. |
| #29 Resumo textual das análises no dashboard | Juliana | Critérios de aceitação conferidos na reunião; considerada feita. |
| #102 GPU na inferência do BERTweet | Ricardo e Gabriel | Feita para GPU NVIDIA. Renato pediu que também haja suporte a GPU AMD, para todos conseguirem rodar o modelo. Repassar a Ricardo e Gabriel, ausentes. |
| #103 Ajuste fino do BERTweet | Ricardo e Gabriel | Não discutida em detalhe, pois os responsáveis estavam ausentes. A entrega está no PR #109, que aguarda revisão (ver a nota da seção 3). |
| #26 e #32 Validação da API e do dashboard integrado | Renato | Não discutidas individualmente. |

A Sprint 5 já havia sido fechada antes da reunião, e a issue que ficou pendente nela já está na Sprint 6.

**Situação no GitHub ao fim da reunião:** Sprint 6 com 3 issues fechadas (#27, #59 e #61) e 6 abertas (#26, #28, #29, #32, #102 e #103). Os números finais da Sprint 6 dependem do aceite formal da PO para #28 e #29.

## 3. Decisões de produto

A PO leu as decisões e pediu concordância da equipe.

| Decisão | Resultado |
| --- | --- |
| **D-01 — Quem escolhe o assunto** | **Alterada.** O Usuário também escolhe o assunto e faz consultas: escolhe o assunto, filtra por período e analisa os gráficos. Justificativa (Renato): o objetivo do SentIA é o usuário pesquisar o que se fala sobre um assunto; o sistema será usado apenas pela equipe e na demonstração ao professor, então não há risco de uso externo. A PO registrou a preocupação com o gasto de créditos do XFetch. |
| **D-02 — Papel dos dados** | **Confirmada.** TweetSentBR e BPSAD servem para avaliar o modelo (verificar se está classificando corretamente). CSV e XFetch são os dados analisados pelo sistema. |
| **D-04 — Filtro de data** | **Alterada.** Textos sem data de publicação aparecem na visão geral do dashboard, mas ficam fora quando o usuário filtra por período. Não se usa a data de importação no lugar da data de publicação. |
| **D-07 — Acesso** | **Confirmada.** A consulta é aberta, sem login; a administração exige login. Justificativa: login de usuários exigiria cadastro e segurança de credenciais no banco, fora do escopo da demonstração. |
| **D-12 — Pré-processamento do BERTweet** | **Confirmada.** O BERTweet recebe o texto sem remoção de stopwords, pois considera o texto inteiro. |
| **D-03 — Meta de 80% de acurácia** | **Adiada.** A PO vai perguntar a Ricardo e Gabriel em particular. Breno relatou que a avaliação apresentada pelo ML indica cerca de 50% de precisão no BPSAD e questionou como o modelo foi testado. A PO indicou que a avaliação terá de ser refeita. |
| **D-09 — XFetch** | **Informações levantadas.** Restam cerca de 51.000 créditos; o último uso registrado foi em 15/11. Renato considera o saldo suficiente e propôs uma contribuição de R$ 10 por pessoa caso falte. Breno repassou a chave à PO após a reunião. |
| **D-10 — Publicação na web (#62)** | **Decidido publicar.** Renato defendeu que o projeto não pode rodar só localmente. Responsáveis: painel com Hellen e Renato; banco de dados com Julia e Maria Eduarda. Renato alertou que o deploy deve dar trabalho e pode exigir um dia dedicado. Rodar o modelo no Google Colab foi citado apenas como alternativa, caso não seja possível publicar o projeto na web. |

As decisões D-06, D-13 e D-14 não foram discutidas. A PO as decide em 24/11.

**Nota posterior à reunião (D-03):** no PR #109, Ricardo informou que o modelo refinado alcançou **77,80% de acurácia** no teste PC1 do BPSAD, ou seja, 2,2 pontos abaixo da meta de 80%. O modelo original tem 67,70% nesse teste. A avaliação também identificou **regressão no TweetSentBR**: a acurácia caiu de 83,90% para 64,87%. A troca do modelo padrão depende da reprodução por Renato, da revisão de outro integrante e do aceite da PO.

## 4. Planejamento da Sprint 7

**Objetivo:** entregar Visão e Arquitetura v1.2.0 sem os defeitos críticos apontados pelo professor e pela inspeção, com métricas coletadas, testes executados e repositório organizado.

| Item | Responsáveis | Combinado |
| --- | --- | --- |
| #86 Documentação final v1.2.0 | Todos | A issue traz a divisão por capítulo e seção, os links e os prazos. Todos devem lê-la com atenção. A PO faz a revisão final e a ABNT. Breno informou que já concluiu sua parte da Arquitetura e da Visão. |
| #110 Repositório conforme o plano de gestão de configuração | Renato e equipe | Inclui o versionamento do repositório (débito técnico). |
| #111 Métricas | Renato, Hellen, Ricardo e Gabriel | Conforme a issue. |
| #112 Testes para a documentação final | Renato e equipe | Conforme a issue. |
| #31 Responsividade | Juliana | Apenas documentação: prints do painel em todas as larguras definidas, anexados na issue, como evidência. |
| #62 Publicação na web | Hellen e Renato (painel); Julia e Maria Eduarda (banco) | Ver D-10. |
| #102 GPU | Ricardo e Gabriel | Adicionar suporte a GPU AMD. |
| README | Todos | Cada integrante envia uma foto para o README. A PO vai cobrar. |

## 5. Apresentação final e calendário

- **Entrega:** tudo pronto até **30/11/2026 (segunda-feira)**. Há apresentações em 30/11 e 02/12; a ordem será aleatória, segundo Breno. Notas em 07/12; revisão e frequência em 09/12.
- **Formato (relato de Maria Eduarda, que já cursou a disciplina):** semelhante ao ponto de controle. Mostra-se a organização do trabalho e, ao final, o sistema rodando.
- **Ensaio e teste final com todos:** **sexta-feira, 27/11, às 19h**, online ou no laboratório do ITRAC, se estiver disponível. Breno e Maria Eduarda não podem na sexta e participam de um encontro no sábado, 28/11, com Hellen e Renato para a revisão final.
- **Próxima reunião:** quarta-feira, 25/11, no horário da disciplina.

**Disponibilidade informada:** Renato tem prova na quarta (25/11) e fica livre a partir de quinta (26/11) e não pode no fim de semana, salvo sábado à noite. Breno está livre só na quinta (26/11) à noite e continua disponível até 04/12. Maria Eduarda só tem horário durante a semana de madrugada. Renato leu uma mensagem de disponibilidade "sexta após as 16h", de Julia ou de Juliana (confirmar). Julia não pode na quinta (26/11).

## 6. Encaminhamentos

| # | Ação | Responsável | Prazo |
| --- | --- | --- | --- |
| 1 | Repassar a Ricardo e Gabriel o pedido de suporte a GPU AMD | Hellen | 24/11 |
| 2 | Decidir a D-03 (meta de 80%) com base no PR #109 | Hellen | 24/11 |
| 3 | Decidir as D-06, D-13 e D-14 | Hellen | 24/11 |
| 4 | Publicar o painel na web (#62) | Hellen e Renato | Até 30/11 |
| 5 | Publicar o banco de dados na web | Julia e Maria Eduarda | Até 30/11 |
| 6 | Prints de responsividade na #31 | Juliana | Conforme a issue |
| 7 | Fazer a sua parte da #86 | Todos | Conforme a issue |
| 8 | Enviar foto para o README | Todos | Antes da entrega |
| 9 | Preencher a planilha de distribuição das atividades | Hellen | Antes da entrega |
| 10 | Enviar as listas de presença (23/11 e 25/11) | Hellen | 23/11 e 25/11 |
| 11 | Publicar os aceites pendentes | Hellen | 24/11 |
| 12 | Confirmar o local do ensaio (online ou laboratório do ITRAC) | Hellen | Até 27/11 |

## 7. Pendências não resolvidas

- Revisor do PR #109 e reprodução dos resultados por Renato.
