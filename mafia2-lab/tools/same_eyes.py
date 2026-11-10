# Give every character Beanie's eyes (his hand-finished ones): 2 wide, 3 tall, navy, top-left pixel a
# soft dark plum. Placement copies his Beanie:
#   front: find the two eyes (small dark blobs in the face) -> wipe -> stamp the standard eye, same spot.
#          If only one is found, the other is mirrored across the face.
#   side:  PixelLab often draws the side eye touching the face edge or hides it, so it is PLACED:
#          eye bottom = top of the face skin + the same gap as on this character's front view,
#          eye sits 2 skin pixels in from the front of the face (exactly like his Beanie).
#   left = mirror of right. His Beanie is the reference and is never touched.
# usage: python same_eyes.py <final dir> [<final dir> ...]
import sys
from collections import Counter
from PIL import Image, ImageOps

NAVY, SOFT = (1, 3, 46), (53, 34, 51)
EYE = [[SOFT, NAVY], [NAVY, NAVY], [NAVY, NAVY]]          # rows top -> bottom
lum = lambda c: c[0]*.3 + c[1]*.59 + c[2]*.11
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
close = lambda a, b, t=40: sum(abs(x-y) for x, y in zip(a, b)) < t

def blobs(im, top_frac=.62):
    W, H = im.size; px = im.load()
    get = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    dark = {(x, y) for y in range(int(H*top_frac)) for x in range(W) if px[x, y][3] and lum(px[x, y][:3]) < 60}
    seen, out = set(), []
    for p in dark:
        if p in seen: continue
        g, st = [], [p]; seen.add(p)
        while st:
            q = st.pop(); g.append(q)
            for dx, dy in N8:
                n = (q[0]+dx, q[1]+dy)
                if n in dark and n not in seen: seen.add(n); st.append(n)
        xs = [x for x, _ in g]; ys = [y for _, y in g]
        ring = [get(x+dx, y+dy) for x, y in g for dx, dy in N8 if (x+dx, y+dy) not in g]
        out.append((g, (min(xs), min(ys), max(xs), max(ys)), ring))
    return out

def stamp(px, W, H, left, bottom):
    for r, row in enumerate(EYE):
        for c, col in enumerate(row):
            x, y = left + c, bottom - 2 + r
            if 0 <= x < W and 0 <= y < H and px[x, y][3]: px[x, y] = col + (255,)

def wipe(px, W, H, xs, ys, skin, need):
    for y in ys:
        for x in xs:
            if 0 <= x < W and 0 <= y < H and px[x, y][3] and lum(px[x, y][:3]) < 60 and \
               sum(close(px[x+a, y+b][:3], skin, 60) for a, b in N8 if 0 <= x+a < W and 0 <= y+b < H) >= need:
                px[x, y] = skin + (255,)

SIDE_EYE = {'brownhair': 16, 'pinkbob': 17, 'ponytail': 15, 'curly': 14, 'farmer': 15, 'raincoat': 14,
            'redcap': 15, 'mafia': 19, 'doctor': 14, 'jester': 16, 'detective': 18}

for d in sys.argv[1:]:
    if d.rstrip('/').endswith('beanie'): continue   # his hand-finished Beanie is the reference: never touch
    # ---- front ----
    im = Image.open(f'{d}/front.png').convert('RGBA'); W, H = im.size; px = im.load()
    eyes = []
    for g, (x0, y0, x1, y1), ring in blobs(im):
        w, h = x1-x0+1, y1-y0+1
        if len(g) > 12 or h < 2 or h > 4 or w > 3 or any(r[3] == 0 for r in ring): continue
        light = [r[:3] for r in ring if r[3] and lum(r[:3]) > 90 and r[0] >= r[2]]
        if len(light) < .35*len(ring): continue
        eyes.append((g, (x0, y0, x1, y1), Counter(light).most_common(1)[0][0]))
    eyes.sort(key=lambda e: e[1][3])
    pair = None
    for i in range(len(eyes)):
        for j in range(i+1, len(eyes)):
            if abs(eyes[i][1][3]-eyes[j][1][3]) <= 1 and abs(eyes[i][1][0]-eyes[j][1][0]) >= 3:
                pair = [eyes[i], eyes[j]]; break
        if pair: break
    if not pair: pair = eyes[:1]
    skin = pair[0][2]
    for g, _, face in pair:
        for x, y in g: px[x, y] = face + (255,)
    for g, (x0, y0, x1, y1), _ in pair:
        stamp(px, W, H, (x0+x1+1)//2 - 1, y1)
    if len(pair) == 1:   # mirror across the face (skin span on that row)
        g, (x0, y0, x1, y1), _ = pair[0]
        row = [x for x in range(W) if px[x, y1][3] and close(px[x, y1][:3], skin, 60)]
        mid = (min(row) + max(row)) / 2
        left0 = (x0+x1+1)//2 - 1
        other = round(2*mid - (left0 + 1)) - 0
        other = other - 1 if other + 1 > max(row) else other
        wipe(px, W, H, range(other-1, other+3), range(y1-3, y1+2), skin, 2)
        stamp(px, W, H, other, y1)
    eb = max(e[1][3] for e in pair)
    skin_top = min(y for y in range(H) for x in range(W) if px[x, y][3] and close(px[x, y][:3], skin))
    gap = eb - skin_top
    im.save(f'{d}/front.png')
    # ---- side ----
    # eye bottom row per character, read off each side face by eye (10 Nov 2026): one row under the
    # hairline. Column: like his Beanie, the eye sits 4 and 3 px in from the face's outer edge
    # (navy edge, shadow, one skin px, then the eye).
    im = Image.open(f'{d}/right.png').convert('RGBA'); W, H = im.size; px = im.load()
    name = d.rstrip('/').split('/')[-1]
    eb = SIDE_EYE[name]
    edge = max(x for x in range(W) if px[x, eb-1][3])
    left = edge - 4
    wipe(px, W, H, range(left-3, edge-1), range(eb-4, eb+2), skin, 3)   # PixelLab's own eye
    stamp(px, W, H, left, eb)
    im.save(f'{d}/right.png')
    ImageOps.mirror(im).save(f'{d}/left.png')
    print(d.split('/')[-1], 'front eyes', [e[1] for e in pair], 'gap', gap, '| side eye at', (left, eb))
