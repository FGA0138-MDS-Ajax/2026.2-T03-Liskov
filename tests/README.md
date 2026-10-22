# Suíte de Testes — Aquisição e Importação de Dados (Issue #4)

Esta suíte implementa os testes automatizados da **Sprint 1** referentes à **Issue #4** (*[Testes] Validar aquisição e importação de dados*), dando suporte direto aos requisitos:

- **RF02 / US02 (Issue #1):** Módulo de aquisição de textos e metadados (corpus inicial *TweetSentBR*).
- **RF01 / US01 (Issue #2):** Rotina de importação de datasets em formato CSV.

> **Nota importante de escopo (T01 / T02):**
> Os testes contidos em `tests/test_aquisicao.py` e `tests/test_importacao.py` são **testes unitários e de contrato** das rotinas Python de leitura, aquisição e importação de dados em lote. Eles **não substituem** os casos de teste completos de ponta a ponta **T01 e T02 da interface administrativa**, os quais exigirão os componentes de API (FastAPI), persistência (MongoDB) e interface (Streamlit) previstos para sprints futuras.

---

## 1. Instalação das Dependências

Recomenda-se utilizar um ambiente virtual Python (`.venv`) na raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

---

## 2. Como Executar os Testes

Com o ambiente virtual ativado, execute na raiz do projeto:

```bash
# Execução detalhada listando cada caso de teste
python -m pytest -v

# Execução exibindo o resumo completo de testes bloqueados/pulados e motivos (-ra)
python -m pytest -ra
```

Toda a suíte foi projetada para executar **100% offline** (sem dependência de internet ou serviços externos), utilizando fixtures locais controladas em `tests/fixtures/` e arquivos temporários isolados via `tmp_path`.

---

## 3. Estrutura de Arquivos

```text
tests/
├── README.md
├── conftest.py
├── fixtures/
│   ├── dataset_valido.csv
│   ├── dataset_vazio.csv
│   └── dataset_invalido.csv
├── test_aquisicao.py
└── test_importacao.py
```

---

## 4. Cenários Cobertos

### 4.1. Aquisição de Dados (`tests/test_aquisicao.py` — RF02 / US02 / Issue #1)

| Teste | Cenário Coberto | Tipo |
| --- | --- | --- |
| `test_aquisicao_leitura_fonte_inicial_sucesso` | Leitura bem-sucedida da fonte inicial controlada (*TweetSentBR*) | Positivo |
| `test_aquisicao_preservacao_textos_e_metadados` | Preservação integral dos textos originais em PT-BR e metadados (`id`, `fonte`, `sentimento`, `data`) | Positivo |
| `test_aquisicao_fonte_ou_arquivo_inexistente` *(3 parâmetros)* | Caminho local, subdiretório ou arquivo inexistente | Negativo |
| `test_aquisicao_fonte_indisponivel_diretorio_no_lugar_de_arquivo` | Fonte indisponível (caminho aponta para diretório em vez de arquivo) | Negativo |
| `test_aquisicao_fonte_indisponivel_erro_permissao_leitura` | Fonte indisponível simulada localmente via falha de permissão (`PermissionError`) | Negativo |
| `test_aquisicao_entrada_sem_registros_validos` *(3 parâmetros)* | Arquivo de 0 bytes, apenas cabeçalho ou apenas registros em branco | Negativo |
| `test_aquisicao_tratamento_erros_previsiveis_parametros_invalidos` *(3 parâmetros)* | Parâmetros de origem inválidos (`None`, `""`, `"   "`) | Negativo |
| `test_aquisicao_tratamento_erros_previsiveis_esquema_incompativel` | Fonte com estrutura incompatível sem campo `texto` | Negativo |

### 4.2. Importação de Dados CSV (`tests/test_importacao.py` — RF01 / US01 / Issue #2)

| Teste | Cenário Coberto | Tipo |
| --- | --- | --- |
| `test_importacao_csv_valido_sucesso` | Importação de `dataset_valido.csv` para estrutura padronizada (`list[dict]`) | Positivo |
| `test_importacao_csv_preservacao_campos_minimos_e_metadados` | Preservação de `id`/`identificador`, `texto`, `fonte`, `sentimento` e `data` (presente ou ausente) | Positivo |
| `test_importacao_csv_caracteres_brasileiros` *(5 parâmetros)* | Preservação de caracteres do português brasileiro (`ç`, `ã`, `é`, `í`, etc.) em UTF-8 | Positivo |
| `test_importacao_fixture_valida_contem_todos_caracteres_brasileiros_obrigatorios` | Validação conjunta de `ç`, `ã`, `é` e `í` em `dataset_valido.csv` | Positivo |
| `test_importacao_csv_vazio_ou_sem_registros` *(3 parâmetros)* | Rejeição de CSV de 0 bytes, apenas cabeçalho ou apenas linhas com espaços | Negativo |
| `test_importacao_csv_colunas_obrigatorias_ausentes` *(3 parâmetros)* | Rejeição de CSV sem coluna obrigatória `texto` ou cabeçalhos fora do contrato | Negativo |
| `test_importacao_fixture_dataset_invalido_rejeitado` | Rejeição da fixture `dataset_invalido.csv` com mensagem clara | Negativo |
| `test_importacao_csv_estrutura_ou_formato_invalido` *(3 parâmetros)* | Rejeição de conteúdo JSON renomeado, binário corrompido ou CSV com aspas/colunas quebradas | Negativo |

---

## 5. Dependências das Issues #1 e #2 e Contrato Proposto

Atualmente, os módulos de produção das **Issues #1 e #2** ainda não estão presentes na branch `developer`. Para não inventar implementações de produção nem utilizar mocks artificiais que mascaram o estado real do projeto, `tests/conftest.py` tenta localizar dinamicamente as funções reais e, enquanto ausentes, marca os testes como **BLOQUEADOS (`SKIPPED`)** com justificativa rastreável.

### Decisões técnicas a validar com Breno (Responsável pelas Issues #1 e #2)

1. **Localização e nome dos módulos/funções:**
   - **Aquisição (Issue #1):** `src/aquisicao.py` (ou `sentia/aquisicao.py`) expondo `adquirir_dados(origem, fonte="TweetSentBR")` (o resolvedor também aceita `carregar_tweetsentbr`, `adquirir_textos` ou `obter_textos`).
   - **Importação (Issue #2):** `src/importacao.py` (ou `sentia/importacao.py`) expondo `importar_csv(caminho_arquivo, encoding="utf-8")` (o resolvedor também aceita `carregar_csv` ou `importar_dataset_csv`).
2. **Formato de retorno padronizado:**
   - Lista de dicionários (`list[dict[str, Any]]`), contendo chaves padronizadas:
     - `"id"` (ou `"identificador"`): identificador do registro (`str | int`).
     - `"texto"`: texto bruto preservado (`str`).
     - `"fonte"`: origem do registro (`str`, ex.: `"TweetSentBR"`).
     - `"sentimento"`: rótulo quando disponível (`"positivo"`, `"negativo"`, `"neutro"`).
     - `"data"`: string de data quando disponível ou `None`/`""` quando ausente na fonte.
3. **Política de tratamento de erros (Exceções):**
   - Arquivo inexistente: `FileNotFoundError` (ou `ValueError` com mensagem descritiva).
   - CSV vazio, apenas cabeçalho, registros com `texto` em branco, colunas obrigatórias ausentes ou estrutura malformada: `ValueError` com mensagem clara.
   - Falha de leitura/permissão da fonte: `OSError` / `PermissionError` / `RuntimeError` / `ValueError` com mensagem explícita.

---

## 6. Limitações Conhecidas

1. **Execução bloqueada até entrega das Issues #1 e #2:** Os 26 casos de teste permanecem registrados como `SKIPPED (BLOQUEADO)` até que os módulos de aquisição e importação sejam implementados e integrados.
2. **Escopo restrito à camada de dados (Sprint 1):** Não cobre upload via interface web (Streamlit) nem endpoints HTTP (FastAPI), que compõem os testes de sistema T01/T02 em sprints posteriores.
3. **Formato real do corpus TweetSentBR:** A fixture `dataset_valido.csv` adota o esquema tabular padronizado proposto; caso o arquivo bruto do TweetSentBR inspecionado na Issue #3 utilize separador ou codificação de classes diferente (ex.: `1`, `0`, `-1`), o adaptador da Issue #1 deverá normalizá-lo para o contrato esperado.

