"""Patterns (prototype/taiko-patterns.json, edited in piano-roll.html) -> Kontakt Thunder X3M -> 5 seamless loops
for the knob player (prototype/bounces/loop-i{0..4}.wav/.m4a + prototype/loop-bounces.js). No DAW, no window.

  .venv/bin/python bounce_taiko.py            # bounce the rhythm selected in the piano roll
  .venv/bin/python bounce_taiko.py --all      # bounce every rhythm set
  .venv/bin/python bounce_taiko.py --init     # write taiko-patterns.json from the built-in patterns (render_taiko.py)
"""
import base64, glob, json, os, random, re, subprocess, sys, zlib
import numpy as np, soundfile as sf
import render_taiko as rt

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "prototype")
PATTERNS = os.path.join(PROTO, "taiko-patterns.json")
OUT = os.path.join(PROTO, "bounces")
SR, STEP, STEPS = rt.SR, rt.STEP, rt.STEPS

# Rows of the piano roll, top to bottom = brightest to deepest. Each row is a group of 6 keys in the
# Thunder X3M Freebie patch (measured by brightness/decay); playing a row cycles its keys like round robins.
HIGH_ROWS = [   # removed from the editor (sounded wrong with the taiko); kept for reference
    # Spitfire LABS Hand Bells, tuned to the drones (D major: D F# A)
    {"id": "b81", "label": "Bell A5", "keys": [81], "inst": "labs-bells"},
    {"id": "b78", "label": "Bell F#5", "keys": [78], "inst": "labs-bells"},
    {"id": "b74", "label": "Bell D5", "keys": [74], "inst": "labs-bells"},
    {"id": "b69", "label": "Bell A4", "keys": [69], "inst": "labs-bells"},
    {"id": "b66", "label": "Bell F#4", "keys": [66], "inst": "labs-bells"},
    {"id": "b62", "label": "Bell D4", "keys": [62], "inst": "labs-bells"},
    # Spitfire LABS Percussion (labels from the GM-style key layout + measured brightness/length)
    {"id": "p82", "label": "Shaker", "keys": [82], "inst": "labs-perc"},
    {"id": "p70", "label": "Maracas", "keys": [70], "inst": "labs-perc"},
    {"id": "p69", "label": "Cabasa", "keys": [69], "inst": "labs-perc"},
    {"id": "p54", "label": "Tambourine", "keys": [54], "inst": "labs-perc"},
    {"id": "p81", "label": "Triangle", "keys": [81], "inst": "labs-perc"},
    {"id": "p80", "label": "Triangle (muted)", "keys": [80], "inst": "labs-perc"},
    {"id": "p75", "label": "Claves", "keys": [75], "inst": "labs-perc"},
    {"id": "p76", "label": "Wood block", "keys": [76, 77], "inst": "labs-perc"},
    {"id": "p60", "label": "Bongos", "keys": [60, 62], "inst": "labs-perc"},
]
ROWS = [
    # Strezov Thunder X3M Taiko Freebie: groups of 6 keys, cycled like round robins
    {"id": "k72", "label": "Rim", "keys": list(range(72, 78)), "inst": "thunder"},
    {"id": "k66", "label": "Bright 3", "keys": list(range(66, 72)), "inst": "thunder"},
    {"id": "k60", "label": "Bright 2", "keys": list(range(60, 66)), "inst": "thunder"},
    {"id": "k54", "label": "Bright 1 (short)", "keys": list(range(54, 60)), "inst": "thunder"},
    {"id": "k48", "label": "Mid 3", "keys": list(range(48, 54)), "inst": "thunder"},
    {"id": "k42", "label": "Mid 2", "keys": list(range(42, 48)), "inst": "thunder"},
    {"id": "k36", "label": "Mid 1 (accent)", "keys": list(range(36, 42)), "inst": "thunder"},
    {"id": "k30", "label": "Low (groove)", "keys": list(range(30, 36)), "inst": "thunder"},
    {"id": "k24", "label": "Deep (big)", "keys": list(range(24, 30)), "inst": "thunder"},
]
GHOST_BASE = 40      # stored velocity of a ghost note; played velocity = v * ghostVel / GHOST_BASE
KIND_ROW = {"big": "k24", "hit": "k30", "accent": "k36", "flam": "k72"}


VEL = {"X": 118, "x": 92, "o": 66, "g": GHOST_BASE}


def lane(row, pat16, bars=range(8), shift=0):
    """One row of a pattern from a 16-char bar string: X accent, x normal, o soft, g ghost, . rest."""
    out, r = [], random.Random(zlib.crc32((row + pat16).encode()))
    for b in bars:
        for i, ch in enumerate(pat16.replace(" ", "")):
            if ch in VEL:
                v = VEL[ch] + r.randint(-4, 4) if ch != "g" else GHOST_BASE + r.randint(-3, 3)
                out.append({"s": b * 16 + i + shift, "r": row, "v": max(1, min(127, v)), "len": 1, **({"g": 1} if ch == "g" else {})})
    return out


