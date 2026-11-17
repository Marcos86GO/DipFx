"""Prueba extremo a extremo en Chrome sin cabeza con cámara simulada y detector facial simulado.
Requisitos: pip install playwright && playwright install chromium   (o CHROME_PATH=/ruta/a/chrome)
            python3 tests/fixtures/gen_e2e.py
Comprueba: método montura en vivo (calibración de pantalla, plantilla, ráfaga apilada, bordes exteriores),
fichas de personas e histórico (dos medidas, persistencia, CSV), método tarjeta en vivo y método iris con fotos subidas."""
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
async def page_with_camera(p,video,query=''):
    args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream',f'--use-file-for-fake-video-capture={os.path.join(OUT,video)}']
    kw={'args':args}
    if os.environ.get('CHROME_PATH'): kw['executable_path']=os.environ['CHROME_PATH']
    b=await p.chromium.launch(**kw); pg=await b.new_page(viewport={'width':1400,'height':1000},locale='es-ES'); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
        if 'vision_bundle.mjs' in r.request.url: await r.fulfill(status=200,content_type='application/javascript',body=FAKE)
        else: await r.abort()
    await pg.route('https://cdn.jsdelivr.net/**',route)
    await pg.goto(f'http://127.0.0.1:{PORT}/index.html{query}'); await pg.wait_for_timeout(500)
    return b,pg,errs
def check_common(t,hexp,A,typ):
    check('DIP',num1(t,'DIP lejos'),64.0,0.2); od,os_=num(t,'Mono OD/OI'); check('mono OD',od,31.5,0.2); check('mono OI',os_,32.5,0.2)
    h1,h2=num(t,'Altura OD/OI'); check('altura OD',h1,hexp,0.3); check('altura OI',h2,hexp,0.3)
    check('A',num1(t,'Montura: A'),A,0.3); check('DBL',num1(t,' DBL'),17.0,0.3)
    if typ not in t: fails.append('tipo de montura'); print('  FALLO tipo de montura')
async def measure_frame(pg, first):
    """Paso montura → foto → revisión (método montura). Devuelve el texto de resultados."""
    await pg.wait_for_selector('#tplPanel:not(.hidden)'); await pg.wait_for_timeout(400)
    if first:
        # arrastrar el borde exterior derecho 40 px (= 10 mm con 4 px/mm)
        w0=float(await pg.input_value('#tW')); bb=await pg.locator('#tplCv').bounding_box()
        x=bb['x']+bb['width']/2+66*4; y=bb['y']+bb['height']*0.3
        await pg.mouse.move(x,y); await pg.mouse.down(); await pg.mouse.move(x+20,y); await pg.mouse.move(x+40,y); await pg.mouse.up()
        check('arrastre en la plantilla (mm)',round(float(await pg.input_value('#tW'))-w0,1),10.0,0.15)
        # en ordenador la plantilla ocupa la pantalla y llega al borde inferior
        bb=await pg.locator('#tplCv').bounding_box(); vh=pg.viewport_size['height']
        ok=await pg.locator('#tplPanel.full').count()==1 and abs(bb['y']+bb['height']-vh)<1.5
        print(f"  {'OK ' if ok else 'FALLO'} plantilla pegada al borde inferior (abajo en {bb['y']+bb['height']:.0f} px de {vh})")
        if not ok: fails.append('plantilla abajo')
        # la línea de centros se arrastra en vertical (cerca del borde izquierdo, lejos de las líneas verticales)
        yl=bb['y']+bb['height']-30*4; await pg.mouse.move(bb['x']+200,yl); await pg.mouse.down(); await pg.mouse.move(bb['x']+200,yl-20); await pg.mouse.up()
        ymm=await pg.evaluate("JSON.parse(localStorage.getItem('dipapp.tpl')||'{}').yMm")
        await pg.select_option('#tMount','full'); await pg.select_option('#tMat','acetate'); await pg.select_option('#tPads','no')
        ymm=await pg.evaluate("JSON.parse(localStorage.getItem('dipapp.tpl')).yMm"); check('línea de centros arrastrada (mm desde abajo)',ymm,35.0,0.3)
        await pg.click('#tplPanel details summary')
        for sel,val in (('#tW','131'),('#tAod','52'),('#tDBL','18'),('#tAos','52')): await pg.fill(sel,val); await pg.dispatch_event(sel,'change')
    else:
        w=float(await pg.input_value('#tW')); check('la plantilla recuerda la última montura (mm)',w,131.0,0.05)
    await pg.click('#tplOk')
    if first:
        # primera medida del dispositivo: se pregunta dónde está la cámara (propuesta: arriba en el centro) y se guarda en Ajustes
        await pg.wait_for_selector('#camModal:not(.hidden)',timeout=5000); await pg.click('#camOk')
        st=await pg.text_content('#camPosStatus'); ok='arriba, en el centro' in st
        print(f"  {'OK ' if ok else 'FALLO'} posición de la cámara guardada en Ajustes: {st}")
        if not ok: fails.append('posición de la cámara en ajustes')
        # selfie: las indicaciones aparecen pegadas al borde donde está la cámara (arriba en el centro) y con vista previa en espejo
        await pg.wait_for_selector('#livePanel.selfie:not(.hidden)'); await pg.wait_for_timeout(300)
        g=await pg.locator('#guideCard').bounding_box(); vw=pg.viewport_size['width']
        ok=g['y']<=70 and abs(g['x']+g['width']/2-vw/2)<2
        print(f"  {'OK ' if ok else 'FALLO'} indicaciones junto a la cámara (arriba {g['y']:.0f} px, centro {g['x']+g['width']/2:.0f} de {vw})")
        if not ok: fails.append('indicaciones junto a la cámara')
        await pg.wait_for_selector('#guideCard.look',timeout=20000)
        txt=await pg.inner_text('#msg'); vis=await pg.is_visible('#stage')
        ok='Mira a la cámara' in txt and not vis and await pg.is_visible('#camArrow')
        print(f"  {'OK ' if ok else 'FALLO'} fase final «{txt}» (vista previa oculta: {not vis})")
        if not ok: fails.append('fase mirar a la cámara')
    await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=40000); await pg.wait_for_timeout(800)
    return await pg.input_value('#copyArea')
