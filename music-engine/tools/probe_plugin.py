"""Load a VST3/AU headless with DawDreamer, list parameters, render one test note."""
import sys, dawdreamer as daw, numpy as np, soundfile as sf
path = sys.argv[1]; sr = 48000
eng = daw.RenderEngine(sr, 512)
p = eng.make_plugin_processor("p", path)
print("loaded:", p.get_name(), "| inputs", p.get_num_input_channels(), "outputs", p.get_num_output_channels())
params = p.get_parameters_description()
print("params:", len(params))
for d in params[:40]: print("  ", d["index"], d["name"], d.get("text", ""))
p.add_midi_note(48, 110, 0.0, 1.5)
eng.load_graph([(p, [])]); eng.render(3.0)
a = eng.get_audio(); print("audio", a.shape, "peak", float(np.abs(a).max()))
if len(sys.argv) > 2: sf.write(sys.argv[2], a.T, sr)
