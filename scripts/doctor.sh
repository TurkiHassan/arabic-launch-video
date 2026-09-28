#!/usr/bin/env bash
# Check everything the workflow needs and say, in plain words, what is missing.
# Usage: doctor.sh            (prints one line per requirement and an install hint)
# Exit code 0 = ready for a full video, 1 = something required is missing.
set -uo pipefail
missing=0
ok()   { printf '  ✅ %s\n' "$1"; }
warn() { printf '  ⚪ %s — %s\n' "$1" "$2"; }
bad()  { printf '  ❌ %s — %s\n' "$1" "$2"; missing=1; }
mac=0; [ "$(uname)" = "Darwin" ] && mac=1
hint() { if [ $mac = 1 ]; then echo "brew install $1"; else echo "$2"; fi; }

echo "Required"
if command -v node >/dev/null 2>&1; then
  major=$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)
  if [ "$major" -ge 20 ]; then ok "Node.js $(node -v)"; else bad "Node.js $(node -v)" "needs v20+: $(hint node 'https://nodejs.org')"; fi
else bad "Node.js" "$(hint node 'install from https://nodejs.org')"; fi
command -v ffmpeg >/dev/null 2>&1 && ok "ffmpeg" || bad "ffmpeg" "$(hint ffmpeg 'winget install Gyan.FFmpeg')"
command -v python3 >/dev/null 2>&1 && ok "Python $(python3 -V 2>&1 | cut -d' ' -f2)" || bad "Python 3" "$(hint python 'https://www.python.org/downloads/')"
brag=$(ls -d "$HOME"/.claude/plugins/cache/brag/brag/*/skills/brag 2>/dev/null | tail -1)
[ -n "$brag" ] && ok "brag plugin (music + sound effects)" || bad "brag plugin" "in Claude Code: /plugin marketplace add latent-spaces/brag  then  /plugin install brag@brag"
if ls "$HOME/.claude/skills" 2>/dev/null | grep -q '^hyperframes-core$'; then ok "Hyperframes skills"
else bad "Hyperframes skills" "npx -y hyperframes@latest skills update hyperframes-core hyperframes-animation hyperframes-creative hyperframes-keyframes hyperframes-cli"; fi

echo "Voice (at least one)"
voice=0
for k in "$HOME/.config/arabic-video/gemini.key" "$HOME/.config/brag/gemini.key"; do
  if [ -s "$k" ] || [ -n "${GEMINI_API_KEY:-}" ]; then ok "Gemini key (Charon — best فصحى)"; voice=1; break; fi
done
[ $voice = 0 ] && warn "Gemini key" "free at https://aistudio.google.com/apikey — run: bash key_setup.sh gemini"
if command -v edge-tts >/dev/null 2>&1; then ok "edge-tts (free, no key)"; voice=1
else warn "edge-tts" "no-key voice: $( [ $mac = 1 ] && echo 'brew install pipx && pipx install edge-tts' || echo 'pip install --user edge-tts')"; fi
for k in "$HOME/.config/arabic-video/elevenlabs.key" "$HOME/.config/brag/elevenlabs.key"; do
  if [ -s "$k" ] || [ -n "${ELEVENLABS_API_KEY:-}" ]; then ok "ElevenLabs key"; voice=1; break; fi
done
[ $voice = 0 ] && { echo "  ❌ no voice engine yet — pick one above"; missing=1; }

echo "Optional"
command -v uv >/dev/null 2>&1 && ok "uv (music-reactive glow)" || warn "uv" "$(hint uv 'https://docs.astral.sh/uv/') — without it the glow just doesn't pulse"
if [ -x /Applications/Blender.app/Contents/MacOS/Blender ] || command -v blender >/dev/null 2>&1; then ok "Blender (3D shots)"
else warn "Blender" "only for the optional 3D shots — https://www.blender.org/download/"; fi

[ $missing = 0 ] && echo "READY" || echo "MISSING"
exit $missing
