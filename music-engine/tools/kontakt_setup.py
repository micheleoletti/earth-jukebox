"""One-time: open Kontakt's window headless-hosted, load the Thunder X3M patch by hand, close the window.
The plugin state (with the patch loaded) is saved to taiko.state so every later render runs with no window.

Usage: .venv/bin/python kontakt_setup.py [path/to/Kontakt.vst3]
"""
import glob, sys, dawdreamer as daw

def find_kontakt():
    hits = sorted(glob.glob("/Library/Audio/Plug-Ins/VST3/Kontakt*.vst3") + glob.glob("/Library/Audio/Plug-Ins/Components/Kontakt*.component"))
    if not hits:
        sys.exit("Kontakt plugin not found in /Library/Audio/Plug-Ins. Install Kontakt Player via Native Access first.")
    return hits[-1]

path = sys.argv[1] if len(sys.argv) > 1 else find_kontakt()
print("plugin:", path)
eng = daw.RenderEngine(48000, 512)
p = eng.make_plugin_processor("kontakt", path)
print("Kontakt window opening: load the Thunder X3M taiko patch, then close the window.")
p.open_editor()  # blocks until the window is closed
p.save_state("taiko.state")
print("saved taiko.state")
