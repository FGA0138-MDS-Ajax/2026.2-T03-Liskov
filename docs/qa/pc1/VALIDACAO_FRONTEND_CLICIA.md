# Validação do Frontend da Clicia — PR #70 + Correções PR #71

Data: **09/11/2026**
PR principal: [#70](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/70) (`feat/painel-frontend` → `developer`, SHA `61926fe`, autora: Héllen Clícia).
PR de correções: [#71](https://github.com/FGA0138-MDS-Ajax/2026.2-T03-Liskov/pull/71) (`fix/pr70-ensaio-pc1` → `feat/painel-frontend`, autor: Renato Rodrigues).

> O PR #70 substitui o antigo PR #66 (fechado sem merge), mantendo o escopo estritamente na camada `src/apresentacao/`, na documentação de contrato/wireframes (`docs/frontend/`) e nos testes do painel (`tests/test_painel_*.py`).

---

## 1. Funcionalidades Entregues no PR #70

1. **Filtros do Dashboard (`src/apresentacao/secoes/filtros.py` e `paginas/dashboard.py`)**:
   - Filtro por intervalo de datas de publicação (`De` / `Até`) e por sentimento (`Todos`, `Positivo`, `Neutro`, `Negativo`).
   - Rejeição de intervalo invertido (`data_inicio > data_fim`) com mensagem de erro amigável e preservação do último resultado válido.
   - Aviso informativo quando há registros sem `data_publicacao` excluídos pelo filtro de período.
2. **Administração com Login em Modo Mock (`src/apresentacao/paginas/administracao.py` e `fontes/administracao_mock.py`)**:
   - Controle de navegação lateral: exibe apenas `Entrar` quando não autenticado e libera `Administração` + `Sair` após login (`admin` / `senha-de-exemplo` no modo `mock`).
   - Expiração de sessão validada em UTC (`DURACAO_SESSAO = 1h`), retornando à tela de login com aviso.
   - Upload de dataset CSV com validação de codificação UTF-8, verificação das colunas obrigatórias (`texto` ou `texto_original`, e `fonte`) e relatório de registros lidos, importados e descartados (`texto_vazio`, `fonte_vazia`).
   - Simulação de início (`em_andamento`) e consulta (`concluida`) de coleta para as fontes de exemplo (`TweetSentBR` e `Dataset importado de exemplo`).
3. **Contrato e Cliente HTTP Administrativo (`src/apresentacao/fontes/administracao_api.py` e `docs/frontend/CONTRATO-API.md`)**:
   - Proposta de contrato para `/api/admin/sessao`, `/api/admin/datasets` e `/api/admin/coletas`, com tratamento de erros HTTP (`400`, `401`, `403`, `404`, `413`, `415`, `422`, `429`, `500`), timeout e falha de conexão.

---

## 2. Problemas Identificados no QA e Corrigidos no PR #71

| Item | Problema observado no #70 | Correção aplicada no #71 (`fix/pr70-ensaio-pc1`) |
|---|---|---|
| **Leitura de CSV malformado ou com campo gigante** | `csv.DictReader` sem `strict=True` e sem captura de `csv.Error` deixava escapar `_csv.Error` na interface ao enviar CSV com aspas abertas ou campo maior que `131.072` bytes | `csv.DictReader(..., strict=True)` e captura de `csv.Error` convertendo para `ErroFonteDados` com mensagem amigável na tela + teste parametrizado isolando `csv.field_size_limit` |
| **Limpeza dos campos de filtro no navegador** | O botão `Limpar` removia chaves de `st.session_state` após a renderização do `st.form`, fazendo o navegador manter as datas antigas preenchidas nos inputs | Adicionado callback `_limpar_filtros` via `on_click` no `st.form_submit_button("Limpar")` + teste automatizado de limpeza seguida de nova aplicação |
| **Layout dos botões em telas de tablet (820 px)** | `st.columns([1, 1, 4])` truncava o texto de `Aplicar filtros` e `Limpar` com o menu lateral aberto | Ajustado para `st.columns(2)` |
| **Docstring de teste e CI** | Docstring de `tests/test_painel_administracao.py` citava arquivo inexistente `tests/test_api_administracao.py` | Docstring ajustada para refletir o escopo mock e workflow `.github/workflows/ci.yml` alinhado com o PR #69 |

---

## 3. Resultado da Validação

- **Testes do painel (`tests/test_painel_*.py`)**: **153 passed** (incluindo 67 testes novos de filtros e administração).
- **Suíte completa integrada (`origin/developer` `66c22ce` + #69 + #70 + #71)**: **538 passed, 0 failed, 0 skipped**, cobertura de `src/` em **94%**.
- **Lint (`uv run ruff check src/apresentacao tests/test_painel_*.py`)**: `All checks passed!`.
- **Parecer de QA**: **Aprovado para integração**, devendo ser feito primeiro o merge do **#71 → #70** e em seguida do **#70 → `developer`**.
