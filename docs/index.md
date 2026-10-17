# SentIA — Análise de Sentimentos

O **SentIA** é uma plataforma web de análise de sentimentos desenvolvida pelo grupo **Liskov — Turma 03**, da disciplina de **Métodos de Desenvolvimento de Software (MDS)** da Universidade de Brasília — Faculdade do Gama.

O projeto tem como objetivo apoiar a análise de grandes volumes de textos em português, classificando os conteúdos de acordo com sua polaridade:

- Positivo
- Negativo
- Neutro

Os resultados serão apresentados de forma consolidada por meio de um dashboard interativo.

## Objetivo do projeto

O SentIA busca automatizar o fluxo de análise de sentimentos, desde a aquisição e preparação dos dados textuais até a classificação, persistência e visualização dos resultados.

## Tecnologias

O projeto utiliza principalmente:

- Python
- FastAPI
- Uvicorn
- Streamlit
- MongoDB
- scikit-learn
- NLTK
- GitHub Actions
- MkDocs Material

## Arquitetura

O sistema será organizado em camadas, separando responsabilidades de:

- Apresentação
- Serviço
- Processamento
- Persistência de dados

O fluxo principal do sistema segue a sequência:

`Aquisição → Pré-processamento → Classificação → Persistência → API → Dashboard`

## Documentação

A documentação do projeto inclui:

- Visão do Produto e Projeto
- Documento de Arquitetura
- Métricas e GQM
- Estratégia de Testes
- Atas de Reunião
- Processo de Desenvolvimento

## Equipe

Projeto desenvolvido pelo grupo **Liskov — T03**, na disciplina de Métodos de Desenvolvimento de Software.