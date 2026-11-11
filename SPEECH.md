# Understanding speech: a field guide for a reader with no ears

`MUSIC.md` is about telling kinds of music apart. This guide is about the other thing sound carries: words.

It covers what speech looks like as a picture, why words cannot simply be read off that picture, and how ears gets the words anyway.

## Sound, in three plain ideas

1. **Sound is vibration.** Something shakes (a string, a drum skin, the folds in your throat) and the air carries the shaking to a listener.
2. **Louder is taller.** In a wave picture, a louder sound makes a taller wave. The technical word is *amplitude*.
3. **Higher is more squashed.** A higher-pitched sound makes waves that are packed closer together. The technical word is *frequency*, counted in Hertz (Hz): waves per second.

The everyday words (tall, squashed) come first on purpose. The technical words are only labels for them.

## How a voice makes sound

There are two sources, and every speech sound is one, the other, or a mix.

| Source | How it is made | What the wave looks like | Examples |
|---|---|---|---|
| **Voiced** | The vocal folds in the throat buzz | A pattern that repeats exactly, over and over | All vowels; m, n, l, r, w, y |
| **Voiceless** | Air hisses through a narrow gap | Random scribble with no repeating pattern | s, sh, f, h |
| **Mixed** | Both at once | A repeating pattern with scribble on top | z, v |

How fast the voiced pattern repeats is the **pitch of the voice**. Roughly 100 repeats a second (100 Hz) is typical of an adult male voice, about twice that for an adult female voice, and higher again for a child. The pitch moves all the time while someone talks; that movement is the melody of speech.

The shape of the mouth then filters the buzz or the hiss. Moving the tongue and lips changes which parts of the sound come through strongly, and that is what turns one buzz into "ee", "ah" or "oo".

## What each kind of speech sound looks like

| Sound | Examples | In the wave | In ears' sound-shape strip |
|---|---|---|---|
| **Vowel** | a, e, i, o, u sounds | The loudest part of speech. Regular repeating pattern. Rises quickly, peaks early, then tails off (a "fish skeleton" shape) | `v` |
| **Nasal** | m, n, ng | Repeating, but simpler and quieter than a vowel, mostly low frequencies | `v` |
| **Glide** | l, r, w, y | Like a brief vowel that is on the move | `v` |
| **Strong hiss** | s, sh, z | Dense random scribble, fairly loud, very bright (high frequencies) | `s` |
| **Weak hiss** | f, th, h | The same but much quieter. Easy to miss | `-` or `.` |
| **Stop, voiceless** | p, t, k | A short silence (the mouth is closed), then a tiny burst (1 to 5 thousandths of a second), then about a tenth of a second of breathy hiss before the vowel starts | `.` then `s` or `-` |
| **Stop, voiced** | b, d, g | A low hum during the closure, then a weaker burst | `.` or `v` |
| **Stop plus hiss** | ch, j | A burst followed by a short, sharply rising hiss | `s` |

Of the stops, **t** has the sharpest, clearest burst (the tongue tip is quick), **p** the weakest, and **k** often a double burst.

So a word like "stick" reads, left to right: hiss (s), gap and burst (t), vowel (i), gap and burst (k).

## Why you cannot just read the words off the picture

- **A wave shows that there is a vowel, not which vowel.** "Heed", "heard" and "hard" look almost the same as waves. Telling vowels apart needs the pitch map (spectrogram), where each vowel has its own pattern of bright bands.
- **Sounds blur into each other.** There are no gaps between words in normal speech. The gaps you see are the closed-mouth moments of p, t, k, b, d, g, which fall in the middle of words as often as between them.
- **The same sound is said many ways.** The "t" in "team" and the "t" in "mountain" are physically very different sounds. An English speaker hears both as "t" because the brain files them in the same mental bin. Linguists call those bins **phonemes**, and the system of bins and rules is the **phonology** of a language.
- **Each language has its own bins.** English keeps "r" and "l" in separate bins. Japanese and Korean keep them in one, which is why speakers of those languages can find the two hard to tell apart. What counts as "the same sound" depends on the language, not on the sound wave.
- **Spelling is a separate code again.** Australian English has 43 speech sounds but the alphabet has 26 letters, so one sound can be written many ways. The "k" sound is spelled k in "king", c in "cat", ck in "duck", ch in "chemist" and q in "queen". The written units are called **graphemes**. Going from sounds to letters is spelling; going from letters to sounds is reading.

A listener therefore does three jobs at once: sorts raw sound into the language's bins, joins the bins into words, and (to write it down) picks the right spelling. None of that is visible in the picture itself. It is learned.

## So how does ears get the words?

With a model that has done that learning. `--words` uses Whisper, a speech model that was shown a very large amount of speech alongside its text. Its input is the same kind of pitch-map picture that ears draws. It has learned the bins, the blurring and the spelling, for many languages.

What to expect from it:

- **Ordinary words come out right** almost all the time on clear speech.
- **Names go wrong.** It has never seen them, so it spells them by sound: "Catherine" came out as "Chather in" in testing.
- **Same-sounding words get swapped.** "Knights of the Table Round" came out as "nights of the table round". The sound is identical; only meaning tells them apart. This is the sounds-versus-spelling problem in action.
- **It invents words when there is no speech.** Given music or noise it may write something anyway. ears checks whether there is really a voice and says so.

## What ears reads about a voice, apart from the words

These come from measuring, not from the speech model, so they work in any language.

| Reading | What it tells you |
|---|---|
| **Voice pitch** | How high or low the voice is, in Hz. A pitch range is a hint about the speaker, not proof of who they are |
| **Melody of the voice** | Whether the pitch moves a lot (lively, expressive) or little (flat, calm, or monotone) |
| **Pace** | Words a minute. About 120 to 180 is ordinary talk. Voiceovers for film are often slower |
| **Pauses** | Every gap of 0.3 seconds or more, with its time. These are the natural places to cut a voiceover |
| **Sound shape** | Under each line, one mark per tenth of a second: `v` voiced, `s` hiss, `-` breath or noise, `.` silence. It shows the rhythm of the line: where the stresses and breaks fall |

## How to talk about speech you have read this way

- Quote the words as "what the speech model read", and expect names to be wrong. Check a name against the title, description or captions before using it.
- Do not judge the tone of voice ("she sounds angry"). You can say the pitch is high and moving a lot, the pace is fast, and the pauses are short. The person can decide what that means.
- For cutting a voiceover to picture, use the pause times and the line start and end times.

## Where this guide comes from

- "The Sound Systems of Language" (Mango Languages): phonemes as the brain's sorting bins, and the rules for how sounds change next to each other. https://www.youtube.com/watch?v=hvMkeX_tD8c
- "The Waveforms of Speech" (Robert Mannell, Macquarie University): voiced and voiceless sources, and what vowels, hisses, stops and nasals look like as waves. Read about two-thirds of the way through. https://www.mq.edu.au/faculty-of-medicine-health-and-human-sciences/departments-and-schools/department-of-linguistics/our-research/phonetics-and-phonology/speech/acoustics/speech-waveforms/the-waveforms-of-speech
- "Learning about sound waves with English language learners" (Alice Leung): sound as vibration, "tall" before amplitude, "squashed" before frequency. https://aliceleung.net/2013/05/24/learning-about-sound-waves-with-english-language-learners/
- "Sound Waves Parent Information" (Firefly Education): 43 sounds against 26 letters, phonemes and graphemes, breaking words into sounds and blending them back. https://www.youtube.com/watch?v=AFUMMebDl0k

The videos were read as transcripts, not heard.
