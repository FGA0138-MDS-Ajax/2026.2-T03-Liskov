# Contratos de dados — aquisição, ML, MongoDB e painel

Referência: integração PC1 `bfaf7da`, 09/11/2026. Contrato observado no código;
o aceite único entre frentes permanece na [issue #19](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/issues/19).

## Entrada dos importadores

CSV genérico: UTF-8 com ou sem BOM, delimitador padrão vírgula. Obrigatórias:
`texto_original` ou `texto`, e `fonte`. Opcionais: `id_origem`/`id`/`identificador`,
`rotulo_original`/`rotulo`/`sentimento`, `data_publicacao`/`data`. A coluna CSV
`sentimento` é interpretada como **rótulo da fonte**, não como inferência.
Colunas adicionais preenchidas vão para `metadados`. Cabeçalhos são normalizados;
colunas sem nome ou duplicadas e estrutura inválida são recusadas.

`iterar_dataset_csv` fornece iterador; `importar_dataset_csv` materializa lista.
Modo estrito interrompe no primeiro erro; modo tolerante registra descartes em
`RelatorioImportacao` (lidos, importados, descartados e motivos). Erros estruturais
de arquivo continuam sendo erros. IDs ausentes são determinísticos por fonte,
posição e conteúdo; reordenar o arquivo pode mudar IDs. Não é deduplicação global.

O adaptador BPSAD lê `review_text`, `rating`, `dataset`, `review_id` e
`review_date`; mapeia para o mesmo contrato. Notas são rótulos indiretos de
sentimento: valores de 1 a 5 são normalizados pelo importador (<2,5 negativo;
<3,5 neutro; demais positivo). Isso exige interpretação metodológica própria.

| Campo | Aquisição | Pipeline / documento para MongoDB | Significado |
|---|---|---|---|
| `id_origem`, `fonte` | Strings não vazias | Preservadas | Identidade e proveniência |
| `texto_original` | String bruta não vazia | Preservada, enviada ao analisador | Sem stemming, stopwords ou TF-IDF externo no BERTweet |
| `rotulo_original` | String ou `None` | Preservado se presente | Anotação da fonte ou nota; nunca previsão |
| `rotulo_padronizado` | `POS`, `NEG`, `NEU` ou `None` | `positivo`, `negativo`, `neutro`, omitido se ausente | Mesma anotação convertida por `converter_rotulo_para_sentia` |
| `sentimento` | Não criado | Uma das três classes por extenso | Previsão do classificador |
| `probabilidades` | Não criado | Três valores finitos entre 0 e 1, soma 1 ± 0,001 | Saída do analisador; não mede acurácia nem certeza humana |
| `modelo` | Não criado | Objeto com nome e versão opcional | Rastreabilidade da previsão |
| `data_publicacao` | String ou `None` | `datetime` UTC, omitida se ausente | Data da fonte; não substituída pela importação |
| `data_processamento` | Não criado | `datetime.now(timezone.utc)` no pipeline | Momento da classificação, não comprova gravação |
| `metadados` | Dicionário opcional, extras CSV como strings | Cópia do dicionário se preenchido | Proveniência extra, sem anonimização automática |

`PipelineClassificacao.processar_registros` recebe iterável de dicionários e
devolve lista de documentos. Processa lotes (padrão 32), preserva ordem e exige
previsões na mesma quantidade. Valida IDs, texto, formato das probabilidades,
rótulos e datas; lote de entrada vazio é erro. Não grava no banco. Uma data
`AAAA-MM-DD` vira meia-noite UTC; timestamp precisa de fuso e é convertido para UTC.
Uma data ausente continua ausente.

## Saída HTTP e painel

O [contrato HTTP proposto](frontend/CONTRATO-API.md) serializa datas como ISO 8601
com fuso. `data_publicacao` pode ser omitida ou nula. No BSON as datas são valores
Date e os opcionais ausentes são omitidos, conforme o [esquema](banco/esquema-mongodb.md).
Essa diferença é de transporte, não uma data inventada.

O painel trabalha com `Analise`, `PaginaAnalises`, `ResumoAnalises`,
`SessaoAdministrador`, `ResultadoImportacao` e `Coleta`, definidos em
[`contrato.py`](../src/apresentacao/contrato.py). O dashboard atual usa resumo,
sem listagem visível. Totais de todas as páginas devem vir da fonte.
`GET /health` é a única rota de negócio implementada no FastAPI desta referência.

## Outras fontes e limites

- TweetSentBR local: sem data/IDs originais/partição oficial; não sustenta avaliação
  independente. [Licença e redistribuição pendentes](tweetsentbr.md).
- BPSAD: fixture sintética disponível; corpus completo e comparação real não
  reproduzidos nesta revisão. [Guia](bpsad.md).
- XFetch: implementação no PR #65, ausente de `bfaf7da`; entrada pretendida com
  rótulos ausentes, fonte `X`, ID/data reais quando disponíveis. [Estado](integracao_xfetch.md).
- O mock administrativo tem parser simplificado próprio. Ele contabiliza linhas,
  mas não chama o importador real e não garante todas as mesmas validações.
  A fonte de coleta de exemplo não corresponde ao arquivo recém-enviado.
- Política documental de não armazenar identificadores de autores não é um
  sanitizador implementado: o CSV pode conter extras ou menções. Curadoria,
  privacidade e aceite entre frentes continuam pendentes.
