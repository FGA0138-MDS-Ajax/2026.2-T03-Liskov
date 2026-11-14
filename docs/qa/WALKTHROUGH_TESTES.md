# Walkthrough Técnico dos Testes — SentIA

**Referência auditada:** `origin/developer` (`fe83ad0`)  
**Escopo:** Mapeamento técnico completo da suíte automatizada (`tests/test_*.py`), configuração de CI (`.github/workflows/ci.yml`), alvos do `Makefile`, contratos de dados (`docs/contratos-dados.md`), roteiros de verificação manual e estado atual de evidências para homologação.

---

## Sumário

1. [Visão Geral: Quais Testes Existem e Quais Requisitos/Issues Cobrem](#1-visão-geral-quais-testes-existem-e-quais-requisitosissues-cobrem)
2. [Preparação do Ambiente e Execução por Grupo](#2-preparação-do-ambiente-e-execução-por-grupo)
3. [O Que Cada Arquivo de Teste Verifica (Com Exemplos Reais do Código)](#3-o-que-cada-arquivo-de-teste-verifica-com-exemplos-reais-do-código)
4. [Classificação Metodológica: Unitário, Contrato, Integração Simulada e Integração Real](#4-classificação-metodológica-unitário-contrato-integração-simulada-e-integração-real)
5. [Como Testar Manualmente: FastAPI, MongoDB e Dashboard](#5-como-testar-manualmente-fastapi-mongodb-e-dashboard)
6. [Testes Ignorados (`SKIPPED`) e Como Executá-los com Segurança](#6-testes-ignorados-skipped-e-como-executá-los-com-segurança)
7. [Evidências Existentes e Lacunas para Homologação (#19 e #22)](#7-evidências-existentes-e-lacunas-para-homologação-19-e-22)

---

## 1. Visão Geral: Quais Testes Existem e Quais Requisitos/Issues Cobrem

Na referência `origin/developer` (`fe83ad0`), o repositório possui **26 arquivos de teste** em `tests/`, contendo **331 funções `def test_*`** que, expandidas por `@pytest.mark.parametrize`, totalizam **715 itens coletados pelo Pytest** (`707 passed` e `8 skipped` em execução offline sem instância local de MongoDB ativa).

> **Nota sobre números históricos:** O valor antigo de `538 passed` citado em roteiros anteriores da PC1 referia-se a uma fotografia prévia do repositório (antes da entrada dos testes de persistência real/unitária em `tests/test_repositorio.py`, dos endpoints `POST /analises` e `GET /analises*` em `tests/test_api.py` e `tests/test_consultas_api.py`, da API de Administração em `tests/test_api_administracao.py` e da atualização de `tests/test_qa_t09_t10.py`). Os números vigentes em `fe83ad0` são **715 itens coletados (`707 passed, 8 skipped`)**.

### 1.1. Matriz de Rastreabilidade (Arquivos × Funções × Itens × Requisitos × Issues)

| Camada | Arquivo de Teste | `def test_*` | Itens Pytest | Requisitos / Casos de Teste | Issues Relacionadas | Escopo Principal |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Aquisição** | `tests/test_aquisicao.py` | 16 | 25 | RF01, RF02, RF03, RF04, T01, T02 | `#1`, `#2`, `#4`, `#5`, `#18` | Adaptadores TweetSentBR e BPSAD, mapeamento de rótulos (`0/1/-1`, `pos/neg/neu`) e contrato de saída de aquisição |
| **Aquisição** | `tests/test_csv_importer.py` | 41 | 96 | RF01, RF02, RF03, RF04, T01, T02, T03 | `#1`, `#2`, `#6`, `#18`, `#58` | `CSVImporter` genérico, dialetos/delimitadores, datas ISO-8601, rejeição de colunas ausentes, vazios e binários |
| **Aquisição** | `tests/test_importacao.py` | 10 | 20 | RF01, RF02, RF03, T01, T02 | `#1`, `#2`, `#6` | Função utilitária `importar_csv`, normalização de nomes de coluna e geração determinística de `id` |
| **Aquisição** | `tests/test_xfetch.py` | 29 | 58 | RF01, RF03, RF04, RNF01 | `#3`, `#18`, `#59`, `#60` | Cliente `XFetchClient`, paginação com `next_token`, deduplicação, validação de `XFETCH_API_KEY`, erros HTTP sem retry/vazamento |
| **Aquisição** | `tests/test_auditoria_datasets.py` | 3 | 3 | RF01, RF02 | `#4`, `#5`, `#6` | Auditoria estrutural de datasets locais (TweetSentBR e BPSAD), contagens de nulos, duplicados e distribuição de rótulos |
| **Aquisição / ML** | `tests/test_experimentos_bpsad.py` | 9 | 14 | RF01, RF05, RF08 | `#5`, `#8`, `#10` | Amostragem estratificada determinística por `seed` do corpus BPSAD e proteção contra sobrescrita via CLI |
| **ML / Classificação** | `tests/test_classificacao.py` | 11 | 14 | RF05, RF06, RF07, T04, T05, T06, T07 | `#7`, `#8`, `#9` | `ClassificadorBaseline` (TF-IDF + Regressão Logística), `ClassificadorBERTweet`, normalização de rótulos e validação de entradas vazias |
| **ML / Avaliação** | `tests/test_avaliacao.py` | 3 | 16 | RF08 | `#8`, `#9`, `#10` | Cálculo de métricas (`acuracia`, `f1_macro`, precisão, revocação e suporte por classe) |
| **ML / Avaliação** | `tests/test_comparar_modelos.py` | 2 | 5 | RF05, RF08 | `#8`, `#9`, `#10` | Comparação experimental entre Baseline e BERTweet e geração de relatório Markdown |
| **Pipeline** | `tests/test_pipeline.py` | 14 | 19 | RF03, RF04, RF05, RF06, RF07, RF09 | `#7`, `#17`, `#19` | `PipelineClassificacao`, documento canônico de análise, preservando texto original e metadados do modelo |
| **Pipeline / Contrato** | `tests/test_integracao_conjunta.py` | 6 | 10 | RF01–RF09, T01–T08 | `#17`, `#18`, `#19` | Fluxo em memória `Importação CSV -> PipelineClassificacao -> BSON` sem serviços externos |
| **Pipeline / XFetch** | `tests/test_xfetch_pipeline.py` | 2 | 3 | RF01, RF05–RF09 | `#3`, `#17`, `#19`, `#60` | Fluxo em memória `XFetch paginado -> PipelineClassificacao -> BSON` e atomicidade em falha de página |
| **Banco (MongoDB)** | `tests/test_database.py` | 16 | 35 | RF09, RF10 | `#11`, `#12`, `#13`, `#14` | `GerenciadorMongoDB`, leitura de `MONGODB_URI`/`MONGODB_DB_NAME`, ping de conexão, sanitização de credenciais em erros |
| **Banco (MongoDB)** | `tests/test_repositorio.py` | 21 | 41 | RF09, RF10, T08, T09 | `#11`, `#19`, `#20`, `#22` | `RepositorioAnalises`: validação de contrato, índices, deduplicação `(id_origem, fonte)` (13 funções offline + 8 funções em MongoDB real) |
| **API FastAPI** | `tests/test_api.py` | 9 | 17 | RF05–RF10, T09 | `#15`, `#16`, `#20`, `#21`, `#22` | `GET /health`, `POST /analises`, validação Pydantic (`422`), deduplicação e sanitização de falhas (`503`) |
| **API FastAPI** | `tests/test_consultas_api.py` | 10 | 48 | RF10, RF11, RF12, T10 | `#19`, `#22`, `#23`, `#24`, `#25` | `GET /analises` e `GET /analises/resumo`, filtros `inicio`, `fim`, `sentimento`, `fonte`, `limite`, e compatibilidade com `FonteApi` |
| **API Administração** | `tests/test_api_administracao.py` | 29 | 38 | RF01–RF04, RF13, RF14, RF15, RNF01 | `#15`, `#16`, `#21`, `#27`, `#61` | `/auth/login`, `/auth/logout`, bloqueio por força bruta, `/datasets`, `/coletas/fontes`, `/coletas` e integração com `AdministracaoApi` |
| **QA (T09 / T10)** | `tests/test_qa_t09_t10.py` | 11 | 19 | RF09, RF10, T09, T10 | `#15`, `#16`, `#19`, `#20`, `#21`, `#22`, `#23` | Suíte dedicada aos casos de teste de integração `T09` (persistência/deduplicação) e `T10` (endpoints da API e consultas) |
| **Painel Streamlit** | `tests/test_painel_arquitetura.py` | 1 | 18 | Arquitetura em camadas | `#27`, `#28` | Garante via AST que `src/apresentacao/` não importa `pymongo`, `fastapi`, `torch`, `transformers` nem `src.dados`/`src.servico`/`src.processamento` |
| **Painel Streamlit** | `tests/test_painel_config.py` | 2 | 12 | Configuração de apresentação | `#27`, `#28` | Validação de `SENTIA_FONTE_DADOS`, `SENTIA_API_URL`, `SENTIA_API_TIMEOUT`, `SENTIA_LIMITE_EXEMPLOS` e `SENTIA_MOCK_CENARIO` |
| **Painel Streamlit** | `tests/test_painel_transformacoes.py` | 4 | 11 | RF10, US14 | `#28` | Cálculo de percentuais inteiros que somam `100%` (maior resto) e formatação numérica |
| **Painel Streamlit** | `tests/test_painel_fonte_mock.py` | 7 | 7 | RF10, RF11, RF12 | `#28` | `FonteMock`, `FonteMockVazia` e `FonteMockComErro` com dados estáticos do contrato |
| **Painel Streamlit** | `tests/test_painel_fonte_api.py` | 17 | 92 | RF10, RF11, RF12, T10 | `#19`, `#25`, `#28` | Cliente `FonteApi`: serialização de filtros, validação estrita do JSON de `/analises` e `/analises/resumo` e tradução de erros HTTP |
| **Painel Streamlit** | `tests/test_painel_filtros.py` | 12 | 18 | RF11, RF12, US17, US18 | `#28` | Filtros combinados de período e sentimento nas funções puras e na interface Streamlit (`AppTest`) |
| **Painel Streamlit** | `tests/test_painel_ui.py` | 9 | 18 | RF10, RF11, RF12, US13–US20 | `#28` | Renderização do Dashboard via `AppTest`, métricas principais, gráficos, tabela de exemplos e estados vazio/erro |
| **Painel Streamlit** | `tests/test_painel_administracao.py` | 37 | 58 | RF13, RF14, RF15, RNF01, US01–US12 | `#27`, `#61` | Login administrativo, sessão expirada, upload CSV, disparo de coleta, histórico, mascaramento de `@menções` e cliente `AdministracaoApi` |
| **TOTAL** | **26 arquivos** | **331** | **715** | **RF01–RF15, RNF01, T01–T10** | **`#1`–`#25`, `#27`, `#28`, `#58`–`#61`** | **707 passed, 8 skipped (offline), 94% de cobertura em `src/`** |

---

## 2. Preparação do Ambiente e Execução por Grupo

> [!IMPORTANT]
> Todos os comandos abaixo devem ser executados **a partir da raiz do repositório** (`2026.2-T03-Liskov/`). O teste `test_cli_e_protecao_contra_sobrescrita` (`tests/test_experimentos_bpsad.py`) invoca `python -m scripts.experimentos.amostrar_bpsad` via subprocesso e depende de o diretório corrente ser a raiz do projeto.

### 2.1. Preparação do Ambiente (`Makefile` e `uv`)

O repositório utiliza Python `>=3.11,<3.13` gerenciado pelo `uv` e possui os seguintes alvos no `Makefile`:

```bash
# 1. Instalar dependências padrão + grupo dev (pytest, pytest-cov, ruff, httpx)
uv sync --locked
# Equivalente via Makefile:
make setup

# 2. (Opcional) Instalar dependências pesadas de ML (pysentimiento, torch, transformers, accelerate)
# Necessário apenas para inferência real do BERTweet fora de mocks:
uv sync --locked --group ml
# Equivalente via Makefile:
make setup-ml

# 3. Criar arquivo .env local a partir de .env.example (não sobrescreve se já existir)
make env

# 4. Verificar integridade do uv.lock (mesma checagem da CI)
uv lock --check
```

### 2.2. Verificação Estática (Lint)

Conforme `.github/workflows/ci.yml` e `Makefile`:

```bash
# Executa ambas as checagens de lint configuradas no projeto:
make lint

# Ou individualmente:
uv run ruff check src/apresentacao tests/test_painel_*.py
uv run ruff check --isolated --select F,E9 .
```

### 2.3. Execução da Suíte por Grupo Funcional

```bash
# Grupo 1 — Aquisição, Importação CSV, XFetch e Auditoria de Datasets (216 itens)
uv run pytest \
  tests/test_aquisicao.py \
  tests/test_csv_importer.py \
  tests/test_importacao.py \
  tests/test_xfetch.py \
  tests/test_auditoria_datasets.py \
  tests/test_experimentos_bpsad.py -ra

# Grupo 2 — Classificação ML, Avaliação e Pipeline em Memória (67 itens)
uv run pytest \
  tests/test_classificacao.py \
  tests/test_avaliacao.py \
  tests/test_comparar_modelos.py \
  tests/test_pipeline.py \
  tests/test_integracao_conjunta.py \
  tests/test_xfetch_pipeline.py -ra

# Grupo 3 — Persistência MongoDB (76 itens: 68 executados offline + 8 ignorados sem Mongo local)
uv run pytest \
  tests/test_database.py \
  tests/test_repositorio.py -ra

# Grupo 4 — API FastAPI, Administração e Casos de QA T09/T10 (122 itens)
uv run pytest \
  tests/test_api.py \
  tests/test_consultas_api.py \
  tests/test_api_administracao.py \
  tests/test_qa_t09_t10.py -ra

# Grupo 5 — Painel Streamlit (Dashboard Público e Administração) (234 itens)
uv run pytest tests/test_painel_*.py -ra
# Equivalente via Makefile:
make test-painel

# Suíte Completa com Relatório de Cobertura (715 itens)
uv run pytest -ra --cov=src --cov-report=term-missing
# Equivalente via Makefile (sem flag de cobertura):
make test
```

### 2.4. O Que Roda na CI (`.github/workflows/ci.yml`)

O workflow `CI` é disparado em `push` e `pull_request` para `main` e `developer` em `ubuntu-latest` com Python `3.11` e executa 5 passos sequenciais:

1. `uv sync --locked`
2. `uv lock --check`
3. `uv run ruff check src/apresentacao tests/test_painel_*.py`
4. `uv run ruff check --isolated --select F,E9 .`
5. `uv run pytest -ra`

> [!NOTE]
> O workflow da CI **não** sobe serviço `mongo` em `services:` nem instala o grupo opcional `--group ml`. Por isso, na CI os 8 testes de `tests/test_repositorio.py` que dependem de conexão real em `localhost:27017` ficam `SKIPPED`, e toda a inferência de testes roda com `ClassificadorBaseline` ou dublês (`StubClassificador` / `MagicMock`).

---

## 3. O Que Cada Arquivo de Teste Verifica (Com Exemplos Reais do Código)

Abaixo está o detalhamento técnico dos **26 arquivos de teste**, organizados por subsistema, com trechos reais do código-fonte de `tests/`.

---

### 3.1. Subsistema de Aquisição e Pré-Processamento (`src/processamento/aquisicao/`)

#### 3.1.1. `tests/test_aquisicao.py` (16 funções / 25 itens)
- **Requisitos e Issues:** RF01, RF02, RF03, RF04, T01, T02 | Issues `#1`, `#2`, `#4`, `#5`, `#18`.
- **O que verifica:**
  - Leitura dos datasets iniciais via `TweetSentBRAdapter` e `BPSADAdapter` (`carregar_tweetsentbr`, `carregar_bpsad`).
  - Mapeamento dos rótulos originais numéricos (`1 -> positivo`, `-1 -> negativo`, `0 -> neutro`) e textuais (`pos/neg/neu`) para o vocabulário canônico (`positivo`, `negativo`, `neutro`).
  - Preservação integral de `texto` com emojis, URLs, `@menções` e `#hashtags` (RF04).
  - Descarte de registros com texto vazio/espaços ou rótulo fora do domínio, sem interromper o lote válido.
- **Exemplo real do código (`tests/test_aquisicao.py`):**
```python
@pytest.mark.parametrize(
    ("rotulo_bruto", "esperado"),
    [
        ("1", "positivo"),
        ("0", "neutro"),
        ("-1", "negativo"),
        ("pos", "positivo"),
        ("NEG", "negativo"),
        ("Neutro", "neutro"),
    ],
)
def test_tweetsentbr_mapeia_rotulos_validos(tmp_path: Path, rotulo_bruto: str, esperado: str) -> None:
    arquivo = tmp_path / "tweetsentbr.csv"
    arquivo.write_text(f"id,text,label\n10,Texto de teste,{rotulo_bruto}\n", encoding="utf-8")

    registros = carregar_tweetsentbr(arquivo)

    assert len(registros) == 1
    assert registros[0]["rotulo_original"] == rotulo_bruto
    assert registros[0]["rotulo_padronizado"] == esperado
```

#### 3.1.2. `tests/test_csv_importer.py` (41 funções / 96 itens)
- **Requisitos e Issues:** RF01, RF02, RF03, RF04, T01, T02, T03 | Issues `#1`, `#2`, `#6`, `#18`, `#58`.
- **O que verifica:**
  - Importação genérica via `CSVImporter`: detecção de delimitadores (vírgula, ponto e vírgula, tabulação), remoção de BOM (`utf-8-sig`), normalização de cabeçalhos com acentos/maiúsculas e geração determinística de `id` quando ausente.
  - Validação estrita de datas (`data`), aceitando ISO-8601 e rejeitando datas impossíveis (ex.: `2026-02-30`) ou formatos ambíguos.
  - Rejeição de arquivos inexistentes, diretórios, extensões inválidas, binários (PNG/PDF/NUL bytes), CSVs vazios, cabeçalhos duplicados e linhas com colunas excedentes (`csv.reader` key `None`).
- **Exemplo real do código (`tests/test_csv_importer.py`):**
```python
def test_rejeita_csv_sem_coluna_obrigatoria_texto(self, tmp_path: Path) -> None:
    arquivo = tmp_path / "sem_texto.csv"
    arquivo.write_text("id,fonte,comentario\n1,XFetch,Bom dia\n", encoding="utf-8")

    importer = CSVImporter()
    with pytest.raises(CSVValidationError, match="texto"):
        importer.importar_arquivo(arquivo)
```

#### 3.1.3. `tests/test_importacao.py` (10 funções / 20 itens)
- **Requisitos e Issues:** RF01, RF02, RF03, T01, T02 | Issues `#1`, `#2`, `#6`.
- **O que verifica:**
  - Interface funcional `importar_csv`, garantindo o contrato mínimo de saída (`id`, `texto`, `fonte`, `metadados`), geração determinística de `id` a partir do conteúdo quando o CSV não fornece identificador e tratamento de `ErroImportacaoCSV`.
- **Exemplo real do código (`tests/test_importacao.py`):**
```python
def test_importar_csv_gera_id_deterministico_quando_ausente(tmp_path: Path) -> None:
    arquivo = tmp_path / "sem_id.csv"
    arquivo.write_text("texto\nPrimeiro texto\n", encoding="utf-8")

    primeira_leitura = importar_csv(arquivo, fonte="upload_manual")
    segunda_leitura = importar_csv(arquivo, fonte="upload_manual")

    assert primeira_leitura[0]["id"] == segunda_leitura[0]["id"]
    assert primeira_leitura[0]["fonte"] == "upload_manual"
```

#### 3.1.4. `tests/test_xfetch.py` (29 funções / 58 itens)
- **Requisitos e Issues:** RF01, RF03, RF04, RNF01 | Issues `#3`, `#18`, `#59`, `#60`.
- **O que verifica:**
  - Normalização de tweets retornados pela API XFetch (`id`, `text`, `created_at` com timezone obrigatório) para o contrato de aquisição (`fonte="XFetch"`, `data` em UTC ISO-8601).
  - Paginação automática (`next_token`) respeitando `quantidade`, `limite_por_pagina <= 20`, `maximo_de_paginas` e interrupção contra loop infinito quando `next_token` se repete.
  - Deduplicação por `id` entre páginas e rejeição imediata sem chamada de rede quando `XFETCH_API_KEY` está ausente/vazia.
  - Tratamento de falhas HTTP (`401`, `402`, `403`, `429`, `500`, `503`) e timeout sem retry oculto e **sem vazar o valor de `XFETCH_API_KEY`** na exceção (`XFetchAPIError`).
- **Exemplo real do código (`tests/test_xfetch.py`):**
```python
@pytest.mark.parametrize("status_code", [401, 402, 403, 429, 500, 503])
def test_status_http_sem_retry_nem_vazamento(status_code: int) -> None:
    segredo = "chave-super-secreta-xfetch-999"
    sessao = MagicMock()
    resposta = MagicMock(status_code=status_code, text=f"Erro interno com token {segredo}")
    sessao.get.return_value = resposta

    cliente = XFetchClient(api_key=segredo, session=sessao)
    with pytest.raises(XFetchAPIError) as exc_info:
        cliente.buscar_tweets_recentes("eleicoes", quantidade=10)

    assert sessao.get.call_count == 1
    assert segredo not in str(exc_info.value)
```

#### 3.1.5. `tests/test_auditoria_datasets.py` (3 funções / 3 itens)
- **Requisitos e Issues:** RF01, RF02 | Issues `#4`, `#5`, `#6`.
- **O que verifica:**
  - Funções de auditoria estatística e estrutural de datasets (`auditar_tweetsentbr`, `auditar_bpsad`), contabilizando total de linhas, textos vazios, duplicatas de ID/texto, comprimentos mínimo/médio/máximo e distribuição de classes antes do treinamento/avaliação.
- **Exemplo real do código (`tests/test_auditoria_datasets.py`):**
```python
def test_auditar_dataset_contabiliza_duplicados_e_distribuicao(tmp_path: Path) -> None:
    csv_path = tmp_path / "amostra.csv"
    csv_path.write_text(
        "id,texto,rotulo\n1, Bom ,positivo\n1, Bom ,positivo\n2,Ruim,negativo\n",
        encoding="utf-8",
    )
    relatorio = auditar_csv_rotulado(csv_path, coluna_id="id", coluna_texto="texto", coluna_rotulo="rotulo")
    assert relatorio["total_linhas"] == 3
    assert relatorio["ids_duplicados"] == 1
```

#### 3.1.6. `tests/test_experimentos_bpsad.py` (9 funções / 14 itens)
- **Requisitos e Issues:** RF01, RF05, RF08 | Issues `#5`, `#8`, `#10`.
- **O que verifica:**
  - Amostragem estratificada reprodutível (`amostrar_bpsad`) mantendo a proporção entre classes (`positivo`, `negativo`, `neutro`) com `seed` fixa.
  - Execução via CLI (`python -m scripts.experimentos.amostrar_bpsad`) e proteção contra sobrescrita acidental do arquivo de saída sem `--sobrescrever`.
- **Exemplo real do código (`tests/test_experimentos_bpsad.py`):**
```python
def test_cli_e_protecao_contra_sobrescrita(corpus):
    saida = corpus.parent / "amostra.csv"
    comando = [sys.executable, "-m", "scripts.experimentos.amostrar_bpsad", "--entrada",
               str(corpus), "--saida", str(saida), "--tamanho", "30"]
    sucesso = subprocess.run(comando, capture_output=True, text=True)
    assert sucesso.returncode == 0, sucesso.stderr

    bloqueado = subprocess.run(comando, capture_output=True, text=True)
    assert bloqueado.returncode != 0
```

---

### 3.2. Subsistema de Classificação ML e Pipeline (`src/processamento/`)

#### 3.2.1. `tests/test_classificacao.py` (11 funções / 14 itens)
- **Requisitos e Issues:** RF05, RF06, RF07, T04, T05, T06, T07 | Issues `#7`, `#8`, `#9`.
- **O que verifica:**
  - Normalização de rótulos do modelo (`POS -> positivo`, `NEG -> negativo`, `NEU -> neutro`).
  - Treinamento e predição do `ClassificadorBaseline` (TF-IDF + LogisticRegression), garantindo retorno de `sentimento` e `probabilidades` para as três classes somando `1.0` (`pytest.approx(1.0)`).
  - Adaptação do `ClassificadorBERTweet` usando analisador injetado (evitando download de pesos do Hugging Face durante os testes unitários), validando rejeição de textos vazios/não-string e falha caso o baseline seja usado antes de `treinar()`.
- **Exemplo real do código (`tests/test_classificacao.py`):**
```python
def test_bertweet_com_analisador_injetado_normaliza_saida() -> None:
    analisador_falso = MagicMock()
    analisador_falso.predict.return_value = SimpleNamespace(
        output="POS",
        probas={"POS": 0.82, "NEG": 0.08, "NEU": 0.10},
    )
    classificador = ClassificadorBERTweet(analisador=analisador_falso)

    resultado = classificador.classificar("Excelente iniciativa!")

    assert resultado["sentimento"] == "positivo"
    assert resultado["probabilidades"] == {
        "positivo": pytest.approx(0.82),
        "negativo": pytest.approx(0.08),
        "neutro": pytest.approx(0.10),
    }
```

#### 3.2.2. `tests/test_avaliacao.py` (3 funções / 16 itens)
- **Requisitos e Issues:** RF08 | Issues `#8`, `#9`, `#10`.
- **O que verifica:**
  - Cálculo de métricas supervisionadas (`avaliar_predicoes`): `acuracia`, `f1_macro`, precisão, revocação e suporte por classe, além de rejeição de listas vazias, tamanhos divergentes ou rótulos fora do contrato.
- **Exemplo real do código (`tests/test_avaliacao.py`):**
```python
def test_avaliar_predicoes_calcula_metricas_corretamente() -> None:
    y_true = ["positivo", "negativo", "neutro", "positivo"]
    y_pred = ["positivo", "negativo", "positivo", "positivo"]

    metricas = avaliar_predicoes(y_true, y_pred)

    assert metricas["total_amostras"] == 4
    assert metricas["acuracia"] == pytest.approx(0.75)
    assert set(metricas["por_classe"].keys()) == {"positivo", "negativo", "neutro"}
```

#### 3.2.3. `tests/test_comparar_modelos.py` (2 funções / 5 itens)
- **Requisitos e Issues:** RF05, RF08 | Issues `#8`, `#9`, `#10`.
- **O que verifica:**
  - Fluxo de comparação entre `ClassificadorBaseline` e `ClassificadorBERTweet` sobre conjuntos de treino/teste e geração da tabela comparativa em Markdown.
- **Exemplo real do código (`tests/test_comparar_modelos.py`):**
```python
def test_comparar_modelos_gera_estrutura_completa() -> None:
    relatorio = executar_comparacao(treino, teste, analisador_bertweet=analisador_simulado)
    assert "baseline" in relatorio
    assert "bertweet" in relatorio
    assert "f1_macro" in relatorio["bertweet"]
```

#### 3.2.4. `tests/test_pipeline.py` (14 funções / 19 itens)
- **Requisitos e Issues:** RF03, RF04, RF05, RF06, RF07, RF09 | Issues `#7`, `#17`, `#19`.
- **O que verifica:**
  - `PipelineClassificacao.processar_registro` e `processar_lote`: transformação de um registro de aquisição (`id`, `texto`, `fonte`, `data`) no documento canônico de análise (`id_origem`, `fonte`, `texto_original`, `sentimento`, `probabilidades`, `modelo`, `data_processamento`, `data_publicacao`).
  - Garantia de que `texto_original` permanece idêntico ao `texto` de entrada, que `data_processamento` e `data_publicacao` são `datetime` timezone-aware em UTC e que campos ausentes opcionais (`data_publicacao`, `rotulo_original`) não geram chaves com `None`.
- **Exemplo real do código (`tests/test_pipeline.py`):**
```python
def test_pipeline_gera_documento_canonico_completo() -> None:
    pipeline = PipelineClassificacao(classificador=ClassificadorSimulado())
    registro = {
        "id": "tw_100",
        "texto": "Adorei o novo sistema! 🚀 @equipe",
        "fonte": "TweetSentBR",
        "data": "2026-10-05T14:30:00Z",
    }

    doc = pipeline.processar_registro(registro)

    assert doc["id_origem"] == "tw_100"
    assert doc["texto_original"] == "Adorei o novo sistema! 🚀 @equipe"
    assert doc["sentimento"] in {"positivo", "negativo", "neutro"}
    assert doc["data_processamento"].tzinfo == UTC
    assert doc["data_publicacao"] == datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
```

#### 3.2.5. `tests/test_integracao_conjunta.py` (6 funções / 10 itens)
- **Requisitos e Issues:** RF01–RF09, T01–T08 | Issues `#17`, `#18`, `#19`.
- **O que verifica:**
  - Integração simulada em memória encadeando `CSVImporter` / `TweetSentBRAdapter` $\rightarrow$ `PipelineClassificacao` $\rightarrow$ serialização `bson.BSON.encode` e validação contra `validar_documento_analise`.
- **Exemplo real do código (`tests/test_integracao_conjunta.py`):**
```python
def test_fluxo_csv_ate_bson_preserva_contrato(tmp_path: Path) -> None:
    registros = importar_csv(caminho_csv, fonte="TweetSentBR")
    pipeline = PipelineClassificacao(classificador=StubClassificador())
    analises = pipeline.processar_lote(registros)

    for doc in analises:
        raw_bson = BSON.encode(doc)
        decodificado = BSON(raw_bson).decode()
        assert decodificado["id_origem"] == doc["id_origem"]
        assert set(decodificado["probabilidades"]) == {"positivo", "negativo", "neutro"}
```

#### 3.2.6. `tests/test_xfetch_pipeline.py` (2 funções / 3 itens)
- **Requisitos e Issues:** RF01, RF05–RF09 | Issues `#3`, `#17`, `#19`, `#60`.
- **O que verifica:**
  - Integração simulada `XFetchClient` (paginado em múltiplas páginas via sessão HTTP mockada) $\rightarrow$ `PipelineClassificacao` $\rightarrow$ `BSON.encode`, além da garantia de que uma falha na 2ª página aborta a coleta sem retornar lote parcial silencioso.
- **Exemplo real do código (`tests/test_xfetch_pipeline.py`):**
```python
def test_falha_na_segunda_pagina_nao_retorna_resultado_parcial() -> None:
    sessao = MagicMock()
    sessao.get.side_effect = [ pagina_1_ok, pagina_2_erro_503 ]
    cliente = XFetchClient(api_key="chave-teste", session=sessao)

    with pytest.raises(XFetchAPIError):
        cliente.buscar_tweets_recentes("ia", quantidade=30, limite_por_pagina=20)
```

---

### 3.3. Subsistema de Persistência MongoDB (`src/dados/`)

#### 3.3.1. `tests/test_database.py` (16 funções / 35 itens)
- **Requisitos e Issues:** RF09, RF10 | Issues `#11`, `#12`, `#13`, `#14`.
- **O que verifica:**
  - `GerenciadorMongoDB`: leitura de `MONGODB_URI` e `MONGODB_DB_NAME`, validação de URI e nome do banco, execução de `admin.command("ping")` no `conectar()`, obtenção de coleção (`obter_colecao`), fechamento idempotente (`fechar_conexao`) e suporte a context manager (`with GerenciadorMongoDB(...)`).
  - Sanitização de mensagens de erro (`ErroConexaoBanco`) para **nunca expor senha ou URI completa** nos logs/exceções caso o MongoDB falhe.
- **Exemplo real do código (`tests/test_database.py`):**
```python
def test_conectar_nao_vaza_credenciais_da_uri_em_erro(monkeypatch: pytest.MonkeyPatch) -> None:
    uri_secreta = "mongodb://admin:SenhaSuperSecreta123@servidor-interno:27017/sentia"
    monkeypatch.setattr("src.dados.database.MongoClient", MagicMock(side_effect=ConnectionFailure(uri_secreta)))

    gerenciador = GerenciadorMongoDB(uri=uri_secreta, db_name="sentia")
    with pytest.raises(ErroConexaoBanco) as exc_info:
        gerenciador.conectar()

    assert "SenhaSuperSecreta123" not in str(exc_info.value)
    assert "servidor-interno" not in str(exc_info.value)
```

#### 3.3.2. `tests/test_repositorio.py` (21 funções / 41 itens: 33 passados offline + 8 `SKIPPED` sem Mongo local)
- **Requisitos e Issues:** RF09, RF10, T08, T09 | Issues `#11`, `#19`, `#20`, `#22`.
- **O que verifica:**
  - **13 funções offline (33 itens parametrizados):**
    - `validar_documento_analise`: rejeita ausência de campos obrigatórios (`id_origem`, `fonte`, `texto_original`, `sentimento`, `probabilidades`, `modelo`, `data_processamento`), rejeita `bool` disfarçado de número em `probabilidades`, rejeita soma de probabilidades fora de `[0.99, 1.01]`, rejeita `datetime` sem fuso (naive) ou string ISO no lugar de `datetime` BSON UTC e remove `data_publicacao=None`.
    - `RepositorioAnalises` com coleção mockada: verifica envio dos 4 índices do esquema (`idx_unico_origem_fonte` único em `(id_origem, fonte)`, `idx_sentimento_data`, `idx_data_processamento`, `idx_data_publicacao`), tratamento de `DuplicateKeyError` (código `11000`), contagem de `{inseridos, duplicados}` em `salvar_analises` (`BulkWriteError`) e propagação de falhas de escrita que não sejam código `11000`.
  - **8 funções de integração real com MongoDB (`colecao` fixture):**
    - Executam contra `mongodb://localhost:27017` no banco isolado `sentia_teste_repositorio` quando ativo, ou são marcadas como `SKIPPED` quando indisponível (ver Seção 6).
- **Exemplo real do código (`tests/test_repositorio.py`):**
```python
def test_lote_conta_duplicatas_sem_banco_real() -> None:
    colecao = MagicMock()
    erro_bulk = BulkWriteError(
        {
            "writeErrors": [{"code": 11000, "index": 1}],
            "nInserted": 2,
        }
    )
    colecao.insert_many.side_effect = erro_bulk
    repo = RepositorioAnalises(colecao)

    resultado = repo.salvar_analises([_documento_valido("1"), _documento_valido("1"), _documento_valido("2")])

    assert resultado == {"inseridos": 2, "duplicados": 1}
```

---

### 3.4. Subsistema de Serviço / API FastAPI e QA (`src/servico/`)

#### 3.4.1. `tests/test_api.py` (9 funções / 17 itens)
- **Requisitos e Issues:** RF05–RF10, T09 | Issues `#15`, `#16`, `#20`, `#21`, `#22`.
- **O que verifica:**
  - `GET /health` retornando `200 OK` com `{"status": "ok"}`.
  - `POST /analises` recebendo lote de registros brutos, classificando via `PipelineClassificacao` e persistindo via `RepositorioAnalises`, retornando `200 OK` com `processados`, `inseridos`, `duplicados` e `resultados`.
  - Rejeição com `422 Unprocessable Entity` para payloads inválidos (lista vazia, texto em branco, campos extras `extra="forbid"`, data sem timezone ou inválida) sem acionar gravação no banco.
  - Tradução de falhas operacionais do classificador ou do MongoDB em `503 Service Unavailable` com mensagem sanitizada (`"Serviço de análise temporariamente indisponível."` / `"Banco de dados temporariamente indisponível."`), garantindo `fechar_conexao()` no bloco `finally` da dependência `obter_colecao_analises`.
- **Exemplo real do código (`tests/test_api.py`):**
```python
def test_post_analises_classifica_e_persiste() -> None:
    colecao_falsa = MagicMock()
    app.dependency_overrides[obter_colecao_analises] = lambda: colecao_falsa
    app.dependency_overrides[obter_classificador] = lambda: ClassificadorFalso()

    with TestClient(app) as client:
        resposta = client.post(
            "/analises",
            json={
                "registros": [
                    {
                        "id": "tw-1",
                        "texto": "O atendimento foi excelente!",
                        "fonte": "TweetSentBR",
                        "data": "2026-10-10T12:00:00Z",
                    }
                ]
            },
        )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["processados"] == 1
    assert corpo["inseridos"] == 1
    assert corpo["duplicados"] == 0
    assert corpo["resultados"][0]["sentimento"] == "positivo"
```

#### 3.4.2. `tests/test_consultas_api.py` (10 funções / 48 itens)
- **Requisitos e Issues:** RF10, RF11, RF12, T10 | Issues `#19`, `#22`, `#23`, `#24`, `#25`.
- **O que verifica:**
  - `GET /analises`: listagem ordenada por `data_processamento` decrescente, remoção de `_id` do MongoDB, formatação de datas em ISO-8601 UTC (`Z`), aplicação de filtros `inicio`, `fim`, `sentimento`, `fonte` e `limite` (`1..500`, padrão `100`).
  - Regra temporal de período (`inicio`/`fim`) conforme `docs/contratos-dados.md`: filtra por `data_publicacao` quando presente no documento e usa `data_processamento` como fallback quando `data_publicacao` está ausente.
  - `GET /analises/resumo`: agregação `total` e `por_sentimento` (`positivo`, `negativo`, `neutro` sempre presentes mesmo quando zero) e eco dos filtros aplicados (`inicio`, `fim`, `sentimento`, `fonte`).
  - Integração simulada ponta a ponta com `FonteApi` (`src/apresentacao/fontes/api.py`), provando que o cliente HTTP do Dashboard consome diretamente as respostas reais do FastAPI sem erro de contrato.
- **Exemplo real do código (`tests/test_consultas_api.py`):**
```python
def test_respostas_aceitas_pelo_cliente_fonte_api() -> None:
    colecao = ColecaoMemoria([_doc_exemplo("1", "positivo"), _doc_exemplo("2", "negativo")])
    app.dependency_overrides[obter_colecao_analises] = lambda: colecao

    with TestClient(app) as client:
        fonte = FonteApi(url_base="http://testserver", sessao=client)
        resumo = fonte.obter_resumo(FiltrosAnalises(sentimento="positivo"))
        exemplos = fonte.listar_exemplos(FiltrosAnalises(sentimento="positivo"), limite=10)

    assert resumo.total == 1
    assert resumo.por_sentimento["positivo"] == 1
    assert len(exemplos) == 1
    assert exemplos[0].id_origem == "1"
```

#### 3.4.3. `tests/test_api_administracao.py` (29 funções / 38 itens)
- **Requisitos e Issues:** RF01–RF04, RF13, RF14, RF15, RNF01 | Issues `#15`, `#16`, `#21`, `#27`, `#61`.
- **O que verifica:**
  - Verificação criptográfica de senha (`pbkdf2_sha256$<iteracoes>$<sal>$<hash>`), rejeitando formatos malformados sem ecoar o segredo.
  - `POST /auth/login` e `POST /auth/logout`: emissão de token Bearer opaco com expiração em UTC, mensagens genéricas de erro que não revelam se o usuário ou a senha falhou, e bloqueio temporário (`429 Too Many Requests`) após excesso de tentativas inválidas.
  - `POST /datasets` e `GET /datasets`: upload multipart de CSV (limite de 10 MB, validação UTF-8 e colunas obrigatórias `texto` e `fonte`), contabilização de registros aceitos/descartados e disponibilização imediata do dataset como fonte de coleta.
  - `GET /coletas/fontes`, `POST /coletas`, `GET /coletas` e `GET /coletas/{id_coleta}`: execução de coletas sobre datasets importados ou `TweetSentBR`, retorno de resumo por sentimento e amostras analisadas.
  - Integração simulada entre `AdministracaoApi` (cliente do painel Streamlit) e o `TestClient(app)` da FastAPI.
- **Exemplo real do código (`tests/test_api_administracao.py`):**
```python
def test_painel_importa_e_ja_analisa_o_csv_na_api_real(ambiente_admin) -> None:
    with TestClient(app) as cliente_http:
        api = AdministracaoApi(url_base="http://testserver", sessao=cliente_http)
        sessao = api.autenticar("admin", "SenhaForte!123")
        dataset, coleta = api.importar_e_analisar_csv(
            sessao.token,
            nome_arquivo="lote.csv",
            conteudo=b"id,texto,fonte\n1,Muito bom!,upload\n2,Ruim demais,upload\n",
        )

    assert dataset.registros_validos == 2
    assert coleta.status == "concluida"
    assert coleta.processados == 2
```

#### 3.4.4. `tests/test_qa_t09_t10.py` (11 funções / 19 itens)
- **Requisitos e Issues:** RF09, RF10, T09, T10 | Issues `#15`, `#16`, `#19`, `#20`, `#21`, `#22`, `#23`.
- **O que verifica:**
  - Formaliza os casos de teste do plano de QA para a Sprint 4:
    - **T09 (Persistência e Deduplicação):** verifica que documentos gerados pelo `PipelineClassificacao` são validados e gravados pelo `RepositorioAnalises`, que a chave composta `(id_origem, fonte)` impede duplicação na reexecução do mesmo lote e permite o mesmo `id_origem` em fontes distintas, e que `POST /analises` reflete `inseridos` e `duplicados`.
    - **T10 (Disponibilidade e Contratos da API):** verifica `GET /health` (`200`), `POST /analises` (`200` com payload válido, `422` com payload inválido, `503` quando classificador/banco falha) e `GET /analises` + `GET /analises/resumo` (`200` com filtros válidos e `422` com parâmetros inválidos).
- **Exemplo real do código (`tests/test_qa_t09_t10.py`):**
```python
def test_t09_reexecucao_do_mesmo_lote_via_post_analises_nao_duplica() -> None:
    colecao = ColecaoComIndiceUnico()
    app.dependency_overrides[obter_colecao_analises] = lambda: colecao
    app.dependency_overrides[obter_classificador] = lambda: StubClassificador()

    payload = {"registros": [{"id": "tw-99", "texto": "Teste T09", "fonte": "TweetSentBR"}]}
    with TestClient(app) as client:
        r1 = client.post("/analises", json=payload).json()
        r2 = client.post("/analises", json=payload).json()

    assert r1["inseridos"] == 1 and r1["duplicados"] == 0
    assert r2["inseridos"] == 0 and r2["duplicados"] == 1
```

---

### 3.5. Subsistema de Apresentação / Painel Streamlit (`src/apresentacao/`)

#### 3.5.1. `tests/test_painel_arquitetura.py` (1 função parametrizada / 18 itens)
- **Requisitos e Issues:** Isolamento arquitetural em camadas | Issues `#27`, `#28`.
- **O que verifica:**
  - Inspeciona a árvore sintática (`ast.parse`) de cada um dos 18 arquivos `.py` dentro de `src/apresentacao/` e garante que a camada de apresentação **nunca importa** `pymongo`, `bson`, `fastapi`, `torch`, `transformers`, `pysentimiento`, `sklearn` nem os pacotes internos `src.dados`, `src.servico` ou `src.processamento` — comunicando-se exclusivamente via contrato HTTP (`requests`).
- **Exemplo real do código (`tests/test_painel_arquitetura.py`):**
```python
MODULOS_PROIBIDOS = {
    "bson", "fastapi", "pymongo", "pysentimiento", "sklearn",
    "torch", "transformers", "src.dados", "src.processamento", "src.servico",
}

@pytest.mark.parametrize("arquivo", ARQUIVOS_APRESENTACAO, ids=lambda p: p.name)
def test_apresentacao_nao_importa_camadas_internas(arquivo: Path) -> None:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    ...
```

#### 3.5.2. `tests/test_painel_config.py` (2 funções / 12 itens)
- **Requisitos e Issues:** Configuração segura por variáveis de ambiente | Issues `#27`, `#28`.
- **O que verifica:**
  - `carregar_configuracao()`: valores padrão seguros (`fonte_dados="mock"`, `cenario_mock="normal"`, `url_api="http://localhost:8000"`, `timeout_segundos=5.0`, `limite_exemplos=50`) e rejeição com `ValueError` para esquemas não-HTTP(S), timeouts `<= 0` ou `> 60`, limites fora de `1..500` ou cenários mock desconhecidos.

#### 3.5.3. `tests/test_painel_transformacoes.py` (4 funções / 11 itens)
- **Requisitos e Issues:** RF10, US14 | Issue `#28`.
- **O que verifica:**
  - `calcular_percentuais()`: garante pelo método do maior resto que os percentuais inteiros de `positivo`, `negativo` e `neutro` **sempre somam exatamente `100%`** quando `total > 0` (ex.: `1, 1, 1 -> 34%, 33%, 33%`) e retornam `0%, 0%, 0%` quando `total == 0`.
  - `formatar_inteiro()`: formatação com separador de milhar brasileiro (`1.234`).

#### 3.5.4. `tests/test_painel_fonte_mock.py` (7 funções / 7 itens)
- **Requisitos e Issues:** RF10, RF11, RF12 | Issue `#28`.
- **O que verifica:**
  - Comportamento determinístico de `FonteMock`, `FonteMockVazia` e `FonteMockComErro`, assegurando que os dados de demonstração respeitam o contrato `AnaliseSentimento` e `ResumoSentimentos`.

#### 3.5.5. `tests/test_painel_fonte_api.py` (17 funções / 92 itens)
- **Requisitos e Issues:** RF10, RF11, RF12, T10 | Issues `#19`, `#25`, `#28`.
- **O que verifica:**
  - Cliente HTTP `FonteApi`: montagem correta de query strings (`inicio`, `fim`, `sentimento`, `fonte`, `limite`) para `GET /analises/resumo` e `GET /analises`.
  - Validação defensiva rigorosa das respostas JSON da API: rejeita payloads não-objeto, contagens negativas ou booleanas, `total` inconsistente com a soma de `por_sentimento`, probabilidades que não somam `1.0`, datas sem timezone ou textos vazios, convertendo qualquer violação de contrato ou erro de rede/HTTP (`Timeout`, `ConnectionError`, `503`, `422`) em `ErroFonteDados` amigável ao usuário.
- **Exemplo real do código (`tests/test_painel_fonte_api.py`):**
```python
def test_obter_resumo_rejeita_total_inconsistente_com_parcelas() -> None:
    sessao = _sessao_com_resposta(
        200,
        {"total": 10, "por_sentimento": {"positivo": 2, "negativo": 2, "neutro": 2}},
    )
    fonte = FonteApi(url_base="http://localhost:8000", sessao=sessao)

    with pytest.raises(ErroFonteDados, match="soma"):
        fonte.obter_resumo(FiltrosAnalises())
```

#### 3.5.6. `tests/test_painel_filtros.py` (12 funções / 18 itens)
- **Requisitos e Issues:** RF11, RF12, US17, US18 | Issue `#28`.
- **O que verifica:**
  - Filtragem por intervalo de datas (`inicio <= data_referencia <= fim`), sentimento e combinação de ambos tanto nas funções de domínio quanto diretamente na árvore de widgets do Streamlit (`streamlit.testing.v1.AppTest`).

#### 3.5.7. `tests/test_painel_ui.py` (9 funções / 18 itens)
- **Requisitos e Issues:** RF10, RF11, RF12, US13–US20 | Issue `#28`.
- **O que verifica:**
  - Testes de sistema da interface pública do Dashboard via `AppTest.from_file("src/apresentacao/app.py")`:
    - Exibição dos 4 cards de indicadores (Total, Positivos, Negativos, Neutros com contagem e percentual).
    - Banner explícito de aviso quando `SENTIA_FONTE_DADOS=mock` e ausência desse banner quando conectado à `FonteApi`.
    - Estado vazio informativo (`"Nenhuma análise encontrada para os filtros selecionados"`) e estado de erro (`ErroFonteDados`) sem stack trace exposto na tela.

#### 3.5.8. `tests/test_painel_administracao.py` (37 funções / 58 itens)
- **Requisitos e Issues:** RF13, RF14, RF15, RNF01, US01–US12 | Issues `#27`, `#61`.
- **O que verifica:**
  - Cliente HTTP `AdministracaoApi`: autenticação `POST /auth/login`, envio de cabeçalho `Authorization: Bearer <token>`, upload multipart `POST /datasets`, disparo e consulta de coletas `POST /coletas` / `GET /coletas`, e tradução de `401`/`403` em `ErroAutenticacao`.
  - Interface administrativa no Streamlit (`AppTest`): bloqueio de tela sem login, formulário de autenticação, importação de CSV com análise imediata, histórico de coletas e **mascaramento automático de menções (`@usuario` $\rightarrow$ `@[usuário]`)** nos textos exibidos na tela (conformidade de privacidade/LGPD).
- **Exemplo real do código (`tests/test_painel_administracao.py`):**
```python
def test_mascarar_mencoes_oculta_arrobas_preservando_email() -> None:
    texto = "Fale com @Maria_Silva ou envie email para contato@dominio.gov.br sobre @joao123!"
    assert mascarar_mencoes(texto) == (
        "Fale com @[usuário] ou envie email para contato@dominio.gov.br sobre @[usuário]!"
    )
```

---

## 4. Classificação Metodológica: Unitário, Contrato, Integração Simulada e Integração Real

Para evitar qualquer confusão entre testes com mocks/clientes em memória e integração real entre processos/serviços, a tabela abaixo classifica rigorosamente as modalidades presentes no repositório:

| Categoria | Definição Técnica no SentIA | O Que Está Real vs. Simulado | Onde Está na Suíte |
| :--- | :--- | :--- | :--- |
| **1. Teste Unitário** | Verifica uma função, classe ou adaptador isolado. Dependências externas (rede, disco, banco, modelo ML) são substituídas por mocks, `MagicMock`, `monkeypatch` ou arquivos temporários (`tmp_path`). | **Real:** lógica da unidade testada.<br>**Simulado:** sessão HTTP (`requests`), `MongoClient`, analisador `pysentimiento`. | `test_aquisicao.py`, `test_csv_importer.py`, `test_importacao.py`, `test_xfetch.py`, `test_classificacao.py`, `test_avaliacao.py`, `test_database.py`, `test_painel_config.py`, `test_painel_transformacoes.py`, `test_painel_fonte_mock.py`. |
| **2. Teste de Contrato** | Verifica se a estrutura de entrada/saída entre duas camadas obedece estritamente às regras de `docs/contratos-dados.md` (nomes de campos, tipos, soma de probabilidades `1.0`, datas UTC ISO-8601 ou BSON `datetime`, códigos HTTP `200`/`401`/`422`/`503` e ausência de vazamento de segredos). | **Real:** validadores (`validar_documento_analise`, schemas Pydantic de `src/servico/esquemas.py`, parser de `FonteApi`, `bson.BSON.encode`, AST de `test_painel_arquitetura.py`).<br>**Simulado:** transporte ou persistência subjacente. | `test_repositorio.py` (validação de documento), `test_painel_fonte_api.py`, `test_painel_arquitetura.py`, validações `422`/`503` em `test_api.py` e `test_consultas_api.py`. |
| **3. Integração Simulada (In-Process)** | Encadeia múltiplos módulos reais do próprio repositório no mesmo processo Python, mas substitui a infraestrutura externa (servidor MongoDB, API remota XFetch ou pesos reais do BERTweet) por objetos em memória (`TestClient(app)`, `ColecaoMemoria`, `StubClassificador`, `AppTest`). | **Real:** encadeamento entre camadas (ex.: `CSVImporter -> PipelineClassificacao -> BSON`, ou `FonteApi / AdministracaoApi -> FastAPI TestClient -> RepositorioAnalises`).<br>**Simulado:** banco em memória ou `MagicMock`, classificador stub, transporte ASGI em memória via `httpx`/`TestClient`. | `test_integracao_conjunta.py`, `test_xfetch_pipeline.py`, `test_api.py`, `test_consultas_api.py`, `test_api_administracao.py`, `test_qa_t09_t10.py`, `test_painel_filtros.py`, `test_painel_ui.py`, `test_painel_administracao.py`. |
| **4. Integração Real (Infraestrutura Externa)** | Executa contra serviços ou artefatos externos reais fora de mocks: instância real do servidor MongoDB via TCP (`mongodb://localhost:27017`), pesos reais do modelo Hugging Face (`pysentimiento/bertweet-pt-sentiment` via `--group ml`) ou API externa XFetch com `XFETCH_API_KEY` real. | **Real:** driver PyMongo falando wire protocol com `mongod` real, índices únicos e `BulkWriteError` gerados pelo motor do MongoDB; ou inferência neural PyTorch/Transformers. | As **8 funções** de `tests/test_repositorio.py` que usam a fixture `colecao` (integração real com MongoDB local) e o script manual `test_mongo.py`. |

> [!CAUTION]
> **Não confunda:**
> - Serializar um dicionário com `bson.BSON.encode(doc)` em `tests/test_integracao_conjunta.py` valida **contrato de tipos BSON em memória**, mas **não** substitui a gravação no servidor MongoDB (`tests/test_repositorio.py` com fixture `colecao`).
> - Chamar `TestClient(app)` com `app.dependency_overrides[obter_colecao_analises]` em `tests/test_api.py`, `tests/test_consultas_api.py` e `tests/test_qa_t09_t10.py` valida **integração simulada entre cliente HTTP, rotas FastAPI e lógica de negócio**, mas **não** prova que o processo Uvicorn esteja conectado a um `mongod` real nem que os pesos do BERTweet estejam instalados no ambiente.

---

## 5. Como Testar Manualmente: FastAPI, MongoDB e Dashboard

### 5.1. Teste Manual do MongoDB (`GerenciadorMongoDB` e `RepositorioAnalises`)

1. Suba um container MongoDB isolado localmente:
   ```bash
   docker run --rm -d --name sentia-mongo-manual -p 27017:27017 mongo:7
   ```
2. Configure `.env` (ou passe variáveis na linha de comando) e execute o script de diagnóstico `test_mongo.py` presente na raiz do repositório:
   ```bash
   MONGODB_URI="mongodb://localhost:27017" MONGODB_DB_NAME="sentia_dev" uv run python test_mongo.py
   ```
3. **Resposta esperada:**
   ```text
   Iniciando teste de conexão com o MongoDB...
   Sucesso! Conectado ao banco: sentia_dev
   Coleção 'analises' pronta para uso: Collection(Database(MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=True, connect=True), 'sentia_dev'), 'analises')
   Conexão encerrada com segurança.
   ```
4. Ao finalizar, remova o container temporário:
   ```bash
   docker stop sentia-mongo-manual
   ```

---

### 5.2. Teste Manual da API FastAPI (`/health`, `/analises`, `/analises/resumo` e Administração)

#### Pré-requisitos para subir a API completa:
- Para usar `POST /analises` com o classificador real padrão (`obter_classificador`), é necessário ter o grupo `ml` instalado (`uv sync --locked --group ml`) e o MongoDB ativo em `MONGODB_URI`.
- Para habilitar as rotas de Administração (`/auth/*`, `/datasets`, `/coletas*`), é obrigatório definir `SENTIA_ADMIN_USUARIO` e `SENTIA_ADMIN_SENHA_HASH` no formato `pbkdf2_sha256$<iteracoes>$<sal_hex>$<hash_hex>`.

#### Passo 1 — Gerar um hash de senha válido para o administrador:
```bash
uv run python -c '
import hashlib
sal = "0123456789abcdef0123456789abcdef"
iteracoes = 390000
derivado = hashlib.pbkdf2_hmac("sha256", b"SenhaAdmin123!", bytes.fromhex(sal), iteracoes).hex()
print(f"pbkdf2_sha256${iteracoes}${sal}${derivado}")
'
```

#### Passo 2 — Iniciar o servidor FastAPI com Uvicorn:
```bash
MONGODB_URI="mongodb://localhost:27017" \
MONGODB_DB_NAME="sentia_dev" \
SENTIA_ADMIN_USUARIO="admin" \
SENTIA_ADMIN_SENHA_HASH="pbkdf2_sha256$390000$0123456789abcdef0123456789abcdef$887bb57e8a93f9ae61c881fa7547cf15c9e15c828419d478bd73923eb2d75148" \
uv run uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
```

#### Passo 3 — Verificar `GET /health`:
```bash
curl -s http://127.0.0.1:8000/health
```
- **Resposta esperada (`200 OK`):**
  ```json
  {"status":"ok"}
  ```

#### Passo 4 — Classificar e persistir um lote via `POST /analises`:
```bash
curl -s -X POST http://127.0.0.1:8000/analises \
  -H "Content-Type: application/json" \
  -d '{
    "registros": [
      {
        "id": "manual-001",
        "texto": "O novo portal de dados abertos ficou excelente e muito rápido!",
        "fonte": "TweetSentBR",
        "data": "2026-10-15T14:00:00Z"
      }
    ]
  }'
```
- **Resposta esperada (`200 OK`):**
  ```json
  {
    "processados": 1,
    "inseridos": 1,
    "duplicados": 0,
    "resultados": [
      {
        "id_origem": "manual-001",
        "fonte": "TweetSentBR",
        "texto_original": "O novo portal de dados abertos ficou excelente e muito rápido!",
        "sentimento": "positivo",
        "probabilidades": {
          "positivo": 0.96,
          "negativo": 0.01,
          "neutro": 0.03
        },
        "modelo": {
          "nome": "pysentimiento/bertweet-pt-sentiment",
          "versao": "1.0.0"
        },
        "data_processamento": "2026-11-11T20:50:00Z",
        "data_publicacao": "2026-10-15T14:00:00Z",
        "rotulo_original": null,
        "rotulo_padronizado": null
      }
    ]
  }
  ```
- **Se reexecutado com o mesmo `(id, fonte)` (`200 OK` idempotente):**
  `"processados": 1, "inseridos": 0, "duplicados": 1`.

#### Passo 5 — Consultar `GET /analises` e `GET /analises/resumo`:
```bash
# Resumo agregado
curl -s "http://127.0.0.1:8000/analises/resumo?sentimento=positivo&fonte=TweetSentBR"
```
- **Resposta esperada (`200 OK`):**
  ```json
  {
    "total": 1,
    "por_sentimento": {
      "positivo": 1,
      "negativo": 0,
      "neutro": 0
    },
    "inicio": null,
    "fim": null,
    "sentimento": "positivo",
    "fonte": "TweetSentBR"
  }
  ```

```bash
# Lista de análises
curl -s "http://127.0.0.1:8000/analises?limite=5&fonte=TweetSentBR"
```
- **Resposta esperada (`200 OK`):** Objeto `{"total": 1, "analises": [...]}` contendo os documentos sem `_id` e com datas em ISO-8601 UTC (`Z`).

#### Passo 6 — Testar Autenticação e Coleta na API de Administração:
```bash
# Login administrativo
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "admin", "senha": "SenhaAdmin123!"}'
```
- **Resposta esperada (`200 OK`):**
  ```json
  {
    "token": "<token_bearer_gerado>",
    "usuario": "admin",
    "expira_em": "2026-11-11T21:20:00Z"
  }
  ```

```bash
# Listar fontes disponíveis para coleta (usando o token obtido)
curl -s http://127.0.0.1:8000/coletas/fontes \
  -H "Authorization: Bearer <token_bearer_gerado>"
```
- **Resposta esperada (`200 OK`):** Lista JSON com as fontes habilitadas (ex.: `TweetSentBR` quando `data/raw/tweetsentbr.csv` existe, mais os datasets enviados via `POST /datasets`).

---

### 5.3. Teste Manual do Dashboard e Painel de Administração (Streamlit)

#### Modo 1 — Demonstração Offline com Dados Simulados (`SENTIA_FONTE_DADOS=mock`)
Não exige FastAPI nem MongoDB ativos. Possui três cenários configuráveis via `SENTIA_MOCK_CENARIO`:

```bash
# Cenário 1: Normal (exibe métricas, gráficos e exemplos estáticos; login admin: admin / sentia-demo)
make run-painel
# Ou diretamente:
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run streamlit run src/apresentacao/app.py

# Cenário 2: Vazio (valida estado sem registros para os filtros selecionados)
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=vazio uv run streamlit run src/apresentacao/app.py

# Cenário 3: Erro (valida exibição de alerta amigável quando a fonte falha)
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=erro uv run streamlit run src/apresentacao/app.py
```
- **Comportamento esperado no navegador (`http://localhost:8501`):**
  - No cenário `normal`: exibe aviso amarelo informando uso de dados de exemplo, 4 cards de indicadores com percentuais que somam `100%`, gráficos de distribuição e tabela de exemplos; na aba **Administração**, permite entrar com usuário `admin` e senha `sentia-demo`.
  - No cenário `vazio`: exibe métricas zeradas e mensagem informativa de ausência de dados.
  - No cenário `erro`: exibe caixa de erro amigável sem stack trace do Python.

#### Modo 2 — Conectado à API FastAPI (`SENTIA_FONTE_DADOS=api`)
Com o servidor Uvicorn rodando em `http://localhost:8000`:

```bash
SENTIA_FONTE_DADOS=api SENTIA_API_URL=http://localhost:8000 uv run streamlit run src/apresentacao/app.py
```
- **Comportamento esperado:**
  - O Dashboard Público consome `GET /analises/resumo` e `GET /analises` em tempo real a partir do MongoDB.
  - A página **Administração** autentica contra `POST /auth/login` usando as credenciais configuradas em `SENTIA_ADMIN_USUARIO` / `SENTIA_ADMIN_SENHA_HASH` na API.

---

## 6. Testes Ignorados (`SKIPPED`) e Como Executá-los com Segurança

### 6.1. Quais Testes São Ignorados por Padrão

Ao executar `uv run pytest -ra` sem um servidor MongoDB local escutando em `localhost:27017`, exatamente **8 testes** são marcados como `SKIPPED`, todos localizados em `tests/test_repositorio.py`:

| Linha | Função de Teste em `tests/test_repositorio.py` | O Que Verifica no MongoDB Real |
| :---: | :--- | :--- |
| `107` | `test_cria_os_quatro_indices_do_esquema` | Criação efetiva dos 4 índices no catálogo do MongoDB (`idx_unico_origem_fonte`, `idx_sentimento_data`, `idx_data_processamento`, `idx_data_publicacao`) com `unique=True` em `(id_origem, fonte)` |
| `119` | `test_criar_indices_de_novo_nao_da_erro` | Idempotência de `criar_indices()` quando chamado repetidas vezes sobre a mesma coleção |
| `123` | `test_salvar_analise_grava_e_nao_duplica` | Inserção real com `insert_one` e retorno `False` na segunda tentativa com mesmo `(id_origem, fonte)` |
| `130` | `test_mesmo_id_em_fontes_diferentes_nao_e_duplicata` | Permissão de mesmo `id_origem` quando `fonte` difere (ex.: `TweetSentBR` vs. `XFetch`) |
| `136` | `test_salvar_analise_nao_altera_o_dicionario_original` | Garantia de que `salvar_analise` não injeta `_id` por efeito colateral no dicionário do chamador |
| `142` | `test_datas_sao_gravadas_como_data_e_publicacao_ausente_e_omitida` | Persistência nativa de `datetime` BSON UTC (`tz_aware=True`) e omissão da chave `data_publicacao` quando ausente |
| `149` | `test_salvar_analises_conta_inseridos_e_duplicados` | Inserção em lote (`insert_many(..., ordered=False)`) contabilizando `{inseridos, duplicados}` via `BulkWriteError` real do MongoDB |
| `159` | `test_lote_com_um_invalido_nao_grava_nada` | Atomicidade da validação prévia: se 1 item do lote é inválido, nenhum documento é gravado na coleção |

### 6.2. Por Que Exigem Ambiente Isolado (Segurança do Banco)

Veja a definição real da fixture `colecao` em `tests/test_repositorio.py` (linhas 40–55):

```python
BANCO_TESTE = "sentia_teste_repositorio"


@pytest.fixture
def colecao():
    gerenciador = GerenciadorMongoDB(
        uri="mongodb://localhost:27017",
        db_name=BANCO_TESTE,
        timeout_ms=1000,
    )
    try:
        gerenciador.conectar()
    except ErroConexaoBanco:
        pytest.skip("MongoDB local indisponível; ligue o Docker para rodar este teste.")

    assert gerenciador.client is not None
    gerenciador.client.drop_database(BANCO_TESTE)
    yield gerenciador.obter_colecao("analises")
    gerenciador.client.drop_database(BANCO_TESTE)
    gerenciador.fechar_conexao()
```

- A fixture conecta fixamente em `mongodb://localhost:27017` e executa `drop_database("sentia_teste_repositorio")` antes e depois de cada teste.
- Embora use um nome de banco específico (`sentia_teste_repositorio`), a boa prática de isolamento é nunca apontar testes destrutivos para uma instância compartilhada de desenvolvimento ou produção.

### 6.3. Passo a Passo para Executar os 8 Testes com Segurança

1. Certifique-se de que não há um MongoDB de uso pessoal ocupando a porta `27017`, e suba um container Docker efêmero (`--rm`, sem volume persistente):
   ```bash
   docker run --rm -d --name sentia-mongo-test -p 27017:27017 mongo:7
   ```
2. Execute `tests/test_repositorio.py`:
   ```bash
   uv run pytest tests/test_repositorio.py -ra
   ```
   - **Resultado esperado com o container ativo:** `41 passed, 0 skipped`.
3. Destrua imediatamente o container efêmero após o término:
   ```bash
   docker stop sentia-mongo-test
   ```

---

## 7. Evidências Existentes e Lacunas para Homologação (#19 e #22)

### 7.1. Resultados Efetivos das Validações Offline Executadas (`fe83ad0`)

As validações abaixo foram executadas em ambiente isolado (sandbox sem acesso à rede e sem instância MongoDB ativa) diretamente sobre o commit `fe83ad0` (`origin/developer`):

| Comando Executado | Resultado Obtido | Detalhamento |
| :--- | :---: | :--- |
| `uv lock --check` | **PASS (`0`)** | `Resolved 139 packages` — `uv.lock` íntegro e sincronizado com `pyproject.toml`. |
| `make lint` | **PASS (`0`)** | `ruff check src/apresentacao tests/test_painel_*.py` (`All checks passed!`) e `ruff check --isolated --select F,E9 .` (`All checks passed!`). |
| `uv run pytest -ra --cov=src --cov-report=term-missing` | **PASS (`0`)** | **715 coletados:** **707 passed**, **8 skipped** (todos em `tests/test_repositorio.py`), **0 failed** em `40.30s`. Cobertura total de `src/`: **94%** (`2280` statements, `130` missed). |
| `uv run pytest tests/test_painel_*.py -q` | **PASS (`0`)** | **234 passed** em `11.41s`. |
| `uv run python -m scripts.demonstrar_pipeline` | **PASS (`0`)** | `5 registros importados, classificados por mock e serializados em BSON.` |

#### Cobertura de Código por Pacote (`src/`):
- `src/apresentacao/`: `95%–100%` na maioria dos módulos (`api.py` `100%`, `contrato.py` `100%`, `dashboard.py` `100%`, `filtros.py` `100%`, `indicadores.py` `100%`, `transformacoes.py` `100%`, `administracao_api.py` `95%`, `paginas/administracao.py` `77%`).
- `src/dados/`: `database.py` `100%`, `repositorio.py` `95%`.
- `src/processamento/`: `tweetsentbr.py` `100%`, `avaliacao.py` `100%`, `baseline.py` `100%`, `rotulos.py` `100%`, `auditoria_datasets.py` `98%`, `csv_importer.py` `98%`, `xfetch.py` `96%`, `bpsad_adapter.py` `93%`, `bertweet.py` `92%`, `pipeline.py` `89%`.
- `src/servico/`: `esquemas.py` `100%`, `main.py` `100%`, `dependencias.py` `96%`, `administracao.py` `91%`, `autenticacao.py` `91%`.

---

### 7.2. Estado Atual e Lacunas de Homologação da Issue `#19` (Contrato Único de Dados)

**O que já está implementado, documentado e testado em `origin/developer` (`fe83ad0`):**
1. O documento `docs/contratos-dados.md` (atualizado até o PR `#82`) consolida em um único artefato:
   - Contrato de Aquisição (`id`, `texto`, `fonte`, `data` opcional, `rotulo_original`/`rotulo_padronizado` opcionais, `metadados` opcional).
   - Contrato de Saída da Classificação e Persistência MongoDB (`id_origem`, `fonte`, `texto_original`, `sentimento`, `probabilidades`, `modelo`, `data_processamento`, `data_publicacao`, `rotulo_original`, `rotulo_padronizado`), incluindo os 4 índices da coleção `analises`.
   - Contrato HTTP da API FastAPI para Análise e Consulta (`GET /health`, `POST /analises`, `GET /analises`, `GET /analises/resumo`) e para Administração (`POST /auth/login`, `POST /auth/logout`, `GET /datasets`, `POST /datasets`, `GET /coletas/fontes`, `POST /coletas`, `GET /coletas`, `GET /coletas/{id_coleta}`).
2. As regras do contrato estão cobertas por testes automatizados em todas as pontas (`tests/test_pipeline.py`, `tests/test_repositorio.py`, `tests/test_api.py`, `tests/test_consultas_api.py`, `tests/test_painel_fonte_api.py`, `tests/test_api_administracao.py`).

**O que ainda falta para encerrar formalmente a homologação da Issue `#19`:**
1. **Aceite formal inter-frentes (Sign-off):** Registro explícito de aprovação conjunta dos responsáveis de Dados, ML, Banco, API e PO na issue/PR de homologação, conforme seção *"Status de Homologação da Sprint 4"* do próprio `docs/contratos-dados.md`.
2. **Alinhamento semântico de `data_publicacao` vs. `data_processamento` nas consultas do painel:** `GET /analises` e `GET /analises/resumo` já filtram `inicio`/`fim` por `data_publicacao` com fallback para `data_processamento`, mas a homologação com o PO deve ratificar esse comportamento para registros importados sem data de publicação original.
3. **Política de retenção/anonimização de `texto_original` (LGPD):** O painel administrativo já mascara `@menções` na visualização (`mascarar_mencoes` em `src/apresentacao/transformacoes.py`), mas o texto bruto é persistido em `texto_original` para reprocessamento (RF04); a decisão institucional sobre curadoria/anonimização em armazenamento definitivo depende de validação com o PO.

---

### 7.3. Estado Atual e Lacunas de Homologação da Issue `#22` (Testes de Integração e QA: T09 e T10)

**O que já existe como evidência automatizada em `origin/developer` (`fe83ad0`):**
1. **Suíte `tests/test_qa_t09_t10.py` (11 funções / 19 itens — 100% passando):**
   - Cobre `T09` (validação de documento, criação dos 4 índices, deduplicação por `(id_origem, fonte)` na reexecução de `POST /analises`) e `T10` (`GET /health`, `POST /analises`, `GET /analises`, `GET /analises/resumo`, validações `422` e falhas sanitizadas `503`).
2. **Suítes `tests/test_api.py` (17 itens) e `tests/test_consultas_api.py` (48 itens) — 100% passando:**
   - Provam em memória que o contrato de `POST /analises`, `GET /analises` e `GET /analises/resumo` conversa sem divergências com `RepositorioAnalises` e com o cliente `FonteApi` do Dashboard Streamlit.

**O que ainda falta para homologação de integração real completa (#22 e fluxo ponta a ponta):**
1. **Execução homologada dos 8 testes de `tests/test_repositorio.py` contra instância MongoDB ativa na CI ou em sessão registrada:** Na CI padrão (`.github/workflows/ci.yml`), não há container `mongo` configurado em `services:`, de modo que os 8 testes de banco real ficam `SKIPPED`.
2. **Teste de fumaça ponta a ponta com pesos reais do BERTweet (`--group ml`) + MongoDB ativo:** Em `tests/test_api.py` e `tests/test_qa_t09_t10.py`, `obter_classificador` e `obter_colecao_analises` são sobrescritos via `app.dependency_overrides`. Um teste de homologação final com `uvicorn` + `mongod` + pesos reais do `pysentimiento/bertweet-pt-sentiment` deve ser registrado como evidência de ambiente integrado.
3. **Unificação da persistência entre a API de Administração (`src/servico/administracao.py`) e o MongoDB (`src/dados/repositorio.py`):**
   - Atualmente, `POST /analises` grava no MongoDB via `RepositorioAnalises`, e `GET /analises` + `GET /analises/resumo` leem do MongoDB.
   - Contudo, as rotas administrativas (`POST /datasets` e `POST /coletas` em `src/servico/administracao.py`) utilizam `RepositorioAdministracao` **em memória** e não gravam os registros analisados na coleção `analises` do MongoDB (nem expõem ainda `XFetch` em `GET /coletas/fontes`). Assim, uma coleta disparada pelo painel de Administração ainda não popula automaticamente a coleção MongoDB lida pelo Dashboard público quando `SENTIA_FONTE_DADOS=api`.
