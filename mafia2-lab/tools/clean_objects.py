"""Tidy the furniture cut-outs made by split_room.py.

Usage: python -I clean_objects.py <room-objects dir>

split_room.py cuts each object out by comparing the furnished room with the
empty one, so bits of floor and wall that were lit differently came along too
(and then cast their own shadows in the game). This removes those by hand-picked
rules, fills two small holes in the desk, and writes bed-quilt.png: the part of
the bed from the sheet line down, drawn over a sleeping head.
Safe to run twice.
"""
import sys, os, json
import numpy as np
from PIL import Image

d = sys.argv[1]
meta = json.load(open(os.path.join(d, 'objects.json')))
room = np.asarray(Image.open(os.path.join(d, 'room-empty.png')).convert('RGBA')).astype(int)


def load(n): return np.array(Image.open(os.path.join(d, n + '.png')).convert('RGBA'))
def save(n, a): Image.fromarray(a, 'RGBA').save(os.path.join(d, n + '.png'))
def cut(a, x0, y0, x1, y1): a[y0:y1 + 1, x0:x1 + 1, 3] = 0   # inclusive box


report = {}

# fireplace: wall strips right of the chimney, floor strip right of the hearth
a = load('fireplace'); before = (a[..., 3] > 0).sum()
cut(a, 31, 0, 38, 44); cut(a, 37, 0, 38, 96)
save('fireplace', a); report['fireplace'] = before - (a[..., 3] > 0).sum()

# armchair: fire-lit floor above the far arm, and a strip down the right edge
a = load('armchair'); before = (a[..., 3] > 0).sum()
for row, col in {0: 37, 1: 37, 2: 37, 3: 16, 4: 17, 5: 18, 6: 18, 7: 18, 8: 22, 9: 30, 10: 35, 11: 36, 12: 37, 13: 37, 14: 36}.items():
    cut(a, col, row, 38, row)
save('armchair', a); report['armchair'] = before - (a[..., 3] > 0).sum()

# rug: strips on the right and top right, a scrap under the bottom edge
a = load('rug'); before = (a[..., 3] > 0).sum()
cut(a, 53, 0, 55, 51); cut(a, 0, 49, 55, 51)
for row, col in {0: 43, 1: 43, 2: 43, 3: 43, 4: 41, 5: 43, 6: 45, 7: 46}.items():
    cut(a, col, row, 55, row)
save('rug', a); report['rug'] = before - (a[..., 3] > 0).sum()

# floor lamp: window leaves beside the shade, skirting beside the pole, a strip on the right
a = load('floorlamp'); before = (a[..., 3] > 0).sum()
cut(a, 0, 2, 2, 3); cut(a, 0, 4, 1, 5)
cut(a, 4, 19, 6, 23); cut(a, 4, 28, 6, 29)
cut(a, 17, 30, 19, 50)
save('floorlamp', a); report['floorlamp'] = before - (a[..., 3] > 0).sum()

# desk chair: shadowed floor either side of the frame
a = load('chair'); before = (a[..., 3] > 0).sum()
cut(a, 0, 0, 1, 25); cut(a, 24, 0, 25, 25)
save('chair', a); report['chair'] = before - (a[..., 3] > 0).sum()

# right bedside table: the floor lamp's shade poking in at the top right
a = load('nightR'); before = (a[..., 3] > 0).sum()
cut(a, 18, 0, 19, 5)
save('nightR', a); report['nightR'] = before - (a[..., 3] > 0).sum()

# bed: lamp-lit wall above the posts, floor beside the frame and under it
a = load('bed'); before = (a[..., 3] > 0).sum()
m = meta['bed']
cut(a, 0, 0, 5, 4); cut(a, 51, 0, 54, 4)
cut(a, 6, 70, 48, 72); cut(a, 0, 72, 54, 72)
sub = room[m['y']:m['y'] + a.shape[0], m['x']:m['x'] + a.shape[1]]
for col in (0, 54):
    diff = np.abs(a[:, col, :3].astype(int) - sub[:, col, :3]).sum(1)
    a[diff < 80, col, 3] = 0
save('bed', a); report['bed'] = before - (a[..., 3] > 0).sum()

# desk: fill the holes on the left edge with the desk colour next to them
a = load('desk'); filled = 0
for row in range(14, 40):
    opaque = np.nonzero(a[row, :, 3])[0]
    if not len(opaque): continue
    for col in range(0, 6):
        if a[row, col, 3] == 0:
            src = opaque[opaque > col]
            if len(src): a[row, col] = a[row, src[0]]; filled += 1
save('desk', a); report['desk (filled)'] = filled

# bed quilt: everything from the sheet's fold line down
bed = load('bed'); q = np.zeros_like(bed)
for col in range(bed.shape[1]):
    edge = 24 if 18 <= col <= 35 else 25 if 14 <= col <= 40 else 27
    q[edge:, col] = bed[edge:, col]
save('bed-quilt', q)

print(report)
