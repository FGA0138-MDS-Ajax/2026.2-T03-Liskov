# Changelog

Mudanças relevantes do SentIA. O processo está descrito em
[docs/frontend/README.md](docs/frontend/README.md#changelog). O projeto ainda não possui
versões publicadas; outras frentes também podem registrar suas entregas aqui.

## [Não lançado]

### Corrigido

- Cliente HTTP rejeita tipos, contagens, paginação e datas incompatíveis com a
  proposta de contrato, sem derrubar a tela nem converter valores incorretos.
- Timeout da API exige número finito positivo; configuração inválida mostra
  mensagem na interface. Aviso de registros sem data é documentado como futuro.

### Alterado


- Dependências migradas de `requirements*.txt` para `pyproject.toml` e `uv.lock`. A instalação
  agora usa `uv sync --locked`, com Python 3.11 definido em `.python-version`.

### Adicionado

- Busca do Usuário no X pelo dashboard (#120): com o filtro de assunto e menos de 50
  análises, o botão "Buscar no X" completa o assunto com textos recentes, sem login, por
  `POST /pesquisas` e `GET /pesquisas/{id}`. Meta fixa de 50; o X só completa o que falta;
  limite diário de buscas no X (padrão 15, `SENTIA_LIMITE_BUSCAS_X_DIA`), em que só conta a
  busca que chama o X; cache de 30 dias para todas as pesquisas. Sem chave ou com o limite
  esgotado, mostra a base com aviso. A Administração não entra no limite.

- Filtro por assunto no dashboard e na API (#113): campo "Assunto" ao lado de período e
  sentimento, e `?assunto=` em `GET /analises` e `GET /analises/resumo`. Usa a mesma regra
  da pesquisa do Administrador (maiúsculas e acentos não importam; palavras vazias
  ignoradas; comparação pelo radical), agora em `src/comum/busca_textual.py`, compartilhado
  pela API, pelo repositório e pelo modo de demonstração. O texto digitado nunca vira
  expressão regular. Sem textos sobre o assunto, o painel avisa em vez de quebrar. A coluna
  de publicação passa a "Publicado em (UTC)" (decisão da PO de 26/11: datas em UTC).

- Resumo textual no dashboard: síntese da seleção atual com o total de análises, a distribuição
  por sentimento e o sentimento predominante, montada por regras a partir do mesmo resumo dos
  indicadores e do gráfico (sem modelo de linguagem). Informa empates, avisa quando a base é
  pequena e, sem dados, informa a ausência de registros sem afirmar sentimentos (#29).
- Gráfico de distribuição dos sentimentos no dashboard: barras com a quantidade e o
  percentual de cada classe no filtro aplicado, usando o mesmo resumo dos indicadores. O
  sentimento é identificado por nome e valor escrito, não só por cor, e há uma tabela
  equivalente para leitores de tela. Classes sem registros aparecem com zero (#28).
- Listagem paginada das análises no dashboard, consumindo `GET /analises` com os mesmos
  filtros dos indicadores: texto (com `@menções` mascaradas), sentimento, fonte, data de
  publicação ("Sem data" quando ausente), data de processamento em UTC e modelo. Tem estados
  de carregamento, vazio e erro; no modo mock continua identificada como dados de exemplo (#27).
- Teste de fumaça que executa o painel contra a API FastAPI real, com só o MongoDB simulado (#27).
- Filtros de período e de sentimento no dashboard, com botão "Limpar" e aviso de quantos
  textos sem data ficaram fora do período, **com dados de exemplo** (#14).
- Login do Administrador: sem login, o menu mostra só "Entrar" e as ferramentas de
  administração ficam ocultas (#59).
- Importação de dataset CSV pelo painel, com relatório de registros importados e descartados
  (#60), e início e acompanhamento de coleta e análise (#61). Ambos usam **dados de exemplo**
  até a API oferecer as rotas.
- Proposta de contrato para login, importação e coleta, com cliente HTTP correspondente (#58).
- Rotas de administração na API: login com senha em hash scrypt e token com expiração, logout,
  importação de CSV e coleta com análise pelo BERTweet, todas exigindo login (#58). Os dados
  ficam em memória até a persistência no MongoDB (#20).
- Pesquisa híbrida por assunto na administração, em aba ao lado da importação: procura primeiro
  nos textos já guardados e, se permitido, completa com tweets novos do X pelo XFetch, mostrando
  a origem de cada texto e o resultado por sentimento (docs/pesquisa_hibrida_mongodb_xfetch.md).
  Versão de teste, ainda sem issue.
- `scripts/analisar_em_lotes.py`: analisa um CSV com o BERTweet de 100 em 100 linhas, no
  processador, para testar em máquinas com pouca memória.
- Análise logo após importar o dataset (#60) e resultado da coleta com indicadores por
  sentimento e exemplos, com `@menções` mascaradas (#61).
- Wireframes do dashboard na documentação, com o que já foi implementado de cada um (#14).
- Base do painel Streamlit com navegação entre Dashboard e Administração; a Administração
  ainda é só um aviso de área não implementada (#13).
- Indicadores de total e percentual por sentimento no dashboard, **com dados de exemplo**
  identificados na tela (#14).
- Mensagens de estado vazio e de erro quando não há dados ou a fonte falha.
- Cliente HTTP para o contrato **proposto** da API. Ainda sem integração com o backend, que
  não oferece as rotas de análises (#19).
- Lint e testes do frontend na CI.
- Makefile com atalhos para instalar, executar e validar o projeto.
