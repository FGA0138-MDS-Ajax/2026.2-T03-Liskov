# Reprodução exploratória BPSAD — correção do PR #64

Os scripts estão em `scripts/experimentos/`. As entradas antigas
`amostrar_bpsad.py` e `scripts/validar_bpsad.py` são wrappers de compatibilidade.
O head do autor antecede a migração uv; os arquivos `pyproject.toml`, `uv.lock` e
`.python-version` foram trazidos da developer auditada, acrescentando somente o
grupo opcional `experimentos` com psutil. Requirements antigos são preservados
nesta branch histórica; na integração com developer prevalece o gerenciamento uv.

```bash
uv sync --locked --group experimentos
uv run python -m scripts.experimentos.amostrar_bpsad --help
uv run python -m scripts.experimentos.amostrar_bpsad --entrada data/BPSAD/concatenated.csv --saida data/BPSAD/amostra_pc1.csv --tamanho 10000 --semente 42
uv run --group experimentos python -m scripts.experimentos.validar_bpsad --entrada data/BPSAD/amostra_pc1.csv --saida data/BPSAD/avaliacao_pc1.json
```

Diretórios de saída devem existir; arquivos existentes e caminhos coincidentes
são recusados. Não há opção de sobrescrita. A amostragem usa SQLite em diretório
exclusivo e o limpa mesmo se a leitura falhar. Textos completos ficam somente em
arquivos locais; não publicar corpus ou respostas reais como evidência de QA.

Padrões: seed 42, amostra 10.000, bloco 50.000, teste 20%. Cada classe precisa
ter pelo menos dois grupos e aparecer em ambas as partições; uma amostra pequena
ou extremamente desbalanceada pode ser recusada com mensagem para ajuste.
O JSON registra parâmetros, versões, distribuições, descartes e conflitos.
A avaliação valida classes/divisões e rejeita duplicatas/vazamento entre partições;
registra hash SHA-256 do CSV. A seed não pode ser deduzida do CSV: preservar o JSON
produzido pela amostragem junto com o arquivo. Tempos e RSS não são benchmarks
controlados. RSS não mede pico de memória.

Para BERTweet real, preparar separadamente `uv sync --locked --group experimentos
--group ml` e acrescentar `--bertweet` à avaliação. Essa opção pode baixar pesos;
não foi executada nesta auditoria. A avaliação padrão executa somente o baseline.

## Mudanças com efeito científico

Mantidos: agrupamento NFKC/casefold/espaços, exclusão total de grupos com rótulos
conflitantes, reservatório por classe e divisão estratificada sem sobreposição.
Corrigidos: arredondamento independente (podia produzir tamanho diferente),
ordem das colunas de entrada, cotas com mínimo de dois grupos, validação de notas
inteiras 1–5 e preservação de espaços do texto original. Classes são percorridas
em ordem explícita. As cotas mínimas podem alterar a proporção de classes raras;
por isso resultados anteriores não são diretamente atribuíveis à nova amostra.
Não há promessa de independência em relação ao pré-treinamento do BERTweet.

| Métrica declarada pelo autor | TF-IDF + LogReg | BERTweet |
|---|---:|---:|
| Acurácia | 70,10% | 67,70% |
| F1 macro | 59,65% | 55,43% |

Esses números **não foram reproduzidos nesta auditoria**. Não houve acesso ao
BPSAD completo nem execução com pesos reais. Não foram alterados.
Testes obrigatórios usam corpus sintético temporário e não exigem psutil/ML:

```bash
uv run pytest tests/test_experimentos_bpsad.py tests/test_classificacao.py tests/test_pipeline.py -v -ra
```
