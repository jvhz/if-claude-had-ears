#!/usr/bin/env python3
"""
Makes short test tracks for rhythm styles, where we know the right answers,
so we can check that the "style clues" in ears.py read them correctly.

  house     124 bpm  kick on every beat, clap on 2 and 4, straight
  backbeat  110 bpm  kick on 1 and 3, snare on 2 and 4, straight (rock / pop)
  swing     150 bpm  swung cymbal, walking bass, no kick pattern (jazz)
  shuffle    96 bpm  kick and snare with swung hi-hats (blues shuffle)
  waltz     150 bpm  three beats in a bar: bass on 1, chords on 2 and 3
  six8       60 bpm  slow beat that splits into three (6/8 ballad)
  trap      140 bpm  snare only every 4th beat, fast hi-hats, long deep bass
  nodrums    80 bpm  chords only, no drums

Usage:  python make_pattern_tracks.py <folder>
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
rng = np.random.default_rng(11)


def env(n, rate):
    return np.exp(-np.arange(n) / SR * rate)


def kick():
    n = int(0.25 * SR)
    x = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-x * 30)) / SR) * env(n, 14)


def snare():
    n = int(0.18 * SR)
    x = np.arange(n) / SR
    return (rng.standard_normal(n) * 0.7 + np.sin(2 * np.pi * 190 * x) * 0.4) * env(n, 24)


def clap():
    n = int(0.12 * SR)
    return np.diff(rng.standard_normal(n), prepend=0) * env(n, 30) * 0.8


def hat(length=0.045):
    n = int(length * SR)
    return np.diff(rng.standard_normal(n), prepend=0) * env(n, 90) * 0.5


def tone(freq, length, decay=3.0, harmonics=(1, 0.4, 0.2)):
    n = int(length * SR)
    x = np.arange(n) / SR
    wave = sum(a * np.sin(2 * np.pi * freq * (i + 1) * x) for i, a in enumerate(harmonics))
    return wave * env(n, decay) * np.sin(np.pi / 2 * np.minimum(1, x / 0.03)) ** 2     # soft start, no click


def chord(freqs, length, decay=2.0):
    return sum(tone(f, length, decay) for f in freqs) / len(freqs)


NOTE = {"A1": 55.0, "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.0, "A2": 110.0,
        "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.0, "A3": 220.0,
        "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0}
CHORDS = {"Am": ["A3", "C4", "E4"], "Dm": ["D3", "F3", "A3"], "Em": ["E3", "G3", "B3"],
          "C": ["C3", "E3", "G3"], "F": ["F3", "A3", "C4"], "G": ["G3", "B3", "D4"]}
ROOT = {"Am": "A1", "Dm": "D2", "Em": "E2", "C": "C2", "F": "F2", "G": "G2"}


class Track:
    def __init__(self, bpm, seconds=40):
        self.beat = 60 / bpm
        self.out = np.zeros(int(seconds * SR))
        self.beats = int(seconds / self.beat)

    def put(self, sound, at_beat, gain=1.0):
        i = int(at_beat * self.beat * SR)
        j = min(len(self.out), i + len(sound))
        if 0 <= i < len(self.out):
            self.out[i:j] += gain * sound[:j - i]

    def save(self, path):
        x = self.out / np.abs(self.out).max() * 0.89
        sf.write(path, x.astype(np.float32), SR)


def house():
    t = Track(124)
    prog = ["Am", "F", "C", "G"]
    for b in range(t.beats):
        c = prog[(b // 4) % 4]
        t.put(kick(), b, 0.95)
        t.put(hat(), b + 0.5, 0.45)
        if b % 2 == 1:
            t.put(clap(), b, 0.5)
        t.put(tone(NOTE[ROOT[c]], t.beat * 0.4, 6), b + 0.5, 0.45)     # off-beat bass
        if b % 4 == 0:
            t.put(chord([NOTE[n] for n in CHORDS[c]], t.beat * 4, 0.6), b, 0.3)
    return t


def backbeat():
    t = Track(110)
    prog = ["C", "G", "Am", "F"]
    for b in range(t.beats):
        c = prog[(b // 4) % 4]
        if b % 2 == 0:
            t.put(kick(), b, 0.95)
            t.put(tone(NOTE[ROOT[c]], t.beat * 0.9, 4), b, 0.5)
        else:
            t.put(snare(), b, 0.6)
        t.put(hat(), b, 0.3)
        t.put(hat(), b + 0.5, 0.3)
        if b % 4 == 2:
            t.put(kick(), b + 0.5, 0.7)
        if b % 2 == 0:
            t.put(chord([NOTE[n] for n in CHORDS[c]], t.beat * 2, 1.5), b, 0.3)
    return t


def swing():
    t = Track(150)
    walk = ["A1", "C2", "D2", "E2", "D2", "F2", "E2", "C2"]
    prog = ["Am", "Dm", "Em", "Am"]
    for b in range(t.beats):
        t.put(hat(0.09), b, 0.5)                               # ride cymbal: ding
        if b % 2 == 1:
            t.put(hat(0.09), b + 2 / 3, 0.4)                   # ...ding-a (swung)
            t.put(hat(0.03), b, 0.3)
        t.put(tone(NOTE[walk[b % 8]], t.beat * 0.9, 5), b, 0.6)            # walking bass
        if b % 4 in (1, 3):
            c = prog[(b // 4) % 4]
            t.put(chord([NOTE[n] for n in CHORDS[c]], t.beat * 0.5, 6), b + 2 / 3, 0.3)
    return t


def shuffle():
    t = Track(96)
    prog = ["Am", "Am", "Dm", "Am", "Em", "Dm", "Am", "Em"]
    for b in range(t.beats):
        c = prog[(b // 4) % 8]
        if b % 2 == 0:
            t.put(kick(), b, 0.9)
        else:
            t.put(snare(), b, 0.6)
        t.put(hat(), b, 0.35)
        t.put(hat(), b + 2 / 3, 0.35)                           # the shuffle
        t.put(tone(NOTE[ROOT[c]], t.beat * 0.6, 5), b, 0.5)
        t.put(tone(NOTE[ROOT[c]], t.beat * 0.3, 6), b + 2 / 3, 0.35)
        if b % 4 == 0:
            t.put(chord([NOTE[n] for n in CHORDS[c]], t.beat * 4, 1.0), b, 0.25)
    return t


def waltz():
    t = Track(150)
    prog = ["C", "F", "G", "C"]
    for b in range(t.beats):
        c = prog[(b // 3) % 4]
        if b % 3 == 0:
            t.put(tone(NOTE[ROOT[c]], t.beat * 1.5, 3), b, 0.8)             # oom
        else:
            t.put(chord([NOTE[n] for n in CHORDS[c]], t.beat * 0.6, 5), b, 0.4)   # pah, pah
    return t


def six8():
    t = Track(60)                                              # the slow beat; splits in three
    prog = ["Am", "F", "C", "G"]
    for b in range(t.beats):
        c = prog[(b // 2) % 4]
        if b % 2 == 0:
            t.put(kick(), b, 0.9)
            t.put(tone(NOTE[ROOT[c]], t.beat * 1.8, 2), b, 0.5)
            t.put(chord([NOTE[n] for n in CHORDS[c]], t.beat * 2, 1.0), b, 0.3)
        else:
            t.put(snare(), b, 0.6)
        for k in range(3):
            t.put(hat(), b + k / 3, 0.4 if k == 0 else 0.25)
    return t


def trap():
    t = Track(140)
    for b in range(t.beats):
        bar = b % 8
        if bar in (0, 5):
            t.put(kick(), b, 0.9)
            t.put(tone(NOTE["A1"] if (b // 8) % 2 == 0 else NOTE["C2"], t.beat * 3, 0.8, (1, 0.15)), b, 0.8)
        if bar == 3:
            t.put(kick(), b + 0.5, 0.7)
        if b % 4 == 2:
            t.put(snare(), b, 0.7)                             # one snare every 4 beats
        t.put(hat(), b, 0.35)
        t.put(hat(), b + 0.5, 0.3)
        if bar == 7:                                           # hi-hat roll
            for k in range(1, 4):
                t.put(hat(0.03), b + 0.5 + k / 8, 0.25)
        if b % 8 == 0:
            t.put(chord([NOTE[n] for n in CHORDS["Am"]], t.beat * 8, 0.3), b, 0.22)
    return t


def nodrums():
    t = Track(80)
    prog = ["C", "Am", "F", "G"]
    for b in range(t.beats):
        if b % 4 == 0:
            c = prog[(b // 4) % 4]
            t.put(chord([NOTE[n] for n in CHORDS[c]], t.beat * 4, 0.5), b, 0.5)
            t.put(tone(NOTE[ROOT[c]], t.beat * 4, 0.6), b, 0.4)
    return t


ALL = {"house": house, "backbeat": backbeat, "swing": swing, "shuffle": shuffle,
       "waltz": waltz, "six8": six8, "trap": trap, "nodrums": nodrums}

if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "pattern_tracks")
    folder.mkdir(parents=True, exist_ok=True)
    for name, make in ALL.items():
        make().save(folder / f"{name}.wav")
        print("wrote", folder / f"{name}.wav")
