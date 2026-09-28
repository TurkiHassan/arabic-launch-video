# Arabic narration that sounds فصحى, not machine

Everything here was learned from rejected takes. The voice drives the timing of the whole
video, so it is written and generated **before** the storyboard.

## 1. Write the lines

- **One line per scene**, 5-6 lines for 20-30 s. Aim for 2-5 s of speech each; the hook ≤ 2.5 s.
- **Spoken, not written**: short clauses, the verb early, one idea per line. Read it aloud
  in your head at an announcer's pace (≈ 2.3-2.8 words/second after tempo).
- **Quote the product's own words** where you can (its tagline, button labels).
- **Full tashkeel on every letter that carries a vowel**, including case endings. The
  diacritics are what hold the model in فصحى; an undiacritized line drifted into an Egyptian
  read and was rejected.
- **Brand and English words spelled as spoken**: آبْ سْتُورْ, جُوجِل بْلَايْ, تِيك تُوك.
  Short Latin acronyms (PDF, AI) may stay Latin — check the read.
- **Numbers as words**, fully voweled: أَرْبَعَةٌ وَثَلَاثُونَ دَرْسًا — never digits in the voice text.
- **End of sentence = waqf**: the last word before a full stop is read with sukun anyway; write
  it with its case vowel or sukun, but do not put tanween-alif where a stop is intended.
- **The app name**: add the vowels you want heard (قُدْرَة), and keep it identical across lines.
- **No instructions inside the text.** "بصوت حماسي: …" gets read aloud. Tone is chosen by voice,
  not by prompt.

Save the lines as a JSON array: `voice-lines.json`. Show them to the user before spending
quota; they may want a word changed.

## 2. Pick the engine

| Engine | Cost / setup | Quality in فصحى | Use when |
|---|---|---|---|
| Gemini `gemini-3.1-flash-tts-preview`, voice **Charon** | free key from aistudio.google.com/apikey, ~10 requests/day/model | best of the three; calm, confident; approved in two shipped ads | default |
| edge-tts `ar-SA-HamedNeural` / `ar-SA-ZariyahNeural` | none — works instantly | clear but flatter, less expressive | first try, no key, or Gemini quota gone |
| ElevenLabs **Haytham** (3 library voices) | API needs paid Starter; free accounts can download from the site by hand | expressive; the voices are tagged Egyptian, so tashkeel + `language_code: ar` is essential and the user must listen | user already pays for ElevenLabs |

Gemini notes:
- One request per line; the script sleeps 6 s between lines for the per-minute limit and stops
  cleanly on the daily limit. **Dry-run first** (`--dry-run` costs nothing).
- Each TTS model has its own daily quota; if one is spent, switch model — but regenerate *all*
  lines on the same model so the voice stays one person.
- If a line comes out much longer than its text, the model read something extra (often a
  bracket or a number). Fix the text and redo only that line with `--only N`.

## 3. Clean and pace

```bash
S="<plugin root>/scripts"
bash $S/prep_voice.sh RAW_DIR COMPOSITION_DIR 1.2     # trim edges, tempo (Gemini 1.15-1.2, ElevenLabs 1.0, edge-tts 1.0-1.05)
python3 $S/tighten_pauses.py COMPOSITION_DIR/assets/voice --keep 0.2 --keep-last 0.3
```

`tighten_pauses.py` cuts every comma/colon breath longer than 0.2 s down to 0.2 s. In the
Qudrah Academy ad it took speech from 27.1 s to 25.6 s without touching a word. Keep a slightly
longer beat (0.3 s) in the last line between the name and the CTA.

If the total is still too long for the target length: shorten words (not tempo past 1.2 —
faster than that sounds rushed in Arabic), or drop one clause the screen already shows.

## 4. You cannot hear it — say so

Tell the user plainly that you cannot listen to audio, and ask them to play the lines (or the
first render) and confirm: فصحى not dialect, the product name, numbers, and English words.
Offer to redo single lines. Common fixes:

| Heard | Fix |
|---|---|
| dialect vowels, "ج" as "g" | add missing tashkeel, especially case endings; re-generate |
| name mispronounced | respell phonetically with vowels; keep that spelling everywhere |
| a number read oddly | write it as words with vowels |
| rushed ending | lower tempo for that line only (re-run prep on it), or trim words |
| long gap mid-line | re-run `tighten_pauses.py` with `--keep 0.15` |

## 5. Own voice (user records)

Give them the diacritized script as a numbered list and ask them to record each line
separately on their phone (Voice Memos), quiet room, phone 20 cm away, a breath of silence
before and after, and send `vo1…voN`. Run the same `prep_voice.sh` with tempo 1.0 and
`tighten_pauses.py`. Human voice beats every engine; offer it to anyone hesitant about AI voices.

## 6. Subtitles (recommended for social)

Most social video is watched muted. After the final mix, `make_srt.py` writes Arabic
subtitles from the same lines (tashkeel stripped, RTL-marked) — upload the `.srt` next to the
video on YouTube/TikTok/LinkedIn.
