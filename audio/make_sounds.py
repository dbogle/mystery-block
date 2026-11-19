"""Generate the block's original 8-bit style sounds as WAV files.

    python audio/make_sounds.py

Writes audio/sd/01/001.wav (coin), 002.wav (bonus), 003.wav (startup).
Copy the *contents* of audio/sd/ to the root of a FAT32 microSD card for the
DFPlayer Mini. Want different sounds? Replace the WAVs with any MP3/WAV you
own, keeping the names.
"""
import math
import struct
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent / "sd" / "01"


def note(name):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4,
             "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[pitch] + 12 * (octave - 4)) / 12)


def square(freq, dur, duty=0.25, attack=0.003, decay=None, vib=0.0, vol=0.6):
    n = int(RATE * dur)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / RATE
        f = freq * (1 + vib * math.sin(2 * math.pi * 6 * t))
        phase = (phase + f / RATE) % 1.0
        s = 1.0 if phase < duty else -1.0
        env = min(1.0, t / attack) if attack else 1.0
        if decay:
            env *= math.exp(-t / decay)
        out.append(s * env * vol)
    return out


def chord(*voices):
    n = max(len(v) for v in voices)
    return [sum(v[i] for v in voices if i < len(v)) / len(voices) for i in range(n)]


def silence(dur):
    return [0.0] * int(RATE * dur)


def soften(samples, k=0.35):
    """One-pole low-pass to take the edge off raw square waves."""
    out, y = [], 0.0
    for s in samples:
        y += k * (s - y)
        out.append(y)
    return out


def write(name, samples):
    OUT.mkdir(parents=True, exist_ok=True)
    peak = max(1e-9, max(abs(s) for s in samples))
    data = b"".join(struct.pack("<h", int(32000 * s / peak * 0.9)) for s in samples)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)
    print(f"  {OUT.relative_to(OUT.parents[2])}/{name}  {len(samples) / RATE:.2f}s")


def coin():
    # quick rising major arpeggio that rings out on the top note
    s = []
    for n in ("C6", "E6", "G6"):
        s += square(note(n), 0.045, decay=0.08)
    s += square(note("C7"), 0.45, decay=0.14, duty=0.125)
    return soften(s)


def bonus():
    s = []
    for n in ("G5", "A5", "B5", "C6", "D6", "E6", "F#6", "G6"):
        s += square(note(n), 0.055, decay=0.12)
    for _ in range(4):  # little trill
        s += square(note("G6"), 0.05, decay=0.2) + square(note("B6"), 0.05, decay=0.2)
    s += chord(square(note("G6"), 0.6, decay=0.25, vib=0.01),
               square(note("D7"), 0.6, decay=0.25, vib=0.01))
    return soften(s)


def startup():
    s = chord(square(note("G5"), 0.16, decay=0.2), square(note("D6"), 0.16, decay=0.2))
    s += silence(0.03)
    s += chord(square(note("C6"), 0.5, decay=0.22), square(note("G6"), 0.5, decay=0.22),
               square(note("E6"), 0.5, decay=0.22))
    return soften(s)


if __name__ == "__main__":
    write("001.wav", coin())
    write("002.wav", bonus())
    write("003.wav", startup())
