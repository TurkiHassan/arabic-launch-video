#!/usr/bin/env python3
"""Lay Arabic voice lines onto a finished video (or onto nothing, for an audio-only file).

Usage:
    python3 mix_voiceover.py --voice-dir DIR --out OUT.mp4 [--video IN.mp4]
        [--starts 0.4,3.6,8.1 | --lead 0.4 --gap 0.35]
        [--music TRACK.mp3 --music-volume 0.3] [--original duck|keep|mute]

- Lines are DIR/vo1.mp3 ... voN.mp3 (from gemini_tts.py / edge_tts_lines.py / elevenlabs_tts.py
  after prep_voice.sh, or recorded by the user and named that way).
- --starts gives each line's start in seconds (one per line). Without it the lines run back to
  back from --lead with --gap between them.
- The video's own sound and the optional music are ducked under the voice with a sidechain
  compressor (they dip while someone speaks and come back in the gaps), then the whole mix is
  normalized to -14 LUFS, the level social platforms expect.
- With --video the picture is copied untouched. Without it the output is audio (use .m4a or .wav).
- Writes OUT.timings.json next to the output: [{"line": n, "start": s, "duration": d}, ...],
  which make_srt.py turns into subtitles.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys


def probe(path: str, entries: str) -> str:
    return subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--video")
    ap.add_argument("--starts")
    ap.add_argument("--lead", type=float, default=0.4)
    ap.add_argument("--gap", type=float, default=0.35)
    ap.add_argument("--music")
    ap.add_argument("--music-volume", type=float, default=0.3)
    ap.add_argument("--original", choices=["duck", "keep", "mute"], default="duck")
    args = ap.parse_args()

    lines = sorted(glob.glob(os.path.join(args.voice_dir, "vo*.*")), key=lambda p: int(re.search(r"vo(\d+)", os.path.basename(p)).group(1)))
    lines = [p for p in lines if os.path.splitext(p)[1].lower() in (".mp3", ".wav", ".m4a")]
    if not lines:
        sys.exit(f"no vo1.mp3 ... in {args.voice_dir}")
    durs = [float(probe(p, "format=duration") or 0) for p in lines]

    if args.starts:
        starts = [float(x) for x in args.starts.split(",")]
        if len(starts) != len(lines):
            sys.exit(f"--starts has {len(starts)} values but there are {len(lines)} lines")
    else:
        starts, t = [], args.lead
        for d in durs:
            starts.append(round(t, 3))
            t += d + args.gap

    voice_end = max(s + d for s, d in zip(starts, durs))
    has_video_audio = False
    if args.video:
        total = float(probe(args.video, "format=duration"))
        has_video_audio = bool(probe(args.video, "stream=codec_type").count("audio"))
        if voice_end > total + 0.05:
            print(f"warning: the voice ends at {voice_end:.2f}s but the video is {total:.2f}s — the last words will be cut. "
                  f"Tighten pauses, trim a line, or pass earlier --starts.", file=sys.stderr)
    else:
        total = voice_end + 1.0

    cmd = ["ffmpeg", "-v", "error", "-y"]
    idx = 0
    if args.video:
        cmd += ["-i", args.video]; vid_i = idx; idx += 1
    voice_i = []
    for p in lines:
        cmd += ["-i", p]; voice_i.append(idx); idx += 1
    if args.music:
        cmd += ["-stream_loop", "-1", "-i", args.music]; music_i = idx; idx += 1

    g = []
    for k, (i, s) in enumerate(zip(voice_i, starts)):
        ms = int(round(s * 1000))
        g.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
    g.append("".join(f"[v{k}]" for k in range(len(voice_i))) + f"amix=inputs={len(voice_i)}:normalize=0,apad,atrim=0:{total:.3f}[vo]")

    bed = []
    if has_video_audio and args.original != "mute":
        g.append(f"[{vid_i}:a]aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{total:.3f}[orig]")
        bed.append("[orig]")
    if args.music:
        fade = max(0.0, total - 1.5)
        g.append(f"[{music_i}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{total:.3f},"
                 f"volume={args.music_volume},afade=t=in:d=0.4,afade=t=out:st={fade:.3f}:d=1.5[mus]")
        bed.append("[mus]")

    if bed:
        g.append("".join(bed) + (f"amix=inputs={len(bed)}:normalize=0[bed]" if len(bed) > 1 else "anull[bed]"))
        if args.original == "keep" and not args.music:
            g.append("[bed][vo]amix=inputs=2:normalize=0[mix]")
        else:
            g.append("[vo]asplit=2[vo_a][vo_sc]")
            g.append("[bed][vo_sc]sidechaincompress=threshold=0.02:ratio=10:attack=25:release=400:makeup=1[duck]")
            g.append("[duck][vo_a]amix=inputs=2:normalize=0[mix]")
    else:
        g.append("[vo]anull[mix]")
    g.append("[mix]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

    cmd += ["-filter_complex", ";".join(g)]
    if args.video:
        cmd += ["-map", f"{vid_i}:v:0", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-t", f"{total:.3f}", "-movflags", "+faststart", args.out]
    else:
        cmd += ["-map", "[aout]", "-t", f"{total:.3f}", args.out]
    subprocess.run(cmd, check=True)

    timings = [{"line": n + 1, "start": s, "duration": round(d, 3)} for n, (s, d) in enumerate(zip(starts, durs))]
    json.dump(timings, open(os.path.splitext(args.out)[0] + ".timings.json", "w"), indent=2)
    for t in timings:
        print(f"vo{t['line']}: {t['start']:.2f}s → {t['start'] + t['duration']:.2f}s")
    print(f"wrote {args.out} ({total:.2f}s)")


if __name__ == "__main__":
    main()
