# Make every cabin cut-out include its full dark outline (the background remover trimmed 1-2 px off
# some roofs), then rebuild the shared template. Pixels always come from the ORIGINAL town art.
# usage (from mafia2-lab/): python -I tools/fix_cabin_cuts.py
import os, shutil
import numpy as np
from PIL import Image
from scipy import ndimage

T = 'assets/town3/'
DOORS = [[280,78],[151,146],[409,146],[78,280],[482,280],[78,446],[482,446],[124,612],[436,612],[280,666]]
FW, FH = 116, 154                      # frame: door x-58..x+58, door top-90..top+64

if not os.path.isdir(T + 'cabins-cut-v1'):
    shutil.copytree(T + 'cabins-cut', T + 'cabins-cut-v1')
    shutil.copy(T + 'cabin-template-mask.png', T + 'cabins-cut-v1/template.png')

o = np.asarray(Image.open('assets/town2-1x.png').convert('RGB')).astype(int)
H, W, _ = o.shape
PAD = 100
op = np.pad(o, ((PAD, PAD), (0, 0), (0, 0)))
inside = np.pad(np.ones((H, W), bool), ((PAD, PAD), (0, 0)))

tmpl = np.asarray(Image.open(T + 'cabins-cut-v1/template.png').convert('L')) > 127
rows = np.where(tmpl.any(1))[0]
bottom = rows.max()                     # lowest row of the steps
td1 = ndimage.binary_dilation(tmpl, iterations=1); td1[bottom+1:] = False
DECK = 136                              # last row of the deck; below it only the steps
upper = np.zeros_like(tmpl); upper[:DECK+1] = True
steps = np.zeros_like(tmpl); steps[:, 40:77] = True
lowrow = np.zeros_like(tmpl); lowrow[DECK+1:DECK+3] = True
# where 9 of the 10 first cuts agree (grown 1 px): surely cabin
v1all = [np.asarray(Image.open(f'{T}cabins-cut-v1/cabin{i}.png'))[..., 3] > 0 for i in range(10)]
safe = np.sum(v1all, 0) >= 9
inner = ndimage.binary_erosion(safe, iterations=4)

masks = []
for i, (cx, top) in enumerate(DOORS):
    y0 = top - 90 + PAD
    reg = op[y0:y0+FH, cx-58:cx+58]
    ok = inside[y0:y0+FH, cx-58:cx+58]
    r, g, b = reg[..., 0], reg[..., 1], reg[..., 2]
    grass = (b > r + 18) & (b > g + 8)
    # the cabins' outline family: very dark red-purple with less blue than red, e.g. (35,4,25), (56,17,26)
    # (the path's dark mortar, e.g. (44,26,65), has more blue than red, so it never matches)
    outline = (g < 30) & (r > g + 10) & (b < r)
    v1 = v1all[i]
    # the first cut kept some grass/shadow beside the walls: keep a grass-coloured pixel only where
    # (nearly) every cabin has cabin (blue walls/roofs live there), drop it elsewhere
    m = v1 & (safe | ~grass) & upper
    m |= td1 & ~grass & upper           # chimney bricks etc. the remover missed
    for _ in range(10):                 # walk out along the dark outline (roof edges the remover trimmed)
        m |= ndimage.binary_dilation(m) & outline & upper
    # fill the little notches between outline pixels and the roof
    m |= ndimage.binary_closing(m, np.ones((3, 3), bool), iterations=2) & ~grass & upper
    m[DECK+1:] = v1[DECK+1:] & steps[DECK+1:]
    for _ in range(3):                  # the deck's bottom line and the steps' outline
        m |= ndimage.binary_dilation(m) & outline & (upper | steps | lowrow)
    # grass still stuck to the edge (e.g. beside the chimneys): peel edge pixels whose exact colour
    # never appears in this cabin's solid middle (pixel art = a small set of exact colours, so
    # roof/wall colours are always in there and are never peeled)
    key = (reg[..., 0] << 16) | (reg[..., 1] << 8) | reg[..., 2]
    pal = np.isin(key, np.unique(key[m & inner]))
    for _ in range(6):
        m &= ~(m & ndimage.binary_dilation(~m) & grass & ~pal)
    blob = v1 & ~m
    lab, n = ndimage.label(m)
    if n > 1: m = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)
    m = ndimage.binary_fill_holes(m)
    # the roof's peak only gets wider going down; a wider shelf above a narrower row is the kerb of
    # a path behind the roof (cabin 5): cut everything above it in the peak's columns
    w = m[:20, 30:76].sum(1)
    shelf = [y for y in range(19) if w[y] > w[y+1] + 2]
    if shelf: m[:max(shelf)+1, 30:76] = False
    m &= ok
    masks.append(m)
    rgba = np.zeros((FH, FW, 4), np.uint8)
    rgba[..., :3] = reg.astype(np.uint8)
    rgba[..., 3] = m * 255
    Image.fromarray(rgba).save(f'{T}cabins-cut/cabin{i}.png')
    ring = ndimage.binary_dilation(m) & ~m & ok
    px = reg[ring]
    left = int(((px.mean(1) < 45) & ~(px[:, 2] > px[:, 0] + 18)).sum())
    print(f'cabin{i}: {int(m.sum())} px, dropped from first cut {int(blob.sum())}, dark non-grass pixels left on the edge: {left}')

vote = np.sum(masks, 0) >= 5
lab, n = ndimage.label(vote)
big = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)
Image.fromarray((ndimage.binary_fill_holes(big) * 255).astype(np.uint8)).save(T + 'cabin-template-mask.png')
