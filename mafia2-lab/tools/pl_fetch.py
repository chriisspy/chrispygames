# Download a PixelLab character's skeleton animations (walk-sk, sit, pickup-sk, water-sk) into
# assets/poses-src/<name>/ as <anim>_<dir>_<i>.png, then tools/pl_poses.py builds the game poses.
# The PixelLab characters are imports of HIS finished sprites (assets/final), so frames are already his style.
# usage (from mafia2-lab/): python -I tools/pl_fetch.py name=<pixellab id> [name=id ...]
import sys, os, io, zipfile, urllib.request
IDS = {  # his finished sprites imported into PixelLab on 10 Nov 2026 ("M2F <name>")
 'batman': '3aa1202b-a61e-43ca-a1aa-490752395559', 'brownhair': '432d35de-7fe9-4514-bc45-1669d101ebd3',
 'curly': '6fbcc7d1-14b7-495a-8056-3d328aba2933', 'detective': '8add977f-188c-41ab-9bcc-ad6774f9d693',
 'doctor': 'a97f5c29-3e33-4eb9-a25f-ad7a70a50eb0', 'farmer': '5437fea4-3c44-4c4e-af9c-42c7bf509783',
 'jester': '2f0fda82-86d5-4e5f-a788-a9a83386996e', 'mafia': '3f5c6737-0136-45a3-97cc-ce851139e95f',
 'pinkbob': 'ff98aad3-04a5-4cbd-919e-d2116d5420fa', 'ponytail': '17e595d8-88e0-48e8-9727-c52d1b37e5ad',
 'raincoat': 'decffd96-b0c4-4c5c-aed2-f9d5c6bc01b8', 'redcap': 'bbcdbe8a-26a1-4d8f-bc8c-72a745eb9739',
 'beanie': '4e5f235d-3211-4040-ac2f-7ff7e3aa4bf4',
 'alfa': 'e0f65bef-bf43-4a59-85f8-fd3c8b457118', 'golf': '37362567-8e45-46bf-ac72-e74b50dab407',
 'ferrari': '4cd5c42a-d2bc-416c-80bb-2eec68dfc8cd',
 'bape': '828246e2-72e7-4ff3-8e60-c65efd6c03f8'}   # added 11 Nov (Alfa Marcus, Golf Chrispy)
MAP = {'walk-sk': 'walk', 'sit': 'sit', 'sit2': 'sit', 'pickup-sk': 'pickup', 'water-sk': 'water'}   # sit2 = the reworded sit (no chair drawn); it wins over sit
for name in sys.argv[1:]:
    req = urllib.request.Request(f'https://api.pixellab.ai/mcp/characters/{IDS[name]}/download', headers={'User-Agent': 'curl/8.0'})
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req).read()))
    out = f'assets/poses-src/{name}/'; os.makedirs(out, exist_ok=True); n = 0
    for f in sorted(z.namelist(), key=lambda f: '/sit2/' in f):
        p = f.split('/')
        if len(p) == 5 and p[1] == 'animations' and p[2] in MAP:
            open(f'{out}{MAP[p[2]]}_{p[3]}_{int(p[4][6:9])}.png', 'wb').write(z.read(f)); n += 1
    print(name, n, 'frames')
