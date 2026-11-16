"""Render LABS drones (Splice INSTRUMENT) headless: one soft held D per preset, as seamless 20 s loops.

Presets are chosen from code: the plugin state is built from states/instrument-base.xml with the patch name
swapped in (see juce_state.py), so no plugin window or clicks are needed.
Output: ../prototype/bounces/drone-<id>-<tone>.wav, tone = root (D), third (F#), fifth (A), low (D -1 oct), low2 (D -2 oct)
"""
import os, re, time, numpy as np, soundfile as sf, dawdreamer as daw, juce_state as j, render_taiko as rt

SR, LOOP = 48000, 20.0
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "prototype", "bounces")
PLUGIN = "/Library/Audio/Plug-Ins/VST3/Splice INSTRUMENT.vst3"
# id, family, preset name, patch (zmulti name), pack version, MIDI note, velocity, retrigger every N s (0 = hold)
DRONES = [
    ("pads-deneb",     "Textural Pads",  "Deneb",           "LABS_Textural_Pads_Deneb",     "1.0.2", 38, 40, 0),
    ("pads-petrichor", "Textural Pads",  "Petrichor",       "LABS_Textural_Pads_Petrichor", "1.0.2", 38, 40, 0),
    ("pads-saudade",   "Textural Pads",  "Saudade",         "LABS_Textural_Pads_Saudade",   "1.0.2", 50, 40, 0),
    ("trumpet-faded",  "Trumpet Fields", "Faded",           "LABS_Faded",                   "1.0.2", 62, 45, 10.0),
    ("trumpet-steady", "Trumpet Fields", "Nice And Steady", "LABS_Nice_And_Steady_1",       "1.0.2", 62, 40, 10.0),
]


def state_for(fam, name, patch, ver, dynamics=0.25, base_file="states/instrument-base.xml"):
    base = open(os.path.join(HERE, base_file)).read().rstrip("\0")
    if base_file != "states/instrument-base.xml":   # a real saved state for this exact patch: use it as is
        x = re.sub(r'(id="i_dynamics" value=")[^"]*', rf"\g<1>{dynamics}", base)
        return j.splice_state(open(os.path.join(HERE, "states/instrument-default.state"), "rb").read(), x)
    x = j.patched_xml(base, fam, name, patch)
    a, b, c = map(int, ver.split("."))
    x = re.sub(r'(id="a_version" value=")[^"]*', rf"\g<1>{(a << 24) | (b << 16) | (c << 8)}", x).replace('version="1.0.5"', f'version="{ver}"')
    x = re.sub(r'(id="i_dynamics" value=")[^"]*', rf"\g<1>{dynamics}", x)   # soft
    if "Trumpet" in fam:   # the base state has vibrato at 1.0: that pitch wobble sounded detuned
        x = re.sub(r'(id="i_vibrato" value=")[^"]*', r"\g<1>0.0", x)
    return j.splice_state(open(os.path.join(HERE, "states/instrument-default.state"), "rb").read(), x)


def seamless(a, xf=0.4):
    L, n = int(LOOP * SR), int(xf * SR)
    out = a[:, L:2 * L].copy(); w = np.linspace(0, 1, n)
    # equal-power: the two sides of a held drone are not in phase with each other
    out[:, :n] = a[:, L:L + n] * np.sin(w * np.pi / 2) + a[:, 2 * L:2 * L + n] * np.cos(w * np.pi / 2)
    return out


TONES = {"root": 0, "third": 4, "fifth": 7, "low": -12, "low2": -24}   # D, F#, A, D an octave down, D two octaves down


def main():
    import sys
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(HERE, "states/_tmp.state")
    args = sys.argv[1:]   # optional: drone ids and/or --tones=low,low2
    tones = next((a.split("=", 1)[1].split(",") for a in args if a.startswith("--tones=")), list(TONES))
    only = [a for a in args if not a.startswith("--")]
    jobs = [(d, t) for d in DRONES for t in tones if not only or d[0] in only]
    for (did, fam, name, patch, ver, root, vel, every), tone in jobs:
        note = root + TONES[tone]
        open(tmp, "wb").write(state_for(fam, name, patch, ver))
        eng = daw.RenderEngine(SR, 512); p = eng.make_plugin_processor("p", PLUGIN); p.load_state(tmp); time.sleep(4)
        ev, t = [(0.0, bytes([0xB0, 1, 30])), (0.0, bytes([0xB0, 11, 100]))], 0.0
        if "Trumpet" in fam: ev.append((0.0, bytes([0xB0, 21, 0])))   # LABS vibrato CC: off (pitch wobble sounded detuned)
        if not every:   # one note held across all 3 cycles
            ev += [(0.0, bytes([0x90, note, vel])), (3 * LOOP + 0.5, bytes([0x80, note, 0]))]
        while every and t < 3 * LOOP:
            # note-off a hair BEFORE the next note-on: an off after a same-pitch on would cut the new note
            ev += [(t, bytes([0x90, note, vel])), (t + every - 0.03, bytes([0x80, note, 0]))]; t += every
        mid = os.path.join(HERE, "states/_drone.mid"); rt.write_midi(mid, ev)
        p.load_midi(mid, clear_previous=True, beats=False, all_events=True)
        eng.load_graph([(p, [])]); eng.render(3 * LOOP + 1)
        a = eng.get_audio()[:2]; loop = seamless(a, 1.5 if not every else 0.4)
        pk = float(np.abs(loop).max()); rms = float(np.sqrt((loop ** 2).mean()))
        sf.write(os.path.join(OUT, f"drone-{did}-{tone}.wav"), loop.T, SR, subtype="FLOAT")
        print(f"{did}-{tone}: note {note} peak {pk:.3f} rms {rms:.4f}", flush=True)


if __name__ == "__main__":
    main()
