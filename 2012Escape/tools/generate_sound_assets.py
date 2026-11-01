"""Generate deterministic placeholder WAV sound assets for 2012Escape.

These sounds are intentionally simple and royalty-free because they are produced
locally from math waveforms. Replace them later with polished assets if desired.
"""

from __future__ import annotations

import math
import os
import wave
from typing import Callable

SAMPLE_RATE = 44100
MAX_AMPLITUDE = 32767


def clamp(value: float) -> float:
    return max(-1.0, min(1.0, value))


def envelope(t: float, duration: float, attack: float = 0.02, release: float = 0.12) -> float:
    if t < attack:
        return t / attack
    if t > duration - release:
        return max(0.0, (duration - t) / release)
    return 1.0


def sine(freq: float, t: float) -> float:
    return math.sin(2.0 * math.pi * freq * t)


def square(freq: float, t: float) -> float:
    return 1.0 if sine(freq, t) >= 0.0 else -1.0


def write_wav(path: str, duration: float, sample_fn: Callable[[float], float]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frame_count = int(duration * SAMPLE_RATE)
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for i in range(frame_count):
            t = i / SAMPLE_RATE
            sample = int(clamp(sample_fn(t)) * MAX_AMPLITUDE)
            frames.extend(sample.to_bytes(2, "little", signed=True))
        wav.writeframes(frames)


def bgm_sample(t: float) -> float:
    progression = [261.63, 329.63, 392.00, 523.25, 493.88, 392.00, 329.63, 293.66]
    beat = 0.5
    note = progression[int(t / beat) % len(progression)]
    local_t = t % beat
    lead = 0.22 * sine(note, t) * envelope(local_t, beat, 0.01, 0.08)
    harmony = 0.12 * sine(note / 2.0, t) * envelope(local_t, beat, 0.02, 0.10)
    pulse = 0.05 * square(65.41, t) * envelope(local_t, beat, 0.005, 0.15)
    return lead + harmony + pulse


def jump_sample(t: float) -> float:
    duration = 0.35
    freq = 420.0 + 620.0 * (t / duration)
    return 0.45 * sine(freq, t) * envelope(t, duration, 0.005, 0.10)


def hit_sample(t: float) -> float:
    duration = 0.28
    freq = 150.0 - 80.0 * (t / duration)
    buzz = 0.35 * square(max(40.0, freq), t)
    thud = 0.30 * sine(70.0, t)
    return (buzz + thud) * envelope(t, duration, 0.002, 0.20)


def clear_sample(t: float) -> float:
    duration = 1.10
    notes = [523.25, 659.25, 783.99, 1046.50]
    note_len = duration / len(notes)
    index = min(len(notes) - 1, int(t / note_len))
    local_t = t - index * note_len
    note = notes[index]
    main = 0.35 * sine(note, t) * envelope(local_t, note_len, 0.01, 0.10)
    sparkle = 0.18 * sine(note * 2.0, t) * envelope(local_t, note_len, 0.005, 0.08)
    return main + sparkle


def ending_sample(t: float) -> float:
    chords = [
        (261.63, 329.63, 392.00),
        (220.00, 261.63, 329.63),
        (174.61, 220.00, 261.63),
        (196.00, 246.94, 293.66),
    ]
    chord_length = 3.0
    chord = chords[int(t / chord_length) % len(chords)]
    local_t = t % chord_length
    pad = sum(sine(note, t) for note in chord) * 0.075
    bell_note = chord[int(local_t / 1.0) % len(chord)] * 2.0
    bell = 0.10 * sine(bell_note, t) * envelope(local_t % 1.0, 1.0, 0.02, 0.55)
    return (pad + bell) * envelope(local_t, chord_length, 0.25, 0.40)


def main() -> None:
    write_wav("sounds/bgm.wav", 12.0, bgm_sample)
    write_wav("sounds/jump.wav", 0.35, jump_sample)
    write_wav("sounds/hit.wav", 0.28, hit_sample)
    write_wav("sounds/clear.wav", 1.10, clear_sample)
    write_wav("sounds/ending.wav", 12.0, ending_sample)


if __name__ == "__main__":
    main()
