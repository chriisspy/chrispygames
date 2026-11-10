# Sitting, dead, watering and picking-up-logs poses for every character, built from HIS finished
# sprites (assets/final/<name>/{front,back,left,right}.png), so they keep his exact pixels and style.
# A watering can and a log bundle are drawn once here (navy outline like the cast) and held by everyone.
#
# Output per character: assets/final/<name>/poses/<pose>.png + poses.json
#   sit_front, sit_back, sit_right, sit_left    seated (on a chair; the legs fold forward on the sides)
#   dead                                         lying on its back, eyes as X
#   water_right_0..3, water_left_0..3            holding a watering can out, drops falling (loop)
#   logs_right_0..3, logs_left_0..3              bend, pick up a bundle of logs, stand holding it
# poses.json: for each picture, ax = the x of the feet's middle (the bottom row is always the ground)
# usage (from mafia2-lab/): python -I tools/make_poses.py [name ...]
import json, os, sys
import numpy as np
from PIL import Image
from collections import Counter

ROOT = 'assets/final/'
NAMES = sys.argv[1:] or sorted(n for n in os.listdir(ROOT) if os.path.isfile(ROOT + n + '/front.png'))

def load(n, v):
    return np.asarray(Image.open(f'{ROOT}{n}/{v}.png').convert('RGBA')).copy()

def trim(a):
    ys, xs = np.nonzero(a[..., 3])
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def navy_of(a):
    dark = [tuple(int(v) for v in p[:3]) for p in a.reshape(-1, 4) if p[3] and int(p[0]) + int(p[1]) + int(p[2]) < 150]
    return np.array(Counter(dark).most_common(1)[0][0] if dark else (1, 3, 46), np.uint8)

def leg_rows(a):
    """bottom rows that are legs: the middle of the body has a gap there (two feet)"""
    al = a[..., 3] > 0; h, w = al.shape; cx = w // 2; half = max(3, w // 4); n = 0
    for y in range(h - 1, 0, -1):
        mid = ''.join('#' if al[y, x] else '.' for x in range(max(0, cx - half), min(w, cx + half + 1))).strip('.')
        if '.' in mid: n += 1
        elif n: break
        elif h - 1 - y >= 1: break
    return max(3, n)

def feet_mid(a):
    al = a[..., 3] > 0; xs = np.nonzero(al[-2:].any(0))[0]
    return (xs.min() + xs.max() + 1) / 2

# ---------- the two props, drawn in the cast's style (N = navy outline) ----------
CAN = ["...NNNN......",
       "..N....N.....",
       "NNNNNNNNN..NN",
       "NHHHHHHHN.NHN",
       "NHMMMMMMNNHN.",
       "NHMMMMMMHHN..",
       "NHMMMMMMNN...",
       "NSSSSSSSN....",
       ".NNNNNNN....."]
CAN_COL = {'H': (126, 182, 214), 'M': (79, 134, 184), 'S': (47, 90, 140)}
SPOUT = (12, 2)                     # where water leaves the can (x, y in CAN)
def log_rows(n):
    """one log n long: bark on top (b light, B dark), a round cut end on the right (T with a ring r)"""
    return ["." + "N" * (n - 2) + "NN.",
            "N" + "b" * (n - 4) + "NTTN",
            "N" + "B" * (n - 4) + "NTrT" + "N",
            "N" + "B" * (n - 4) + "NTTN",
            "." + "N" * (n - 2) + "NN."]
def stack(*rows_list):
    out = []
    for i, (rows, dx) in enumerate(rows_list):
        rows = [" " * dx + r for r in rows]
        if out:                                   # share the outline row with the log below / above
            last = out.pop()
            rows[0] = "".join(a if a not in ". " else b for a, b in zip(rows[0].ljust(len(last)), last.ljust(len(rows[0]))))
        out += rows
    w = max(len(r) for r in out)
    return [r.replace(" ", ".").ljust(w, ".") for r in out]
LOGS = stack((log_rows(9), 2), (log_rows(11), 0))
LOG_COL = {'b': (162, 102, 60), 'B': (118, 68, 42), 'r': (176, 120, 66), 'T': (236, 196, 134)}
DROP = (159, 216, 255)

def art(rows, cols, navy):
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == 'N': a[y, x] = (*navy, 255)
            elif ch in cols: a[y, x] = (*cols[ch], 255)
    return a

