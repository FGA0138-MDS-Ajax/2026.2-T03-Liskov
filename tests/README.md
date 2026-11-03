# Suíte de Testes — Aquisição, Importação e Auditoria de Dados (Issue #4)

Esta suíte implementa os testes automatizados da **Sprint 1** referentes à **Issue #4** (*[Testes] Validar aquisição e importação de dados*), validando os requisitos:

- **RF02 / US02 (Issue #1):** Módulo de aquisição automatizada de textos e metadados do corpus inicial (*TweetSentBR*) em [`src/processamento/aquisicao/tweetsentbr.py`](../src/processamento/aquisicao/tweetsentbr.py).
- **RF01 / US01 (Issue #2):** Rotina de importação de datasets em formato CSV ([`src/processamento/aquisicao/csv_importer.py`](../src/processamento/aquisicao/csv_importer.py)) e adaptador BPSAD ([`src/processamento/aquisicao/bpsad_adapter.py`](../src/processamento/aquisicao/bpsad_adapter.py)).
- **Auditoria de Datasets (Issue #3):** Inspeção programática reprodutível de datasets ([`src/processamento/aquisicao/auditoria_datasets.py`](../src/processamento/aquisicao/auditoria_datasets.py)).

> **Nota importante de escopo (T01 / T02):**
> Os testes contidos em `tests/` validam o contrato, as regras de negócio e o tratamento de erros da camada Python de aquisição e importação de dados em lote. Eles **não substituem** os testes integrados de ponta a ponta **T01 e T02 da interface administrativa**, que dependem da integração com API (FastAPI), persistência (MongoDB) e interface (Streamlit) previstas para sprints posteriores.

---

## 1. Instalação das Dependências

Recomenda-se utilizar um ambiente virtual Python (`.venv`) na raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Como Executar os Testes e a Cobertura

Com o ambiente virtual ativado, execute na raiz do projeto:

```bash
# Suíte de aquisição (Issue #1 / RF02)
python -m pytest tests/test_aquisicao.py -v -ra

# Suítes de importação CSV e BPSAD (Issue #2 / RF01)
python -m pytest tests/test_importacao.py -v -ra
python -m pytest tests/test_csv_importer.py -v -ra

# Suíte de auditoria reprodutível de datasets (Issue #3)
python -m pytest tests/test_auditoria_datasets.py -v -ra

# Execução completa com relatório de cobertura por módulo
python -m pytest -v -ra --cov=src --cov-report=term-missing
```

Toda a suíte executa **100% offline** (sem dependência de rede ou serviços externos), utilizando fixtures locais controladas em `tests/fixtures/` e arquivos temporários via `tmp_path`.

---

## 3. Estrutura de Arquivos

```text
tests/
├── README.md
├── conftest.py
├── fixtures/
│   ├── bpsad_sample.csv
│   ├── dataset_invalido.csv
│   ├── dataset_valido.csv
│   └── dataset_vazio.csv
├── test_api.py
├── test_aquisicao.py
├── test_auditoria_datasets.py
├── test_csv_importer.py
└── test_importacao.py
```

---

## 4. Cenários Cobertos

### 4.1. Aquisição de Dados (`tests/test_aquisicao.py` — RF02 / US02 / Issue #1) — 25 casos

| Teste | Cenário Coberto | Tipo |
| --- | --- | --- |
| `test_aquisicao_leitura_fonte_inicial_sucesso` | Leitura bem-sucedida da fonte inicial controlada (*TweetSentBR*) | Positivo |
| `test_aquisicao_preservacao_textos_e_metadados` | Preservação integral dos textos originais em PT-BR e metadados (`id_origem`, `fonte`, `rotulo_padronizado`, `data_publicacao`) | Positivo |
| `test_aquisicao_fonte_ou_arquivo_inexistente` *(3 parâmetros)* | Caminho local, subdiretório ou arquivo inexistente | Negativo |
| `test_aquisicao_fonte_indisponivel_diretorio_no_lugar_de_arquivo` | Fonte indisponível (caminho aponta para diretório em vez de arquivo) | Negativo |
| `test_aquisicao_fonte_indisponivel_erro_permissao_leitura` | Fonte indisponível simulada localmente via falha de permissão (`PermissionError`) | Negativo |
| `test_aquisicao_entrada_sem_registros_validos` *(3 parâmetros)* | Arquivo de 0 bytes, apenas cabeçalho ou apenas registros em branco | Negativo |
| `test_aquisicao_tratamento_erros_previsiveis_parametros_invalidos` *(3 parâmetros)* | Parâmetros de origem inválidos (`None`, `""`, `"   "`) | Negativo |
| `test_aquisicao_tratamento_erros_previsiveis_esquema_incompativel` | Fonte com estrutura incompatível sem campo `texto` | Negativo |
| `test_aquisicao_caminho_padrao_independente_do_diretorio_atual` | Resolução do caminho padrão (`Datasets/tweetsent.csv`) fora do diretório raiz do projeto | Positivo |
| `test_aquisicao_processamento_iterativo_e_limite` | Leitura iterativa em streaming (`iterar_tweetsentbr`) com parâmetro `limite` | Positivo |
| `test_aquisicao_rejeita_limite_invalido` *(4 parâmetros)* | Rejeição de `limite` inválido (`0`, negativo, booleano, string) | Negativo |
| `test_aquisicao_rejeita_tipo_caminho_invalido` | Rejeição de caminho com tipo não textual (`TypeError`) | Negativo |
| `test_aquisicao_rejeita_diretorio_relativo_a_raiz` | Rejeição de caminho relativo que aponta para diretório na raiz (`IsADirectoryError`) | Negativo |
| `test_aquisicao_preserva_acentuacao_emojis_estabilidade_id_e_rotulos` | Preservação de acentuação PT-BR, emojis, determinismo de `id_origem` e contrato `POS/NEG/NEU` | Positivo |
| `test_aquisicao_erro_encoding_invalido` | Mensagem clara ao tentar ler arquivo fora do padrão UTF-8 | Negativo |
| `test_aquisicao_amostra_sintetica_bpsad` | Carregamento e normalização da fixture sintética `bpsad_sample.csv` | Positivo |

### 4.2. Importação de Dados CSV e BPSAD (`tests/test_importacao.py` — 20 casos; `tests/test_csv_importer.py` — 96 casos)

Cobre integralmente o contrato da Issue #2 (RF01/US01):
- Normalização de rótulos para `POS`, `NEG` e `NEU` em `normalizar_rotulo()` e conversão explícita via `converter_rotulo_para_sentia()`.
- Preservação de `id_origem` original ou geração determinística baseada em SHA-256 e posição por fonte.
- Suporte a datasets não rotulados (`rotulo_original = None`, `rotulo_padronizado = None`) sem criar o campo `sentimento`.
- Modo estrito (`modo_estrito=True`) e modo tolerante (`modo_estrito=False`) com `RelatorioImportacao`.
- Adaptador BPSAD (`iterar_bpsad`) em streaming.

### 4.3. Auditoria Reprodutível de Datasets (`tests/test_auditoria_datasets.py` — 3 casos)

Valida o cálculo de hash SHA-256, codificação, contagem por classe, detecção de duplicatas exatas/normalizadas e identificação de rótulos conflitantes em `Datasets/tweetsent.csv` e `tests/fixtures/bpsad_sample.csv`.

---

## 5. Contrato Homologado (Issues #1, #2, #3, #4, #11 e #19)

1. **Módulo `src.processamento.aquisicao`:**
   - **Aquisição (Issue #1):** `adquirir_dados`, `carregar_tweetsentbr`, `iterar_tweetsentbr`, `iterar_dados_aquisicao`, `resolver_caminho_tweetsentbr`, `CAMINHO_PADRAO_TWEETSENTBR`.
   - **Importação CSV e BPSAD (Issue #2):** `importar_csv`, `importar_dataset_csv`, `iterar_csv`, `iterar_dataset_csv`, `iterar_bpsad`, `normalizar_rotulo`, `converter_rotulo_para_sentia`, `RelatorioImportacao`.
   - **Auditoria (Issue #3):** `auditar_dataset_csv`, `calcular_sha256_arquivo`, `detectar_codificacao_utf8`, `RelatorioAuditoriaDataset`, `ResumoDuplicatas`.
2. **Estrutura de cada registro retornado (`dict[str, Any]`):**
   - `"id_origem"`: `str` estável (preservado da origem ou determinístico).
   - `"texto_original"`: `str` com o texto bruto preservado.
   - `"fonte"`: `str` identificando a origem (ex.: `"TweetSentBR"`, `"b2w"`).
   - `"rotulo_original"`: `str | None` (valor bruto do dataset ou `None` quando não rotulado).
   - `"rotulo_padronizado"`: `"POS" | "NEG" | "NEU" | None`.
   - `"data_publicacao"`: `str | None`.
   - `"metadados"`: `dict[str, str]` opcional quando houver colunas extras preenchidas.
   - O campo `"sentimento"` **não** é criado na aquisição/importação (reservado à saída do classificador ML).
