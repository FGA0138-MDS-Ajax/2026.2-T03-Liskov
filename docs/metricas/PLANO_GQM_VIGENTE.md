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
A Mini-tarefa GQM separada e `PACOTE_PRE_INSPECAO_LISKOV.zip` não foram localizados. O confronto abaixo usa
o GQM contido na Visão e preserva suas metas originais até revisão formal.

## Correspondência com o GQM histórico

A numeração G/Q deste plano é operacional e não renumera o histórico. Objetivo 1
histórico (projeto) corresponde a G2; Objetivo 2 (qualidade) a G1 e G3; Objetivo 3
(usabilidade/confiança) é complementado por G4 abaixo.

| Fonte histórica (Visão, seção 5.1) | Medida mantida / correspondência | Divergência e encaminhamento |
|---|---|---|
| O1/Q1 → 1.1 burndown, pp. 28–29 | G2/Q2.2; SP restantes por dia | Fórmula requer registro diário, mas a cadência escrita é semanal. Proposta: captura diária e análise semanal, sem criar snapshots passados. |
| O1/Q2 → 1.2 velocidade, p. 29 | G2/Q2.1; SP de itens que atendem DoD | Meta histórica: Sprint 2 como base e variação máxima de 20% desde Sprint 3. Base/valores não demonstrados: N/D. Preservar meta como referência a fundamentar; não inventar baseline. |
| O2/Q1 → 2.1 desempenho, p. 30 | G1/Q1.1–Q1.6; acurácia ~80%, acrescida de medidas por classe e proveniência | Histórico fala em novo treinamento e notebooks; código usa checkpoint pré-treinado/scripts. Atualização proposta acompanha versão/amostra e #86, sem atribuir treinamento próprio inexistente. |
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
| Q1.2: trata as classes de forma equilibrada? → precisão, recall, F1 por classe e macro | `TPc=Mcc`; `FPc=sum_i(Mic)-TPc`; `FNc=sum_j(Mcj)-TPc`; `Pc=TPc/(TPc+FPc)`; `Rc=TPc/(TPc+FNc)`; `F1c=2TPc/(2TPc+FPc+FNc)`; `F1macro=sum(F1c)/3` | Mesmo JSON, suporte real por classe e relatório de `avaliar()`; campos estruturados por classe propostos no PR #89 | Mesma execução de Q1.1; ML + auditoria QA | Denominador zero: valor matemático N/D; código usa `zero_division=0`, devendo sinalizar classe sem suporte/previsão no relatório. N inteiro maior que zero é condição de entrada. Macro não é acurácia nem F1 ponderado. Limiar por classe: N/D, a definir com PO; investigar classe pior. |
| Q1.3: quais erros são recorrentes? → matriz de confusão e suporte | `Mij=count(y=i, yhat=j)`; `suporte_i=sum_j Mij`; contagens inteiras | JSON com rótulos ordenados e matriz; conferência de somas contra N e distribuição do teste | Cada avaliação; ML, revisão QA | Não inverter eixos nem comparar matrizes com classes diferentes. Usar erros dominantes para selecionar análise qualitativa e novos cenários. |
| Q1.4: os dados e a execução são identificáveis? → tamanhos, hash, versões e separação | N de origem/descartados/duplicatas/conflitos/treino/teste por classe; `SHA256(bytes CSV)`; interseção de grupos normalizados treino/teste deve ser vazia | [`amostrar_bpsad.py`](../../scripts/experimentos/amostrar_bpsad.py), [`validar_bpsad.py`](../../scripts/experimentos/validar_bpsad.py), JSON de amostragem e avaliação, origem/licença, comando e ambiente | Cada geração de amostra; ML e responsável pela proveniência; QA verifica antes de comparar | Seed não é inferida do CSV. Registrar seed, cotas, algoritmo, versão, fração e hash do corpus quando disponível. Ausência desses campos impede afirmar reprodução independente. Não publicar textos de corpus sem licença. |
| Q1.5: o ganho se sustenta no mesmo conjunto? → diferença BERTweet/baseline e incerteza | `Δacc=100*(accB-accBase)` em pontos percentuais; análogo para F1 macro; IC por bootstrap pareado de grupos (proposta) | Mesma partição, previsões pareadas em ambiente autorizado, parâmetros do bootstrap e seed registrados | Antes da decisão sobre modelo/meta; ML + QA, PO decide | Sem previsões pareadas: IC N/D. Não treinar/ajustar pelo teste; independência do pré-treinamento requer investigação própria. Baseline ajusta TF-IDF e regressão apenas no treino. |
| Q1.6: qual custo no ambiente disponível? → tempo e memória | Tempo final − inicial em s; RSS em GiB (`bytes/1024³`); pico exige instrumento específico | Script, hardware/CPU/GPU, versões, lote, aquecimento e tipo de medição registrados | Cada candidato; ML | Script atual mede wall clock incluindo treino/carregamento e RSS após execução. Não representa benchmark controlado nem pico. Limite de aceite: N/D; propor orçamento de latência/memória com PO. |

**G2 — Previsibilidade do projeto:** analisar o trabalho planejado e aceito para
apoiar replanejamento, sob a perspectiva da equipe e PO, por Sprint, sem estimativas
ou séries temporais reconstruídas retrospectivamente.

| Questão → métrica | Fórmula/unidade | Fonte exigida | Frequência e responsável proposto | Limite → decisão esperada |
|---|---|---|---|---|
| Q2.1: qual capacidade aceita foi observada? → velocidade da Sprint | `Vs=sum(SP_i)` dos itens aceitos naquela Sprint, segundo política de crédito acordada | Snapshot de Planning com SP, Sprint, histórico de alterações e evidência datada de aceite da PO | Fechamento real de cada Sprint; equipe estima, SM registra, PO aceita | SP ou aceite ausentes: N/D. PR mesclado/issue fechada não substitui aceite. Média só com quantidade de Sprints válidas >0. Usar apenas para planejar capacidade da própria equipe. |
| Q2.2: como varia o trabalho restante? → burndown | `R(d)=sum(SP ainda não aceitos no dia d)`; ideal proposto `R0*(1-d/D)`, D>0 dias definidos no Planning | Snapshots diários com fuso, baseline, entradas/saídas e alteração de escopo separadas | Diário durante a Sprint; SM mantém captura, equipe confirma bloqueios | Sem SP/snapshot: N/D; não desenhar linha histórica a partir de merges. Registrar carry-over sem crédito duplo. Discutir desvios na Daily/Review e registrar causa/decisão. |
| Q2.3: as medidas são confiáveis? → completude da coleta | `registros com campos obrigatórios / registros previstos`, somente se denominador >0 | Registro de coleta e pendências, exportação de Projects com permissão | Daily e Review; SM + QA | Valor atual N/D. Ausência de evidência não é zero produtividade. Corrigir processo de coleta antes de concluir desempenho. |

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
