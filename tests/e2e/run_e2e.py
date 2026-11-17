"""Prueba extremo a extremo en Chrome sin cabeza con cámara simulada y detector facial simulado.
Requisitos: pip install playwright && playwright install chromium   (o CHROME_PATH=/ruta/a/chrome)
            python3 tests/fixtures/gen_e2e.py
Comprueba: método tarjeta en vivo (autocaptura) y método iris con dos fotos subidas."""
import asyncio, http.server, threading, functools, os, re, sys
from playwright.async_api import async_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); OUT=os.path.join(ROOT,'tests','fixtures','out')
PORT=8790
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(http.server.SimpleHTTPRequestHandler,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
FAKE=open(os.path.join(OUT,'fake_vision.mjs')).read()
def num(txt,label):
    m=re.search(label+r'[^\d-]*(-?\d+,\d)\s*/\s*(-?\d+,\d)',txt); return tuple(float(x.replace(',','.')) for x in m.groups())
def num1(txt,label):
    m=re.search(label+r'[^\d-]*(-?\d+,\d)',txt); return float(m.group(1).replace(',','.'))
fails=[]
def check(name,val,exp,tol):
    ok=abs(val-exp)<=tol; print(f"  {'OK ' if ok else 'FALLO'} {name}: {val} (esperado {exp} ± {tol})")
    if not ok: fails.append(name)
async def main():
    args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream',f'--use-file-for-fake-video-capture={os.path.join(OUT,"card.y4m")}']
    async with async_playwright() as p:
        kw={'args':args}
        if os.environ.get('CHROME_PATH'): kw['executable_path']=os.environ['CHROME_PATH']
        b=await p.chromium.launch(**kw); pg=await b.new_page(viewport={'width':1400,'height':1000}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        async def route(r):
            if 'vision_bundle.mjs' in r.request.url: await r.fulfill(status=200,content_type='application/javascript',body=FAKE)
            else: await r.abort()
        await pg.route('https://cdn.jsdelivr.net/**',route)
        await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(500)
        print('Método tarjeta (en vivo):')
        await pg.click('#startBtn')
        await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=30000); await pg.wait_for_timeout(800)
        t=await pg.input_value('#copyArea')
        check('DIP',num1(t,'DIP lejos'),64.0,0.2); od,os_=num(t,'Mono OD/OI'); check('mono OD',od,31.5,0.2); check('mono OI',os_,32.5,0.2)
        h1,h2=num(t,'Altura OD/OI'); check('altura OD',h1,22.5,0.3); check('altura OI',h2,22.5,0.3)
        check('A',num1(t,'Montura: A'),53.0,0.3); check('DBL',num1(t,'DBL'),17.0,0.3)
        if 'Aro completo metálico' not in t: fails.append('tipo tarjeta'); print('  FALLO tipo de montura')
        await pg.screenshot(path=os.path.join(OUT,'e2e_tarjeta.png'),full_page=True)
        print('Método iris (2 fotos subidas):')
        await pg.select_option('#modeSel','iris')
        await pg.set_input_files('#fileN',os.path.join(OUT,'iris_N.png')); await pg.wait_for_timeout(1500)
        await pg.set_input_files('#fileG',os.path.join(OUT,'iris_G.png'))
        await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=15000); await pg.wait_for_timeout(800)
        for sel,val in (('#rxOdS','-5'),('#rxOsS','-4')): await pg.fill(sel,val); await pg.dispatch_event(sel,'input')
        await pg.wait_for_timeout(400); t=await pg.input_value('#copyArea')
        check('DIP',num1(t,'DIP lejos'),64.0,0.2); od,os_=num(t,'Mono OD/OI'); check('mono OD',od,31.5,0.2); check('mono OI',os_,32.5,0.2)
        h1,h2=num(t,'Altura OD/OI'); check('altura OD',h1,22.5,0.4); check('altura OI',h2,22.5,0.4)
        check('A',num1(t,'Montura: A'),53.0,0.4); check('DBL',num1(t,'DBL'),17.0,0.3)
        m=re.search(r'OD (\d+,\d), OI (\d+,\d)',t); check('vértice OD',float(m.group(1).replace(',','.')),13.0,0.5); check('vértice OI',float(m.group(2).replace(',','.')),13.0,0.5)
        if 'pasta' not in t: fails.append('tipo iris'); print('  FALLO tipo de montura')
        await pg.screenshot(path=os.path.join(OUT,'e2e_iris.png'),full_page=True)
        if errs: fails.append('errores JS'); print('Errores JS:',errs)
        await b.close()
asyncio.run(main())
print('\nRESULTADO:', 'TODO OK' if not fails else 'FALLOS: '+', '.join(fails)); sys.exit(1 if fails else 0)
