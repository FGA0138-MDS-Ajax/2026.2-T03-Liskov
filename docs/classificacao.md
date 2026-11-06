> Atualização de 06/11/2026: o pipeline CSV está implementado e a homologação conjunta com as correções de validação está registrada em [QA dos PRs #44 e #45](qa/pr44-pr45/relatorio.md). Os números e pendências das seções abaixo são históricos da entrega inicial, não o estado atual da integração.

# Classificação de sentimentos

## Componente e uso

O classificador está em `src/processamento/classificacao/bertweet.py`.

```python
from src.processamento.classificacao.bertweet import ClassificadorBertweet

classificador = ClassificadorBertweet()
resultados = classificador.prever_com_probabilidades(
    ["Adorei o atendimento!", "A entrega atrasou muito."]
)
print(resultados)
```

Reutilizar a instância para evitar carregar o modelo a cada chamada.
A primeira inicialização baixa os arquivos do modelo para o cache do
Hugging Face. Os pesos não devem ser versionados no Git.

Modelo declarado: `pysentimiento/bertweet-pt-sentiment`.
A revisão exata do checkpoint ainda precisa ser fixada.

## Entrada e saída

Aceita uma string ou uma coleção de strings não vazias.
Coleção vazia retorna lista vazia. Tipos inválidos e textos vazios
são rejeitados. O tamanho do lote deve ser inteiro positivo.

A saída preserva a ordem e contém `sentimento` e `probabilidades`
para as classes `positivo`, `negativo` e `neutro`.

## Preparação textual — issues #5 a #8

O classificador encaminha os textos ao analisador PySentimiento.
Não aplica externamente remoção de stopwords, stemming ou TF-IDF.

Preservar palavras como "não" mantém informações de negação.
Dispensar stemming externo preserva as palavras para o tokenizador.
O detalhamento das normalizações internas da biblioteca permanece pendente.

O baseline TF-IDF com regressão logística está separado em `baseline.py`.
Seu vetorizador deve ser ajustado somente no conjunto de treino.

A revisão dos requisitos originais depende de aceite da PO.

## Evidências de execução

Ambiente local: Windows e Python 3.13.5.

Após a integração dos arquivos:
- 126 testes aprovados.
- 14 testes de aquisição pulados por ausência de funções compatíveis
  com o contrato procurado pelos testes (#1/RF02).
- Nenhum teste falhou.

Antes da mudança de pasta, o modelo real produziu:

| Texto | Sentimento | Probabilidade da classe |
| --- | --- | --- |
| Adorei o atendimento! | positivo | 0.992056 |
| A entrega atrasou muito. | negativo | 0.932464 |
| O produto chegou hoje. | neutro | 0.878978 |

Essa demonstração confirma carregamento e inferência.
Não representa medição de acurácia ou avaliação independente.

## Pendências

- Avaliação independente e comparação com baseline (#17).
- Pipeline de registros com IDs, fonte e metadados (#9).
- Fixação da revisão do modelo e das versões das dependências.
- Medições de inicialização, latência e consumo.
- Complementação dos testes de falhas e preservação textual.
- Revisão por outro integrante, verificação da CI e aceite da PO.

Esta entrega é parcial e não encerra automaticamente as issues na qual fiz referência.