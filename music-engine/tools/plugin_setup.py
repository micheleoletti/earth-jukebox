"""One-time GUI step for any plugin: open its window (hosted by DawDreamer), pick the sound, close the window.
The plugin state is saved so later renders run with no window.

Usage: .venv/bin/python plugin_setup.py "/Library/Audio/Plug-Ins/VST3/Splice INSTRUMENT.vst3" states/textural-pads.state
"""
import os, sys, dawdreamer as daw

plugin, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
eng = daw.RenderEngine(48000, 512)
p = eng.make_plugin_processor("p", plugin)
if os.path.exists(out):
    p.load_state(out)
print("window open: pick the preset, then close the window")
p.open_editor()
p.save_state(out)
print("saved", out)
