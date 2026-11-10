# Build the town BASE from the current town art, keeping its exact pixels:
#   - cabins taken out (their cut-outs are in assets/town3/cabins-cut), the gap filled with grass/path
#     (always hidden under a cabin sprite, so the fill only has to be plausible)
#   - the cobble paths recoloured to grey stone; the kerb edge and every stone stay where they are
# usage: python -I build_town_base.py   (run from mafia2-lab/)
import numpy as np, cv2
from PIL import Image
from scipy import ndimage
from collections import deque

T = 'assets/town3/'
# the town with the old posts, lamps and strings already painted out (tools/build_props.py makes it)
src = np.asarray(Image.open(T + 'town-noprops-1x.png').convert('RGB')).astype(np.float64)
H, W, _ = src.shape
DOORS = [[280,78],[151,146],[409,146],[78,280],[482,280],[78,446],[482,446],[124,612],[436,612],[280,666]]

# 1) cabins out
cab = np.zeros((H, W), bool)
for i, (cx, top) in enumerate(DOORS):
    a = np.asarray(Image.open(f'{T}cabins-cut/cabin{i}.png'))[..., 3] > 0
    for yy in range(a.shape[0]):
        Y = top - 90 + yy
        if 0 <= Y < H:
            cab[Y, cx-58:cx-58+a.shape[1]] |= a[yy]
# fill ONLY under the cabin (always hidden by a cabin sprite); every pixel outside stays original
hole = cab
base = cv2.inpaint(src.astype(np.uint8), hole.astype(np.uint8)*255, 6, cv2.INPAINT_TELEA).astype(np.float64)

# 2) the path: warm, low-saturation stone joined to the square, plus the dark kerb lines along it
# found on the ORIGINAL art (the cabin fill would cut paths off where they meet a cabin)
mx, mn = src.max(-1), src.min(-1)
sat = np.where(mx > 0, (mx-mn)/np.maximum(mx, 1), 0); val = mx/255
r, g, b = src[..., 0], src[..., 1], src[..., 2]
warm = (r >= b) & (r >= g - 4)
stone = warm & (sat < 0.52) & (val > 0.28) & ~((val > 0.86) & (sat < 0.33))   # not the warm bulbs
yy, xx = np.mgrid[0:H, 0:W]
stage = ((xx-279)/43.5)**2 + ((yy-365.5)/41.0)**2 <= 1     # measured: wood spans x 237..321, y 326..405
stone &= ~stage & ~cab
lab, n = ndimage.label(stone)
keep = lab == lab[340, 210]                         # the region joined to the square
for p in [(150, 280), (650, 280), (352, 90), (352, 470)]:   # paths, in case one is cut off by a post
    if lab[p] and lab[p] != lab[340, 210]: keep |= lab == lab[p]
path = ndimage.binary_fill_holes(keep) & ~stage
# the dark gaps between stones are a little purple; where a path runs into a cabin they are not
# enclosed, so take any non-grass pixel hugging the path too (grass is strongly blue)
grass = (b > r + 18) & (b > g + 8)
path |= ndimage.binary_closing(keep, iterations=3) & ~grass & ~stage & ~cab
# stones lit orange by the old baked window light: grow the path through anything that isn't
# grass, a cabin or the stage (the code draws window light itself now)
path = ndimage.binary_propagation(path, mask=~grass & ~cab & ~stage)
edge = ndimage.binary_dilation(path, iterations=2) & ~path & warm & (val < 0.5)   # the kerb's dark lines
path_all = path | edge

# 3) grey stone: same light and dark as the old stone, colour swapped for a cool moonlit grey
r, g, b = base[..., 0], base[..., 1], base[..., 2]
y = 0.30*r + 0.59*g + 0.11*b
grey = np.stack([y*0.92+6, y*0.97+5, y*1.06+10], -1)
# ...but keep a soft orange tint where the old art was lit by the lights in the middle (his call):
# the old stones' own warmth, smoothed, says how much light hit each spot (warm ~60 by the stage,
# ~15 at the outer path ends); keep up to TINT of the old colour there, none at the far ends
TINT = 0.7
sr, sb = src[..., 0], src[..., 2]
pm = path_all.astype(np.float64)
den = np.maximum(ndimage.gaussian_filter(pm, 10), 1e-6)
warmth = ndimage.gaussian_filter((sr - sb) * pm, 10) / den
light = np.clip((warmth - 15) / 45, 0, 1) ** 1.3
k = (TINT * light)[..., None]
stone = grey * (1 - k) + base * k
out = base.copy(); out[path_all] = stone[path_all]
out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save(f'{T}town-base-night-1x.png')
Image.fromarray((path_all*255).astype(np.uint8)).save(f'{T}path-mask.png')
print('cabin pixels', int(cab.sum()), 'path pixels', int(path_all.sum()))
