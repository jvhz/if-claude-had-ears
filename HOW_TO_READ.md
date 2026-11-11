# How to read what ears writes

This guide is for an AI (or a person) looking at the output of `ears.py` and trying to understand a piece of sound without hearing it.

## Start with report.md

Read `report.md` first. It answers most questions without looking at a picture.

- **At a glance** gives length, tempo, key and overall character.
- **Style clues** says how the music is built: whether it counts in three or four, whether it is straight or swung, where the kick and snare fall, the likely chords, and a shortlist of the kinds of music that usually have that rhythm. `MUSIC.md` explains how to reason from these to a genre.
- **Sections** splits the track into stretches that sound alike, with a short description of each.
- **Moments** lists the times when sound suddenly kicks in or drops out. These are the natural places to cut picture to.
- **Second-by-second strips** show loudness, bass, highs and hits as one character per second. Taller bar means more. Reading along a strip is the quickest way to see the shape of a track.
- **Chord changes** lists the likely chord at each change, with its time.
- **Beat times** lists every beat in seconds, for cutting on the beat.

Then open `overview.png` to see the whole track, and a `zoom_` picture when you need detail about a particular moment.

## The four rows of a picture

### 1. Loudness

- Grey shape: the raw sound wave. Spikes are hits. A smooth block is sustained sound.
- Red line: loudness averaged over one second. 0 is the loudest moment in this track. Every 10 down is roughly "half as loud" to a listener.
- Dashed vertical lines: section changes. Letter and level are written at the top.
- Green up-triangle: sound kicks in here. Blue down-triangle: sound drops out here.
- Ticks along the bottom (close-ups only): beats. Every fourth beat is numbered.

### 2. Pitch map (spectrogram)

Low pitch at the bottom, high pitch at the top. Brighter colour means stronger.

| What you see | What it usually is |
|---|---|
| Bright blob at the very bottom, repeating | Kick drum |
| Thin vertical stripe reaching the top | Hi-hat, cymbal, clap, any sharp click |
| Wide vertical smear, bottom to top | Snare or a crash |
| Steady horizontal lines, stacked | A held note or chord (the stack is the note's overtones) |
| Wavy horizontal lines | A voice, or an instrument with vibrato |
| Lines that slide up or down | A pitch bend, riser, siren, or a voice gliding |
| Fuzzy cloud with no lines | Noise: wind, rain, applause, hiss |
| Everything goes dark | Silence or a pause |

Two dotted lines mark where "bass" ends (250 Hz) and where "highs" begin (4000 Hz).

### 3. Bass / mids / highs

Three lines on the same scale as loudness.

- Bass line jumps up: kick or bass instrument has come in. This is usually "the drop".
- Highs line jumps up: cymbals, hi-hats or bright synths have come in. Often part of a build-up.
- All three fall together: a breakdown or a fade.
- Only mids present: often a voice, piano or guitar on its own.

### 4. Notes

Twelve rows, one per note, C at the bottom. Darker means that note is stronger.

- Three or four dark bars at once is a chord. Read the note names off the left edge (A + C + E is A minor).
- One dark bar moving from row to row is a melody.
- Grey smear across all rows means drums or noise are covering the notes at that point.

## Words to use, and words to avoid

Say what the pictures show. Good: "the bass comes in at 0:16 and the track gets about twice as loud". Good: "there is a breakdown from 0:32 to 0:40 where the drums stop".

Do not claim to have heard anything, and do not describe feelings as facts. "This sounds uplifting" is a guess. "It is in a major key, fast, and bright" is something the data supports, and a person can decide what that feels like.

Treat the style shortlist as a shortlist. Say "the rhythm fits house or disco" and give the clues, not "this is house". If the exact genre matters, ask what instruments and vocals are in it.

Treat tempo and key as estimates. If the report says the key is "a guess" or "unclear", say so. If the tempo looks wrong for the style, try the double or half value listed next to it.
