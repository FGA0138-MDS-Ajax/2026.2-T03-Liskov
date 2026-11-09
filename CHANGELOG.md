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

- Filtros de período e de sentimento no dashboard, com botão "Limpar" e aviso de quantos
  textos sem data ficaram fora do período, **com dados de exemplo** (#14).
- Login do Administrador: sem login, o menu mostra só "Entrar" e as ferramentas de
  administração ficam ocultas (#59).
- Importação de dataset CSV pelo painel, com relatório de registros importados e descartados
  (#60), e início e acompanhamento de coleta e análise (#61). Ambos usam **dados de exemplo**
  até a API oferecer as rotas.
- Proposta de contrato para login, importação e coleta, com cliente HTTP correspondente (#58).
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

## Preparação PC1 — 09/11/2026 (proposta)

- README do produto, roteiro offline e relatórios de QA com limites explícitos.
- Demo CSV → analisador simulado → BSON, sem serviços externos.
- Exemplo de ambiente unificado, template de PR e lint incremental em todas as camadas.
- Auditoria e correções dos PRs #64/#65 em branches próprias; sem merge oficial.
