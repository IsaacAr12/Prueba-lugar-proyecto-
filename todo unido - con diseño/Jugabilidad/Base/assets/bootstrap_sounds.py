
# -*- coding: utf-8 -*-
import os, wave, struct, math

def _write_beep_wav(path, freq=880.0, duration_ms=80, volume=0.22, framerate=44100):
    nframes = int(framerate * duration_ms / 1000.0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(framerate)
        for i in range(nframes):
            sample = int(volume * 32767 * math.sin(2 * math.pi * freq * (i / framerate)))
            w.writeframesraw(struct.pack('<h', sample))
        w.writeframes(b'')

def ensure_default_sounds(move_path="assets/sounds/move.wav",
                          shot_path="assets/sounds/shot.wav"):
    if not os.path.exists(move_path):
        _write_beep_wav(move_path, freq=660.0, duration_ms=55, volume=0.18)
    if not os.path.exists(shot_path):
        _write_beep_wav(shot_path, freq=1200.0, duration_ms=75, volume=0.22)
