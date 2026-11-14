# Plano GQM para acompanhamento vigente — proposta para revisão

Referência da inspeção: **14/11/2026**. Código observado: `developer` em
`1723a7d62d55fa98fbf6eaf5cc9da80650dbe920` (base B). Este plano operacionaliza a
coleta futura e identifica a evidência disponível; não registra aceite da PO nem
substitui o GQM acadêmico original. A meta original **aproximadamente 80% de
acurácia** permanece, conforme [#85](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/85)
e [#86](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86).

A Visão v1.0.0 (30/09/2026), seção 5.1, pp. 28–32, foi recuperada do arquivo
local `Correções Doc_Visao.zip`, junto da versão anotada pelo professor. Os
hashes e a identificação estão no [relatório](../qa/inspecao/RELATORIO_EXECUCAO.md#fonte-histórica-recuperada).
A Mini-tarefa GQM separada foi recuperada nesta regularização; suas definições
e a identificação dos três PDFs constam na seção seguinte. O pacote de
pré-inspeção permanece não localizado. As metas originais são preservadas até
revisão formal.


## Regularização posterior ao PR #91: fontes e estado

Base desta alteração: `c47ceaba7aee4f1f15318e29821f4b30bb6ab147`, após
[merge do #91](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/91).
Os registros originais da inspeção em B continuam históricos, não novas medições.
Em 14/11/2026, #89, #90 e #92 permanecem abertos; #90 está em Draft. Foram
consultados os documentos acadêmicos do
[#90 no SHA 6aa6a38](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/6aa6a386146d26b8ed861a24881afcf9e25f6d70/docs/revisao-academica/MATRIZ_DIVERGENCIAS.md)
(D26–D29) e o catálogo do
[#92 no SHA 25f2587](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/25f258786981f29552d2df2f1b4597ab7ef01c44/docs/inspecao/PLANO_REGULARIZACAO.md).
São propostas em revisão, sem inferir integração ou aprovação da PO.

Fontes locais lidas por extração textual, sem republicar PDFs ou dados pessoais:

| Fonte | Identificação SHA-256 | Trecho usado |
|---|---|---|
| Mini-tarefa, `T03_Liskov - Tarefa GQM.pdf`, 14 páginas | `ecb629621eb253d4b85f78aa17f42db1012b4498369268681595782fc6cda0d4` | §§2.2–2.4, pp. 7–9: Q1/M1 acurácia, Q2/M2 macro, Q3/M3 temporal e regra por classe; §§3.2–3.4, pp. 10–13: velocidade/burndown |
| Visão original v1.0.0, 41 páginas | `9da7c31fa07a012bfa68e541dcbdc18453075256377737253a7a3b84506c7ccd` | §5.1, pp. 28–32 e T04–T08, pp. 36–37 |
| Arquitetura original v1.0.0, 29 páginas | `8596fbb6e102da2d71919e0ccb75fffa9f7e94802280b49e66f2284958becd19` | Classificador/vetorizador treinados e .pkl, confrontados com o código atual |

### F1 individual: regra histórica e condições

A Mini-tarefa §2.2 define M2 como **F1 macro**, mas §2.4, p. 9, acrescenta uma
regra diferente: **F1 de qualquer classe abaixo de 60% indica desequilíbrio**.
Portanto, monitorar `F1c=2*TPc/(2*TPc+FPc+FNc)` para cada classe; equivale a
`2*Pc*Rc/(Pc+Rc)` quando os denominadores são definidos. O corte é 0,60 na
escala [0,1] ou 60 na escala percentual. Exatamente 60% não dispara a regra
estrita <60%; superar o corte isoladamente não significa aceite de RNF01.

Exigir teste rotulado independente das escolhas de treino/hiperparâmetros,
classes/ordem/suporte explícitos e mesma amostra para comparar modelos. Sem suporte
real de uma classe, registrar avaliação insuficiente/N/D para decidir equilíbrio,
ainda que a biblioteca emita zero por `zero_division=0`. Publicar também F1 macro,
sem substituir os três valores individuais pela média. Coletar a cada avaliação
candidata; ML executa e QA revisa. O [registro](REGISTRO_E_ANALISE.md#regularização-da-mini-tarefa-gqm)
compara o limiar ao BPSAD: a classe neutra de ambos os modelos está abaixo do corte;
isso indica desequilíbrio nos resultados declarados, sem aprovação do modelo.

### M3: variação temporal da acurácia

Definição original (§2.2, p. 7): variação entre **treinamentos consecutivos**, em
**pontos percentuais**. Sua operacionalização é `M3(t)=A(t)-A(t-1)` quando A é
percentual, ou `100*(a(t)-a(t-1))` se a é proporção. A fonte não imprime equação
própria de M3; essa subtração explicita a unidade declarada, sem convertê-la em
variação relativa `100*(a(t)-a(t-1))/a(t-1)`.

Períodos originais: cada novo treinamento, com marcos de fim da Sprint 3 e
validação final na Sprint 7 (§2.3, p. 8). Para o checkpoint pré-treinado, propõe-se
medir entre avaliações/versões candidatas consecutivas comparáveis, com data e
Sprint registradas, sem chamar inferência de treinamento. Essa adaptação de Q3
para evolução de desempenho exige ratificação em PO-01b/PO-12.

Dados necessários: dois resultados ordenados do mesmo modelo/linhagem, SHA de
código, revisão de pesos/tokenizador, hash/versão e IDs do teste, N e suporte,
mesmo protocolo de rótulos, partição, amostragem e condições de inferência;
para baseline, seed e configuração de treino. Mudança de corpus/domínio exige
estrato ou nova série, sem atribuir diferença ao modelo. ML (Ricardo/Gabriel)
coleta; QA (Renato) revisa, conforme responsabilidade histórica proposta.

M3 positiva indica aumento de acurácia, negativa queda e zero estabilidade
numérica nas condições registradas; não demonstram significância estatística
nem causa por si. Mesmos pesos/teste/protocolo podem manter valor constante.
**Estado atual: N/D**, sem par temporal comparável demonstrado. Os −2,40 pp
BERTweet−baseline da mesma avaliação BPSAD são comparação entre modelos, não M3.
Não criar CSV ou gráfico temporal sem execuções reais; o CSV/notebook indicado
no PDF é destino planejado, não evidência de arquivo/execução existente.

### Faixas: preservação histórica e proposta sem sobreposição

§2.4, pp. 8–9, registra faixa esperada 75–90%, meta ~80%, faixas ≥80%,
70–79%, <70% e >90%. >90% também satisfaz ≥80%, e valores decimais entre 79
e 80 não têm fronteira explícita. Não arredondar antes da classificação.
A faixa esperada 75–90% é contexto histórico, não uma categoria adicional.

| Acurácia A em %, antes de arredondar | Categoria proposta | Encaminhamento proposto |
|---|---|---|
| `0 <= A < 70` | Crítico | Investigar dados/erros e recomendar replanejamento à PO |
| `70 <= A < 80` | Atenção | Abrir melhoria e reavaliar; explicita o intervalo decimal 79–80 |
| `80 <= A <= 90` | Referência numérica de acurácia alcançada | Revisão de evidência, F1 por classe, domínio e PO antes de aceite |
| `90 < A <= 100` | Sob auditoria | Auditar duplicatas/vazamento/dificuldade antes de qualquer aceite |

Valores ausentes, não finitos, fora de [0,100] ou N=0: inválido/N/D, fora dessas
categorias. A condição F1c<60% é um **alerta independente** aplicável a qualquer
faixa; não sobrepõe as categorias de acurácia. Fronteiras, prioridade da auditoria
e substituição da aprovação automática escrita no histórico são **propostas
dependentes da PO (PO-02/PO-12)**, sem alterar unilateralmente critério de aceite.

### Modelo, requisitos e decisões

| Operação / vínculo | Evidência e interpretação vigente | Ratificação pendente |
|---|---|---|
| Inferência BERTweet / RF03–RF07, T04–T08 | `ClassificadorBertweet` carrega `pysentimiento/bertweet-pt-sentiment` via create_analyzer e chama predict; preserva texto, sem stopwords/stemming/TF-IDF externos. Revisão dos pesos ainda não fixada no carregador | PO-01a (RF03–RF06/T04–T07/ADR-001) e PO-01b (RF07/T08) |
| Avaliação do checkpoint / RNF01, US08, complemento de T08 | Comparar previsões com rótulos humanos calcula desempenho; isso não treina pesos. Testes com espião verificam contrato, não acurácia | PO-02 e reprodução independente #85/#89 |
| Treino baseline / comparador offline | TF-IDF + Regressão Logística ajustados somente na partição de treino; avaliar no teste congelado, sem ajustar hiperparâmetros por ele | PO-01b, papel separado do fluxo BERTweet |
| Fine-tuning BERTweet | Não há evidência concreta de ajuste fino próprio nesta base. Não atribuir treinamento próprio em notebook/Colab ao SentIA | Nova evidência e decisão seriam necessárias antes de afirmar execução |

PO-12 abrange conciliação das questões/métricas/limiares e protocolo; PO-13
abrange aceite por requisito, cenário e SHA. Nenhum status numérico substitui
resposta datada da PO. O [plano de testes](../qa/inspecao/PLANO_TESTES_ATUAL.md)
e a [matriz](../qa/inspecao/MATRIZ_RASTREABILIDADE.md) permanecem referências do
#91; a pendência de localizar Mini-tarefa nesses documentos é histórica e está
superada por esta leitura, sem editar arquivos fora do escopo autorizado.

## Correspondência com o GQM histórico

A numeração G/Q deste plano é operacional e não renumera o histórico. Objetivo 1
histórico (projeto) corresponde a G2; Objetivo 2 (qualidade) a G1 e G3; Objetivo 3
(usabilidade/confiança) é complementado por G4 abaixo.

| Fonte histórica (Visão, seção 5.1) | Medida mantida / correspondência | Divergência e encaminhamento |
|---|---|---|
| O1/Q1 → 1.1 burndown, pp. 28–29 | G2/Q2.2; SP restantes por dia | Fórmula requer registro diário, mas a cadência escrita é semanal. Proposta: captura diária e análise semanal, sem criar snapshots passados. |
| O1/Q2 → 1.2 velocidade, p. 29 | G2/Q2.1; SP de itens que atendem DoD | Meta histórica: Sprint 2 como base e variação máxima de 20% desde Sprint 3. Base/valores não demonstrados: N/D. Preservar meta como referência a fundamentar; não inventar baseline. |
| O2/Q1 → 2.1 desempenho, p. 30 | G1/Q1.1–Q1.7; acurácia ~80%, acrescida de medidas por classe e proveniência | Histórico fala em novo treinamento e notebooks; código usa checkpoint pré-treinado/scripts. Atualização proposta acompanha versão/amostra e #86, sem atribuir treinamento próprio inexistente. |
| O2/Q2 → 2.2 densidade de defeitos, pp. 30–31 | G3/Q3.4 abaixo | Definição diz tamanho do código, fórmula divide por histórias concluídas. Manter unidade defeitos/US, propor ajustar o nome/definição com PO, sem substituir por KLOC. |
| O2/Q3 → 2.3 débito técnico, p. 31 | G3/Q3.5 abaixo | Preservar contagem de issues rotuladas e regra histórica de não crescer por duas Sprints; faltam snapshots e política de rótulo. |
| O2/Q4 → cobertura, p. 30 | G3/Q3.2 | Questão sem métrica correspondente no histórico; anotação do professor, p. 28, pede completar a ligação. Medida de linhas proposta com escopo src explicitado. |
| O3/Q1 → 3.1 sucesso em tarefas, p. 32 | G4/Q4.1 abaixo | Preservar 85% no total e mínimo de 70% por tarefa como referências históricas a fundamentar, sem inventar sessões. |
| O3/Q2 → concordância dos usuários, p. 32 | G4/Q4.2 abaixo, nova medida proposta | Questão sem métrica histórica; anotação do professor, p. 28, pede ligação explícita. Não usar concordância como acurácia com verdade objetiva. |

## Objetivos, questões e medidas

**G1 — Qualidade do modelo:** analisar o classificador de sentimentos para avaliar
sua correção e limitações, sob a perspectiva de ML, QA e PO, em português e com
domínio, dados e versões explicitados. BERTweet pré-treinado é o caminho principal;
TF-IDF + regressão logística é um baseline comparativo separado.

Na tabela, M é a matriz de confusão: linha = classe real, coluna = prevista;
a ordem canônica é `positivo, negativo, neutro`, conforme
[`rotulos.py`](../../src/processamento/classificacao/rotulos.py).

| Questão → métrica | Fórmula/unidade | Fonte e artefato exigido | Frequência e responsável proposto | Limite de interpretação → decisão esperada |
|---|---|---|---|---|
| Q1.1: acerta quantas classificações? → acurácia | `tr(M)/N`, `N=sum(M)`, proporção e % | [`avaliacao.py`](../../src/processamento/classificacao/avaliacao.py), JSON de avaliação, SHA do código e do CSV | Cada versão candidata, mudança de amostra/modelo; Ricardo/Gabriel executam, Renato audita (#85) | Se N=0: N/D e avaliação recusada. Comparar com ~80%; resultado abaixo exige análise e recomendação à PO, sem reduzir a meta unilateralmente. |
| Q1.2: trata as classes de forma equilibrada? → precisão, recall, F1 por classe e macro | `TPc=Mcc`; `FPc=sum_i(Mic)-TPc`; `FNc=sum_j(Mcj)-TPc`; `Pc=TPc/(TPc+FPc)`; `Rc=TPc/(TPc+FNc)`; `F1c=2TPc/(2TPc+FPc+FNc)`; `F1macro=sum(F1c)/3` | Mesmo JSON, suporte real por classe e relatório de `avaliar()`; campos estruturados por classe propostos no PR #89 | Mesma execução de Q1.1; ML + auditoria QA | Denominador zero: valor matemático N/D; código usa `zero_division=0`, devendo sinalizar classe sem suporte/previsão no relatório. N inteiro maior que zero é condição de entrada. Macro não é acurácia nem F1 ponderado. Limiar histórico: F1 de qualquer classe <0,60 aciona análise de desequilíbrio (Mini-tarefa §2.4, p. 9); não aplicar esse corte ao F1 macro. Ratificação de aceite pendente da PO. |
| Q1.3: quais erros são recorrentes? → matriz de confusão e suporte | `Mij=count(y=i, yhat=j)`; `suporte_i=sum_j Mij`; contagens inteiras | JSON com rótulos ordenados e matriz; conferência de somas contra N e distribuição do teste | Cada avaliação; ML, revisão QA | Não inverter eixos nem comparar matrizes com classes diferentes. Usar erros dominantes para selecionar análise qualitativa e novos cenários. |
| Q1.4: os dados e a execução são identificáveis? → tamanhos, hash, versões e separação | N de origem/descartados/duplicatas/conflitos/treino/teste por classe; `SHA256(bytes CSV)`; interseção de grupos normalizados treino/teste deve ser vazia | [`amostrar_bpsad.py`](../../scripts/experimentos/amostrar_bpsad.py), [`validar_bpsad.py`](../../scripts/experimentos/validar_bpsad.py), JSON de amostragem e avaliação, origem/licença, comando e ambiente | Cada geração de amostra; ML e responsável pela proveniência; QA verifica antes de comparar | Seed não é inferida do CSV. Registrar seed, cotas, algoritmo, versão, fração e hash do corpus quando disponível. Ausência desses campos impede afirmar reprodução independente. Não publicar textos de corpus sem licença. |
| Q1.5: o ganho se sustenta no mesmo conjunto? → diferença BERTweet/baseline e incerteza | `Δacc=100*(accB-accBase)` em pontos percentuais; análogo para F1 macro; IC por bootstrap pareado de grupos (proposta) | Mesma partição, previsões pareadas em ambiente autorizado, parâmetros do bootstrap e seed registrados | Antes da decisão sobre modelo/meta; ML + QA, PO decide | Sem previsões pareadas: IC N/D. Não treinar/ajustar pelo teste; independência do pré-treinamento requer investigação própria. Baseline ajusta TF-IDF e regressão apenas no treino. |
| Q1.6: qual custo no ambiente disponível? → tempo e memória | Tempo final − inicial em s; RSS em GiB (`bytes/1024³`); pico exige instrumento específico | Script, hardware/CPU/GPU, versões, lote, aquecimento e tipo de medição registrados | Cada candidato; ML | Script atual mede wall clock incluindo treino/carregamento e RSS após execução. Não representa benchmark controlado nem pico. Limite de aceite: N/D; propor orçamento de latência/memória com PO. |
| Q1.7: o desempenho evolui entre avaliações comparáveis? → M3, variação temporal da acurácia | `M3(t)=A(t)-A(t-1)` em pp, com A em % | Dois resultados temporais identificados; [definição, condições e fonte histórica de M3](#m3-variação-temporal-da-acurácia) | Cada avaliação candidata comparável; ML coleta, QA revisa | Atual N/D; adaptação da definição histórica entre treinamentos depende PO-01b/PO-12. Não é a comparação entre modelos de Q1.5. |

**G2 — Previsibilidade do projeto:** analisar o trabalho planejado e aceito para
apoiar replanejamento, sob a perspectiva da equipe e PO, por Sprint, sem estimativas
ou séries temporais reconstruídas retrospectivamente.

| Questão → métrica | Fórmula/unidade | Fonte exigida | Frequência e responsável proposto | Limite → decisão esperada |
|---|---|---|---|---|
| Q2.1: qual capacidade aceita foi observada? → velocidade da Sprint e variação percentual histórica | `Vs=sum(SP_i)` dos itens que atendem DoD; `μs=sum(Vj)/n`, para as n Sprints anteriores válidas, sem incluir s; `δs=100*(Vs-μs)/μs` em %, somente se n>0 e μs>0 | Snapshot de Planning com SP, Sprint, histórico de alterações e evidência datada de aceite da PO; Mini-tarefa §§3.3–3.4, pp. 11–13 | Fechamento real de cada Sprint e Planning seguinte; SM registra, equipe estima/participa e PO valida. Sprint 2 é base histórica; análise desde Sprint 3 | SP/aceite ausentes ou média anterior zero/indisponível: N/D. Duas Sprints consecutivas com `δs < -20%` acionam historicamente replanejamento (Visão §2.6); não tratar -20% exatos como abaixo do limite. Critério preservado para ratificação PO-12/PO-13, sem presumir decisão. PR mesclado não substitui DoD/aceite. |
| Q2.2: como varia o trabalho restante? → burndown | `R(d)=sum(SP ainda não aceitos no dia d)`; ideal proposto `R0*(1-d/D)`, D>0 dias definidos no Planning | Snapshots diários com fuso, baseline, entradas/saídas e alteração de escopo separadas | Diário durante a Sprint; SM mantém captura, equipe confirma bloqueios | Sem SP/snapshot: N/D; não desenhar linha histórica a partir de merges. Registrar carry-over sem crédito duplo. Discutir desvios na Daily/Review e registrar causa/decisão. |
| Q2.3: as medidas são confiáveis? → completude da coleta | `registros com campos obrigatórios / registros previstos`, somente se denominador >0 | Registro de coleta e pendências, exportação de Projects com permissão | Daily e Review; SM + QA | Valor atual N/D. Ausência de evidência não é zero produtividade. Corrigir processo de coleta antes de concluir desempenho. |

A variação de Q2.1 é relativa à média **anterior**, não à própria velocidade atual
nem à Sprint imediatamente anterior isolada. Cada uma das duas Sprints do gatilho
usa sua própria média histórica disponível; não inserir dados ausentes como zero.
Se uma das variações for N/D, o gatilho não é verificável: não concluir nem
ocorrência nem ausência. Aplicar a análise somente à própria equipe, com Sprints
comparáveis e política de SP/DoD registrada. Estado atual: velocidade, média,
variação e gatilho **N/D**, sem SP/aceites suficientes. A fórmula e o gatilho
recuperam D28 do #90; não são medições ou decisões novas da PO.

**G3 — Qualidade verificável do software:** analisar testes e defeitos para apoiar
decisões de revisão e integração, sob a perspectiva QA/equipe, por SHA.

| Questão → métrica | Fórmula/unidade | Fonte exigida | Frequência e responsável proposto | Limite → decisão esperada |
|---|---|---|---|---|
| Q3.1: a suíte aplicável executa? → PASS/FAIL/ERROR/SKIP | Contagens do pytest por execução, SHA e ambiente | Log, JUnit e [relatório](../qa/inspecao/RELATORIO_EXECUCAO.md) | Cada PR e push em developer; autor executa e QA verifica | SKIP é pendência de execução. Nenhum limiar autoriza ignorar falhas; distinguir serviços reais de mocks. |
| Q3.2: que código foi exercitado? → cobertura de linhas | `linhas cobertas/linhas executáveis` em `src`, com denominador >0 | pytest-cov/coverage, versão e módulos ausentes | Mesma execução de Q3.1; QA | Não mede acurácia, segurança, qualidade de asserts nem cobertura de scripts fora de src. Não há meta nova imposta por este plano. Usar lacunas por módulo para priorizar cenários. |
| Q3.3: defeitos tiveram reteste? → cadeia de evidência | Registro por defeito de falha → correção → execução posterior | [Defeitos e correções](../qa/inspecao/DEFEITOS_E_CORRECOES.md), PR, teste e log | Cada correção; autor + QA | Antes sem log: N/D para reprodução do defeito. CI verde do conjunto não prova execução do produto com todos os serviços. |

Complementos às questões históricas de qualidade e usabilidade:

| Objetivo → questão → métrica | Fórmula / fonte | Frequência / responsável proposto | Limites / decisão esperada |
|---|---|---|---|
| G3/Q3.4 / O2-Q2 histórico → incidência de defeitos → 2.2 defeitos por US concluída | `defeitos únicos registrados na Sprint / US que atendem DoD na Sprint`; registro de defeitos/Issues e aceite por US | Fim de Sprint; QA e desenvolvedores | Denominador zero/aceite ausente: N/D. Sem contar funcionalidade futura como defeito. Critério histórico: queda e nenhum crítico aberto; cadastro/estados datados são necessários para avaliar. |
| G3/Q3.5 / O2-Q3 histórico → evolução de débito → 2.3 issues técnicas adiadas | Contar issues abertas com rótulo de débito técnico no snapshot de fechamento | Refinamento/Planning e snapshot no fim da Sprint; SM/equipe | Rótulo e data de referência precisam de definição; dados atuais N/D. Se crescer por duas Sprints conforme referência histórica, discutir capacidade de pagamento; não rotular itens retroativamente para fabricar série. |
| G4/Q4.1: validar usabilidade/confiança do dashboard, perspectiva usuário/PO → O3-Q1 → 3.1 sucesso em tarefas | `tarefas concluídas corretamente sem ajuda / tentativas válidas * 100`; idem por tarefa; planilha anonimizada de observação | Cada sessão de candidato de UI; PO, frontend e QA | Denominador zero: N/D. Roteiro histórico: distribuição, predominância, filtro de período, sentimento e resumo; duas últimas só se implementadas. Metas históricas 85% global/70% por tarefa preservadas, fundamento pendente; nenhuma sessão atual. Corrigir obstáculos observados e repetir. |
| G4/Q4.2 → O3-Q2 → concordância de usuário com previsão (proposta nova) | `julgamentos concordantes / pares texto-julgamento válidos * 100`; registrar tamanho, amostragem, rótulos, discordâncias e revisão de instrução | Sessão com textos controlados; PO/QA/ML | Valor/meta N/D. Definir protocolo e agregação entre avaliadores, proteger dados e não publicar identidades. Não equivale a verdade anotada independente; usar discordâncias para investigar confiança e comunicação. |


## Procedimento de coleta e interpretação

1. Antes do experimento, congelar SHA, origem/licença dos dados, domínio, hash,
   partição, versões (incluindo revisão de pesos/tokenizador), comandos e hardware.
   O carregador atual identifica o checkpoint por nome, sem fixar revisão; registrar
   essa limitação. Preservar JSON de amostragem junto do CSV local.
2. Executar baseline e, em ambiente preparado para ML, BERTweet nos mesmos textos.
   Registrar erros e ausências. CI com analisador simulado verifica software, sem
   produzir métrica de qualidade do modelo.
3. Conferir suporte, eixos e somas da matriz; derivar medidas sem dividir por zero.
   Registrar resultados em [REGISTRO_E_ANALISE.md](REGISTRO_E_ANALISE.md), incluindo
   se são declaração do autor, conferência aritmética ou reprodução independente.
4. Discutir BPSAD (avaliações de produtos, notas convertidas em sentimento) separado
   de tweets: queda em BPSAD não determina desempenho em redes sociais. Desbalanceamento
   e possível sobreposição com pré-treinamento limitam generalização. A revisão
   de RNF01 depende de recomendação de ML/QA e decisão formal da PO (#85/#86).
5. A partir do próximo Planning, estimar SP pela equipe e registrar aceite,
   snapshots diários e mudanças de escopo. O acesso a Projects está pendente de
   permissão; os números de velocidade/burndown atuais permanecem N/D.

## Atendimento ao formulário

O formulário do professor, Quadro 6 (métricas, itens i–iv), pede plano, estrutura
GQM, coleta e análise. Este documento cobre a definição; o registro vinculado
expõe as coletas disponíveis e ausentes. A versão local consultada foi
`Formulario Inspeção_professor.pdf`, seções de métricas e testes; identificação
e hash estão no [relatório de execução](../qa/inspecao/RELATORIO_EXECUCAO.md).
Não se atribui nota nem homologação. Responsáveis e frequências propostos aqui
precisam de ratificação no Planning/Review; não são novas atribuições automáticas.
