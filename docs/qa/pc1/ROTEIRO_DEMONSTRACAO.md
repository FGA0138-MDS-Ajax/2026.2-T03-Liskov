# Roteiro validado de demonstração — PC1

Data: **09/11/2026**. Duração sugerida: 5–8 minutos, sem constituir regra da disciplina.
Cenário principal: **B**, integração `test/pc1-integracao-frontend-atualizado`,
SHA `bfaf7da4437493f5ee9b44022d4979623b232add` (#69 + frontend #70 + correção
#71). A branch `docs/pc1-documentacao-consolidada` mantém o mesmo código e acrescenta
esta documentação. Não confundir com `developer`, ainda em `c6fc535` no corte.

Contingência **A**: `chore/pc1-estabilizacao-organizacao`, SHA
`b9d832669e7f49b7a09ef8ad0be6e55959d4c135`, em `/tmp/sentia-pc1/base` neste
computador. Nela não há filtros/login/administração novos do #70.
O roteiro anterior está preservado no [histórico Git](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/blob/b9d832669e7f49b7a09ef8ad0be6e55959d4c135/docs/qa/pc1/ROTEIRO_DEMONSTRACAO.md).

## 1. Preparar antes da apresentação

Na raiz do cenário escolhido:

```bash
git rev-parse HEAD
uv sync --locked
make env
uv run --offline python -m scripts.demonstrar_pipeline
uv run --offline pytest -v -ra --cov=src --cov-report=term-missing
```

Preparar dependências antes; offline exige cache/ambiente já instalado. Não é
necessário instalar grupo ML ou configurar serviços externos. `make env`
preserva `.env` existente; não mostrar conteúdo privado durante a apresentação.
Se uv não estiver no PATH neste computador:

```bash
export PATH=/tmp/sentia-pc1/tooling/bin:$PATH
export UV_CACHE_DIR=/tmp/sentia-pc1/cache
export UV_PYTHON_INSTALL_DIR=/tmp/sentia-pc1/python
```

## 2. Apresentar o produto e as fronteiras

“O SentIA busca consolidar sentimentos de textos em português, especialmente
publicações sobre temas em redes sociais. Este incremento mostra aquisição,
contratos de classificação e interface com dados de exemplo. A integração real
com banco e endpoints completos ainda é próxima entrega.”

Mostrar a [arquitetura observada](../../arquitetura.md). São dois fluxos
independentes nesta versão: painel mock e pipeline demonstrativo.

## 3. Cenário principal B — dashboard e administração simulada

Terminal A:

```bash
SENTIA_FONTE_DADOS=mock SENTIA_MOCK_CENARIO=normal uv run --offline streamlit run src/apresentacao/app.py --browser.gatherUsageStats=false
```

Abra `http://localhost:8501`. Mostrar o aviso Dados de exemplo e a ressalva sobre
previsão. Sem filtros, a fonte fixa tem **17 registros**, 8 positivos, 4 neutros e
5 negativos; percentuais inteiros **47%, 24%, 29%**. Isso não é resultado de
inferência executada na apresentação.

1. Selecionar Negativo e aplicar: total 5, classe negativa 100%.
2. Aplicar agosto/2026: somente registros publicados no período; aviso sobre
   registros sem data. Com sentimento Negativo, total 1 e aviso de 1 excluído
   sem data. Limpar restaura o conjunto completo.
3. Mostrar Entrar; usar `admin` / `senha-de-exemplo` (credenciais fictícias).
4. Em Administração, enviar `tests/fixtures/dataset_valido.csv`: cinco válidos.
   Se necessário, usar fixture inválida/vazia para demonstrar mensagem de erro.
5. Em Coleta e análise, iniciar uma fonte de exemplo e clicar Atualizar situação.
   O mock conclui com a contagem fixa de 17, sem usar o CSV recém-enviado.
6. Sair: menu volta para Entrar. Sessão expirada também retorna ao login.

Dizer explicitamente: **login, coleta e importação são fluxos simulados; não há
persistência ou classificação real pelo painel, nem atualização dos indicadores
com o CSV importado**. Gráfico, listagem, resumo textual e busca temática ainda
não aparecem nesta versão.

Estados opcionais: interromper com Ctrl+C e reiniciar com
`SENTIA_MOCK_CENARIO=vazio` ou `erro`. No modo `api`, rotas ausentes geram erro,
sem substituir a resposta por mocks. [Validação](VALIDACAO_FRONTEND_CLICIA.md).

## 4. API básica

Terminal B:

```bash
uv run --offline uvicorn src.servico.main:app --host 127.0.0.1 --port 8000
```

Terminal C:

```bash
curl --fail http://127.0.0.1:8000/health
uv run --offline python -c "from src.servico.main import app; print(list(app.openapi()['paths']))"
```

Esperado: `{"status":"ok"}` e `['/health']`. A documentação OpenAPI automática
não implica endpoints de análise/administração. Não demonstrar backend do #66.

## 5. Pipeline independente

```bash
uv run --offline python -m scripts.demonstrar_pipeline
```

Cinco registros sintéticos → analisador simulado constante → documentos BSON.
Mostrar texto/ID/fonte preservados, rótulo humano separado de `sentimento`,
probabilidades e datas UTC. `data_processamento` é criada pelo pipeline;
`data_publicacao` vem da fonte. BSON serializável não significa MongoDB gravado.
O analisador simulado não mede acurácia BERTweet.

## 6. Testes e resultados reais

Exibir [ensaio atual](RELATORIO_ENSAIO_FINAL.md) e [matriz](MATRIZ_RASTREABILIDADE.md):
09/11/2026, código `bfaf7da`, **461 aprovados, 0 falhas/skips, cobertura `src` 94%**.
Lint e lock verificados. O valor de 394 testes/96% pertence à base histórica
`c6fc535`/`b9d8326`; 471/96% pertence à integração antiga `480ecf1` com outras
entregas. Não misturar contagens. Mocks e testes locais não são métricas GQM.

## 7. Próximas entregas e limites

Revisar/aceitar #69/#70/#71; contrato #19; MongoDB #20; endpoints #21/#23–#25;
autenticação real #58; dashboard integrado/listagem/gráficos/resumo #27–#29;
avaliação reproduzível #17; homologar #64/#65 e decisões de licença/privacidade.
Pesquisa híbrida é proposta. Não afirmar aceite acadêmico, avaliação independente
ou serviço externo homologado sem evidência.

## Contingência A

Se a integração B não estiver disponível, usar a base `b9d8326` preparada.
Os comandos de painel, `/health`, pipeline e suíte são os mesmos, mas mostrar
somente indicadores mock e navegação. A Administração é placeholder; não apresentar
login, filtros, upload ou coleta. A evidência histórica da base registra 394
aprovados/96%, em 09/11/2026, sem atribuir esse número ao cenário B.

Se faltar uv mas a `.venv` correspondente estiver preparada, substituir `uv run
--offline` por `.venv/bin/python -m` para Streamlit/Uvicorn e por
`.venv/bin/python -m scripts.demonstrar_pipeline` para a demo. Para testes,
`.venv/bin/python -m pytest -v -ra`.
Porta ocupada: `--server.port 8502` / `--port 8001`, ajustando as URLs.
Sem ambiente preparado, mostrar [evidências preservadas](evidencias/README.md),
identificando reprodução gravada/documental. Não afirmar execução ao vivo.
