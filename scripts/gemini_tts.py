#!/usr/bin/env python3
"""Generate Modern Standard Arabic (فصحى) voiceover lines with Gemini TTS.

Usage:
    python gemini_tts.py LINES.json OUT_DIR [--model M] [--voice V] [--only 3 5] [--dry-run]

LINES.json is a JSON array of strings, one per scene, fully diacritized (تشكيل كامل).
Writes OUT_DIR/vo1.wav ... voN.wav and prints each duration.

Why it looks the way it does (learned the hard way):
- Send ONLY the diacritized line. Any style prefix ("Say in formal Arabic: ...") gets read
  aloud, and this model family rejects `systemInstruction`. Full tashkeel is what keeps the
  read in فصحى instead of drifting to a dialect.
- Free tier allows ~10 requests per day per TTS model (plus a per-minute limit). One request
  per line, no test calls. A per-minute 429 is retried automatically; a per-day 429 stops.
- Responses come back either as a RIFF/WAV blob or raw L16 PCM (rate in the mime type).
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import wave

KEY_FILES = [os.path.expanduser(p) for p in ("~/.config/arabic-video/gemini.key", "~/.config/brag/gemini.key")]
KEY_PATTERN = r"AIza[0-9A-Za-z_-]{30,}|AQ\.[0-9A-Za-z_-]{20,}"


def load_key() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    key_file = next((p for p in KEY_FILES if os.path.exists(p)), None)
    if not key_file:
        sys.exit(f"No key. Run: bash key_setup.sh gemini   (it creates {KEY_FILES[0]} for you) — then paste the Google AI Studio key into it.")
    raw = open(key_file).read()
    match = re.search(KEY_PATTERN, raw)
    return match.group(0) if match else raw.strip()


def synthesize(key: str, model: str, voice: str, text: str) -> tuple[bytes, str]:
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.load(resp)
            part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
            return base64.b64decode(part["data"]), part.get("mimeType", "")
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")
            if err.code == 429 and "PerDay" not in detail and attempt < 7:
                wait = int(float((re.search(r'"retryDelay":\s*"([\d.]+)s"', detail) or [0, 15])[1])) + 2
                print(f"  per-minute limit, retrying in {wait}s", flush=True)
                time.sleep(wait)
                continue
            if err.code == 429:
                sys.exit(f"Daily free quota used up for {model}. Try another TTS model (they have separate quotas) or tomorrow.\n{detail[:600]}")
            sys.exit(f"HTTP {err.code}: {detail[:800]}")
    sys.exit("Gave up after repeated rate limits.")


def write_wav(path: str, audio: bytes, mime: str) -> float:
    if audio[:4] == b"RIFF":
        open(path, "wb").write(audio)
    else:
        rate = int(re.search(r"rate=(\d+)", mime).group(1)) if "rate=" in mime else 24000
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(audio)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("out_dir")
    ap.add_argument("--model", default="gemini-3.1-flash-tts-preview")
    ap.add_argument("--voice", default="Charon")
    ap.add_argument("--only", type=int, nargs="*", help="1-based line numbers to (re)generate")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = json.load(open(args.lines))
    which = args.only or list(range(1, len(lines) + 1))
    if args.dry_run:
        for n in which:
            print(f"vo{n}: {lines[n - 1]}")
        print(f"{len(which)} request(s) to {args.model} with voice {args.voice}")
        return

    key = load_key()
    os.makedirs(args.out_dir, exist_ok=True)
    for n in which:
        audio, mime = synthesize(key, args.model, args.voice, lines[n - 1])
        seconds = write_wav(os.path.join(args.out_dir, f"vo{n}.wav"), audio, mime)
        print(f"vo{n}: {seconds:.2f}s", flush=True)
        if seconds > 2.5 * max(1.0, len(lines[n - 1]) / 12):
            print(f"  warning: vo{n} is much longer than its text; the model may have read extra words")
        time.sleep(6)  # stay under the per-minute limit


if __name__ == "__main__":
    main()
