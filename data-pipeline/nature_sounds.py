"""Build playground/audio/nature-sounds.js from the CC0 Freesound recordings in earth-jukebox-cache/sounds/raw.

Loops (fire, rain, wind, storm_wind, waves, birds, traffic): a 40 s stretch, made seamless with a 4 s equal-power crossfade
of its tail into its head, mono, level-matched, a gentle high-frequency roll-off (no hiss), AAC 64 kbps.
One-shots (thunder, volcano): the loudest moment with 1.5 s before it, 12 s max, 30 ms fade-in and a long fade-out.
Output is base64 inside a .js file so the page works from file:// (fetch of local files is blocked there).
Usage: python data-pipeline/nature_sounds.py   (needs numpy and ffmpeg)
"""
import base64
import json
import pathlib
import subprocess
import tempfile

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
RAW = REPO.parent / "earth-jukebox-cache" / "sounds" / "raw"
OUT = REPO / "playground" / "audio" / "nature-sounds.js"
SR = 44100
FILES = {"fire": "fire_bonfire.mp3"}   # fire = "Bonfire HQ" by tosha73 (CC0), chosen by the owner
LOOPS = {"fire": 8, "rain": 4, "wind": 20, "storm_wind": 10, "waves": 20, "birds": 10, "traffic": 30}   # start second of the loop
SHOTS = ["thunder", "volcano"]
LOOP_S, XF_S = 40.0, 4.0


def decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)


def encode(x, bitrate="64k"):
    with tempfile.TemporaryDirectory() as td:
        raw, m4a = pathlib.Path(td) / "x.f32", pathlib.Path(td) / "x.m4a"
        raw.write_bytes(x.astype(np.float32).tobytes())
        # gentle roll-off of the highs (the owner dislikes high-pitched sound), then AAC
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
                        "-af", "highshelf=f=5000:g=-6,lowpass=f=11000", "-c:a", "aac", "-b:a", bitrate, str(m4a)], check=True)
        return m4a.read_bytes()


def level(x, target_db=-20.0):
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    y = x * (10 ** (target_db / 20) / rms)
    peak = np.max(np.abs(y))
    return y / peak * .95 if peak > .95 else y


def make_loop(x, start):
    L, X = int(LOOP_S * SR), int(XF_S * SR)
    a = int(start * SR)
    if a + L + X > len(x):
        a = max(0, len(x) - L - X)
    seg = x[a:a + L + X]
    if len(seg) < L + X:   # short recording: use what there is
        L = len(seg) - X
    t = np.linspace(0, np.pi / 2, X)
    out = seg[:L].copy()
    out[:X] = seg[L:L + X] * np.cos(t) + seg[:X] * np.sin(t)   # equal-power crossfade: the end flows into the start
    return level(out)


def make_shot(x):
    env = np.convolve(np.abs(x), np.ones(2205) / 2205, "same")
    p = int(np.argmax(env))
    a, b = max(0, p - int(1.5 * SR)), min(len(x), p + int(10.5 * SR))
    y = x[a:b].copy()
    fi, fo = int(.03 * SR), int(min(3.5, (b - a) / SR / 2) * SR)
    y[:fi] *= np.linspace(0, 1, fi)
    y[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    return level(y, -16.0)


def main():
    meta = {json.loads(l)["key"]: json.loads(l) for l in (RAW / "hits.jsonl").read_text().splitlines()}
    out, credits = {}, {}
    for k, st in LOOPS.items():
        y = make_loop(decode(RAW / FILES.get(k, f"{k}.mp3")), st)
        out[k] = base64.b64encode(encode(y)).decode()
        print(f"loop {k}: {len(y) / SR:.1f} s, {len(out[k]) / 1e6:.2f} MB b64")
    for k in SHOTS:
        y = make_shot(decode(RAW / f"{k}.mp3"))
        out[k] = base64.b64encode(encode(y, "80k")).decode()
        print(f"shot {k}: {len(y) / SR:.1f} s, {len(out[k]) / 1e6:.2f} MB b64")
    for k, m in meta.items():
        credits[k] = {"title": m["title"], "creator": m["creator"], "license": "CC0 1.0", "page": m["page"]}
    OUT.write_text("// CC0 recordings from Freesound (found via Openverse), trimmed into seamless loops by data-pipeline/nature_sounds.py\n"
                   f"window.NATURE_CREDITS = {json.dumps(credits)};\n"
                   f"window.NATURE_SOUNDS = {json.dumps(out)};\n")
    print("wrote", OUT, round(OUT.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
