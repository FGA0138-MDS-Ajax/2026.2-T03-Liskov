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

- O lint da CI e do `make lint` passa a cobrir também `src/servico` e os testes da
  administração da API.
- O painel limita o upload a 10 MB, o mesmo limite padrão da API.

- Dependências migradas de `requirements*.txt` para `pyproject.toml` e `uv.lock`. A instalação
  agora usa `uv sync --locked`, com Python 3.11 definido em `.python-version`.

### Adicionado

- Filtros de período e de sentimento no dashboard, com botão "Limpar" e aviso de quantos
  textos sem data ficaram fora do período, **com dados de exemplo** (#14).
- Login do Administrador: sem login, o menu mostra só "Entrar" e as ferramentas de
  administração ficam ocultas (#59).
- Importação de dataset CSV pelo painel, com relatório de registros importados e descartados
  (#60), e início e acompanhamento de coleta e análise (#61), no modo de exemplo e com a API.
- Autenticação do Administrador na API (#58): `POST /auth/login` e `POST /auth/logout`, senha
  guardada só como hash scrypt em variável de ambiente, sessões com expiração e limite de
  tentativas. Comando `make hash-senha` para gerar o hash.
- Rotas de administração na API: `POST /datasets`, `GET /coletas/fontes`, `POST /coletas` e
  `GET /coletas/{id}`, com a análise pelo BERTweet em segundo plano (#60, #61). Até a
  persistência (#20), os dados ficam **em memória** e se perdem quando a API reinicia.
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
