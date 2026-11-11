---
name: ears
description: Read the sound of an audio or video file (music, voiceover, a film's sound track) by turning it into pictures and notes with ears.py. Use when asked what a track or video sounds like, its tempo, key, beat times, structure, or where to cut to the music.
---

# ears: read sound you cannot hear

You cannot hear audio. This tool turns a sound file into pictures and notes you can read. Use it whenever a question depends on what is in the sound of a file.

## When to use

- "What does this track sound like?" / "Describe this music"
- "What's the tempo / key / BPM?"
- "Where are the beats?" / "Where should I cut?" / "Where is the drop?"
- "Does the music fit this edit?" / "Map the energy of this track"
- Any video where the sound track matters, not just the picture

You need the actual file (mp3, wav, mp4, mov...). A streaming link is not enough. If you only have a link, ask for the file.

## Steps

1. Get the tool if it is not already on the machine:
   ```
   git clone https://github.com/jvhz/ears.git
   pip install -r ears/requirements.txt
   ```
   ffmpeg must be installed.
2. Run it:
   ```
   python ears/ears.py "<file>" --out "<folder>"
   ```
   Add `--words` if speech or lyrics matter (needs `pip install faster-whisper`).
3. Read `<folder>/report.md` first. It has length, tempo, key, sections, moments and beat times.
4. Look at `<folder>/overview.png`. Open a `zoom_*.png` only when you need detail on a specific stretch.
5. Read `HOW_TO_READ.md` in the repo if you are unsure what a shape in the picture means.

## How to answer

- Say what the data shows, with times: "the bass comes in at 0:16", "there are beats every 0.5 seconds from 0:08".
- Never say you listened or heard. You read it.
- Do not present feelings as facts. Give the measurable character (fast, major key, bright, heavy bass) and let the person judge the mood.
- Tempo and key are estimates. Pass on the confidence the report gives. Mention the double/half tempo when the style suggests it.
- For editing work, give cut points from the "Moments" list and the beat times.
