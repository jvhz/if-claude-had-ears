# Understanding music: a field guide for a reader with no ears

`ears.py` measures sound. This guide is about what the measurements mean: how to go from "120 beats per minute, low hit on every beat, clap on every second beat" to "this is probably house music".

It is written for an AI reading an ears report, but a person can use it the same way.

## What makes one kind of music different from another

Six things, roughly in order of how much they tell you.

1. **Tempo.** How fast the beat is, in beats per minute (bpm). A slow ballad sits around 60 to 80. Most pop is 90 to 130. Dance music is 118 to 150. Drum and bass is around 170.
2. **The count.** Most music counts in four (ONE two three four). Some counts in three (ONE two three): waltzes, and songs in 6/8, which sway instead of march.
3. **The drum pattern.** Where the low hits (kick drum) and the bright hits (snare, clap) fall.
   - *Four-on-the-floor:* a kick on every beat. Disco, house, techno, most dance music.
   - *Backbeat:* kick on beats 1 and 3, snare on 2 and 4. Rock, pop, funk, soul, hip hop.
   - *Half-time:* snare only on beat 3. Feels half as fast as it is written. Trap, drill, dubstep.
   - *No drum kit:* the rhythm is carried by notes. Classical, solo piano, acoustic folk, a lot of film score.
4. **The feel between the beats.**
   - *Straight:* the in-between note sits exactly halfway. Most modern music.
   - *Swung:* the in-between note comes late, giving a long-short, long-short lilt. Jazz, blues shuffles, some hip hop and lo-fi.
   - *Threes:* each beat splits into three. 12/8 blues, doo-wop, slow soul.
5. **The chords.**
   - *Three or four plain chords, repeating:* country, punk, most pop and rock.
   - *One chord throughout:* trap, drill, a lot of funk and dance music. The interest comes from rhythm and sound, not harmony.
   - *Rich chords* (extra notes stacked on top: sevenths, ninths): jazz, R&B, neo-soul, lo-fi, bossa nova, house. They sound smoother and more "expensive".
   - *Major* keys tend to sound bright or happy, *minor* keys dark or sad. This is a tendency, not a rule.
6. **The sound itself.** Which instruments, clean or distorted, warm or bright, polished or deliberately rough. This is often what really decides the genre, and it is the part ears is weakest at.

There is also **what the melody is doing**. In pop and country the melody is the point. In trap it is a quiet repeating background and the drums and bass are the point. In drum and bass there may be no melody at all, only a collage of sounds.

## What ears can and cannot see

| Thing | Can ears read it? | Where in the report |
|---|---|---|
| Tempo | Yes, but it can come out double or half | At a glance |
| Count in three or four | Usually | Style clues |
| Kick on every beat, backbeat, half-time | Yes when the drums are clear | Style clues |
| Straight, swung or threes | Yes | Style clues |
| Which chords, and how often they change | Roughly. It only knows plain major and minor chords | Style clues, Chord changes |
| Rich chords (sevenths and so on) | No. They show as the nearest plain chord | |
| Major or minor | Usually | At a glance |
| Deep sub bass | Yes | Style clues |
| Wide or narrow loud-to-quiet range | Yes | Style clues |
| Build-ups and drops | Yes | Moments, Sections |
| Which instruments | No. It can say "drum-like hits" or "notes", no more | |
| Singing, rapping, lyrics | No (words only with `--words`, untested) | |
| Distortion, warmth, "lo-fi" texture | Barely. "Overall tone" says dark or bright | |
| Mood | No | |

So ears can usually place a track in a **rhythm family**. Telling apart genres inside one family (rock from pop from country, say) needs the things in the bottom half of the table. Ask the person, or look at the title, artist and cover.

## Genres, and what each looks like to ears

Tempos are typical, not rules. "Felt" tempo is what you would tap your foot to.

### No drum kit

