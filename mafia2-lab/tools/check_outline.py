# Checks his outline rule on every character (legs excluded):
#   - every pixel on the outside edge is navy
#   - right behind every outside navy pixel there is the coloured shadow line (or an inside navy line/eye),
#     never the raw fill colour
# usage: python check_outline.py <final dir> ...   (needs assets/pixellab/<name> next to it for the raw colours)
import sys, os
from PIL import Image

NAVY = (1, 3, 46)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
bad_total = 0
for d in sys.argv[1:]:
    name = d.rstrip('/').split('/')[-1]
    raw = os.path.join(os.path.dirname(os.path.dirname(d.rstrip('/'))), 'pixellab', name)
    rawcols = set()
    if os.path.isdir(raw):
        for v in ('south', 'north', 'east'):
            rawcols |= {p[:3] for p in Image.open(f'{raw}/{v}.png').convert('RGBA').getdata() if p[3]}
    for v in ('front', 'back', 'right', 'left'):
        im = Image.open(f'{d}/{v}.png').convert('RGBA'); W, H = im.size; px = im.load()
        g = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
        legs_top = H - 3
        not_navy, no_ring = [], []
        for y in range(legs_top - 1):          # body only (above the leg rows and their join)
            for x in range(W):
                if not px[x, y][3]: continue
                outs = [(a, b) for a, b in N4 if g(x+a, y+b)[3] == 0]
                if not outs: continue
                if px[x, y][:3] != NAVY: not_navy.append((x, y)); continue
                for a, b in outs:
                    q = g(x-a, y-b)
                    if q[3] and q[:3] != NAVY and q[:3] in rawcols and (x-a, y-b)[1] < legs_top - 2:
                        if not any(g(x-a+i, y-b+j)[3] == 0 for i, j in N4):   # not a 1px sliver
                            no_ring.append((x-a, y-b))
        bad = len(not_navy) + len(no_ring); bad_total += bad
        flag = 'OK ' if bad == 0 else 'BAD'
        print(f'{flag} {name:10s} {v:6s} edge-not-navy {len(not_navy):3d}  missing-colour-line {len(no_ring):3d}',
              (not_navy + no_ring)[:6] if bad else '')
print('TOTAL problems:', bad_total)
