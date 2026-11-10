# Put Chris's cut posts, lamps and bulb strings (assets/town3/props-src, drawn bigger than the town)
# onto the town's own 560 x 750 pixel grid, each exactly where the old one was painted.
#
# Where each piece goes was measured by tools/fit_props.py: every piece was shrunk at many sizes and slid
# over the ORIGINAL town (town2-1x.png) until it covered the old post best. The plaza is mirror-symmetric
# (pixel column c <-> 560 - c), so the left side is fitted and the right side is its mirror image.
#
# Output (assets/town3/props/):
#   <name>.png        one sprite per post / lamp, cropped, at 1x
#   strings.png       the overhead bulb strings, full 560 x 750 (always drawn over people)
#   props.json        where each sprite sits and the y its feet are at (for sorting with people)
#   town-noprops-1x.png  the ORIGINAL town with the old posts, lamps and strings painted out
#                        (build_town_base.py starts from this)
# usage (from mafia2-lab/): python -I tools/build_props.py
import json, os
import numpy as np, cv2
from PIL import Image
from scipy import ndimage

T = 'assets/town3/'
SRC = T + 'props-src/'
OUT = T + 'props/'
os.makedirs(OUT, exist_ok=True)
Z = 4                                   # fitting was done on the town blown up 4x (quarter-pixel steps)
W, H = 560, 750

# piece, scale (piece pixels per town pixel), mirrored?, top-left on the 4x town
FIT = {
    'top':    ('top-post-with-lights.png',    6.72, False, 699, 947),
    'bottom': ('bottom-post-with-lights.png', 6.76, False, 904, 1741),
    'side':   ('post-with-lights.png',        6.80, False, 701, 1255),   # left; right = mirror
    'bare':   ('bare-post.png',               6.18, False, 685, 1144),
    'lampU':  ('lamp-post.png',               8.26, False, 632, 1201),   # the two upper lamps are smaller
    'lampD':  ('lamp-post.png',               6.84, False, 629, 1626),
}

def palette_of(p, n=40):
    """the piece's own colours (it is soft-edged AI art, so cluster them down to a pixel-art palette)"""
    px = p[p[..., 3] > 200][:, :3].astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.2)
    _, _, cent = cv2.kmeans(px, min(n, len(px)), None, crit, 4, cv2.KMEANS_PP_CENTERS)
    return cent

