# Sheik Osama rides a flying carpet, so he gets his own poses: in every one he sits on the carpet exactly as drawn.
# His body never moves. Only the carpet ripples, and the whole thing floats HOVER px above the ground.
#   walk_<dir>_0..7      the carpet rippling (the game uses these for walking AND standing still AND sitting)
#   walkb_<dir>_0..7     the same with his eyes shut (blink, asleep); front, left, right
#   sit_<dir>            one still frame
#   water_*, logs_*      on the carpet, holding the can / the logs (the props come from make_poses.py)
#   bend_*               the carpet lowered to the ground (feeding the cat)
#   dead                 lying on the carpet, on the ground, X eyes
# usage (from mafia2-lab/): python -I tools/make_carpet.py [check-sheet.png]
import json, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_argv = sys.argv; sys.argv = sys.argv[:1]
import make_poses as MP
sys.argv = _argv

NAME = 'sheik'; ROOT = 'assets/final/'; HOVER = 4
CARPET = {(0x34, 0x7f, 0x61), (0x01, 0x59, 0x57), (0xe1, 0xc3, 0x99), (0xbc, 0x9a, 0x7c), (0x75, 0x80, 0x8d), (0x18, 0x2d, 0x34), (0x32, 0x46, 0x33), (0x8c, 0x56, 0x51)}
GREEN = (0x01, 0x59, 0x57, 255); TAN = (0xbc, 0x9a, 0x7c, 255)
# per view: ct = first carpet row, (b0, b1) = the columns his body covers on the carpet, edge = first row of the carpet's front edge
VIEW = {'front': dict(ct=18, b0=7, b1=19, edge=29), 'back': dict(ct=18, b0=7, b1=19, edge=30),
        'right': dict(ct=19, b0=8, b1=18, edge=29), 'left': dict(ct=19, b0=8, b1=18, edge=29)}

# His drawing as cut from the sheet lives in raw/. He asked for 1 px more navy all round (he looked thinner than the cast),
# so everything saved (the four views and every pose) gets stroke() on top. Coordinates in this file are raw/ pixels.
EYES = {'front': [[10, 9, 2, 3], [15, 9, 2, 3]], 'right': [[16, 9, 2, 3]], 'left': [[9, 9, 2, 3]]}
def load(v): return np.asarray(Image.open(f'{ROOT}{NAME}/raw/{v}.png').convert('RGBA')).copy()

def stroke(a, navy):
    """1 px of navy round the whole shape (up, down, left, right of every pixel); the picture grows 1 px each side"""
    h, w = a.shape[:2]; p = np.zeros((h + 2, w + 2, 4), np.uint8); p[1:-1, 1:-1] = a
    al = p[..., 3] > 0; d = al.copy(); d[1:] |= al[:-1]; d[:-1] |= al[1:]; d[:, 1:] |= al[:, :-1]; d[:, :-1] |= al[:, 1:]
    p[d & ~al] = (*navy, 255); return p

def ripple(a, v, f):
    """frame f of 8: the carpet's two free ends flap (whole columns slide up and down), and its front edge ripples under him"""
    V = VIEW[v]; h, w = a.shape[:2]; out = a.copy(); cx = (V['b0'] + V['b1']) / 2
    sgn = -1 if v == 'left' else 1
    for x in range(w):
        ph = 2 * math.pi * (f / 8 + sgn * x / 17)
        if x < V['b0'] or x > V['b1']:                       # a free end: the further out, the more it moves
            far = (V['b0'] - x) if x < V['b0'] else (x - V['b1'])
            d = round(min(2, .45 + far * .32) * math.sin(ph))
            col = a[V['ct']:, x].copy(); out[V['ct']:, x] = 0
            for y in range(len(col)):
                yy = V['ct'] + y + d
                if col[y, 3] and 0 <= yy < h + 9: out_put(out, yy, x, col[y])
        else:                                                # under him: only the front edge moves, 1 px
            d = round(.8 * math.sin(ph)); e = V['edge']
            if d > 0:   out[e + 1:, x] = a[e:-1, x]; out[e, x] = a[e - 1, x]
            elif d < 0: out[e - 1:-1, x] = a[e:, x]; out[-1, x] = 0
    return out

def out_put(out, y, x, px):
    if y < out.shape[0]: out[y, x] = px

def shut_eyes(a, eyes):
    a = a.copy()
    for x, y, w, h in eyes: a[y:y + h - 1, x:x + w] = a[y, x - 1]
    return a

def hover(a, n=HOVER):
    """n clear rows under the carpet: the picture's bottom row is the ground"""
    return np.concatenate([a, np.zeros((n, a.shape[1], 4), np.uint8)], 0) if n else a

def grow(a, pad=2):
    """room below for the carpet to dip into"""
    return np.concatenate([a, np.zeros((pad, a.shape[1], 4), np.uint8)], 0)

def tidy(a, n):
    """cut the spare rows back off, then float it n px up"""
    ys = np.nonzero(a[..., 3].any(1))[0]
    return hover(a[:ys.max() + 1], n)

def full_carpet(F):
    """the front carpet with the part hidden under him painted in (plain green, tan back border)"""
    V = VIEW['front']; c = F[V['ct']:].copy(); h, w = c.shape[:2]
    for y in range(h):
        xs = np.nonzero(c[y, :, 3])[0]
        if not len(xs): continue
        for x in range(max(V['b0'], xs.min()), min(V['b1'], xs.max()) + 1):
            if tuple(int(q) for q in c[y, x, :3]) in CARPET and y > 8: continue
            if V['ct'] + y >= V['edge'] + 1: continue
            c[y, x] = (1, 3, 46, 255) if y == 0 else TAN if y == 1 else GREEN
    return c

