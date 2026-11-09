# SentIA — consulta rápida para apresentação do PC1

**09/11/2026 · cenário B · código `bfaf7da` · #69 + #70 + correção #71.**
Os PRs estão abertos; esta integração não é a developer. Documentação em
`docs/pc1-documentacao-consolidada`. [Roteiro completo](ROTEIRO_DEMONSTRACAO.md).

1. **Objetivo:** analisar sentimentos de textos em português, com foco em
   publicações de redes sociais sobre temas de interesse.
2. **Problema:** grandes volumes de menções dificultam entender percepções;
   o produto pretende consolidá-las em positivo, negativo e neutro.
3. **Arquitetura:** Streamlit → FastAPI → processamento/classificação → MongoDB.
   Hoje: painel mock separado do pipeline; API só `/health`; banco sem CRUD.
4. **Entregas até aqui:** importadores CSV/TweetSentBR/BPSAD, auditoria, pipeline,
   adaptador BERTweet, baseline, conexão encapsulada, interface de exemplo,
   testes/CI e documentação. XFetch/#65 e experimentos/#64 ficam fora deste SHA.
5. **Demonstração:** abrir painel com aviso Dados de exemplo → indicadores e
   filtros → Entrar (`admin` / `senha-de-exemplo`) → CSV sintético → coleta
   simulada/Atualizar → Sair → `/health` → demo do pipeline → evidências.
6. **Testes:** em 09/11, `bfaf7da`: **461 passed, 0 failed/skipped, 94% de `src`**.
   [Log](evidencias/documentacao/suite.txt); lint/lock e servidores locais verificados.
   AppTest/HTTP/MongoDB/analisador simulados não são estudo de usabilidade ou GQM.
7. **Resultados reais da demo:** painel exibe 17 registros sintéticos, 8/4/5 por
   classe (47%/24%/29%). CSV da demo tem cinco registros; saída BSON é validada.
   Esses valores são de exemplos, não acurácia do modelo.
8. **Limitações:** login/importação/coleta são simulados, sem persistência nem
   classificação real e sem atualizar o dashboard. Rotas administrativas e de
   análises ausentes; gráficos/listagem/resumo pendentes. Sem nova inferência real,
   Atlas ou XFetch nesta auditoria. Métricas BPSAD não reproduzidas, licença
   TweetSentBR e documentos completos Visão/Arquitetura/GQM pendentes.
9. **Próximas entregas:** revisão/aceite dos PRs, contrato único, persistência/API,
   autenticação real, integração e visualizações, avaliação independente e
   decisões de escopo/privacidade. Pesquisa híbrida permanece proposta.

**Fala comum:** “Mostramos incrementos testados e uma interface navegável com
dados de exemplo. O fluxo completo com resultados reais ainda depende de integração.”

**Contingência A:** `b9d8326`, base offline sem #70. Mostrar indicadores/mock,
navegação com Administração placeholder, `/health`, pipeline e evidências
históricas (394 testes/96%, 09/11). Não demonstrar login/filtros/admin novos.
Sem ambiente, apresentar evidência salva e declarar que não é execução ao vivo.
