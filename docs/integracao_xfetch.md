
# Integração do módulo XFetch — SentIA

## 1. Objetivo

O módulo `xfetch.py` é responsável pela aquisição de tweets recentes por meio da API XFetch.

Sua responsabilidade termina na obtenção e padronização dos dados. A classificação de sentimentos e a persistência no banco de dados são responsabilidades de outros módulos do SentIA.

## 2. Configuração

A chave de acesso deve ser armazenada em uma variável de ambiente chamada `XFETCH_API_KEY`.

Na raiz do projeto, criar um arquivo `.env`:

```env
XFETCH_API_KEY=sua_chave_aqui
```

O arquivo `.env` não deve ser enviado ao repositório Git.

O módulo utiliza `python-dotenv` para carregar a variável de ambiente e `requests` para realizar as requisições HTTP.

## 3. Utilização

Importar a função de aquisição:

```python
from src.processamento.aquisicao.xfetch import (
    buscar_tweets_xfetch
)
```

Exemplo de pesquisa de 45 tweets:

```python
tweets = buscar_tweets_xfetch(
    consulta="tecnologia",
    quantidade=45
)
```

A paginação é automática. O módulo solicita novas páginas até atingir a quantidade desejada ou até a API não disponibilizar mais resultados.

### Parâmetros

| Parâmetro | Descrição | Valor padrão |
|---|---|---|
| `consulta` | Palavra-chave ou frase pesquisada | Obrigatório |
| `quantidade` | Quantidade máxima de tweets desejada | 100 |
| `api_key` | Chave da API, caso não seja usada a variável de ambiente | Variável de ambiente |
| `limite_por_pagina` | Quantidade máxima solicitada em cada requisição | 20 |
| `max_paginas` | Limite opcional de páginas consultadas | `None` |

A API permite solicitar até 20 tweets por página e o módulo aceita até 100 tweets por consulta.

O parâmetro `max_paginas` é opcional. Quando não informado, a paginação ocorre automaticamente, sem um limite fixo de páginas.

Também é possível definir um limite manual:

```python
tweets = buscar_tweets_xfetch(
    consulta="tecnologia",
    quantidade=100,
    max_paginas=3
)
```

Nesse exemplo, a busca será interrompida após três páginas, mesmo que ainda existam resultados.

A quantidade solicitada representa um máximo, não uma garantia. A função pode retornar menos tweets caso não existam resultados suficientes.

## 4. Funcionamento da paginação

O tamanho padrão de cada página é 20 tweets. O módulo ajusta automaticamente o limite da última requisição para não solicitar mais tweets do que o necessário.

Exemplo para uma solicitação de 45 tweets:

| Requisição | Tweets solicitados | Total acumulado |
|---|---:|---:|
| 1ª página | 20 | 20 |
| 2ª página | 20 | 40 |
| 3ª página | 5 | 45 |

A próxima página é identificada pelo `next_token` retornado pela API.

O processo é interrompido quando:

- A quantidade solicitada é atingida.
- A API não disponibiliza outro `next_token`.
- A API retorna um token que já foi utilizado.
- Um limite manual de páginas é atingido.

Tweets duplicados são eliminados pelo identificador original. Por isso, em situações com duplicatas ou páginas incompletas, mais requisições podem ser necessárias para atingir a quantidade desejada.

## 5. Formato dos dados retornados

A função retorna uma lista de dicionários padronizados para utilização pelos demais módulos do SentIA.

Exemplo:

```python
{
    "id_origem": "2119663307661451422",
    "texto_original": "Exemplo de publicação no X",
    "fonte": "X",
    "rotulo_original": None,
    "rotulo_padronizado": None,
    "data_publicacao": "2026-11-09T05:28:08.000Z",
    "metadados": {
        "provedor": "XFetch",
        "author_id": "1520220864",
        "lang": "pt",
        "like_count": 0,
        "retweet_count": 0,
        "reply_count": 0,
        "quote_count": 0
    }
}
```

### Descrição dos campos

| Campo | Descrição |
|---|---|
| `id_origem` | Identificador original do tweet no X |
| `texto_original` | Texto publicado |
| `fonte` | Origem do dado, identificada como X |
| `rotulo_original` | Rótulo original, quando disponível |
| `rotulo_padronizado` | Rótulo convertido para o padrão SentIA |
| `data_publicacao` | Data de publicação retornada pela API |
| `metadados` | Informações adicionais disponibilizadas pela API |

Os campos `rotulo_original` e `rotulo_padronizado` são retornados como `None`, pois a aquisição não realiza classificação de sentimentos.

## 6. Integração com outros módulos

O módulo pode ser chamado diretamente pelo serviço ou por outro componente responsável por coordenar a aquisição.

Exemplo simplificado:

```python
from src.processamento.aquisicao.xfetch import (
    buscar_tweets_xfetch
)

tweets = buscar_tweets_xfetch(
    consulta="educação no Brasil",
    quantidade=100
)

for tweet in tweets:
    print(tweet["texto_original"])
```

O resultado pode ser encaminhado ao módulo de pré-processamento e classificação.

Fluxo conceitual:

```text
Pesquisa do usuário
        |
        v
     Serviço
        |
        v
      XFetch
        |
        v
  Padronização dos dados
        |
        v
 Pré-processamento
        |
        v
 Classificação de sentimento
        |
        v
    Persistência
```

A integração com classificação e persistência deve ser realizada pelos respectivos responsáveis, sem transferir essas responsabilidades para o módulo de aquisição.

## 7. Tratamento de erros

O módulo utiliza a exceção `ErroXFetch` para sinalizar problemas relacionados à comunicação com a API, chave de acesso e respostas inválidas.

Exemplo:

```python
from src.processamento.aquisicao.xfetch import (
    buscar_tweets_xfetch,
    ErroXFetch
)

try:
    tweets = buscar_tweets_xfetch(
        consulta="educação",
        quantidade=100
    )

except ErroXFetch as erro:
    print(f"Erro na aquisição: {erro}")
```

Parâmetros inválidos são tratados com `ValueError` ou `TypeError`.

## 8. Testes

Os testes automatizados estão localizados em:

```text
tests/test_xfetch.py
```

Para executar somente os testes do XFetch:

```bash
python -m pytest tests/test_xfetch.py -v
```

Os testes simulam as respostas da API, portanto não precisam de uma chave válida nem consomem créditos do XFetch.
