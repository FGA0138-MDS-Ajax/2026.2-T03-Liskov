# Contrato entre o painel e a API

**Situação em 07/11/2026:** o backend oferece somente `GET /health`. As rotas de
análises abaixo **ainda não existem**. Este documento é uma **proposta do frontend**
para as issues #19, #21, #23, #24 e #25, e pode mudar quando o contrato for aprovado.

No código, a proposta é consumida por `src/apresentacao/fontes/api.py`. Enquanto o
backend não evolui, as telas usam `fontes/mock.py`, que implementa a mesma interface
(`FonteAnalises`, em `contrato.py`). Testes com respostas simuladas **não comprovam
integração**.

## Rotas

| Rota | Situação | Origem |
|---|---|---|
| `GET /health` | **Existe** | `src/servico/main.py` |
| `GET /analises` | Não existe | Nome e filtros: Arquitetura 2.4.2. Paginação e corpo: proposta |
| `GET /analises/resumo` | Não existe | **Proposta.** O esquema (seção 4.7) prevê a contagem por sentimento, mas não define a rota |
| `POST /datasets` | Não existe | Nome: Arquitetura 2.4.2. Corpo: a definir |
| `POST /coletas` | Não existe | Nome: Arquitetura 2.4.2. Corpo: a definir |

**Por que `/analises/resumo`?** Indicadores, gráfico e resumo precisam de totais sobre
todos os registros filtrados. Calculá-los no painel exigiria baixar todas as páginas,
contrariando a meta de resposta em até 2 segundos e a regra de filtrar no banco.

## Filtros (propostos para as duas rotas de leitura)

| Parâmetro | Formato | Regra proposta |
|---|---|---|
| `inicio` | `AAAA-MM-DD` | Inclusivo |
| `fim` | `AAAA-MM-DD` | Inclusivo; `inicio` depois de `fim` retorna 422 |
| `sentimento` | `positivo`, `neutro` ou `negativo` | Outro valor retorna 422 |

Somente em `/analises`: `pagina` (a partir de 1) e `tamanho`. O backend define o limite
máximo e uma ordenação determinística (issue #23).

`pagina` e `tamanho` devem ser inteiros positivos; `total` é inteiro não negativo.
Booleanos, números fracionários e números em strings são rejeitados, sem conversão.
`itens` é uma lista com no máximo `tamanho` registros, respeitando o total restante
a partir de `(pagina - 1) * tamanho`. Uma página além do fim pode retornar lista vazia.
Ainda não há limite máximo de tamanho aprovado; o cliente não inventa esse limite.

## Respostas propostas

`GET /analises`: coleção vazia retorna 200 com `itens: []`, sem erro.

```json
{
  "itens": [
    {
      "id_origem": "c_001",
      "fonte": "exemplo_coleta",
      "texto_original": "Texto de exemplo.",
      "sentimento": "negativo",
      "modelo": { "nome": "pysentimiento/bertweet-pt-sentiment" },
      "data_processamento": "2026-10-29T14:30:05Z",
      "data_publicacao": null
    }
  ],
  "pagina": 1,
  "tamanho": 20,
  "total": 1
}
```

Os campos seguem `docs/banco/esquema-mongodb.md`. `data_publicacao` pode ser nula:
datas nunca são inventadas.

O cliente valida os tipos em tempo de execução: `id_origem` é string não vazia,
`fonte` e `texto_original` são strings, `sentimento` é uma das três classes e
`modelo.nome` é string não vazia. Strings apenas com espaços não servem como ID ou
nome de modelo. Datas devem ser strings ISO 8601 com horário e fuso; offsets válidos
são normalizados para UTC. Ausência ou `null` em `data_publicacao` representa data
desconhecida; string vazia e datetime sem fuso são rejeitados.

`GET /analises/resumo`:

```json
{
  "total": 3,
  "por_sentimento": { "positivo": 1, "neutro": 1, "negativo": 1 },
  "sem_data_publicacao": 2
}
```

`sem_data_publicacao` conta os registros deixados de fora do filtro de período por não
terem data. Sem filtro de período, vale 0. O painel usará esse número para avisar o
usuário quando os filtros forem implementados, como recomenda o esquema (seção 4.7).
Esse aviso ainda não é exibido pelo dashboard atual.

`total` conta somente os registros que atendem aos filtros e deve ser igual à soma
das contagens das três classes em `por_sentimento`. Essas contagens e
`sem_data_publicacao` são inteiros não negativos, sem booleanos ou coerção de strings.
`por_sentimento` contém exatamente `positivo`, `neutro` e `negativo`.
Os excluídos sem data não entram no total filtrado e podem superar esse total.
Sem filtro de período, `sem_data_publicacao` deve ser 0; quando omitido, assume 0
por compatibilidade com o contrato inicial. Respostas inválidas geram `ErroFonteDados`.

## Erros

| Situação | Mensagem exibida no painel |
|---|---|
| Sem conexão | Não foi possível conectar à API... |
| Tempo esgotado | A API demorou demais para responder. |
| 400 ou 422 | A API recusou os filtros informados. |
| 404 | A API não oferece a rota... |
| Outros códigos | A API retornou um erro inesperado (HTTP N). |
| Corpo inválido ou fora do contrato | A resposta da API não segue o contrato. |

## Pontos em aberto

1. Qual data o filtro de período usa (decisão pendente; issue #24).
2. Fuso horário usado para interpretar `inicio` e `fim` (issue #24).
3. Dados para o gráfico "Evolução no período", se for mantido (decisão pendente da PO).
4. Responsável pelo backend: as issues #21, #23, #24 e #25 estão sem responsável.

## Como trocar o mock pela API

1. O backend publica as rotas e o contrato é aprovado na issue #19.
2. Ajustar `fontes/api.py` e `tests/test_painel_fonte_api.py` se o contrato mudar.
3. Definir `SENTIA_FONTE_DADOS=api` e `SENTIA_API_URL`. As telas não mudam.
