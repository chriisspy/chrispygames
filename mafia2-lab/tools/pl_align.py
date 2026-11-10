# Line up PixelLab rotations: feet on one baseline, centred on the feet.
# usage: python pl_align.py <dir with south/east/north/west.png> [W H BASE]
import sys
from PIL import Image
d=sys.argv[1];W,H,BASE=(int(v) for v in sys.argv[2:5]) if len(sys.argv)>4 else (32,40,37)
for n in ['south','east','north','west']:
    im=Image.open(f'{d}/{n}.png').convert('RGBA');a=im.getchannel('A');x0,y0,x1,y1=im.getbbox()
    cols=[x for x in range(im.width) for y in range(y1-4,y1) if a.getpixel((x,y))>0]
    fc=(min(cols)+max(cols)+1)/2
    c=Image.new('RGBA',(W,H));c.alpha_composite(im,(round(W/2-fc),BASE-y1));c.save(f'{d}/{n}.png')
