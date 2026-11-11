# Where every character's eyes are, written to assets/final/eyes.json.
# The game used to GUESS the eyes while it ran ("a short dark run with skin on both sides"), which also caught
# hair strands, hood edges, sideburns and ears: hair blinked, some characters never shut their eyes in bed, and
# dead poses got X's in the wrong place. Now the eyes are found once here, checked on a sheet, and fixed by hand
# where the finder is wrong (FIX). The game (blink, sleep) and make_poses.py (dead X eyes) both read this file.
#
# eyes.json: { name: { front: [[x, y, w, h], ...], right: [...], left: [...] } }   (pixels of that view's own PNG)
# An empty list = no eyes to shut (sunglasses, a mask).
# usage (from mafia2-lab/): python -I tools/make_eyes.py [sheet.png]
import json, os, sys
import numpy as np
from PIL import Image

ROOT = 'assets/final/'
NAMES = sorted(n for n in os.listdir(ROOT) if os.path.isfile(ROOT + n + '/front.png'))

# hand-set answers, where the finder is wrong or there is nothing to find
FIX = {
    'alfa':   {'front': [], 'right': [], 'left': []},      # sunglasses
    'golf':   {'front': [], 'right': [], 'left': []},      # sunglasses
    'batman': {'front': [], 'right': [], 'left': []},      # white mask eyes
    'mafia':     {'front': [[11, 17, 2, 3], [17, 17, 2, 3]]},                       # the eyes touch his moustache
    'detective': {'front': [[11, 15, 2, 3], [17, 15, 2, 3]], 'right': [[17, 16, 2, 3]], 'left': [[5, 16, 2, 3]]},   # the eye touches the hat brim
    'ferrari':   {'right': [[17, 12, 1, 3]], 'left': [[6, 12, 1, 3]]},
    'redcap':    {'right': [[15, 13, 2, 3]], 'left': [[7, 13, 2, 3]]},
}

def lum(a): return a[..., 0] * .3 + a[..., 1] * .59 + a[..., 2] * .11

def candidates(a):
    """dark blocks 1-3 wide and 2-4 tall, standing in skin: light pixels to the left and right of most rows"""
    h, w = a.shape[:2]; al = a[..., 3] > 0; L = lum(a.astype(float)); dark = al & (L < 70); light = al & (L > 105)
    seen = np.zeros((h, w), bool); out = []
    for y in range(int(h * .2), int(h * .75)):
        for x in range(1, w - 1):
            if not dark[y, x] or seen[y, x]: continue
            st = [(x, y)]; seen[y, x] = True; px = []
            while st:
                cx, cy = st.pop(); px.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and dark[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; st.append((nx, ny))
            xs = [p[0] for p in px]; ys = [p[1] for p in px]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); bw, bh = x1 - x0 + 1, y1 - y0 + 1
            if not (1 <= bw <= 3 and 2 <= bh <= 4) or len(px) < bw * bh - 1: continue
            if x0 < 1 or x1 > w - 2: continue
            sides = sum(light[yy, x0 - 1] for yy in range(y0, y1 + 1)) + sum(light[yy, x1 + 1] for yy in range(y0, y1 + 1))
            if sides < (bh * 2) - 2: continue
            out.append((x0, y0, bw, bh))
    return out

def pick(c, view, w):
    if view == 'front':
        best = None
        for i in range(len(c)):
            for j in range(i + 1, len(c)):
                a, b = c[i], c[j]; dx = abs(a[0] - b[0])
                if not 4 <= dx <= 10: continue
                score = 3 * abs(a[1] - b[1]) + 2 * abs(a[2] - b[2]) + 2 * abs(a[3] - b[3]) + abs((a[0] + b[0] + a[2]) / 2 - w / 2) * .3 + a[1] * .2 - a[2] * a[3] * .5
                if best is None or score < best[0]: best = (score, a, b)
        return sorted([best[1], best[2]]) if best else []
    if not c: return []
    # a side view shows one eye: the candidate nearest the way they face
    return [max(c, key=lambda e: (e[2] * e[3], e[0]))] if view == 'right' else [max(c, key=lambda e: (e[2] * e[3], -e[0]))]

def main():
    out = {}
    for n in NAMES:
        out[n] = {}
        for v in ('front', 'right', 'left'):
            a = np.asarray(Image.open(f'{ROOT}{n}/{v}.png').convert('RGBA'))
            out[n][v] = FIX[n][v] if n in FIX and v in FIX[n] else [list(map(int, e)) for e in pick(candidates(a), v, a.shape[1])]
        print(n, out[n])
    json.dump(out, open(ROOT + 'eyes.json', 'w'), indent=0)
    if len(sys.argv) > 1:   # check sheet: every view with its eyes shut (the top rows wiped to skin), eyes boxed in red beside it
        S = 5; tiles = []
        for n in NAMES:
            row = []
            for v in ('front', 'right', 'left'):
                a = np.asarray(Image.open(f'{ROOT}{n}/{v}.png').convert('RGBA')).copy(); b = a.copy()
                for x, y, w, h in out[n][v]:
                    skin = a[y, x - 1].copy(); a[y:y + h - 1, x:x + w] = skin
                    b[y:y + h, x:x + w] = (255, 0, 0, 255)
                row += [a, b]
            H = max(r.shape[0] for r in row); W = sum(r.shape[1] + 2 for r in row)
            t = Image.new('RGBA', (W, H), (104, 106, 130, 255)); x = 0
            for r in row: t.alpha_composite(Image.fromarray(r), (x, 0)); x += r.shape[1] + 2
            tiles.append(t.resize((t.width * S, t.height * S), Image.NEAREST))
        cols = 2; cw = max(t.width for t in tiles) + 8; ch = max(t.height for t in tiles) + 8
        sh = Image.new('RGBA', (cw * cols, ch * ((len(tiles) + 1) // cols)), (60, 60, 80, 255))
        for i, t in enumerate(tiles): sh.paste(t, ((i % cols) * cw + 4, (i // cols) * ch + 4))
        sh.save(sys.argv[1])

if __name__ == '__main__':
    main()
