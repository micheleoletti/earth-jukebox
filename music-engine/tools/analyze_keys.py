import numpy as np, render_taiko as r
eng, p = r.kontakt()
rows = []
for note in range(24, 78):
    p.clear_midi(); p.add_midi_note(note, 110, 0.05, 0.4)
    eng.load_graph([(p, [])]); eng.render(3.0)
    a = eng.get_audio().mean(0); sr = r.SR
    seg = a[: int(sr * 0.5)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); f = np.fft.rfftfreq(len(seg), 1 / sr)
    cent = (spec * f).sum() / spec.sum()
    low = spec[f < 120].sum() / spec.sum()
    env = np.abs(a); pk = env.max(); idx = np.where(env > pk * 0.05)[0]; dur = (idx[-1] - idx[0]) / sr if len(idx) else 0
    rows.append((note, pk, cent, low, dur))
for n, pk, c, lo, d in rows: print(f"{n:3d} peak {pk:.2f} centroid {c:6.0f}Hz low<120 {lo:.2f} dur {d:.2f}s")
