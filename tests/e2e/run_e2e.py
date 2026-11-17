"""Prueba extremo a extremo en Chrome sin cabeza con cámara simulada y detector facial simulado.
Requisitos: pip install playwright && playwright install chromium   (o CHROME_PATH=/ruta/a/chrome)
            python3 tests/fixtures/gen_e2e.py
Comprueba: método montura en vivo (calibración de pantalla, plantilla, ráfaga apilada, bordes exteriores),
método tarjeta en vivo (autocaptura) y método iris con dos fotos subidas."""
import asyncio, http.server, threading, functools, os, re, sys
from playwright.async_api import async_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); OUT=os.path.join(ROOT,'tests','fixtures','out')
PORT=8790
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Quiet,directory=ROOT))
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
async def page_with_camera(p,video):
    args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream',f'--use-file-for-fake-video-capture={os.path.join(OUT,video)}']
    kw={'args':args}
    if os.environ.get('CHROME_PATH'): kw['executable_path']=os.environ['CHROME_PATH']
    b=await p.chromium.launch(**kw); pg=await b.new_page(viewport={'width':1400,'height':1000}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
        if 'vision_bundle.mjs' in r.request.url: await r.fulfill(status=200,content_type='application/javascript',body=FAKE)
        else: await r.abort()
    await pg.route('https://cdn.jsdelivr.net/**',route)
    await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(500)
    return b,pg,errs
def check_common(t,hexp,A,typ):
    check('DIP',num1(t,'DIP lejos'),64.0,0.2); od,os_=num(t,'Mono OD/OI'); check('mono OD',od,31.5,0.2); check('mono OI',os_,32.5,0.2)
    h1,h2=num(t,'Altura OD/OI'); check('altura OD',h1,hexp,0.3); check('altura OI',h2,hexp,0.3)
    check('A',num1(t,'Montura: A'),A,0.3); check('DBL',num1(t,' DBL'),17.0,0.3)
    if typ not in t: fails.append('tipo de montura'); print('  FALLO tipo de montura')
async def main():
    async with async_playwright() as p:
        # ---------- método montura (por defecto) ----------
        b,pg,errs=await page_with_camera(p,'frame.y4m')
        print('Método montura (plantilla + ráfaga en vivo):')
        if not await pg.is_visible('#scrPanel'): fails.append('calibración inicial'); print('  FALLO no se pide calibrar la pantalla la primera vez')
        await pg.select_option('#scrRef','100')
        await pg.eval_on_selector('#scrRange','e=>{e.value=400;e.dispatchEvent(new Event("input"))}')
        await pg.click('#scrSave')
        st=await pg.inner_text('#scrStatus'); ok='4,000 px/mm' in st; print(f"  {'OK ' if ok else 'FALLO'} calibración guardada: {st}")
        if not ok: fails.append('calibración de pantalla')
        await pg.click('#startBtn'); await pg.wait_for_selector('#tplPanel:not(.hidden)'); await pg.wait_for_timeout(1200)   # fin del desplazamiento suave
        # arrastrar el borde exterior derecho 40 px (= 10 mm con 4 px/mm)
        w0=float(await pg.input_value('#tW')); bb=await pg.locator('#tplCv').bounding_box()
        x=bb['x']+bb['width']/2+66*4; y=bb['y']+bb['height']*0.3
        await pg.mouse.move(x,y); await pg.mouse.down(); await pg.mouse.move(x+20,y); await pg.mouse.move(x+40,y); await pg.mouse.up()
        check('arrastre en la plantilla (mm)',round(float(await pg.input_value('#tW'))-w0,1),10.0,0.15)
        for sel,val in (('#tW','131'),('#tAod','52'),('#tDBL','18'),('#tAos','52')): await pg.fill(sel,val); await pg.dispatch_event(sel,'change')
        await pg.click('#tplOk')
        await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=40000); await pg.wait_for_timeout(800)
        t=await pg.input_value('#copyArea'); notes=await pg.inner_text('#autoMsg')
        m=re.search(r'Imagen de medida:[^\n]*',notes); print('  ',m.group(0) if m else 'sin nota de ráfaga')
        if 'promedio' not in t: fails.append('ráfaga apilada'); print('  FALLO no se usó el promedio de la ráfaga')
        m=re.search(r'procesado (\d+,\d) s',notes)
        if m: check('tiempo de procesado de la ráfaga (s)',float(m.group(1).replace(',','.')),0,4.0)
        check_common(t,22.5,53.0,'pasta')
        m=re.search(r'diferencia entre referencias (-?\+?\d+,\d) %',t); check('diferencia entre referencias (%)',float(m.group(1).replace(',','.').replace('+','')),0,0.5)
        # el selector de imagen vuelve a analizar el mejor fotograma
        await pg.select_option('#imgSel','best'); await pg.wait_for_timeout(1500)
        t2=await pg.input_value('#copyArea'); print('  mejor fotograma:'); check('DIP (mejor fotograma)',num1(t2,'DIP lejos'),64.0,0.2)
        await pg.screenshot(path=os.path.join(OUT,'e2e_montura.png'),full_page=True)
        if errs: fails.append('errores JS (montura)'); print('Errores JS:',errs)
        await b.close()
        # ---------- método tarjeta e iris ----------
        b,pg,errs=await page_with_camera(p,'card.y4m')
        print('Método tarjeta (en vivo):')
        await pg.select_option('#modeSel','card')
        await pg.click('#startBtn')
        await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=40000); await pg.wait_for_timeout(800)
        t=await pg.input_value('#copyArea')
        check_common(t,22.5,53.0,'Aro completo metálico')
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
        check('A',num1(t,'Montura: A'),53.0,0.4); check('DBL',num1(t,' DBL'),17.0,0.3)
        m=re.search(r'OD (\d+,\d), OI (\d+,\d)',t); check('vértice OD',float(m.group(1).replace(',','.')),13.0,0.5); check('vértice OI',float(m.group(2).replace(',','.')),13.0,0.5)
        if 'pasta' not in t: fails.append('tipo iris'); print('  FALLO tipo de montura')
        await pg.screenshot(path=os.path.join(OUT,'e2e_iris.png'),full_page=True)
        if errs: fails.append('errores JS'); print('Errores JS:',errs)
        await b.close()
asyncio.run(main())
print('\nRESULTADO:', 'TODO OK' if not fails else 'FALLOS: '+', '.join(fails)); sys.exit(1 if fails else 0)
