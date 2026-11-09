"""Ensaio local com Chrome isolado; não usa credenciais ou serviços externos."""
import argparse
import json
from datetime import datetime, timezone
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--raiz-b', type=Path, default=Path.cwd())
parser.add_argument('--raiz-a', type=Path, default=Path('/tmp/sentia-pc1/base'))
parser.add_argument('--evidencias', type=Path, default=Path('/tmp/sentia-ensaio/evidencias/navegador'))
parser.add_argument('--chrome', default='/usr/bin/google-chrome')
args = parser.parse_args()
ROOT, A, EVID = args.raiz_b.resolve(), args.raiz_a.resolve(), args.evidencias.resolve()
EVID.mkdir(parents=True, exist_ok=True)
procs = []
checks = []


def start(root, nome, port, *, cenario='normal', fonte='mock', api=False):
    log = open(EVID / f'{nome}.log', 'w')
    comando = [str(root / '.venv/bin/python'), '-m']
    if api:
        comando += ['uvicorn', 'src.servico.main:app', '--host', '127.0.0.1', '--port', str(port)]
        health = '/health'
    else:
        comando += ['streamlit', 'run', 'src/apresentacao/app.py', '--server.address=127.0.0.1',
                    f'--server.port={port}', '--server.headless=true', '--browser.gatherUsageStats=false']
        health = '/_stcore/health'
    env = {**os.environ, 'SENTIA_FONTE_DADOS': fonte, 'SENTIA_MOCK_CENARIO': cenario,
           'SENTIA_API_URL': 'http://127.0.0.1:9', 'SENTIA_API_TIMEOUT_SEGUNDOS': '2'}
    proc = subprocess.Popen(comando, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    procs.append((proc, log))
    for _ in range(150):
        if proc.poll() is not None:
            raise RuntimeError(f'{nome} encerrou com {proc.returncode}; consultar log')
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}{health}', timeout=1) as r:
                body = r.read().decode()
                checks.append({'check': nome + ' health', 'http': r.status, 'corpo': body})
                return f'http://127.0.0.1:{port}'
        except (OSError, TimeoutError):
            time.sleep(.1)
    raise RuntimeError(f'Timeout ao iniciar {nome}')


def ready(page):
    page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'", timeout=30000)


def screenshot(page, nome):
    ready(page)
    page.screenshot(path=str(EVID / (nome + '.png')), full_page=True)


def fechar_menu_movel(page, width):
    if width < 600:
        botao = page.get_by_test_id('stSidebarCollapseButton').get_by_role('button')
        if botao.is_visible():
            botao.click(force=True)
            expect(page.get_by_test_id('stSidebar')).not_to_be_in_viewport()


def data(page, rotulo, valor):
    campo = page.get_by_label(rotulo, exact=True)
    for parte, numero in zip(('day', 'month', 'year'), valor.split('/')):
        segmento = campo.locator(f'[data-type="{parte}"]')
        segmento.click()
        segmento.press_sequentially(numero, delay=30)
    campo.locator('[data-type="year"]').press('Tab')


def login(page):
    page.get_by_label('Usuário', exact=True).fill('admin')
    page.get_by_label('Senha', exact=True).fill('senha-de-exemplo')
    page.get_by_role('button', name='Entrar', exact=True).click()
    expect(page.get_by_role('heading', name='Administração', exact=True)).to_be_visible()
    ready(page)
    expect(page.get_by_text('Fonte', exact=True)).to_be_visible()


