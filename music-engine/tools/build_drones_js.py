"""Package rendered drone stems for the player: one gain per preset (taken from its root note, so the
chord tones keep their natural balance), drop silent tones (outside the instrument's range), encode AAC,
write ../prototype/drones.js as base64 so the player works from file://.
"""
import base64, glob, os, subprocess
import numpy as np, soundfile as sf
from render_drones import DRONES, TONES

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "bounces")
SOURCES = {"Textural Pads": "LABS Textural Pads", "Trumpet Fields": "LABS Trumpet Fields"}
LABELS = {"pads-deneb": "Deneb", "pads-petrichor": "Petrichor", "pads-saudade": "Saudade",
          "trumpet-faded": "Trumpet, faded", "trumpet-steady": "Trumpet, steady"}

entries = []
for did, fam, *_ in DRONES:
    root, sr = sf.read(os.path.join(B, f"drone-{did}-root.wav"))
    gain = min(10 ** (-20 / 20) / np.sqrt((root ** 2).mean()), 10 ** (-1 / 20) / np.abs(root).max())
    tones = {}
    for t in TONES:
        f = os.path.join(B, f"drone-{did}-{t}.wav")
        if not os.path.exists(f):
            continue
        a, _ = sf.read(f)
        rms_db = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-12)
        if rms_db < -75:
            print(f"skip {did}-{t}: silent ({rms_db:.0f} dB)"); continue
        a = a * min(gain, 10 ** (-1 / 20) / max(np.abs(a).max(), 1e-9))
        n, m = f.replace(".wav", "-n.wav"), f.replace(".wav", ".m4a")
        sf.write(n, a, sr, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", n, "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", m], check=True)
        tones[t] = base64.b64encode(open(m, "rb").read()).decode()
        print(f"{did}-{t}: {rms_db:+.0f} dB raw, {os.path.getsize(m) // 1024} KB")
    entries.append((did, LABELS.get(did, did), SOURCES.get(fam, fam), tones))

out = os.path.join(B, "..", "drones.js")
with open(out, "w") as f:
    f.write("// Drone layers: seamless 20 s loops, one soft held note each, per tone (root D, third F#, fifth A,\n")
    f.write("// low = D an octave down, low2 = two octaves down). Spitfire LABS via Splice INSTRUMENT + DawDreamer.\n")
    f.write("window.DRONES = [\n")
    for did, label, src, tones in entries:
        t = ", ".join(f'{k}: "{v}"' for k, v in tones.items())
        f.write(f'  {{ id: "{did}", label: "{label}", source: "{src}", tones: {{ {t} }} }},\n')
    f.write("];\n")
print("wrote", out, os.path.getsize(out) // 1024, "KB")
