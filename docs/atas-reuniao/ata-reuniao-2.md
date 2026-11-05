# Ata de Reunião 02 — Daily e alinhamento técnico do SentIA

## Informações gerais

| Campo | Informação |
| --- | --- |
| Projeto | SentIA — Análise de Sentimentos |
| Equipe | Liskov — Turma 03 |
| Disciplina | Métodos de Desenvolvimento de Software (MDS) — UnB/FGA, 2026.2 |
| Data | 04/11/2026 (quarta-feira) |
| Horário | 18h00 às 19h15 (horário de Brasília) |
| Duração da gravação | Aproximadamente 59 minutos e 21 segundos |
| Plataforma | Microsoft Teams |
| Condução | Renato Rodrigues Campos Filho (Scrum Master) |

**Participantes identificados por falas na transcrição:** Renato Rodrigues Campos Filho, Breno Weber Rabelo, Julia Neiva Lima, Maria Eduarda de Jezus Guimaraes, Juliana Silva Teixeira e Hellen Clicia Barros Rego.

**Observação:** Gabriel Souza de Matos e Ricardo Eduardo da Silva Leal foram mencionados e parecem ter interagido por outros meios durante a chamada, mas **não possuem falas identificadas nominalmente no arquivo VTT**. Sua presença deve ser confirmada antes de atualizar a lista oficial. Maria Eduarda entrou após o início da reunião, e Julia saiu antes do encerramento.

## 1. Objetivo da reunião

Acompanhar o andamento do desenvolvimento do SentIA, identificar dependências entre as frentes de trabalho e preparar os próximos pontos de controle e apresentações. A reunião também tratou de uma possível ampliação do fluxo de aquisição de dados: **pesquisar publicações por palavra-chave, consultando o banco existente e utilizando uma API externa quando necessário**.

## 2. Andamento e assuntos discutidos

### 2.1. Acompanhamento das issues e do banco de dados

Breno comentou que algumas atividades do GitHub já poderiam começar sem depender da conclusão das demais frentes. Indicou a **issue #12** como iniciável e sugeriu que Julia verificasse a viabilidade de começar a **issue #20**, sem garantir que todas as suas dependências estivessem resolvidas.

Julia confirmou sua atuação no banco de dados. O grupo avaliou que a **modelagem e a estrutura inicial do banco** poderiam ser adiantadas enquanto se aguardavam dados e artefatos de integração dos demais componentes. Breno mencionou a dependência de um arquivo CSV a ser finalizado por Ricardo, no contexto então discutido.

### 2.2. Ponto de controle e inspeção

A pedido de Renato, Maria Eduarda compartilhou sua compreensão das avaliações da disciplina:

- **Ponto de controle:** apresentação do progresso do projeto, incluindo artefatos já desenvolvidos, demonstração do sistema quando possível, andamento do Scrum e situação do cronograma;
- **Inspeção:** avaliação por formulário, com observações sobre o que está adequado e o que precisa ser melhorado.

Maria Eduarda ressaltou que estava explicando com base em sua lembrança de experiências anteriores. Portanto, detalhes como a escala de notas e as exigências de demonstração **não foram confirmados como regras oficiais** durante a reunião.

A equipe destacou a necessidade de preparar entregáveis para as apresentações mencionadas para a **segunda-feira e a quarta-feira seguintes**, com preferência por ter material apresentável já na segunda-feira. As datas de calendário não constam da transcrição.

### 2.3. Aquisição dos dados, treinamento e avaliação do modelo

Renato relatou resultados de uma sessão de trabalho anterior (*war room*) com Breno e Gabriel, na qual avançaram na obtenção e organização de datasets. A etapa seguinte seria garantir que os dados chegassem corretamente ao modelo e aferir a qualidade de suas classificações.

A discussão diferenciou duas finalidades dos dados:

1. **Treinamento e validação:** manter datasets disponíveis para desenvolver e medir o desempenho do classificador;
2. **Uso da aplicação:** consultar publicações relacionadas a um assunto pesquisado pelo usuário e apresentar a distribuição dos sentimentos.

Foram mencionados datasets de tweets e de avaliações de produtos, bem como o uso do **BERTweet** (nome citado na discussão sobre o modelo). Breno alertou que resultados obtidos sobre dados próximos dos utilizados no treinamento podem não demonstrar generalização adequada, propondo validação com dados de outra origem. **Nenhum percentual definitivo de acurácia foi aprovado na reunião.**

