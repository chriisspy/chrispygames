"""Split the furnished room into an empty room + one object per piece of furniture.

Usage: python -I split_room.py full-1x.png empty-1x.png out_dir
Each object is cut from the FULL room (so it looks exactly as approved) using
the difference between the full and empty rooms as its mask. Writes
out_dir/<name>.png with alpha, plus objects.json with positions and sort bases.
"""
import sys, os, json
import numpy as np
from PIL import Image

full_p, empty_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
full = np.asarray(Image.open(full_p).convert('RGB')).astype(int)
empty = np.asarray(Image.open(empty_p).convert('RGB')).astype(int)
assert full.shape == empty.shape, (full.shape, empty.shape)
H, W, _ = full.shape

# best small shift of the empty room against the full one, judged on the walls (no furniture up there)
best, bsc = (0, 0), 1e18
for dy in range(-3, 4):
    for dx in range(-3, 4):
        a = full[10:50, 20:170]
        b = empty[10 + dy:50 + dy, 20 + dx:170 + dx]
        sc = np.abs(a - b).sum()
        if sc < bsc: best, bsc = (dx, dy), sc
dx, dy = best
emp = np.roll(np.roll(empty, -dy, axis=0), -dx, axis=1)
print('empty shift', best, 'wall diff/px', round(bsc / (40 * 150 * 3), 1))

diff = np.abs(full - emp).sum(axis=2) > 48

# name: [x0, y0, x1, y1, base_y]   (order matters: each pixel goes to the first rect that claims it)
OBJECTS = {
    'rug':        [68, 129, 128, 186, 0],
    'armchair':   [14, 156, 54, 195, 193],
    'fireplace':  [13, 56, 54, 158, 157],
    'nightL':     [51, 56, 71, 98, 96],
    'nightR':     [126, 56, 146, 98, 96],
    'bed':        [70, 56, 127, 130, 128],
    'floorlamp':  [144, 44, 164, 98, 96],
    'plantR':     [160, 56, 182, 98, 96],
    'desk':       [125, 116, 182, 168, 166],
    'chair':      [145, 162, 171, 197, 195],
}


def neighbours4(m):
    n = np.zeros(m.shape, int)
    n[1:] += m[:-1]; n[:-1] += m[1:]; n[:, 1:] += m[:, :-1]; n[:, :-1] += m[:, 1:]
    return n


def fill_holes(m):
    """Anything not reachable from the rect's border through 'off' pixels is a hole: fill it."""
    h, w = m.shape
    reach = np.zeros_like(m)
    stack = [(y, x) for y in range(h) for x in (0, w - 1) if not m[y, x]] + [(y, x) for x in range(w) for y in (0, h - 1) if not m[y, x]]
    for y, x in stack: reach[y, x] = True
    while stack:
        y, x = stack.pop()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and not m[ny, nx] and not reach[ny, nx]:
                reach[ny, nx] = True; stack.append((ny, nx))
    return m | ~reach


claimed = np.zeros((H, W), bool)
meta = {}
for name, (x0, y0, x1, y1, base) in OBJECTS.items():
    m = diff[y0:y1, x0:x1] & ~claimed[y0:y1, x0:x1]
    # close small gaps, drop specks, fill holes
    for _ in range(2): m = m | (neighbours4(m) >= 3)
    m = m & (neighbours4(m) >= 1)
    m = fill_holes(m)
    m = m & (neighbours4(m) >= 2)
    # keep only blobs of a real size (drops thin slivers left by the diff)
    seen = np.zeros_like(m); keep = np.zeros_like(m)
    for sy, sx in zip(*np.nonzero(m)):
        if seen[sy, sx]: continue
        comp = [(sy, sx)]; seen[sy, sx] = True; k = 0
        while k < len(comp):
            y, x = comp[k]; k += 1
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; comp.append((ny, nx))
        if len(comp) >= 12:
            for y, x in comp: keep[y, x] = True
    m = keep
    if not m.any(): print('EMPTY', name); continue
    claimed[y0:y1, x0:x1] |= m
    ys, xs = np.nonzero(m)
    ya, yb, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    spr = np.zeros((yb - ya, xb - xa, 4), np.uint8)
    spr[..., :3] = full[y0 + ya:y0 + yb, x0 + xa:x0 + xb]
    spr[..., 3] = m[ya:yb, xa:xb] * 255
    Image.fromarray(spr, 'RGBA').save(os.path.join(out, name + '.png'))
    meta[name] = {'x': int(x0 + xa), 'y': int(y0 + ya), 'w': int(xb - xa), 'h': int(yb - ya), 'base': int(base)}
    print(name, meta[name])
json.dump(meta, open(os.path.join(out, 'objects.json'), 'w'), indent=1)

# the empty room, with our shift applied, and anything the furniture claimed patched from the empty art
Image.fromarray(emp.astype(np.uint8), 'RGB').save(os.path.join(out, 'room-empty.png'))
