"""Turn an AI pixel-art sheet (characters on flat magenta) into true small sprites.

Usage: python -I extract_sprites.py sheet.png out_dir [names,comma,separated]
Finds each character, works out how big one "art pixel" is, and samples one
colour per art pixel, so the result is a crisp 1:1 sprite the game can scale.
"""
import sys, os, json
from collections import Counter
from PIL import Image
import numpy as np

src, out = sys.argv[1], sys.argv[2]
names = sys.argv[3].split(',') if len(sys.argv) > 3 else []
os.makedirs(out, exist_ok=True)

im = np.asarray(Image.open(src).convert('RGB')).astype(int)
H, W, _ = im.shape
r, g, b = im[..., 0], im[..., 1], im[..., 2]
# magenta-ish background: strong red + blue, weak green
bg = (r > 150) & (b > 150) & (g < 110) & (np.abs(r - b) < 90)
fg = ~bg

# --- find blobs on a coarse grid (fast connected components) ---
cs = 8
gh, gw = H // cs, W // cs
coarse = fg[:gh * cs, :gw * cs].reshape(gh, cs, gw, cs).mean(axis=(1, 3)) > 0.15
seen = np.zeros_like(coarse)
boxes = []
for y in range(gh):
    for x in range(gw):
        if coarse[y, x] and not seen[y, x]:
            stack = [(y, x)]; seen[y, x] = True
            y0 = y1 = y; x0 = x1 = x; n = 0
            while stack:
                cy, cx = stack.pop(); n += 1
                y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
                for dy in (-2, -1, 0, 1, 2):
                    for dx in (-2, -1, 0, 1, 2):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < gh and 0 <= nx < gw and coarse[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; stack.append((ny, nx))
            if n > 20:
                boxes.append([x0 * cs, y0 * cs, (x1 + 1) * cs, (y1 + 1) * cs])

# sort into rows, then left to right
boxes.sort(key=lambda b: (b[1] + b[3]) / 2)
rows, cur = [], []
for bx in boxes:
    cy = (bx[1] + bx[3]) / 2
    if cur and abs(cy - np.mean([(c[1] + c[3]) / 2 for c in cur])) > (bx[3] - bx[1]) * 0.5:
        rows.append(cur); cur = []
    cur.append(bx)
if cur: rows.append(cur)
ordered = [bx for row in rows for bx in sorted(row, key=lambda b: b[0])]


def pixel_size(crop):
    """Estimate art-pixel size from the lengths of same-colour runs."""
    runs = Counter()
    for arr in (crop, crop.transpose(1, 0, 2)):
        for line in arr[::3]:
            d = np.abs(np.diff(line, axis=0)).sum(axis=1) > 40
            idx = np.flatnonzero(d)
            for a, bb in zip(idx[:-1], idx[1:]):
                L = bb - a
                if L >= 4: runs[L] += 1
    best, score = 16, -1
    for s in range(6, 90):
        sc = sum(c for L, c in runs.items() if abs(L / s - round(L / s)) < 0.12 and round(L / s) >= 1) * (1 + s / 200)
        if sc > score: best, score = s, sc
    return best


meta = []
for i, (x0, y0, x1, y1) in enumerate(ordered):
    pad = 6
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(W, x1 + pad), min(H, y1 + pad)
    crop = im[y0:y1, x0:x1]
    s = pixel_size(crop)
    # find the grid offset that best lines up with colour edges
    best_off, best_sc = (0, 0), -1
    m = fg[y0:y1, x0:x1]
    for oy in range(0, s, max(1, s // 8)):
        for ox in range(0, s, max(1, s // 8)):
            sc = 0
            for yy in range(oy + s // 2, crop.shape[0], s):
                for xx in range(ox + s // 2, crop.shape[1], s):
                    cell = crop[max(0, yy - s // 3):yy + s // 3, max(0, xx - s // 3):xx + s // 3]
                    sc -= cell.std(axis=(0, 1)).sum()
            if sc > best_sc: best_off, best_sc = (oy, ox), sc
    oy, ox = best_off
    gw_, gh_ = (crop.shape[1] - ox) // s, (crop.shape[0] - oy) // s
    spr = np.zeros((gh_, gw_, 4), dtype=np.uint8)
    for gy in range(gh_):
        for gx in range(gw_):
            yy, xx = oy + gy * s, ox + gx * s
            cell = crop[yy + s // 4: yy + s - s // 4, xx + s // 4: xx + s - s // 4].reshape(-1, 3)
            mm = m[yy + s // 4: yy + s - s // 4, xx + s // 4: xx + s - s // 4].reshape(-1)
            if mm.mean() < 0.5: continue
            col = np.median(cell[mm], axis=0)
            spr[gy, gx, :3] = col; spr[gy, gx, 3] = 255
    # trim empty edges
    a = spr[..., 3] > 0
    ys, xs = np.flatnonzero(a.any(1)), np.flatnonzero(a.any(0))
    spr = spr[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    name = names[i] if i < len(names) else f'sprite{i:02d}'
    Image.fromarray(spr, 'RGBA').save(os.path.join(out, name + '.png'))
    meta.append({'name': name, 'w': int(spr.shape[1]), 'h': int(spr.shape[0]), 'px': int(s)})
    print(name, spr.shape[1], 'x', spr.shape[0], 'art px', s)

json.dump(meta, open(os.path.join(out, 'sprites.json'), 'w'), indent=1)