| Genre | Tempo | Rhythm | Chords and sound | In an ears report |
|---|---|---|---|---|
| Classical | Any, often changing | Carried by the instruments | Many chord changes; violin, piano, cello, full orchestra | No drum-like hits. Often "no steady beat" because players speed up and slow down. Wide loud-to-quiet range. Almost no deep bass |
| Solo piano, ragtime | 80 to 150 | Steady left hand, straight | Left hand low, right hand busy | Steady beat, no drum-like hits, low hit on most beats (the left hand) |
| Acoustic folk | 70 to 130 | Strummed guitar | Three or four plain chords, major | Steady beat, no drum-like hits, one chord dominating |
| Bossa nova | 120 to 140 | Soft, off-beat guitar pattern | Rich chords, soft voice | Steady beat, quiet or no drums, narrow range. Hard to tell from other soft acoustic music |
| Ambient, film pads | None | None | Long held sounds | No steady beat, very few hits |

### Counts in three

| Genre | Tempo | Rhythm | In an ears report |
|---|---|---|---|
| Waltz | 90 to 180 | Low note on ONE, lighter chords on two and three | "Count: in three". Low hits on about a third of beats |
| 6/8 ballad (soul, R&B, folk) | 50 to 70 felt | Two slow beats, each split in three; snare on the second | "In three", or "each beat splits into three". ears may report the tempo 1.5 times too fast |

### Swung

| Genre | Tempo | Rhythm | Chords and sound | In an ears report |
|---|---|---|---|---|
| Swing jazz | 100 to 250 | Swung cymbal, bass walking on every beat | Rich chords, improvised solos; saxophone, trumpet, double bass, piano, drums | "Swung". Chords change often. Tempo often reported at half |
| Blues | 60 to 120 | Shuffle (swung) or threes | Three chords in a 12-bar pattern; guitar, harmonica, piano | "Swung" or "threes", three main chords |
| Lo-fi hip hop | 60 to 90 | Lazy, slightly swung backbeat | Seventh chords; deliberately worn sound: hiss, wobble, muffled highs | Slow, backbeat, maybe swung, "dark, warm" tone, narrow range |

### Backbeat (kick and snare take turns)

| Genre | Tempo | Rhythm | Chords and sound | In an ears report |
|---|---|---|---|---|
| Hip hop (classic) | 80 to 100 | Heavy kick and snare, often sampled from old soul records | A short loop, few chords; rapping | Backbeat, slow to mid tempo, low hits not on every beat |
| Soul, R&B | 60 to 110 | Smooth backbeat | Rich chords, the voice leads; saxophone, keys | Backbeat, slow. Chords read less reliably |
| Neo-soul | 60 to 100 felt | Loose backbeat | Unusual rich chords; electric piano and bass | As R&B. Producers often write it at double tempo |
| Funk | 90 to 125 | Busy, syncopated, strong first beat | Often one or two chords; big bass line | Backbeat, many hits per second, few chords |
| Reggae | 60 to 90 | Guitar chops on the off-beats, kick on beat 3 | Heavy bass, few chords | Slow, heavy bass, hits between the beats |
| Country | 70 to 130 | Simple backbeat | Three or four plain major chords; guitar, banjo, fiddle, slide guitar; storytelling | Backbeat or no drums, major key, slow chord changes |
| Pop | 90 to 130 | Steady backbeat or four-on-the-floor | Four-chord loop, catchy melody, soft polished sounds | Backbeat or four-on-the-floor, clear sections, narrow range |
| Rock 'n' roll | 120 to 180 | Driving backbeat, often shuffled | 12-bar blues chords; electric guitar, bass, drums | Backbeat, fast, three main chords |
| Rock, indie, grunge | 100 to 160 | Backbeat | Guitar-led. Grunge is distorted with quiet-loud changes; indie is warmer, with reverb | Backbeat. Grunge shows big jumps between sections |
| Punk | 160 to 200 | Fast, straight backbeat | Three chords, raw | Backbeat, very fast |
| Metal | 100 to 200+ | Fast double kick drum | Distorted guitars, minor, complex | Many low hits per beat, narrow range, minor |
| Drum and bass | 165 to 180 | Fast broken beat, snare on 2 and 4 | Heavy, morphing bass sounds; little melody | Backbeat at about 170, or reported as 85 |