def dead(F, eyes, navy):
    """him laid on his back on a bigger copy of his carpet (head to the left), carpet on the ground"""
    V = VIEW['front']; a = F.copy()
    for x, y, w, h in eyes:
        a[y:y + h, x:x + w] = a[y, x - 1]
        for dx, dy in MP.X5: a[y + h // 2 + dy, x + dx] = (*navy, 255)
    body = a[:V['edge'] - 2].copy()                           # everything that is him: rows above the carpet, and his lap on it
    for y in range(V['ct'], body.shape[0]):
        for x in range(body.shape[1]):
            if x < V['b0'] or x > V['b1'] or tuple(int(q) for q in body[y, x, :3]) in CARPET: body[y, x] = 0
    body[V['ct'], :V['b0'] + 1] = 0; body[V['ct'], V['b1']:] = 0
    body = MP.trim(np.rot90(body, 1).copy())
    c = full_carpet(F)
    cols = list(range(8)) + [7] * 5 + list(range(8, 20)) + [19] * 5 + list(range(20, 27))   # longer
    c = c[:, cols]
    rows = [0, 1, 2, 3] + [4, 5] * 4 + [6, 7, 8] + list(range(9, 16))                         # deeper
    c = c[rows]
    ch, cw = c.shape[:2]; bh, bw = body.shape[:2]
    out, (ox, oy) = MP.paste(c, body, (cw - bw) // 2, ch - 7 - bh)
    return MP.trim(stroke(out, navy))

def main():
    eyes = EYES
    F, B, R, L = (load(v) for v in ('front', 'back', 'right', 'left'))
    navy = MP.navy_of(F); out = {}
    for v, a in (('front', F), ('back', B), ('right', R), ('left', L)):
        ax = a.shape[1] / 2 + 1
        Image.fromarray(stroke(a, navy)).save(f'{ROOT}{NAME}/{v}.png')
        for f in range(8):
            out[f'walk_{v}_{f}'] = (tidy(stroke(ripple(grow(a), v, f), navy), HOVER), ax)
            if v != 'back': out[f'walkb_{v}_{f}'] = (tidy(stroke(ripple(grow(shut_eyes(a, eyes[v])), v, f), navy), HOVER), ax)
        out[f'sit_{v}'] = (hover(stroke(a, navy)), ax)
    can = MP.art(MP.CAN, MP.CAN_COL, navy); logs = MP.art(MP.LOGS, MP.LOG_COL, navy); lh, lw = logs.shape[:2]
    w = R.shape[1] + 2; ax = w / 2
    def both(key, a, ox):
        out[key.replace('*', 'right')] = (a, ax + ox); out[key.replace('*', 'left')] = (MP.mirror(a), a.shape[1] - (ax + ox))
    for k in range(4):
        # watering: the can held out over the front of the carpet, it dips and the water falls to the ground
        base = tidy(stroke(ripple(grow(R), 'right', k * 2), navy), HOVER)
        cx, cy = 17, 13 + (1 if k in (1, 2) else 0)
        a, (ox, oy) = MP.paste(base, can, cx, cy)
        sx, sy = cx + ox + MP.SPOUT[0], cy + oy + MP.SPOUT[1]
        if k:
            for d in range(1 + (k - 1) % 3, a.shape[0] - sy, 3):
                if not a[sy + d, sx, 3]: a[sy + d, sx] = (*MP.DROP, 255)
        both(f'water_*_{k}', a, ox)
        # logs: 0 on the ground ahead, 1 the carpet comes down to them, 2 on the front of the carpet, 3 on his lap
        lift = (HOVER, 1, 2, HOVER)[k]; base = hover(stroke(R, navy), lift); H = base.shape[0]
        lx, ly = ((w, H - lh), (w - 2, H - lh), (w - lw - 2, H - lift - 10 - lh), (12, 15))[k]
        a, (ox, oy) = MP.paste(base, logs, lx, ly)
        both(f'logs_*_{k}', a, ox)
    both('bend_*', hover(stroke(R, navy), 1), 0)
    out['dead'] = (dead(F, eyes['front'], navy), None)
    d = f'{ROOT}{NAME}/poses/'; os.makedirs(d, exist_ok=True); meta = {}
    for k, (a, x) in out.items():
        Image.fromarray(a).save(d + k + '.png')
        meta[k] = {'w': int(a.shape[1]), 'h': int(a.shape[0]), 'ax': round(float(x if x is not None else a.shape[1] / 2), 1)}
    json.dump(meta, open(d + 'poses.json', 'w'), indent=1)
    print(NAME, 'poses', len(meta))
    if len(sys.argv) > 1:
        S = 5; rows = [[f'walk_{v}_{f}' for f in range(8)] for v in ('front', 'right', 'back', 'left')]
        rows += [[f'walkb_front_{f}' for f in (0, 3)] + [f'water_right_{k}' for k in range(4)] + ['bend_right', 'sit_left'],
                 [f'logs_right_{k}' for k in range(4)] + ['logs_left_3', 'water_left_2', 'dead']]
        cw, chh = 44, 44; sh = Image.new('RGBA', (cw * 8 * S, chh * len(rows) * S), (104, 106, 130, 255))
        for j, r in enumerate(rows):
            for i, k in enumerate(r):
                a = out[k][0]; im = Image.fromarray(a).resize((a.shape[1] * S, a.shape[0] * S), Image.NEAREST)
                sh.alpha_composite(im, (i * cw * S + 10, (j + 1) * chh * S - im.height - 10))
        sh.save(sys.argv[1])

if __name__ == '__main__':
    main()
