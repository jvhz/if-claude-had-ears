# Example

`test_track.mp3` is a one-minute track made by `make_test_track.py`. It was built so the right answers are known in advance:

- 120 beats per minute
- A minor (the chords are A minor, D minor, A minor, E minor)
- 0:00 quiet pad, 0:08 hi-hats build, 0:16 full beat, 0:32 pad only, 0:40 full beat again, 0:56 fade out

`test_track_ears/` is what `ears.py` wrote when given that track. Compare its `report.md` with the list above to see how well it reads.

To rebuild it yourself:

```
python make_test_track.py test_track.wav
python ../ears.py test_track.wav
```

## Rhythm test tracks

`make_pattern_tracks.py` builds eight short tracks, one per rhythm style (house, backbeat, swing, shuffle, waltz, 6/8, trap, no drums), each with known answers written at the top of the file. They are used to check the "Style clues" part of the report:

```
python make_pattern_tracks.py pattern_tracks
python ../ears.py pattern_tracks/waltz.wav
```
