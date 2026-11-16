# Harmony Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A soft four-voice chord on top of Nature mode where the interval says whether two signals move together (A) and a tension voice says how far the main signal is from normal (B); version 2 adds a 2025 monsoon story whose tension is read from NASA EIC anomaly frames.

**Architecture:** Engine in a new self-contained file `playground/audio/harmony.js` (`window.Harmony`), fed every ~120 ms by the page with three numbers. EIC monsoon is a new story `c3_monsoon_eic` built by a new pipeline. `playground/c4-src/template.html` is wired LAST, after the other background agent (Jose breathing + Iberia) has finished editing it.

**Tech Stack:** Web Audio API, three.js page, Python + numpy pipelines, ffmpeg/PIL for frames.

**Spec:** docs/superpowers/specs/2026-11-15-harmony-layer-design.md

## Global Constraints
- No melodies, no percussion, no high voices: all pad voices between D2 (MIDI 38) and D4 (MIDI 62).
- Rooted on D in the story's scale (`SCALE` / `STORY_MODE` in template.html).
- Every change ramps over seconds (setTargetAtTime time constants >= 0.8 s); nothing jumps.
- Dissonance = a half-step rub plus a few cents detune; never a cluster or alarm.
- No invented normal: stories without a sigma normal band get no tension voice.
- No em dashes in user-visible text. Honesty rules: data never faked; footers state methods.
- Do not commit or push.

## Review Focus
- Story change / explore screen: chord must fade out (not cut) and restart cleanly on the next story.
- Mute and master volume: harmony must follow `Music.master` and mute.
- Gaps in the main signal (null values): tension holds and eases to zero, never spikes.
- Music mode (not Nature): harmony layer off.
- EIC frame missing for a day: tension eases to zero; no error.

---

### Task 1: Harmony engine (V1 core)

**Files:**
- Create: `playground/audio/harmony.js`

**Interfaces:**
- Produces: `window.Harmony` with `start(ctx: AudioContext, dest: AudioNode): void`, `setScale(scale: number[]): void` (semitone offsets from D, e.g. `[0,1,3,5,7,8,10]`), `set({main: number /*0..1 position of main signal in its lane*/, link: number /*0..1 rolling link strength, same as the chart thread*/, tension: number|null /*0..1 distance from normal; null = no normal band*/}): void`, `swell(): void` (lock-in), `setOn(on: boolean): void`.

- [ ] **Step 1:** Write `harmony.js`: four voices (root D2 or D3; main voice = chord tone chosen by `main` within D3..A3; partner = consonant interval above main (fifth if in scale, else third or octave) blended toward a half-step rub + 8 to 15 cents detune as `link` goes 0.7 -> 0.3; tension voice = the scale note a half-step from a chord tone, gain proportional to `tension`, silent if null). Each voice: two detuned saws + one triangle through lowpass ~700-1200 Hz, slow attack; output gain about 0.12.
- [ ] **Step 2:** Verify: `node --check playground/audio/harmony.js` prints nothing; a small node test with a stubbed AudioContext is not required.

### Task 2: V2 data: monsoon 2025 with EIC anomaly frames

**Files:**
- Create: `data-pipeline/c3_monsoon_eic.py`, output `playground/stories/c3_monsoon_eic.js`
- Cache: `/Users/mykhayloolefirenko/projects/earth-jukebox-cache/c3_monsoon_eic/`

**Interfaces:**
- Produces story data like `c3_monsoon` (see data-pipeline/STORY_FORMAT.md) for 2025-01-01..2025-12-31 daily, plus a new layer `{"id":"eic","type":"eicframes","name":"NASA EIC rain anomaly","frames":[{"t": step, "img": "data:image/jpeg;base64,..."}], "colorbar":{"stops":[[r,g,b,value],...]}, "source":"SVS/EIC 4897"}`.

- [ ] **Step 1:** Verify EIC 4897 frames: download one `flatcomposite` (no dates) frame and the anomaly colour bar if listed (API `https://svs.gsfc.nasa.gov/api/4897`); confirm equirectangular 3600x1800 and what "variation"/"anomaly" encodes; if the anomaly frames are only available with burned-in dates or the meaning is unclear, report and stop Task 2.
- [ ] **Step 2:** Fetch every 3rd day Jun-Oct 2025 (plus monthly Jan-May, Nov-Dec), downsize to 2048x1024 JPEG (quality ~80) and embed; build the colour-to-value table from the colour bar.
- [ ] **Step 3:** Re-use `c3_monsoon.py` logic for 2025 for wind (ERA5), greenness (MODIS NDVI) and stored water (GRACE-FO) where available without Earthdata login problems; anything missing is listed in `gaps`.
- [ ] **Step 4:** Verify: `node --check playground/stories/c3_monsoon_eic.js`; node prints frame count, date span, layers.

### Task 3: Wire into the page (after the other agent finishes)

**Files:**
- Modify: `playground/c4-src/template.html` (Music.load, frame loop, enterExplore, STORIES, a new `eicframes` layer type)

- [ ] **Step 1:** Load `audio/harmony.js` with Nature; `Harmony.setScale(SCALE)` on story change; every ~120 ms in Nature mode `Harmony.set({main, link, tension})` with `link` = the thread's rolling strength, `tension` = clamp((|z| - 1) / 3) from `heroNorm` sigma (null without sigma); `Conn.lockIn` -> `Harmony.swell()`; off in Music mode and on the explore screen.
- [ ] **Step 2:** Faint glow on the normal band proportional to tension (chart canvas).
- [ ] **Step 3:** `eicframes` layer: globe texture of the frame nearest in time (held, 15% blend like fields), organic edge not needed (global); in `c3_monsoon_eic` tension = anomaly read from the current frame at the listening point via the colour table (|anomaly| scaled 0..1).
- [ ] **Step 4:** Add preset `c3_monsoon_eic` (visible), KID text and notes, footer stating EIC source and mapping.
- [ ] **Step 5:** `python3 playground/c4-src/build.py`; extract module script and `node --check`; open in Safari.
