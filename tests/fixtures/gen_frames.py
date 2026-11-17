# Genera monturas sintéticas (pasta, metal, nylon, al aire) con geometría conocida: A 52, B 38, DBL 18,
# monoculares 31,5/32,5, alturas 22/23, escala 0,2 mm/px. Salida en tests/fixtures/out/.
import numpy as np, json, sys, math
W,H=1600,900; s=0.2  # mm/px
cx0,cy0=800,420     # frame center (bridge) px, pupil level y
def sdf_rr(X,Y,cx,cy,a,b,r):  # rounded rect half sizes a,b, corner radius r
    qx=np.abs(X-cx)-(a-r); qy=np.abs(Y-cy)-(b-r)
    return np.hypot(np.maximum(qx,0),np.maximum(qy,0))+np.minimum(np.maximum(qx,qy),0)-r
def scene(kind, seed=0):
    rng=np.random.default_rng(seed)
    yy,xx=np.mgrid[0:H,0:W].astype(float)
    img=np.full((H,W),178.0)+8*np.sin(xx/90)*np.cos(yy/70)+rng.normal(0,3,(H,W))
    A,B,DBL=52,38,18
    mono={'od':31.5,'os':32.5}; hgt={'od':22,'os':23}
    truth={}
    for e,sg in (('od',-1),('os',1)):
        bcx=cx0+sg*(DBL/2+A/2)/s
        px=cx0+sg*mono[e]/s; py=cy0
        bcy=py+(hgt[e]-B/2)/s
        truth[e]={'pupil':[px,py],'box':[bcx-A/2/s,bcy-B/2/s,bcx+A/2/s,bcy+B/2/s]}
        d=sdf_rr(xx,yy,bcx,bcy,A/2/s,B/2/s,9/s)
        # eye
        img=np.where(((xx-px)/(14/s))**2+((yy-py)/(6/s))**2<=1,222,img)
        img=np.where((xx-px)**2+(yy-py)**2<=(5.8/s)**2,80,img)
        img=np.where((xx-px)**2+(yy-py)**2<=(2/s)**2,25,img)
        # lower lid crease
        img=np.where((np.abs(yy-(py+8/s))<0.5/s)&(np.abs(xx-px)<10/s),150,img)
        if kind=='acetate':
            img=np.where((d>=0)&(d<4.5/s),55,img)
        elif kind=='metal':
            img=np.where((d>=0)&(d<1.2/s),70,img)
        elif kind=='nylor':
            top=(yy<bcy+2/s)
            img=np.where((d>=0)&(d<1.5/s)&top,65,img)
            img=np.where((d>=0)&(d<0.35/s)&~top,165,img)
        elif kind=='rimless':
            img=np.where((d>=0)&(d<0.3/s),198,img)
        if kind in('metal','nylor','rimless'):
            # pads: small bright/dark blobs on nose flank
            pdx=cx0+sg*(DBL/2-3)/s; pdy=py+6/s
            img=np.where(((xx-pdx)/(1.5/s))**2+((yy-pdy)/(4/s))**2<=1,215,img)
            img=np.where((np.abs(xx-pdx)<0.25/s)&(np.abs(yy-pdy)<5/s),60,img)
            img=np.where((np.abs(xx-(pdx+sg*0.8/s))<0.6/s)&(np.abs(yy-pdy+1/s)<0.6/s),250,img)
    if kind=='acetate':
        # bridge + acetate continuing along nose flanks
        img=np.where((np.abs(xx-cx0)<DBL/2/s)&(np.abs(yy-(cy0-6/s))<2.5/s),55,img)
        for sg in(-1,1):
            img=np.where((np.abs(xx-(cx0+sg*(DBL/2-2.5)/s))<2.5/s)&(yy>cy0-6/s)&(yy<cy0+12/s),55,img)
    elif kind!='none':
        img=np.where((np.abs(xx-cx0)<DBL/2/s)&(np.abs(yy-(cy0-8/s))<0.6/s),70,img)
    img=np.clip(img,0,255).astype(np.uint8)
    return img,truth
import os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'out'); os.makedirs(OUT,exist_ok=True)
for kind in ['acetate','metal','nylor','rimless']:
    img,t=scene(kind,1)
    img.tofile(os.path.join(OUT,f'fr_{kind}.gray')); json.dump({'W':W,'H':H,'s':s,'truth':t},open(os.path.join(OUT,f'fr_{kind}.json'),'w'))
    from PIL import Image; Image.fromarray(img).save(os.path.join(OUT,f'fr_{kind}.png'))
print('ok')