def fill(row, bars=(3, 7), pat="....  ....  ....  XxXX"):
    return lane(row, pat.replace(" ", ""), bars)


def rhythm(levels):
    """levels: 5 lists of notes -> 5 patterns, later notes win on the same row+step. Only rows in ROWS (taiko) are kept."""
    ids = {r["id"] for r in ROWS}
    pats = []
    for notes in levels:
        seen = {}
        for n in notes:
            if n["r"] in ids: seen[(n["r"], n["s"])] = n
        pats.append(sorted(seen.values(), key=lambda n: (n["s"], n["r"])))
    return pats


ALL, EVEN, ODD, B04 = range(8), range(0, 8, 2), range(1, 8, 2), (0, 4)


def rhythm_sets(original):
    heartbeat = rhythm([
        lane("k24", "o...............", B04) + lane("b74", "o...............", B04),
        lane("k24", "X..x............") + lane("b74", "o...............", B04),
        lane("k24", "X..x............") + lane("k30", "....x.......x...") + lane("p82", "g.g.g.g.g.g.g.g."),
        lane("k24", "X..x............") + lane("k30", "..g.x.g...g.x.g.") + lane("k36", "........X.......", ODD) + lane("p82", "g.g.g.g.g.g.g.g.") + lane("p76", "...x.......x....") + fill("k30"),
        lane("k24", "X..x...X..x.....") + lane("k30", "..g.x.g...g.x.g.") + lane("k36", "........X.......") + lane("p82", "gggggggggggggggg") + lane("p54", "....x.......x...")
        + lane("b74", "X...............", EVEN) + lane("b69", "........x.......", EVEN) + lane("k72", "..........g.g.g.") + fill("k30") + fill("k72", pat="............gggg"),
    ])
    march = rhythm([
        lane("k24", "o...............", B04),
        lane("k30", "o...o...o...o..."),
        lane("k30", "X...x...X...x...") + lane("k24", "X.......X......."),
        lane("k30", "X...x...X...x...") + lane("k24", "X.......X.......") + lane("k36", "X.......X.......", EVEN) + lane("k42", "..g...g...g...g.") + lane("p75", "..x...x...x...x.") + fill("k30"),
        lane("k30", "X...x...X...x...") + lane("k24", "X.......X.......") + lane("k36", "X.......X.......") + lane("k42", "..g...g...g...g.") + lane("k72", "g.g.g.g.g.g.g.g.")
        + lane("p75", "..x...x...x...x.") + lane("p81", "X...............", B04) + lane("b62", "X...............", B04) + fill("k30", pat="........XxXxXXXX", bars=(7,)) + fill("k36"),
    ])
    gallop = rhythm([
        lane("b69", "o.......o.......", B04),
        lane("k30", "x...x...x...x..."),
        lane("k30", "x.ggx.ggx.ggx.gg") + lane("k24", "X..............."),
        lane("k30", "x.ggx.ggx.ggx.gg") + lane("k24", "X.....X.X.......") + lane("p70", "gggggggggggggggg") + fill("k36"),
        lane("k30", "x.ggx.ggx.ggx.gg") + lane("k24", "X.....X.X.......") + lane("p70", "gggggggggggggggg") + lane("k36", "....X.......X...") + lane("k72", "...g...g...g...g")
        + lane("b74", "X.......X.......", EVEN) + lane("p54", "....x.......x...") + fill("k36") + fill("k72", pat="............XXXX", bars=(7,)),
    ])
    halftime = rhythm([
        lane("k24", "o...............", EVEN),
        lane("k24", "X...............", EVEN) + lane("b62", "o...............", B04),
        lane("k24", "X.......x.......") + lane("k36", "........X.......", ODD) + lane("b62", "o...............", B04),
        lane("k24", "X..x....x.......") + lane("k36", "........X.......") + lane("k30", "..g..g....g..g.g") + lane("p82", "..x...x...x...x.") + fill("k30"),
        lane("k24", "X..x....x..x....") + lane("k36", "........X.......") + lane("k30", "..g..g....g..g.g") + lane("p82", ".gx..gx..gx..gx.") + lane("k72", "....g.g.....g.g.")
        + lane("b81", "X...............", EVEN) + lane("b74", "........X.......", EVEN) + lane("p81", "X...............", B04) + fill("k30") + fill("k24", pat="............X.X.", bars=(7,)),
    ])
    tribal = rhythm([
        lane("p76", "o..o..o.........", B04),
        lane("k30", "x..x..x........."),
        lane("k30", "X..x..x.X..x..x.") + lane("k24", "X.......X......."),
        lane("k30", "X..x..x.X..x..x.") + lane("k24", "X.......X.......") + lane("k42", ".gg.gg.g.gg.gg.g") + lane("p60", "..x..x.x..x..x.x") + fill("k30"),
        lane("k30", "X..x..x.X..x..x.") + lane("k24", "X.......X.......") + lane("k42", ".gg.gg.g.gg.gg.g") + lane("p60", "..x..x.x..x..x.x") + lane("k36", "X..X..X.X..X..X.", ODD)
        + lane("p54", "....x.......x...") + lane("b74", "X..x..x.........", EVEN) + lane("b69", "X..x..x.........", ODD) + fill("k30") + fill("k72", pat="........g.g.gggg", bars=(7,)),
    ])
    return [{"name": "Original", "patterns": original}, {"name": "Heartbeat", "patterns": heartbeat}, {"name": "War march", "patterns": march},
            {"name": "Gallop", "patterns": gallop}, {"name": "Half-time epic", "patterns": halftime}, {"name": "Tribal 3+3+2", "patterns": tribal}]


