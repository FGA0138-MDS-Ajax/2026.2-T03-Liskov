# Ata de Reunião 04 — Acompanhamento da Sprint 7

## Informações gerais

| Campo | Informação |
| --- | --- |
| Projeto | SentIA — Análise de Sentimentos |
| Equipe | Liskov — Turma 03 |
| Disciplina | Métodos de Desenvolvimento de Software (MDS) — UnB/FGA, 2026.2 |
| Data | 25/11/2026 (quarta-feira) |
| Horário | Início às 19h58 (horário de Brasília) |
| Duração | Cerca de 32 minutos de pauta (gravação de 53 minutos) |
| Plataforma | Microsoft Teams |
| Condução | Hellen Clicia Barros Rego (Product Owner) |

**Participantes:** Hellen Clicia Barros Rego, Renato Rodrigues Campos Filho, Breno Weber Rabelo, Gabriel Souza de Matos, Ricardo Eduardo da Silva Leal, Maria Eduarda de Jezus Guimaraes e Juliana Silva Teixeira.

**Ausente:** Julia Neiva Lima.

## 1. Objetivo da reunião

Acompanhar a Sprint 7 (24 a 30/11), revisar as decisões da reunião de 23/11, redistribuir tarefas atrasadas e combinar os prazos finais da documentação e do ensaio.

## 2. Situação das Sprints

