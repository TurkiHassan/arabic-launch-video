#!/usr/bin/env bash
# Make a private key file and open it in a plain text editor for the user to paste into.
# Usage: key_setup.sh gemini|elevenlabs
# The key never passes through the chat: the user pastes it into this file and saves.
# Afterwards the agent waits with:
#   until grep -qE 'AIza|AQ\.|sk_' ~/.config/arabic-video/<name>.key; do sleep 2; done
set -euo pipefail
name="${1:?usage: key_setup.sh gemini|elevenlabs}"
case "$name" in
  gemini) url="https://aistudio.google.com/apikey" ;;
  elevenlabs) url="https://elevenlabs.io/app/settings/api-keys" ;;
  *) echo "unknown key: $name (use gemini or elevenlabs)" >&2; exit 1 ;;
esac
dir="$HOME/.config/arabic-video"
file="$dir/$name.key"
mkdir -p "$dir"
touch "$file"
chmod 600 "$file"
if [ "$(uname)" = "Darwin" ]; then
  open -e "$file"
elif command -v notepad.exe >/dev/null 2>&1; then
  notepad.exe "$(wslpath -w "$file" 2>/dev/null || echo "$file")" &
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$file" >/dev/null 2>&1 &
fi
echo "KEY_FILE=$file"
echo "GET_KEY_AT=$url"
