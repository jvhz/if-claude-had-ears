#!/usr/bin/env python3
"""
Makes a short test track where we already know the right answers, so we can
check that ears.py reads sound correctly.

The answers:
  tempo   120 beats per minute
  key     A minor
  layout  0:00 quiet pad -> 0:08 hi-hats build -> 0:16 full beat ("the drop")
          -> 0:32 pad only (breakdown) -> 0:40 full beat again -> 0:56 fade out
          -> 1:04 end

Usage:  python make_test_track.py test_track.wav
"""
import sys

import numpy as np
import soundfile as sf

SR = 44100
BPM = 120
BEAT = 60 / BPM
TOTAL = 64.0

A_MINOR = {  # chord -> note frequencies (Hz)
    "Am": [220.00, 261.63, 329.63],
    "Dm": [146.83, 174.61, 220.00],
    "Em": [164.81, 196.00, 246.94],
}
ORDER = ["Am", "Dm", "Am", "Em"]
BASS = {"Am": 55.00, "Dm": 73.42, "Em": 41.20}

rng = np.random.default_rng(7)
t = np.arange(int(TOTAL * SR)) / SR
out = np.zeros_like(t)


def place(sound, at, gain=1.0):
    i = int(at * SR)
    j = min(len(out), i + len(sound))
    if i < len(out):
        out[i:j] += gain * sound[:j - i]


def kick():
    n = int(0.28 * SR)
    x = np.arange(n) / SR
    pitch = 45 + 110 * np.exp(-x * 30)
    return np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-x * 14)


def hat(length=0.05):
    n = int(length * SR)
    x = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = np.diff(noise, prepend=0)          # keep only the bright part
    return noise * np.exp(-x * 90) * 0.5


def snare():
    n = int(0.18 * SR)
    x = np.arange(n) / SR
    return (rng.standard_normal(n) * 0.6 + np.sin(2 * np.pi * 190 * x) * 0.5) * np.exp(-x * 24)


def pad(freqs, length):
    n = int(length * SR)
    x = np.arange(n) / SR
    tone = sum(np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2 * f * x) for f in freqs)
    fade = np.minimum(1, x / 0.4) * np.minimum(1, (length - x) / 0.4)
    return tone / len(freqs) * fade


def bass(freq, length=BEAT * 0.9):
    n = int(length * SR)
    x = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * x) + 0.4 * np.sin(2 * np.pi * 2 * freq * x)) * np.exp(-x * 4)


beats = int(TOTAL / BEAT)
for b in range(beats):
    at = b * BEAT
    chord = ORDER[(b // 4) % 4]
    full = (16 <= at < 32) or (40 <= at < 56)
    build = 8 <= at < 16
    fade_out = at >= 56

    if b % 4 == 0:                                   # one chord every four beats
        level = 0.16 if (at < 8 or 32 <= at < 40) else 0.22
        if fade_out:
            level *= max(0, 1 - (at - 56) / 8)
        place(pad(A_MINOR[chord], BEAT * 4), at, level)

    if build:
        rise = (at - 8) / 8                          # hi-hats get louder and denser
        place(hat(), at, 0.15 + 0.35 * rise)
        place(hat(), at + BEAT / 2, 0.10 + 0.35 * rise)
        if rise > 0.5:
            place(hat(), at + BEAT / 4, 0.25 * rise)
            place(hat(), at + 3 * BEAT / 4, 0.25 * rise)

    if full:
        place(kick(), at, 0.95)
        place(hat(), at + BEAT / 2, 0.45)
        place(hat(), at + BEAT / 4, 0.2)
        place(hat(), at + 3 * BEAT / 4, 0.2)
        if b % 2 == 1:
            place(snare(), at, 0.5)
        place(bass(BASS[chord]), at, 0.5)
        place(bass(BASS[chord], BEAT * 0.4), at + BEAT / 2, 0.3)

out = out / np.abs(out).max() * 0.89
path = sys.argv[1] if len(sys.argv) > 1 else "test_track.wav"
sf.write(path, out.astype(np.float32), SR)
print(f"Wrote {path}: {TOTAL:.0f}s, {BPM} bpm, A minor")
