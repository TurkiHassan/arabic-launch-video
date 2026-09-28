---
name: arabic-voiceover
description: Add a فصحى Arabic voiceover to a video the user already has (or produce a narration audio file) — write or polish the script, fully diacritize it, generate it with Gemini (Charon), edge-tts (free, no key) or ElevenLabs, or use the user's own recording, fit it to the video's length, duck the original sound and music under it, and export subtitles. Use when someone says "أبغى تعليق صوتي عربي", "أضف صوت على الفيديو", "تعليق فصحى", "narration in Arabic", "voice over my video", or has a finished video and only needs the Arabic voice.
---

# Arabic voiceover

The user has a video (screen recording, product demo, slideshow, reel) and wants Arabic
narration on it — or just an Arabic voice file. They are usually not technical: plain Arabic,
one step at a time, no key in the chat.

`S` = `<this skill's base directory>/../../scripts`. The linguistic rules live in
`../arabic-launch-video/references/arabic-voice.md` — read it first; everything there applies.

## 1. Interview (AskUserQuestion, skip what is already known)

1. **The video**: "اسحب الفيديو إلى المحادثة أو ضعه في مجلد المشروع" — or "no video, audio only".
   Probe it (`ffprobe` duration, has audio?) and watch a few frames (`ffmpeg -ss T -frames:v 1`)
   so the script matches what is on screen and when.
2. **The words**: they have a script / they give bullet points / you write it from the video.
3. **Engine & voice**: Gemini Charon (recommended, free key) · edge-tts (instant, no key) ·
   ElevenLabs Haytham · their own voice (you give them the script to record).
   Male/female, calm/energetic.
4. **The video's own sound**: خفضه تحت الصوت (default) · أبقه كما هو · احذفه.
   **Music**: add a bundled bed (brag's `assets/music/`) · their own track · none.
5. **Subtitles**: yes (recommended for social) / no.

Show a short checklist (video ✅, script ⏳, key ⏳, …) and set up what is missing
(`bash "$S/key_setup.sh" gemini` — see the full skill's Phase 1 for the paste-and-save steps).

## 2. Script → timing plan

- Split the narration into lines by what is on screen: one line per shot or idea, with the
  second each one should start (from the frames you looked at).
- Budget ≈ 2.5 words/second after pacing; the lines must end before the video does. If they
  do not fit, cut words — do not speed past tempo 1.2.
- Full tashkeel, numbers as words, brand names spelled as spoken (arabic-voice.md §1).
- Show the diacritized lines with their start times and get an OK before generating.

Save `voice-lines.json` (array of lines) in a working folder, e.g. `voiceover/`.

## 3. Generate, clean, pace

```bash
python3 "$S/gemini_tts.py" voiceover/voice-lines.json voiceover/raw --dry-run
python3 "$S/gemini_tts.py" voiceover/voice-lines.json voiceover/raw
#   no key: python3 "$S/edge_tts_lines.py" voiceover/voice-lines.json voiceover/raw --voice ar-SA-HamedNeural
#   own voice: put their vo1.m4a … in voiceover/raw
bash "$S/prep_voice.sh" voiceover/raw voiceover 1.2        # 1.0 for edge-tts / ElevenLabs / own voice
python3 "$S/tighten_pauses.py" voiceover/assets/voice
```

Say that you cannot hear audio; open the folder for them and ask them to listen and confirm.

## 4. Mix onto the video

```bash
python3 "$S/mix_voiceover.py" --video INPUT.mp4 --voice-dir voiceover/assets/voice \
  --starts 0.5,4.2,9.0 --original duck [--music TRACK.mp3 --music-volume 0.3] \
  --out voiceover/output-ar.mp4
# audio only: omit --video, use --out voiceover/narration.m4a
```

The picture is copied untouched; the original sound and music dip under the voice and come
back in the gaps; the result is normalized to -14 LUFS. The script warns if the voice runs
past the end.

## 5. Subtitles and hand-off

```bash
python3 "$S/make_srt.py" voiceover/voice-lines.json voiceover/output-ar.timings.json voiceover/output-ar.srt
```

Deliver the MP4 (and SRT) with SendUserFile when available. Tell them how to add the SRT
(YouTube: Subtitles → Upload file; TikTok/Instagram: most editors import SRT) and offer to
redo any single line.
