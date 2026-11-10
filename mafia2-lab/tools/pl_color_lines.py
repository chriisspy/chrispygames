# Coloured lines (Lospec "Pixel Art Outlines Part 2"):
# - the OUTSIDE ring stays navy: it must be darker than the character AND our dark night backgrounds
# - every other navy line (inner ring of the thick outline, hat brim, collar, hair lines) becomes a
#   dark shade of the part it wraps; between two parts, the darker part wins
# - selective outlining: lines on the lit top are a little lighter than lines at the bottom
# - eyes (dark blobs fully inside skin) and shoes (bottom 3 rows) stay as drawn
# - touching colours that can't be told apart at 1x are merged
# usage: python pl_color_lines.py <src dir> <out dir>
import sys, os, colorsys
from collections import Counter
from PIL import Image

# add --all to colour the outside ring too (no navy anywhere)
ALL = '--all' in sys.argv; args = [a for a in sys.argv[1:] if a != '--all']
src, out = args[0], args[1]; os.makedirs(out, exist_ok=True)
NAVY = (1, 3, 46)
VIEWS = ['south', 'east', 'north', 'west']
lum = lambda c: c[0]*.3 + c[1]*.59 + c[2]*.11
dist = lambda a, b: sum((x-y)**2 for x, y in zip(a, b)) ** .5
is_line = lambda p: p[3] and max(p[:3]) < 60 and p[2] >= p[0]

def shade(c, k):
    """darker, a touch more saturated, nudged toward blue (cool shadows)"""
    h, s, v = colorsys.rgb_to_hsv(*(x/255 for x in c))
    s = min(1, s*1.25 + .15); v = v*k
    if s > .2:  # hue shift toward blue/purple, but keep skin warm-ish
        h = h + (0.66 - h) * .12 if h > .25 else h - .03
    return tuple(round(x*255) for x in colorsys.hsv_to_rgb(h % 1, s, v))

def merge_close(ims, th=22):
    cnt = Counter(p[:3] for im in ims for p in im.getdata() if p[3])
    keep = []
    for c, _ in cnt.most_common():
        if not any(dist(c, k) < th for k in keep): keep.append(c)
    near = {c: min(keep, key=lambda k: dist(c, k)) for c in cnt}
    for im in ims:
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                p = px[x, y]
                if p[3]: px[x, y] = near[p[:3]] + (255,)
    return len(cnt), len(keep)

ims = [Image.open(f'{src}/{v}.png').convert('RGBA') for v in VIEWS]
before, after = merge_close(ims)
for v, im in zip(VIEWS, ims):
    W, H = im.size; px = im.load(); x0, y0, x1, y1 = im.getbbox()
    get = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    outer = {(x, y) for y in range(H) for x in range(W) if px[x, y][3] and
             any(get(x+dx, y+dy)[3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    lines = {(x, y) for y in range(H) for x in range(W) if is_line(px[x, y]) and (x, y) not in outer and y < y1-3}
    # group line pixels; a group with only light skin round it is an eye -> keep
    seen, groups = set(), []
    for p in lines:
        if p in seen: continue
        st, g = [p], []
        seen.add(p)
        while st:
            q = st.pop(); g.append(q)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (q[0]+dx, q[1]+dy)
                if n in lines and n not in seen: seen.add(n); st.append(n)
        groups.append(g)
    new = {}
    for g in groups:
        gs = set(g)
        ring = [get(x+dx, y+dy) for x, y in g for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if (x+dx, y+dy) not in gs]
        fills = [r[:3] for r in ring if r[3] and not is_line(r)]
        if fills and all(lum(c) > 150 for c in fills) and len(g) <= 6:
            continue  # eye
        for x, y in g:
            nb = [get(x+dx, y+dy)[:3] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                  if get(x+dx, y+dy)[3] and not is_line(get(x+dx, y+dy))]
            if not nb: continue
            base = min(nb, key=lum)                      # the darker part wins
            t = (y - y0) / max(1, y1 - y0)               # 0 top (lit) .. 1 bottom (shadow)
            new[(x, y)] = shade(base, .62 - .22*t)
    if ALL:  # no navy at all: the outside ring becomes an even darker shade of the part it wraps
        for x, y in outer:
            if y >= y1-3 or not is_line(px[x, y]): continue
            nb = [get(x+dx, y+dy)[:3] for dx in range(-2, 3) for dy in range(-2, 3)
                  if get(x+dx, y+dy)[3] and not is_line(get(x+dx, y+dy))]
            if not nb: continue
            t = (y - y0) / max(1, y1 - y0)
            new[(x, y)] = shade(min(nb, key=lum), .38 - .16*t)
    for (x, y), c in new.items(): px[x, y] = c + (255,)
    im.save(f'{out}/{v}.png')
    print(v, 'recoloured', len(new), 'line pixels')
print('colours merged', before, '->', after)
