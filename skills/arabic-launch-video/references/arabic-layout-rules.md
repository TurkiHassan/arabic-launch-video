# Arabic RTL in Hyperframes — rules that each fixed a real failure

Read `examples/pdf-extractor.html` (calm app-store ad) and `examples/qudrah-academy.html`
(showreel ad with Blender plates) before building. Reuse their structure — persistent
background, scene clips with `.inner`, voice/music/SFX tracks, bass-reactive glow, RTL
line-wipe — but write this product's own copy, colors and scenes. Their asset folders are not
in the repo (fonts, music and voice are licensed or personal); the HTML is the reference.

## Direction
- **Never `dir="rtl"` on `<html>`** — Hyperframes renders a blank video (`check` flags
  `html_dir_attribute_breaks_render`). Use `lang="ar"` on `<html>` and `direction: rtl` on each
  scene's `.inner` and any RTL block outside a scene.
- **Reveal text right-to-left**: `clipPath: "inset(0 0 0 100%)"` → `"inset(0 0 0 0%)"`, one line
  at a time, ≥ 0.55 s apart so each can be read.
- **Motion follows reading direction**: the next scene enters from the left (`x: -160`), the
  outgoing one leaves to the right (`x: 160`). Whip pans: out `x: 1100`, in from `x: -1100`.
- Words can be staggered as blocks (flex row of `<span>` per word); letters cannot — Arabic
  letters join, splitting them breaks the shaping.

## Digits and mixed text
- Follow the product's own convention. Western digits (5, 1,000) by default; if the product
  uses Arabic-Indic digits (٣٤, ١٨٧٩) use them everywhere, including rolling counters
  (`String(n).replace(/[0-9]/g, d => "٠١٢٣٤٥٦٧٨٩"[d])`).
- A string that **starts** with a digit or a Latin word: prefix U+200F (`&#x200F;`) or the
  line flips. Isolate Latin/URLs in `<span style="direction:ltr;unicode-bidi:isolate">`.
- Inside an LTR input (a number being typed), keep the box `direction: ltr`.
- Arithmetic in running Arabic text reads right-to-left: «١٦ ÷ ٤ = ٤» renders with ١٦ on the
  right. That is correct for Arabic readers; do not force it LTR.

## Type
- Use the font the product ships (`public/fonts`, `src/assets/fonts`, app bundle). Otherwise a
  good free pair: Thmanyah Serif Display / Thmanyah Sans, or Cairo / Tajawal / IBM Plex Sans
  Arabic. Every named `font-family` needs an in-file `@font-face` to a file in `assets/fonts/`.
- Display 700-900 at 120-330 px, body 400-500 at 32-46 px. Leave room above for shadda and
  hamza: a line under a very large word needs extra `margin-top`, or the marks collide.
- `letterSpacing` must not be animated (it snaps per frame and `check` errors); animate
  `scale` instead. Never add letter-spacing to Arabic at all — it breaks the joins.

## Composition hygiene (each one failed `check` or a render once)
- **No decorative "ghost" words** — they fail the WCAG contrast gate. Use shapes: glows,
  outlined sheets, grids, grain.
- **One image file per element** — the same `img src` twice is a duplicate-media warning; copy
  the logo to a second filename for the corner mark.
- **Two `fromTo` tweens on one element** → the later one gets `immediateRender: false`.
- **Glows bleeding off-canvas** → `data-layout-allow-overflow`.
- **State overlays that repeat text** (a green "correct" layer with the same number) fail
  `content_overlap`. Put only the background and the ✓ in the overlay and tween the text color.
- **Cards entering during a wipe** fail contrast if they fade in; bring them in from off-screen
  at full opacity instead.
- **Every `<audio>` needs an `id`**, or the render is silent.
- `<video>` plates (Blender renders) sit in a *non-timed* wrapper div; the `<video>` carries
  `data-start`. Animate the wrapper (scale, opacity), never the video element.

## Audio in the composition
- Voice on one track (`data-track-index="10"`), music on its own, every overlapping SFX on its
  own track index.
- Duck music with a `data-automation` volume lane: ≈ 0.2-0.25 under the voice, ≈ 0.42-0.55 in
  gaps and on the big hit, fade to 0 at the end.
- SFX quiet (0.15-0.55). Keypress per typed character, a click on a simulated tap, a soft
  impact on scene cuts, a bell on the logo. A synthesized whoosh/riser works well:
  `ffmpeg -f lavfi -i "anoisesrc=d=0.5:c=pink:a=0.6:seed=3" -af "highpass=f=350,lowpass=f=3200,afade=t=in:d=0.18:curve=exp,afade=t=out:st=0.2:d=0.3" whoosh.wav`
- Bass-reactive glow: extract bands (see `scripts/bass_js.py`) and drive a glow's scale/opacity
  from a per-frame `tl.call` loop. Subtle on text, bolder on light and shapes.

## Honesty
- No prices (they vary by storefront), no invented claims ("الأكثر استخدامًا"), no fake
  reviews. Illustrative numbers in a demo (XP, scores) carry a small «مثال توضيحي».
- Check facts against the source: when the landing page and the code disagree (e.g. what is
  free), the code wins — and tell the user about the stale copy.
