#!/usr/bin/env bash
# Pick the poster, bake it as frame 0, and normalize loudness for social platforms.
# Usage: finalize.sh OUTPUT_DIR POSTER_SECONDS
#   OUTPUT_DIR      folder holding brag.mp4 (the raw render)
#   POSTER_SECONDS  a settled moment (text fully in, not mid-transition), e.g. the "done" beat
# Writes OUTPUT_DIR/brag.jpg and replaces brag.mp4 (H.264 + AAC 48k, -14 LUFS, faststart).
set -euo pipefail
dir="$1"; at="$2"
cd "$dir"
ffmpeg -v error -y -ss "$at" -i brag.mp4 -frames:v 1 -q:v 2 brag.jpg
ffmpeg -v error -y -i brag.mp4 -i brag.jpg \
  -filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart brag.final.mp4
mv brag.final.mp4 brag.mp4
find . -maxdepth 1 -name 'work-*' -type d -exec rm -rf {} +
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact brag.mp4
ffmpeg -i brag.mp4 -af ebur128 -f null - 2>&1 | grep -A1 "Integrated loudness" | tail -1
