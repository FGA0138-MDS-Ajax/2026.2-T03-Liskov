# TweetSentBR — Corpus Inicial de Aquisição e Auditoria Técnica (Issues #1 e #3)

## 1. Descrição e Papel no SentIA

O **TweetSentBR** (Brum & Volpe Nunes, LREC 2018) é utilizado pelo SentIA como **fonte inicial para o módulo de aquisição automatizada de textos em português brasileiro (RF02 / US02 — Issue #1)**.

> [!IMPORTANT]
> **Escopo de uso autorizado (Aquisição vs. Avaliação de ML):**
> - **Uso autorizado (Issue #1 — RF02/US02):** Carregamento automatizado de textos na camada de aquisição (`adquirir_dados` / `carregar_tweetsentbr`) e validação do pipeline de ingestão.
> - **Restrição para avaliação de ML (Issue #3 / Issue #17):** O arquivo `Datasets/tweetsent.csv` **não deve ser utilizado integralmente como dataset independente de avaliação** do modelo `pysentimiento/bertweet-pt-sentiment`, pois esse checkpoint foi ajustado (*fine-tuned*) sobre o próprio TweetSentBR e o arquivo local não contém a coluna de partição oficial (`split: train/test`) nem os IDs originais dos tweets para isolar o conjunto de teste, o que causaria vazamento de dados (*data leakage*).

---

## 2. Localização e Resolução de Caminho

O arquivo está armazenado na raiz do repositório em:

```text
Datasets/
└── tweetsent.csv
```

- **Convenção oficial (case-sensitive no Linux):** `Datasets/tweetsent.csv` (com `D` maiúsculo).
- O módulo [`src/processamento/aquisicao/tweetsentbr.py`](../src/processamento/aquisicao/tweetsentbr.py) resolve `CAMINHO_PADRAO_TWEETSENTBR` em relação à raiz do projeto (`Path(__file__).resolve().parents[3]`), funcionando independentemente do diretório de trabalho atual (`cwd`). Por compatibilidade, `resolver_caminho_tweetsentbr()` também resolve referências relativas em minúsculas (`datasets/tweetsent.csv`).

---

## 3. Como Executar a Aquisição e a Importação

### 3.1. Preparação do Ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.2. Aquisição Automatizada do Corpus Inicial (Issue #1 — RF02/US02)

```python
from src.processamento.aquisicao import (
    adquirir_dados,
    carregar_tweetsentbr,
    iterar_tweetsentbr,
    converter_rotulo_para_sentia,
)

# Carregamento completo usando o caminho padrão relativo à raiz do projeto
registros = adquirir_dados()

# Ou carregamento com limite em modo streaming (sem ler o arquivo inteiro)
primeiros_10 = carregar_tweetsentbr(limite=10)
for reg in iterar_tweetsentbr(limite=5):
    rotulo_sentia = converter_rotulo_para_sentia(reg["rotulo_padronizado"])
    print(reg["id_origem"], reg["rotulo_padronizado"], "->", rotulo_sentia)
```

### 3.3. Importação Genérica de Arquivos CSV (Issue #2 — RF01/US01)

```python
from src.processamento.aquisicao import importar_dataset_csv, RelatorioImportacao

relatorio = RelatorioImportacao()
registros = importar_dataset_csv(
    "Datasets/tweetsent.csv",
    modo_estrito=True,
    relatorio=relatorio,
)
print(f"Lidos: {relatorio.total_lidos} | Importados: {relatorio.total_importados}")
```

---

## 4. Auditoria Programática Reproduzível (`Datasets/tweetsent.csv`)

Para reproduzir integralmente os números abaixo a qualquer momento, execute:

```bash
python scripts/auditar_datasets.py Datasets/tweetsent.csv
```

### 4.1. Métricas Gerais e Integridade Estrutural

| Propriedade Auditada | Valor Verificado |
|---|---|
| **Caminho canônico** | `Datasets/tweetsent.csv` |
| **Tamanho do arquivo** | `861.743` bytes |
| **Hash SHA-256** | `8b7be5d0a6bb982c99bf0613ac71f9f8eed49849586a5019b2db2094a6136060` |
| **Codificação detectada** | `UTF-8-SIG` (UTF-8 com BOM) |
| **Colunas presentes** | `texto`, `rotulo`, `fonte` |
| **Coluna de ID original do tweet** | Ausente (`id_origem` determinístico gerado pelo SentIA) |
| **Coluna de data de publicação** | Ausente (`data_publicacao = None` nos 8.530 registros) |
| **Coluna de partição (`split`)** | Ausente (sem separação entre treino e teste) |
| **Total de registros lidos** | `8.530` |
| **Total de registros importados** | `8.530` (modo estrito e modo tolerante) |
| **Total de registros descartados** | `0` (zero textos vazios ou campos nulos em `texto`, `rotulo`, `fonte`) |

### 4.2. Distribuição por Classe

| Rótulo Original (`rotulo_original`) | Rótulo de Aquisição (`rotulo_padronizado`) | Rótulo de Fronteira SentIA | Quantidade | Proporção (%) |
|---|---|---|---:|---:|
| `positivo` | `POS` | `positivo` | 3.953 | 46,34% |
| `negativo` | `NEG` | `negativo` | 2.403 | 28,17% |
| `neutro` | `NEU` | `neutro` | 2.174 | 25,49% |
| **Total** | — | — | **8.530** | **100,00%** |

---

## 5. Análise de Duplicatas e Rótulos Conflitantes

Conforme diretriz de governança de dados, **nenhum registro foi removido silenciosamente do arquivo original**. A auditoria identificou:

| Critério de Duplicidade | Textos Únicos | Grupos Duplicados | Registros Envolvidos | Ocorrências Excedentes | Grupos com Rótulos Conflitantes |
|---|---:|---:|---:|---:|---:|
| **Exata (`texto_original` idêntico)** | 8.495 | 21 | 56 | 35 | **5** (12 registros) |
| **Normalizada (`lowercase` + espaços colapsados)** | 8.481 | 30 | 79 | 49 | **12** (28 registros) |

### 5.1. Identificação Estável dos Grupos com Rótulos Conflitantes

Para preservar a privacidade e evitar redistribuição desnecessária de textos de usuários em relatórios técnicos, cada grupo conflitante é identificado pelo hash SHA-256 curto do texto normalizado e pelos identificadores determinísticos (`id_origem`) gerados pelo importador:

| # | Hash do Texto (Normalizado) | Rótulos em Conflito | Posições e `id_origem` dos Registros Afetados | Conflito Exato? |
|---:|---|---|---|---|
| 1 | `f68ef1252708` | `NEU`, `POS` | `#263` (`TweetSentBR_000263_813e105164b8`=`POS`), `#5458` (`TweetSentBR_005458_88a1ba17e33a`=`NEU`) | Sim (`84c24db0865a`) |
| 2 | `60d06b7f6d8d` | `NEU`, `POS` | `#319` (`TweetSentBR_000319_dfb97982cce8`=`POS`), `#5657` (`TweetSentBR_005657_a799546e034b`=`NEU`) | Sim (`c9aadba8b240`) |
| 3 | `1c2bce9529aa` | `NEU`, `POS` | `#383` (`TweetSentBR_000383_257c2542a497`=`POS`), `#1572` (`TweetSentBR_001572_6c5ed2b05072`=`NEU`), `#4481` (`TweetSentBR_004481_5d9346fa4a0a`=`NEU`), `#6466` (`TweetSentBR_006466_6bd8dd67a8e9`=`NEU`) | Sim (`250b9a768586`) |
| 4 | `784552008df5` | `NEG`, `NEU`, `POS` | `#423` (`TweetSentBR_000423_2b10d3c2f0a8`=`POS`), `#6163` (`TweetSentBR_006163_e9ea07fc2378`=`NEG`), `#8454` (`TweetSentBR_008454_061c960bcb2a`=`NEU`) | Sim (`4961964ad72d` entre `#423` e `#8454`) |
| 5 | `fe3363d661c9` | `NEU`, `POS` | `#920` (`TweetSentBR_000920_2169c3f1ff0a`=`NEU`), `#3554` (`TweetSentBR_003554_7d96fd00538d`=`NEU`), `#5099` (`TweetSentBR_005099_19481fbc62f9`=`POS`) | Não (diferença de caixa/espaço) |
| 6 | `13097b3a2190` | `NEU`, `POS` | `#1233` (`TweetSentBR_001233_3b69cc2497ba`=`POS`), `#5643` (`TweetSentBR_005643_8a3ceb1db75e`=`NEU`) | Não (diferença de caixa/espaço) |
| 7 | `87db703e4095` | `NEU`, `POS` | `#1242` (`TweetSentBR_001242_43536159b082`=`POS`), `#6605` (`TweetSentBR_006605_a205518b5c16`=`NEU`) | Não (diferença de caixa/espaço) |
| 8 | `406f5c171d3c` | `NEU`, `POS` | `#1401` (`TweetSentBR_001401_f1f6033767d3`=`POS`), `#6216` (`TweetSentBR_006216_a482e9f2675e`=`NEU`) | Não (diferença de caixa/espaço) |
| 9 | `a9a8e39b180f` | `NEU`, `POS` | `#1459` (`TweetSentBR_001459_cc8b9ba3c04b`=`POS`), `#7218` (`TweetSentBR_007218_6a0207723ebe`=`NEU`) | Não (diferença de caixa/espaço) |
| 10 | `13a5643f5127` | `NEG`, `NEU` | `#2206` (`TweetSentBR_002206_ff3d72f61fd4`=`NEG`), `#5234` (`TweetSentBR_005234_73a933a2997a`=`NEU`) | Não (diferença de caixa/espaço) |
| 11 | `1b68593f0cfa` | `NEU`, `POS` | `#2711` (`TweetSentBR_002711_3584235871ee`=`POS`), `#3623` (`TweetSentBR_003623_e3abe506a8cb`=`NEU`), `#4068` (`TweetSentBR_004068_d093cf6e4bd4`=`NEU`), `#5441` (`TweetSentBR_005441_9e5d8848aa44`=`POS`) | Não (diferença de caixa/espaço) |
| 12 | `e983a73450ca` | `NEU`, `POS` | `#4294` (`TweetSentBR_004294_8a6ec7f769d6`=`NEU`), `#6060` (`TweetSentBR_006060_a1d8dfdb6663`=`POS`) | Sim (`16fb93e13183`) |

### 5.2. Política Sugerida de Curadoria (Pendente de Aceite da PO)

1. **Na camada de Aquisição (Issue #1):** Preservar os `8.530` registros originais para fidelidade ao arquivo de entrada, permitindo auditoria transparente.
2. **Em Treinamento/Avaliação (Issue #17):**
   - Desduplicar registros unânimes mantendo apenas a primeira ocorrência (`30` duplicatas exatas unânimes).
   - Excluir ou submeter a voto majoritário os `12` grupos com rótulos conflitantes, pois textos idênticos com classes contraditórias introduzem ruído irredutível no cálculo de Acurácia e Macro-F1.

---

## 6. Procedência, Licença e Privacidade (Pendência de Governança para a PO)

1. **Publicação original:** Brum, Henrico B.; Volpe Nunes, Maria das Graças. *"Building a Sentiment Corpus of Tweets in Brazilian Portuguese"*, Proceedings of the Eleventh International Conference on Language Resources and Evaluation (LREC 2018). Repositórios de referência: `HBrum/tweetsentbr` (Bitbucket) e `brasileiras-pln/tweetSentBR` (GitHub).
2. **Condições de distribuição da fonte:** Em conformidade com a política de desenvolvedores do Twitter/X (*Developer Agreement and Policy*), a distribuição oficial do TweetSentBR disponibiliza apenas os **identificadores numéricos dos tweets (`tweet_id`) e os respectivos rótulos**, exigindo hidratação local via script autorizado (`get_ttsbr.py`).
3. **Situação do arquivo `Datasets/tweetsent.csv` no repositório:** O arquivo adicionado no PR #40 contém `8.530` textos já hidratados (com `@menções` de usuários) e sem os `tweet_id` originais.
4. **Recomendação técnica e decisão pendente da PO:**
   - **Não versionar novas cópias públicas** de textos hidratados do Twitter/X.
   - Submeter à decisão da Product Owner e da coordenação da disciplina se o arquivo `Datasets/tweetsent.csv` deve ser removido do versionamento Git público em um PR dedicado (mantendo-o apenas localmente em `Datasets/tweetsent.csv` listado no `.gitignore` e mantendo no Git uma fixture sintética/anonimizada para a CI).
