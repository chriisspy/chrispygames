# Poses from PixelLab SKELETON animations (his pick "B", 10 Nov 2026): PixelLab moves the real character
# (stays on-model), then TINY props go in the hands (his rule: props must fit the hands, never big).
# Input : assets/poses-src/<name>/{sit_south,sit_east,sit_north,water_east,pickup_east}_<i>.png  (48x48 frames)
# Output: assets/final/<name>/poses/*.png + poses.json  (ax = x of the feet's middle; gy = rows below the ground line)
# Colours are snapped to the character's finished palette (assets/final/<name>), dark edge fuzz -> navy.
# usage (from mafia2-lab/): python -I tools/pl_poses.py <name> [name ...]
import json, os, sys
import numpy as np
from PIL import Image

NAVY = (1, 3, 46)
def rows(*r): return r
CAN = rows(".NNN...",          # tiny watering can, spout to the right (7 x 5)
           "NhhhN.N",
           "NmmmNN.",
           "NsssN..",
           ".NNN...")
CANC = {'h': (140, 190, 220), 'm': (86, 140, 190), 's': (52, 96, 146)}
LOG = rows(".NNNNNN.",         # one small log (8 x 4), cut end on the right
           "NbbbbbTN",
           "NBBBBBrN",
           ".NNNNNN.")
LOGC = {'b': (166, 106, 62), 'B': (120, 70, 44), 'T': (236, 196, 134), 'r': (190, 140, 84)}
DROP = (159, 216, 255)

def art(rws, cols):
    a = np.zeros((len(rws), len(rws[0]), 4), np.uint8)
    for y, r in enumerate(rws):
        for x, ch in enumerate(r):
            if ch == 'N': a[y, x] = (*NAVY, 255)
            elif ch in cols: a[y, x] = (*cols[ch], 255)
    return a

def palette(name):
    cols = set()
    for v in ('front', 'back', 'right'):
        a = np.asarray(Image.open(f'assets/final/{name}/{v}.png').convert('RGBA'))
        cols |= {tuple(int(c) for c in p[:3]) for p in a.reshape(-1, 4) if p[3]}
    return np.array(sorted(cols), np.float32)

def clean(a, pal):
    """solid pixels only, every colour snapped to the finished palette"""
    a = a.copy(); op = a[..., 3] >= 128
    px = a[op][:, :3].astype(np.float32)
    idx = ((px[:, None] - pal[None]) ** 2).sum(-1).argmin(1)
    a[op] = np.concatenate([pal[idx].astype(np.uint8), np.full((len(idx), 1), 255, np.uint8)], 1)
    a[~op] = 0
    return a

def put(dst, src, x, y):
    h, w = src.shape[:2]; m = src[..., 3] > 0
    dst[y:y + h, x:x + w][m] = src[m]

def front_at(a, y):
    xs = np.nonzero(a[y, :, 3])[0]
    return int(xs.max()) if len(xs) else None

HEAD_LOCK = {'bape': 21, 'fisher': 19}   # characters whose front head gets pinned: how many rows of front.png are head
SIDE_LOCK = {'fisher': 19}               # same for the leaning side poses (watering, picking up): PixelLab smears a cap + glasses when the head tilts

def blob(a):
    """drop crumbs PixelLab leaves floating off the sprite: keep the biggest 4-connected blob"""
    al = a[..., 3] > 0; h, w = al.shape; lab = np.zeros((h, w), int); n = 0; sz = {}
    for y in range(h):
        for x in range(w):
            if al[y, x] and not lab[y, x]:
                n += 1; st = [(x, y)]; lab[y, x] = n; c = 0
                while st:
                    cx, cy = st.pop(); c += 1
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and al[ny, nx] and not lab[ny, nx]: lab[ny, nx] = n; st.append((nx, ny))
                sz[n] = c
    if n > 1: a = a.copy(); a[lab != max(sz, key=sz.get)] = 0
    return a