async def main():
    async with async_playwright() as p:
        # ---------- método montura (por defecto) con fichas de personas ----------
        b,pg,errs=await page_with_camera(p,'frame.y4m')
        print('Método montura (plantilla + ráfaga en vivo) e histórico:')
        if not await pg.is_visible('#scrPanel'): fails.append('calibración inicial'); print('  FALLO no se pide calibrar la pantalla la primera vez')
        await pg.select_option('#scrRef','100')
        await pg.eval_on_selector('#scrRange','e=>{e.value=400;e.dispatchEvent(new Event("input"))}')
        await pg.click('#scrSave')
        st=await pg.inner_text('#scrStatus'); ok='4,000 px/mm' in st; print(f"  {'OK ' if ok else 'FALLO'} calibración guardada: {st}")
        if not ok: fails.append('calibración de pantalla')
        if not await pg.is_visible('#peopleEmpty'): fails.append('vista inicial'); print('  FALLO la vista inicial no muestra la lista vacía de personas')
        # nueva medida → nueva persona
        await pg.click('#newMeasureBtn'); await pg.wait_for_selector('#stepPerson:not(.hidden)')
        await pg.click('#personNewBtn'); await pg.fill('#pfName','Ana Pérez'); await pg.fill('#pfRef','H-0012'); await pg.click('#pfSave')
        t=await measure_frame(pg, True); notes=await pg.text_content('#autoMsg')
        m=re.search(r'Imagen de medida:[^\n]*',notes); print('  ',m.group(0) if m else 'sin nota de ráfaga')
        if 'promedio' not in t: fails.append('ráfaga apilada'); print('  FALLO no se usó el promedio de la ráfaga')
        m=re.search(r'procesado (\d+,\d) s',notes)
        if m: check('tiempo de procesado de la ráfaga (s)',float(m.group(1).replace(',','.')),0,4.0)
        check_common(t,22.5,53.0,'pasta')
        m=re.search(r'diferencia entre referencias (-?\+?\d+,\d) %',t); check('diferencia entre referencias (%)',float(m.group(1).replace(',','.').replace('+','')),0,0.5)
        sel=[await pg.input_value(x) for x in ('#mountSel','#matSel','#padSel')]; ok=sel==['full-acetate','acetate','no']
        print(f"  {'OK ' if ok else 'FALLO'} tipo, material y plaquetas de la plantilla en la revisión: {sel}")
        if not ok: fails.append('tipo de montura elegido')
        await pg.select_option('#imgSel','best'); await pg.wait_for_timeout(1500)
        t2=await pg.input_value('#copyArea'); check('DIP (mejor fotograma)',num1(t2,'DIP lejos'),64.0,0.2)
        await pg.screenshot(path=os.path.join(OUT,'e2e_montura.png'),full_page=True)
        # guardar en la ficha
        if await pg.input_value('#savePerson')=='' : fails.append('persona preseleccionada'); print('  FALLO la persona no está preseleccionada al guardar')
        await pg.fill('#saveFrameName','Acetato 52□18'); await pg.click('#saveBtn')
        await pg.wait_for_selector('#viewPerson:not(.hidden)'); await pg.wait_for_timeout(300)
        n1=await pg.locator('#personMeasures tbody tr').count(); check('medidas en la ficha tras guardar',n1,1,0)
        # segunda medida de la misma persona desde su ficha
        await pg.click('#personMeasureBtn')
        await measure_frame(pg, False); await pg.click('#saveBtn')
        await pg.wait_for_selector('#viewPerson:not(.hidden)'); await pg.wait_for_timeout(300)
        check('medidas en la ficha tras la segunda',await pg.locator('#personMeasures tbody tr').count(),2,0)
        stats=await pg.inner_text('#personStats'); ok='media de 2' in stats; print(f"  {'OK ' if ok else 'FALLO'} resumen de varias medidas: {stats.splitlines()[0] if stats else ''}")
        if not ok: fails.append('resumen del histórico')
        # detalle de una medida guardada
        await pg.click('#personMeasures tbody tr >> nth=0'); await pg.wait_for_selector('#viewRecord:not(.hidden)')
        rb=await pg.inner_text('#recordBody'); check('DIP en la medida guardada',num1(rb,'DIP de lejos'),64.0,0.2)
        if 'Pasta (acetato)' not in rb or 'plaquetas: no' not in rb: fails.append('material guardado'); print('  FALLO la medida guardada no recoge material y plaquetas')
        if not await pg.locator('#recordBody img.recImg').count(): fails.append('foto guardada'); print('  FALLO la medida no guarda la foto')
        await pg.screenshot(path=os.path.join(OUT,'e2e_registro.png'),full_page=True)
        # persistencia tras recargar y exportación CSV
        await pg.reload(); await pg.wait_for_timeout(800)
        rows=await pg.locator('#peopleTable tbody tr').all_inner_texts()
        ok=len(rows)==1 and 'Ana Pérez' in rows[0] and '\t2\t' in rows[0]; print(f"  {'OK ' if ok else 'FALLO'} datos tras recargar: {rows}")
        if not ok: fails.append('persistencia')
        await pg.click('nav [data-view=settings]')
        async with pg.expect_download() as dl: await pg.click('#exportCsv')
        csv=open(await (await dl.value).path(),encoding='utf-8-sig').read().splitlines()
        ok=len(csv)==3 and csv[1].startswith('Ana Pérez;H-0012;') and ';64' in csv[1]; print(f"  {'OK ' if ok else 'FALLO'} CSV exportado ({len(csv)-1} medidas)")
        if not ok: fails.append('exportación CSV'); print(csv[:2])
        await pg.screenshot(path=os.path.join(OUT,'e2e_ajustes.png'),full_page=True)
        if errs: fails.append('errores JS (montura)'); print('Errores JS:',errs)
        await b.close()
        # ---------- método tarjeta e iris ----------
        b,pg,errs=await page_with_camera(p,'card.y4m','?e2e')
        print('Método tarjeta (en vivo):')
        await pg.click('#scrSkip')
        await pg.click('nav [data-view=settings]'); await pg.select_option('#modeSel','card')
        await pg.click('#newMeasureBtn'); await pg.click('#personSkip')
        # sin calibración no se sabe dónde está la cámara: se pregunta antes de la foto selfie
        await pg.wait_for_selector('#camModal:not(.hidden)',timeout=5000); print('  OK  se pregunta dónde está la cámara')
        await pg.click('#camPickModal button >> nth=1'); await pg.click('#camOk')
        await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=40000); await pg.wait_for_timeout(800)
        t=await pg.input_value('#copyArea')
        check_common(t,22.5,53.0,'Aro completo metálico')
        await pg.screenshot(path=os.path.join(OUT,'e2e_tarjeta.png'),full_page=True)
        print('Método tarjeta, foto hecha por el óptico:')
        await pg.click('nav [data-view=settings]'); await pg.select_option('#whoSel','operator')
        await pg.click('#newMeasureBtn'); await pg.click('#personSkip')
        await pg.wait_for_selector('#livePanel.operator:not(.hidden)'); await pg.wait_for_timeout(300)
        tr=await pg.eval_on_selector('#video','e=>getComputedStyle(e).transform'); ok=tr in ('none','matrix(1, 0, 0, 1, 0, 0)')
        print(f"  {'OK ' if ok else 'FALLO'} vista previa sin espejo para el óptico ({tr})")
        if not ok: fails.append('vista del óptico')
        await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=40000); await pg.wait_for_timeout(800)
        t=await pg.input_value('#copyArea'); check('DIP (óptico)',num1(t,'DIP lejos'),64.0,0.2)
        await pg.click('nav [data-view=settings]'); await pg.select_option('#whoSel','selfie')
        print('Personalización: galbe con plantilla y panto y vértice con foto de perfil:')
        await pg.check('#persChk')
        await pg.click('#newMeasureBtn'); await pg.click('#personSkip')
        await pg.wait_for_selector('#wrapPanel:not(.hidden)'); await pg.wait_for_timeout(500)
        od=lambda t: float(re.search(r'OD (-?\d+,\d)',t).group(1).replace(',','.'))
        w0=od(await pg.inner_text('#wrapVals')); bb=await pg.locator('#wrapCv').bounding_box(); k=96/25.4
        x=bb['x']+bb['width']/2+62*k; y=bb['y']+bb['height']*0.38+6*k
        await pg.mouse.move(x,y); await pg.mouse.down(); await pg.mouse.move(x,y+15); await pg.mouse.move(x,y+30); await pg.mouse.up()
        w1=od(await pg.inner_text('#wrapVals')); ok=w1>w0+3
        print(f"  {'OK ' if ok else 'FALLO'} el galbe OD sigue al punto temporal ({w0} → {w1}°)")
        if not ok: fails.append('plantilla del galbe')
        await pg.click('#wrapOk')
        await pg.wait_for_selector('#profPanel:not(.hidden)',timeout=40000); print('  OK  tras la foto frontal se pide la foto de perfil')
        await pg.click('#profStart')
        await pg.wait_for_selector('#measurePanel:not(.hidden)',timeout=40000); await pg.wait_for_timeout(800)
        res=await pg.inner_text('#results'); tabs=await pg.inner_text('#capTabs')
        ok='Ángulo pantoscópico' in res and 'Distancia al vértice' in res and 'Galbe' in res and 'Foto de perfil' in tabs and await pg.is_disabled('#pVertex')
        print(f"  {'OK ' if ok else 'FALLO'} resultados de personalización y pestaña de perfil")
        if not ok: fails.append('resultados de personalización'); print(res, errs)
        m=re.search(r'Galbe \(OD (-?\d+,\d)',res); check('galbe OD en resultados',float(m.group(1).replace(',','.')),w1,0.15)
        await pg.select_option('#savePerson','__new'); await pg.fill('#pfName','Marta'); await pg.click('#pfSave'); await pg.wait_for_timeout(300)
        await pg.click('#saveBtn'); await pg.wait_for_selector('#viewPerson:not(.hidden)')
        await pg.click('#personMeasures tbody tr >> nth=0'); await pg.wait_for_selector('#viewRecord:not(.hidden)')
        rb=await pg.inner_text('#recordBody'); ok='Ángulo pantoscópico' in rb and 'Galbe' in rb
        print(f"  {'OK ' if ok else 'FALLO'} la medida guardada incluye la personalización")
        if not ok: fails.append('personalización guardada')
        await pg.click('nav [data-view=settings]'); await pg.uncheck('#persChk')
        print('Método iris (2 fotos subidas):')
        await pg.click('nav [data-view=settings]'); await pg.select_option('#modeSel','iris')
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
        # guardar sin persona previa: se crea desde el selector
        await pg.select_option('#savePerson','__new'); await pg.fill('#pfName','Luis'); await pg.click('#pfSave'); await pg.wait_for_timeout(300)
        await pg.click('#saveBtn'); await pg.wait_for_selector('#viewPerson:not(.hidden)')
        check('medida iris guardada en una persona nueva',await pg.locator('#personMeasures tbody tr').count(),1,0)
        await pg.screenshot(path=os.path.join(OUT,'e2e_iris.png'),full_page=True)
        print('Interfaz en inglés:')
        await pg.click('nav [data-view=settings]'); await pg.select_option('#langSel','en'); await pg.wait_for_timeout(300)
        nav=await pg.inner_text('header.top'); ok='People' in nav and 'Settings' in nav and '+ New measurement' in nav and 'Measurement method' in await pg.inner_text('#viewSettings')
        print(f"  {'OK ' if ok else 'FALLO'} menús y ajustes traducidos"); 
        if not ok: fails.append('inglés: menús')
        await pg.click('nav [data-view=people]'); await pg.wait_for_timeout(300)
        ok='Name' in await pg.text_content('#peopleTable thead'); print(f"  {'OK ' if ok else 'FALLO'} lista de personas en inglés")
        if not ok: fails.append('inglés: personas')
        await pg.click('nav [data-view=settings]')
        await pg.set_input_files('#fileN',os.path.join(OUT,'iris_N.png')); await pg.wait_for_timeout(1500)
        await pg.set_input_files('#fileG',os.path.join(OUT,'iris_G.png'))
        try: await pg.wait_for_selector('#viewWizard #measurePanel:not(.hidden)',state='visible',timeout=15000)
        except Exception: print('  ERR', errs, await pg.evaluate('document.querySelector(".view:not(.hidden)").id'), await pg.inner_text('#loadMsg')); raise
        await pg.wait_for_timeout(800)
        for sel,val in (('#rxOdS','-5'),('#rxOsS','-4')): await pg.fill(sel,val); await pg.dispatch_event(sel,'input')
        await pg.wait_for_timeout(400); t=await pg.input_value('#copyArea'); res=await pg.inner_text('#results')
        m=re.search(r'Distance PD: (\d+\.\d)',t); ok=m and abs(float(m.group(1))-64.0)<=0.2 and 'Distance PD' in res and 'Height OS' in res
        print(f"  {'OK ' if ok else 'FALLO'} resultados y texto copiado en inglés ({m.group(0) if m else t[:60]})")
        if not ok: fails.append('inglés: resultados')
        async with pg.expect_download() as dl:
            await pg.click('nav [data-view=settings]'); await pg.click('#exportCsv')
        csv=open(await (await dl.value).path(),encoding='utf-8-sig').read().splitlines()
        ok=csv[0].startswith('Person,Reference,Date,Method') and ',64.' in csv[1]; print(f"  {'OK ' if ok else 'FALLO'} CSV en inglés ({csv[0][:40]}…)")
        if not ok: fails.append('inglés: CSV'); print(csv[:2])
        await pg.select_option('#langSel','es'); await pg.wait_for_timeout(300)
        ok='Personas' in await pg.inner_text('header.top') and 'Método de medida' in await pg.inner_text('#viewSettings')
        print(f"  {'OK ' if ok else 'FALLO'} vuelta al español"); 
        if not ok: fails.append('vuelta al español')
        await pg.screenshot(path=os.path.join(OUT,'e2e_ajustes_es.png'),full_page=True)
        if errs: fails.append('errores JS'); print('Errores JS:',errs)
        await b.close()
asyncio.run(main())
print('\nRESULTADO:', 'TODO OK' if not fails else 'FALLOS: '+', '.join(fails)); sys.exit(1 if fails else 0)
