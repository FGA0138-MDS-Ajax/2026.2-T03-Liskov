# Frontend do SentIA

Painel em **Streamlit** (`src/apresentacao/`), conforme o Documento de Arquitetura. A
interface acessa o sistema **somente pela API** e nunca importa banco ou processamento;
`tests/test_painel_arquitetura.py` verifica essa regra.

- Contrato com o backend: [CONTRATO-API.md](CONTRATO-API.md)
- Mudanças entregues: [CHANGELOG.md](../../CHANGELOG.md)

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

Sem `make` (por exemplo, no Windows):

```bash
uv sync --locked
cp .env.frontend.example .env                 # Windows: copy .env.frontend.example .env
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
| Instalar também o BERTweet real (download grande) | `uv sync --group ml` ou `make setup-ml` |

## Modos de dados

| Variável | Valores | Uso |
|---|---|---|
| `SENTIA_FONTE_DADOS` | `mock`, `api` | Dados de exemplo ou API real |
| `SENTIA_MOCK_CENARIO` | `normal`, `vazio`, `erro` | Valida os estados da tela sem backend |
| `SENTIA_API_URL` | URL | Endereço da API |
| `SENTIA_API_TIMEOUT_SEGUNDOS` | número | Tempo máximo de espera |

No modo `mock`, todas as telas exibem o aviso **"Dados de exemplo"**. Não remova esse
aviso: mock não é integração concluída. O modo `api` ainda mostra erro porque as rotas de
análises não existem (ver contrato).

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
├── contrato.py        # tipos de dados e a interface FonteAnalises
├── tema.py            # rótulos, ícones e cores de cada sentimento
├── transformacoes.py  # cálculos sem Streamlit (fáceis de testar)
├── componentes.py     # componentes reutilizáveis
├── fontes/            # mock.py e api.py: de onde vêm os dados
└── paginas/           # uma tela por arquivo
```

## Convenções

- **Código e textos em português**, como no restante do projeto; PEP 8 e type hints.
- **Telas não acessam dados diretamente:** recebem uma `FonteAnalises`. Erros chegam como
  `ErroFonteDados` e são exibidos com `estado_erro`.
- **Filtros são aplicados pela fonte de dados**, nunca nas telas (Arquitetura 2.4.1).
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
PR revisado, aceite da PO e documentação atualizada (Documento de Visão, seção 3).