def render(name, alpha_cut=0.5):
    """the piece on the 1x town grid: every town pixel takes the colour that covers most of it"""
    f, k, flip, x4, y4 = FIT[name]
    p = np.asarray(Image.open(SRC + f).convert('RGBA'))
    if flip: p = p[:, ::-1]
    pal = palette_of(p)
    rgb = p[..., :3].astype(np.float32)
    d = ((rgb[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    idx = d.argmin(-1)
    opaque = p[..., 3] > 127
    n = len(pal)
    w4, h4 = round(p.shape[1] * Z / k), round(p.shape[0] * Z / k)
    # where the piece lands, padded out to whole town pixels
    X0, Y0 = x4 // Z, y4 // Z
    X1, Y1 = -(-(x4 + w4) // Z), -(-(y4 + h4) // Z)
    votes = np.zeros((Y1 - Y0, X1 - X0, n + 1), np.float32)       # last = see-through
    for c in range(n + 1):
        m = ((idx == c) & opaque) if c < n else ~opaque
        if not m.any(): continue
        s = cv2.resize(m.astype(np.float32), (w4, h4), interpolation=cv2.INTER_AREA)
        canvas = np.zeros(((Y1 - Y0) * Z, (X1 - X0) * Z), np.float32)
        if c == n: canvas[:] = 1
        canvas[y4 - Y0 * Z:y4 - Y0 * Z + h4, x4 - X0 * Z:x4 - X0 * Z + w4] = s
        votes[..., c] = canvas.reshape(Y1 - Y0, Z, X1 - X0, Z).mean((1, 3))
    cover = 1 - votes[..., n]
    col = pal[votes[..., :n].argmax(-1)]
    out = np.zeros((H, W, 4), np.uint8)
    out[Y0:Y1, X0:X1, :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[Y0:Y1, X0:X1, 3] = (cover >= alpha_cut) * 255
    return out

def mirror(a):
    """column c -> 560 - c (column 0 has no partner; nothing is drawn there)"""
    m = np.zeros_like(a)
    m[:, 1:] = a[:, :0:-1]
    return m


def fill(img, hole, avoid, lab, p=4, win=44):
    """exemplar fill (Criminisi): grow the hole shut from its edge, each time copying the real
    patch of town (exact pixels, so stones stay crisp) whose known part matches best;
    linear things like the kerb lines get filled first so they carry on straight.
    lab = 1 for stone, 0 for water/grass (inside the hole: the nearest known one), and a copied
    patch must have the same stone/water layout, so stones never land in a pond or the other way"""
    img = img.astype(np.float32).copy()
    hole = hole.copy()
    Hh, Ww = hole.shape
    labf = lab.astype(np.float32)
    conf = (~hole).astype(np.float32)
    P = 2 * p + 1
    bad = ndimage.binary_dilation(hole | avoid, np.ones((P, P), bool))   # patch centres that touch these can't be sources
    bad[:p] = bad[-p:] = True; bad[:, :p] = bad[:, -p:] = True
    gray0 = img.mean(-1)
    steps = 0
    while hole.any():
        front = hole & ndimage.binary_dilation(~hole)
        ys, xs = np.nonzero(front)
        # confidence term
        cs = ndimage.uniform_filter(conf, P)[ys, xs]
        # data term: isophote strength across the front
        g = np.where(hole, np.nan, img.mean(-1))
        gy, gx = np.gradient(np.where(np.isnan(g), gray0, g))
        known = (~hole).astype(np.float32)
        ny, nx = np.gradient(ndimage.gaussian_filter(known, 1))
        dterm = np.abs(-gy[ys, xs] * nx[ys, xs] + gx[ys, xs] * ny[ys, xs]) / 255 + 0.001
        i = np.argmax(cs * dterm)
        cy, cx = int(np.clip(ys[i], p, Hh - p - 1)), int(np.clip(xs[i], p, Ww - p - 1))
        tgt = img[cy - p:cy + p + 1, cx - p:cx + p + 1]
        tk = ~hole[cy - p:cy + p + 1, cx - p:cx + p + 1]
        y0, y1 = max(p, cy - win), min(Hh - p, cy + win + 1)
        x0, x1 = max(p, cx - win), min(Ww - p, cx + win + 1)
        region = img[y0 - p:y1 + p, x0 - p:x1 + p]
        sw = np.lib.stride_tricks.sliding_window_view(region, (P, P), axis=(0, 1))   # (ny,nx,3,P,P)
        diff = ((sw - tgt.transpose(2, 0, 1)[None, None]) ** 2 * tk[None, None, None]).sum((2, 3, 4))
        lw = np.lib.stride_tricks.sliding_window_view(labf[y0 - p:y1 + p, x0 - p:x1 + p], (P, P))
        diff += np.abs(lw - labf[cy - p:cy + p + 1, cx - p:cx + p + 1][None, None]).sum((2, 3)) * 4e4
        diff[bad[y0:y1, x0:x1]] = np.inf
        # a little nudge towards nearby sources keeps the stones' rhythm local
        yy, xx = np.mgrid[y0:y1, x0:x1]
        diff = diff + ((yy - cy) ** 2 + (xx - cx) ** 2) * 0.5
        j = np.unravel_index(np.argmin(diff), diff.shape)
        sy, sx = y0 + j[0], x0 + j[1]
        src = img[sy - p:sy + p + 1, sx - p:sx + p + 1]
        um = hole[cy - p:cy + p + 1, cx - p:cx + p + 1].copy()
        tgt[um] = src[um]
        conf[cy - p:cy + p + 1, cx - p:cx + p + 1][um] = cs[i] / 1.0
        hole[cy - p:cy + p + 1, cx - p:cx + p + 1][um] = False
        steps += 1
    return img, steps


def bbox(a):
    ys, xs = np.nonzero(a[..., 3])
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

def post_columns(a, run=25):
    """columns a post stands in: find each pole (a solid run of 25+ rows; strings are 1-2 px),
    then take the width of the base box at the pole's foot"""
    al = a[..., 3] > 0
    best = np.zeros(W, int)
    for x in range(W):
        col = al[:, x]
        if col.any():
            lab, n = ndimage.label(col)
            best[x] = np.bincount(lab)[1:].max()
    lab, n = ndimage.label(best >= run)
    cols = []
    for i in range(1, n + 1):
        xs = np.nonzero(lab == i)[0]
        foot = np.nonzero(al[:, xs].any(1))[0].max()          # the pole's lowest row
        base = al[foot - 5:foot + 1].any(0)
        bl, _ = ndimage.label(base)
        part = np.nonzero(bl == bl[xs[0]])[0]
        cols.append((int(part.min()), int(part.max()) + 1))
    return cols

if __name__ == '__main__':
    L = {n: render(n) for n in FIT}
    sprites = {}            # name -> full-size RGBA
    over = np.zeros((H, W, 4), np.uint8)
    # posts 1, 2 (top) and 7, 8 (bottom): the posts stand with people, the strings go over them
    for piece, names in (('top', ('post1', 'post2')), ('bottom', ('post7', 'post8'))):
        a = L[piece]
        cols = post_columns(a)
        assert len(cols) == 2, (piece, cols)
        rest = a.copy()
        for nm, (c0, c1) in zip(names, cols):
            s = np.zeros_like(a); s[:, c0:c1] = a[:, c0:c1]; sprites[nm] = s
            rest[:, c0:c1] = 0
        m = rest[..., 3] > 0; over[m] = rest[m]
    # the sides: bare post 3 behind, the bulb chain on it, post 4 below; right side = mirror
    side = L['side']; SPLIT = 367          # first row of post 4's cap (the chain's last bulb ends above it)
    chain = side.copy(); chain[SPLIT:] = 0
    p4 = side.copy(); p4[:SPLIT] = 0
    sprites.update(post3=L['bare'], chain3=chain, post4=p4, lamp1=L['lampU'], lamp2=L['lampD'])
    sprites.update(post5=mirror(L['bare']), chain5=mirror(chain), post6=mirror(p4),
                   lamp3=mirror(L['lampU']), lamp4=mirror(L['lampD']))
    meta = {}
    for nm, s in sprites.items():
        x0, y0, x1, y1 = bbox(s)
        Image.fromarray(s[y0:y1, x0:x1]).save(OUT + f'{nm}.png')
        meta[nm] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), base=int(y1 - 1))
    # a chain hangs on its post: sort it just in front of that post
    for c, p in (('chain3', 'post3'), ('chain5', 'post5')):
        meta[c]['base'] = meta[p]['base'] + 0.5
    # lamp glass (the brightest bit) = where the lamp's glow is drawn
    for nm in ('lamp1', 'lamp2', 'lamp3', 'lamp4'):
        s = sprites[nm].astype(int); v = s[..., :3].sum(-1) * (s[..., 3] > 0)
        ys, xs = np.nonzero(v >= np.sort(v[v > 0])[-12])
        meta[nm]['glow'] = [round(float(xs.mean()) + .5, 1), round(float(ys.mean()) + .5, 1)]
    x0, y0, x1, y1 = bbox(over)
    Image.fromarray(over[y0:y1, x0:x1]).save(OUT + 'strings.png')
    meta['strings'] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0), base=None)
    json.dump(meta, open(OUT + 'props.json', 'w'), indent=1)
    print('sprites', len(sprites), {k: (v['x'], v['y'], v['w'], v['h'], v['base']) for k, v in meta.items()})

    # ---- paint the OLD posts, lamps and strings out of the original town ----
    src = np.asarray(Image.open('assets/town2-1x.png').convert('RGB'))
    s = src.astype(int)
    hole = np.zeros((H, W), bool)
    # the old posts and lamps (the rects the game used to redraw them), 1 px wider, and the side chains
    OLD = [[226,237,241,288],[321,237,336,288],[156,296,170,347],[170,284,186,348],[170,363,186,420],
           [156,404,170,465],[389,296,404,347],[375,284,391,348],[375,363,391,420],[389,404,404,465],
           [225,434,241,491],[321,434,337,491],[170,347,186,364],[375,347,391,364]]
    for x0, y0, x1, y1 in OLD: hole[y0-1:y1+1, x0-1:x1+1] = True
    # the old strings ran close to the new ones: everything near a new string that is string-dark or bulb-bright
    band = np.asarray(Image.open(T + 'mask-pass1-1x.png').convert('L')) > 127
    near = ndimage.binary_dilation(over[..., 3] > 0, iterations=7) & ndimage.binary_dilation(band, iterations=3)
    mx, mn = s.max(-1), s.min(-1)
    val = mx / 255; sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = s[..., 0], s[..., 1], s[..., 2]
    dark = (val < 0.36) & ~((b > r + 40) & (b > 110))          # string: very dark (not deep water)
    bright = (val > 0.86) & (r > b + 40)                       # bulb cores
    rim = (sat > 0.45) & (r > g + 25) & (r > b + 60) & (val > 0.55)   # bulb rims
    hole |= near & dark
    hole |= ndimage.binary_dilation(near & (bright | rim), iterations=2)
    hole = ndimage.binary_dilation(hole & near, iterations=1) & near | hole
    Image.fromarray((hole * 255).astype(np.uint8)).save(OUT + '_hole.png')
    # never copy from cabins or the stage
    D = [[280,78],[151,146],[409,146],[78,280],[482,280],[78,446],[482,446],[124,612],[436,612],[280,666]]
    cab = np.zeros((H, W), bool)
    for i, (cx, top) in enumerate(D):
        a = np.asarray(Image.open(f'{T}cabins-cut/cabin{i}.png'))[..., 3] > 0
        for yy in range(a.shape[0]):
            Y = top - 90 + yy
            if 0 <= Y < H: cab[Y, cx-58:cx+58] |= a[yy]
    yy, xx = np.mgrid[0:H, 0:W]
    stage = ((xx - 279) / 46) ** 2 + ((yy - 365.5) / 44) ** 2 <= 1
    # stone or water/grass (water is strongly blue); inside the hole, whichever is nearest
    wet = (b > r + 18) & (b > g + 8)
    # over a pond, anything near a string that is not one of the pond's own colours is old string / glow
    key = (r << 16) | (g << 8) | b
    u, c = np.unique(key[wet & ~ndimage.binary_dilation(near | hole, iterations=4)], return_counts=True)
    waterpal = u[c >= 30]
    clean = wet & np.isin(key, waterpal)
    pond = ndimage.binary_closing(wet, np.ones((7, 7), bool))
    hole |= near & pond & ~clean
    Image.fromarray((hole * 255).astype(np.uint8)).save(OUT + '_hole.png')
    _, (iy, ix) = ndimage.distance_transform_edt(hole, return_indices=True)
    lab = ~wet[iy, ix]
    Image.fromarray((lab * 255).astype(np.uint8)).save(OUT + '_lab.png')
    work = src.copy(); left = hole.copy()
    # stone: Chris's floor-only picture (pass1-a.png: the same town with the posts painted out; it lines
    # up stone for stone). Shrink it to the grid, match its colour to the real floor around the holes,
    # then snap every patched pixel to a colour the real floor uses, so the patch is as crisp as the rest.
    fl = cv2.resize(np.asarray(Image.open(T + 'pass1-a.png').convert('RGB')).astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)
    plaza = np.zeros((H, W), bool); plaza[215:505, 140:421] = True
    flw = cv2.resize(np.asarray(Image.open(T + 'pass1-a.png').convert('RGB')), (W, H), interpolation=cv2.INTER_AREA).astype(int)
    fwet = (flw[..., 2] > flw[..., 0] + 18) & (flw[..., 2] > flw[..., 1] + 8)     # what the floor picture says is water
    out = work.astype(np.float32); steps = 0
    for kind, here in (('stone', ~fwet), ('water', fwet)):
        ref = plaza & (lab if kind == 'stone' else clean) & here & ~ndimage.binary_dilation(hole, iterations=2) & ~stage
        f2 = fl.copy()
        for ch in range(3):
            A = np.stack([fl[..., ch][ref], np.ones(ref.sum())], 1)
            k, c0 = np.linalg.lstsq(A, s[..., ch][ref].astype(np.float64), rcond=None)[0]
            f2[..., ch] = fl[..., ch] * k + c0
        u, c = np.unique(key[ref], return_counts=True)
        pal = u[c >= 10]
        palrgb = np.stack([pal >> 16, (pal >> 8) & 255, pal & 255], 1).astype(np.float32)
        ys, xs = np.nonzero(left & here)
        px = f2[ys, xs]
        out[ys, xs] = palrgb[((px[:, None, :] - palrgb[None]) ** 2).sum(-1).argmin(1)]
        print(kind, 'patched', len(ys), 'palette', len(pal))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(T + 'town-noprops-1x.png')
    print('hole px', int(hole.sum()), 'fill steps', steps)
