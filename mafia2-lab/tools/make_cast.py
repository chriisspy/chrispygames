# One go per character: download PixelLab turnaround -> feet on one line -> merge near-same colours
# -> his final style (tools/final_style.py) -> assets/final/<name>/{front,back,left,right}.png
# usage: python make_cast.py name=<pixellab character id> [name=id ...]
import sys, os, subprocess, urllib.request, time
from collections import Counter
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
USER = '86a357f3-f8dc-4947-92d1-4b46f9125b7f'
DIRS = ['south', 'east', 'north', 'west']
dist = lambda a, b: sum((x-y)**2 for x, y in zip(a, b)) ** .5

for arg in sys.argv[1:]:
    name, cid = arg.split('=')
    raw = os.path.join(ROOT, 'assets', 'pixellab', name); os.makedirs(raw, exist_ok=True)
    ims = {}
    for d in DIRS:
        url = f'https://backblaze.pixellab.ai/file/pixellab-characters/{USER}/{cid}/rotations/{d}.png'
        p = os.path.join(raw, f'{d}.png')
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.0'})   # default python agent gets 403
        open(p, 'wb').write(urllib.request.urlopen(req).read())
        ims[d] = Image.open(p).convert('RGBA')
    W, H = ims['south'].size; BASE = H - 3
    # 1) feet on one baseline, centred on the feet
    for d, im in ims.items():
        a = im.getchannel('A'); x0, y0, x1, y1 = im.getbbox()
        cols = [x for x in range(im.width) for y in range(y1-4, y1) if a.getpixel((x, y)) > 0]
        fc = (min(cols) + max(cols) + 1) / 2
        c = Image.new('RGBA', (W, H)); c.alpha_composite(im, (round(W/2 - fc), BASE - y1)); ims[d] = c
    # 2) merge near-same colours across all views; drop half-transparent pixels
    cnt = Counter(p[:3] for im in ims.values() for p in im.getdata() if p[3] >= 128)
    pal = []
    for c, _ in cnt.most_common():
        if not any(dist(c, q) < 14 for q in pal): pal.append(c)
    near = {c: min(pal, key=lambda q: dist(c, q)) for c in cnt}
    for d, im in ims.items():
        px = im.load()
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                px[x, y] = near[(r, g, b)] + (255,) if a >= 128 else (0, 0, 0, 0)
        for tries in range(20):   # Dropbox briefly locks a file it has just seen written
            try: im.save(os.path.join(raw, f'{d}.png')); break
            except OSError: time.sleep(.5)
    print(name, 'cleaned', len(cnt), '->', len(pal), 'colours')
    # 3) his style
    out = os.path.join(ROOT, 'assets', 'final', name)
    subprocess.run([sys.executable, os.path.join(HERE, 'final_style.py'), raw, out], check=True)
