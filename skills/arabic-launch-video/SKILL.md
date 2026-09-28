---
name: arabic-launch-video
description: Make a short Arabic launch/promo video (إعلان) with Arabic RTL motion graphics and a فصحى voiceover, rendered with Hyperframes on top of the /brag workflow — from a project folder, a website link, screenshots, or just a description. Starts by interviewing the user about the goal, platform, voice and materials, and lists what is needed (files, links, keys) before building. Use whenever someone asks for an Arabic ad, promo, launch video, App Store preview, reel or social video — "سوّ إعلان", "فيديو إعلاني", "إعلان بالعربي", "إعلان بتعليق صوتي", "make an Arabic launch video" — even if they do not name Hyperframes, brag, or this skill.
---

# Arabic launch video

A 15-35 second Arabic video: the product's real UI and words, Arabic RTL typography in its
own palette, a فصحى voiceover, a ducked music bed, motion-matched sound effects, and — when
Blender is available and wanted — 3D shots. The user is often **not technical**: speak plain
Arabic, explain each step in one line, never show a command they must run unless there is no
other way, and never ask for an API key in the chat.

`S` below means `<this skill's base directory>/../../scripts` (the plugin's shared scripts).

## Phase 0 — Check the machine (silent unless something is missing)

```bash
bash "$S/doctor.sh"
```

- `❌` rows: explain in one sentence each and fix them with the user's OK (`brew install …`
  on macOS; for the brag plugin ask before running `claude plugin marketplace add
  latent-spaces/brag && claude plugin install brag@brag`; for Hyperframes skills run
  `npx -y hyperframes@latest skills update hyperframes-core hyperframes-animation
  hyperframes-creative hyperframes-keyframes hyperframes-cli`).
- No voice engine yet is fine at this point — the interview decides which one.

## Phase 1 — Interview, then a requirements checklist (mandatory)

Read `references/intake.md` and run it: goal → voice → materials, with `AskUserQuestion`,
skipping what the request or the project already answers. End with the checklist table and
wait for the user's go. If they only want narration on a video they already have, switch to
the `arabic-voiceover` skill.

Set up missing pieces now, not mid-render:
- **Voice key** (Gemini/ElevenLabs): `bash "$S/key_setup.sh" gemini` opens a private file.
  Tell the user: open the link it prints (for Gemini: aistudio.google.com/apikey → Create
  API key → copy), paste into the file that just opened, press ⌘S (Ctrl+S). Wait in the
  background with `until grep -qE 'AIza|AQ\.|sk_' ~/.config/arabic-video/gemini.key; do sleep 2; done`,
  then strip the file down to the bare key (people paste extra text).
- **Files**: ask them to drag files into the chat, or drop them in `assets-in/`.
- **Links**: fetch them yourself.

## Phase 2 — Gather the material

Work in `brag-output/` at the project root (or `brag-output-YYYY-MM-DD-HHmmss/` if one exists;
add `brag-output*/` to `.gitignore` in a git repo).

- **Project folder**: follow brag's `references/step-1-inspect.md` (find it:
  `ls ~/.claude/plugins/cache/brag/brag/*/skills/brag`). Collect real screens (App Store
  screenshots, `fastlane/`, `docs/`), the Arabic copy the app really uses (localization, TSX/Swift
  strings, store metadata), brand colors (CSS vars, Tailwind, `.colorset`), the Arabic font it
  ships, the icon/logo, and facts from code (counts, what is free).
- **Website link**: fetch the page for headline, copy, colors; screenshot key sections with the
  browser tool when available.
- **Screenshots/description only**: design the key screens in HTML from them; keep the user's words.

## Phase 3 — Narration first

