# Changelog

Mudanças disponíveis na referência selecionada do SentIA. **Sem release publicada.**
`[Não lançado]` não inventa uma versão de produto; `0.0.0` no manifesto é um
valor técnico. Convenção: [guia do frontend](docs/frontend/README.md#changelog).

## [Não lançado]

Corte documental: **09/11/2026**, integração experimental `bfaf7da` (#69 + #70 +
correção #71). Os PRs permanecem abertos; estas entradas indicam presença nessa
integração, **não merge em developer/main**. A revisão documental deriva desse
SHA em `docs/pc1-documentacao-consolidada`.

### Adicionado

- Base Streamlit com navegação, indicadores de total/percentuais e estados
  normal, vazio e erro, usando dados de exemplo identificados (#13/#14).
- Filtros de publicação e sentimento, Aplicar/Limpar e aviso de textos sem data,
  na fonte mock (#14; PR #70).
- Login, sessão/expiração/logout e menu de administração de exemplo (#59).
  Upload CSV contabiliza linhas/descartes (#60); coleta tem acompanhamento
  fictício (#61). Não persistem nem classificam dados reais (PR #70).
- Clientes HTTP para propostas de análises/resumo e administração (#19/#58),
  sem rotas correspondentes no backend atual. Wireframes preservados com status.
- Preparação offline PC1: demo CSV sintético → analisador simulado → BSON,
  exemplo de ambiente unificado, template de PR e evidências por SHA (PR #69).
- Índice documental, retrato da arquitetura, contratos de dados, inventário de
  fontes acadêmicas, matriz de rastreabilidade, status das entregas, resumo de
  apresentação e auditoria da documentação nesta revisão.

### Alterado

- Dependências gerenciadas em `pyproject.toml` e `uv.lock`, execução validada com
  Python 3.11; substituem requirements da base anterior (PR #48).
- Makefile e CI com instalação locked, lock check, lint do frontend, verificação
  incremental `F,E9` geral e pytest com cobertura; comandos e limites documentados.
- README e guias técnicos alinhados à integração PC1; relatórios antigos
  identificados como históricos. Novo frontend referenciado por #70.

### Corrigido

- Cliente de análises rejeita tipos, contagens, paginação e datas incompatíveis
  com a proposta; timeout exige número finito positivo e erros não quebram a UI.
- Mock administrativo converte erros de leitura CSV em mensagem compreensível,
  inclusive CSV malformado/campo acima do limite. Regressões isolam o limite
  global do leitor CSV (PR #71, `eb071a0`/`e40acf3`).
- Limpar restaura também os valores visíveis dos filtros no navegador (`bcd75e7`).
- Botões dos filtros preservam rótulos em tablet; cabeçalho de testes deixa de
  citar arquivo de integração administrativa inexistente (PR #71).
- Documentação distingue anotações humanas/previsão e atribui ao pipeline a
  conversão de datas/rótulos e a criação de `data_processamento`.

## Fora da referência selecionada

PR #64 (experimentos BPSAD) e #65 (XFetch) continuam abertos e ausentes de
`bfaf7da`. Correções #67/#68 foram incorporadas às branches desses PRs, mas não
à referência desta documentação. Não são registradas como funcionalidades
integradas aqui. #66 foi fechado sem merge e substituído por #70; seu backend
administrativo não compõe o produto desta referência.
