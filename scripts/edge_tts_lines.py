#!/usr/bin/env python3
"""Arabic voiceover lines with Microsoft Edge neural voices — free, no account, no key.

Usage:
    python3 edge_tts_lines.py LINES.json OUT_DIR [--voice ar-SA-HamedNeural] [--rate +0%] [--only 2 4] [--dry-run]

LINES.json is a JSON array of fully diacritized فصحى strings, one per scene.
Writes OUT_DIR/vo1.mp3 ... voN.mp3 and prints each duration.

This is the "try it right now" engine: nothing to sign up for. It reads فصحى more flatly
than Gemini Charon and has no performance control, so for a final ad prefer Gemini when the
user has (or is willing to make) a free Google AI Studio key.

Good فصحى voices: ar-SA-HamedNeural (male, default), ar-SA-ZariyahNeural (female),
ar-AE-HamdanNeural, ar-QA-MoazNeural, ar-KW-FahedNeural. Avoid ar-EG-* for فصحى ads.
Needs: pipx install edge-tts   (or: uv tool install edge-tts)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys


def duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout.strip()
    return float(out or 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("out_dir")
    ap.add_argument("--voice", default="ar-SA-HamedNeural")
    ap.add_argument("--rate", default="+0%", help="speaking rate, e.g. +8%% or -5%%")
    ap.add_argument("--only", type=int, nargs="*", help="1-based line numbers to (re)generate")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = json.load(open(args.lines))
    which = args.only or list(range(1, len(lines) + 1))
    if args.dry_run:
        for n in which:
            print(f"vo{n}: {lines[n - 1]}")
        print(f"{len(which)} line(s) with {args.voice} at rate {args.rate}")
        return

    exe = shutil.which("edge-tts")
    if not exe:
        sys.exit("edge-tts is not installed. Run: pipx install edge-tts   (or: uv tool install edge-tts)")
    os.makedirs(args.out_dir, exist_ok=True)
    for n in which:
        path = os.path.join(args.out_dir, f"vo{n}.mp3")
        subprocess.run(
            [exe, "--voice", args.voice, f"--rate={args.rate}", "--text", lines[n - 1], "--write-media", path],
            check=True, capture_output=True,
        )
        print(f"vo{n}: {duration(path):.2f}s", flush=True)


if __name__ == "__main__":
    main()