### 2.4. Esclarecimento do escopo funcional

Surgiu uma divergência sobre o produto: uma proposta era permitir que o usuário digitasse um texto isolado para receber sua classificação; outra era analisar o sentimento de **publicações de redes sociais relativas a determinado tema**.

Renato reforçou que o objetivo do SentIA é a **análise de sentimentos em redes sociais**, e não apenas a classificação pontual de frases digitadas manualmente. Exemplificou uma busca por palavra-chave ou assunto, seguida da apresentação de menções positivas, negativas e neutras. Também defendeu manter, quando viável, a visualização dos resultados por período.

Breno observou que datasets estáticos podem não conter publicações sobre todos os assuntos pesquisados, o que motivou a discussão sobre novas consultas a fontes externas.

### 2.5. Proposta de consulta externa e reaproveitamento de dados

A equipe debateu uma evolução do fluxo do SentIA:

1. Receber do usuário um **termo ou palavra-chave**;
2. Consultar inicialmente os registros armazenados no **MongoDB**;
3. Quando necessário, buscar novas publicações por meio de **API externa**;
4. Encaminhar os textos obtidos para o pipeline de tratamento e classificação;
5. Salvar as novas publicações/resultados, permitindo reutilizá-los em consultas posteriores;
6. Apresentar os resultados no dashboard, com distribuição de sentimentos e filtros aplicáveis.

Breno demonstrou opções de uma ferramenta externa de consulta de tweets, inclusive a possibilidade de pesquisa por tendências ou termos, e explicou que seria preciso confirmar o comportamento da API. Também mencionou créditos de uso já adquiridos e o custo associado a novas consultas. A ideia de contribuição financeira para comprar créditos adicionais foi **levantada como possibilidade, não aprovada como despesa do grupo**.

Foi considerada a realização de buscas antecipadas para a apresentação, a fim de evitar consumo excessivo de créditos em demonstrações. O grupo concordou que o banco de dados continuaria útil para persistência e redução da repetição de consultas pagas.

**Estado da definição:** ao final, o encaminhamento foi **manter o projeto e acrescentar essa nova entrada/consulta externa**, sem remover o banco ou os datasets de treinamento. A API específica, os limites de consulta, a estratégia de cache e as alterações formais dos requisitos permaneceram dependentes de implementação e validação.

### 2.6. Interface, prototipação e filtros

Juliana informou que ela e Hellen estavam desenvolvendo o protótipo no **Figma**. Hellen já havia elaborado parte significativa do material, e Juliana planejava avançar na sua seção. Hellen estimou concluir um protótipo mais fiel até o fim da semana.

Foram discutidos elementos para a interface:

- **Campo de busca** por assunto ou palavra-chave;
- **Gráficos de distribuição** de sentimentos;
- Possível **evolução temporal** das menções e filtro por data, quando a fonte oferecer metadados suficientes;
- **Filtros ou sugestões de temas**, para ajudar a demonstrar a utilização da plataforma.

Renato sugeriu que o frontend fosse implementado **com dados simulados (*mockados*)**, mesmo sem o backend e o modelo concluídos, para viabilizar testes e uma apresentação navegável. Juliana confirmou que havia anotado essa orientação e que alinharia os próximos passos com Hellen.

### 2.7. Integração e organização do trabalho

A equipe discutiu a necessidade de integrar as frentes de aquisição, modelo, banco de dados, API e dashboard. Renato destacou que a integração não deveria ficar exclusivamente sob responsabilidade do frontend, devendo envolver integrantes de cada componente.

Foram citadas issues de integração existentes, mas a reunião identificou a necessidade de **ajustar o backlog para incluir o novo fluxo de consulta externa e reaproveitamento dos dados**. Renato assumiu a articulação da integração final com apoio das demais frentes.

### 2.8. Prazos e disponibilidade

Foi solicitado que **Gabriel e Ricardo disponibilizassem o modelo até sexta-feira, preferencialmente à tarde**, para permitir testes e integração entre quinta e sexta-feira, conforme disponibilidade dos envolvidos.

A disponibilidade para uma chamada de integração na sexta-feira não ficou totalmente fechada: Breno relatou que só conseguiria participar tarde da noite, e Renato mencionou a possibilidade de começar com os integrantes disponíveis e incorporar outros posteriormente. A presença de Gabriel e Ricardo nesse encontro deveria ser confirmada.

## 3. Encaminhamentos e responsabilidades