def init_patterns():
    """Write taiko-patterns.json: the original patterns (soft hits marked as ghosts) + 5 new rhythm sets."""
    old = json.load(open(PATTERNS)) if os.path.exists(PATTERNS) else None
    if old and "sets" in old:
        original = old["sets"][0]["patterns"]
    elif old:
        original = old["patterns"]
    else:
        original = []
        for x in rt.LEVELS:
            notes = []
            for n, v, kind in rt.pattern(x, random.Random(1234)):
                if n >= STEPS: continue
                if kind == "hit" and v >= 0.85: kind = "accent"
                notes.append({"s": n, "r": KIND_ROW[kind], "v": max(1, min(127, int(30 + 97 * v * (0.6 + 0.4 * x)))), "len": 1})
            original.append(notes)
    for pat in original:        # soft hits become ghost notes, steered by the ghost velocity knob
        for n in pat:
            if n["v"] < 70 or n.get("g"):
                n["g"] = 1; n["v"] = GHOST_BASE
    data = {"bpm": (old or {}).get("bpm", rt.BPM), "bars": rt.BARS, "stepsPerBar": 16, "ghostVel": (old or {}).get("ghostVel", 34),
            "current": 0, "rows": ROWS, "sets": rhythm_sets(original)}
    json.dump(data, open(PATTERNS, "w"), indent=1)
    print("wrote", PATTERNS, [(st["name"], [len(p) for p in st["patterns"]]) for st in data["sets"]])


def played_velocity(n, ghost_vel):
    return max(1, min(127, round(n["v"] * ghost_vel / GHOST_BASE))) if n.get("g") else int(n["v"])


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "rhythm"


def bounce(which="current"):
    """Render rhythm sets through the plugins. which: "current" (the set selected in the piano roll) or "all".
    Each set -> prototype/bounces/sets/<slug>/loop-i{0..4}.m4a; then loop-bounces.js is rebuilt with every bounced set."""
    import instruments
    data = json.load(open(PATTERNS))
    rowdef = {r["id"]: r for r in data["rows"]}
    STEP = 60 / float(data.get("bpm", rt.BPM)) / 4      # tempo set in the piano roll
    gv = data.get("ghostVel", 34)
    idxs = range(len(data["sets"])) if which == "all" else [data.get("current", 0)]
    L = int(round(STEPS * STEP * SR))
    loops = {i: [np.zeros((2, L)) for _ in data["sets"][i]["patterns"]] for i in idxs}
    insts = sorted({rowdef[n["r"]].get("inst", "thunder") for i in idxs for p in data["sets"][i]["patterns"] for n in p})
    for inst in insts:                    # load each plugin once, render every set with it
        eng, p = instruments.load(inst)
        for i in idxs:
            rset = data["sets"][i]
            for k, notes in enumerate(rset["patterns"]):
                notes = [n for n in notes if rowdef[n["r"]].get("inst", "thunder") == inst]
                if not notes: continue
                turn, events = {}, []
                for c in range(rt.CYCLES):
                    for nt in sorted(notes, key=lambda n: n["s"]):
                        keys = rowdef[nt["r"]]["keys"]; turn[nt["r"]] = turn.get(nt["r"], -1) + 1
                        key = keys[turn[nt["r"]] % len(keys)]
                        t = (c * STEPS + nt["s"]) * STEP
                        events += [(t, bytes([0x90, key, played_velocity(nt, gv)])), (t + max(1, nt.get("len", 1)) * STEP * 0.95, bytes([0x80, key, 0]))]
                mid = os.path.join(OUT, "_render.mid"); rt.write_midi(mid, events)
                p.load_midi(mid, clear_previous=True, beats=False, all_events=True)
                eng.load_graph([(p, [])]); eng.render(STEPS * rt.CYCLES * STEP)
                a = eng.get_audio()[:2]
                loop = a[:, L:2 * L].copy(); n = int(0.3 * SR); w = np.linspace(0, 1, n)
                loop[:, :n] = a[:, L:L + n] * w + a[:, 2 * L:2 * L + n] * (1 - w)
                loops[i][k] += loop
            print(f"{inst}: {rset['name']} rendered", flush=True)
    for i in idxs:
        name = data["sets"][i]["name"]; d = os.path.join(OUT, "sets", slug(name)); os.makedirs(d, exist_ok=True)
        gain = 10 ** (-1 / 20) / (max(float(np.abs(l).max()) for l in loops[i]) or 1.0)
        for k, loop in enumerate(loops[i]):
            wav = os.path.join(d, f"loop-i{k}.wav")
            sf.write(wav, (loop * gain).T, SR, subtype="PCM_16")
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", wav[:-4] + ".m4a"], check=True)
            os.remove(wav)
        print(f"bounced {name}: gain {20 * np.log10(gain):+.1f} dB", flush=True)
    build_js(data)
    print(f"done: {len(idxs)} rhythm(s), {data.get('bpm', rt.BPM)} BPM, loop {STEPS * STEP:.2f} s, loop-bounces.js rebuilt", flush=True)


