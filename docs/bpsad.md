# BPSAD — Brazilian Portuguese Sentiment Analysis Dataset (Issue #3)

## 1. Descrição e Papel no SentIA

O **BPSAD** (*Brazilian Portuguese Sentiment Analysis Dataset*) reúne avaliações de produtos e aplicativos em português brasileiro oriundas de múltiplas plataformas (*B2W*, *Buscapé*, *Olist*, *Mercado Livre* e *UTLC*).

Referência: integração PC1 `bfaf7da`, 09/11/2026. A implementação disponível
é o adaptador e a auditoria; experimentos completos do #64 estão fora deste SHA.

No projeto SentIA, o BPSAD é utilizado ou proposto para:

1. **Validação de escala e streaming do módulo de importação (Issue #2):** Processamento de grandes volumes via [`iterar_bpsad`](../src/processamento/aquisicao/bpsad_adapter.py) e [`iterar_dataset_csv`](../src/processamento/aquisicao/csv_importer.py) sem materializar milhões de registros em memória.
2. **Fonte candidata à avaliação em outro domínio (Issues #3/#17):** avaliações de produtos diferem de tweets, mas isso não comprova independência em relação ao pré-treinamento. É necessário auditar proveniência, licença, duplicatas e partições. Notas `rating` de 1 a 5 são convertidas em `NEG`, `NEU` e `POS`; são rótulos indiretos, não previsões.

---

## 2. Obtenção e Armazenamento Local

Devido ao seu tamanho (~2,8 milhões de registros no arquivo consolidado `concatenated.csv`), **o dataset completo do BPSAD jamais deve ser versionado no GitHub**.

1. **Fonte oficial:** https://github.com/paulobio/BPSAD
2. **Armazenamento local recomendado:** manter o arquivo fora do controle de versão (por exemplo, em um diretório local externo ou ignorado pelo Git) e informar seu caminho ao importador ou ao script de auditoria.
3. **Amostra sintética versionada para testes automatizados:** Para execução offline da suíte de testes e da CI, o repositório inclui a fixture sintética [`tests/fixtures/bpsad_sample.csv`](../tests/fixtures/bpsad_sample.csv) (5 registros sintéticos cobrindo notas de 1 a 5 e metadados `review_id`, `review_date`, `category`, sem redistribuir textos reais de terceiros).

---

## 3. Estado da Validação e Auditoria Técnica

### 3.1. Números Declarados para o Corpus Completo (`concatenated.csv`)

Na entrega inicial da documentação (PR #40), foram declarados os seguintes números a partir de execução local em modo tolerante (`modo_estrito=False`) sobre `concatenated.csv`:

| Métrica Declarada | Valor Informado | Status de Auditoria |
|---|---:|---|
| Registros importados | `2.786.073` | **Declarado pela equipe (pendente de log/hash SHA-256)** |
| Registros descartados | `19` | **Declarado pela equipe (pendente de log/hash SHA-256)** |
| Motivo dos descartes | `texto_vazio` (`19`) | **Declarado pela equipe** |

> [!NOTE]
> Como o arquivo `concatenated.csv` (~2,8 milhões de linhas) não fica armazenado no repositório Git, os números acima permanecem classificados como **declarados pela equipe** até que o relatório JSON gerado pelo script `scripts/auditar_datasets.py` (incluindo o hash SHA-256 do arquivo local) seja anexado pela equipe na issue/PR correspondente.

### 3.2. Validação Reproduzida sobre a Fixture Sintética (`tests/fixtures/bpsad_sample.csv`)

Executando o auditor reprodutível sobre a amostra sintética versionada:

```bash
uv run python -m scripts.auditar_datasets tests/fixtures/bpsad_sample.csv
```

- **Total lidos:** `5` | **Total importados:** `5` | **Total descartados:** `0`
- **Distribuição por classe (`rotulo_padronizado`):** `POS: 2` (notas 5 e 4), `NEU: 1` (nota 3), `NEG: 2` (notas 2 e 1)
- **Preservação de `id_origem` (`review_id`) e `data_publicacao` (`review_date`):** 100% (`5/5` registros)

---

## 4. Como Reproduzir a Auditoria do BPSAD Completo em Streaming

O script [`scripts/auditar_datasets.py`](../scripts/auditar_datasets.py) processa o arquivo em fluxo (`iterar_dataset_csv`) e calcula o hash SHA-256 em blocos de 64 KB, sem carregar a base inteira na memória RAM.

Para auditar o `concatenated.csv` completo localmente sem sobrecarga de memória, utilize a flag `--sem-duplicatas`:

```bash
uv run python -m scripts.auditar_datasets /caminho/para/concatenated.csv --sem-duplicatas > relatorio_bpsad.json
```

O arquivo `relatorio_bpsad.json` gerado conterá:
- `sha256`, `tamanho_bytes` e `codificacao`;
- `total_lidos`, `total_importados`, `total_descartados` e `descartes_por_motivo`;
- `contagem_por_classe` (`POS`, `NEG`, `NEU`) e `proporcao_por_classe`;
- `contagem_rotulo_original` (notas `1` a `5`).

---

## 5. Exemplo de Uso Programático em Streaming

```python
from src.processamento.aquisicao import (
    RelatorioImportacao,
    converter_rotulo_para_sentia,
    iterar_bpsad,
)

relatorio = RelatorioImportacao()

for indice, registro in enumerate(
    iterar_bpsad(
        "tests/fixtures/bpsad_sample.csv",
        modo_estrito=False,
        relatorio=relatorio,
    ),
    start=1,
):
    rotulo_ml = converter_rotulo_para_sentia(registro["rotulo_padronizado"])
    print(
        f"#{indice} id={registro['id_origem']} "
        f"fonte={registro['fonte']} "
        f"nota={registro['rotulo_original']} -> {registro['rotulo_padronizado']} ({rotulo_ml})"
    )

print("Importados:", relatorio.total_importados)
print("Descartados:", relatorio.total_descartados)
print("Motivos:", relatorio.descartes_por_motivo)
```

## 6. Contrato e alcance das evidências

`review_text` → `texto_original`, `rating` → `rotulo_original` e sigla em
`rotulo_padronizado`, `dataset` → `fonte`, `review_id` → `id_origem`,
`review_date` → `data_publicacao`. Extras como `category` vão para `metadados`.
Ausência de publicação não autoriza usar processamento como substituto.
O adaptador não produz `sentimento` nem `probabilidades`; isso cabe ao classificador.
Ver [contratos](contratos-dados.md).

A amostra de cinco linhas é sintética. Contagens históricas do corpus completo
são declaradas pelo autor do PR #40, sem hash/log suficiente para validação
independente nesta tarefa. Resultados atuais de testes estão no
[ensaio por SHA/data](qa/pc1/RELATORIO_ENSAIO_FINAL.md).
[Experimentos #64](experimentos_bpsad.md) e métricas declaradas não foram
reproduzidos sobre o corpus real nesta revisão.
