# Bring his hand-fixed sheets back into the game.
# Sheet: 4 cells (front, right, back, left), each 40x48, feet on row 44 (made 10 Nov 2026).
# Cuts each cell, trims it, saves assets/final/<name>/{front,right,back,left}.png (as he drew them).
# usage: python from_sheet.py "<...>/character sprites/<name>/<name>-sheet.png" [more sheets]
import sys, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CW, CH = 40, 48
for path in sys.argv[1:]:
    name = os.path.basename(path).replace('-sheet.png', '')
    s = Image.open(path).convert('RGBA')
    if s.size != (CW*4, CH): print(name, 'unexpected size', s.size, '(want 160x48)'); continue
    out = os.path.join(ROOT, 'assets', 'final', name); os.makedirs(out, exist_ok=True)
    for i, v in enumerate(['front', 'right', 'back', 'left']):
        cell = s.crop((i*CW, 0, i*CW+CW, CH))
        cell = cell.crop(cell.getbbox()); cell.save(os.path.join(out, v + '.png'))
    print(name, 'imported')
