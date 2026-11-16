"""The plugins the taiko editor can play, each loaded headless with DawDreamer from a saved/crafted state."""
import glob, os, time
import dawdreamer as daw
import render_drones as rd

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000


def _kontakt():
    path = sorted(glob.glob("/Library/Audio/Plug-Ins/VST3/Kontakt*.vst3"))[-1]
    eng = daw.RenderEngine(SR, 512); p = eng.make_plugin_processor("p", path); p.load_state(os.path.join(HERE, "taiko.state"))
    return eng, p


def _splice(state_bytes):
    st = os.path.join(HERE, "states/_inst.state"); open(st, "wb").write(state_bytes)
    eng = daw.RenderEngine(SR, 512); p = eng.make_plugin_processor("p", rd.PLUGIN); p.load_state(st); time.sleep(4)
    return eng, p


INSTRUMENTS = {
    # Strezov Thunder X3M Taiko Freebie (Kontakt Player)
    "thunder": {"dir": "taiko", "load": _kontakt},
    # Spitfire LABS Percussion: state saved by the Splice INSTRUMENT app (patch LABS_Percussion_Percussion)
    "labs-perc": {"dir": "labs-perc", "load": lambda: _splice(rd.state_for("Percussion", "Percussion", "LABS_Percussion", "1.0.1", dynamics=1.0, base_file="states/labs-percussion.xml"))},
    # Spitfire LABS Hand Bells (tuned, C4-C6)
    "labs-bells": {"dir": "labs-bells", "load": lambda: _splice(rd.state_for("Hand Bells", "Hand Bells", "LABS_Hand_Bells", "1.0.0", dynamics=1.0))},
}


def load(inst):
    eng, p = INSTRUMENTS[inst]["load"]()
    return eng, p
