import sys
from PIL import Image
from collections import Counter
# usage: clean.py out_prefix TH img1 img2 ... -> merges near-same colours across all views
pre,TH,files=sys.argv[1],float(sys.argv[2]),sys.argv[3:]
ims=[Image.open(f).convert('RGBA') for f in files]
cnt=Counter(p[:3] for im in ims for p in im.getdata() if p[3])
pal=[]
for c,_ in cnt.most_common():
    if not any(sum((a-b)**2 for a,b in zip(c,p))<TH*TH for p in pal):pal.append(c)
def near(c):return min(pal,key=lambda p:sum((a-b)**2 for a,b in zip(c,p)))
for f,im in zip(files,ims):
    px=im.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=px[x,y]
            px[x,y]=near((r,g,b))+(255,) if a>=128 else (0,0,0,0)
    im.save(pre+f.split('/')[-1].replace('fix_',''))
print(len(cnt),'->',len(pal),'colours')
