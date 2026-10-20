# Ata de Reunião 01 — Alinhamento inicial do SentIA

## Informações gerais

| Campo | Informação |
| --- | --- |
| Projeto | SentIA — Análise de Sentimentos |
| Equipe | Liskov — Turma 03 |
| Disciplina | Métodos de Desenvolvimento de Software (MDS) — UnB/FGA, 2026.2 |
| Data | **25/09/2026** |
| Horário | Noturno; início e término exatos não informados |
| Duração da gravação | Aproximadamente 1 hora e 7 minutos |
| Plataforma | Microsoft Teams |
| Condução | Renato Rodrigues Campos Filho |

**Participação identificada na transcrição:** Renato Rodrigues Campos Filho, Hellen Clicia Barros Rego, Juliana Silva Teixeira e Ricardo Eduardo da Silva Leal.

**Observação sobre presença:** os quatro participantes acima são identificados por suas falas. Ao final, foi mencionado que aproximadamente metade do grupo não estava presente. O arquivo não permite confirmar individualmente a presença ou a ausência dos demais integrantes.

## 1. Objetivo da reunião

Alinhar o problema a ser resolvido pelo SentIA, discutir funcionalidades e alternativas tecnológicas, organizar as responsabilidades iniciais da equipe e distribuir a elaboração do **Documento de Visão do Produto e do Projeto**.

## 2. Assuntos discutidos

### 2.1. Problema e proposta de solução

A equipe discutiu a dificuldade de identificar sistematicamente as percepções expressas em grandes volumes de publicações de redes sociais. O SentIA foi apresentado como uma solução para analisar textos relacionados a temas, pessoas, produtos ou acontecimentos e classificar os sentimentos como **positivos, negativos ou neutros**.

As funcionalidades levantadas inicialmente foram:

- Apresentação de **gráficos** com a distribuição dos sentimentos;
- Exibição de um **breve resumo textual** das percepções identificadas;
- Disponibilização de **filtros**, incluindo a possibilidade de consultar recortes temporais, como as últimas 24 horas.

Hellen sugeriu como referência os resumos de avaliações encontrados em serviços como Google Maps e Mercado Livre. A forma de gerar esses resumos, os tipos de gráfico e os filtros específicos ficaram para refinamento posterior.

### 2.2. Experimentos de classificação de sentimentos

Renato demonstrou experimentos iniciais com duas alternativas:

- **LeIA:** abordagem baseada em léxico, considerada insatisfatória em exemplos apresentados;
- **scikit-learn:** abordagem de aprendizado de máquina com resultados exploratórios mencionados entre aproximadamente **75% e 80% de acerto**, conforme a configuração.

O **scikit-learn** foi considerado a alternativa inicial mais promissora. Ricardo indicou que precisaria estudar melhor o modelo, e Renato se dispôs a compartilhar o material de referência.

> Os percentuais apresentados são resultados de provas de conceito mostradas na reunião, **não a avaliação definitiva do modelo do SentIA**.

### 2.3. Pipeline de aquisição e processamento

Foi discutido um fluxo preliminar:

1. **Aquisição de dados:** estudar datasets disponíveis e, se necessário, coletar textos via web scraping ou APIs;
2. **Pré-processamento:** conversão para minúsculas, limpeza textual, remoção de stopwords, tratamento de emojis, redução de radicais e vetorização;
3. **Classificação:** utilização de um modelo para identificar a polaridade dos textos;
4. **Apresentação:** gráficos, resumos e filtros para consulta dos resultados.

A adequação dos datasets foi apontada como um ponto ainda a avaliar. Também foi comentado que, caso fosse necessária uma coleta própria, ela não precisaria funcionar em tempo real.

### 2.4. Tecnologias e formato da aplicação

A seguinte stack foi discutida como **proposta inicial**, sujeita a ajustes:

| Área | Tecnologias consideradas |
| --- | --- |
| Linguagem principal | Python |
| Interface e visualização | Streamlit |
| Backend / API | FastAPI |
| Banco de dados | MongoDB |
| Machine Learning | scikit-learn |
| Processamento de linguagem natural | NLTK |
| Organização e versionamento | Git e GitHub |

Também foram discutidas alternativas de aplicação web ou aplicativo e a eventual utilização de Java. A orientação geral foi priorizar uma solução simples, com tecnologias que a equipe pudesse estudar e utilizar de maneira viável.

### 2.5. Distribuição inicial de funções

Foi proposta a seguinte divisão das frentes de trabalho, **a ser confirmada com os integrantes que não participaram**:

