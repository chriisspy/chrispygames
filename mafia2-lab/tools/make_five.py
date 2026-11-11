# The game font (Pixelify Sans) draws its 5 like an S. This makes a proper 5 in the same chunky style, as four tiny
# fonts (one per weight the page uses) holding ONLY the digit 5. The page lists them under the same family name with
# unicode-range U+35, so every 5 on the page and on the canvas uses this one. Sizes were measured off Pixelify Sans.
# usage (from the game folder): python -I tools/make_five.py
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
L, B, C = 60, -12, 91                       # left edge, bottom, corner step
W = {400: dict(R=525, T=631, tv=101, th=101, adv=586), 500: dict(R=531, T=633, tv=109, th=112, adv=592),
     600: dict(R=536, T=636, tv=118, th=124, adv=597), 700: dict(R=542, T=638, tv=127, th=137, adv=603)}
def rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath()
for w, p in W.items():
    R, T, tv, th = p['R'], p['T'], p['tv'], p['th']
    M = B + th + round((T - B - 3 * th) * .56) + th      # top of the middle bar
    pen = TTGlyphPen(None)
    rect(pen, L, T - th, R, T)                  # flat top bar, square corners (this is what makes it a 5)
    rect(pen, L, M - th, L + tv, T)             # left stem down to the middle
    rect(pen, L, M - th, R - C, M)              # middle bar
    rect(pen, R - tv, B + C, R, M - C)          # right side of the bowl
    rect(pen, L + C, B, R - C, B + th)          # bottom bar
    rect(pen, L, B + C, L + tv, B + C + th)     # the little tail bottom-left
    g = pen.glyph(); empty = TTGlyphPen(None).glyph()
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(['.notdef', 'five']); fb.setupCharacterMap({0x35: 'five'})
    fb.setupGlyf({'.notdef': empty, 'five': g})
    fb.setupHorizontalMetrics({'.notdef': (p['adv'], 0), 'five': (p['adv'], L)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({'familyName': 'M2 Five', 'styleName': 'Regular'})
    fb.setupOS2(usWeightClass=w, sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupPost(); fb.save(f'assets/fonts/five-{w}.ttf'); print(w, 'ok')
