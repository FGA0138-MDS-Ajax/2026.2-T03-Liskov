# Experimentos BPSAD — entrega em PR e limites científicos

Referência documental: 09/11/2026. O [PR #64](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/64)
continua aberto, branch `feat/integrar-classificador`, head consultado
`3da81d5e65a1850374145741a62106aafd531ea0`, com correção #67 incorporada.
**Esses scripts e o grupo `experimentos` não existem no SHA PC1 `bfaf7da`.**
Não executar seus comandos neste checkout.

O [guia completo no SHA do PR](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/3da81d5e65a1850374145741a62106aafd531ea0/docs/experimentos_bpsad.md)
documenta `scripts/experimentos/`, wrappers antigos, amostragem com seed/cotas,
deduplicação e exclusão de conflitos, partições sem sobreposição e avaliação
baseline por padrão; BERTweet real é opt-in. A correção usa SQLite temporário
exclusivo, preserva arquivos existentes e registra hash/parâmetros/versões.

Para reprodução **somente em checkout separado daquele SHA**, os comandos do guia são:

```bash
uv sync --locked --group experimentos
uv run python -m scripts.experimentos.amostrar_bpsad --help
uv run python -m scripts.experimentos.validar_bpsad --help
uv run pytest tests/test_experimentos_bpsad.py tests/test_classificacao.py tests/test_pipeline.py -v -ra
```

O corpus real fica local, fora do Git. Os arquivos de saída devem ser novos e os
diretórios devem existir. Preservar o relatório de amostragem, não inferir sua seed
a partir do CSV. Para BERTweet, preparar grupos ML/experimentos e usar `--bertweet`
conforme o guia. Esses comandos não foram executados nesta revisão documental.

| Métrica declarada pelo autor no #64 | TF-IDF + LogReg | BERTweet |
|---|---:|---:|
| Acurácia | 70,10% | 67,70% |
| F1 macro | 59,65% | 55,43% |

**Não reproduzidas nesta revisão.** O BPSAD completo/pesos não foram usados.
Separação interna treino/teste não prova independência do pré-treinamento do
checkpoint. Mudanças de cotas e validação podem mudar a amostra e seus resultados;
não atribuir números antigos ao código corrigido. Tempo/RSS observados não são
benchmark controlado nem medida de pico de memória.

O [relatório histórico](qa/pc1/RELATORIO_FINAL_CODEX.md) registra testes sintéticos
de `1cd636e` e da integração anterior `480ecf1`. Os resultados da referência PC1
selecionada estão no [ensaio atual](qa/pc1/RELATORIO_ENSAIO_FINAL.md).
Aceite científico e de RNF01/#17 continuam pendentes com ML/PO.
