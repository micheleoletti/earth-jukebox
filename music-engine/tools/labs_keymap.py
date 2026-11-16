"""Scan which keys of a LABS patch make sound (headless) and how bright/long each is."""
import sys, time, os, numpy as np, dawdreamer as daw
import render_drones as rd
fam, name, patch, ver = sys.argv[1:5]; base = sys.argv[5] if len(sys.argv) > 5 else "states/instrument-base.xml"
st = os.path.join(rd.HERE, "states/_scan.state"); open(st, "wb").write(rd.state_for(fam, name, patch, ver, dynamics=1.0, base_file=base))
eng = daw.RenderEngine(rd.SR, 512); p = eng.make_plugin_processor("p", rd.PLUGIN); p.load_state(st); time.sleep(4)
for key in range(21, 109):
    p.clear_midi(); p.add_midi_note(key, 100, 0.0, 0.3); eng.load_graph([(p, [])]); eng.render(2.5)
    a = eng.get_audio()[:2]; m = a.mean(0); pk = float(np.abs(a).max())
    if pk < 0.002: continue
    seg = m[: int(rd.SR * 0.4)]; sp = np.abs(np.fft.rfft(seg)); f = np.fft.rfftfreq(len(seg), 1 / rd.SR)
    env = np.abs(m); idx = np.where(env > env.max() * 0.05)[0]
    print(f"{key:3d} peak {pk:.3f} centroid {(sp * f).sum() / sp.sum():6.0f}Hz dur {(idx[-1] - idx[0]) / rd.SR:.2f}s", flush=True)