def paste(dst, src, x, y):
    """src over dst at (x, y); dst grows as needed. returns (new dst, how far dst's origin moved)"""
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    x0, y0 = min(0, x), min(0, y); x1, y1 = max(W, x + w), max(H, y + h)
    out = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    out[-y0:-y0 + H, -x0:-x0 + W] = dst
    m = src[..., 3] > 0
    out[y - y0:y - y0 + h, x - x0:x - x0 + w][m] = src[m]
    return out, (-x0, -y0)

# ---------- poses ----------
def sit_straight(a, n):
    """front/back: the legs fold away under the seat, only the shoes show below the body"""
    return np.concatenate([a[:-n], a[-2:]], 0)

def sit_side(a, n, navy):
    """facing right: the body drops onto the seat and the legs stick out forward"""
    body = a[:-n]
    legs = a[-n:]
    al = legs[..., 3] > 0
    cols = [tuple(int(v) for v in p[:3]) for p in legs[al] if int(p[0]) + int(p[1]) + int(p[2]) >= 150]
    pants = np.array(Counter(cols).most_common(1)[0][0] if cols else navy, np.uint8)
    h, w = body.shape[:2]
    bal = body[..., 3] > 0
    front = int(np.nonzero(bal[-3:].any(0))[0].max())      # front edge of the seat of the pants
    L = 4                                                   # how far the thighs reach forward
    out = np.zeros((h + 2, w + L + 2, 4), np.uint8)
    out[:h, :w] = body
    for x in range(front - 2, front + L + 1):               # thigh: navy top and bottom, pants inside
        out[h - 3, x] = (*navy, 255); out[h - 2, x] = (*pants, 255); out[h - 1, x] = (*navy, 255)
    fx = front + L                                          # shin + shoe hanging down at the knee
    for y in range(h - 3, h + 2):
        out[y, fx - 1] = (*navy, 255); out[y, fx] = (*navy, 255) if y >= h else (*pants, 255); out[y, fx + 1] = (*navy, 255)
    out[h + 1, fx - 1:fx + 2] = (*navy, 255)
    out[h - 3, fx + 1] = (*navy, 255)
    return trim(out)

def find_eyes(a):
    """the eyes: short navy runs with skin on both sides, in the middle band of the face (like the game's blink)"""
    h, w = a.shape[:2]; al = a[..., 3] > 0
    L = a[..., 0] * .3 + a[..., 1] * .59 + a[..., 2] * .11
    eyes, first = [], -1
    for y in range(int(h * .25), int(h * .75)):
        hits = []; x = 0
        while x < w:
            if al[y, x] and L[y, x] < 70:
                x2 = x
                while x2 < w and al[y, x2] and L[y, x2] < 70: x2 += 1
                if x2 - x <= 4 and x > 0 and x2 < w and al[y, x - 1] and L[y, x - 1] > 110 and al[y, x2] and L[y, x2] > 110:
                    hits.append((x, x2, y))
                x = x2
            else: x += 1
        if len(hits) >= 2 or (hits and first >= 0):
            if first < 0: first = y
            if y - first < 6: eyes += hits
        elif first >= 0: break
    return eyes

