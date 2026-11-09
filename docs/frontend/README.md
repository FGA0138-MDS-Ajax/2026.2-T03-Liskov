# Frontend do SentIA

Referência: integração PC1 `bfaf7da`, 09/11/2026, com o frontend #70 (`61926fe`) e a correção de ensaio `bcd75e7`.
O PR continua aberto para `developer`; as novas telas não estão naquela branch.

Painel em **Streamlit** (`src/apresentacao/`). Em modo `mock`, usa fontes locais;
em modo `api`, usa clientes HTTP. Nunca importa banco ou processamento;
`tests/test_painel_arquitetura.py` verifica essa regra.

- Contrato com o backend: [CONTRATO-API.md](CONTRATO-API.md)
- Wireframes e o que já foi implementado deles: [WIREFRAMES.md](WIREFRAMES.md)
- Mudanças entregues: [CHANGELOG.md](../../CHANGELOG.md)

## Telas

| Tela | Quem vê | O que faz |
|---|---|---|
| Dashboard | Todos | Filtros de período e sentimento e indicadores de total e percentual. Gráfico, listagem e resumo ainda serão adicionados (#27, #28, #29) |
| Entrar | Quem não fez login | Formulário de usuário e senha do Administrador |
| Administração | Administrador com login | Importar dataset CSV, iniciar coleta e análise e acompanhar a situação |

Sem login, o menu mostra **Entrar** no lugar de **Administração**; as ferramentas do
Administrador não aparecem (teste T03). No modo `mock`, entre com o usuário `admin` e a senha
`senha-de-exemplo`. Essas credenciais são fictícias e não funcionam no modo `api`.

## Como executar

Execute os comandos na raiz do repositório. Não há etapa de build: o Streamlit executa o
código Python diretamente. As dependências são gerenciadas pelo
[uv](https://docs.astral.sh/uv/getting-started/installation/), que também instala a versão do
Python definida em `.python-version`. Instale-o uma vez:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # Linux e macOS
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"    # Windows
```

Com `make` (Linux e macOS):

```bash
make setup   # instala as dependências do uv.lock e cria o .env
make run     # depois acesse http://localhost:8501
make check   # lint e testes, como na CI
make         # lista todos os comandos
```

Comandos diretos (para preparar o ambiente sem make, veja o [README principal](../../README.md#instalação)):

```bash
uv sync --locked
uv run streamlit run src/apresentacao/app.py  # depois acesse http://localhost:8501
```

Se o `.env` já existir (por exemplo, com `MONGODB_URI`), acrescente as variáveis em vez de
sobrescrever o arquivo.

## Dependências

`pyproject.toml` declara as dependências e `uv.lock` fixa as versões exatas. **Faça commit dos
dois** e não use `pip install` neste projeto.

| Tarefa | Comando |
|---|---|
| Adicionar dependência do projeto | `uv add pacote` |
| Adicionar dependência de desenvolvimento | `uv add --group dev pacote` |
| Remover dependência | `uv remove pacote` |
| Atualizar uma versão no `uv.lock` | `uv lock --upgrade-package pacote` |
| Instalar também o BERTweet real (download grande) | `uv sync --locked --group ml` ou `make setup-ml` |

## Modos de dados

| Variável | Valores | Uso |
|---|---|---|
| `SENTIA_FONTE_DADOS` | `mock`, `api` | Dados de exemplo ou API real |
| `SENTIA_MOCK_CENARIO` | `normal`, `vazio`, `erro` | Valida os estados da tela sem backend |
| `SENTIA_API_URL` | URL | Endereço da API |
| `SENTIA_API_TIMEOUT_SEGUNDOS` | número | Tempo máximo de espera |

No modo `mock`, todas as telas exibem o aviso **"Dados de exemplo"**. Não remova esse
aviso: mock não é integração concluída. O modo `api` ainda mostra erro porque as rotas de
análises e de administração não existem (ver contrato). O cenário `erro` também simula a
API de administração indisponível.

## Verificações

| Verificação | Comando | Local | CI |
|---|---|---|---|
| Lint do frontend | `uv run ruff check src/apresentacao tests/test_painel_*.py` | Sim | Sim |
| Testes do frontend | `uv run pytest tests/test_painel_*.py` | Sim | Pela suíte completa |
| Suíte completa | `uv run pytest --cov=src` | Antes do PR | Sim |
| Responsividade e aparência | Manual | Sim | Não |

A CI e o ambiente local usam Python 3.11, definido em `.python-version`. O projeto não tem
verificador de tipos configurado: use type hints e deixe a revisão por pares conferi-las.
O painel usa `st.navigation` e `st.metric(border=True)`, então evite fixar uma versão muito
antiga do Streamlit (validado com a 1.67).

## Estrutura

```text
src/apresentacao/
├── app.py             # entrada, navegação e aviso de mock
├── config.py          # variáveis de ambiente
├── contrato.py        # tipos e interfaces FonteAnalises e FonteAdministracao
├── tema.py            # rótulos, ícones e cores de cada sentimento
├── transformacoes.py  # cálculos e validações sem Streamlit (fáceis de testar)
├── componentes.py     # componentes reutilizáveis
├── fontes/            # de onde vêm os dados: mock ou API, análises e administração
├── secoes/            # uma seção do dashboard por arquivo (filtros, indicadores...)
└── paginas/           # uma tela por arquivo; só compõe as seções
```

Cada seção nova do dashboard (gráfico, listagem, resumo) ganha um arquivo em `secoes/` e recebe
os filtros aplicados por `secoes/filtros.py`. Assim, duas pessoas trabalham em seções diferentes
sem conflito.

## Convenções

- **Código e textos em português**, como no restante do projeto; PEP 8 e type hints.
- **Telas não acessam dados diretamente:** recebem uma `FonteAnalises`. Erros chegam como
  `ErroFonteDados` e são exibidos com `estado_erro`.
- **Filtros são aplicados pela fonte de dados**, nunca nas telas. A remissão herdada à Arquitetura 2.4.1 não foi conferida no documento completo.
- **Cálculos ficam em `transformacoes.py`**, com testes.
- **Estado:** use `st.session_state` só quando precisar manter algo entre interações.
- **Formulários:** use `st.form` para agrupar campos enviados por um botão, como "Aplicar
  filtros". Valide a entrada antes de chamar a fonte.
- **Estilo:** prefira recursos nativos e `.streamlit/config.toml`. CSS injetado é frágil e
  deve ser exceção justificada.
- **Linguagem:** apresente o sentimento como previsão do modelo. Não invente datas.

## Testes

Teste comportamento que o usuário percebe e regras de dados: filtros, cálculos, estados de
carregamento, vazio e erro. Use `AppTest` para telas (`tests/test_painel_ui.py`). Não teste
marcação estática nem detalhes internos. Não há meta numérica de cobertura para o frontend.

## Changelog

O [CHANGELOG.md](../../CHANGELOG.md) é mantido manualmente, sem ferramenta de release.

- **Quando:** no mesmo PR de qualquer mudança perceptível ao usuário ou à equipe. Refatorações
  internas e ajustes de teste não precisam de entrada.
- **Como:** adicione em `[Não lançado]`, na categoria certa (Adicionado, Alterado, Corrigido,
  Removido). Descreva o resultado, não o arquivo, e cite a issue:
  `Filtro por sentimento no dashboard, com dados de exemplo (#14).`
- **Honestidade:** deixe claro quando algo usa dados de exemplo. Nunca registre o que não foi
  entregue nem crie versões ou datas por conta própria; versões dependem de decisão da equipe.
- **Rascunho:** os commits já costumam seguir o formato `tipo(escopo): descrição`
  (`feat`, `fix`, `docs`, `test`, `chore`). Mantenha esse formato e liste os candidatos assim:

  ```bash
  git log --no-merges --format='- %s (%h)' origin/developer..HEAD -- src/apresentacao tests docs/frontend
  ```

  O resultado é só um rascunho: reescreva em linguagem de usuário antes de registrar.

## Fluxo de trabalho

Crie branches a partir de `developer` (`feat/...`, `fix/...`, `docs/...`) e abra o PR para
`developer`. Uma tarefa só está pronta com testes aprovados, CI sem falhas,
PR revisado, aceite da PO e documentação atualizada, conforme a DoD das issues.
O Documento de Visão completo ainda precisa ser disponibilizado. Para esta revisão
documental, a base é a integração PC1 selecionada, não a developer.

## Interface implementada versus backend efetivamente implementado

| Operação | Interface #70 nesta referência | Backend em `src/servico/main.py` |
|---|---|---|
| Dashboard e indicadores | Mock com total/percentuais e filtros aplicáveis | Sem `/analises` ou `/analises/resumo` |
| Filtro de período | Publicação, limites inclusivos, abertos; datas desconhecidas excluídas com aviso | #24 pendente; escolha definitiva da data/fuso requer aceite |
| Login e administração | Fluxo de exemplo; credenciais fictícias | Sem autenticação, autorização ou emissão de token |
| Importação | Lê bytes UTF-8/CSV e conta válidos/descartes no mock | Sem `POST /datasets` e sem persistência |
| Coleta | Inicia estado de exemplo e conclui ao atualizar | Sem rotas de coleta e sem inferência iniciada pelo painel |
| Sessão/logout | Sessão em `st.session_state`; expiração e retorno ao login | Sem sessão/revogação no servidor |
| Saúde | Pode ser consultada separadamente | `GET /health` implementado |

O menu mostra Dashboard e Entrar sem sessão; depois do login, Administração
substitui Entrar no mesmo caminho `/administracao`. A sessão mock dura uma hora.
Sair limpa sessão/coleta locais mesmo se o logout HTTP falhar. `st.session_state`
é estado da sessão Streamlit no servidor, não armazenamento persistente do navegador.

**Importação e coleta de exemplo não persistem nem classificam dados reais.**
O parser administrativo é simplificado e não chama o importador do processamento.
`dataset_exemplo` é uma fonte fixa; uma coleta concluída não analisa o arquivo
recém-enviado nem atualiza os indicadores do dashboard.

Estados tratados: período invertido mantém os filtros anteriores; Limpar restaura
a seleção; sem resultados mostra estado vazio; configuração inválida, timeout,
rede, 404 e contrato inválido mostram mensagens. Credenciais inválidas não liberam
administração; sessão expirada volta ao login. No modo API, o backend atual retorna
404 nas rotas propostas e o painel não apresenta mocks como resposta real.

Testes existentes: [filtros](../../tests/test_painel_filtros.py),
[administração](../../tests/test_painel_administracao.py),
[UI](../../tests/test_painel_ui.py), [fonte mock](../../tests/test_painel_fonte_mock.py),
[cliente HTTP](../../tests/test_painel_fonte_api.py),
[configuração](../../tests/test_painel_config.py),
[transformações](../../tests/test_painel_transformacoes.py) e
[arquitetura](../../tests/test_painel_arquitetura.py). O cabeçalho do teste de administração no #70 original citava
`tests/test_api_administracao.py`, ausente. A correção de ensaio `eb071a0` removeu
a referência; os testes existentes continuam sendo mock, sem integração administrativa.

Resultados, escopo de AppTest e limites visuais no
[relatório de validação](../qa/pc1/VALIDACAO_FRONTEND_CLICIA.md).
