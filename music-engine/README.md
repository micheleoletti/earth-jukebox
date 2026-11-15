# Earth Jukebox music engine

One knob turns Earth data into music. The knob is **intensity** (0 to 1): calm planet at the low end, stressed planet at the high end. Everything is in **D, 96 BPM, 8-bar loops (20 s)**, so every layer fits with every other one and can be faded in or out at any moment without breaking the groove.

The engine is a set of pre-rendered, seamless loops plus a small Web Audio player. Nothing is generated note by note at runtime, so it is cheap to run in the browser and sounds the same everywhere.

The default mix (the "final" configuration, 2026-11-14) is **all synthesized**: synth drums in the *Tribal 3+3+2* rhythm plus 14 synth layers. Sampled drones (Spitfire LABS) are available but switched off.

## Quick start

Open the player directly, no server needed:

```bash
open -a Safari music-engine/prototype/loop-player.html
```

Press **Play**, then turn the knob (drag, scroll, arrow keys, or keys `1` to `5`). Pick a rhythm above the knob. Switch layers on and off in the panels below it.

To edit rhythms or re-render loops you need the local dev server:

```bash
python3 music-engine/tools/serve.py 8766
```

Then open `http://localhost:8766/loop-player.html` (player) and `http://localhost:8766/piano-roll.html` (rhythm editor).

## How it sounds: the three layer groups

### 1. Drums (one rhythm at a time)

Six rhythms, each bounced at 5 intensities (Calm, Stirring, Pulse, Driving, Epic). The knob crossfades between the 5 versions of the selected rhythm.

| Rhythm | Feel |
|---|---|
| Original | the first groove |
| Heartbeat | deep "lub-dub" pulse |
| War march | steady quarter notes with accents |
| Gallop | galloping 16ths with ghost notes |
| Half-time epic | slow, heavy, big hits |
| **Tribal 3+3+2** (default) | 3+3+2 accents |

Drums are synthesized (`prototype/synth-drums.js`): 9 voices from *Deep (big)* to *Rim*, each a pitch-swept drum skin with stick noise and an attack click, through light saturation and a hall reverb. Successive hits vary slightly in pitch, like round robins.

### 2. Synth layers (each switchable)

Each layer is one seamless loop. The knob sets its level along its own curve (knob positions 1 to 5).

| Layer | Plays at (1 → 5) | Default volume |
|---|---|---|
| Sub bass | everywhere | 0.30 |
| Synth pad | strongest when calm, fades as intensity rises | 0.70 |
| Chimes | calm end only | 0.90 |
| Low pulse | 2 to 5, peaks at 3 | 0.70 |
| Brass stabs | 4 to 5 | 0.90 |
| Braams | 4 to 5 | 0.60 |
| Riser | 5 only | 1.00 |
| Synth trumpets (detuned field) | builds from calm to full | 0.50 |
| Shimmer (high air) | mostly calm | 0.70 |
| Glass pad (high) | calm to mid | 0.35 |
| FM bells | everywhere, peak in the middle | 0.60 |
| Mallet arpeggio | 2 to 5 | 0.35 |
| Plucks | 3 to 5 | 0.50 |
| Sparkle | everywhere, most at 3 to 4 | 0.90 |

In the default mix all 14 are on.

### 3. Drones (optional, off by default)

Soft held notes from Spitfire LABS (Textural Pads: Deneb, Petrichor, Saudade; Trumpet Fields: faded, steady). Each drone can play D two octaves down, D one octave down, D, F♯ and A, with its own volume, "follow knob" amount (louder or quieter as intensity rises) and tone (low-pass). Trumpet Fields is a recorded ensemble with natural detuning between players; the synth trumpets layer is the in-tune replacement.

## Using the engine in the app

`prototype/loop-player.html` is the reference implementation. To drive the music from data, do what the player does:

1. Load the data files: `loop-bounces.js` (drums: `window.LOOP_SETS`), `synth-layers.js` (`window.SYNTH_LAYERS`), `drones.js` (`window.DRONES`, optional), `engine-config.js` (`window.ENGINE_CONFIG`, the default mix). All audio is base64 AAC, so it works from `file://`.
2. On a user gesture (required on iOS), create an `AudioContext`, decode the loops of the chosen rhythm and the enabled layers, and start every loop with `loop = true` at the same start time `t0`. Start anything added later at offset `(now - t0) % loopLength` so it stays in phase.
3. Map the data signal to intensity `x` in 0..1 and call `setV(x)` in the player, which does:
   - drums: crossfade weights over the 5 versions, `p = x * 4`, `i = floor(p)`, weight `1 - (p - i)` on version `i` and `p - i` on version `i + 1`;
   - each synth layer: `gain = volume * curve(x)` where `curve` interpolates its 5 points (table above);
   - each drone: `gain = volume * follow(x)`.
   Ramp gains with `setTargetAtTime(…, 0.12–0.25 s)` so nothing clicks.
4. Switch rhythm with `switchRhythm(i)`: the new set starts in phase and crossfades over about 1.2 s.

Memory: one rhythm (5 loops) is about 40 MB decoded, each synth layer about 8 MB. Only the selected rhythm and the enabled layers are decoded.

