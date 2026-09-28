#!/usr/bin/env python3
"""Turn Hyperframes' extracted audio bands into audio-bass.js for the bass-reactive glow.

Usage:
    uv run --with numpy python ~/.claude/skills/hyperframes-creative/scripts/extract-audio-data.py \
        assets/music/bed.wav --fps 30 --bands 4 -o /tmp/bands.json
    python3 bass_js.py /tmp/bands.json 26.2 > composition/audio-bass.js

Writes window.AUDIO_BASS = [band0 per frame], padded or cut to exactly the video length, so
the per-frame tl.call loop never runs past the root data-duration.
"""
import json
import sys

data = json.load(open(sys.argv[1]))
seconds = float(sys.argv[2])
fps = data.get("fps", 30)
n = int(round(seconds * fps))
bass = [round(f["bands"][0], 3) for f in data["frames"][:n]]
bass += [0] * (n - len(bass))
print("window.AUDIO_BASS=" + json.dumps(bass) + ";")