| Encaminhamento | Responsável(eis) | Prazo / situação registrada |
| --- | --- | --- |
| Avaliar e iniciar a issue #12; verificar dependências da issue #20 | Julia | Início conforme viabilidade |
| Avançar na modelagem e estrutura do MongoDB, mantendo preparação para receber dados | Julia e Maria Eduarda | Dar continuidade imediatamente |
| Entregar o modelo de classificação em versão adequada para integração e testes | Gabriel e Ricardo | **Até sexta-feira**, preferencialmente à tarde |
| Documentar o código do modelo e as interfaces necessárias à integração | Gabriel e Ricardo | Junto à entrega do modelo |
| Implementar/adaptar a obtenção de publicações por termo de pesquisa via fonte externa | Breno | Iniciar a adaptação; prazo exato não fixado |
| Articular uma sessão de testes e integração do modelo e da aquisição | Renato, com Breno, Ricardo e demais participantes disponíveis | Entre quinta e sexta-feira, conforme entrega e disponibilidade |
| Continuar o protótipo no Figma e iniciar a interface funcional | Hellen e Juliana | Avançar até o fim da semana |
| Criar dados simulados para demonstrar e testar o frontend independentemente da integração | Hellen e Juliana | Próxima versão apresentável |
| Atualizar/refinar o backlog para abranger a nova forma de entrada e consulta | Hellen (Product Owner), com apoio de Renato e equipe | Após alinhamento dos requisitos |
| Organizar e divulgar as issues disponíveis, registros e materiais da reunião | Renato | Compartilhamento prometido ao grupo |
| Preparar material demonstrável e andamento do Scrum para o ponto de controle | Toda a equipe | Preferencialmente até a segunda-feira mencionada |

## 4. Decisões e consensos de trabalho

- **Preservar o propósito do produto:** analisar o sentimento de publicações de redes sociais relacionadas a temas ou palavras-chave.
- **Não substituir os datasets de treinamento/avaliação** pela nova busca de publicações; os dois usos têm finalidades diferentes.
- **Manter o banco de dados** e aproveitar consultas anteriores para evitar buscas externas repetidas quando possível.
- **Acrescentar ao planejamento** o fluxo de pesquisa por palavra-chave, sujeito a validação técnica e ao refinamento do backlog.
- **Desacoplar o progresso do frontend** da conclusão do modelo, utilizando dados simulados para prototipação, testes e apresentações.
- **Priorizar a entrega do modelo e o início dos testes integrados** antes do próximo ponto de controle.

## 5. Riscos, impedimentos e pontos a confirmar

| Ponto | Observação |
| --- | --- |
| Fonte externa | Confirmar API, autenticação, custos, limites de uso e viabilidade da pesquisa por termos/tendências |
| Metadados temporais | Nem todos os datasets discutidos possuem data; o filtro por período dependerá da origem dos dados |
| Validação do modelo | Definir conjunto de teste independente e registrar métricas para evitar uma avaliação enviesada |
| Integração | Delimitar interfaces entre API, modelo, aquisição e MongoDB, incluindo tratamento de consultas sem resultados |
| Banco de dados | Definir como identificar, armazenar e reutilizar publicações obtidas em pesquisas anteriores |
| Frontend | Concluir protótipo e implementar telas com dados simulados antes da integração definitiva |
| Planejamento | Revisar backlog, critérios de aceitação, estimativas e impacto da busca externa sobre o escopo |
| Calendário | Confirmar as datas dos pontos de controle e o horário da sessão de integração |
| Participação | Confirmar presença de Gabriel e Ricardo e as disponibilidades efetivas para a integração |

## 6. Próximos acompanhamentos

O acompanhamento seguinte deve verificar a disponibilidade do modelo para testes, o progresso da nova aquisição por API, a preparação do MongoDB, a conclusão do protótipo e a apresentação do frontend com dados simulados. Também deverá ser verificado se os requisitos e o backlog foram atualizados para refletir o fluxo discutido.

---

**Fonte:** transcrição automática em formato WebVTT, arquivo “Daily - Liskov.vtt”, fornecido pela equipe.

**Nota editorial:** nomes de ferramentas e trechos técnicos foram normalizados apenas quando o contexto permitiu. A transcrição contém falas truncadas, palavras em inglês atribuídas incorretamente e intervenções sem identificação de participante. Por isso, propostas, hipóteses e prazos relativos não foram convertidos em decisões formais ou datas absolutas sem evidência suficiente.