| Frente | Integrante(s) |
| --- | --- |
| Scrum Master, acompanhamento e testes | Renato |
| Product Owner e apoio ao frontend | Hellen |
| Frontend / dashboard | Hellen e Juliana |
| Banco de dados | Julia e Maria Eduarda |
| Machine Learning e tratamento de dados | Ricardo e Gabriel |
| Dataset e aquisição dos dados | Breno, com apoio de Renato |

Juliana manifestou preferência por atuar no frontend, mantendo-se disponível para apoiar atividades de banco de dados, área em que relatou experiência.

### 2.6. Divisão do Documento de Visão

Foi apresentado o documento compartilhado no Google Docs. A distribuição inicial dos tópicos ficou registrada da seguinte forma:

| Seção | Assunto | Responsável(eis) indicados |
| --- | --- | --- |
| 1 | Visão Geral do Produto | Julia e Juliana |
| 2 | Visão Geral do Projeto | Ricardo e Gabriel |
| 3 | Processo de Desenvolvimento de Software | Breno |
| 4 | Declaração de Escopo do Projeto, incluindo backlog, perfis e cenários | Hellen |
| 5 | Métricas e Medições | **Não definido explicitamente na transcrição** |
| 6 | Testes de Software | Renato |

Foi mencionado um possível prazo para a quarta-feira seguinte, mas a transcrição não permite confirmar a data. A discussão detalhada do **Documento de Arquitetura** foi deixada para a próxima reunião.

### 2.7. Processo de trabalho e comunicação

Foi proposta a organização do desenvolvimento em **Sprints de aproximadamente sete dias**, com priorização de histórias de usuário e manutenção do backlog pela Product Owner, em colaboração com a equipe.

Renato relembrou orientações de Git e GitHub, incluindo clonagem do repositório, branches, issues e pull requests, e incentivou os integrantes a estudarem suas áreas e auxiliarem outras frentes quando necessário.

A equipe também foi convidada a realizar **ao menos uma reunião semanal**, com espaço para informar atividades concluídas, planejamento, dificuldades e impedimentos. O horário de sexta-feira à noite foi considerado pouco favorável à presença de todos; ficou pendente buscar um horário em que **seis ou sete integrantes** pudessem participar.

## 3. Encaminhamentos

| Encaminhamento | Responsável(eis) | Situação registrada |
| --- | --- | --- |
| Compartilhar o Documento de Visão, o quadro Miro e a transcrição em canais acessíveis | Renato | Compartilhamento/organização anunciados; conclusão posterior não verificável |
| Iniciar a construção e priorização do Product Backlog | Hellen, com apoio da equipe | A iniciar |
| Elaborar as seções do Documento de Visão conforme a divisão proposta | Integrantes indicados na seção 2.6 | A iniciar / em elaboração |
| Avaliar datasets e alternativas de aquisição | Breno, com apoio de Renato | Pendente |
| Estudar o uso de scikit-learn e o pré-processamento | Ricardo e Gabriel | Pendente |
| Pesquisar as tecnologias de cada frente | Toda a equipe | A iniciar |
| Revisar as instruções de uso do GitHub | Toda a equipe | A verificar |
| Confirmar a distribuição de atividades com os demais integrantes | Toda a equipe | Pendente |
| Definir horário semanal de reunião com maior participação | Equipe, com facilitação do Scrum Master | Pendente |
| Discutir o Documento de Arquitetura | Toda a equipe | Próxima reunião |

## 4. Pontos pendentes de confirmação

- Data, horário e lista oficial de presença da primeira reunião;
- Aceite da distribuição de funções pelos integrantes que não participaram;
- Responsável pela **seção 5 — Métricas e Medições** do Documento de Visão;
- Dataset, abordagem final de classificação e stack definitiva;
- Detalhes da interface, filtros e geração do resumo textual;
- Prazo de entrega do Documento de Visão;
- Data e horário da próxima reunião.

## 5. Próxima reunião

Foi indicado que o próximo encontro abordaria o **Documento de Arquitetura**, o andamento das atividades por frente de trabalho e eventuais impedimentos. **A data e o horário não foram definidos na transcrição.**

---

**Fonte:** transcrição automática em formato WebVTT da reunião “Primeira reunião - Grupo Liskov T03”, fornecida pela equipe.

**Nota editorial:** esta ata sintetiza o conteúdo da reunião. Termos claramente distorcidos pela transcrição automática foram normalizados com apoio da documentação do projeto. As propostas iniciais não são apresentadas como definições técnicas definitivas.
