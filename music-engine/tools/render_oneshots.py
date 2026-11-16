"""Render Thunder X3M one-shots (every key at 5 velocities) so the piano roll can preview instantly in the browser.
Local editing aid only: raw samples must not be shipped in the public app (Strezov licence), only bounced loops.
Output: ../prototype/samples/<inst dir>/k<key>-v<vel>.m4a + index.json
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
import render_taiko as rt, instruments

KEYS = range(24, 78)
VELS = [24, 48, 72, 100, 127]


def main():
    # usage: render_oneshots.py [inst] [key,key,...]   (default: thunder, keys 24-77)
    inst = sys.argv[1] if len(sys.argv) > 1 else "thunder"
    keys = [int(k) for k in sys.argv[2].split(",")] if len(sys.argv) > 2 else list(KEYS)
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "samples", instruments.INSTRUMENTS[inst]["dir"])
    os.makedirs(OUT, exist_ok=True)
    eng, p = instruments.load(inst)
    index = {}
    for key in keys:
        for vel in VELS:
            p.clear_midi(); p.add_midi_note(key, vel, 0.0, 0.25)
            eng.load_graph([(p, [])]); eng.render(3.0)
            a = eng.get_audio()[:2]
            env = np.abs(a).max(0); pk = float(env.max())
            if pk < 1e-4:
                continue
            end = int(np.where(env > pk * 0.003)[0][-1]) + int(0.05 * rt.SR)
            a = a[:, :min(end, a.shape[1])]
            fade = min(2400, a.shape[1]); a[:, -fade:] *= np.linspace(1, 0, fade)
            wav = os.path.join(OUT, f"k{key}-v{vel}.wav"); sf.write(wav, a.T, rt.SR, subtype="PCM_24")
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "160k", wav[:-4] + ".m4a"], check=True)
            os.remove(wav)
            index.setdefault(str(key), []).append(vel)
        print(f"key {key}: {index.get(str(key))}", flush=True)
    json.dump({"velocities": VELS, "keys": index}, open(os.path.join(OUT, "index.json"), "w"))


if __name__ == "__main__":
    main()
