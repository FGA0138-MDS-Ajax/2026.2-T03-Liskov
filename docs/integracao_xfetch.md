# Aquisição XFetch — contrato e operação

## Implementado nesta proposta

`src/processamento/aquisicao/xfetch.py` consulta `/v1/search/recent`, pagina,
normaliza registros, elimina duplicatas por ID e trata erros. Não classifica nem
persiste. Testes usam exclusivamente respostas sintéticas e chaves fictícias.

```python
from src.processamento.aquisicao.xfetch import buscar_tweets_xfetch

registros = buscar_tweets_xfetch("tecnologia lang:pt", quantidade=45, max_paginas=3)
```

Esse exemplo faz requisições pagas se executado com chave real: preparar e obter
autorização antes. Configure `XFETCH_API_KEY` em ambiente ou `.env` não versionado.
A branch foi atualizada com a developer `c6fc535` em 09/11/2026. A instalação
atual usa `uv sync --locked`; o workflow preserva a CI uv da developer e inclui
o destino `xfetch` para correções. Para testes offline, após preparar dependências:
`uv run --offline pytest tests/test_xfetch.py tests/test_xfetch_pipeline.py -v -ra`.
O pipeline continua separado deste módulo; os testes de integração usam somente
HTTP/analisador simulados e serialização BSON, sem gravar no MongoDB.

## Contrato externo verificado em 09/11/2026

Fontes oficiais consultadas: [OpenAPI](https://xfetch.io/openapi.json),
[documentação de busca](https://xfetch.io/twitter-search-api) e
[regras gerais](https://xfetch.io/docs). O endpoint recebe Bearer, `query`, `limit`,
`sort_order` e `next_token`, retorna `data[]` e token em
`meta.pagination.next_token`. Tokens são opacos; query, limit e ordenação devem
permanecer iguais entre páginas. A página de busca documenta páginas de até 20.
Manter `limit` constante corrige a documentação anterior que prometia reduzi-lo
na última requisição. Para 45 resultados com páginas cheias: pedidos 20/20/20,
com no máximo 45 registros devolvidos pelo módulo; itens extras podem ter custo.

## Limites locais e custos

| Parâmetro | Padrão / limites |
|---|---|
| `quantidade` | 100; inteiro de 1 a 100, máximo de registros únicos devolvidos |
| `limite_por_pagina` | 20; inteiro de 1 a 20 |
| `max_paginas` | `None`; paginação automática com **teto absoluto de 10 requisições** |
| Timeout | 30 segundos por requisição; sem retry automático |

`max_paginas=3` reduz o teto a três; valores acima de dez continuam limitados a dez.
O teto é uma política de segurança do SentIA, não um limite contratual do XFetch.
Páginas vazias, incompletas ou duplicadas também contam. A busca termina ao atingir
a quantidade, faltar token, repetir token ou atingir teto. Pode retornar menos
resultados. Não há garantia de representatividade da opinião pública.
O teto limita requisições, não promete um custo financeiro fixo.

HTTP 401/402/403/429/500/503 e demais falhas interrompem a chamada com `ErroXFetch`;
não há tentativas automáticas nem retorno parcial silencioso após falha HTTP.
Erros não reproduzem mensagem do driver, chave, headers ou consulta.
JSON inválido, ausência de `data`, envelope/token inválido ou data malformada
são erros explícitos. Registros individuais sem texto/ID válidos são ignorados.

## Contrato interno e privacidade

Exemplo inteiramente sintético:

```python
{
    "id_origem": "synthetic-1",
    "texto_original": "Texto sintético para demonstração 😊",
    "fonte": "X",
    "rotulo_original": None,
    "rotulo_padronizado": None,
    "data_publicacao": "2026-11-09T10:00:00Z",
    "metadados": {"provedor": "XFetch", "lang": "pt", "like_count": 0}
}
```

Texto é preservado integralmente, sem limpeza externa ao tokenizador do BERTweet.
ID é string não vazia (inteiros são convertidos); datas informadas precisam de
fuso e são normalizadas para ISO 8601 UTC. Datas ausentes ficam `None`.
Não se inventa `sentimento`, rótulo humano nem data. O pipeline converte a data
para datetime UTC e adiciona previsão/probabilidades para o contrato MongoDB.

`author_id`, nomes, perfis e objetos arbitrários **não são propagados**. Metadados
permitidos: provedor, idioma textual e contadores inteiros não negativos
`like_count`, `retweet_count`, `reply_count`, `quote_count`. Essa redução atende
à política existente em `docs/banco/esquema-mongodb.md` da developer, sem alterar
a política. O texto bruto pode conter menções fornecidas na fonte; sua eventual
anonimização é decisão de produto/privacidade que exige discussão com a PO.

## Ainda proposto

Pesquisa híbrida, consultas ao MongoDB, embeddings, Vector Search e orquestração
banco + provedor não estão implementados. Ver a
[proposta futura](pesquisa_hibrida_mongodb_xfetch.md). API/frontend ainda não
expõem essa aquisição ao usuário. Compatibilidade offline com o pipeline não
comprova consulta real, licença de dados, autenticação ou persistência.

## Validação de integração — 09/11/2026

Referências: head XFetch `2dfa96f47f08da723590a15aa7f2abf77c7ae8e9`, já com
a correção #68, e developer `c6fc53561055178085edcbc123fc86166edf89fa`.
O único conflito foi `.github/workflows/ci.yml`: preservados Python 3.11,
instalação uv locked e lint/testes da developer, reunindo também o destino
`xfetch` aos destinos de PR existentes. Nenhuma versão/dependência foi alterada.

Suíte integrada: **455 passed, 0 failed/skipped, 96% de cobertura de src**
(1.173 instruções, 46 não cobertas). Focados XFetch/pipeline: **61 passed**.
Ruff do frontend, Ruff `F,E9` geral, lock check e diff check aprovados.
Um aviso de depreciação Starlette/httpx permanece, sem falhas.

Os novos testes em `tests/test_xfetch_pipeline.py` verificam paginação e
deduplicação, lotes de um/dois registros, preservação de texto/ID/fonte,
datas UTC e ausentes, exclusão de identificadores do autor, anotações humanas
ausentes e documentos BSON serializáveis. Uma falha HTTP na segunda página
interrompe a aquisição sem retornar resultado parcial ou repetir a chamada.

A verificação usa respostas HTTP e analisador sintéticos, sem chave real,
requisição paga, inferência BERTweet real ou servidor MongoDB. O contrato
externo foi reconferido na OpenAPI/documentação oficial citada acima.
A aprovação técnica do módulo não conclui a pesquisa híbrida nem a integração
real do dashboard, persistência e serviço externo.
