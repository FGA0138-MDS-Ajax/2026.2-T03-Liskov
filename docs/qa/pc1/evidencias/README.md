# Evidências do PC1 — procedência e limites

Todas as coleções são de **09/11/2026**, salvo a pasta histórica `../../pr44-pr45/`
(homologação de 06/11 identificada no próprio relatório). Logs antigos permanecem
intactos; erros/skips/tentativas intermediárias não foram apagados.

| Coleção | Referência | Como interpretar |
|---|---|---|
| Arquivos `base-*` | Base `c6fc535` e preparação `b9d8326` | 394 testes/96%; cenário A, anterior ao frontend #70 |
| `pr64-*`, `pr65-*`, `pr65-xfetch.txt` | Correções `1cd636e` e `4507aac` | Branches históricas; testes offline, não métricas de modelo ou API externa |
| `integracao-suite.txt` e `integracao-resolucoes.md` | Integração antiga `480ecf1` | 471 testes/96%, combinação diferente da apresentação principal atual |
| `ensaio-final/` | Ensaio mais recente, origem e SHAs nos relatórios | Logs de base, integração #70, falhas/correções e navegador com dados sintéticos |
| `documentacao/suite-ca25e12.txt` | Integração inicial `ca25e12` | 458 testes/94%; reexecução durante a revisão antes das correções posteriores |
| `documentacao/suite-a5f343a.txt` | Integração intermediária `a5f343a` | 460 testes/94%; anterior à correção final de Limpar no navegador |
| `documentacao/suite.txt` | Código congelado identificado no ensaio atual | Reexecução da revisão documental com cobertura; não inferência real |
| `documentacao/execucoes.json` | `bfaf7da`, 09/11/2026 | Manifesto da validação e limitações; inclui contagens atuais/históricas |
| `documentacao/comandos.txt` | Mesmo código da revisão documental | Make env/lint e lock check |
| `documentacao/smoke.json` | SHA/data incluídos no JSON | FastAPI e Streamlit locais 200; OpenAPI só `/health` |
| `documentacao/demo.txt` | Mesmo código da revisão documental | Cinco textos sintéticos, analisador simulado e BSON; sem gravação |
| `documentacao/bpsad.json`, `documentacao/tweetsentbr.json` | Hash do arquivo em cada JSON | Auditoria de metadados/contagens, sem novos textos reais |
| `documentacao/issues.json`, `documentacao/prs.json` | Consulta GitHub datada | Estado administrativo e critérios; não aceite técnico/PO inferido |
| `documentacao/links.json` | Auditoria final de Markdown | Links/âncoras locais e referências GitHub verificáveis; limites externos declarados |

`test_integracao_prs.py` é um artefato histórico de QA para uma combinação que
contém XFetch. Não é parte da suíte padrão (`testpaths=tests`) desta referência;
não executar junto à suíte atual sem reproduzir aquela composição.

O uv/ambiente foram provisionados em `/tmp`; caminhos absolutos nos logs são
procedência da execução, não requisito de instalação em outra máquina.
Snapshots das issues contêm critérios públicos, sem dados novos de usuários ou
credenciais. Capturas do ensaio usam mocks/fixtures sintéticas.
