# Genera fotos sintéticas para las pruebas extremo a extremo:
#  - card_G.png / card.y4m: gafas metálicas + tarjeta (método tarjeta, Rx 0, vértice 12, plano de lente a 420 mm)
#  - frame_G.png / frame.y4m: misma escena con gafas de pasta y sin tarjeta (método montura; ancho exterior 131 mm)
#  - iris_N.png: sin gafas, limbo a 430 mm;  iris_G.png: gafas de pasta, Rx OD -5 / OI -4, vértice 13, 1,5 % más cerca
# Verdad: DIP 64 (31,5/32,5), A 52, B 38, DBL 18, alturas 22 (al borde interior; +0,5 de ranura en aro completo)
import numpy as np, json, math, os, subprocess, shutil
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'out'); os.makedirs(OUT,exist_ok=True)
P=lambda n: os.path.join(OUT,n)
from PIL import Image
W,H=1920,1080; D=math.hypot(W,H); f=D/2/math.tan(math.radians(75/2)); cx,cy=(W-1)/2,(H-1)/2
CR,EL=13.5,3.0
XR={'od':-31.5,'os':32.5}; HB={'od':22.0,'os':22.0}; A_,B_,DBL=52.0,38.0,18.0
rng=np.random.default_rng(3)
yy,xx=np.mgrid[0:H,0:W].astype(float)
def cover(fn):
    acc=np.zeros((H,W))
    for sy in range(3):
        for sx in range(3):
            acc+=fn(xx+(sx+.5)/3-.5, yy+(sy+.5)/3-.5)
    return acc/9
def base():
    return np.full((H,W),178.0)+6*np.sin(xx/110)*np.cos(yy/90)+rng.normal(0,2.5,(H,W))
def paint(img,a,val): return img*(1-a)+val*a
def sdf_rr(X,Y,ccx,ccy,a,b,r):
    qx=np.abs(X-ccx)-(a-r); qy=np.abs(Y-ccy)-(b-r)
    return np.hypot(np.maximum(qx,0),np.maximum(qy,0))+np.minimum(np.maximum(qx,qy),0)-r
def lensdata(F,n=1.5):
    F1=max(0.5,min(12,F+6 if F>=0 else F/2+6)); t=1.5+0.55*F*(0.5/(n-1)) if F>0 else 2.0
    return F1,t,n
def appmag(h,Zf,F,F1,t,n):
    hm,tm=h/1000,t/1000; F2=F-F1/(1-(tm/n)*F1); L1=-1/hm; L1p=L1+F2; L2=L1p/(1-(tm/n)*L1p); L2p=L2+F1
    m=(L1/L1p)*(L2/L2p); l2p=1000/L2p; return m*(Zf+t+h)/(Zf-l2p)
def solveXL(XRt,Zm,rf,F):
    lo,hi=-300.,300.
    for _ in range(200):
        m=(lo+hi)/2; v=m+rf*(m/Zm-(m-XRt)/1000*F)
        if v<XRt: lo=m
        else: hi=m
    return (lo+hi)/2
def draw_eye(img,px,py,r):
    img=paint(img,cover(lambda X,Y:((X-px)/(r*2.4))**2+((Y-py)/(r*0.95))**2<=1),224)
    img=paint(img,cover(lambda X,Y:(X-px)**2+(Y-py)**2<=r*r),78)
    img=paint(img,cover(lambda X,Y:(X-px)**2+(Y-py)**2<=(r*0.33)**2),25)
    return img
def draw_frame(img,Zm,kind,shift=(0,0)):
    s=Zm/f
    for e,sg in (('od',-1),('os',1)):
        bcx=cx+sg*(DBL/2+A_/2)/s; bcy=cy+(HB[e]-B_/2)/s
        d=sdf_rr(xx,yy,bcx,bcy,A_/2/s,B_/2/s,9/s)
        w=4.5 if kind=='acetate' else 1.2
        val=55 if kind=='acetate' else 70
        img=np.where((d>=0)&(d<w/s),val,img)
        if kind=='metal':
            pdx=cx+sg*(DBL/2-3)/s; pdy=cy+6/s
            img=np.where(((xx-pdx)/(1.5/s))**2+((yy-pdy)/(4/s))**2<=1,215,img)
            img=np.where((np.abs(xx-pdx)<0.25/s)&(np.abs(yy-pdy)<5/s),60,img)
    if kind=='acetate':
        img=np.where((np.abs(xx-cx)<DBL/2/s)&(np.abs(yy-(cy-6/s))<2.5/s),55,img)
        for sg in(-1,1): img=np.where((np.abs(xx-(cx+sg*(DBL/2-2.5)/s))<2.5/s)&(yy>cy-6/s)&(yy<cy+12/s),55,img)
    else:
        img=np.where((np.abs(xx-cx)<DBL/2/s)&(np.abs(yy-(cy-8/s))<0.6/s),70,img)
    return img
def marker(img,val): img[0:4,0:4]=val; return img
def save(img,name): Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert('RGB').save(name)
truth={}
# ---- CARD mode, Rx 0, v 12, ZL 420 (lens mid-plane)
ZL=420.; v=12.; F1,t,n=lensdata(0); rf=v+t/2+CR; Zc=ZL-1.5
img=base(); eyes={}
Zlimb=ZL+t/2+v+EL
for e in XR:
    XL=solveXL(XR[e],ZL,rf,0); px,py=cx+XL*f/ZL,cy+solveXL(0,ZL,rf,0)*f/ZL
    r=11.7/2*f/Zlimb*appmag(v+EL,Zlimb-(v+EL)-t,0,F1,t,n); eyes[e]=(px,py,r); img=draw_eye(img,px,py,r)
