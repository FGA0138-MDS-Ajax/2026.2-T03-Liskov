# Contratos de Dados — Aquisição, Pipeline ML, MongoDB e Painel

Resumo consolidado dos contratos de dados implementados no código para o PC1 e da proposta de contrato HTTP entre frontend e backend ([issue #19](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/19)).

## 1. Contrato de Aquisição e Pipeline (`src/processamento/`)

Os módulos de aquisição (`csv_importer.py`, `tweetsentbr.py`, `bpsad_adapter.py` e `xfetch.py`) produzem dicionários padronizados que alimentam `PipelineClassificacao.processar_registros()`.

| Campo | Saída da Aquisição | Saída do Pipeline (Documento BSON) | Regra de Contrato |
|---|---|---|---|
| `id_origem` | `str` não vazia | `str` preservada | Identificador original ou hash determinístico SHA-256 por fonte/posição |
| `fonte` | `str` não vazia | `str` preservada | Proveniência do registro (`tweetsentbr`, `bpsad`, `X`, etc.) |
| `texto_original` | `str` não vazia | `str` preservada | Texto bruto enviado ao BERTweet sem stemming ou remoção de stopwords |
| `rotulo_original` | `str \| None` | `str` (omitido se `None`) | Rótulo original do dataset ou nota original (nunca inferência do modelo) |
| `rotulo_padronizado` | `"POS" \| "NEG" \| "NEU" \| None` | `"positivo" \| "negativo" \| "neutro"` (omitido se `None`) | Rótulo humano convertido por `converter_rotulo_para_sentia()` |
| `sentimento` | *Não criado na aquisição* | `"positivo" \| "negativo" \| "neutro"` | Previsão produzida pelo classificador de sentimentos |
| `probabilidades` | *Não criado na aquisição* | `dict[str, float]` (`positivo`, `negativo`, `neutro`) | Valores finitos em `[0, 1]` com soma `1.0 ± 0.001` |
| `modelo` | *Não criado na aquisição* | `{"nome": str, "versao": str \| None}` | Identificação do modelo responsável pela inferência |
| `data_publicacao` | `str \| None` | `datetime` UTC (omitido se `None`) | Data original da publicação; não é inventada quando ausente na fonte |
| `data_processamento` | *Não criado na aquisição* | `datetime` UTC | Timestamp da execução do pipeline |
| `metadados` | `dict[str, str]` opcional | `dict` copiado quando não vazio | Colunas extras do CSV ou metadados da coleta XFetch (`autor_id`, `conversa_id`, métricas) |

### Particularidades por Fonte
- **CSV Genérico (`csv_importer.py`)**: aceita UTF-8 (com ou sem BOM), exige `texto` (ou `texto_original`) e `fonte`. Possui modo estrito (`importar_dataset_csv`) e modo tolerante com `RelatorioImportacao` (`importar_dataset_csv_com_relatorio`).
- **BPSAD (`bpsad_adapter.py`)**: mapeia `review_text`, `rating`, `dataset`, `review_id` e `review_date`. Notas de 1 a 5 são convertidas em sentimento (`< 2.5` → `NEG`, `< 3.5` → `NEU`, `>= 3.5` → `POS`).
- **TweetSentBR (`tweetsentbr.py`)**: lê o corpus local e normaliza classes para `POS`, `NEG` e `NEU`.
- **XFetch (`xfetch.py`, PR #65)**: coleta paginada com limite de páginas (`max_pages`), `rotulo_original=None`, `rotulo_padronizado=None`, `fonte="X"` e integração validada com `PipelineClassificacao` em `tests/test_xfetch_pipeline.py`.

## 2. Contrato do Painel e API Proposta (`src/apresentacao/contrato.py`)

O painel Streamlit opera sobre dataclasses imutáveis em [`src/apresentacao/contrato.py`](../src/apresentacao/contrato.py) e sobre o contrato HTTP proposto em [`docs/frontend/CONTRATO-API.md`](frontend/CONTRATO-API.md):

- **Consulta e Dashboard**: `Analise`, `PaginaAnalises`, `ResumoAnalises` e `FiltrosAnalises` (`data_inicio`, `data_fim`, `sentimento`).
- **Administração**: `SessaoAdministrador` (com `token` oculto no `repr` e `expira_em` UTC), `ResultadoImportacao`, `FonteColeta` e `Coleta` (`em_andamento`, `concluida`, `falhou`).
- **Estado atual da API (`src/servico/main.py`)**: apenas `GET /health` está implementado no servidor FastAPI. Enquanto as rotas de análises e administração não forem implementadas no backend (#19, #21, #23–#25, #58), o painel deve ser demonstrado com `SENTIA_FONTE_DADOS=mock`.
