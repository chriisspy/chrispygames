# HIS FINAL STYLE, learned pixel-by-pixel from his hand-finished Beanie (assets/final/beanie, 10 Nov 2026).
# Input: the cleaned PixelLab turnaround (aligned, purple specks -> navy), e.g. assets/pixellab/beanie.
# Rules:
#   1. the outside edge is a 1px navy line (navy pixels touching the outside stay navy)
#   2. where the line is doubled (a navy pixel right behind the edge), that inner pixel becomes the
#      SHADOW of the part it sits on: ~1/3 darker, hue nudged to violet (cool) or rose/plum (warm),
#      reusing a palette colour when one is close
#   3. inside lines (hat brim, collar...) and eyes stay navy; shoes stay as drawn
#   4. left = exact mirror of right; files trimmed: front/back/left/right.png
# usage: python final_style.py <cleaned pixellab dir> <out dir> [--report his_dir]
import sys, os, colorsys, math
from collections import Counter
from PIL import Image, ImageOps

args = [a for a in sys.argv[1:] if not a.startswith('--')]
src, out = args[0], args[1]; os.makedirs(out, exist_ok=True)
NAVY = (1, 3, 46)
VIEWS = {'south': 'front', 'north': 'back', 'east': 'right'}
is_line = lambda p: p[3] and max(p[:3]) < 60 and p[2] >= p[0]
lum = lambda c: c[0]*.3 + c[1]*.59 + c[2]*.11
dist = lambda a, b: sum((x-y)**2 for x, y in zip(a, b)) ** .5
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

def feat(c):
    h, s, v = colorsys.rgb_to_hsv(*(x/255 for x in c))
    return (math.cos(h*6.283)*s, math.sin(h*6.283)*s, v*.3)
fd = lambda a, b: sum((x-y)**2 for x, y in zip(feat(a), feat(b))) ** .5

def shadow(c):
    # his updated Beanie (12:09, 10 Nov): hat (63,138,200)->(30,58,119), hoodie (117,128,141)->(41,41,74),
    # skin (252,217,181)->(128,76,86), hair (110,52,50)->(31,12,32). That is a purple multiply over the
    # part; least-squares fit of the multiply colour:
    M = (.454, .356, .540)
    return tuple(max(0, round(c[i]*M[i])) for i in range(3))

ims = {v: Image.open(f'{src}/{v}.png').convert('RGBA') for v in VIEWS}

# Dark parts drawn in the outline colour (black hair, a black top hat): a solid navy PATCH inside the
# body (not a thin line, not an eye) is a part, not a line. Lift it to a soft near-black so the navy
# edge + shadow still read around it. A patch = has pixels whose 4 neighbours are all navy too.
LIFT = (30, 27, 18)
for im in ims.values():
    W, H = im.size; px = im.load()
    get = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    edge = {(x, y) for y in range(H) for x in range(W) if is_line(px[x, y]) and any(get(x+dx, y+dy)[3] == 0 for dx, dy in N4)}
    behind = {(x+dx, y+dy) for x, y in edge for dx, dy in N4 if is_line(get(x+dx, y+dy))}
    inner = {(x, y) for y in range(H) for x in range(W) if is_line(px[x, y])} - edge - behind
    seen = set()
    for p in inner:
        if p in seen: continue
        g, st = [], [p]; seen.add(p)
        while st:
            q = st.pop(); g.append(q)
            for dx, dy in N4:
                n = (q[0]+dx, q[1]+dy)
                if n in inner and n not in seen: seen.add(n); st.append(n)
        solid = sum(all(is_line(get(x+dx, y+dy)) for dx, dy in N4) for x, y in g)
        if solid >= 3:
            for x, y in g:
                c = px[x, y]; px[x, y] = tuple(min(255, c[i] + LIFT[i]) for i in range(3)) + (255,)
            # its edge pixels that touch this patch keep the line; the patch itself is now a part

fills = Counter(p[:3] for im in ims.values() for p in im.getdata() if p[3] and not is_line(p))
parts = []
for c, _ in fills.most_common():
    best = min(parts, key=lambda p: fd(c, p[0]), default=None)
    if best and fd(c, best[0]) < .3: best[1].append(c)
    else: parts.append([c, [c]])
size = {p[0]: sum(fills[m] for m in p[1]) for p in parts}
big = [p for p in parts if size[p[0]] >= 15] or parts
for p in parts:
    if p not in big: min(big, key=lambda b: fd(p[0], b[0]))[1].extend(p[1])
part_of = {m: p[0] for p in big for m in p[1]}
SH = {}
for p in big:
    SH[p[0]] = shadow(p[0])
    print('part', p[0], '-> shadow', SH[p[0]])

HIS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'final', 'beanie')
LEGS = {}
for v, name in VIEWS.items():
    hi = Image.open(os.path.join(HIS, name + '.png')).convert('RGBA'); hw, hh = hi.size
    row = [x for x in range(hw) if hi.getpixel((x, hh-4))[3]]          # body's bottom navy row
    cx = (min(row) + max(row)) // 2
    LEGS[v] = [(x - cx, y - (hh-3), hi.getpixel((x, y))[:3]) for y in range(hh-3, hh) for x in range(hw) if hi.getpixel((x, y))[3]]

def leg_rows(im):
    """how many bottom rows are legs: rows where the middle of the body has a gap (two runs)"""
    W, H = im.size; x0, y0, x1, y1 = im.getbbox(); cx = (x0 + x1) // 2; half = max(3, (x1 - x0)//4)
    n = 0
    for y in range(y1-1, y0, -1):
        mid = ''.join('#' if im.getpixel((x, y))[3] else '.' for x in range(cx-half, cx+half+1)).strip('.')
        if '.' in mid: n += 1
        elif n: break
        elif y1-1-y >= 1: break
    return max(3, n)

