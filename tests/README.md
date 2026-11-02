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
| `test_importacao_csv_preservacao_campos_minimos_e_metadados` | Preservação de `id_origem`, `texto_original`, `fonte`, `rotulo_original`, `rotulo_padronizado` (`POS`/`NEG`/`NEU`) e `data_publicacao` | Positivo |
| `test_importacao_csv_campos_id_rotulo_e_data_opcionais` | Importação de CSV contendo apenas `texto` e `fonte`, com `id`, rótulo e data opcionais | Positivo |
| `test_importacao_conversao_fronteira_rotulo_para_avaliacao_e_mongodb` | Conversão explícita de `POS/NEG/NEU` para `positivo/negativo/neutro` na fronteira | Positivo |
| `test_importacao_csv_caracteres_brasileiros` *(5 parâmetros)* | Preservação de caracteres do português brasileiro (`ç`, `ã`, `é`, `í`, etc.) em UTF-8 | Positivo |
| `test_importacao_fixture_valida_contem_todos_caracteres_brasileiros_obrigatorios` | Validação conjunta de `ç`, `ã`, `é` e `í` em `dataset_valido.csv` | Positivo |
| `test_importacao_csv_vazio_ou_sem_registros` *(3 parâmetros)* | Rejeição de CSV de 0 bytes, apenas cabeçalho ou apenas linhas com espaços | Negativo |
| `test_importacao_csv_colunas_obrigatorias_ausentes` *(3 parâmetros)* | Rejeição de CSV sem coluna obrigatória `texto` ou cabeçalhos fora do contrato | Negativo |
| `test_importacao_fixture_dataset_invalido_rejeitado` | Rejeição da fixture `dataset_invalido.csv` com mensagem clara | Negativo |
| `test_importacao_csv_estrutura_ou_formato_invalido` *(3 parâmetros)* | Rejeição de conteúdo JSON renomeado, binário corrompido ou CSV com aspas/colunas quebradas | Negativo |

---

## 5. Contrato Homologado (Issues #2, #4, #11 e #19) e Estado das Dependências

1. **Localização e nome dos módulos/funções:**
   - **Importação CSV e BPSAD (Issue #2 — Implementado):** `src.processamento.aquisicao` expondo `importar_csv` / `importar_dataset_csv`, `iterar_csv` / `iterar_dataset_csv`, `iterar_bpsad`, `normalizar_rotulo` e `converter_rotulo_para_sentia`.
   - **Aquisição externa / corpus TweetSentBR (Issue #1 — Pendente):** `src.processamento.aquisicao` expondo `adquirir_dados` / `carregar_tweetsentbr`. Enquanto a rotina específica da Issue #1 não está implementada, os 14 casos de `tests/test_aquisicao.py` permanecem legitimamente como `SKIPPED (BLOQUEADO [Issue #1 / RF02])`.
2. **Formato de retorno padronizado:**
   - Lista de dicionários (`list[dict[str, Any]]`), contendo chaves padronizadas:
     - `"id_origem"`: identificador estável do registro (`str`, preservado da origem ou determinístico).
     - `"texto_original"`: texto bruto preservado (`str`).
     - `"fonte"`: origem do registro (`str`, ex.: `"TweetSentBR"`).
     - `"rotulo_original"`: valor original do rótulo no dataset (`str`) ou `None` quando não rotulado.
     - `"rotulo_padronizado"`: `"POS"`, `"NEG"`, `"NEU"` ou `None` quando não rotulado.
     - `"data_publicacao"`: string de data quando disponível ou `None` quando ausente na fonte.
     - `"metadados"` (opcional): dicionário com colunas adicionais não vazias.
     - O campo `"sentimento"` **não** é criado na aquisição/importação (reservado à previsão do classificador ML).
   - Na fronteira com avaliação ML e persistência MongoDB, utiliza-se `converter_rotulo_para_sentia()` para converter `POS/NEG/NEU` em `positivo/negativo/neutro`.

---

## 6. Limitações Conhecidas

1. **Execução bloqueada até entrega das Issues #1 e #2:** Os 26 casos de teste permanecem registrados como `SKIPPED (BLOQUEADO)` até que os módulos de aquisição e importação sejam implementados e integrados.
2. **Escopo restrito à camada de dados (Sprint 1):** Não cobre upload via interface web (Streamlit) nem endpoints HTTP (FastAPI), que compõem os testes de sistema T01/T02 em sprints posteriores.
3. **Formato real do corpus TweetSentBR:** A fixture `dataset_valido.csv` adota o esquema tabular padronizado proposto; caso o arquivo bruto do TweetSentBR inspecionado na Issue #3 utilize separador ou codificação de classes diferente (ex.: `1`, `0`, `-1`), o adaptador da Issue #1 deverá normalizá-lo para o contrato esperado.

