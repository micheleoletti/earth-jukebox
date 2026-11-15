"""Render real taiko stems from Kontakt (Thunder X3M) with no DAW: MIDI notes + dynamics CC per intensity.

  .venv/bin/python render_taiko.py map            # play every key, report which ones make sound (finds the drums)
  .venv/bin/python render_taiko.py stems          # render 5 intensity stems (keys in KEYS)

Stems: 3 cycles of the 8-bar loop (96 BPM, 60 s), same timing as prototype/loop-engine.js, which takes the
middle cycle so the loop wraps seamlessly. Output: ../prototype/bounces/taiko-i{0..4}.wav
"""
import glob, os, random, sys
import dawdreamer as daw, numpy as np, soundfile as sf

SR, BPM, BARS, CYCLES = 48000, 96, 8, 3
STEP = 60 / BPM / 4
STEPS = BARS * 16
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "bounces")
LEVELS = [0, 0.25, 0.5, 0.75, 1]


def kontakt():
    hits = sorted(glob.glob("/Library/Audio/Plug-Ins/VST3/Kontakt*.vst3") + glob.glob("/Library/Audio/Plug-Ins/Components/Kontakt*.component"))
    eng = daw.RenderEngine(SR, 512)
    p = eng.make_plugin_processor("kontakt", hits[-1])
    p.load_state("taiko.state")
    return eng, p


def key_map():
    eng, p = kontakt()
    found = []
    for note in range(24, 97):
        p.clear_midi()
        p.add_midi_note(note, 110, 0.05, 0.4)
        eng.load_graph([(p, [])]); eng.render(1.2)
        pk = float(np.abs(eng.get_audio()).max())
        if pk > 0.01:
            found.append((note, pk))
            print(f"note {note:3d}  peak {pk:.3f}")
    print("sounding keys:", [n for n, _ in found])


def pattern(x, rnd):
    """Taiko hits for one intensity: list of (step, velocity 0..1, kind) with kind in big/hit/flam."""
    groove = {0: 1, 3: 0.45, 6: 0.7, 8: 0.9, 10: 0.4, 11: 0.55, 14: 0.75}
    sparse = {0: 1, 8: 0.8, 14: 0.45}
    extra = {1: 0.3, 4: 0.5, 7: 0.35, 12: 0.5, 15: 0.4}
    hits = []
    for n in range(STEPS * CYCLES):
        i = n % STEPS; s = i % 16; bar = i // 16
        if x < 0.24:
            # calm + stirring: a single distant boom every 4 bars
            if s == 0 and bar % 4 == 0 and x > 0.1: hits.append((n, 0.35, "big"))
            continue
        if x < 0.49:
            v = {0: 0.6, 8: 0.4}.get(s)
            if v: hits.append((n, v, "big" if s == 0 else "hit"))
            continue
        if x < 0.74:
            v = sparse.get(s)
            if bar % 4 == 3 and s == 12: v = 0.5
        else:
            v = groove.get(s)
            if x >= 0.99 and not v: v = extra.get(s)
            if bar % 4 == 3 and s >= 12: v = 0.5 + 0.15 * (s - 12)
        if v:
            kind = "big" if s == 0 and (bar % 2 == 0 or x >= 0.99) else ("flam" if bar % 4 == 3 and s >= 12 else "hit")
            hits.append((n, v, kind))
        if x >= 0.99 and s == 8: hits.append((n, 0.75, "big"))
    return hits


def write_midi(path, events):
    """Minimal Standard MIDI File (format 0). events: (seconds, bytes). Tempo = BPM, 480 ticks per beat."""
    tpb = 480; tick = lambda sec: int(round(sec * BPM / 60 * tpb))
    def vlq(n):
        out = [n & 0x7F]; n >>= 7
        while n: out.insert(0, (n & 0x7F) | 0x80); n >>= 7
        return bytes(out)
    us = int(60_000_000 / BPM)
    body, last = bytearray(vlq(0) + b"\xFF\x51\x03" + us.to_bytes(3, "big")), 0
    for sec, msg in sorted(events, key=lambda e: (e[0], e[1][0] & 0xF0 != 0xB0)):
        t = tick(sec); body += vlq(t - last) + msg; last = t
    body += vlq(0) + b"\xFF\x2F\x00"
    with open(path, "wb") as f:
        f.write(b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big") + (1).to_bytes(2, "big") + tpb.to_bytes(2, "big"))
        f.write(b"MTrk" + len(body).to_bytes(4, "big") + body)


# Thunder X3M Freebie key groups (measured with analyze_keys.py): 24-29 deepest low strokes, 30-41 mid strokes,
# 72-77 rims. Several keys per role so consecutive hits alternate like real hands.
KEYS = {"big": [25, 26, 27], "hit": [30, 31, 33], "accent": [37, 38], "flam": [72, 73, 74]}


def stems():
    eng, p = kontakt()
    os.makedirs(OUT, exist_ok=True)
    turn = {k: 0 for k in KEYS}
    def key(kind):
        turn[kind] += 1; return KEYS[kind][turn[kind] % len(KEYS[kind])]
    dur = STEPS * CYCLES * STEP
    for k, x in enumerate(LEVELS):
        rnd = random.Random(1234)
        # the "real VST knob": dynamics CC1 (mod wheel) + CC11 (expression) follow intensity
        dyn = int(40 + 87 * x)
        events = [(0.0, bytes([0xB0, 1, dyn])), (0.0, bytes([0xB0, 11, dyn]))]
        hits = pattern(x, rnd)
        for n, v, kind in hits:
            t = max(0.0, n * STEP + (rnd.random() - 0.5) * 0.01 * (n > 0))
            vel = max(1, min(127, int(30 + 97 * v * (0.6 + 0.4 * x))))
            if kind == "hit" and v >= 0.85: kind = "accent"
            k_ = key(kind)
            events += [(t, bytes([0x90, k_, vel])), (t + 0.25, bytes([0x80, k_, 0]))]
        mid = os.path.join(OUT, f"taiko-i{k}.mid"); write_midi(mid, events)
        p.load_midi(mid, clear_previous=True, beats=False, all_events=True)
        eng.load_graph([(p, [])]); eng.render(dur)
        a = eng.get_audio()[:2]          # Kontakt exposes 64 outputs; 1-2 is the main stereo mix
        path = os.path.join(OUT, f"taiko-i{k}.wav")
        sf.write(path, a.T, SR, subtype="FLOAT")
        print(f"{path}: {len(hits)} hits, dyn CC {dyn}, peak {float(np.abs(a).max()):.3f}")


if __name__ == "__main__":
    if sys.argv[1] == "map": key_map()
    elif sys.argv[1] == "stems": stems()
