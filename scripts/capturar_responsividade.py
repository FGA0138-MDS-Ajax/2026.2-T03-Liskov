"""Capturas do teste T18 (#31): painel em 8 larguras, com verificação de transbordo.

Uso, com o painel (``make run``) e a API (``make api``) rodando:

    SENTIA_ADMIN_SENHA_LOCAL='<senha>' \\
        uv run --no-project --with playwright python scripts/capturar_responsividade.py <pasta>

Por padrão captura os dois temas (#121): o escuro é ligado simulando a preferência de cor do
sistema, que o painel segue quando o tema está em "Sistema". Para um tema só, defina
SENTIA_TEMAS=claro ou SENTIA_TEMAS=escuro.

O Playwright não é dependência do projeto: ``--with`` cria um ambiente temporário.
Na primeira vez: ``uv run --no-project --with playwright playwright install chromium``.
"""

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

URL_PAINEL = os.environ.get("SENTIA_PAINEL_URL", "http://127.0.0.1:8501")
USUARIO = os.environ.get("SENTIA_ADMIN_USUARIO", "admin")
LARGURAS = [360, 390, 768, 820, 1024, 1280, 1440, 1920]
ESQUEMAS = {"claro": "light", "escuro": "dark"}

# Procura rolagem horizontal, elementos fora da tela e textos cortados.
# As tabelas (st.dataframe) rolam por dentro, então ficam de fora.
VERIFICACAO = """() => {
  const largura = window.innerWidth;
  const documento = document.documentElement;
  const conteudo = document.querySelector('[data-testid="stMain"]')
                || document.querySelector('[data-testid="stAppViewContainer"]');
  // Um elemento recortado por um ancestral que cabe na tela não aparece para quem usa
  // (por exemplo, o preenchimento da barra de progresso, que desliza dentro do trilho).
  const recortadoNaTela = (el) => {
    for (let a = el.parentElement; a; a = a.parentElement) {
      const o = getComputedStyle(a).overflowX;
      if (o === 'hidden' || o === 'clip') {
        const r = a.getBoundingClientRect();
        if (r.left >= -1 && r.right <= largura + 1) return true;
      }
    }
    return false;
  };
  const fora = [];
  for (const el of document.querySelectorAll('[data-testid="stMain"] *')) {
    if (el.closest('[data-testid="stDataFrame"], .stDataFrame')) continue;
    const caixa = el.getBoundingClientRect();
    if (!caixa.width || !caixa.height) continue;
    const estilo = getComputedStyle(el);
    if (estilo.visibility === 'hidden' || estilo.display === 'none') continue;
    if (recortadoNaTela(el)) continue;
    if (caixa.right > largura + 1 || caixa.left < -1) {
      fora.push((el.getAttribute('data-testid') || el.tagName) + ' ' + Math.round(caixa.left) + '..' + Math.round(caixa.right));
    }
  }
  const cortados = [];
  const textos = '[data-testid="stMain"] p, [data-testid="stMain"] label, [data-testid="stMain"] h1, '
    + '[data-testid="stMain"] h2, [data-testid="stMain"] h3, [data-testid="stMetricValue"], '
    + '[data-testid="stMetricLabel"], button';
  for (const el of document.querySelectorAll(textos)) {
    const estilo = getComputedStyle(el);
    if ((estilo.overflow === 'hidden' || estilo.textOverflow === 'ellipsis') && el.scrollWidth > el.clientWidth + 1) {
      cortados.push((el.getAttribute('data-testid') || el.tagName) + ': ' + el.innerText.slice(0, 40));
    }
  }
  return {
    pagina_inexistente: document.body.innerText.includes('Page not found'),
    rolagem_horizontal_documento: documento.scrollWidth > largura + 1,
    rolagem_horizontal_conteudo: conteudo ? conteudo.scrollWidth > conteudo.clientWidth + 1 : null,
    elementos_fora_da_tela: fora.slice(0, 15),
    total_fora: fora.length,
    textos_cortados: cortados.slice(0, 15),
    altura: conteudo ? conteudo.scrollHeight : documento.scrollHeight,
  };
}"""


