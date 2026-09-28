#!/usr/bin/env python3
"""Arabic subtitles (.srt) from the voice lines and their timings.

Usage:
    python3 make_srt.py LINES.json TIMINGS.json OUT.srt [--max-chars 42] [--keep-tashkeel]

TIMINGS.json is what mix_voiceover.py writes ([{"line", "start", "duration"}, ...]).
Subtitles are for reading, so the tashkeel that steers the TTS is stripped by default
(pass --keep-tashkeel for educational content). Lines longer than --max-chars are split at
the comma or space nearest the middle, and the time is shared by character count.
Each cue is wrapped in U+202B … U+202C so players that ignore the file's direction still
lay the Arabic out right-to-left with punctuation on the correct side.
"""
import argparse
import json
import re

TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")


def split(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    mid = len(text) // 2
    cuts = [m.end() for m in re.finditer(r"[،,:؛]\s|\s", text)]
    best = min(cuts, key=lambda c: (abs(c - mid) - (6 if text[c - 2:c - 1] in "،,:؛" else 0)))
    return split(text[:best].strip(), max_chars) + split(text[best:].strip(), max_chars)


def ts(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("timings")
    ap.add_argument("out")
    ap.add_argument("--max-chars", type=int, default=42)
    ap.add_argument("--keep-tashkeel", action="store_true")
    args = ap.parse_args()

    lines = json.load(open(args.lines))
    timings = json.load(open(args.timings))
    cues = []
    for t in timings:
        text = lines[t["line"] - 1]
        if not args.keep_tashkeel:
            text = TASHKEEL.sub("", text)
        chunks = split(text, args.max_chars)
        weight = sum(len(c) for c in chunks)
        start = t["start"]
        for c in chunks:
            d = t["duration"] * len(c) / weight
            cues.append((start, start + d, c))
            start += d
    with open(args.out, "w", encoding="utf-8") as f:
        for n, (a, b, c) in enumerate(cues, 1):
            f.write(f"{n}\n{ts(a)} --> {ts(b)}\n‫{c}‬\n\n")
    print(f"wrote {args.out} ({len(cues)} cues)")


if __name__ == "__main__":
    main()
