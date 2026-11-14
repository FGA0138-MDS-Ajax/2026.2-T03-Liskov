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