def esperar_painel(pagina: Page) -> None:
    """Espera o Streamlit terminar de desenhar a tela."""
    pagina.wait_for_load_state("networkidle")
    pagina.wait_for_selector('[data-testid="stMain"]', timeout=60_000)
    pagina.wait_for_function(
        "() => !document.querySelector('[data-testid=\"stStatusWidgetRunningIcon\"]')",
        timeout=60_000,
    )
    pagina.wait_for_timeout(3_500)


def capturar(pagina: Page, pasta: Path, tela: str, largura: int, tema: str) -> dict:
    """Verifica a tela e salva a captura da página inteira."""
    resultado = pagina.evaluate(VERIFICACAO)
    altura_original = pagina.viewport_size["height"]
    # O Streamlit rola dentro do conteúdo, então a janela cresce até a altura da página.
    altura_total = max(altura_original, int(resultado["altura"]) + 40)
    pagina.set_viewport_size({"width": largura, "height": altura_total})
    pagina.wait_for_timeout(1_500)
    pagina.screenshot(path=str(pasta / f"{tela}-{tema}-{largura}.png"))
    pagina.set_viewport_size({"width": largura, "height": altura_original})
    return {"tela": tela, "tema": tema, "largura": largura, **resultado}


def passou(resultado: dict) -> bool:
    return not (
        resultado["pagina_inexistente"]
        or resultado["rolagem_horizontal_documento"]
        or resultado["rolagem_horizontal_conteudo"]
        or resultado["total_fora"]
        or resultado["textos_cortados"]
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    senha = os.environ.get("SENTIA_ADMIN_SENHA_LOCAL")
    if not senha:
        print("Defina SENTIA_ADMIN_SENHA_LOCAL com a senha do administrador local.")
        return 2
    pasta = Path(sys.argv[1])
    pasta.mkdir(parents=True, exist_ok=True)

    resultados = []
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch()
        temas = [t.strip() for t in os.environ.get("SENTIA_TEMAS", "claro,escuro").split(",")]
        for tema in temas:
            for largura in LARGURAS:
                altura = 800 if largura < 768 else 900
                contexto = navegador.new_context(
                    viewport={"width": largura, "height": altura},
                    color_scheme=ESQUEMAS[tema],
                )
                pagina = contexto.new_page()

                pagina.goto(f"{URL_PAINEL}/")  # o dashboard é a página padrão
                esperar_painel(pagina)
                resultados.append(capturar(pagina, pasta, "dashboard", largura, tema))

                pagina.goto(f"{URL_PAINEL}/administracao")
                esperar_painel(pagina)
                resultados.append(capturar(pagina, pasta, "login", largura, tema))

                pagina.get_by_label("Usuário").fill(USUARIO)
                pagina.get_by_label("Senha").fill(senha)
                pagina.get_by_role("button", name="Entrar").click()
                pagina.get_by_role("tab", name="Pesquisar assunto").wait_for(timeout=60_000)
                esperar_painel(pagina)
                resultados.append(capturar(pagina, pasta, "admin-importar", largura, tema))

                pagina.get_by_role("tab", name="Pesquisar assunto").click()
                esperar_painel(pagina)
                resultados.append(capturar(pagina, pasta, "admin-pesquisa", largura, tema))
                contexto.close()
        navegador.close()

    (pasta / "resultado.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for resultado in resultados:
        situacao = "ok" if passou(resultado) else "FALHOU"
        print(
            f"{resultado['tela']:15} {resultado['tema']:7} {resultado['largura']:5} {situacao}"
        )
    falhas = sum(not passou(r) for r in resultados)
    print(f"{len(resultados) - falhas} de {len(resultados)} capturas sem problema.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
