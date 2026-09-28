#!/usr/bin/env python3
"""Shorten long pauses inside voice lines without touching the words.

Usage:
    python3 tighten_pauses.py VOICE_DIR [--keep 0.2] [--keep-last 0.3]

Rewrites VOICE_DIR/vo*.mp3 in place (the originals go to VOICE_DIR/untightened/).
TTS voices often breathe 0.4-0.7s at every comma and colon; in a 20-30s ad that adds up to
several seconds. Every silence longer than --keep is cut down to --keep, split evenly around
the cut so the words keep their natural attack and release. --keep-last applies to the last
line (usually "Name. CTA."), where a slightly longer beat after the name reads better.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout.strip()
    return float(out or 0)


def tighten(src: str, dst: str, keep: float) -> float:
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", src, "-af", "silencedetect=noise=-38dB:d=0.12", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    total = probe_duration(src)
    segments, cursor = [], 0.0
    for s, e in zip(starts, ends):
        if e - s > keep:
            segments.append((cursor, s + keep / 2))
            cursor = e - keep / 2
    segments.append((cursor, total))
    parts = "".join(
        f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,"
        f"afade=t=out:st={max(0, b - a - 0.012):.4f}:d=0.012[s{i}];"
        for i, (a, b) in enumerate(segments)
    )
    graph = parts + "".join(f"[s{i}]" for i in range(len(segments))) + f"concat=n={len(segments)}:v=0:a=1[o]"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", graph, "-map", "[o]",
         "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "192k", dst],
        check=True,
    )
    return probe_duration(dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("voice_dir")
    ap.add_argument("--keep", type=float, default=0.2)
    ap.add_argument("--keep-last", type=float, default=0.3)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.voice_dir, "vo*.mp3")), key=lambda p: int(re.search(r"vo(\d+)", p).group(1)))
    if not files:
        raise SystemExit(f"no vo*.mp3 in {args.voice_dir}")
    backup = os.path.join(args.voice_dir, "untightened")
    os.makedirs(backup, exist_ok=True)
    total = 0.0
    for i, f in enumerate(files):
        original = os.path.join(backup, os.path.basename(f))
        if not os.path.exists(original):
            shutil.copy2(f, original)
        keep = args.keep_last if i == len(files) - 1 else args.keep
        d = tighten(original, f, keep)
        total += d
        print(f"{os.path.basename(f)} {d:.2f}s")
    print(f"total speech {total:.2f}s")


if __name__ == "__main__":
    main()
