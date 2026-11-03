# BPSAD

## Descrição

O BPSAD é utilizado pelo SentIA como uma fonte adicional de textos em português para testes, processamento e avaliação relacionados à classificação de sentimento.

Diferentemente do TweetSentBR, o BPSAD possui volume muito grande para ser armazenado diretamente no repositório Git do projeto.

Por esse motivo, **o dataset completo não deve ser versionado no GitHub**.

## Acesso ao dataset

O dataset completo deve ser obtido externamente e mantido localmente quando necessário.

Fonte:

https://github.com/paulobio/BPSAD

> A equipe deve verificar as condições de uso e distribuição da fonte antes de redistribuir os arquivos.

## Arquivo utilizado na validação

Na validação local do SentIA foi utilizado o arquivo:

```text
concatenated.csv
```

O arquivo possui aproximadamente **2,8 milhões de registros**, portanto não é adequado para ser colocado no repositório do projeto.

## Validação realizada

A importação do arquivo completo foi executada em modo tolerante utilizando o módulo de aquisição do SentIA.

- Registros importados: **2.786.073**
- Registros descartados: **19**
- Motivo dos descartes: **texto vazio (`texto_vazio`)**
- Outros motivos de descarte registrados: **nenhum**

Os 19 registros com `review_text` vazio foram descartados pelo importador em modo tolerante, permitindo que a leitura do restante do dataset continuasse normalmente.

## Uso no projeto

O BPSAD é utilizado como uma fonte de maior volume para validação e experimentação do pipeline de aquisição e processamento.

O arquivo completo deve permanecer fora do Git e ser disponibilizado localmente apenas quando necessário.

Para testes automatizados e testes rápidos do importador, recomenda-se manter no repositório apenas uma pequena amostra (`bpsad_sample.csv`) representativa da estrutura do BPSAD.

## Reprodutibilidade

Para reproduzir a validação completa:

1. Obter o dataset BPSAD pela fonte indicada acima.
2. Localizar o arquivo `concatenated.csv`.
3. Executar o importador do SentIA apontando para o arquivo local.
4. Utilizar o modo tolerante quando a intenção for processar o dataset completo mesmo havendo registros inválidos.

Exemplo:

```python
from src.processamento.aquisicao.csv_importer import (
    importar_dataset_csv,
    RelatorioImportacao,
)

relatorio = RelatorioImportacao()

registros = importar_dataset_csv(
    "caminho/para/concatenated.csv",
    modo_estrito=False,
    relatorio=relatorio,
)

print("Importados:", len(registros))
print("Descartados:", relatorio.total_descartados)
print("Motivos:", relatorio.descartes_por_motivo)
```

## Observação sobre versionamento

O fato de o BPSAD não estar no repositório é intencional. O GitHub deve conter o código necessário para importar e processar o dataset, além da documentação e, se necessário, uma pequena amostra para testes.

O dataset completo deve ser tratado como um recurso externo e não como parte do código-fonte do SentIA.
