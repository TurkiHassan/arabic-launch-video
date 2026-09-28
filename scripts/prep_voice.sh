#!/usr/bin/env bash
# Trim leading/trailing silence, tighten the pace, and encode voice lines for the composition.
# Usage: prep_voice.sh RAW_DIR COMPOSITION_DIR [TEMPO]
#   RAW_DIR          folder with vo1..voN as .wav or .mp3 (gemini_tts.py, elevenlabs_tts.py, or downloaded by hand)
#   COMPOSITION_DIR  Hyperframes project; writes assets/voice/voN.mp3
#   TEMPO            atempo factor, default 1.15 (Gemini reads slowly; use 1.0-1.05 for ElevenLabs)
# Prints each final duration and the total, which drive the scene timing.
set -euo pipefail
raw="$1"; comp="$2"; tempo="${3:-1.15}"
mkdir -p "$comp/assets/voice"
total=0
shopt -s nullglob
files=("$raw"/vo*.wav "$raw"/vo*.mp3)
[ ${#files[@]} -gt 0 ] || { echo "no vo*.wav or vo*.mp3 in $raw" >&2; exit 1; }
for f in "${files[@]}"; do
  name=$(basename "${f%.*}")
  out="$comp/assets/voice/$name.mp3"
  tmp="$comp/assets/voice/.$name.tmp.mp3"
  ffmpeg -v error -y -i "$f" -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,atempo=$tempo" -ar 44100 -c:a libmp3lame -b:a 192k "$tmp"
  mv "$tmp" "$out"
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")
  printf '%s %.2fs\n' "$name" "$d"
  total=$(python3 -c "print($total+$d)")
done
printf 'total speech %.2fs (leave ~0.25s before and ~0.3s after each line)\n' "$total"
