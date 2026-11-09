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

- Base do painel Streamlit com navegação entre Dashboard e Administração; a Administração
  ainda é só um aviso de área não implementada (#13).
- Indicadores de total e percentual por sentimento no dashboard, **com dados de exemplo**
  identificados na tela (#14).
- Mensagens de estado vazio e de erro quando não há dados ou a fonte falha.
- Cliente HTTP para o contrato **proposto** da API. Ainda sem integração com o backend, que
  não oferece as rotas de análises (#19).
- Lint e testes do frontend na CI.
- Makefile com atalhos para instalar, executar e validar o projeto.
