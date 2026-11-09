"""Snap an AI pixel-art background onto one even pixel grid.

Usage: python -I clean_bg.py src.png out.webp [pixel_size] [colours]
AI images fake pixel art: pixel sizes drift and edges are blurry. This finds
the art-pixel size, takes one colour per cell, trims the palette, then scales
back up with hard edges, so every pixel in the scene is the same size.
"""
import sys
from collections import Counter
import numpy as np
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
forced = float(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != 'auto' else None
colours = int(sys.argv[4]) if len(sys.argv) > 4 else 0

img = Image.open(src).convert('RGB')
a = np.asarray(img).astype(np.int32)
H, W, _ = a.shape


def estimate(a):
    # distance between colour edges, along many rows and columns
    runs = Counter()
    for arr in (a, a.transpose(1, 0, 2)):
        for line in arr[:: max(1, arr.shape[0] // 300)]:
            d = np.abs(np.diff(line, axis=0)).sum(axis=1) > 60
            idx = np.flatnonzero(d)
            for L in np.diff(idx):
                if 3 <= L <= 200:
                    runs[int(L)] += 1
    best, score = 8.0, -1
    for s10 in range(30, 400):  # 3.0 .. 40.0 in 0.1 steps
        s = s10 / 10
        sc = 0
        for L, c in runs.items():
            k = L / s
            if k >= 0.8 and abs(k - round(k)) < 0.15:
                sc += c * min(round(k), 4)
        if sc > score:
            best, score = s, sc
    return best


s = forced or estimate(a)
gw, gh = int(W / s), int(H / s)
small = np.zeros((gh, gw, 3), np.uint8)
for gy in range(gh):
    y0, y1 = int(gy * s), int((gy + 1) * s)
    m0, m1 = y0 + (y1 - y0) // 4, y1 - (y1 - y0) // 4
    for gx in range(gw):
        x0, x1 = int(gx * s), int((gx + 1) * s)
        n0, n1 = x0 + (x1 - x0) // 4, x1 - (x1 - x0) // 4
        cell = a[m0:max(m1, m0 + 1), n0:max(n1, n0 + 1)].reshape(-1, 3)
        small[gy, gx] = np.median(cell, axis=0)
sm = Image.fromarray(small, 'RGB')
if colours:
    sm = sm.quantize(colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
k = max(1, round(2000 / gw))
big = sm.resize((gw * k, gh * k), Image.NEAREST)
big.save(out, 'WEBP', lossless=True, method=6)
sm.save(out.rsplit('.', 1)[0] + '-1x.png')
print(f'pixel size {s:.1f} -> grid {gw}x{gh}, saved {big.size[0]}x{big.size[1]} (x{k})')
