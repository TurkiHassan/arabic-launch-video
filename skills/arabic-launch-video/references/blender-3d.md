# Optional: 3D shots from Blender

Offer this only when `doctor.sh` finds Blender (4.2+; tested on 5.2 EEVEE) and the user wants
a "showreel" feel. It adds 10-20 minutes of rendering on an Apple M1. The rest of the video is
built exactly as without it; the 3D renders arrive as `<video>` plates.

Three templates live in `blender/` (they made the Qudrah Academy ad):

| Script | Shot | Output |
|---|---|---|
| `shot_a_ascent.py` | a glowing line draws across a blueprint grid, then N tiles (one per lesson/feature) rise and wind upward into a spiral path; wireframe solids and paper chips drift | opaque 1080×1920 MP4 (full-bleed background for the hook + reveal) |
| `shot_b_badge.py` | a medal spins in like a coin, lands on a beat, six pips click into orbit | transparent 1080×1080 WebM |
| `shot_c_mark.py` | the product logo, extruded from its SVG, swings in and lands; the accent part stamps down on the next beat; a light sweeps the metal | transparent 1080×1080 WebM |

## Adapting them

1. Copy `blender/` into the output folder (`brag-output/blender/`) and edit the copies.
2. **Palette**: the constants at the top of `common.py` (sRGB hex; `lin()` converts). Put the
   product's colors there.
3. **Shot A**: `UNITS = [...]` is the tile grouping (the Qudrah curriculum: 34 lessons in 11
   units). Use the product's real count — features, steps, lessons. Timings (`2.75` = the
   music's lift) come from the storyboard.
4. **Shot C**: needs the logo as SVG split into two files next to the script,
   `mark_base.svg` (whole silhouette) and `mark_gold.svg` (the accent parts laid over it). One
   `<path>` each, `fill-rule="evenodd"`. A single-color logo → only `mark_base.svg`; delete
   the gold import and its keys.
5. Beat times inside each script are **scene-local** (`LAND = 1.09` → the plate's `data-start`
   + 1.09 lands on a strong beat).

## Render loop

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender        # or `blender` on Linux/Windows
cd brag-output/blender
# 1) test stills at 35-40 % — seconds, not minutes; look at them before a full render
$B -b --factory-startup --python shot_a_ascent.py -- still=20,75,110,150,215 scale=35 samples=16 out=test_a
# 2) full render (background it; ~1.4 s/frame at 1080×1920 on M1)
$B -b --factory-startup --python shot_a_ascent.py -- anim=1 samples=24 out=out_a
# 3) encode
ffmpeg -framerate 30 -i out_a/f_%04d.png -c:v libx264 -crf 14 -pix_fmt yuv420p ascent.mp4
ffmpeg -framerate 30 -i out_c/f_%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 20 -row-mt 1 -auto-alt-ref 0 mark.webm
```

Transparent VP9 WebM composites correctly in both Hyperframes snapshot and render.

## Pitfalls already paid for

- Blender 5.x compositor is a node group: `scene.compositing_node_group`, and the Glare node's
  type is an input socket that defaults to **Streaks** — set it to `"Bloom"` (common.py does).
- SVG import units are tiny; after scaling, `transform_apply(scale=True, properties=False)` —
  with properties on, the curve radius is multiplied too and the bevel balloons into a blob.
- Never keyframe `obj.scale.copy() * k` after an earlier key already changed `obj.scale`;
  use literal tuples.
- Metal reflects the world. With a transparent film the world is invisible, so give it a warm
  bright color (e.g. rosegold at 0.5) purely for reflections; a dark world makes gold look black.
- Emission above ~4 under AgX goes white; lower it and let Bloom carry the glow.
- Leave the top third of the hook frames dark and empty for the headline, and plan where
  text will sit in the reveal (add a scrim gradient behind it).
