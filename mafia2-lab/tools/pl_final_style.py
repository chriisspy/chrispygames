# HIS FINAL STYLE (learned from his hand-finished Beanie, 10 Nov 2026, assets/final/beanie):
#   - outer 1px = navy (1,3,46)
#   - the 1px just inside it = that part's SHADOW: ~a third darker, a bit more saturated, hue nudged
#     toward purple (cool parts) or toward red-plum (warm parts). He reused an existing palette colour
#     when one was close (hat -> its own dark blue, hoodie -> the pants purple-grey).
#   - inner lines (hat brim etc.) use the same shadow of the part they sit on
#   - eyes and shoes stay as drawn
# Input: a 2px-navy sprite set (pl_thick_outline.py output). Output: front/back/left/right, trimmed.
# usage: python pl_final_style.py <even dir> <out dir>
import sys, os, colorsys, math
from collections import Counter
from PIL import Image

src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
NAVY = (1, 3, 46)
VIEWS = {"south": "front", "north": "back", "east": "right"}
is_line = lambda p: p[3] and max(p[:3]) < 60 and p[2] >= p[0]
lum = lambda c: c[0]*.3 + c[1]*.59 + c[2]*.11
dist = lambda a, b: sum((x-y)**2 for x, y in zip(a, b)) ** .5

def feat(c):
    h, s, v = colorsys.rgb_to_hsv(*(x/255 for x in c))
    return (math.cos(h*6.283)*s, math.sin(h*6.283)*s, v*.3)
fd = lambda a, b: sum((x-y)**2 for x, y in zip(feat(a), feat(b))) ** .5

def shadow(c):  # fitted to his four picks (hat, skin, hoodie, hair)
    h, s, v = colorsys.rgb_to_hsv(*(x/255 for x in c))
    if s < .3 and v > .85:                       # pale skin -> dusty rose
        h, s, v = 0.0, s + .14, v*.68
    elif h < .15 or h > .9:                       # warm (hair, browns) -> plum
        h, s, v = (h - .07) % 1, min(1, s + .08), v*.37
    else:                                         # cool (hat, greys) -> toward violet
        h, s, v = h + (.68 - h)*.5, min(1, s*1.1 + .17 if s < .3 else s), v*(.6 if s < .3 else .72)
    return tuple(round(x*255) for x in colorsys.hsv_to_rgb(h % 1, s, v))

ims = {v: Image.open(f'{src}/{v}.png').convert('RGBA') for v in VIEWS}
fills = Counter(p[:3] for im in ims.values() for p in im.getdata() if p[3] and not is_line(p))
parts = []
for c, _ in fills.most_common():
    best = min(parts, key=lambda p: fd(c, p[0]), default=None)
    if best and fd(c, best[0]) < .3: best[1].append(c)
    else: parts.append([c, [c]])
size = {p[0]: sum(fills[m] for m in p[1]) for p in parts}
big = [p for p in parts if size[p[0]] >= 15]
for p in parts:
    if size[p[0]] < 15: min(big, key=lambda b: fd(p[0], b[0]))[1].extend(p[1])
part_of = {m: p[0] for p in big for m in p[1]}
pal = list(fills)
SH = {}
for p in big:
    s = shadow(p[0]); near = min(pal, key=lambda c: dist(c, s))
    SH[p[0]] = near if dist(near, s) < 28 and lum(near) < lum(p[0]) else s   # reuse a palette colour if close
    print('part', p[0], '-> shadow', SH[p[0]])

for v, name in VIEWS.items():
    im = ims[v]; W, H = im.size; px = im.load(); x0, y0, x1, y1 = im.getbbox()
    get = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    lines = {(x, y) for y in range(H) for x in range(W) if is_line(px[x, y]) and y < y1-3}
    outer = {(x, y) for (x, y) in lines if any(get(x+dx, y+dy)[3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    seen, keep = set(), set()
    for p in lines - outer:   # eyes: small dark groups inside skin
        if p in seen: continue
        g, st = [], [p]; seen.add(p)
        while st:
            q = st.pop(); g.append(q)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (q[0]+dx, q[1]+dy)
                if n in lines and n not in outer and n not in seen: seen.add(n); st.append(n)
        gs = set(g)
        f = [get(x+dx, y+dy)[:3] for x, y in g for dx in (-1, 0, 1) for dy in (-1, 0, 1)
             if (x+dx, y+dy) not in gs and get(x+dx, y+dy)[3] and not is_line(get(x+dx, y+dy))]
        if len(g) <= 8 and f and sum(lum(c) > 140 for c in f) >= .7*len(f): keep |= gs
    new = {}
    for (x, y) in lines - outer - keep:
        nb = [get(x+dx, y+dy)[:3] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
              if get(x+dx, y+dy)[3] and not is_line(get(x+dx, y+dy))]
        if not nb:
            nb = [get(x+dx, y+dy)[:3] for dx in range(-2, 3) for dy in range(-2, 3)
                  if get(x+dx, y+dy)[3] and not is_line(get(x+dx, y+dy))]
        if nb:  # the part it touches most (ties: the darker part)
            part = max(Counter(part_of[c] for c in nb).items(), key=lambda kv: (kv[1], -lum(kv[0])))[0]
            new[(x, y)] = SH[part]
    for (x, y), c in new.items(): px[x, y] = c + (255,)
    # outer ring: keep only 1px of navy (drop navy that has no colour behind it), shoes untouched
    for (x, y) in outer:
        if y >= y1-3: continue
        if not any((x+dx, y+dy) in new or (get(x+dx, y+dy)[3] and not is_line(get(x+dx, y+dy)))
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[x, y] = (0, 0, 0, 0)
    im = im.crop(im.getbbox()); im.save(f'{out}/{name}.png'); print(name, im.size)
# his rule: left is an exact mirror of right
from PIL import ImageOps
ImageOps.mirror(Image.open(f'{out}/right.png')).save(f'{out}/left.png'); print('left = mirrored right')
