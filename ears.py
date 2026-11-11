#!/usr/bin/env python3
"""
ears - turn sound into pictures and notes that an AI (or a person) can read.

Give it any audio or video file. It writes a folder containing:

  overview.png   the whole track in one picture (loudness, pitch map,
                 bass/mids/highs, notes)
  zoom_*.png     the same thing, close up, a stretch at a time
  report.md      the track described in plain words and tables
  data.json      every number behind the report (beat times, sections...)

Usage:
  python ears.py song.mp3
  python ears.py film.mp4 --words          # also write down what is said
  python ears.py song.wav --out my_folder
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

SR = 22050          # samples per second we analyse at
HOP = 512           # one analysis step = 512 samples = about 1/43 second
N_FFT = 2048
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BARS = "▁▂▃▄▅▆▇█"

# How strongly each of the 12 notes tends to appear in a major / minor key
# (Krumhansl-Kessler profiles, the standard way to guess a key).
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

BASS_TOP = 250      # Hz. Below this = bass (kick drum, bass guitar, rumble)
HIGH_BOTTOM = 4000  # Hz. Above this = highs (cymbals, hiss, sparkle, "s" sounds)


# ----------------------------------------------------------------- helpers

def mmss(t):
    t = round(max(0.0, float(t)), 1)
    return f"{int(t // 60)}:{t % 60:04.1f}"


def mmss_short(t):
    t = max(0.0, float(t))
    return f"{int(t // 60)}:{int(t % 60):02d}"


def load_audio(src):
    """Read any audio or video file as one channel of sound."""
    import soundfile as sf
    if shutil.which("ffmpeg"):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "audio.wav"
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn",
                   "-ac", "1", "-ar", str(SR), "-f", "wav", str(wav)]
            run = subprocess.run(cmd, capture_output=True, text=True)
            if run.returncode != 0 or not wav.exists():
                sys.exit(f"Could not read sound from {src}:\n{run.stderr.strip()}")
            y, _ = sf.read(str(wav), dtype="float32")
    else:
        import librosa
        y, _ = librosa.load(str(src), sr=SR, mono=True)
    if y.ndim > 1:
        y = y.mean(axis=1)
    if len(y) < SR:
        sys.exit("The file has less than one second of sound.")
    return y


def smooth(x, frames):
    frames = max(1, int(frames))
    if frames == 1:
        return x
    kernel = np.ones(frames) / frames
    return np.convolve(np.pad(x, (frames // 2, frames - 1 - frames // 2), mode="edge"),
                       kernel, mode="valid")


def guess_key(chroma_mean):
    scores = []
    for i in range(12):
        scores.append((np.corrcoef(chroma_mean, np.roll(MAJOR, i))[0, 1], f"{NOTES[i]} major"))
        scores.append((np.corrcoef(chroma_mean, np.roll(MINOR, i))[0, 1], f"{NOTES[i]} minor"))
    scores.sort(reverse=True)
    (best, name), (second, name2) = scores[0], scores[1]
    gap = best - second
    sure = "fairly sure" if gap > 0.08 and best > 0.6 else "a guess" if best > 0.4 else "unclear"
    return {"key": name, "runner_up": name2, "confidence": sure,
            "score": round(float(best), 3), "gap": round(float(gap), 3)}


def level_word(pct):
    return ("very quiet" if pct < 15 else "quiet" if pct < 35 else
            "medium" if pct < 65 else "loud" if pct < 88 else "very loud")


# ---------------------------------------------------------------- analysis

def analyse(y):
    import librosa

    dur = len(y) / SR
    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP))
    P = S ** 2
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=SR, hop_length=HOP)
    fps = SR / HOP

    # Loudness, in decibels below the loudest moment of the track.
    rms = librosa.feature.rms(S=S, frame_length=N_FFT)[0]
    loud_db = librosa.amplitude_to_db(rms, ref=max(rms.max(), 1e-9), top_db=80)
    loud_1s = smooth(loud_db, fps)

    # Pitch map (spectrogram) on a scale close to how ears space pitches.
    mel_db = librosa.power_to_db(
        librosa.feature.melspectrogram(S=P, sr=SR, n_mels=160, fmax=SR / 2),
        ref=np.max, top_db=80)

    # How loud the bass, the mids and the highs each are (same scale as loudness).
    freqs = librosa.fft_frequencies(sr=SR, n_fft=N_FFT)
    top = max(P.sum(axis=0).max(), 1e-12)

    def band(mask):
        return smooth(np.maximum(10 * np.log10(P[mask].sum(axis=0) / top + 1e-12), -80), fps / 2)
    bass = band(freqs < BASS_TOP)
    mids = band((freqs >= BASS_TOP) & (freqs < HIGH_BOTTOM))
    highs = band(freqs >= HIGH_BOTTOM)
    bright = librosa.feature.spectral_centroid(S=S, sr=SR)[0]

    # Split into sustained sound (notes, voices) and hits (drums, clicks).
    H, Pc = librosa.decompose.hpss(S)
    hit_share = (Pc ** 2).sum(axis=0) / ((H ** 2).sum(axis=0) + (Pc ** 2).sum(axis=0) + 1e-12)

    # Which of the 12 notes are sounding.
    chroma = librosa.feature.chroma_cqt(y=librosa.effects.harmonic(y, margin=2),
                                        sr=SR, hop_length=HOP)
    n = min(chroma.shape[1], S.shape[1])
    chroma = chroma[:, :n]

    # Pulse: tempo and the time of every beat.
    onset = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    tempo, repeat = pick_tempo(librosa, onset, fps)
    _, beat_frames = librosa.beat.beat_track(onset_envelope=onset, sr=SR, hop_length=HOP,
                                             bpm=tempo)
    beat_frames = np.asarray(beat_frames, dtype=int)
    if three_against_two(onset, beat_frames):
        # A waltz counted as "two in a bar" instead of three: the real beat is 1.5 times faster.
        tempo *= 1.5
        _, beat_frames = librosa.beat.beat_track(onset_envelope=onset, sr=SR, hop_length=HOP,
                                                 bpm=tempo)
        beat_frames = np.asarray(beat_frames, dtype=int)
    if len(beat_frames) > 8:
        # The tracker can lock onto the off-beat (the hi-hat between kicks). If the
        # bass hits land half a beat away from where it put the beats, slide across.
        # (Measured in plain loudness, so a kick drum outweighs a softer bass note.)
        deep = np.sqrt(P[freqs < 200].sum(axis=0))
        low = np.maximum(0, np.diff(deep, prepend=deep[0]))
        half = int(round(np.median(np.diff(beat_frames)) / 2))

        def weight(frames):
            f = np.clip(frames, 1, len(low) - 2)
            return np.maximum(np.maximum(low[f - 1], low[f]), low[f + 1]).mean()
        if weight(beat_frames + half) > 1.5 * weight(beat_frames):
            beat_frames = beat_frames + half
            beat_frames = beat_frames[beat_frames < len(onset)]
    # Measured on test tracks: hits are reported about one step (23 ms) late, so pull back.
    late = HOP / SR
    beat_times = np.maximum(0, librosa.frames_to_time(beat_frames, sr=SR, hop_length=HOP) - late)
    if len(beat_times) > 8:                      # trust the spacing of the beats we found
        gaps = np.sort(np.diff(beat_times))
        trim = len(gaps) // 10
        tempo = float(60.0 / gaps[trim:len(gaps) - trim].mean())
    hit_frames = librosa.onset.onset_detect(onset_envelope=onset, sr=SR, hop_length=HOP)
    hit_frames = hit_frames[onset[hit_frames] >= 0.7]      # ignore ripples too faint to be hits
    hit_times = np.maximum(0, librosa.frames_to_time(hit_frames, sr=SR, hop_length=HOP) - late)
    if len(beat_frames) > 8:
        on_beat = onset[np.clip(beat_frames, 0, len(onset) - 1)].mean()
        pulse = float(on_beat / (onset.mean() + 1e-9))
        gaps = np.diff(beat_times)
        steady = float(1 - min(1.0, gaps.std() / (gaps.mean() + 1e-9) * 4))
    else:
        pulse, steady = 0.0, 0.0
    hit_rate = len(hit_times) / dur
    has_beat = hit_rate >= 0.5 and repeat >= 0.12
    pulse_word = ("no steady beat" if not has_beat else
                  "strong, steady beat" if repeat >= 0.35 and steady > 0.6 else
                  "clear beat" if repeat >= 0.2 else "loose beat")

    # Sections: stretches of the track that sound alike.
    sections = find_sections(librosa, loud_db, bass, highs, onset, hit_times,
                             chroma, mel_db, times, beat_times, dur, fps)

    # Moments: where the sound suddenly jumps up or falls away.
    moments = find_moments(loud_1s, times, fps)

    # Silent gaps.
    silent = loud_db < -55
    gaps_out, start = [], None
    for i, s in enumerate(silent):
        if s and start is None:
            start = i
        if (not s or i == len(silent) - 1) and start is not None:
            if (i - start) / fps >= 0.4:
                gaps_out.append([round(float(times[start]), 2), round(float(times[i]), 2)])
            start = None

    key = guess_key(chroma.mean(axis=1))
    style = style_clues(librosa, y, beat_times, chroma, fps, loud_1s, has_beat, key, tempo)
    for sec in sections:          # likely chords inside each section
        sec["chords"] = [c for c, t in zip(style["chord_per_beat"], beat_times)
                         if sec["start"] <= t < sec["end"]] if style["chord_per_beat"] else []
        sec["chords"] = top_chords(sec["chords"], 3)

    return {
        "duration": dur, "times": times, "fps": fps,
        "loud_db": loud_db, "loud_1s": loud_1s, "mel_db": mel_db,
        "bass": bass, "mids": mids, "highs": highs, "bright": bright,
        "hit_share": hit_share, "hit_times": hit_times, "chroma": chroma, "onset": onset,
        "tempo": tempo, "beat_times": beat_times, "pulse": pulse,
        "steady": steady, "pulse_word": pulse_word, "has_beat": has_beat,
        "repeat": repeat,
        "key": key, "style": style,
        "sections": sections, "moments": moments, "silences": gaps_out,
        "y": y,
    }


def three_against_two(onset, beat_frames):
    """True when hits fall a third of the way through one beat and two thirds of the way
    through the next, turn and turn about. That pattern means the music is in three and
    the beat was found at two-thirds of its real speed."""
    if len(beat_frames) < 12:
        return False
    x = np.arange(len(onset))
    f0, f1 = beat_frames[:-1].astype(float), beat_frames[1:].astype(float)

    def at(phase):
        mid = f0 + (f1 - f0) * phase
        return np.max([np.interp(mid + k, x, onset) for k in (-1, 0, 1)], axis=0)
    on, third, half, two_thirds = at(0.0), at(1 / 3), at(0.5), at(2 / 3)
    if min(third.mean(), two_thirds.mean()) < 0.25 * on.mean():
        return False
    if max(third.mean(), two_thirds.mean()) < 1.5 * half.mean():
        return False

    def takes_turns(v):               # strong on every other beat, weak on the ones between
        return abs(v[0::2].mean() - v[1::2].mean()) / (v.mean() + 1e-9)
    return max(takes_turns(third), takes_turns(two_thirds)) > 0.8


def pick_tempo(librosa, onset, fps):
    """Try every tempo from 50 to 210 and keep the one whose beat, 2 beats,
    3 beats and 4 beats all land on repeating hits. Leans towards 80-160,
    where most music is felt."""
    env = onset - onset.mean()
    ac = librosa.autocorrelate(env, max_size=int(fps * 10))
    ac = ac / (ac[0] + 1e-9)
    lags = np.arange(len(ac))
    best, best_score = 120.0, -np.inf
    for bpm in np.arange(50, 210.25, 0.25):
        period = fps * 60.0 / bpm
        pts = period * np.arange(1, 5)
        if pts[-1] >= len(ac) - 1:
            continue
        score = float(np.interp(pts, lags, ac).mean())
        score *= np.exp(-0.5 * (np.log2(bpm / 112.0) / 0.7) ** 2)
        if score > best_score:
            best, best_score = float(bpm), score
    period = fps * 60.0 / best
    repeat = float(np.interp(period * np.arange(1, 5), lags, ac).mean())
    return best, repeat          # repeat: 0 = hits never repeat, 1 = perfectly regular


FINE = 256          # a finer time step for rhythm detail: about 1/86 second


def top_chords(seq, most):
    if not seq:
        return []
    names, counts = np.unique(seq, return_counts=True)
    order = np.argsort(counts)[::-1]
    return [str(names[i]) for i in order[:most] if counts[i] / len(seq) >= 0.1]


def style_clues(librosa, y, beat_times, chroma, fps, loud_1s, has_beat, key, tempo):
    """Clues that tell one style of music from another: how the beat is built,
    which chords are used, and what the sound is made of."""
    P = np.abs(librosa.stft(y, n_fft=1024, hop_length=FINE)) ** 2
    freqs = librosa.fft_frequencies(sr=SR, n_fft=1024)
    energy = P.sum(axis=0)
    loud = energy > np.median(energy)
    live = loud_1s[loud_1s > -50]
    out = {
        "deep_bass_share": round(float(P[freqs < 70][:, loud].sum() / (P[:, loud].sum() + 1e-12)), 3),
        "loudness_swing_db": round(float(np.percentile(live, 95) - np.percentile(live, 10)), 1)
        if len(live) else 0.0,
        "chord_per_beat": [],
    }

    # How strongly the sound jumps up from one moment to the next, in four pitch ranges.
    mel = librosa.feature.melspectrogram(S=P, sr=SR, n_mels=64, fmax=SR / 2)
    mf = librosa.mel_frequencies(n_mels=64, fmax=SR / 2)
    squashed = np.log1p(1e5 * mel / (mel.max() + 1e-12))     # anything fainter than about -50 dB fades out
    jump = np.maximum(0, np.diff(squashed, axis=1, prepend=squashed[:, :1]))
    full, low = jump.mean(axis=0), jump[mf < 150].mean(axis=0)
    high, body = jump[mf >= 1500].mean(axis=0), jump[mf < 2000].mean(axis=0)
    ffps = SR / FINE

    # Are the hits noise (drums, shakers) or notes (piano, guitar)? Look at the strongest ones.
    peaks = librosa.util.peak_pick(high, pre_max=4, post_max=4, pre_avg=20, post_avg=20,
                                   delta=0.3 * high.std(), wait=6)
    peaks = peaks[high[peaks] >= 0.3]                 # ignore ripples far too faint to be hits
    if len(peaks) >= 8:
        strong = peaks[np.argsort(high[peaks])[::-1][:max(8, len(peaks) // 2)]]
        strong = strong[(strong > 2) & (strong < P.shape[1] - 3)]
        band = (freqs >= 1000) & (freqs <= 9000)
        rise = np.maximum(0, P[band][:, strong + 1] - P[band][:, strong - 2]) + 1e-12
        flat = np.exp(np.log(rise).mean(axis=0)) / rise.mean(axis=0)
        out["hit_noisiness"] = round(float(np.median(flat)), 3)
    else:
        out["hit_noisiness"] = 0.0

    bt = np.asarray(beat_times, dtype=float)
    if not has_beat or len(bt) < 12:
        out["rhythm"] = None
        return out
    gap = float(np.median(np.diff(bt)))
    K = 24                                    # each beat cut into 24 slices

    def profile(env, shift=0.0):
        rows = [np.interp((t0 + shift + (t1 - t0) * np.arange(K) / K) * ffps,
                          np.arange(len(env)), env) for t0, t1 in zip(bt[:-1], bt[1:])]
        return np.mean(rows, axis=0)

    # Line the beat grid up with where the hits really are.
    first = profile(full)
    near = [-2, -1, 0, 1, 2]
    shift = near[int(np.argmax([first[k % K] for k in near]))] * gap / K
    prof = profile(full, shift)
    on = max(prof[0], 1e-9)
    rel = prof / on

    def at(env, width=0.03):
        w = int(round(width * ffps))
        f = np.clip(np.round((bt + shift) * ffps).astype(int), w, len(env) - w - 1)
        return np.max([env[f + k] for k in range(-w, w + 1)], axis=0)

    L, Hh, B = at(low), at(high), at(body)
    # Judge the drum pattern on the fuller half of the track, so intros and breakdowns don't blur it.
    level = np.interp(bt, np.arange(len(loud_1s)) / fps, smooth(loud_1s, fps * 4))
    busy = level >= np.median(level)

    # What happens between two beats: straight halves, swing, or threes.
    between = int(np.argmax(rel[10:19])) + 10
    spot = between / K
    half, third1, third2, quarter3 = rel[12], rel[8], rel[16], rel[18]
    if third1 > 0.3 and third2 > 0.3 and max(third1, third2) > 1.3 * half:
        feel = "threes"
    elif rel[between] > 0.25 and 0.56 <= spot <= 0.72 and rel[between] > 1.3 * half \
            and third2 >= quarter3:
        feel = "swung"
    elif max(half, rel[6], quarter3) > 0.2:
        feel = "straight"
    else:
        feel = "on the beat only"

    # Beats per bar: do the accents and chord changes come round every 3 beats or every 4?
    bf = np.clip((bt * fps).astype(int), 0, chroma.shape[1] - 1)
    per_beat = []
    for f0, f1 in zip(bf[:-1], bf[1:]):
        c = chroma[:, f0:max(f1, f0 + 1)].mean(axis=1)
        per_beat.append(c / (np.linalg.norm(c) + 1e-9))
    per_beat = np.array(per_beat)
    change = np.r_[0, 1 - (per_beat[1:] * per_beat[:-1]).sum(axis=1)]

    def comes_round(x, lag):
        x = x - x.mean()
        return float(np.dot(x[:-lag], x[lag:]) / (np.dot(x, x) + 1e-9))
    feats = [x for x in (L[:-1], Hh[:-1], B[:-1], change)
             if x.std() > 0.2 * (x.mean() + 1e-9)]          # skip anything that is the same on every beat
    in3 = float(np.mean([comes_round(x, 3) for x in feats])) if feats else 0.0
    in4 = float(np.mean([max(comes_round(x, 2), comes_round(x, 4)) for x in feats])) if feats else 0.0
    bar = "three" if in3 > in4 + 0.1 and in3 > 0.12 else "four" if in4 > 0.05 else "unclear"

    # Low hits (kick drum or bass note): on how many beats, and how many per beat.
    strong_low = np.percentile(low, 99.5)
    need = max(0.4 * np.percentile(L[busy], 90), 0.2 * strong_low)
    low_pk = librosa.util.peak_pick(low, pre_max=4, post_max=4, pre_avg=20, post_avg=20,
                                    delta=0.2 * strong_low, wait=8)
    # Bright hits (snare, clap): every 2nd beat is a backbeat, every 4th is half-time.
    first_busy = int(np.argmax(busy))
    Hb = np.where(busy, Hh, np.nan)[first_busy:]

    def phases(x, p):
        m = np.array([np.nanmean(x[k::p]) if np.isfinite(x[k::p]).any() else 0.0 for k in range(p)])
        return np.sort(m / (m.sum() + 1e-9))[::-1]
    two, four = phases(Hb, 2), phases(Hb, 4)
    if out["hit_noisiness"] < 0.03 or np.nanmean(Hb) < 0.02 * (np.nanmean(at(full)) + 1e-9):
        snare = "no drum-like hits"
    elif four[0] > 0.36 and four[0] > 1.6 * four[1]:
        snare = "every fourth beat"
    elif two[0] > 0.58:
        snare = "every second beat"
    else:
        snare = "no pattern found"

    bprof = profile(body, shift)
    off = 1 - float(bprof[[K - 1, 0, 1]].sum() / (bprof.sum() + 1e-9))

    out["rhythm"] = {
        "beats_per_bar": bar, "in3_score": round(in3, 2), "in4_score": round(in4, 2),
        "between_beats": feel, "swing_spot": round(spot, 2),
        "low_hit_on_beats": round(float((L[busy] > need).mean()), 2),
        "low_hits_per_beat": round(len(low_pk) / len(bt), 2),
        "bright_hit": snare, "bright2": round(float(two[0]), 2), "bright4": round(float(four[0]), 2),
        "off_beat_share": round(off, 2),
        "profile": [round(float(v), 2) for v in rel],
    }

    # Chords: match each beat's notes against the 24 plain major and minor chords.
    shapes, names = [], []
    for i in range(12):
        for tag, steps in (("", (0, 4, 7)), ("m", (0, 3, 7))):
            v = np.zeros(12)
            v[[(i + k) % 12 for k in steps]] = 1 / np.sqrt(3)
            shapes.append(v)
            names.append(NOTES[i] + tag)
    seq = (np.array(shapes) @ per_beat.T).argmax(axis=0)
    for i in range(1, len(seq) - 1):          # drop one-beat blips
        if seq[i - 1] == seq[i + 1] != seq[i]:
            seq[i] = seq[i - 1]
    out["chord_per_beat"] = [names[k] for k in seq]
    ids, counts = np.unique(seq, return_counts=True)
    order = np.argsort(counts)[::-1]
    out["chords"] = [{"chord": names[ids[i]], "share": round(float(counts[i] / len(seq)), 2)}
                     for i in order[:5] if counts[i] / len(seq) >= 0.08]
    out["chord_changes_per_4_beats"] = round(float((np.diff(seq) != 0).mean() * 4), 2)

    # Major or minor: let the chords overrule the note count when they clearly disagree.
    tonic, mode = key["key"].split()
    share = {c["chord"]: c["share"] for c in out["chords"]}
    if mode == "major" and share.get(tonic + "m", 0) > share.get(tonic, 0) + 0.1:
        key["key"], key["confidence"] = f"{tonic} minor", "a guess"
    elif mode == "minor" and share.get(tonic, 0) > share.get(tonic + "m", 0) + 0.1:
        key["key"], key["confidence"] = f"{tonic} major", "a guess"
    return out


def find_sections(librosa, loud_db, bass, highs, onset, hit_times, chroma, mel_db,
                  times, beat_times, dur, fps):
    from scipy.ndimage import median_filter

    n = min(len(loud_db), chroma.shape[1], mel_db.shape[1], len(onset))
    step = max(1, int(fps / 2))                       # two readings per second
    idx = np.arange(0, n - step + 1, step)
    if len(idx) < 8:
        bounds = [0.0, dur]
    else:
        def block(a):
            return np.array([a[..., i:i + step].mean(axis=-1) for i in idx]).T
        feats = np.vstack([
            block(loud_db[:n])[None, :] / 6.0,
            block(mel_db[:, :n])[::8] / 12.0,
            block(chroma[:, :n]) * 0.5,
            block(bass[:n])[None, :] / 6.0,
            block(highs[:n])[None, :] / 6.0,
            block(onset[:n])[None, :] / (onset.std() + 1e-9),
        ])
        feats = median_filter(feats, size=(1, 9))
        k = int(np.clip(round(dur / 6), 2, 24))   # more candidates than needed; merged below
        k = min(k, feats.shape[1] // 4)
        cuts = librosa.segment.agglomerative(feats, k) if k >= 2 else np.array([0])
        bounds = sorted(set([0.0] + [float(times[idx[c]]) for c in cuts if c > 0] + [dur]))
        # Move each cut to the nearest beat.
        if len(beat_times) > 4:
            bounds = [bounds[0]] + [
                float(beat_times[np.argmin(np.abs(beat_times - b))])
                if np.min(np.abs(beat_times - b)) < 0.6 else b
                for b in bounds[1:-1]] + [bounds[-1]]
        bounds = sorted(set(bounds))

    # Join neighbours that sound the same, so every cut left is one you would hear.
    def stats(a, b):
        m = (times[:n] >= a) & (times[:n] < b)
        hits = ((hit_times >= a) & (hit_times < b)).sum() / max(b - a, 1e-9)
        if not m.any():
            return np.zeros(4)
        # one unit = a difference you would clearly hear
        return np.array([loud_db[:n][m].mean() / 5.0, bass[:n][m].mean() / 8.0,
                         highs[:n][m].mean() / 10.0, hits / 3.0])

    def jump(b):                                  # how big the change is right at a cut
        return float(np.abs(stats(max(0, b - 2.5), b) - stats(b, min(dur, b + 2.5))).sum())
    while len(bounds) > 2:
        st = [stats(a, b) for a, b in zip(bounds[:-1], bounds[1:])]
        diffs = [float(np.abs(st[i] - st[i + 1]).max()) for i in range(len(st) - 1)]
        lengths = np.diff(bounds)
        short = int(np.argmin(lengths))
        if lengths[short] < 3.0:                  # a sliver: keep only its stronger edge
            edges = [j for j in (short, short + 1) if 0 < j < len(bounds) - 1]
            i = min(edges, key=lambda j: jump(bounds[j])) - 1
        else:
            i = int(np.argmin(diffs))
            if diffs[i] >= 1.0:
                break
        del bounds[i + 1]

    # Words like "loud" and "full bass" are relative to the rest of this track.
    bass_ref, highs_ref = np.percentile(bass[:n], 95), np.percentile(highs[:n], 95)
    out = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        m = (times[:n] >= a) & (times[:n] < b)
        if not m.any():
            continue
        lvl = float(np.mean(loud_db[:n][m]))
        pct = float((loud_db[:n] < lvl).mean() * 100)
        cm = chroma[:, :n][:, m].mean(axis=1)
        top = [NOTES[i] for i in np.argsort(cm)[::-1][:3]]
        out.append({
            "start": round(a, 2), "end": round(b, 2), "length": round(b - a, 2),
            "loudness_db": round(lvl, 1), "level": level_word(pct),
            "bass_db": round(float(bass[:n][m].mean()), 1),
            "highs_db": round(float(highs[:n][m].mean()), 1),
            "hits_per_second": round(float(((hit_times >= a) & (hit_times < b)).sum() / (b - a)), 1),
            "main_notes": top,
            "_bass_gap": float(bass[:n][m].mean() - bass_ref) if bass_ref > -35 else -99.0,
            "_highs_gap": float(highs[:n][m].mean() - highs_ref) if highs_ref > -45 else -99.0,
        })
    for i, s in enumerate(out):
        s["name"] = chr(ord("A") + i) if i < 26 else f"S{i + 1}"
        s["feel"] = describe(s)
        del s["_bass_gap"], s["_highs_gap"]
    return out


def describe(s):
    bits = [s["level"]]
    bits.append("full bass" if s["_bass_gap"] > -6 else
                "some bass" if s["_bass_gap"] > -15 else "little bass")
    bits.append("bright highs" if s["_highs_gap"] > -6 else
                "some highs" if s["_highs_gap"] > -18 else "no highs")
    bits.append("busy rhythm" if s["hits_per_second"] >= 3 else
                "steady hits" if s["hits_per_second"] >= 1 else "smooth, few hits")
    return ", ".join(bits)


def find_moments(loud_1s, times, fps):
    """Sudden rises (things kicking in) and sudden falls (things dropping out)."""
    lag = int(fps * 1.0)
    if len(loud_1s) <= lag * 2:
        return []
    change = loud_1s[lag:] - loud_1s[:-lag]
    found = []
    for sign, kind in ((1, "kicks in"), (-1, "drops out")):
        c = change * sign
        order = np.argsort(c)[::-1]
        picked = []
        for i in order:
            if c[i] < 8:
                break
            where = times[i + lag // 2]
            if where < 1.0 or where > times[-1] - 1.0:
                continue
            if all(abs(i - j) > fps * 3 for j in picked):
                picked.append(i)
            if len(picked) >= 8:
                break
        for i in picked:
            found.append({"time": round(float(times[i + lag // 2]), 2), "what": kind,
                          "change_db": round(float(change[i]), 1)})
    return sorted(found, key=lambda m: m["time"])


# ------------------------------------------------------------------ words

def transcribe(src, model_name):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  (skipping words: run `pip install faster-whisper` to switch this on)")
        return None
    print(f"  listening for words (model: {model_name})...")
    try:
        model = WhisperModel(model_name, device="auto", compute_type="int8")
        segments, info = model.transcribe(str(src), vad_filter=True)
        lines = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
                 for s in segments]
    except Exception as err:        # usually: the speech model could not be downloaded
        print(f"  (skipping words: {type(err).__name__}: {str(err)[:120]})")
        return None
    return {"language": info.language, "lines": lines}


# --------------------------------------------------------------- pictures

def draw(a, t0, t1, path, title, wide=16.0, show_beats=True):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    ink, soft, paper = "#1b1b1f", "#8a8a93", "#fbfaf7"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": soft, "axes.linewidth": 0.5,
                         "xtick.color": soft, "ytick.color": soft, "text.color": ink,
                         "axes.labelcolor": ink, "font.family": "DejaVu Sans"})
    fig, axes = plt.subplots(4, 1, figsize=(wide, 10.5), sharex=True, facecolor=paper,
                             gridspec_kw={"height_ratios": [1.5, 2.2, 1.1, 1.5], "hspace": 0.28})
    times, fps = a["times"], a["fps"]
    m = (times >= t0) & (times <= t1)
    tt = times[m]

    # 1. Loudness: the grey shape is the raw wave, the line is loudness.
    ax = axes[0]
    y = a["y"]
    i0, i1 = int(t0 * SR), min(len(y), int(t1 * SR))
    cols = 2400
    seg = y[i0:i1]
    if len(seg) >= cols:
        chunk = len(seg) // cols
        seg = seg[:chunk * cols].reshape(cols, chunk)
        peak = np.abs(seg).max(axis=1)
        wt = t0 + np.arange(cols) * chunk / SR
    else:
        peak, wt = np.abs(seg), t0 + np.arange(len(seg)) / SR
    scale = max(np.abs(y).max(), 1e-9)
    ax.fill_between(wt, -80 + 80 * peak / scale, -80, color="#cfcfd6", linewidth=0)
    ax.plot(tt, a["loud_1s"][m], color="#d1452f", linewidth=0.9)
    ax.set_ylim(-80, 3)
    ax.set_ylabel("LOUDNESS\n(0 = loudest)")
    for s in a["sections"]:
        if s["end"] <= t0 or s["start"] >= t1:
            continue
        if s["start"] > t0:
            for axx in axes:
                axx.axvline(s["start"], color=ink, linewidth=0.5, linestyle=(0, (4, 3)))
        x = max(s["start"], t0)
        room = (min(s["end"], t1) - x) / (t1 - t0)       # narrow stretch: letter only
        label = f"{s['name']}  {s['level']}" if room > 0.09 else s["name"]
        ax.text(x + (t1 - t0) * 0.004, 1.0, label, fontsize=8.5,
                va="top", ha="left", weight="bold")
    for mo in a["moments"]:
        if t0 <= mo["time"] <= t1:
            up = mo["what"] == "kicks in"
            ax.annotate("▲" if up else "▼", (mo["time"], -74), ha="center", fontsize=8,
                        color="#1f7a4d" if up else "#3157b8")
    if show_beats and a["has_beat"] and (t1 - t0) <= 45:
        for i, b in enumerate(a["beat_times"]):
            if t0 <= b <= t1:
                ax.axvline(b, ymin=0, ymax=0.06, color=ink, linewidth=0.5)
                if i % 4 == 0:
                    ax.text(b, -67, str(i + 1), fontsize=6.5, ha="center", color=soft)

    # 2. Pitch map: low sounds at the bottom, high at the top, brighter = stronger.
    import librosa
    import librosa.display
    ax = axes[1]
    f0, f1 = int(t0 * fps), min(a["mel_db"].shape[1], int(t1 * fps) + 1)
    librosa.display.specshow(a["mel_db"][:, f0:f1], sr=SR, hop_length=HOP, x_coords=times[f0:f1],
                             y_axis="mel", fmax=SR / 2, cmap="magma", ax=ax, vmin=-80, vmax=0)
    ax.set_ylabel("PITCH MAP\n(Hz, low to high)")
    ax.set_xlabel("")
    for hz, name in ((BASS_TOP, "bass below"), (HIGH_BOTTOM, "highs above")):
        ax.axhline(hz, color="#ffffff", linewidth=0.4, linestyle=(0, (2, 4)))
        ax.text(t0 + (t1 - t0) * 0.004, hz * 1.08, name, color="#ffffff", fontsize=7, va="bottom")

    # 3. Balance of bass / mids / highs.
    ax = axes[2]
    for arr, name, col in ((a["bass"], "bass", "#2b3a67"), (a["mids"], "mids", "#b8860b"),
                           (a["highs"], "highs", "#c2410c")):
        ax.plot(tt, arr[m], color=col, linewidth=0.8, label=name)
    ax.set_ylim(-80, 3)
    ax.set_yticks([-60, -30, 0])
    ax.set_ylabel("BASS / MIDS / HIGHS\n(how loud each is)")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), ncols=3, frameon=False,
              fontsize=7.5, handlelength=1.2, borderaxespad=0.2)

    # 4. Notes: which of the 12 notes are sounding.
    ax = axes[3]
    c0, c1 = int(t0 * fps), min(a["chroma"].shape[1], int(t1 * fps) + 1)
    if c1 > c0 + 1:
        ax.imshow(a["chroma"][:, c0:c1], aspect="auto", origin="lower", cmap="Greys",
                  extent=[times[c0], times[c1 - 1], -0.5, 11.5], vmin=0, vmax=1,
                  interpolation="nearest")
    ax.set_yticks(range(12))
    ax.set_yticklabels(NOTES, fontsize=7)
    ax.set_ylabel("NOTES\n(darker = stronger)")
    ax.set_xlabel("time (minutes:seconds)")

    axes[-1].xaxis.set_major_locator(MaxNLocator(nbins=20, steps=[1, 2, 5, 10]))
    axes[-1].xaxis.set_major_formatter(FuncFormatter(lambda v, _: mmss_short(v)))
    for axx in axes:
        axx.set_xlim(t0, t1)
        axx.tick_params(length=2, width=0.5)
        axx.yaxis.label.set_size(7.5)
    fig.suptitle(title, x=0.125, y=0.925, ha="left", fontsize=12, weight="bold")
    fig.savefig(path, dpi=150, facecolor=paper, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)


# ----------------------------------------------------------------- report

def strip(values, lo, hi):
    v = np.clip((np.asarray(values) - lo) / (hi - lo + 1e-9), 0, 0.999)
    return "".join(BARS[int(x * len(BARS))] for x in v)


def per_second(arr, times, dur, how=np.mean):
    out = []
    for s in range(int(np.ceil(dur))):
        m = (times >= s) & (times < s + 1)
        out.append(float(how(arr[:len(times)][m])) if m.any() else 0.0)
    return np.array(out)


def style_words(a):
    """Turn the style measurements into plain sentences, and list the kinds of
    music whose usual rhythm matches. Returns (clue lines, style suggestions)."""
    st, r, tempo = a["style"], a["style"]["rhythm"], a["tempo"]
    lines, fits = [], []
    drums = st["hit_noisiness"] >= 0.03
    deep = st["deep_bass_share"]
    swing_db = st["loudness_swing_db"]

    if r is None:
        lines.append("**Beat:** none to count along to, so there is no drum pattern to read.")
    else:
        bar = r["beats_per_bar"]
        lines.append({"three": "**Count:** in three (ONE-two-three), like a waltz or a 6/8 song.",
                      "four": "**Count:** in four (or two), like most pop, rock, hip hop and dance music.",
                      "unclear": "**Count:** unclear whether it is in three or four."}[bar])
        feel = r["between_beats"]
        lines.append({
            "straight": "**Between the beats:** straight. The in-between notes sit exactly halfway.",
            "swung": f"**Between the beats:** swung. The in-between note comes late "
                     f"(about {r['swing_spot'] * 100:.0f}% of the way to the next beat), the long-short "
                     f"lilt of jazz and blues shuffles.",
            "threes": "**Between the beats:** each beat splits into three (triplets, as in 6/8 or 12/8).",
            "on the beat only": "**Between the beats:** very little. Almost everything lands on the beat.",
        }[feel])
        low = r["low_hit_on_beats"]
        lines.append("**Low hits (kick drum or bass note):** " + (
            "on every beat." if low >= 0.85 else
            "on roughly half the beats." if low >= 0.4 else
            "sparse, well under one per beat."))
        hit = r["bright_hit"]
        lines.append("**Bright hits (snare or clap):** " + {
            "every second beat": "on every second beat. This is a backbeat, the spine of pop, rock, funk and hip hop.",
            "every fourth beat": "on every fourth beat only. A half-time feel, typical of trap, drill and dubstep.",
            "no pattern found": "drum-like hits are there, but with no regular two-or-four pattern.",
            "no drum-like hits": "none that sound like a drum kit. The hits are notes (piano, guitar, strings, plucks).",
        }[hit])
        if st.get("chords"):
            names = ", ".join(f"{c['chord']} ({c['share'] * 100:.0f}%)" for c in st["chords"])
            per = st["chord_changes_per_4_beats"]
            pace = ("it stays on one chord almost throughout" if st["chords"][0]["share"] >= 0.8 else
                    "changing about once every four beats" if 0.6 <= per <= 1.5 else
                    "changing slowly" if per < 0.6 else "changing often, most beats or every other beat")
            lines.append(f"**Chords (best match to plain major/minor):** {names}; {pace}.")
    lines.append("**Deep bass (below 70 Hz):** " + (
        f"very heavy ({deep * 100:.0f}% of the sound), like 808-style sub bass." if deep >= 0.5 else
        f"almost none ({deep * 100:.0f}%)." if deep < 0.03 else f"present ({deep * 100:.0f}% of the sound)."))
    lines.append("**Loud-to-quiet range:** " + (
        f"wide ({swing_db:.0f} dB). It breathes, like acoustic, orchestral or film music, or a track with big drops."
        if swing_db >= 12 else
        f"narrow ({swing_db:.0f} dB). Evenly loud throughout, typical of modern produced tracks and loops."
        if swing_db < 6 else f"moderate ({swing_db:.0f} dB)."))

    # ---- which kinds of music usually have this rhythm
    def near(lo, hi):                       # the tempo, or its double or half, sits in this range
        for t, how in ((tempo, ""), (tempo * 2, " counted double-time"), (tempo / 2, " counted half-time")):
            if lo <= t <= hi:
                return f"{t:.0f} bpm{how}"
        return None

    if r is None:
        if not drums:
            fits.append(("Free-tempo music: classical, orchestral, solo instrument or film score",
                         "no steady beat and no drum kit"))
            fits.append(("Or not music at all: speech, ambience or sound design", "no steady beat"))
        else:
            fits.append(("Free-time percussion, sound effects or speech over noise", "hits but no steady beat"))
        return lines, fits
    bar, feel, hit, low = r["beats_per_bar"], r["between_beats"], r["bright_hit"], r["low_hit_on_beats"]
    if bar == "three":
        fits.append(("Waltz, or a 6/8 ballad (soul, R&B, folk, film score)", "it counts in three"))
        if not drums:
            fits.append(("Classical dance piece (waltz, minuet)", "in three with no drum kit"))
    if feel == "swung":
        jazz, blues = near(110, 260), near(60, 130)
        pair = [("Swing jazz", f"swung notes at {jazz}") if jazz else None,
                ("Blues shuffle, or hip hop / lo-fi with a swung beat", f"swung notes at {blues}")
                if blues else None]
        if 60 <= tempo < 110:                # at slower speeds the shuffle is the likelier reading
            pair.reverse()
        fits += [x for x in pair if x]
    if feel == "threes" and bar != "three":
        fits.append(("12/8 blues, doo-wop or slow soul ballad", "each beat splits into three"))
    if drums and bar != "three" and feel in ("straight", "on the beat only"):
        if low >= 0.85 and hit != "every fourth beat":
            why = "a low hit on every beat (four-on-the-floor), straight"
            for lo, hi, name in ((84, 108, "Reggaeton, dancehall or slow disco"),
                                 (108, 119, "Disco, funk or nu-disco"),
                                 (119, 132, "House, dance-pop or disco"),
                                 (132, 152, "Techno, trance or big-room EDM"),
                                 (152, 200, "Hard dance or hardstyle")):
                if lo <= tempo < hi:
                    fits.append((name, f"{why}, {tempo:.0f} bpm"))
                elif r["low_hits_per_beat"] >= 1.3 and lo <= tempo * 2 < hi:
                    fits.append((name, f"two low hits per counted beat, so it may really run at "
                                       f"{tempo * 2:.0f} bpm"))
        if hit == "every fourth beat":
            extra = ", with very heavy deep bass" if deep >= 0.5 else ""
            fits.append(("Trap or drill (or dubstep near 140)", f"snare only every fourth beat{extra}, "
                         f"{tempo:.0f} bpm felt as {tempo / 2:.0f}"))
        if hit == "every second beat" and low < 0.85:
            why = "kick and snare taking turns (a backbeat), straight"
            for lo, hi, name in ((55, 85, "Slow hip hop, R&B, soul or a ballad"),
                                 (85, 105, "Hip hop, R&B, reggae or mid-tempo pop"),
                                 (105, 135, "Pop, rock, funk or country"),
                                 (135, 165, "Rock, indie, punk-pop, or drum-and-bass counted half-time"),
                                 (165, 215, "Drum and bass, punk or metal")):
                if lo <= tempo < hi:
                    fits.append((name, f"{why}, {tempo:.0f} bpm"))
        if hit == "no pattern found" and not fits:
            fits.append(("Percussion-led or broken-beat music", "drum hits without a regular backbeat"))
    if not drums and bar != "three" and feel != "swung":
        fits.append(("Acoustic or classical piece without a drum kit (piano, guitar, strings), or folk",
                     "a steady beat carried by notes, not drums"))
    return lines, fits


def chord_timeline(a):
    """Each chord change as (time, chord), from the per-beat chord matches."""
    seq, bt = a["style"]["chord_per_beat"], a["beat_times"]
    out = []
    for c, t in zip(seq, bt):
        if not out or out[-1][1] != c:
            out.append((round(float(t), 2), c))
    return out


def write_report(a, src, out, words, zooms):
    dur, tempo, key = a["duration"], a["tempo"], a["key"]
    n = min(len(a["times"]), len(a["loud_db"]))
    t = a["times"][:n]
    loud_s = per_second(a["loud_db"], t, dur)
    bass_s = per_second(a["bass"], t, dur)
    high_s = per_second(a["highs"], t, dur)
    hits_s = np.array([float(((a["hit_times"] >= s) & (a["hit_times"] < s + 1)).sum())
                       for s in range(int(np.ceil(dur)))])
    bright = float(np.median(a["bright"]))
    tone = "bright" if bright > 2800 else "dark, warm" if bright < 1200 else "mid-toned"

    L = [f"# Listening notes: {Path(src).name}", ""]
    L += ["## At a glance", "",
          f"- **Length:** {mmss(dur)} ({dur:.1f} seconds)",
          (f"- **Tempo:** about {tempo:.0f} beats per minute, {a['pulse_word']}"
           f" (could also be felt at {tempo / 2:.0f} or {tempo * 2:.0f})" if a["has_beat"] else
           f"- **Tempo:** no steady beat found (speech, ambience or free-flowing music). "
           f"Forced guess {tempo:.0f} bpm, not reliable"),
          f"- **Key:** {key['key']} ({key['confidence']}; next best guess {key['runner_up']})",
          f"- **Beats found:** {len(a['beat_times'])}",
          f"- **Overall tone:** {tone}",
          f"- **Rhythm:** about {len(a['hit_times']) / dur:.1f} hits per second on average "
          f"(drum hits, plucks, any sound with a sharp start)",
          f"- **Loudness range:** quietest second {loud_s.min():.0f} dB, "
          f"loudest second {loud_s.max():.0f} dB (0 = the loudest moment in the track)", ""]

    clues, fits = style_words(a)
    L += ["## Style clues", "",
          "What the rhythm, chords and sound are built from. These are the things that "
          "separate one kind of music from another.", ""]
    L += [f"- {c}" for c in clues]
    L += ["", "**Kinds of music that usually have this rhythm:**", ""]
    L += [f"- {name} ({why})" for name, why in fits] or ["- Nothing in the built-in list matches cleanly."]
    L += ["", "Treat these as a shortlist, not a verdict. Rhythm narrows the field, but the instruments "
          "and the voice decide the genre, and this tool cannot name those. `MUSIC.md` explains "
          "how to reason from clues to a style.", ""]

    L += ["## Sections", "",
          "Stretches that sound alike. Letters are just labels in order, not verse/chorus.", "",
          "| Section | From | To | Length | Feel | Main notes | Likely chords |",
          "|---|---|---|---|---|---|---|"]
    for s in a["sections"]:
        L.append(f"| {s['name']} | {mmss(s['start'])} | {mmss(s['end'])} | {s['length']:.1f}s "
                 f"| {s['feel']} | {' '.join(s['main_notes'])} | {' '.join(s.get('chords', [])) or '-'} |")
    L.append("")

    L += ["## Moments", ""]
    if a["moments"]:
        L += ["Where the sound suddenly jumps up or falls away. Good places to cut on.", ""]
        for mo in a["moments"]:
            L.append(f"- **{mmss(mo['time'])}** sound {mo['what']} ({mo['change_db']:+.0f} dB)")
    else:
        L.append("No sudden jumps or drops: the level moves gradually.")
    L.append("")
    if a["silences"]:
        L += ["## Silences", ""] + [f"- {mmss(x)} to {mmss(y)}" for x, y in a["silences"]] + [""]

    L += ["## Second-by-second strips", "",
          "One character per second. Taller bar = more of that thing.", "", "```"]
    row = 60
    for s0 in range(0, len(loud_s), row):
        s1 = min(len(loud_s), s0 + row)
        L.append(f"{mmss_short(s0):>5} to {mmss_short(s1):<5}")
        L.append(f"  loudness  {strip(loud_s[s0:s1], -50, 0)}")
        L.append(f"  bass      {strip(bass_s[s0:s1], bass_s.max() - 40, bass_s.max())}")
        L.append(f"  highs     {strip(high_s[s0:s1], high_s.max() - 40, high_s.max())}")
        L.append(f"  hits      {strip(hits_s[s0:s1], 0, 8)}")
        L.append("")
    L += ["```", ""]

    if words:
        L += ["## Words", "", f"Language heard: {words['language']}", ""]
        L += [f"- **{mmss(w['start'])}** {w['text']}" for w in words["lines"]] or ["No words found."]
        L.append("")

    changes = chord_timeline(a)
    if changes:
        L += ["## Chord changes", "",
              "Best match to a plain major or minor chord at each change (m = minor). Richer chords "
              "(sevenths, ninths) show up as their nearest plain chord, and drums can blur the reading.",
              "", "```"]
        cells = [f"{mmss_short(t)} {c}" for t, c in changes[:160]]
        L += ["   ".join(cells[i:i + 8]) for i in range(0, len(cells), 8)]
        if len(changes) > 160:
            L.append(f"... and {len(changes) - 160} more")
        L += ["```", ""]

    L += ["## Beat times", "",
          "Seconds from the start. Every beat, in order." if a["has_beat"] else
          "No steady beat was found, so treat these as rough pulses only.", "", "```"]
    bt = [f"{b:.2f}" for b in a["beat_times"]]
    L += [" ".join(bt[i:i + 12]) for i in range(0, len(bt), 12)] + ["```", ""]

    L += ["## Pictures", "", "- `overview.png` the whole track"]
    L += [f"- `{z['file']}` close-up, {mmss_short(z['from'])} to {mmss_short(z['to'])}" for z in zooms]
    L += ["", "## What this cannot tell you", "",
          "These notes describe structure, energy, pitch, timing and rhythm style. They do not say "
          "whether the track is good, what instrument a sound really is, whether there is singing, "
          "or how it feels to a listener. Tempo, key, chords and style are estimates; treat them "
          "as a strong hint, not a fact.", ""]
    (out / "report.md").write_text("\n".join(L), encoding="utf-8")

    data = {
        "file": Path(src).name, "duration_seconds": round(dur, 2),
        "tempo_bpm": round(tempo, 1), "pulse": a["pulse_word"],
        "has_steady_beat": bool(a["has_beat"]), "beat_regularity": round(a["repeat"], 3),
        "key": key,
        "tone": tone, "hits_per_second": round(len(a["hit_times"]) / dur, 2),
        "style": {**{k: v for k, v in a["style"].items() if k != "chord_per_beat"},
                  "clues": [c.replace("**", "") for c in clues],
                  "fits": [{"style": n, "why": w} for n, w in fits]},
        "chord_changes": [{"time": t, "chord": c} for t, c in changes],
        "sections": a["sections"], "moments": a["moments"], "silences": a["silences"],
        "beat_times": [round(float(b), 3) for b in a["beat_times"]],
        "per_second": {"loudness_db": [round(x, 1) for x in loud_s],
                       "bass_db": [round(x, 1) for x in bass_s],
                       "highs_db": [round(x, 1) for x in high_s],
                       "hits": [int(x) for x in hits_s]},
        "words": words, "pictures": ["overview.png"] + [z["file"] for z in zooms],
    }
    (out / "data.json").write_text(json.dumps(data, indent=1), encoding="utf-8")


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Turn sound into pictures and notes an AI can read.")
    ap.add_argument("file", help="any audio or video file")
    ap.add_argument("--out", help="folder to write into (default: <file name>_ears)")
    ap.add_argument("--zoom", type=float, default=20,
                    help="seconds shown in each close-up picture (default 20)")
    ap.add_argument("--max-zooms", type=int, default=24,
                    help="most close-up pictures to make (default 24)")
    ap.add_argument("--words", action="store_true",
                    help="also write down speech or lyrics (needs faster-whisper)")
    ap.add_argument("--words-model", default="small",
                    help="speech model size: tiny, base, small, medium, large-v3")
    args = ap.parse_args()

    src = Path(args.file)
    if not src.exists():
        sys.exit(f"File not found: {src}")
    out = Path(args.out) if args.out else src.with_name(src.stem + "_ears")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("zoom_*.png"):
        old.unlink()

    print(f"Reading {src.name}...")
    y = load_audio(src)
    print("  measuring loudness, pitch, beat and sections...")
    a = analyse(y)
    dur = a["duration"]

    print("  drawing pictures...")
    beat = f"about {a['tempo']:.0f} bpm" if a["has_beat"] else "no steady beat"
    head = f"{src.name}    {mmss_short(dur)}    {beat}    {a['key']['key']} ({a['key']['confidence']})"
    draw(a, 0, dur, out / "overview.png", head, show_beats=dur <= 45)

    zooms = []
    span = args.zoom
    if dur > span * 1.5:
        count = int(np.ceil(dur / span))
        if count > args.max_zooms:
            span = float(np.ceil(dur / args.max_zooms))
            count = int(np.ceil(dur / span))
        for i in range(count):
            t0, t1 = i * span, min(dur, (i + 1) * span)
            if t1 - t0 < 2:
                continue
            name = f"zoom_{i + 1:02d}_{mmss_short(t0).replace(':', 'm')}-{mmss_short(t1).replace(':', 'm')}.png"
            draw(a, t0, t1, out / name, f"{src.name}    close-up {mmss_short(t0)} to {mmss_short(t1)}")
            zooms.append({"file": name, "from": round(t0, 2), "to": round(t1, 2)})

    words = transcribe(src, args.words_model) if args.words else None
    write_report(a, src, out, words, zooms)
    print(f"Done. Open {out / 'report.md'} and {out / 'overview.png'}")


if __name__ == "__main__":
    main()
