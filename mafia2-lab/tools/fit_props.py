# fit every cut piece onto each spot it belongs to on the ORIGINAL town (scale, mirror, position)
import numpy as np, cv2, json
from PIL import Image
A='C:/Users/Chris/Dropbox/Documents/chrispy games/town assets/'
town=np.asarray(Image.open('C:/Users/Chris/Dropbox/Documents/claude chrispy/chrispygames/mafia2-lab/assets/town2-1x.png').convert('RGB')).astype(np.float32)
Z=4
big=cv2.resize(town,None,fx=Z,fy=Z,interpolation=cv2.INTER_NEAREST)
bigb=cv2.GaussianBlur(big,(0,0),2)
P={}
def piece(f,flip):
    p=np.asarray(Image.open(A+f).convert('RGBA')).astype(np.float32)
    if flip: p=p[:,::-1].copy()
    return p
# spot: name, file, search box (1x: x0,y0,x1,y1 the piece must sit inside), scale range
SPOTS=[
 ('top','top-post-with-lights.png',(150,225,410,305),(6.0,7.4)),
 ('bottom','bottom-post-with-lights.png',(210,425,350,500),(6.0,7.4)),
 ('side-L','post-with-lights.png',(160,275,200,430),(4.8,8.0)),
 ('side-R','post-with-lights.png',(365,275,400,430),(4.8,8.0)),
 ('bare-L','bare-post.png',(160,275,200,360),(5.0,9.0)),
 ('bare-R','bare-post.png',(365,275,400,360),(5.0,9.0)),
 ('lamp1','lamp-post.png',(146,285,180,356),(6.5,9.5)),
 ('lamp2','lamp-post.png',(146,393,180,474),(6.5,9.5)),
 ('lamp3','lamp-post.png',(380,285,414,356),(6.5,9.5)),
 ('lamp4','lamp-post.png',(380,393,414,474),(6.5,9.5)),
]
def search(f,flip,box,ks):
    p=piece(f,flip)
    x0,y0,x1,y1=box; reg=bigb[y0*Z:y1*Z,x0*Z:x1*Z]
    out=[]
    for k in ks:
        fz=Z/k; w,h=round(p.shape[1]*fz),round(p.shape[0]*fz)
        if h>reg.shape[0] or w>reg.shape[1]: continue
        t=cv2.resize(p,(w,h),interpolation=cv2.INTER_AREA)
        a=t[...,3:]/255; pre=t[...,:3]*a/np.maximum(a,1e-3)
        m=(a[...,0]>0.6).astype(np.float32)
        tb=cv2.GaussianBlur(np.where(m[...,None]>0,pre,0),(0,0),2)
        mb=cv2.GaussianBlur(m,(0,0),2)
        tb=tb/np.maximum(mb[...,None],1e-3)
        m3=np.ascontiguousarray(np.repeat(m[...,None],3,-1))
        r=cv2.matchTemplate(reg,np.ascontiguousarray(tb*m3),cv2.TM_SQDIFF,mask=m3)/(m.sum()*3)
        mn,_,loc,_=cv2.minMaxLoc(r)
        out.append((mn,float(k),flip,(x0*Z+loc[0],y0*Z+loc[1]),(w,h)))
    out.sort(key=lambda r:r[0]); return out
res={}
for name,f,box,(ka,kb) in SPOTS:
    best=None
    for flip in (False,True):
        r=search(f,flip,box,np.arange(ka,kb,0.1))
        k0=r[0][1]
        r=search(f,flip,box,np.arange(k0-0.1,k0+0.11,0.02))
        if best is None or r[0][0]<best[0]: best=r[0]
    mn,k,flip,(X4,Y4),(w,h)=best
    res[name]=dict(file=f,k=round(k,3),flip=flip,x4=int(X4),y4=int(Y4),w4=w,h4=h)
    print(f'{name:7s} k={k:.2f} flip={flip!s:5s} rmse={mn**.5:5.1f}  at 1x x={X4/Z:.2f} y={Y4/Z:.2f}  size {w/Z:.1f}x{h/Z:.1f}  bottom y={(Y4+h)/Z:.2f}')
json.dump(res,open('fit.json','w'),indent=1)
