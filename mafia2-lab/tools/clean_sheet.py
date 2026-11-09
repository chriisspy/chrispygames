"""Turn one AI turnaround sheet (4 poses on magenta) into 4 clean game sprites.

Usage: python -I clean_sheet.py sheet.png out_dir name
Writes name_front.png, name_left.png, name_right.png, name_back.png.
Each sprite: one colour per true art pixel, a trimmed palette, stray pixels
removed, and a fresh outline exactly 1 pixel thick all the way round.
"""
import sys, os
from collections import Counter
import numpy as np
from PIL import Image

src, out, name = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
OUT = (27, 23, 48)

im = np.asarray(Image.open(src).convert('RGB')).astype(int)
H, W, _ = im.shape
r, g, b = im[..., 0], im[..., 1], im[..., 2]
bg = ((255 - r) ** 2 + g ** 2 + (255 - b) ** 2) < 85 ** 2  # only true magenta, so pink/purple clothes survive
fg = ~bg

# blobs, left to right (columns of foreground)
cols = fg.sum(axis=0) > 3
spans, inside = [], False
for x, c in enumerate(cols):
    if c and not inside: x0, inside = x, True
    if not c and inside:
        if x - x0 > 30: spans.append((x0, x))
        inside = False
if inside: spans.append((x0, W))
# merge spans separated by tiny gaps (e.g. a bell on a hat)
merged = []
for s in spans:
    if merged and s[0] - merged[-1][1] < 25: merged[-1] = (merged[-1][0], s[1])
    else: merged.append(s)
assert len(merged) >= 4, f'found {len(merged)} poses'
merged = sorted(merged, key=lambda s: s[1] - s[0], reverse=True)[:4]
merged.sort()


def pixel_size(crop):
    """Grid size = the spacing whose lines catch the most colour edges,
    beyond what random lines would catch (so half-sizes don't win)."""
    best, score = 16.0, -1
    edges = []
    for axis, arr in ((0, crop), (1, crop.transpose(1, 0, 2))):
        pos = []
        for line in arr[::3]:
            d = np.abs(np.diff(line, axis=0)).sum(axis=1) > 60
            pos.extend((np.flatnonzero(d) + 1).tolist())
        edges.append(np.array(pos, float))
    for s10 in range(160, 420, 2):
        s = s10 / 10; tot = 0
        for pos in edges:
            if not len(pos): continue
            bestf = 0
            for o in np.arange(0, s, .5):
                ph = np.mod(pos - o, s)
                near = np.minimum(ph, s - ph) <= 1.6
                bestf = max(bestf, near.mean())
            tot += bestf - 3.2 / s
        if tot > score: best, score = s, tot
    return best


def sample(x0, x1):
    rows = np.flatnonzero(fg[:, x0:x1].any(axis=1))
    y0, y1 = rows[0], rows[-1] + 1
    crop, m = im[y0:y1, x0:x1], fg[y0:y1, x0:x1]
    s = float(sys.argv[4]) if len(sys.argv) > 4 else pixel_size(crop)
    best, bsc = (0, 0), -1e18
    step = max(1, int(s // 6))
    for oy in np.arange(0, s, step):
        for ox in np.arange(0, s, step):
            sc = 0
            for yy in np.arange(oy + s / 2, crop.shape[0], s):
                for xx in np.arange(ox + s / 2, crop.shape[1], s):
                    c = crop[int(yy - s / 3):int(yy + s / 3) + 1, int(xx - s / 3):int(xx + s / 3) + 1]
                    if c.size: sc -= c.std(axis=(0, 1)).sum()
            if sc > bsc: best, bsc = (oy, ox), sc
    oy, ox = best
    gh, gw = int((crop.shape[0] - oy) // s) + 1, int((crop.shape[1] - ox) // s) + 1
    spr = np.zeros((gh, gw, 4), np.uint8)
    for gy in range(gh):
        for gx in range(gw):
            ya, xa = int(oy + gy * s + s * .25), int(ox + gx * s + s * .25)
            yb, xb = int(oy + gy * s + s * .75) + 1, int(ox + gx * s + s * .75) + 1
            cm = m[ya:yb, xa:xb]
            if cm.size == 0 or cm.mean() < .5: continue
            cell = crop[ya:yb, xa:xb][cm]
            spr[gy, gx, :3] = np.median(cell, axis=0); spr[gy, gx, 3] = 255
    return spr, s


def lum(c): return c[..., 0] * .3 + c[..., 1] * .59 + c[..., 2] * .11


def tidy(spr):
    a = spr[..., 3] > 0
    # palette: snap to at most 22 colours so near-identical shades merge
    if a.sum():
        pal_img = Image.fromarray(spr[..., :3][a].reshape(-1, 1, 3).astype(np.uint8), 'RGB')
        q = pal_img.quantize(22, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
        spr[..., :3][a] = np.asarray(q).reshape(-1, 3)
    pad = np.zeros((spr.shape[0] + 4, spr.shape[1] + 4, 4), np.uint8); pad[2:-2, 2:-2] = spr; spr = pad
    def nb(a):
        n = np.zeros(a.shape, int)
        n[1:] += a[:-1]; n[:-1] += a[1:]; n[:, 1:] += a[:, :-1]; n[:, :-1] += a[:, 1:]
        return n
    # strip the old outline (dark pixels on the silhouette edge), twice
    for _ in range(2):
        a = spr[..., 3] > 0
        edge = a & (nb(a) < 4)
        dark = lum(spr[..., :3].astype(int)) < 72
        spr[edge & dark, 3] = 0
    # drop lonely specks
    a = spr[..., 3] > 0
    spr[a & (nb(a) <= 1), 3] = 0
    # fresh outline: exactly one pixel, 4-connected, all the way round
    a = spr[..., 3] > 0
    ring = (~a) & (nb(a) > 0)
    spr[ring, :3] = OUT; spr[ring, 3] = 255
    a = spr[..., 3] > 0
    ys, xs = np.flatnonzero(a.any(1)), np.flatnonzero(a.any(0))
    return spr[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]


def facing(spr):
    """+1 if the face looks right, -1 if left: where the skin sits in the head."""
    a = spr[..., 3] > 0
    h = spr.shape[0]
    head = spr[int(h * .2):int(h * .6)]
    rgb = head[..., :3].astype(int)
    skin = (head[..., 3] > 0) & (rgb[..., 0] > 170) & (rgb[..., 1] > 110) & (rgb[..., 1] < 215) & (rgb[..., 2] < 190) & (rgb[..., 0] > rgb[..., 2] + 30)
    if skin.sum() < 3: return 0
    xs = np.nonzero(skin)[1]
    return 1 if xs.mean() > spr.shape[1] / 2 else -1


sprites = []
for x0, x1 in merged:
    spr, s = sample(x0, x1)
    sprites.append((tidy(spr), s))
front, back = sprites[0][0], sprites[3][0]
s1, s2 = sprites[1][0], sprites[2][0]
f1 = facing(s1)
right, left = (s1, s2) if f1 >= 0 else (s2, s1)
for d, spr in (('front', front), ('left', left), ('right', right), ('back', back)):
    Image.fromarray(spr, 'RGBA').save(os.path.join(out, f'{name}_{d}.png'))
print(name, 'px', [round(s, 1) for _, s in sprites], 'sizes', [f'{p.shape[1]}x{p.shape[0]}' for p, _ in sprites], 'side1 faces', 'right' if f1 >= 0 else 'left')
