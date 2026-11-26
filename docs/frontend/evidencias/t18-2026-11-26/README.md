# T18: legibilidade e responsividade do painel (#31)

Evidência do teste T18 em 26/11/2026, no painel da `developer` (`ee240d4`), rodando com a API e o MongoDB reais
(1.016 análises). Não são dados de exemplo.

## Como foi feito

- Painel (`make run`) no modo `api` e API FastAPI sem `--reload`, os dois em `127.0.0.1`.
- Navegador Chromium sem interface, controlado pelo Playwright com `scripts/capturar_responsividade.py`.
- **Larguras:** as 8 definidas pela PO em 07/11: 360, 390, 768, 820, 1024, 1280, 1440 e 1920 px.
- **Telas:** dashboard, entrada do Administrador, Administração → Importar dataset e Administração → Pesquisar
  assunto (com a seção Coleta e análise abaixo). São 4 telas em 8 larguras, num total de 32 capturas de página
  inteira.
- **Verificação automática em cada captura:**
  - rolagem horizontal da página e do conteúdo;
  - elementos saindo da tela;
  - textos cortados com reticências ou escondidos.

  As tabelas (`st.dataframe`) ficam fora dessa verificação, porque rolam na horizontal por dentro, como previsto
  no critério "com rolagem quando necessária".
- **Conferência visual** pela PO.

## Resultado

| Largura | Dashboard | Entrar | Importar dataset | Pesquisar assunto |
|---|---|---|---|---|
| 360 | ✅ | ✅ | ✅ | ✅ |
| 390 | ✅ | ✅ | ✅ | ✅ |
| 768 | ✅ | ✅ | ✅ | ✅ |
| 820 | ✅ | ✅ | ✅ | ✅ |
| 1024 | ✅ | ✅ | ✅ | ✅ |
| 1280 | ✅ | ✅ | ✅ | ✅ |
| 1440 | ✅ | ✅ | ✅ | ✅ |
| 1920 | ✅ | ✅ | ✅ | ✅ |

✅ = sem rolagem horizontal da página, sem elemento fora da tela, sem texto cortado e com todas as seções
visíveis. **32 de 32 capturas passaram.**

Os arquivos seguem o padrão `<tela>-<largura>.png`, por exemplo `dashboard-360.png`.

## Observações (não são falhas)

- **Até 820 px, a tabela "Análises" rola na horizontal por dentro**, e as colunas da direita aparecem ao rolar. A
  coluna "Texto" mostra o início do texto, e a página não ganha rolagem lateral.
- **Abaixo de 768 px**, os filtros, os indicadores e os botões ficam em uma coluna, e o menu lateral se recolhe
  no botão `»`. É o comportamento padrão do Streamlit.
- **O campo de arquivo** da importação mostra "Upload" e "200MB per file" em inglês. É texto fixo do componente
  do Streamlit e fica registrado como limitação.
- **O sentimento nunca aparece só pela cor:** o gráfico tem rótulo e percentual em cada barra, e há a tabela
  alternativa "Ver os dados do gráfico em tabela".

## Limitações do teste

- Foi testado só no Chromium. Firefox e Safari não foram testados aqui.
- O teste vale para o layout atual. **O protótipo novo, aprovado em 25/11, muda o layout.** Quando ele entrar,
  rode o script de novo e substitua estas capturas:

  ```bash
  # com o painel e a API rodando (make api e make run)
  SENTIA_ADMIN_SENHA_LOCAL='<senha do admin local>' \
    uv run --no-project --with playwright python scripts/capturar_responsividade.py docs/frontend/evidencias/t18-AAAA-MM-DD
  ```

  Na primeira vez, instale o navegador com `uv run --no-project --with playwright playwright install chromium`.
  O Playwright não entra nas dependências do projeto.
