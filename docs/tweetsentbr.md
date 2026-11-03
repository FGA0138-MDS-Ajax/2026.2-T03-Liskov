# TweetSentBR

## Descrição

O TweetSentBR é utilizado pelo SentIA como uma das fontes de textos em português para tarefas de classificação de sentimento.

O dataset utilizado pelo projeto está incluído diretamente no repositório, pois seu tamanho é compatível com o versionamento do projeto.

## Localização no projeto

```text
datasets/
└── tweetsent.csv
```

> **Importante:** o arquivo `tweetsent.csv` faz parte do repositório e deve permanecer nessa pasta para que a aquisição local consiga encontrá-lo.

## Formato

O arquivo é um CSV. O módulo de aquisição do SentIA realiza a leitura do arquivo e converte os registros para a estrutura padronizada utilizada pelo pipeline.

## Validação realizada

O arquivo foi importado pelo módulo de aquisição em modo tolerante.

- Registros importados: **8.530**
- Registros descartados: **0**
- Motivos de descarte: **nenhum**

## Uso no projeto

O TweetSentBR é utilizado como fonte inicial para a camada de aquisição de dados. A importação prepara os registros para as etapas posteriores de pré-processamento e classificação.

A importação do dataset não realiza classificação de sentimento por conta própria.

## Reprodutibilidade

Para testar a importação localmente, utilize o módulo de aquisição apontando para:

```text
datasets/tweetsent.csv
```

O dataset deve permanecer com o nome e a localização documentados acima para evitar divergências entre os ambientes dos integrantes da equipe.
