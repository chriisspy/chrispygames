"""Chris's own town art (12 Nov 2026) -> the game's files.   Run:  python -I tools/make_town_art.py   (from mafia2-lab/)

He drew these in  Dropbox/Documents/chrispy games/town background assets/NEW :
  night.png, day.png        the whole ground, 560 x 750, road and trees painted in (no cabins, no posts)
  cabins/cabin1..10.png     ten huts, 152 x 152 (cabin-5.png and cabin-10.png are huts 5 and 10)
  lights/*.png              chain3, lamp2, post2, strings with the bulbs OFF (for the day)

What this does, and nothing more (it never repaints his art):
  * copies night.png / day.png to assets/town4/
  * moves each hut into the game's 116 x 154 hut frame (his picture sits 17 px right and 3 px up of it)
  * the game counts its hut spots 0-9 and he counts his huts 1-10: hut N goes on spot N, and hut 10 goes on spot 0 (top middle)
  * lights off: his four pictures as they are; chain5 and lamp4 are mirror twins of chain3 and lamp2, so they are his
    pictures flipped, and post1 is his post2 flipped (his call); lamp1 and lamp3 he did not draw, so only their bulb pixels are turned to the same greys he
    used (looked up from his own before/after colours); posts with no bulb are copied unchanged
"""
import os, shutil, sys
from PIL import Image, ImageOps

SRC = r'C:\Users\Chris\Dropbox\Documents\chrispy games\town background assets\NEW'
OUT = 'assets/town4'
LIT = 'assets/town3/props'
HUT_FOR_SPOT = {0: 10}               # spot 0 (top middle) is his hut 10
HUT_DX, HUT_DY = 17, -3              # where the game's hut frame starts inside his 152 x 152 picture

def main():
    os.makedirs(OUT + '/cabins', exist_ok=True); os.makedirs(OUT + '/props-off', exist_ok=True)
    for n in ('night', 'day'):
        im = Image.open(f'{SRC}/{n}.png'); assert im.size == (560, 750), im.size
        im.convert('RGB').save(f'{OUT}/{n}.png', optimize=True)
    for spot in range(10):
        n = HUT_FOR_SPOT.get(spot, spot); p = f'{SRC}/cabins/cabin{n}.png'
        if not os.path.exists(p): p = f'{SRC}/cabins/cabin-{n}.png'
        im = Image.open(p).convert('RGBA'); assert im.size == (152, 152), im.size
        fr = Image.new('RGBA', (116, 154), (0, 0, 0, 0)); fr.paste(im, (-HUT_DX, -HUT_DY))
        assert fr.getchannel('A').getbbox() == (10, 11, 106, 147), fr.getchannel('A').getbbox()
        fr.save(f'{OUT}/cabins/cabin{spot}.png', optimize=True)
    # lights off
    his = {n: Image.open(f'{SRC}/lights/{n}.png').convert('RGBA') for n in ('chain3', 'lamp2', 'post2', 'strings')}
    lut = {}                                                   # lit colour -> the grey he gave it
    for n, off in his.items():
        lit = Image.open(f'{LIT}/{n}.png').convert('RGBA'); assert lit.size == off.size, n
        for a, b in zip(lit.getdata(), off.getdata()):
            if a[3] and a != b: lut.setdefault(a[:3], []).append(b[0])
    lut = {k: round(sum(v) / len(v)) for k, v in lut.items()}
    def grey(c):
        k = min(lut, key=lambda q: (q[0] - c[0]) ** 2 + (q[1] - c[1]) ** 2 + (q[2] - c[2]) ** 2); return lut[k]
    names = [f[:-4] for f in sorted(os.listdir(LIT)) if f.endswith('.png') and not f.startswith('_')]
    for n in names:
        lit = Image.open(f'{LIT}/{n}.png').convert('RGBA')
        if n in his: out = his[n]
        elif n == 'chain5': out = ImageOps.mirror(his['chain3'])
        elif n == 'lamp4': out = ImageOps.mirror(his['lamp2'])
        elif n == 'post1': out = ImageOps.mirror(his['post2'])      # his call: the left post is his right post flipped
        else:
            out = lit.copy(); px = out.load()
            for y in range(out.height):
                for x in range(out.width):
                    r, g, b, a = px[x, y]
                    if a and r > 170 and g > 115 and r - b > 50: v = grey((r, g, b)); px[x, y] = (v, v, v, a)
        assert out.size == lit.size, n
        out.save(f'{OUT}/props-off/{n}.png', optimize=True)
    print('town art copied:', len(names), 'props,', 10, 'huts')

if __name__ == '__main__':
    main()