def dilate(S, W, H):
    return S | {(x+dx, y+dy) for x, y in S for dx, dy in N4 if 0 <= x+dx < W and 0 <= y+dy < H}

L = leg_rows(ims['south']); print('leg rows cut:', L)
for v, name in VIEWS.items():
    im = ims[v]; W, H = im.size; px = im.load(); x0, y0, x1, y1 = im.getbbox()
    get = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    FOOT = y1 - L                                   # PixelLab's legs are cut; his legs go back on
    opaque = {(x, y) for y in range(H) for x in range(W) if px[x, y][3]}
    # PixelLab leaves dark "fuzz" just outside its outline: on the very edge, anything dark counts as line
    edgy = lambda p: is_line(p) or (p[3] and lum(p[:3]) < 55)
    # the outline band: navy reachable from outside through navy (edge + doubled line)
    band, st = set(), [(x, y) for (x, y) in opaque if edgy(px[x, y]) and any(get(x+dx, y+dy)[3] == 0 for dx, dy in N4)]
    band.update(st)
    while st:
        x, y = st.pop()
        for dx, dy in N4:
            n = (x+dx, y+dy)
            if n in opaque and n not in band and is_line(get(*n)):
                # stop at inside lines: only take a navy pixel if it still touches the band's outer side
                if any(m in band and any(get(m[0]+a, m[1]+b)[3] == 0 for a, b in N4) for m in [(x, y)]):
                    band.add(n); st.append(n)
    core = {p for p in opaque if p not in band and p[1] < FOOT - 2}
    # trim whiskers (core pixels hanging on by one side) and crumbs (tiny loose bits) so they
    # don't each grow their own 2px line and look like spikes or smoke
    for _ in range(2):
        core -= {(x, y) for (x, y) in core if sum((x+dx, y+dy) in core for dx, dy in N4) <= 1}
    seen = set()
    for p in list(core):
        if p in seen: continue
        g, st2 = [], [p]; seen.add(p)
        while st2:
            q = st2.pop(); g.append(q)
            for dx, dy in N4:
                n = (q[0]+dx, q[1]+dy)
                if n in core and n not in seen: seen.add(n); st2.append(n)
        if len(g) < 6: core -= set(g)
    # lone navy specks inside the body (1-2 px, not eyes): fill with the colour around them
    for (x, y) in list(core):
        if not is_line(px[x, y]): continue
        nl = [(x+dx, y+dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and is_line(get(x+dx, y+dy)) and (x+dx, y+dy) in core]
        if len(nl) > 1: continue
        ring = [get(x+dx, y+dy)[:3] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if (dx or dy) and (x+dx, y+dy) in core and not is_line(get(x+dx, y+dy))]
        if len(ring) >= 6 and sum(lum(c) > 140 for c in ring) < .7*len(ring):
            px[x, y] = Counter(ring).most_common(1)[0][0] + (255,)
    # rebuild the stroke from the core: ring 1 = shadow of the part, ring 2 = navy
    r1 = dilate(core, W, H) - core
    r2 = dilate(core | r1, W, H) - core - r1
    out_px = {}
    for (x, y) in r1:
        nb = [get(x+dx, y+dy)[:3] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
              if (x+dx, y+dy) in core and not is_line(get(x+dx, y+dy))]
        if not nb:
            nb = [get(x+dx, y+dy)[:3] for dx in range(-2, 3) for dy in range(-2, 3)
                  if (x+dx, y+dy) in core and not is_line(get(x+dx, y+dy))]
        if not nb:   # still nothing: the nearest real colour anywhere in the body
            cands = [p for p in core if not is_line(get(*p))]
            if cands:
                q = min(cands, key=lambda p: (p[0]-x)**2 + (p[1]-y)**2); nb = [get(*q)[:3]]
        part = max(Counter(part_of[c] for c in nb).items(), key=lambda kv: (kv[1], -lum(kv[0])))[0] if nb else None
        out_px[(x, y)] = SH[part] if part else NAVY
    for p in r2: out_px[p] = NAVY
    res = Image.new('RGBA', (W, H))
    rp = res.load()
    for p in core: rp[p] = px[p]
    for p, c in out_px.items(): rp[p] = c + (255,)
    # his legs, under the body's bottom navy row
    by = max(y for (x, y) in out_px); row = [x for (x, y) in out_px if y == by]
    cx = (min(row) + max(row)) // 2               # whole pixels only (half pixels made striped legs)
    for dx, dy, c in LEGS[v]:
        X, Y = cx + dx, by + 1 + dy
        if 0 <= X < W and 0 <= Y < H: rp[X, Y] = c + (255,)
    res = res.crop(res.getbbox()); res.save(f'{out}/{name}.png'); print(name, res.size)
ImageOps.mirror(Image.open(f'{out}/right.png')).save(f'{out}/left.png')

if '--report' in sys.argv:
    his = sys.argv[sys.argv.index('--report')+1]
    for n in ['front', 'right', 'back', 'left']:
        a = Image.open(f'{his}/{n}.png').convert('RGBA'); b = Image.open(f'{out}/{n}.png').convert('RGBA')
        if a.size != b.size: print(n, 'size differs', a.size, b.size); continue
        tot = same = 0
        for y in range(a.height):
            for x in range(a.width):
                p, q = a.getpixel((x, y)), b.getpixel((x, y))
                if p[3] or q[3]:
                    tot += 1; same += p[3] == q[3] and (p[3] == 0 or dist(p[:3], q[:3]) < 4)
        print(n, round(100*same/tot, 1), '% same as his')
