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

## Execução em CPU e GPU — issue #102

### Configuração do dispositivo

O dispositivo de inferência do BERTweet é configurado pelas variáveis de ambiente:

| Variável | Descrição | Padrão |
|---|---|---|
| `SENTIA_DISPOSITIVO` | Dispositivo de execução: `cpu`, `cuda` ou `auto`. | `cpu` |
| `SENTIA_GPU_INDEX` | Índice físico da GPU selecionada. | `0` |

Se o runtime da GPU já tiver sido inicializado antes da seleção de uma GPU física diferente do índice zero, será necessário reiniciar o processo. Nesse cenário, o modo auto utiliza a CPU; o modo cuda informa o erro.

Os modos de execução são:

- `cpu`: executa a inferência no processador, utilizando precisão FP32.
- `cuda`: exige uma GPU compatível e gera erro se ela não estiver disponível. Na GPU, o modelo utiliza precisão FP16.
- `auto`: seleciona a GPU quando disponível e utiliza a CPU como alternativa.

Em máquinas com múltiplas GPUs, `SENTIA_GPU_INDEX` permite selecionar a placa desejada. O dispositivo lógico pode aparecer como `cuda:0`, mesmo quando outra GPU física foi selecionada, devido ao isolamento dos dispositivos pelo PyTorch.

Se ocorrer falta de memória da GPU (OOM) durante a inferência de um lote, o classificador registra um aviso, recria o analisador na CPU, tenta novamente o lote afetado e continua a inferência nesse dispositivo.

Exemplo de configuração:

```dotenv
SENTIA_DISPOSITIVO=cuda
SENTIA_GPU_INDEX=1
```

A disponibilidade de GPU depende da instalação de uma versão do PyTorch compatível com o hardware e os respectivos drivers. A instalação do grupo de dependências `ml`, isoladamente, não garante suporte a GPU.

### Avaliação de desempenho local

Os experimentos foram realizados no Windows, utilizando a AMD Radeon RX 9070 com 16 GB de VRAM e PyTorch com suporte ROCm.

**Comparação entre tamanhos de lote**

Foi utilizado um conjunto controlado de 252 textos, formado pela repetição de seis frases. Os valores representam a mediana de três execuções após uma execução de aquecimento.

| Tamanho do lote | Tempo mediano | Vazão aproximada | Pico de VRAM |
|---:|---:|---:|---:|
| 2 | 2,0159 s | 125,01 textos/s | 592,1 MB |
| 8 | 0,5718 s | 440,70 textos/s | 596,2 MB |
| 16 | 0,3406 s | 739,88 textos/s | 599,4 MB |
| 32 | 0,2182 s | 1.155,07 textos/s | 609,1 MB |

Nesse experimento, o lote de 32 apresentou a maior vazão entre as configurações avaliadas, com aumento de aproximadamente 9,24 vezes em relação ao lote de 2. O pico de memória permaneceu próximo entre as configurações.

**Comparação entre FP32 e FP16**

Com lote de 32 e o mesmo conjunto controlado de 252 textos, foram obtidos os seguintes resultados:

| Métrica | FP32 | FP16 |
|---|---:|---:|
| Tempo mediano | 0,4635 s | 0,1229 s |
| Pico de VRAM | 609,1 MB | 358,4 MB |

A execução FP16 apresentou tempo aproximadamente 3,77 vezes menor e redução de cerca de 41,2% no pico de VRAM em relação à execução FP32.

Não houve divergência nas classes previstas nos 252 textos. A maior diferença observada entre as probabilidades foi de aproximadamente 0,00291222.

### Comparação entre CPU e GPU

Foi realizada uma comparação adicional com os mesmos 252 textos e tamanho de lote 32, utilizando FP32 nos dois dispositivos. Os modelos foram carregados e aquecidos antes das três execuções cronometradas.

| Métrica | CPU (Ryzen 7 9800X3D) | GPU (Radeon RX 9070) |
|---|---:|---:|
| Tempo mediano | 25,7245 s | 0,2182 s |
| Vazão aproximada | 9,80 textos/s | 1.155,07 textos/s |
| Precisão | FP32 | FP32 |
| Pico de memória medido | 1.638,9 MB de RAM do processo | 609,1 MB de VRAM alocada pelo PyTorch |

Nesse experimento, a GPU apresentou desempenho aproximadamente 117,9 vezes maior que a CPU em tempo de inferência.

O valor de RAM corresponde ao pico de memória residente do processo Python. O valor de VRAM corresponde ao pico de memória alocada pelo PyTorch. São métricas diferentes e não representam uma comparação direta do consumo total de memória dos dispositivos.

**Comparação das previsões: CPU FP32 × GPU FP16**

Também foram comparadas diretamente as previsões dos dois dispositivos, utilizando
as configurações efetivas do classificador: CPU em FP32 e RX 9070 em FP16.
Foram utilizados os mesmos 252 textos, com lote de 32.

| Métrica | Resultado |
|---|---:|
| Textos comparados | 252 |
| Divergências de classificação | 0 (0%) |
| Maior diferença absoluta de probabilidade | 0,00291133 |
| Diferença média absoluta de probabilidade | 0,00027217 |

A maior diferença absoluta por classe foi de 0,00291133 para positivo,
0,00167051 para negativo e 0,00177661 para neutro.

Nenhuma das 252 previsões apresentou mudança na classe de sentimento.
Essa comparação demonstra consistência entre as duas configurações nessa
amostra controlada, mas não comprova equivalência geral entre FP32 e FP16
nem substitui uma avaliação independente em dados representativos.

Assim como nos demais experimentos, a amostra contém seis frases repetidas e não representa necessariamente o desempenho em uma base real.

### Limitações dos experimentos

Os resultados são medições locais e exploratórias, não uma avaliação independente da qualidade do classificador.

O conjunto utilizado nos benchmarks contém seis frases repetidas, não representando a diversidade de textos, comprimentos e distribuição de classes de um dataset real. As medições também foram realizadas com o modelo carregado e aquecido, não incluindo o tempo de inicialização e carregamento dos pesos.

A ausência de divergência nas classes nesse conjunto não comprova equivalência geral entre FP32 e FP16, nem permite concluir que a acurácia do modelo foi mantida em qualquer conjunto de dados.

Uma avaliação mais representativa deve utilizar uma amostra diversificada, documentar as condições de execução e comparar as previsões e métricas de classificação em um conjunto de avaliação independente.

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
- Benchmark complementar com amostra representativa e textos de comprimentos variados.
- Revisão por outro integrante, verificação da CI e aceite da PO.

Esta entrega é parcial e não encerra automaticamente as issues nela referenciadas.
