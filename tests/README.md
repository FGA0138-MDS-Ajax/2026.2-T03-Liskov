# Suíte de testes do SentIA

Este diretório contém os testes automatizados do projeto. A suíte cobre aquisição e importação de dados, pipeline e classificação, serviço HTTP, persistência MongoDB, pesquisa híbrida e interface Streamlit.

## 1. Configuração

Na raiz do repositório, instale as dependências de desenvolvimento:

```bash
uv sync --locked
```

A configuração do Pytest está em `pytest.ini`:

- `testpaths = tests`
- `pythonpath = .`

As fixtures compartilhadas ficam em `tests/conftest.py`; arquivos pequenos de entrada e casos controlados ficam em `tests/fixtures/`.

## 2. Executar os testes

```bash
# Suíte completa
uv run pytest -ra --cov=src --cov-report=term-missing

# Apenas testes da interface
uv run pytest tests/test_painel_*.py -q

# Testes de persistência e repositório
uv run pytest tests/test_database.py tests/test_repositorio.py tests/test_persistencia_leitura.py -ra

# Testes do pipeline e classificação
uv run pytest tests/test_pipeline.py tests/test_classificacao.py tests/test_avaliacao.py -ra
```

Verificações equivalentes às principais etapas do workflow de CI:

```bash
uv run ruff check src/apresentacao tests/test_painel_*.py
uv run ruff check --isolated --select F,E9 .
uv lock --check
```

O atalho `make check` reúne as verificações disponíveis no `Makefile`.

## 3. Dependência de MongoDB

A CI da branch `developer` provisiona um serviço `mongo:7` e define `MONGODB_URI_TESTE`. Os testes de banco/repositório precisam de uma instância MongoDB acessível para reproduzir esse cenário.

Em execução local sem `MONGODB_URI_TESTE` ou sem MongoDB acessível, os testes que dependem do serviço podem ser ignorados (*skipped*), conforme as fixtures e condições da suíte. Portanto, não é correto descrever toda a suíte atual como 100% offline.

## 4. Organização por área

Os módulos permanecem diretamente em `tests/` para manter descoberta simples e preservar os imports/fixtures compartilhados. A categorização abaixo é temática; não representa marcadores Pytest nem subpastas configuradas.

| Área | Módulos de teste |
|---|---|
| Aquisição, importação e auditoria | `test_aquisicao.py`, `test_auditoria_datasets.py`, `test_csv_importer.py`, `test_importacao.py` |
| Classificação e pipeline | `test_analisar_em_lotes.py`, `test_avaliacao.py`, `test_classificacao.py`, `test_comparar_modelos.py`, `test_pipeline.py`, `test_experimentos_bpsad.py` |
| API e serviço | `test_api.py`, `test_api_administracao.py`, `test_consultas_api.py`, `test_integracao_conjunta.py` |
| Persistência e pesquisa | `test_database.py`, `test_repositorio.py`, `test_persistencia_leitura.py`, `test_pesquisa_hibrida.py` |
| Apresentação Streamlit | `test_painel_administracao.py`, `test_painel_arquitetura.py`, `test_painel_config.py`, `test_painel_filtros.py`, `test_painel_fonte_api.py`, `test_painel_fonte_mock.py`, `test_painel_transformacoes.py`, `test_painel_ui.py` |
| XFetch | `test_xfetch.py`, `test_xfetch_pipeline.py` |
| QA/regressão | `test_qa_t09_t10.py` |

## 5. Fixtures e dados de teste

- `conftest.py`: fixtures compartilhadas e configuração da suíte.
- `fixtures/bpsad_sample.csv`: amostra sintética/controlada para testes do adaptador BPSAD.
- `fixtures/dataset_invalido.csv`, `dataset_valido.csv` e `dataset_vazio.csv`: cenários de importação CSV.

Os datasets de teste não devem ser confundidos com os corpora versionados em `Datasets/`.

## 6. Observações de manutenção

- Não mover testes para `unitarios/`, `integracao/` e `sistema/` sem ajustar `pytest.ini`, imports, caminhos de fixtures, comandos do Makefile e workflow da CI.
- Não remover testes só por nomes parecidos; comparar cenários, asserts e cobertura antes de consolidar.
- Testes de inferência BERTweet e chamadas externas devem continuar controlados por dublês/mocks para não exigir download de pesos nem consumo de API paga na suíte padrão.
- Os resultados históricos registrados em `docs/qa/` estão vinculados ao commit/ambiente em que foram gerados. Sempre identificar o SHA ao citar contagens de testes e cobertura.
