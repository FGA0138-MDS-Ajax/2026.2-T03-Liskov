# T18 nos dois temas: painel de alta fidelidade (#121)

Repetição do teste T18 em 27/11/2026, com a #121 completa: dashboard, Administração e login no
layout de alta fidelidade, tema claro e escuro, termos frequentes (#30) e evolução no período. O primeiro registro, do layout anterior, está em `../t18-2026-11-26/`.

## Como foi feito

- Branch `feat/issue-121-dashboard-tema` (versão final), com o painel no modo `api` e a API e o
  MongoDB reais (1.459 análises).
- `scripts/capturar_responsividade.py`, agora com os dois temas. O escuro é ligado simulando a
  preferência de cor do sistema, que o painel segue quando o tema está em "Sistema".
- **Telas:** dashboard, entrada do Administrador, Importar dataset e Pesquisar assunto.
- **Larguras:** 360, 390, 768, 820, 1024, 1280, 1440 e 1920 px.
- **Temas:** claro e escuro.
- **Total:** 64 capturas de página inteira. Os arquivos seguem o padrão `<tela>-<tema>-<largura>.png`.
- **Verificação automática em cada captura:**
  - rolagem horizontal;
  - elementos fora da tela;
  - textos cortados.

  Ficam de fora as tabelas, que rolam por dentro, e o que é recortado por um contêiner que
  cabe na tela, como o preenchimento da barra de progresso.

## Resultado

**64 de 64 capturas sem problema:** nenhuma rolagem horizontal da página, nenhum elemento fora da
tela e nenhum texto cortado, nos dois temas e nas 8 larguras. A conferência visual foi feita
pela PO.

## O que mudou no painel

- **Tema claro e escuro** em `.streamlit/config.toml`. A troca fica no menu ⋮ (Sistema, Claro ou
  Escuro). Os gráficos usam a paleta do tema ativo, definida em `src/apresentacao/tema.py`.
- **Cartões** em duas linhas de dois, com barra de proporção **na cor de cada sentimento** e "N texto(s)".
- **Distribuição em rosca**, com o total no centro e uma legenda com quadradinho colorido, nome,
  quantidade e percentual alinhados, mais a tabela com os mesmos dados.
- **Evolução no período** por dia, semana ou mês (só textos com data, em UTC), com tabela.
- **Termos mais frequentes** em barras (#30, no lugar da nuvem de palavras), com tabela.
- **"Última análise"** no topo, a partir da análise mais recente; **etiqueta "Assunto: X ✕"** que
  remove só o assunto; **selo do sentimento predominante** no resumo.
- **Grade:** indicadores → (distribuição | evolução) → (resumo | termos) → análises. Em telas
  estreitas, tudo fica empilhado.
- **Administração:** envio do CSV ao lado do "Formato esperado"; relatório com 3 métricas e os
  motivos dos descartes; pesquisa em grade; coleta numa linha; 4 contadores de origem, barra de
  resultado e exemplos com etiqueta.
- **Login** centralizado, com "Entrar" largo e "Voltar ao dashboard".
- **Etiqueta de sentimento na tabela**, com fundo tingido e o nome escrito. O contraste do texto é
  de pelo menos 4,5:1 nos dois temas, conferido em teste.
- **Botões dos filtros** numa linha só.

## Observações

- Até 820 px, a tabela "Análises" rola por dentro, como no registro anterior.
- O campo de arquivo continua com "Upload" e "200MB per file" em inglês, porque é texto fixo do
  Streamlit.
- Só foi testado no Chromium.
- O tema é trocado pelo menu ⋮ do Streamlit (Sistema, Claro ou Escuro). Um botão na tela
  recarregaria a página e foi recusado pela PO.