def dead(a, navy):
    """lying on its back: the front view laid down (head to the left), eyes turned into little X's"""
    a = a.copy()
    eyes = find_eyes(a)
    if eyes:
        # group runs into the two eyes by x
        xs = sorted(set((x0 + x1) // 2 for x0, x1, y in eyes))
        groups = []
        for x0, x1, y in eyes:
            c = (x0 + x1 - 1) / 2
            for g in groups:
                if abs(g['c'] - c) < 3: g['px'] += [(x, y) for x in range(x0, x1)]; break
            else: groups.append({'c': c, 'px': [(x, y) for x in range(x0, x1)]})
        for g in groups:
            px = g['px']; skin = None
            x0 = min(p[0] for p in px); y0 = min(p[1] for p in px)
            skin = a[y0, x0 - 1].copy()
            for x, y in px: a[y, x] = skin
            cx = round(sum(p[0] for p in px) / len(px) - .01); cy = round(sum(p[1] for p in px) / len(px) - .01)
            for dx, dy in ((-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)):
                if a[cy + dy, cx + dx, 3]: a[cy + dy, cx + dx] = (*navy, 255)
    return trim(np.rot90(a, 1).copy())

def water(side, navy, k):
    """facing right, holding the can out at the waist; k = frame 0..3: the can dips and drops fall"""
    n = leg_rows(side)
    h, w = side.shape[:2]
    can = art(CAN, CAN_COL, navy)
    al = side[..., 3] > 0
    waist = h - n - 3
    front = int(np.nonzero(al[waist - 2:waist + 1].any(0))[0].max())
    cx, cy = front - 3, waist - 7 + (1 if k in (1, 2) else 0)
    out, (ox, oy) = paste(side, can, cx, cy)
    sx, sy = cx + ox + SPOUT[0], cy + oy + SPOUT[1]
    if k > 0:                                       # water: a dotted stream from the spout tip to the ground
        pad = np.zeros((out.shape[0], 2, 4), np.uint8); out = np.concatenate([out, pad], 1)
        H2 = out.shape[0]
        for d in range(1 + (k - 1) % 3, H2 - sy, 3):
            yy = sy + d; xx = sx + (1 if d > 2 else 0)
            if yy < H2 and not out[yy, xx, 3]: out[yy, xx] = (*DROP, 255)
    return out, ox

def logs(side, navy, k):
    """facing right: 0 = logs on the ground in front, 1 = bent down reaching, 2 = bent holding them, 3 = standing holding them"""
    n = leg_rows(side)
    h, w = side.shape[:2]
    bundle = art(LOGS, LOG_COL, navy)
    lh, lw = bundle.shape[:2]
    al = side[..., 3] > 0
    if k in (1, 2):                                 # bend: the body drops 2 rows (legs squash) and leans 1 forward
        top = side[:-n]; legs = np.concatenate([side[-n:-n + 1], side[-2:]], 0) if n >= 3 else side[-n:]
        bent = np.zeros((top.shape[0] + legs.shape[0], w + 1, 4), np.uint8)
        bent[:top.shape[0] - 6, 1:] = top[:-6]                 # head and shoulders lean forward 1 px
        bent[top.shape[0] - 6:top.shape[0], :w] = top[-6:]
        bent[top.shape[0]:, :w] = legs
        body = bent
    else:
        body = side
    bh = body.shape[0]
    bal = body[..., 3] > 0
    front = int(np.nonzero(bal.any(0))[0].max())
    if k == 0:   lx, ly = front - 2, bh - lh             # on the ground, just in front of the feet
    elif k == 1: lx, ly = front - 3, bh - lh             # hands on them
    elif k == 2: lx, ly = front - 6, bh - lh - 4         # lifted to the knees
    else:        lx, ly = w - lw // 2 - 2, h - n - lh - 1   # held against the chest
    out, (ox, oy) = paste(body, bundle, lx, ly)
    return out, ox

def mirror(a):
    return a[:, ::-1].copy()

def main():
    for name in NAMES:
        F, B, R, L = (load(name, v) for v in ('front', 'back', 'right', 'left'))
        navy = navy_of(F)
        out = {}
        nF, nB, nR = leg_rows(F), leg_rows(B), leg_rows(R)
        out['sit_front'] = (sit_straight(F, nF), None)
        out['sit_back'] = (sit_straight(B, nB), None)
        sr = sit_side(R, nR, navy)
        out['sit_right'] = (sr, feet_mid(R[:-nR]) if False else None)
        out['sit_left'] = (mirror(sr), None)
        out['dead'] = (dead(F, navy), None)
        for k in range(4):
            a, ox = water(R, navy, k); out[f'water_right_{k}'] = (a, ox + feet_mid(R))
            out[f'water_left_{k}'] = (mirror(a), a.shape[1] - (ox + feet_mid(R)))
            a, ox = logs(R, navy, k); out[f'logs_right_{k}'] = (a, ox + feet_mid(R))
            out[f'logs_left_{k}'] = (mirror(a), a.shape[1] - (ox + feet_mid(R)))
        d = f'{ROOT}{name}/poses/'
        os.makedirs(d, exist_ok=True)
        meta = {}
        for k, (a, ax) in out.items():
            Image.fromarray(a).save(d + k + '.png')
            meta[k] = {'w': int(a.shape[1]), 'h': int(a.shape[0]), 'ax': round(float(ax if ax is not None else a.shape[1] / 2), 1)}
        # sitting on the side: the hips sit over where the feet were
        meta['sit_right']['ax'] = round(float(feet_mid(R)), 1)
        meta['sit_left']['ax'] = round(float(out['sit_left'][0].shape[1] - feet_mid(R)), 1)
        json.dump(meta, open(d + 'poses.json', 'w'), indent=1)
        print(name, 'legs', nF, nR, 'poses', len(meta))

if __name__ == '__main__':
    main()