Read `references/arabic-voice.md`. Write one fully diacritized فصحى line per scene into
`brag-output/voice-lines.json`, show the lines to the user, then write `brag-plan.md` and
`composition-brief.md` (brag's step 2 and 3 shapes) with narration and timings.

Scene shape that worked twice (adapt it):

| # | Scene | Line pattern |
|---|---|---|
| 1 | Hook: the pain or the promise, big headline on the product's own material | «عِنْدَكَ …؟» / the product's tagline |
| 2 | Reveal: name + subtitle, a real screenshot or key numbers | «[الاسم] …» |
| 3 | The core flow recreated: input → a simulated tap → the result appearing | «اِخْتَرْ… وَ…» |
| 4 | Proof / value: explanation, plans, rewards, cards arriving on beats | one concrete benefit |
| 5 | Outro: logo, name, tagline, 2-3 pills, CTA | «[الاسم]. [الدعوة].» |

## Phase 4 — Generate and pace the voice

```bash
python3 "$S/gemini_tts.py" brag-output/voice-lines.json <scratch>/voice-raw --dry-run   # free check
python3 "$S/gemini_tts.py" brag-output/voice-lines.json <scratch>/voice-raw            # one request per line
#   or: python3 "$S/edge_tts_lines.py" …   (no key)   ·   python3 "$S/elevenlabs_tts.py" …
bash "$S/prep_voice.sh" <scratch>/voice-raw brag-output/composition 1.2    # 1.0 for edge-tts / ElevenLabs / own voice
python3 "$S/tighten_pauses.py" brag-output/composition/assets/voice
```

Tell the user you cannot hear audio; ask them to listen to the lines now (open the folder
for them) and confirm pronunciation. Redo single lines with `--only N`.

## Phase 5 — Time everything to the voice and the beat

1. Pick a bundled track from brag (`assets/music/`); read its cue preset in `assets/music/cues/`.
   A track with a quiet build then a lift is great: trim it with `ffmpeg -ss <offset>` so the
   lift lands on the reveal cut.
2. Lay the lines end to end (≈ 0.2 s lead-in, ≈ 0.3 s gap). Snap each scene cut to the nearest
   beat that still contains its line (a voice may start ~0.1 s before a cut — a J-cut is fine).
3. Put simulated taps, "done" moments and sequential cards on beats (cards every other beat,
   then hold). Mark them `// beat-locked` / `// beat-grid` in the code.
4. Keep the agreed length. If the voice runs long: tighten pauses, trim words, tempo ≤ 1.2.
   Never flash text to make it fit.

## Phase 6 — Build the composition

Read the Hyperframes skills (`hyperframes-core`, `-animation`, `-creative`, `-keyframes`,
`-cli` — `ls ~/.claude/skills | grep hyperframes`; they are plain files, read their SKILL.md),
brag's `references/step-3-compose.md` and `references/audio.md`, then
`references/arabic-layout-rules.md` and both examples in `references/examples/`.

Copy music, chosen SFX (brag `assets/sfx/`) and fonts into `composition/assets/`. Build the
bass-reactive glow with Hyperframes' `extract-audio-data.py` + `"$S/bass_js.py"`.

Optional 3D: `references/blender-3d.md`.

## Phase 7 — Check, look, render, deliver

```bash
cd brag-output/composition
npx -y hyperframes@latest check                     # must pass: 0 errors, contrast all green
npx -y hyperframes@latest snapshot --at <one settled moment per scene> --no-end
npx -y hyperframes@latest render --output ../brag.mp4
bash "$S/finalize.sh" .. <poster seconds>           # poster as frame 0, -14 LUFS
```

- Read `snapshots/contact-sheet*.jpg`; fix overlap, clipping, colliding diacritics, wrong RTL
  order before rendering. Then look at a few mid-transition frames of the render itself.
  Delete `snapshots/` afterwards.
- `nested_structure_needs_subcomposition` warnings are fine for a single-file composition.
- Write `share-copy.txt` (1-3 Arabic sentences in the product's words). Offer Arabic subtitles:
  write `[{"line":1,"start":…,"duration":…},…]` from the composition's voice starts and run
  `python3 "$S/make_srt.py" brag-output/voice-lines.json timings.json brag-output/brag.srt`.
- Send `brag.mp4` with SendUserFile (if available). Tell the user the scenes with timings, the
  voice/model, anything stated as illustrative, and offer: horizontal/square cut, another voice,
  re-generating one line, subtitles.