- **Sprint 6:** fechada no GitHub em 24/11, com 7 issues concluídas (#27, #28, #29, #59, #61, #102 e #103). As issues #26 e #32 passaram para a Sprint 7.
- **Sprint 7:** em andamento, com 11 issues abertas. O projeto terá 7 Sprints no total.

## 3. Decisões

### 3.1 Revisão das decisões de 23/11

A PO relembrou as decisões da reunião anterior, sem contestação: TweetSentBR e BPSAD avaliam o modelo, e CSV e XFetch são os dados analisados (D-02). Textos sem data aparecem na visão geral e saem só quando se aplica o filtro de período (D-04). A consulta é aberta, e só o Administrador faz login (D-07). O BERTweet recebe o texto inteiro, sem remoção de stopwords (D-12).

Sobre o XFetch, há cerca de 51.000 créditos. A PO já está com a chave e fez um teste em 25/11.

### 3.2 Decisões novas ou alteradas

| Assunto | Decisão |
| --- | --- |
| **Pesquisa do Usuário no XFetch (D-01)** | **Ampliada.** Além de escolher o assunto, o Usuário também pode acionar a busca no XFetch. Justificativa (Breno): o professor e os monitores podem querer testar o sistema fora do horário da apresentação, então todos precisam conseguir pesquisar. A PO fará as adaptações e vai alinhar os detalhes com Breno. |
| **Quantidade "suficiente" de textos** | **No mínimo 50 textos por assunto.** Se a base tiver menos de 50 textos sobre o assunto, o sistema completa com os textos mais recentes do XFetch, dos últimos 30 dias. A PO havia proposto 30 e fechou 50 com Breno. |
| **Gasto do XFetch** | Breno explicou que a pesquisa só vai ao XFetch para completar o que falta até a meta de 50: a base é consultada primeiro, e o XFetch traz apenas a diferença. Pesquisas repetidas reaproveitam o resultado guardado, então um teste de carga só gasta créditos com pesquisas novas. |
| **Publicação na web (#62)** | **Renato** fica responsável pela publicação de tudo: banco, modelo e painel. Também documenta o deploy. Renato informou que nunca publicou um sistema completo e vai estudar como fazer. |
| **Novo protótipo de alta fidelidade** | **Aprovado.** A PO apresentou o novo protótipo do painel e da administração (PR #114 e Figma), com mais cores e informações: importação de dataset com o formato esperado, pesquisa por assunto e identificação do Administrador logado. A equipe aprovou a implementação. Renato perguntou sobre modo escuro; a PO disse que é possível aplicá-lo. **Decidido pela PO em 26/11, depois da reunião: o modo escuro será implementado.** |
| **Nuvem de palavras (#30)** | **Continua opcional.** Só é implementada se sobrar tempo. |
| **Possível novo dataset** | Gabriel pediu um novo dataset por causa de problemas com o BPSAD. Breno vai prepará-lo em 26/11, à tarde. Pode haver mudança no dataset de avaliação. |

## 4. Redistribuição de tarefas

| Issue | Antes | Agora |
| --- | --- | --- |
| #113 Usuário filtra as análises por assunto | Renato e Hellen | Hellen |
| #26 Validar consultas e filtros na API | Renato | Hellen |
| #32 Validar dashboard, gráficos, filtros e resumo integrado | Renato | Hellen |
| #31 Responsividade (prints em todas as larguras) | Juliana | Hellen |
| #63 Teste de usabilidade | Hellen | Renato, junto com o deploy |
| #62 Publicação na web | Renato e Hellen | Renato |

Renato fica com a sua parte da documentação (#86), as suas issues atrasadas (#110, #111 e #112) e o deploy com a documentação dele.

## 5. Andamento da Sprint 7

| Issue | Situação relatada |
| --- | --- |
| #86 Documentação final | Até 25/11, só a parte de Breno estava feita. A PO marcou a parte de Breno na Arquitetura como concluída. Os demais ainda não tinham alterado a Visão e a Arquitetura. |
| #110 Repositório conforme o plano de gestão de configuração | Prazo em 25/11. Responsáveis: Renato, Breno, Ricardo e Gabriel. Gabriel estava trabalhando em uma parte. Renato convidou quem puder para trabalhar com ele no laboratório do ITRAC em 26/11. |
| #111 Métricas | Responsáveis: Hellen, Renato, Ricardo e Gabriel. Nenhum dado tinha sido coletado ainda; a PO também não havia feito a sua parte. É preciso atualizar o histórico de planejamento, conforme apontado na inspeção. |
| #31 Responsividade | A PO vai implementar o novo protótipo e anexar os prints de responsividade. |
| #102 Suporte a GPU AMD | Renato voltou a pedir o suporte a AMD. Gabriel disse que a melhoria da GPU foi feita por Ricardo e que vai verificar o PyTorch. **Decidido pela PO em 26/11: fica com quem implementou (Ricardo), até 27/11.** |
| Execução do modelo na GPU | Renato não conseguiu rodar o modelo na GPU. Falta instalar a versão certa do PyTorch e uma configuração no `.env`, que a PO enviou a ele no chat. Roda no Linux e funcionou na máquina da PO. A PO pediu a Ricardo e Gabriel que coloquem os comandos de instalação no README até 26/11. |

**Inspeção:** a equipe perdeu mais pontos na documentação. A versão final v1.2.0 incorpora as críticas do professor e da inspeção.

## 6. Prazos combinados

- **Documentação (#86): 26/11, até as 23h59.** Depois, a PO faz a ABNT e a revisão final. A PO foi clara: não aceita a documentação depois de 26/11.
- **Demais pendências: até sexta-feira, 27/11, no ensaio.** O sábado, 28/11, fica de folga para resolver o que atrasar ou não der tempo (decidido pela PO em 26/11).

## 7. Ensaio e apresentação

- **Reunião de ensaio:** sexta-feira, 27/11, entre 19h e 19h30, **online**. Breno, e talvez Maria Eduarda, não podem na sexta. Quem não puder participa no sábado, 28/11; o horário será decidido em grupo.

  > Correção de 26/11: a primeira versão desta ata registrou "sexta-feira, 28/11" e "sábado, 29/11". Em 2026, 27/11 é sexta e 28/11 é sábado.
- **Formato da apresentação:** dividir o projeto por partes, conforme a familiaridade de cada um. Por exemplo, Renato fala dos testes, e Breno ou Hellen mostram o sistema funcionando. Segundo relatos de quem já cursou a disciplina, o professor quer principalmente ver o sistema rodando e fazendo o que foi prometido. Hellen e Renato vão planejar a apresentação antes de sexta.

## 8. Encaminhamentos

| # | Ação | Responsável | Prazo |
| --- | --- | --- | --- |
| 1 | Concluir a sua parte da documentação (#86) | Todos | 26/11, 23h59 |
| 2 | Adaptar a #113 e o painel para o Usuário acionar o XFetch, com o mínimo de 50 textos | Hellen, alinhando com Breno | 27/11 |
| 3 | Implementar o novo protótipo, com modo escuro, e registrar os prints de responsividade (#31) | Hellen | 27/11 |
| 4 | Executar as validações #26 e #32 | Hellen | 27/11 |
| 5 | Publicar banco, modelo e painel na web e documentar o deploy (#62) | Renato | 27/11 |
| 6 | Teste de usabilidade (#63) | Renato | 27/11 |
| 7 | Concluir as issues #110, #111 e #112 | Responsáveis de cada issue | 27/11 |
| 8 | Preparar um novo dataset para avaliação | Breno | 26/11, à tarde |
| 9 | Colocar no README os comandos de instalação do PyTorch para GPU | Ricardo e Gabriel | 26/11 |
| 10 | Verificar o suporte a GPU AMD | Ricardo (quem implementou) | 27/11 |
| 11 | Enviar foto para o README | Todos | Antes da entrega |
| 12 | Preencher a planilha de distribuição das atividades | Hellen | Antes da entrega |
| 13 | Enviar a lista de presença para assinatura | Hellen | 25/11 |
| 14 | Planejar a divisão da apresentação | Hellen e Renato | 27/11 |
| 15 | Atualizar o site do projeto e publicar as atas | Hellen | Antes da entrega |

## 9. Pendências não resolvidas

- Horário do encontro de sábado (28/11) para quem não puder na sexta: **será decidido em grupo**.

Resolvidas pela PO em 26/11, depois da reunião:
- Modo escuro: **será implementado**, junto com o novo protótipo.
- Suporte a GPU AMD: **Ricardo**, que implementou a melhoria da GPU, **até 27/11**.
- Prazos: tudo que estava para 28/11 passa para **sexta, 27/11**. O sábado, 28/11, fica de folga para o que atrasar.
