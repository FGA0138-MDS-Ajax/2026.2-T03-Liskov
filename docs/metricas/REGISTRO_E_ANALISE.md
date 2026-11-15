# Registro e análise de métricas

Data de coleta: **14/11/2026**. Base B: `developer`,
`1723a7d62d55fa98fbf6eaf5cc9da80650dbe920`, conferida por `git fetch origin`.
Registros abaixo distinguem execução auditada, declaração histórica e proposta.
Fórmulas, limites e cadência futura: [plano GQM](PLANO_GQM_VIGENTE.md).

## Dados verificáveis e encaminhamentos

| ID / objetivo | Dado e origem verificável | Interpretação | Ação / responsável proposto |
|---|---|---|---|
| R01 / G3 | [CI 43503741871](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871), SHA B, 13/11/2026 20:40:37 UTC; [job 132155891920](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/actions/runs/43503741871/job/132155891920): **814 coletados/aprovados, 0 falhas, 0 skips, 10 warnings, 21,40 s; cobertura de linhas src: 93%** (2699 statements, 176 missing) | Log do job consultado diretamente. Banco mongo:7 inicializado; testes de banco reais executam no CI. BERTweet e HTTP externo são simulados na suíte. Cobertura não mede acurácia do modelo. | QA mantém referência imutável e separa reteste local, descrito no [relatório](../qa/inspecao/RELATORIO_EXECUCAO.md). Não trocar esse resultado por contagem declarada no PR #81. |
| R02 / G3 | [`docs/qa/pc1/STATUS_FINAL.md`](../qa/pc1/STATUS_FINAL.md): 538 aprovados / 94%, referência histórica de 09/11, combinação documentada de PRs | Resultado histórico, sem atribuição ao SHA B. | Preservar arquivo original; usar o relatório atual na inspeção. |
| R03 / G3 | [PR #83](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/83), head `7009500027fe1acfbe6dad997ef79730453c29b3`: **OPEN, não integrado**; descrição informa 707 aprovados, 8 skips, 94%, base `fe83ad0` | Walkthrough em revisão, com corte anterior. Seus números não são execução local atual. | Revisores devem reconciliar com a base B antes de integrar. |
| R04 / G1 | [`docs/experimentos_bpsad.md`](../experimentos_bpsad.md) em B preserva acurácia baseline 70,10% e BERTweet 67,70%; F1 macro 59,65% / 55,43%, declarados no contexto do PR #64 | O próprio documento diz que a auditoria não os reproduziu. Não provam atendimento de RNF01. | Prosseguir com reprodução independente pela #85, sem alterar meta. |
| R05 / G1 | [PR #89](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/89), head `4a0e338c2a4f919b7095c3821339228b9a7c620b`: **OPEN, não integrado**. JSONs identificados abaixo contêm amostra 10.000, treino 8.000, teste 2.000, seed 42; distribuição do teste POS=1371, NEG=319, NEU=310 | Artefatos do autor disponíveis para revisão; consistência aritmética conferida nesta inspeção, sem reexecutar amostragem/inferência. Seed consta do JSON de amostragem, não é deduzida do CSV. | Ricardo/Gabriel fornecem ambiente e dados autorizados; Renato reproduz. PO avalia recomendação após revisão. |
| R06 / G1 | Mesmo JSON #89: baseline acc=0,701, F1macro=0,5964593556860648; BERTweet acc=0,677, F1macro=0,5543063931312299 | Matrizes totalizam 2.000 e reproduzem esses valores por aritmética. Diferença BERTweet−baseline: **−2,40 pp** de acurácia e **−4,2153 pp** de F1 macro; arredondamento a 4 casas, sem intervalo de confiança disponível. | Investigar classe neutra e domínio; não concluir superioridade geral de um modelo nem revisar ~80% automaticamente. |
| R07 / G1 | JSON #89: baseline 0,6395417 s e RSS 0,19216156; BERTweet 148,5326237 s e RSS 1,07770538, campo denominado `memoria_rss_gb_apos_execucao` | Declaração do autor. Fórmula do script divide por 1024³ (GiB). Tempos incluem treino/carregamento; RSS é posterior, não pico; comparação não controlada. | Instrumentar aquecimento, repetições, hardware e pico antes de decidir orçamento de desempenho. |
| R08 / G1 | [#85](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/85), [#86](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/86), ambas abertas na consulta: meta original ~80%, reprodução e revisão documental pendentes | BPSAD mede avaliações de produtos, com nota convertida em sentimento; não é o mesmo domínio de tweets. Independência do pré-treinamento não comprovada. | ML/QA recomendam com limitações; PO ratifica eventual nova meta. Aceite formal não localizado nestas fontes. |
| R09 / G2 | `gh project list --owner FGA0138-MDS-Ajax --format json`: recusado por token sem escopo **read:project**, em 14/11/2026 | Projects não inspecionável com a credencial disponível; não significa que não existam estimativas no board. | Responsável de gestão exporta campos/histórico com autorização. Nenhuma alteração de escopo do token feita nesta tarefa. |
| R10 / G2 | Issues [#4](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/4), [#17](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/17), [#22](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/22), [#26](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/26), [#32](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/32) solicitam SP a estimar, sem números nos corpos consultados | **SP, velocidade por Sprint, média de velocidades e burndown histórico: N/D.** Ausência de Planning estimado e snapshots diários verificáveis nas fontes acessadas. Número de issues/PRs não substitui SP. | Estimar no próximo Planning; coletar snapshots prospectivamente. Não reconstruir série com datas de merges. |
| R11 / G3 | [PR #81](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/81) integrado em B; sua descrição declara 750 aprovados/8 pulados e também pede não mesclar antes de resolver aceite/custo | Código integrado não equivale a homologação. Divergência de governança documentada, sem presumir autorização ou reverter integração. | PO/equipe resolvem custo, relevância e aceite; gestão registra decisão. Nenhum XFetch real acionado nesta inspeção. |

## Confronto com a Visão histórica e comentários do professor

Fonte: Visão v1.0.0, 30/09/2026, seção 5.1, pp. 28–32; versão original e
anotada identificadas no [relatório](../qa/inspecao/RELATORIO_EXECUCAO.md#fonte-histórica-recuperada).
Nenhum resultado ausente foi preenchido com números das metas.

| Registro | Dado documental e interpretação | Decisão / ação |
|---|---|---|
| R12 / gestão | Métrica 1.1 exige cálculo diário, mas prevê atualização semanal; 1.2 usa Sprint 2 como base e variação máxima de 20%. Sem SP/snapshots acessíveis: resultados N/D | Propor captura diária/análise semanal; base e variação atuais N/D, sem reconstituição da Sprint 2. Equipe deve fundamentar limites antes de ratificação. |
| R13 / qualidade | Métrica 2.2 fala em tamanho de código e divide por US concluídas; 2.3 conta issues rotuladas como débito técnico. Não há cadastro completo de defeitos por Sprint, aceite de US nem snapshots de rótulos nas fontes verificadas | Densidade e evolução de débito: N/D. Os quatro casos deste dossiê não são censo de defeitos e não podem fornecer o numerador de todas as Sprints. |
| R14 / cobertura | O2/Q4 histórico não tinha métrica correspondente; anotação do professor solicita esse vínculo. Coleta atual R01/E2 fornece 93% CI / 92% local em src, com limites distintos | Usar G3/Q3.2 do plano; não definir limiar novo de aceite por inferência. |
| R15 / usabilidade | Métrica 3.1 estabelece 85% global e 70% por tarefa; O3/Q2 de concordância não tinha medida. Comentário do professor pede completar a correspondência e justificar referências | Taxa de sucesso e concordância atuais: N/D, sem sessões registradas nesta execução. G4 propõe coleta e protocolo; PO/QA devem ratificar. |
| R16 / testes | Visão seção 6.2: T01=coleta, T02=importação, T08=RF07/classificação, T18=RNF02/responsividade. Backlog p. 27 escreve RF02 para responsividade | Matriz segue roteiro histórico e registra conflito RF02/RNF02 para PO, sem editar PDFs. T11–T13 continuam testes de sistema com critérios pela UI; aprovação de API é parcial. |

## Auditoria aritmética dos artefatos do PR #89

Fontes imutáveis consultadas, fora de B:

- [Avaliação JSON](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/4a0e338c2a4f919b7095c3821339228b9a7c620b/docs/resultados_bpsad/avaliacao_pc1_final.json), blob `d48514dba91be362a227f962ef4cf18910692749`.
- [Amostragem JSON](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/4a0e338c2a4f919b7095c3821339228b9a7c620b/docs/resultados_bpsad/relatorio_amostragem_pc1.json), blob `2340c315079be4ba535ea06d32134303df29e72b`.

Hash da amostra **declarado** no JSON de avaliação:
`607fd459fdf7cb1721d154dce7322d9256d9dcd9d4cc712ccc589907eeb659b6`.
CSV/corpus completo não acessados nesta inspeção; hash não recalculado.
Versões declaradas: Python 3.12.10, pandas 3.1.1, scikit-learn 1.9.1,
pysentimiento 0.7.3, torch 2.15.0+cpu e psutil 7.2.2. Revisão exata dos pesos,
hardware e IC: N/D nestes JSONs. O nome do checkpoint não fixa a revisão.

Matrizes (linhas reais, colunas previstas, ordem positivo/negativo/neutro):

| Modelo | Linha positivo | Linha negativo | Linha neutro | Diagonal / N |
|---|---|---|---|---|
| Baseline | 1065, 101, 205 | 56, 209, 54 | 123, 59, 128 | 1402 / 2000 |
| BERTweet | 1031, 136, 204 | 33, 249, 37 | 146, 90, 74 | 1354 / 2000 |

Valores por classe publicados no JSON (arredondados aqui a seis casas):

| Modelo / classe | Precisão | Recall | F1 | Suporte |
|---|---:|---:|---:|---:|
| Baseline / positivo | 0,856109 | 0,776805 | 0,814532 | 1371 |
| Baseline / negativo | 0,566396 | 0,655172 | 0,607558 | 319 |
| Baseline / neutro | 0,330749 | 0,412903 | 0,367288 | 310 |
| BERTweet / positivo | 0,852066 | 0,752006 | 0,798915 | 1371 |
| BERTweet / negativo | 0,524211 | 0,780564 | 0,627204 | 319 |
| BERTweet / neutro | 0,234921 | 0,238710 | 0,236800 | 310 |

Conferência efetivamente executada com Python padrão, em 14/11: para cada matriz,
somar células, linhas e diagonal e calcular `F1c=2*Mcc/(soma_linha_c+soma_coluna_c)`;
a média dos três F1 coincide com o JSON. A reexecução completa de ML é **NÃO
EXECUTADA**. Essa conferência não verifica origem das previsões nem independência.
O suporte positivo de 1371/2000 mostra desbalanceamento; F1 neutro do BERTweet é
0,2368. Comparar somente acurácia ocultaria esse resultado.

## Coleta prospectiva e revisão

| Momento | Registro mínimo a iniciar | Uso na análise |
|---|---|---|
| Próximo Planning | ID da Sprint, datas/dias úteis, baseline de escopo e SP estimados pela equipe; definição de item aceito e tratamento de carry-over | Fixar denominadores sem estimar retrospectivamente. |
| Cada Daily | Snapshot com data/fuso, itens restantes, SP, bloqueios e mudanças de escopo com decisão | Produzir burndown apenas a partir do primeiro snapshot verificável. |
| Review | Evidência de aceite por item e data, itens carregados e causas; SP aceitos | Calcular velocidade da Sprint válida; não creditar o mesmo item duas vezes. |
| Retrospectiva | Questão GQM, dado, interpretação, decisão, responsável e próxima revisão | Avaliar utilidade da coleta e corrigir processo. |
| Avaliação ML | SHA, hashes, amostragem, versões/revisões, domínio, matriz, suporte, comandos, log e parecer de reprodução | Comparar modelos/meta com limites explícitos. |

Responsáveis propostos: SM mantém registros de gestão; equipe estima; PO registra
aceite; Ricardo/Gabriel executam avaliação; QA audita. Confirmação desses papéis e
acesso a Projects permanecem pendentes. Não se atribui velocidade zero nem se
calcula média de uma lista vazia.

## Regularização da Mini-tarefa GQM

Revisão documental sobre developer `c47ceaba7aee4f1f15318e29821f4b30bb6ab147`,
após #91, em 14/11/2026. Não representa nova execução ML. As linhas R01–R16
mantêm seus cortes históricos. À época da nova consulta, #90 (Draft, head `6aa6a38`),
#92 (head `25f2587`) e #89 (head `4a0e338`) estavam abertos e apenas #91 integrado;
subsequentemente, #90, #92 e este ajuste (#94) foram integrados à `developer`,
permanecendo #89 em aberto.
As fontes, hashes, páginas e links fixados estão no
[plano atualizado](PLANO_GQM_VIGENTE.md#regularização-posterior-ao-pr-91-fontes-e-estado).

| Registro | Evidência / resultado | Análise e ação |
|---|---|---|
| R17 / M2 e alerta por classe | Mini-tarefa §2.4, p. 9: F1 de qualquer classe <60%; §2.2, p. 7: M2 macro | Corrige a indicação anterior de limiar por classe N/D. O limiar histórico existe; ratificação de critério/aceite permanece pendente (PO-02/PO-12). |
| R18 / M3 | §2.2, p. 7: diferença entre treinamentos consecutivos em pp; §2.3, p. 8: frequência a cada treino e marcos S3/S7 | Estado N/D: não há duas avaliações temporais comparáveis demonstradas. Diferença entre modelos BPSAD não é evolução temporal. Adaptação ao checkpoint em avaliações candidatas é proposta PO-01b/PO-12. |
| R19 / faixas | §2.4: ≥80% e >90% se sobrepõem; 70–79% deixa fronteira decimal ambígua | Plano propõe [0,70), [70,80), [80,90], (90,100], sem arredondamento prévio; prioridade de auditoria e mudança do aceite automático dependem PO-02/PO-12. |
| R20 / execução | Código em c47ceab mantém inferência de checkpoint, treino somente do baseline comparativo e testes com substitutos | Nenhuma evidência nova de fine-tuning, treinamento próprio BERTweet ou reprodução independente nesta tarefa. RF03–RF07/T04–T08 a ratificar em PO-01a/b; RNF01 em PO-02; aceite por SHA em PO-13. |

Comparação do corte individual de 60% aos JSONs do #89, sem arredondamento
para decidir (valores exibidos em % com quatro casas):

| Modelo | F1 positivo | F1 negativo | F1 neutro | Alerta histórico por classe |
|---|---:|---:|---:|---|
| Baseline | 81,4532% | 60,7558% | 36,7288% | Neutro abaixo de 60% |
| BERTweet | 79,8915% | 62,7204% | 23,6800% | Neutro abaixo de 60% |

Ambos não satisfazem a referência de ausência de classe abaixo de 60% nos
resultados declarados. Positivo/negativo ultrapassam o corte, sem implicar aceite.
F1 macro de 59,6459%/55,4306% é outra medida e não determina qual classe falhou.
Acurácia baseline 70,10% corresponde à categoria proposta Atenção; BERTweet
67,70% à categoria proposta Crítico; nenhum alcança a meta original ~80%.
Essas categorias são análise documental proposta, não decisão de replanejamento
ou reprovação/aprovação formal da PO.

Limitações: teste BPSAD de 2.000 registros, suporte 1371/319/310, avaliações de
produtos e notas convertidas em sentimento; não extrapolar para tweets. Amostra
10.000, seed 42, treino baseline 8.000; pesos BERTweet pré-treinados não foram
ajustados nesses 8.000 por evidência disponível. Hash do CSV é declarado no
JSON, sem corpus local para recalcular. Independência do pré-treinamento não
comprovada; ausência de repetição independente e intervalos de incerteza impede
atribuir homologação. Métricas/limiares e domínio de aceite dependem PO-02/PO-12.

Validação desta regularização: links Markdown e âncoras locais dos dois arquivos
conferidos por Python; matrizes recalculadas para F1 individual, regra estrita
<60% (inclusive fronteira 60%), sinais/unidade de M3 e partição das categorias
conferidos. Foram verificados 100.001 valores de acurácia em [0,100], mais
fronteiras 70/79/80/90 e entradas inválidas: cada valor válido pertence a uma
única categoria. Esses são testes aritméticos/documentais, não novas medições ML.
`uv lock --check` e `make lint` concluíram com saída 0, usando o ambiente isolado
`/tmp/sentia-sol-medium-venv`; `git diff --check` aprovado. Sem alteração de
produção/testes e sem reexecução ML local; o resultado do CI do novo PR deve ser
consultado por seu HEAD, sem reutilizar contagens de R01 como execução nova.

## Ajuste após revisão independente do PR #94

A revisão comunicada pelo usuário classificou o PR como apto com ressalvas,
sem bloqueantes. Este ajuste registra somente os dois pontos solicitados:

| Registro | Correção e fonte | Estado / limite |
|---|---|---|
| R21 / O1 → G2/Q2.1 | Mini-tarefa §§3.3–3.4, pp. 11–13, e D28 do #90: `δs=100*(Vs-μs)/μs`, com μs calculada somente sobre Sprints anteriores válidas; duas Sprints consecutivas com δs < −20% acionam historicamente replanejamento | Média zero/indisponível, SP ou aceite ausentes: N/D; se faltar uma variação, gatilho não verificável. Sem novas estimativas, séries ou decisão da PO; ratificação PO-12/PO-13 permanece pendente. |
| R22 / O2 → G1/Q1.7 | Identificador próprio Q1.7 para M3, com link à definição existente em pontos percentuais e condições temporais; Q1.5 preservada como diferença BERTweet/baseline | M3 continua N/D. O1→G2, O2→G1/G3 e O3→G4 preservados, sem renumerar objetivos históricos. |

Validação documental deste ajuste: links/âncoras locais e unicidade dos
identificadores conferidos; fórmula usa a média anterior no denominador, com
checagens aritméticas de sinal, zero/ausência e fronteira estrita −20% para duas
Sprints consecutivas. Valores usados nessas checagens são sintéticos, não dados
do projeto. `git diff --check`, `uv lock --check` e `make lint` aprovados; nenhum
código de produção, teste ou arquivo fora destes dois Markdown foi alterado.
