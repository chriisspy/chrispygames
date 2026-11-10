# Make the outer outline 1px everywhere: peel outline pixels that touch the outside
# but no coloured (non-outline) pixel. Bottom rows (shoes) are left alone.
# usage: python pl_thin_outline.py <src dir> <out dir>
import sys,os
from PIL import Image
src,out=sys.argv[1],sys.argv[2];os.makedirs(out,exist_ok=True)
def dark(p):return p[3] and max(p[:3])<60 and p[2]>=p[0]   # navy outline family
for n in ['south','east','north','west']:
    im=Image.open(f'{src}/{n}.png').convert('RGBA');W,H=im.size
    for rnd in range(2):
        px=im.load();y1=im.getbbox()[3];kill=[]
        for y in range(H):
            for x in range(W):
                p=px[x,y]
                if not dark(p) or y>=y1-3:continue
                N=lambda dx,dy:px[x+dx,y+dy] if 0<=x+dx<W and 0<=y+dy<H else (0,0,0,0)
                outside=any(N(dx,dy)[3]==0 for dx,dy in((1,0),(-1,0),(0,1),(0,-1)))
                touches_fill=any(N(dx,dy)[3] and not dark(N(dx,dy)) for dx in(-1,0,1) for dy in(-1,0,1))
                if outside and not touches_fill:kill.append((x,y))
        for x,y in kill:px[x,y]=(0,0,0,0)
        print(n,'round',rnd,'peeled',len(kill))
    im.save(f'{out}/{n}.png')
