# Even 2px outer outline: take a 1px-outline sprite (pl_thin_outline.py output) and add one
# more navy layer on every outside side. Shoe rows (bottom 3) are left as drawn, so the baseline stays.
# usage: python pl_thick_outline.py <thin dir> <out dir>
import sys,os
from PIL import Image
src,out=sys.argv[1],sys.argv[2];os.makedirs(out,exist_ok=True)
NAVY=(1,3,46,255)
for n in ['south','east','north','west']:
    im=Image.open(f'{src}/{n}.png').convert('RGBA');W,H=im.size;px=im.load();y1=im.getbbox()[3]
    add=[(x,y) for y in range(y1-3) for x in range(W) if px[x,y][3]==0 and
         any(0<=x+dx<W and 0<=y+dy<H and px[x+dx,y+dy][3] for dx,dy in((1,0),(-1,0),(0,1),(0,-1)))]
    for x,y in add:px[x,y]=NAVY
    im.save(f'{out}/{n}.png');print(n,'added',len(add))
