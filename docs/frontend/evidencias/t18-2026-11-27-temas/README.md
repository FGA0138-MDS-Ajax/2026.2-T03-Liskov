# T18 nos dois temas: painel novo do dashboard (#121)

Repetição do teste T18 em 27/11/2026, depois do layout novo do dashboard e do tema claro e
escuro (#121). O primeiro registro, do layout anterior, está em `../t18-2026-11-26/`.

## Como foi feito

- Branch `feat/issue-121-dashboard-tema`, com o painel no modo `api` e a API e o MongoDB reais (1.459 análises).
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

## O que mudou no dashboard

- **Tema claro e escuro** em `.streamlit/config.toml`. A troca fica no menu ⋮ (Sistema, Claro ou
  Escuro). Os gráficos usam a paleta do tema ativo, definida em `src/apresentacao/tema.py`.
- **Cartões** em duas linhas de dois, com barra de proporção e "N texto(s)".
- **Distribuição em rosca**, com o total no centro e uma legenda escrita (nome, quantidade e
  percentual), mais a tabela com os mesmos dados.
- **Resumo** com barra de proporção, lado a lado com a distribuição. Em telas estreitas, os dois
  ficam empilhados.
- **Etiqueta de sentimento na tabela**, com fundo tingido e o nome escrito. O contraste do texto é
  de pelo menos 4,5:1 nos dois temas, conferido em teste.
- **Botões dos filtros** numa linha só.

## Observações

- Até 820 px, a tabela "Análises" rola por dentro, como no registro anterior.
- O campo de arquivo continua com "Upload" e "200MB per file" em inglês, porque é texto fixo do
  Streamlit.
- Só foi testado no Chromium.
- A Administração e o login receberam o tema, mas ainda não o layout novo. Isso fica para um
  segundo PR da #121.
