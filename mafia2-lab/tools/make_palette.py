# Adds the colours of newer characters to his PixelLab palette file, without disturbing the colours already in it.
#   Dropbox "chrispy games/character sprites/MAFIA2-palette.png" (one row of 24 px swatches) + MAFIA2-palette.txt (hex list)
# A colour is added only if it is used a fair bit and nothing close to it is already in the palette.
# usage (from mafia2-lab/): python -I tools/make_palette.py alfa golf ferrari batman
import sys
import numpy as np
from PIL import Image
from collections import Counter

OUT = 'C:/Users/Chris/Dropbox/Documents/chrispy games/character sprites/MAFIA2-palette'
NEAR, MIN_PX, SW = 24, 8, 24      # how close counts as "already there"; how many pixels a colour needs; swatch size

def main():
    pal = [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in open(OUT + '.txt').read().split()]
    before = len(pal); cnt = Counter()
    for n in sys.argv[1:]:
        for v in ('front', 'back', 'left', 'right'):
            a = np.asarray(Image.open(f'assets/final/{n}/{v}.png').convert('RGBA')).reshape(-1, 4)
            cnt.update(tuple(int(c) for c in p[:3]) for p in a if p[3] >= 128)
    added = []
    for c, k in cnt.most_common():
        if k < MIN_PX: break
        if min(sum((a - b) ** 2 for a, b in zip(c, q)) ** .5 for q in pal) > NEAR: pal.append(c); added.append((c, k))
    pal.sort(key=lambda c: c[0] * .3 + c[1] * .59 + c[2] * .11)
    im = Image.new('RGB', (SW * len(pal), SW))
    for i, c in enumerate(pal): im.paste(c, (i * SW, 0, i * SW + SW, SW))
    im.save(OUT + '.png')
    open(OUT + '.txt', 'w').write(' '.join('#%02x%02x%02x' % c for c in pal) + '\n')
    print(before, '->', len(pal)); [print('  + #%02x%02x%02x  (%d px)' % (*c, k)) for c, k in added]

if __name__ == '__main__':
    main()
