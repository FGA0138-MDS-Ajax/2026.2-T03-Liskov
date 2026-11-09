# Pesquisa híbrida: MongoDB + XFetch

## Objetivo

Implementar uma pesquisa híbrida no SentIA: primeiro consultar os tweets já armazenados no MongoDB e, caso não existam resultados suficientes, buscar novos tweets no XFetch.

A pesquisa deve ser *loose* (flexível), procurando publicações relacionadas ao significado e ao contexto da consulta, em vez de depender exclusivamente da correspondência exata das palavras digitadas pelo usuário.

## Fluxo geral

1. Receber a consulta do usuário.
2. Preparar a consulta para a pesquisa.
3. Pesquisar no MongoDB os tweets relacionados ao assunto.
4. Avaliar a quantidade e a relevância dos resultados encontrados.
5. Se houver resultados suficientes, reutilizá-los.
6. Se houver menos resultados do que o necessário, consultar o XFetch para complementar a amostra.
7. Salvar no MongoDB os novos tweets obtidos.
8. Unir os resultados, remover duplicatas e encaminhar os tweets para a etapa seguinte do sistema.

```text
        Usuário pesquisa
               |
               v
       Preparar consulta
               |
               v
       Pesquisar MongoDB
               |
         Há resultados
          suficientes?
          /         \
        SIM          NÃO
         |            |
         v            v
   Reutilizar       Consultar XFetch
   resultados       para complementar
         |            |
         |            v
         |       Salvar novos tweets
         |       no MongoDB
         |            |
         +-----+------+
               |
               v
       Remover duplicatas
               |
               v
        Retornar resultados
```

## Estratégia de pesquisa no MongoDB

Existem diferentes formas de pesquisar textos no MongoDB:

| Método | Funcionamento | Limitação |
|---|---|---|
| `$regex` | Procura trechos de texto que correspondam a um padrão | Depende bastante das palavras presentes na consulta |
| Text Search | Pesquisa termos indexados no texto | Encontra correspondências lexicais, mas não compreende plenamente o significado |
| Vector Search | Compara vetores (*embeddings*) que representam o conteúdo semântico dos textos | Exige gerar e armazenar embeddings e configurar a busca vetorial |

### Pesquisa semântica com embeddings

A estratégia recomendada para uma pesquisa realmente flexível é utilizar embeddings e Vector Search.

Um modelo de embeddings transforma a consulta e os textos dos tweets em representações numéricas. A busca compara essas representações para encontrar conteúdos semanticamente semelhantes.

Por exemplo, uma pesquisa por:

> O preço das coisas está aumentando muito.

poderia encontrar um tweet como:

> Está cada vez mais caro fazer compras no supermercado.

Mesmo sem repetir as mesmas palavras, os textos tratam de assuntos relacionados.

**Pré-requisito:** para utilizar essa estratégia, os embeddings dos tweets precisam ser gerados e armazenados no banco. Também é necessário configurar o índice de Vector Search na infraestrutura MongoDB compatível.

## Integração com o XFetch

O XFetch será utilizado para complementar os resultados quando o MongoDB não encontrar uma quantidade suficiente de tweets relevantes.

Exemplo com uma meta de 100 tweets:

| Origem | Quantidade |
|---|---:|
| MongoDB | 35 |
| XFetch | Até 65 novos tweets |
| Total desejado | 100 |

A quantidade efetivamente obtida do XFetch pode ser menor que a solicitada. Por isso, o sistema deve trabalhar com a quantidade realmente retornada, e não presumir que sempre receberá todos os tweets pedidos.

Antes de combinar os resultados, o sistema deve remover duplicatas, utilizando o identificador de origem do tweet (`id_origem`).

## Responsabilidades por camada

| Camada | Responsabilidade |
|---|---|
| Aquisição | Consultar o XFetch e normalizar os tweets recebidos |
| Dados | Consultar, recuperar e persistir tweets no MongoDB |
| Serviço | Coordenar a pesquisa híbrida, verificar se há resultados suficientes e combinar as fontes |
| Classificação | Receber os tweets selecionados e classificá-los com o BERTweet |

A lógica que decide quando consultar o MongoDB ou o XFetch deve ficar na camada de serviço. O módulo `xfetch.py` deve continuar responsável somente pela aquisição de dados no XFetch, sem incorporar a lógica de consulta ao banco.

## Exemplo de comportamento esperado

Considere que o usuário pesquise por **“custo de vida”** e o sistema esteja configurado para buscar até 100 tweets.

1. O sistema consulta o MongoDB por tweets semanticamente relacionados a “custo de vida”.
2. Encontra 35 tweets relevantes.
3. Solicita ao XFetch até 65 tweets novos, usando a consulta e os filtros definidos para a aquisição.
4. Salva os novos tweets no MongoDB.
5. Remove eventuais duplicatas entre os resultados.
6. Encaminha os tweets reunidos para a classificação de sentimento.

## Pontos de atenção

- A busca semântica não garante que todos os resultados sejam relevantes; é necessário definir um critério de similaridade.
- A busca do XFetch também pode retornar publicações pouco relacionadas ao assunto, mesmo com filtros de idioma.
- A quantidade de 100 tweets é uma configuração inicial para testes e análises exploratórias, não uma amostra automaticamente representativa da opinião pública.
- A persistência deve evitar duplicatas, especialmente quando uma mesma publicação aparecer em pesquisas diferentes.
- A consulta ao MongoDB e a aquisição no XFetch devem permanecer separadas por responsabilidade, com a coordenação feita pela camada de serviço.

## Recomendação inicial

Para a primeira versão, utilizar 100 tweets como quantidade-alvo por pesquisa e deixar esse valor configurável. A busca no MongoDB deve priorizar a recuperação de conteúdo já armazenado; o XFetch deve ser chamado apenas para complementar os resultados quando necessário.

A pesquisa semântica com Vector Search pode ser implementada como evolução do sistema, após a geração e persistência dos embeddings dos tweets.