## Editing rhythms: the piano roll

`http://localhost:8766/piano-roll.html`

- **Rhythm** menu picks the set; tabs 1 to 5 are its intensities (keys `1`–`5`). **+ Copy** duplicates a rhythm.
- Click to draw, drag to move, drag a right edge for length, right-click (or Ctrl+click) to delete, hold and drag to delete many. Shift/Cmd+drag selects, Cmd+B duplicates, arrows nudge, Cmd+Z undoes.
- **Velocity lane** at the bottom: drag over any notes to set velocity.
- **Ghost notes** are hollow and marked `g`: press `G` to toggle selected notes. The **ghost vel** knob sets how loud all ghost notes play.
- Click a row name to hear it (left = soft, right = loud); right-click a row name to clear that row.
- **Tempo** box/slider (40–200 BPM).
- **Bounce to knob** renders the selected rhythm's 5 intensities in the browser and rebuilds `loop-bounces.js`; **Bounce all** does every rhythm. Reload the player afterwards.

Patterns are stored in `prototype/taiko-patterns.json`.

## Changing the default mix

1. Run the dev server and open the player from `http://localhost:8766/loop-player.html`.
2. Set rhythm, layers, volumes and drones as you like. The player saves the current mix to `prototype/engine-config.json` on every change.
3. Copy that JSON into `prototype/engine-config.js` (`window.ENGINE_CONFIG = {…};`). That file is the default for anyone who has not changed settings in their own browser.

Settings a listener changes are kept in their browser (`localStorage`), so they override the defaults on that machine only.

## Re-rendering the synth layers

The synth layers come from `prototype/loop-engine.js` (Web Audio, rendered offline in the browser).

1. Dev server running, open `http://localhost:8766/bounce.html`.
2. Click **Bounce synth layers**. Each layer renders as its own seamless loop, they are saved to `prototype/bounces/synth-*.wav`, encoded to AAC and packed into `synth-layers.js`.

To add a layer: add its sound under the `only === '<id>'` branch in `loop-engine.js`, add it to the `LAYERS` list in `bounce.html`, and add a row (label, curve, default volume, on/off) to `LAYERS` in `loop-player.html`.

## Files

| Path | What it is |
|---|---|
| `prototype/loop-player.html` | the engine player: knob, rhythm picker, synth layers, drones |
| `prototype/piano-roll.html` | rhythm editor (FL Studio style) |
| `prototype/bounce.html` | renders synth layers (and the older all-in-one loops) in the browser |
| `prototype/synth-drums.js` | synthesized drum voices (shared by editor preview and bounce) |
| `prototype/loop-engine.js` | synthesized layers, offline renderer, WAV writer |
| `prototype/taiko-patterns.json` | the 6 rhythms × 5 intensities, rows, tempo, ghost velocity |
| `prototype/loop-bounces.js`, `synth-layers.js`, `drones.js` | the bounced audio, base64 AAC |
| `prototype/engine-config.js` | the default mix |
| `prototype/bounces/` | the same audio as files (`sets/<rhythm>/loop-iN.m4a`, `synth-*.m4a`, `drone-*.m4a`) |
| `prototype/intensity-lab.html` | first sound experiments (three synth approaches); not part of the engine |
| `tools/serve.py` | dev server: static files + save/encode endpoints |
| `tools/bounce_taiko.py` | patterns file tools: `--init` writes the rhythm sets, `--encode` packs browser bounces, no flag renders sampled rhythms through Kontakt |
| `tools/render_drones.py`, `build_drones_js.py` | render and pack the LABS drones |
| `tools/juce_state.py`, `instruments.py`, `render_oneshots.py`, `render_taiko.py`, `plugin_setup.py`, `labs_keymap.py` | headless VST hosting (DawDreamer) used for the sampled options |
| `research/` | background research (instruments, real-time vs stems, harmony and mix) |

## Sampled options (not in the default mix)

The tools can also render real instruments without a DAW, by hosting plugins headless with DawDreamer (`tools/.venv`):

- **Strezov Thunder X3M Taiko Freebie** (Kontakt Player): `tools/taiko.state`, sampled taiko rows, `bounce_taiko.py` renders them. Set a row's `"inst"` to `"thunder"` in `taiko-patterns.json` to use it.
- **Spitfire LABS** via Splice INSTRUMENT: presets are chosen from code by building the plugin state (`juce_state.py`); `states/labs-percussion.xml` is a real saved state for packs whose internal patch name differs from the file name.

Licences: the bounced loops can be used in the app. Raw samples (`prototype/samples/`) are a local editing aid only and must not be shipped; they are in `.gitignore`.

## Known limits

- Synth layers and drones are rendered at 96 BPM / 20 s. If you change the tempo in the piano roll, re-bounce the synth layers with a matching tempo in `loop-engine.js` (`BPM`), or the layers will drift against the drums.
- iOS: audio must start from a tap; the player sets `navigator.audioSession.type = "playback"` so the silent switch does not mute it.
- Audio files are large (drums about 15 MB, synth layers about 6 MB, drones about 9 MB as base64). For production, serve the `.m4a` files directly instead of the `.js` bundles.
