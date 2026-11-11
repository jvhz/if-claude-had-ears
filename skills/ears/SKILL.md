---
name: ears
description: Read sound you cannot hear. Turns an audio or video file into pictures and notes (tempo, key, chords, style, sections, beat times, picture cuts against the beat, loudness) and reads the words of a voiceover or speech in many languages. Can also read a YouTube or other browser tab live, and fetch YouTube transcripts. Use when asked what a track, film or video sounds like, what is said in it, or where to cut to the music.
---

# ears: read sound you cannot hear

You cannot hear audio. This tool turns a sound file into pictures and notes you can read. Use it whenever a question depends on what is in the sound of a file.

## When to use

- "What does this track sound like?" / "Describe this music"
- "What's the tempo / key / BPM?" / "What chords?" / "What genre or style is this?"
- "Where are the beats?" / "Where should I cut?" / "Where is the drop?"
- "Does the music fit this edit?" / "Map the energy of this track"
- "What do they say?" / "Transcribe the voiceover" / "How fast is the VO, where are its pauses?"
- "Do my cuts land on the beat?" / "Is this loud enough to deliver?"
- "Listen to this YouTube link"
- Any video where the sound track matters, not just the picture

Best with the actual file (mp3, wav, mp4, mov...). If you only have a link and you can drive the user's browser, use the live script instead (see "Only a link" below). It gives less detail.

## Steps

1. Get the tool if it is not already on the machine:
   ```
   git clone https://github.com/jvhz/if-claude-had-ears.git ears
   pip install -r ears/requirements.txt
   ```
   ffmpeg must be installed.
2. Run it:
   ```
   python ears/ears.py "<file>" --out "<folder>"
   ```
   Add `--words` if speech matters (needs `pip install sherpa-onnx`; fetches a speech model of about 150 MB once). It adds the words with times, plus voice pitch, pace and pauses. It works out the language by itself; if you know it, say so with `--words-language ms` (or `en`, `zh` ...), which is steadier when the voice is over music.
3. Read `<folder>/report.md` first. It has length, tempo, key, loudness for delivery, style clues, sections, chord changes, moments and beat times. For a video it also lists each picture cut and whether it lands on the beat.
4. Look at `<folder>/overview.png`. Open a `zoom_*.png` only when you need detail on a specific stretch.
5. Read `HOW_TO_READ.md` in the repo if you are unsure what a shape in the picture means.
6. For anything about speech, read `SPEECH.md`: what to expect from the words, and how to talk about a voice.
7. For "what kind of music is this?" read `MUSIC.md`. It explains how to go from the style clues to a genre, and what about 30 genres look like in a report.

## Only a link

When there is no file but you can run JavaScript in the user's browser and take screenshots:

1. Read `live/README.md` and follow its steps: open the link in a new tab, paste in the whole of `live/ears_live.js`, `await earsLive.start()`, click the page once, `await earsLive.start()` again, wait, then `earsLive.read()` and `earsLive.draw()` plus a screenshot.
2. It runs in real time and the tab is silent while tapped. Tell the user before starting a long one.
3. For what is said in a YouTube video, use `await earsLive.transcript()` and `earsLive.text(0)`, `text(1)`...
4. It reads tempo, key, notes, bass and loudness shape only. Say so; do not present it as the full report.

## How to answer

- Say what the data shows, with times: "the bass comes in at 0:16", "there are beats every 0.5 seconds from 0:08".
- Never say you listened or heard. You read it.
- Do not present feelings as facts. Give the measurable character (fast, major key, bright, heavy bass) and let the person judge the mood.
- Genre: give the shortlist from "Style clues" with the clues behind it. Do not state a single genre as fact; instruments and vocals decide that and the tool cannot name them.
- Words: quote them as what the speech model read. Names and same-sounding words are often wrong; check names against the title or captions, and ask for the script if exact wording matters. A voice over music is read less reliably than clean speech. Do not describe emotion or guess who is speaking.
- Picture cuts: the beat grid is an estimate, so call a miss of under a tenth of a second a "maybe", not a mistake.
- Tempo and key are estimates. Pass on the confidence the report gives. Mention the double/half tempo when the style suggests it.
- For editing work, give cut points from the "Moments" list and the beat times.