def main():
    for name in sys.argv[1:]:
        src = f'assets/poses-src/{name}/'; pal = palette(name)
        F0 = lambda k, i: clean(np.asarray(Image.open(f'{src}{k}_{i}.png').convert('RGBA')), pal)
        def F(k, i):
            a = F0(k, i)
            # PixelLab turned this character's head sideways on some front-walk frames (it flickered left and right):
            # keep the standing frame's whole upper body on every frame and let only the legs move
            if name in HEAD_LOCK and k in ('walk_south', 'sit_south'):
                # PixelLab redraws this character's head on some front frames (the cap brim comes and goes): put HIS drawn
                # head back on every frame, wherever the head is, and keep PixelLab's body, arms and legs under it
                fr = np.asarray(Image.open(f'assets/final/{name}/front.png').convert('RGBA'))[:HEAD_LOCK[name]]; fh, fw = fr.shape[:2]; best = None
                for y in range(0, a.shape[0] - fh + 1):
                    for x in range(0, a.shape[1] - fw + 1):
                        w = a[y:y + fh, x:x + fw]; sc = int(((w[..., :3] == fr[..., :3]).all(-1) & (fr[..., 3] > 0) & (w[..., 3] > 0)).sum())
                        if best is None or sc > best[0]: best = (sc, x, y)
                _, x, y = best; a = a.copy(); a[:y + fh] = 0; m = fr[..., 3] > 0; a[y:y + fh, x:x + fw][m] = fr[m]
            if name in SIDE_LOCK and k in ('water_east', 'pickup_east') and a[..., 3].any():
                # his own side head, upright, set where PixelLab's tilted head is (cap brim tip to brim tip); the body under it is kept
                hr = np.asarray(Image.open(f'assets/final/{name}/right.png').convert('RGBA'))[:SIDE_LOCK[name]]; fh, fw = hr.shape[:2]
                # line it up on the most face-like spot: where the frame has the most of his head's own bright colours
                # (glasses, skin) under the same pixels; then wipe PixelLab's head (everything above, and under his outline)
                m = hr[..., 3] > 0; lum = hr[..., 0] * .3 + hr[..., 1] * .59 + hr[..., 2] * .11
                face = m & (hr[..., 0].astype(int) - hr[..., 2] > 60)                       # warm pixels: red glasses + skin
                cols = {tuple(c) for c in hr[face][:, :3]}
                warm = np.zeros(a.shape[:2], bool)
                for c in cols: warm |= (a[..., :3] == c).all(-1) & (a[..., 3] > 0)
                ys, xs = np.nonzero(warm); fy, fx = np.nonzero(face)
                if len(ys):
                    top = int(round(np.median(ys[ys <= ys.min() + 9]) - np.median(fy))); x0 = int(round(np.median(xs[ys <= ys.min() + 9]) - np.median(fx)))
                    top = max(0, min(top, a.shape[0] - fh)); x0 = max(0, min(x0, a.shape[1] - fw)); a = a.copy()
                    a[:top] = 0
                    for r in range(fh):
                        q = np.nonzero(m[r])[0]
                        if len(q): a[top + r, x0 + q.min():] = 0
                    a[top:top + fh, x0:x0 + fw][m] = hr[m]
            return a
        out = {}
        def base(a):                       # ground line + feet middle from a standing frame
            ys, xs = np.nonzero(a[..., 3]); g = ys.max()
            fx = np.nonzero(a[g - 1:g + 1, :, 3].any(0))[0]
            return g, (fx.min() + fx.max() + 1) / 2
        def save(key, a, g, ax):
            ys, xs = np.nonzero(a[..., 3]); x0, x1, y0 = xs.min(), xs.max() + 1, ys.min()
            y1 = max(ys.max(), g) + 1
            out[key] = (a[y0:y1, x0:x1], ax - x0, 0)
            m = a[:, ::-1]; out[key.replace('right', 'left')] = (m[y0:y1, a.shape[1] - x1:a.shape[1] - x0], (x1 - x0) - (ax - x0), 0) if 'right' in key else out[key]
        # --- sitting: the last frame of PixelLab's sit ---
        # (PixelLab sometimes draws a chair under them near the end: take the latest frame that is still just the character)
        for d, k in (('front', 'sit_south'), ('right', 'sit_east'), ('back', 'sit_north')):
            f0 = F(k, 0); g, ax = base(f0); n0 = (f0[..., 3] > 0).sum(); w0 = np.nonzero(f0[..., 3].any(0))[0]
            ok = [i for i in range(2, 8) if (F(k, i)[..., 3] > 0).sum() <= n0 * 1.06 and np.ptp(np.nonzero(F(k, i)[..., 3].any(0))[0]) <= np.ptp(w0) + 4]
            save(f'sit_{d}', F(k, max(ok) if ok else 3), g, ax)
        # --- watering: leaning frames + a tiny can in the hands + drops ---
        g, ax = base(F('water_east', 0))
        sleeve = None
        can = art(CAN, CANC)
        nw = len([f for f in os.listdir(src) if f.startswith('water_east_')])
        for n, i in enumerate((2, 3, 4, 5) if nw >= 8 else (0, 1, 2, 3)):
            a = F('water_east', i).copy()
            hy = g - 7                                            # hand height: just above the legs, below the chin
            fx = max(front_at(a, y) for y in range(hy - 1, hy + 2))
            body = a[hy, fx - 2, :3].copy()                       # sleeve colour just inside the outline
            cx, cy = fx + 1, hy - 2 + (n % 2)                     # the can sits right at the hands, dipping as it pours
            put(a, can, cx, cy)
            a[cy + 1, cx - 1] = (*NAVY, 255); a[cy + 2, cx - 1] = (*body, 255); a[cy + 3, cx - 1] = (*NAVY, 255)   # a little arm to the handle
            sx, sy = cx + 6, cy + 1                               # spout tip
            for d in range(2 + n % 3, g - sy + 1, 3):
                if not a[sy + d, sx + 1, 3]: a[sy + d, sx + 1] = (*DROP, 255)
            save(f'water_right_{n}', a, g, ax)
        # --- log: 0 stand by it, 1 bend to it, 2 lift, 3 stand holding it (hugged at the chest) ---
        g, ax = base(F('pickup_east', 0))
        log = art(LOG, LOGC)
        for n, (i, where) in enumerate(((0, 'ground'), (3, 'ground'), (4, 'hands'), (7, 'chest'))):
            a = F('pickup_east', i).copy()
            ys = np.nonzero(a[..., 3].any(1))[0]; top = ys.min()
            if where == 'ground':
                fx = front_at(a, g - 1); put(a, log, min(fx + 2, a.shape[1] - 9), g - 3)
            else:
                hy = g - (5 if where == 'hands' else 8); fx = max(front_at(a, y) for y in range(hy - 1, hy + 2))
                body = a[hy, fx - 2, :3].copy()
                lx, ly = fx - 4, hy - 1
                put(a, log, lx, ly)
                a[ly + 1:ly + 3, lx + 2:lx + 4] = (*body, 255)    # the arm wrapped over the log
                a[ly, lx + 2:lx + 4] = (*NAVY, 255); a[ly + 3, lx + 2:lx + 4] = (*NAVY, 255)
            save(f'logs_right_{n}', a, g, ax)
        save('bend_right', F('pickup_east', 3).copy(), g, ax)   # bending down with empty hands (feeding the cat)
        # --- walking: 8 frames each way, all cut with one shared box so the body never jitters ---
        walk = {}
        for v, k in (('front', 'walk_south'), ('right', 'walk_east'), ('back', 'walk_north')):
            fr = [F(k, i) for i in range(8)]
            al = np.any([a[..., 3] > 0 for a in fr], 0); ys, xs = np.nonzero(al)
            x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            b0 = np.nonzero(fr[0][..., 3].any(0))[0]                 # frame 0 = standing: its middle is the anchor,
            ax = (b0.min() + b0.max() + 1) / 2 - x0                    # the same middle the idle sprite is drawn from
            for i, a in enumerate(fr):
                c = a[y0:y1, x0:x1]; walk[f'walk_{v}_{i}'] = (c, ax, 0)
                if v == 'right': walk[f'walk_left_{i}'] = (c[:, ::-1], (x1 - x0) - ax, 0)
        out.update(walk)
        d = f'assets/final/{name}/poses/'; os.makedirs(d, exist_ok=True)
        meta = json.load(open(d + 'poses.json')) if os.path.exists(d + 'poses.json') else {}
        for k, (a, ax, _) in out.items():
            if not k.startswith(('water', 'logs')): a = blob(np.ascontiguousarray(a))
            Image.fromarray(np.ascontiguousarray(a)).save(d + k + '.png')
            meta[k] = {'w': int(a.shape[1]), 'h': int(a.shape[0]), 'ax': round(float(ax), 1)}
        json.dump(meta, open(d + 'poses.json', 'w'), indent=1)
        Image.fromarray(art(LOG, LOGC)).save('assets/final/log.png')
        print(name, sorted(out))

if __name__ == '__main__':
    main()