def encode():
    """Browser-rendered loops (piano-roll synth bounce) -> AAC per set, then rebuild loop-bounces.js."""
    data = json.load(open(PATTERNS)); n = 0
    for st in data["sets"]:
        d = os.path.join(OUT, "sets", slug(st["name"]))
        for k in range(5):
            wav = os.path.join(d, f"loop-i{k}.wav")
            if os.path.exists(wav):
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", wav[:-4] + ".m4a"], check=True)
                os.remove(wav); n += 1
    build_js(data)
    # synth layer stems (bounce.html "Bounce synth layers") -> synth-layers.js
    layers = []
    for wav in sorted(glob.glob(os.path.join(OUT, "synth-*.wav"))):
        m4a = wav[:-4] + ".m4a"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", m4a], check=True)
        os.remove(wav); n += 1
    for m4a in sorted(glob.glob(os.path.join(OUT, "synth-*.m4a"))):
        layers.append((os.path.basename(m4a)[6:-4], base64.b64encode(open(m4a, "rb").read()).decode()))
    if layers:
        with open(os.path.join(PROTO, "synth-layers.js"), "w") as f:
            f.write("// Synthesized layers (loop-engine.js, browser OfflineAudioContext), one seamless 8-bar loop each, base64 AAC.\n")
            f.write("window.SYNTH_LAYERS = {\n" + "".join(f'  "{k}": "{b}",\n' for k, b in layers) + "};\n")
    print(f"done: encoded {n} files, loop-bounces.js + synth-layers.js rebuilt", flush=True)


def build_js(data):
    """loop-bounces.js: every bounced rhythm set (5 base64 AAC loops each) for the knob player."""
    sets = []
    for st in data["sets"]:
        d = os.path.join(OUT, "sets", slug(st["name"]))
        files = [os.path.join(d, f"loop-i{k}.m4a") for k in range(5)]
        if all(os.path.exists(f) for f in files):
            sets.append((st["name"], [base64.b64encode(open(f, "rb").read()).decode() for f in files]))
    cur = data["sets"][data.get("current", 0)]["name"]
    with open(os.path.join(PROTO, "loop-bounces.js"), "w") as f:
        f.write(f"// Bounced rhythm sets for the knob player: 5 loops each (8 bars, {data.get('bpm', rt.BPM)} BPM, ghost velocity {data.get('ghostVel', 34)}), from taiko-patterns.json.\n")
        f.write("// Strezov Thunder X3M Taiko Freebie (Kontakt) + Spitfire LABS Percussion / Hand Bells (Splice INSTRUMENT), via DawDreamer (tools/bounce_taiko.py). Base64 AAC.\n")
        f.write("window.LOOP_SETS = [\n")
        for name, b64 in sets:
            f.write(f"  {{ name: {json.dumps(name)}, loops: [\n" + "".join(f'    "{b}",\n' for b in b64) + "  ] },\n")
        f.write("];\n")
        f.write(f"window.LOOP_DEFAULT = {json.dumps(cur)};\n")


if __name__ == "__main__":
    if "--init" in sys.argv: init_patterns()
    elif "--encode" in sys.argv: encode()
    else: bounce("all" if "--all" in sys.argv else "current")
