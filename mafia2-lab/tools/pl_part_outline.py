# Solid part-coloured outline (his rule, 10 Nov 2026):
# every outline/line pixel takes ONE solid dark shade of the part it touches
# (face -> dark skin, beanie -> dark blue, hoodie -> dark grey, hair -> dark brown).
# Both rings of the 2px stroke use the same colour. No gradients, fill colours untouched.
# Eyes (dark blobs inside skin) and shoes (bottom 3 rows) stay as drawn.
# usage: python pl_part_outline.py <even dir> <out dir> [--keep-outer]   (--keep-outer = navy outside ring)
import sys, os, colorsys, math
from collections import Counter, deque
from PIL import Image

KEEP_OUTER = '--keep-outer' in sys.argv
src, out = [a for a in sys.argv[1:] if not a.startswith('--')]
os.makedirs(out, exist_ok=True)
VIEWS = ['south', 'east', 'north', 'west']
is_line = lambda p: p[3] and max(p[:3]) < 60 and p[2] >= p[0]
lum = lambda c: c[0]*.3 + c[1]*.59 + c[2]*.11

def feat(c):  # chroma plane + a bit of value: greys cluster together, hues stay apart
    h, s, v = colorsys.rgb_to_hsv(*(x/255 for x in c))
    return (math.cos(h*6.283)*s, math.sin(h*6.283)*s, v*.3)
fd = lambda a, b: sum((x-y)**2 for x, y in zip(feat(a), feat(b))) ** .5

def dark(c):  # the one solid line colour for a part
    h, s, v = colorsys.rgb_to_hsv(*(x/255 for x in c))
    s = min(1, s*1.2 + .2); v = max(.16, v*.42)
    if h < .15 and s > .3: h = (h - .04) % 1   # skin/hair: redder brown, not khaki
    return tuple(round(x*255) for x in colorsys.hsv_to_rgb(h, s, v))

ims = [Image.open(f'{src}/{v}.png').convert('RGBA') for v in VIEWS]
fills = Counter(p[:3] for im in ims for p in im.getdata() if p[3] and not is_line(p))
parts = []  # [base colour, members]
for c, _ in fills.most_common():
    best = min(parts, key=lambda p: fd(c, p[0]), default=None)
    if best and fd(c, best[0]) < .3: best[1].append(c)
    else: parts.append([c, [c]])
size = {p[0]: sum(fills[m] for m in p[1]) for p in parts}
big = [p for p in parts if size[p[0]] >= 15]
for p in parts:
    if size[p[0]] < 15:
        min(big, key=lambda b: fd(p[0], b[0]))[1].extend(p[1])
parts = big
part_of = {m: p[0] for p in parts for m in p[1]}
LINE = {p[0]: dark(p[0]) for p in parts}
for p in parts: print('part', p[0], '->', LINE[p[0]], len(p[1]), 'shades')

for v, im in zip(VIEWS, ims):
    W, H = im.size; px = im.load(); x0, y0, x1, y1 = im.getbbox()
    get = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    lines = {(x, y) for y in range(H) for x in range(W) if is_line(px[x, y]) and y < y1-3}
    # eyes: small line groups with only light skin around them
    seen, keep = set(), set()
    for p in lines:
        if p in seen: continue
        g, st = [], [p]; seen.add(p)
        while st:
            q = st.pop(); g.append(q)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (q[0]+dx, q[1]+dy)
                if n in lines and n not in seen: seen.add(n); st.append(n)
        gs = set(g)
        ring = [get(x+dx, y+dy) for x, y in g for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (x+dx, y+dy) not in gs]
        f = [r[:3] for r in ring if r[3] and not is_line(r)]
        if len(g) <= 8 and f and sum(lum(c) > 140 for c in f) >= .7*len(f): keep |= gs
    outer = {(x, y) for (x, y) in lines if any(get(x+dx, y+dy)[3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    todo = lines - keep - (outer if KEEP_OUTER else set())
    # grow out from the fill one ring at a time; each line pixel takes the part of the pixels
    # one ring further in, and where two parts meet the darker part wins (Lospec rule)
    owner = {(x, y): part_of[px[x, y][:3]] for y in range(H) for x in range(W)
             if px[x, y][3] and not is_line(px[x, y])}
    left = set(todo)
    while left:
        layer = {}
        for (x, y) in left:
            near = {owner[(x+dx, y+dy)] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (x+dx, y+dy) in owner}
            if near: layer[(x, y)] = min(near, key=lum)
        if not layer: break
        owner.update(layer); left -= set(layer)
    new = {n: LINE[owner[n]] for n in todo if n in owner}
    for (x, y), c in new.items(): px[x, y] = c + (255,)
    im.save(f'{out}/{v}.png'); print(v, 'line pixels coloured', len(new))