### Four-on-the-floor (kick on every beat)

| Genre | Tempo | Chords and sound | In an ears report |
|---|---|---|---|
| Reggaeton, dancehall | 85 to 105 | Kick on every beat with a snare pattern on top; simple repeating melody | Low hit on every beat, 85 to 105 |
| Disco | 110 to 130 | Strings, octave bass, open hi-hat on the off-beat | Low hit on every beat, clap on every second |
| House | 118 to 130 | Rich chords moved around as a block, off-beat bass | Low hit on every beat, about two low hits per beat (kick plus off-beat bass) |
| Techno, trance | 125 to 150 | Synthesisers, long builds | Low hit on every beat, long sections, big "kicks in" moments |
| EDM (festival) | 125 to 150 | Build-up, silence, drop | Same, with sharp drops and returns in "Moments" |
| K-pop | 90 to 130 | Mixes several styles in one song | Many different sections; the rhythm family may change part-way |

### Half-time (snare on every fourth counted beat)

| Genre | Tempo | Chords and sound | In an ears report |
|---|---|---|---|
| Trap | 130 to 160 written, felt as half | One minor chord; long deep "808" bass; fast rolling hi-hats; quiet, repetitive melody | Snare every fourth beat, very heavy deep bass, one chord, sparse low hits |
| Drill | About 140 | Dark and minimal; one minor chord; sliding bass | As trap. ears cannot tell them apart |
| Rage | About 140 | As trap but with bright, distorted synths up front | As trap with a brighter tone |
| Dubstep | About 140 | Wobbling, distorted bass | As trap, with big drops |

## How to reason from a report to a style

1. **Is there a steady beat?** If not: classical, film score, ambient, or not music at all (speech, sound effects).
2. **Three or four?** If three: waltz or 6/8.
3. **Straight, swung or threes?** Swung points to jazz or blues, or hip hop with swing.
4. **What do the drums do?** Kick on every beat is a dance family. Backbeat is the pop, rock, hip hop family. Snare every fourth beat is the trap family. No drum kit is acoustic or classical.
5. **Now use the tempo** to narrow within the family (the tables above). Try the double and the half as well.
6. **Check the supporting clues.** One chord and heavy deep bass supports trap. Wide loud-to-quiet range supports acoustic or orchestral. Many "kicks in" and "drops out" moments support EDM.
7. **Stop there and say what you cannot know.** Give a shortlist, say which clues led to it, and ask about instruments and vocals if the exact genre matters.

## Two traps to avoid

- **Double and half tempo.** A trap beat written at 140 feels like 70. Drum and bass at 174 can be counted as 87. If the style and the tempo do not fit, try doubling or halving before deciding the style is wrong.
- **Low hits are not always a kick drum.** A walking jazz bass or a pianist's left hand also puts a low note on every beat. Only call it four-on-the-floor when there are drum-like hits too.

## Where this guide comes from

The genre descriptions draw on two videos, plus general music knowledge:

- "Music Genres Explained in 8 Minutes" (Ball League): the history, instruments and key artists of 20 genres. https://www.youtube.com/watch?v=8KiJ4_GZIt0
- "Analyzing 20 Genres And Their Unique Melodies" (Servida Music): how a producer builds a melody for each of 20 genres, with tempos, chord choices and sound choices. https://www.youtube.com/watch?v=0vLNybDXh2g

Both were read as transcripts, not heard. The second video's main lesson is worth keeping in mind: in many modern genres the melody is simple on purpose, and the style lives in the rhythm, the chord colour and how the sounds are processed.