img=draw_frame(img,ZL,'metal')
sc=Zc/f; x0,x1=cx-42.8/sc,cx+42.8/sc; y0,y1=cy-72/sc,cy-17.6/sc
img=paint(img,cover(lambda X,Y:(X>=x0)&(X<=x1)&(Y>=y0)&(Y<=y1)),246)
img=marker(img,128); save(img,P('card_G.png')); truth['card']={'eyes':eyes}
# ---- método montura: misma escena (mismos ojos, Rx 0, vértice 12, plano de lente a 420 mm), montura de pasta
# de 4,5 mm de aro y sin tarjeta. Ancho exterior a la altura del centro de las cajas = DBL + 2A + 2·4,5 = 131 mm.
img=base()
for e in XR: img=draw_eye(img,*eyes[e])
img=draw_frame(img,ZL,'acetate')
img=marker(img,128); save(img,P('frame_G.png'))
# ---- IRIS mode N (no glasses) Z limbus 430
ZN=430.; img=base(); eN={}
for e in XR:
    rfp=CR-EL; xp=XR[e]*ZN/(ZN+rfp); px,py=cx+xp*f/ZN,cy; r=11.7/2*f/ZN; eN[e]=(px,py,r); img=draw_eye(img,px,py,r)
img=marker(img,10); save(img,P('iris_N.png'))
# ---- IRIS mode G: k=1.015, v=13, Rx OD -5 OS -4, acetate
k=1.015; Z2=ZN/k; v=13.; Rx={'od':-5.,'os':-4.}
L={e:lensdata(Rx[e]) for e in Rx}; tbar=(L['od'][1]+L['os'][1])/2; Zm=Z2-EL-v-tbar/2
img=base(); eG={}
for e in XR:
    F1,t,n=L[e]; rfe=v+t/2+CR
    XL=solveXL(XR[e],Zm,rfe,Rx[e]); YL=solveXL(0,Zm,rfe,Rx[e])
    A=appmag(v+EL,Z2-(v+EL)-t,Rx[e],F1,t,n)
    px,py=cx+XL*f/Zm,cy+YL*f/Zm; r=11.7/2*f/Z2*A; eG[e]=(px,py,r,A); img=draw_eye(img,px,py,r)
img=draw_frame(img,Zm,'acetate')
img=marker(img,240); save(img,P('iris_G.png'))
truth['iris']={'N':eN,'G':eG,'k':k}
json.dump({'W':W,'H':H,'f':f,'cx':cx,'cy':cy,'truth':truth},open(P('truth2.json'),'w'))


# ---- detector facial simulado (sustituye a MediaPipe en las pruebas e2e): devuelve landmarks coherentes
# con cada imagen; distingue la imagen por el píxel marcador (1,1): 10 = sin gafas, 240 = con gafas, 128 = tarjeta
def lmset(eyes, scale=1.0, off=(1.2,-0.8)):
    od,os_=eyes['od'],eyes['os']; Pt={}
    def s(i,x,y): Pt[i]=[x,y]
    o=[od[0]+off[0],od[1]+off[1]]; q=[os_[0]-off[0],os_[1]-off[1]]
    for c,(r,ids) in ((o,(od[2],(468,469,470,471,472))),(q,(os_[2],(473,474,475,476,477)))):
        s(ids[0],c[0],c[1]); s(ids[1],c[0]+r,c[1]); s(ids[2],c[0],c[1]-r); s(ids[3],c[0]-r,c[1]); s(ids[4],c[0],c[1]+r)
    s(33,o[0]-45,o[1]); s(133,o[0]+45,o[1]); s(362,q[0]-45,q[1]); s(263,q[0]+45,q[1]); s(168,cx,cy); s(1,cx,cy+90)
    base={234:(-230,60),454:(230,60),61:(-75,230),291:(75,230),129:(-55,120),358:(55,120),172:(-180,260),397:(180,260),132:(-200,180),361:(200,180),136:(-170,300),365:(170,300),58:(-150,330),288:(150,330),98:(-40,140),327:(40,140)}
    for i,(dx,dy) in base.items(): s(i,cx+dx*scale,cy+dy*scale)
    return [[(Pt[i][0]+0.5)/W,(Pt[i][1]+0.5)/H] if i in Pt else [0.5,0.6] for i in range(478)]
sets={'card':lmset(truth['card']['eyes']),'N':lmset(truth['iris']['N']),'G':lmset(truth['iris']['G'],truth['iris']['k'])}
js="const SETS="+json.dumps(sets)+""";
function mk(arr){const L=arr.map(([x,y])=>({x,y,z:0}));return {faceLandmarks:[L],faceBlendshapes:[{categories:[]}],facialTransformationMatrixes:[{rows:4,columns:4,data:[1,0,0,0,0,1,0,0,0,0,1,0,0,0,-45,1]}]};}
const R={card:mk(SETS.card),N:mk(SETS.N),G:mk(SETS.G)};
function pick(src){try{const v=src.getContext('2d').getImageData(1,1,1,1).data[0];return v<60?R.N:v>200?R.G:R.card;}catch(e){return R.card;}}
export const FilesetResolver={forVisionTasks:async()=>({})};
export const FaceLandmarker={createFromOptions:async()=>({detectForVideo:()=>R.card,detect:(src)=>pick(src)})};
"""
open(P('fake_vision.mjs'),'w').write(js)
if shutil.which('ffmpeg'):
    for n in ('card','frame'):
        subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',P(n+'_G.png'),'-t','8','-r','10','-pix_fmt','yuv420p',P(n+'.y4m')],check=True)
else:
    print('Aviso: sin ffmpeg no se generan card.y4m ni frame.y4m (cámara simulada para las pruebas en vivo)')
print('Fixtures e2e en', OUT)
