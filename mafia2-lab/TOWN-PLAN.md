# MAFIA 2 town rebuild: the plan (10 Nov 2026)

Goal: the same HD look as now (one even pixel grid, 560 x 750 town, drawn at a whole-number zoom),
but built from layers so cabins can change theme and people can walk under the lights.

## Layers (back to front)
1. **Base**: grass, trees, bushes, ponds, the stage and the stone paths. No cabins, no posts, no lamps,
   no lights baked in. Two images: `town-base-night` and `town-base-day`, same layout pixel-for-pixel.
2. **Cabins**: one image per cabin theme, all cut to the same template (same size, door, steps and window
   spots), so any theme fits any of the 10 spots. Day + night version of each theme.
3. **People, posts and lamp posts**, sorted by how far down the screen their feet are,
   so you walk in front of a post or behind it correctly.
4. **Overhead strings of bulbs**: always drawn on top of people (they hang above heads).
5. **Light**: lamp glows, bulb glows, window glows (red in the kill scene, out when a light dies), rain.

## What actually works (10 Nov, after testing)
- Nano Banana 2.1 masked edits of the whole town FAILED: it darkened everything, left dark rectangles
  where cabins were, moved paths (and "auto" aspect squashed it to a square). Don't repaint the town with AI.
- Instead, exact pixels: `tools/build_town_base.py` takes the cabins out of `town2-1x.png` (cut-outs
  from Higgsfield's background remover, used ONLY as the mask, pixels stay original; one shared cabin
  outline from all 10 cleans the edges) and recolours the paths grey (kerb and every stone kept).
  Output: `assets/town3/town-base-night-1x.png`, cabins in `assets/town3/cabins-cut/cabin0-9.png`
  (frame = door x-58 .. x+58, door top-90 .. top+64).
- `tools/fix_cabin_cuts.py` (run BEFORE build_town_base): the remover trimmed 1-2 px of dark outline off
  some roofs and kept grass blobs beside walls/chimneys; it walks the outline back in, drops grass whose
  exact colour never appears inside that cabin, and cuts a path kerb off cabin 5's roof peak.
  First cut kept in `cabins-cut-v1`. Check: base + cabins = original everywhere except the path (0 px).
- Stone tint (his call 10 Nov): grey, but up to 50% of the old orange kept where the old stones were lit
  by the middle lights (`TINT` in build_town_base.py); outer path ends stay grey.
- Cabin art is AI-painted, so cabins differ slightly (cabin 9's ridge is 8 px taller). Themes must be
  drawn to the template; base holes are per cabin.
- Posts / lamps / strings (DONE 10 Nov): Chris drew them bigger than the grid (assets/town3/props-src:
  top + bottom posts with strings, side post with bulbs, bare post, lamp). `tools/build_props.py` puts each
  on the 1x grid exactly over the old one (sizes/spots measured by `tools/fit_props.py`; right side = mirror,
  column c <-> 560-c; upper lamps are smaller than lower ones, like the old art). Output `assets/town3/props/`
  (one png per post/lamp/chain + strings.png + props.json). Old posts are painted out using HIS floor-only
  picture `assets/town3/pass1-a.png` (lines up stone for stone; colour-matched, snapped to the floor palette)
  -> `town-noprops-1x.png`, which build_town_base.py now starts from. Do NOT use my own fill: he saw the
  smudges and said to use the floor picture. Run order: fix_cabin_cuts, build_props, build_town_base.
- In index.html `TOWN.occ` is now the prop list (drawProp, sorted with people by foot y; strings last = overhead).

## How each layer is made (original plan)
- **Base night**: Nano Banana 2.1 masked edit of the current town (`town2-1x.png` at 4x).
  Pass 1 mask = cabins (with steps) + posts + lamps + strings → painted out, rest untouched.
  Pass 2 mask = only the paths/plaza → repainted in grey stone (close to now, not identical),
  keeping the raised stone kerb edge he loves. No baked lamp light pools (the code draws the glow).
- **Base day**: the finished night base relit as daytime, then checked to line up pixel-for-pixel.
- **Every image** goes through `tools/clean_bg.py` so its pixels land on the exact 560 x 750 grid.
- **Posts, lamps, strings**: cut from the current town art (exact pixels, same style).
  Option: Chris separates them in Photoshop (he offered). Posts are split one per file so each sorts by its feet.
- **Cabins**: default themes cut from the current 10 cabins; extra themes (dark, Christmas, ...) made by
  Nano Banana from the template cabin on a flat colour, then snapped to the template.

## Code (index.html)
- `CABIN_THEMES` catalogue: id, name, rarity, day/night images. Each player has `cabinTheme`;
  unlocked from the Mafia case (wired to the real case later).
- Cabins become depth-sorted sprites (people can walk behind a cabin's roof).
- Windows, door and feet positions come from the template, so lights, the kill scene's red windows,
  lights going out and the door opening keep working for every theme.
- `TOWN.occ` patches are replaced by the separate post / lamp sprites; strings drawn after people.
- Day/night: swap the base + cabin images; lamps and windows only glow at night.

## Cabin interior (done)
- His cleaned pieces are in `assets/room-objects` (identical to `Documents/chrispy games/cabin assets`).
- Every piece with a floor footprint gets the soft shadow; the rug and chair backing don't need one.
- Lamp, fire and room ambient light unchanged.
- Chair (10 Nov, his new cut): full chair incl. the top rail, 22 x 31 at (147,163); `chair-backing.png` uses the
  same frame and is drawn over you when you sit. He cuts on an 8x copy; shrink by 8, colours from room-1x.png.
  Old 26 x 26 pair kept in `assets/room-objects/_old-chair`.

## Checks before showing anything
- Overlay new vs old: trees/bushes/ponds/stage unmoved; paths reach each cabin's steps.
- Pixel grid even everywhere (no blurry or half pixels), colours match the current style.
- In the demo: walk under the strings (bulbs over heads), behind a post, behind a cabin; day + night;
  kill scene windows; lamps going out.
