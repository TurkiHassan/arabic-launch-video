#!/usr/bin/env python3
"""Generate Arabic voiceover lines with ElevenLabs (default voice: Haytham).

Usage:
    python elevenlabs_tts.py LINES.json OUT_DIR [--voice-id ID] [--model M] [--only 3 5] [--dry-run]

LINES.json is a JSON array of fully diacritized فصحى strings, one per scene.
Writes OUT_DIR/vo1.mp3 ... voN.mp3 and prints each duration.

Notes:
- Haytham is a *library* voice. Free ElevenLabs accounts cannot use library voices over the
  API (HTTP 402 paid_plan_required); Starter or above can. On a free plan, the user can still
  generate the lines on elevenlabs.io with the same voice, save them as vo1.mp3 ... voN.mp3,
  and hand the folder to prep_voice.sh.
- Library voices are labelled by the speaker's native accent (the Haytham voices say
  "egyptian"). Full tashkeel plus language_code "ar" keeps the read as close to فصحى as the
  voice allows; have the user listen before rendering.
- Key: ~/.config/arabic-video/elevenlabs.key (chmod 600, made by key_setup.sh) or ELEVENLABS_API_KEY.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

HAYTHAM_VOICES = {
    "IES4nrmZdUBHByLBde0P": "Haytham - Energetic, Warm and Cheerful (most used)",
    "UR972wNGq3zluze0LoIp": "Haytham - Dramatic, Warm and Friendly",
    "wxweiHvoC2r2jFM7mS8b": "Haytham - Dramatic and Narrative",
}
DEFAULT_VOICE = "IES4nrmZdUBHByLBde0P"
KEY_FILES = [os.path.expanduser(p) for p in ("~/.config/arabic-video/elevenlabs.key", "~/.config/brag/elevenlabs.key")]


def load_key() -> str:
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"].strip()
    key_file = next((p for p in KEY_FILES if os.path.exists(p)), None)
    if not key_file:
        sys.exit(f"No key. Run: bash key_setup.sh elevenlabs   (it creates {KEY_FILES[0]} for you) — then paste the ElevenLabs key into it.")
    raw = open(key_file).read()
    match = re.search(r"sk_[A-Za-z0-9]{48}", raw)
    return match.group(0) if match else raw.strip()


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
    ap.add_argument("--voice-id", default=DEFAULT_VOICE)
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--only", type=int, nargs="*", help="1-based line numbers to (re)generate")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = json.load(open(args.lines))
    which = args.only or list(range(1, len(lines) + 1))
    chars = sum(len(lines[n - 1]) for n in which)
    if args.dry_run:
        for n in which:
            print(f"vo{n}: {lines[n - 1]}")
        print(f"voice {args.voice_id} ({HAYTHAM_VOICES.get(args.voice_id, 'custom')}), model {args.model}, ~{chars} characters")
        return

    key = load_key()
    os.makedirs(args.out_dir, exist_ok=True)
    for n in which:
        body = {
            "text": lines[n - 1],
            "model_id": args.model,
            "language_code": "ar",
            "voice_settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.1, "use_speaker_boost": True},
        }
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{args.voice_id}?output_format=mp3_44100_128",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "xi-api-key": key},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                audio = resp.read()
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")
            if err.code == 402:
                sys.exit(
                    "ElevenLabs refused the library voice: this account is on the free plan (paid_plan_required).\n"
                    "Options: upgrade to Starter, generate the lines on elevenlabs.io with the same voice and save them "
                    "as vo1.mp3..voN.mp3, or use gemini_tts.py instead."
                )
            sys.exit(f"HTTP {err.code}: {detail[:600]}")
        path = os.path.join(args.out_dir, f"vo{n}.mp3")
        open(path, "wb").write(audio)
        print(f"vo{n}: {duration(path):.2f}s", flush=True)


if __name__ == "__main__":
    main()
