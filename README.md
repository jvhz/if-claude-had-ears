# ears

**Lets an AI that cannot hear read sound instead.**

AI assistants like Claude work with text and pictures. They have no ears. But sound can be turned into pictures and numbers, the same way a musician can look at a score in silence and know how the music goes.

`ears` takes any audio or video file and writes a small folder of pictures and notes that describe what is in the sound: how loud it is from second to second, where the beat falls, which notes are playing, where the bass comes in, and where the track changes.

It is reading, not hearing. It gives an AI the structure, timing and energy of a track. It does not give it the feeling.

![The whole test track in one picture](examples/test_track_ears/overview.png)

## What you get

Run it on `song.mp3` and you get a folder called `song_ears` with:

| File | What it is |
|---|---|
| `report.md` | The track in plain words: length, tempo, key, sections, the moments where sound kicks in or drops out, and the time of every beat |
| `overview.png` | The whole track in one picture |
| `zoom_01...png` | The same picture, close up, 20 seconds at a time |
| `data.json` | Every number behind the report, for other tools to use |

## How to use it

You need Python 3.9 or newer and [ffmpeg](https://ffmpeg.org) (ffmpeg is what lets it open mp3, mp4, mov and almost anything else).

```
pip install -r requirements.txt
python ears.py song.mp3
```

It works on video files too. It just reads the sound track:

```
python ears.py film.mp4
```

To also write down speech or lyrics with timestamps, add `--words`. This needs one extra install and downloads a speech model the first time:

```
pip install faster-whisper
python ears.py interview.mp4 --words
```

Other options: `--out folder` chooses where the results go, and `--zoom 10` makes each close-up cover 10 seconds instead of 20.

## How to read the picture

Time runs left to right in all four rows.

1. **Loudness.** The grey shape is the raw sound wave. The red line is how loud it is, where 0 is the loudest moment of the track. Dashed lines mark where the track changes, and each stretch gets a letter. Green triangles mark sound kicking in, blue triangles mark sound dropping out. In close-ups, small ticks along the bottom are the beats.
2. **Pitch map.** Low sounds at the bottom, high sounds at the top, brighter means stronger. A kick drum is a bright blob at the very bottom. A cymbal is a thin stripe reaching the top. A held note is a horizontal line.
3. **Bass / mids / highs.** Three lines showing how loud the low, middle and high parts of the sound each are. When the bass line jumps up, the bass has come in.
4. **Notes.** Which of the twelve notes are sounding. A chord shows up as three or four dark bars at the same time.

There is a longer guide in [HOW_TO_READ.md](HOW_TO_READ.md).

## How accurate is it

Tested on a small set, so treat these as a first check, not a guarantee.

**Five made-up tracks where the right answers are known** (same layout at 90, 120, 128, 140 and 174 beats per minute, all in A minor; `examples/make_test_track.py` builds them):

| What | Result |
|---|---|
| Tempo | Within 0.5 bpm on four tracks. The 174 track was read as 87, exactly half. This double-or-half mix-up is common, so the report always lists both |
| Key | Correct on all five |
| Big changes (beat comes in, breakdown, beat returns, fade) | All found, within 0.6 seconds |
| Small change (quiet hi-hats starting) | Found on four, misplaced on one |
| Beat positions | Typically within 1/100 of a second where drums are playing |

**Three real recordings** (from the open example set that comes with the librosa library):

| Recording | Result |
|---|---|
| A drum and bass loop | 137 bpm, strong steady beat |
| Tchaikovsky, Dance of the Sugar Plum Fairy | E minor, which is the key it is written in. Clear beat, about 109 bpm |
| A spoken audiobook clip | Correctly reported "no steady beat" |

**Not tested yet:** the `--words` option. The speech model could not be downloaded on the machine this was built on.

## What it cannot do

- It cannot tell you if a track is good, or how it feels.
- It does not name instruments. It can say "bright hits" but not "that is a tambourine".
- Tempo can come out as double or half the real speed. Key can be confused with a close relative (C major and A minor use the same notes).
- Where there are no drums, beat positions are estimated and can drift.
- Section letters (A, B, C) are labels in order. They do not mean verse or chorus.

## Using it with Claude

[SKILL.md](SKILL.md) is a short instruction sheet that tells Claude when to run this tool and how to talk about what it finds. Add it as a skill, or just tell Claude: "run ears on this file and tell me what you find".

## How it works

One Python file, `ears.py`, built on [librosa](https://librosa.org) (sound analysis) and [matplotlib](https://matplotlib.org) (drawing). The code is commented in plain language.

## Licence

MIT. See [LICENSE](LICENSE).