try:
    api = start(ROOT, 'api-B', 8000, api=True)
    with urllib.request.urlopen(api + '/openapi.json') as r:
        schema = json.load(r)
    assert set(schema['paths']) == {'/health'}, schema['paths'].keys()
    checks.append({'check': 'API sem backend administrativo do #66', 'paths': list(schema['paths'])})
    for rota, metodo in [('/auth/login', 'POST'), ('/datasets', 'POST'), ('/coletas/fontes', 'GET'), ('/analises/resumo', 'GET')]:
        try:
            urllib.request.urlopen(urllib.request.Request(api + rota, method=metodo))
            raise AssertionError('Rota administrativa incorporada: ' + rota)
        except urllib.error.HTTPError as erro:
            assert erro.code == 404
    base = start(ROOT, 'streamlit-B', 18570)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=args.chrome, headless=True,
                                    args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='pt-BR')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(base)
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('17')
        expect(page.get_by_text('Dados de exemplo', exact=False).first).to_be_visible()
        assert page.get_by_role('link', name='Entrar').count() == 1
        assert page.get_by_role('link', name='Administração', exact=True).count() == 0
        for width in (1440, 820, 390):
            amostra = browser.new_page(viewport={'width': width, 'height': 1000})
            amostra.goto(base)
            expect(amostra.get_by_test_id('stMetricValue').first).to_have_text('17')
            screenshot(amostra, f'dashboard-{width}')
            if width == 390:
                amostra.get_by_test_id('stMetricValue').last.scroll_into_view_if_needed()
                screenshot(amostra, 'dashboard-390-inferior')
            scroll = amostra.evaluate('({viewport: innerWidth, document: document.documentElement.scrollWidth, main: document.querySelector(".stMain")?.scrollWidth, mainClient: document.querySelector(".stMain")?.clientWidth})')
            assert scroll['document'] <= scroll['viewport'], scroll
            checks.append({'check': 'dashboard visual', 'largura': width, 'scroll': scroll})
            amostra.close()
        page.set_viewport_size({'width': 1440, 'height': 1000})
        data(page, 'Publicado a partir de', '01/08/2026')
        data(page, 'Publicado até', '31/08/2026')
        page.get_by_role('button', name='Aplicar filtros', exact=True).click()
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('5')
        expect(page.get_by_text('texto(s) sem data de publicação ficaram fora', exact=False)).to_be_visible()
        screenshot(page, 'filtro-agosto')
        data(page, 'Publicado a partir de', '01/09/2026')
        data(page, 'Publicado até', '01/08/2026')
        page.get_by_role('button', name='Aplicar filtros', exact=True).click()
        expect(page.get_by_text('Os filtros anteriores foram mantidos.', exact=False)).to_be_visible()
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('5')
        screenshot(page, 'periodo-invertido')
        page.get_by_role('button', name='Limpar', exact=True).click()
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('17')
        ready(page)
        expect(page.get_by_label('Publicado a partir de', exact=True).locator('[data-type=day]')).to_have_text('dd')
        expect(page.get_by_label('Publicado até', exact=True).locator('[data-type=day]')).to_have_text('dd')
        checks.append({'check': 'periodo-agosto-invertido-limpar', 'resultado': 'aprovado'})
        page.get_by_test_id('stSelectbox').first.click()
        page.get_by_role('option', name='Negativo', exact=True).click()
        # Valores digitados no formulário não alteram indicadores antes do submit.
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('17')
        page.get_by_role('button', name='Aplicar filtros', exact=True).click()
        ready(page)
        screenshot(page, 'filtro-negativo-diagnostico')
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('5')
        screenshot(page, 'filtro-negativo')
        page.get_by_role('button', name='Limpar', exact=True).click()
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('17')
        if not page.get_by_role('link', name='Entrar', exact=True).is_visible():
            page.get_by_role('button', name='Expand sidebar', exact=True).click()
        page.get_by_role('link', name='Entrar', exact=True).click()
        expect(page.get_by_role('heading', name='Entrar como administrador')).to_be_visible()
        screenshot(page, 'login-desktop')
        login(page)
        for width in (1440, 820, 390):
            amostra = browser.new_page(viewport={'width': width, 'height': 1100})
            amostra.goto(base+'/administracao')
            expect(amostra.get_by_role('heading', name='Entrar como administrador')).to_be_visible()
            login(amostra)
            screenshot(amostra, f'administracao-{width}')
            if width == 390:
                amostra.get_by_role('button', name='Iniciar coleta e análise', exact=True).scroll_into_view_if_needed()
                screenshot(amostra, 'administracao-390-inferior')
            assert amostra.evaluate('document.documentElement.scrollWidth <= innerWidth')
            amostra.close()
        page.set_viewport_size({'width': 1440, 'height': 1100})
        page.locator('input[type=file]').set_input_files(str(ROOT / 'tests/fixtures/dataset_valido.csv'))
        page.get_by_role('button', name='Importar', exact=True).click()
        expect(page.get_by_text('5 de 5 registros importados.', exact=False)).to_be_visible()
        screenshot(page, 'importacao-valida')
        sintetico = EVID / 'importacao-descartes.csv'
        sintetico.write_text('texto,fonte\nTexto sintético,sintetica\n,sintetica\nOutro texto,\n', encoding='utf-8')
        page.locator('input[type=file]').set_input_files(str(sintetico))
        page.get_by_role('button', name='Importar', exact=True).click()
        expect(page.get_by_text('1 de 3 registros importados.', exact=False)).to_be_visible()
        expect(page.get_by_text('2 registro(s) descartado(s).', exact=False)).to_be_visible()
        screenshot(page, 'importacao-descartes')
        invalido = EVID / 'importacao-campo-longo.csv'
        invalido.write_text('texto,fonte\n'+('a'*150000)+',sintetica\n', encoding='utf-8')
        page.locator('input[type=file]').set_input_files(str(invalido))
        page.get_by_role('button', name='Importar', exact=True).click()
        expect(page.get_by_text('O CSV está malformado', exact=False)).to_be_visible()
        assert page.get_by_test_id('stException').count() == 0
        screenshot(page, 'importacao-erro-tratado')
        page.get_by_role('button', name='Iniciar coleta e análise', exact=True).click()
        expect(page.get_by_role('button', name='Atualizar situação', exact=True)).to_be_visible()
        page.get_by_role('button', name='Atualizar situação', exact=True).click()
        expect(page.get_by_text('17 texto(s) analisado(s).', exact=False)).to_be_visible()
        screenshot(page, 'coleta-simulada-concluida')
        page.get_by_role('button', name='Sair', exact=True).click()
        expect(page.get_by_role('heading', name='Entrar como administrador')).to_be_visible()
        assert page.get_by_role('link', name='Administração', exact=True).count() == 0
        screenshot(page, 'logout')
        checks.append({'check': 'navegacao-login-importacao-descarte-coleta-logout', 'resultado': 'aprovado'})
        assert not errors, errors
        context.close()
        for nome, cenario, fonte, porta in [('vazio','vazio','mock',18571),('erro','erro','mock',18572),('api-indisponivel','normal','api',18573)]:
            url = start(ROOT, nome, porta, cenario=cenario, fonte=fonte)
            pagina = browser.new_page(viewport={'width': 1440, 'height': 1000})
            pagina.goto(url)
            esperado = 'Nenhuma análise encontrada.' if cenario=='vazio' else ('Erro simulado' if cenario=='erro' else 'Não foi possível conectar')
            expect(pagina.get_by_text(esperado, exact=False).first).to_be_visible()
            screenshot(pagina, nome)
            if cenario=='erro' or fonte=='api':
                pagina.get_by_role('link', name='Entrar', exact=True).click()
                pagina.get_by_label('Usuário', exact=True).fill('admin')
                pagina.get_by_label('Senha', exact=True).fill('senha-de-exemplo')
                pagina.get_by_role('button', name='Entrar', exact=True).click()
                expect(pagina.get_by_text('indisponível' if cenario=='erro' else 'Não foi possível conectar', exact=False).first).to_be_visible()
                screenshot(pagina, nome+'-login')
            checks.append({'check': nome, 'resultado': 'aprovado'})
            pagina.close()
        # Reserva A independente: servidor + indicadores e demo, sem PR #70.
        url_a = start(A, 'streamlit-A', 18569)
        pagina = browser.new_page(viewport={'width': 1440, 'height': 1000})
        pagina.goto(url_a)
        expect(pagina.get_by_test_id('stMetricValue').first).to_have_text('17')
        assert pagina.get_by_role('button', name='Aplicar filtros', exact=True).count()==0
        screenshot(pagina, 'reserva-A-dashboard')
        checks.append({'check': 'cenario A independente', 'resultado': 'aprovado'})
        browser.close()
    (EVID / 'resultado.json').write_text(json.dumps({'checks': checks, 'resultado': 'aprovado', 'data_UTC': datetime.now(timezone.utc).isoformat(), 'sha_B': subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'], text=True).strip(), 'sha_A': subprocess.check_output(['git','-C',str(A),'rev-parse','HEAD'], text=True).strip()}, ensure_ascii=False, indent=2))
    print(json.dumps({'checks':len(checks),'resultado':'aprovado','evidencias':str(EVID)}, ensure_ascii=False))
except Exception as erro:
    # Salva a tela antes de encerrar o navegador no próximo ensaio independente.
    (EVID / 'falha.json').write_text(json.dumps({'checks': checks, 'falha': str(erro)}, ensure_ascii=False, indent=2))
    raise
finally:
    for proc, log in reversed(procs):
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        log.close()
