# 3D globe performance guide

Rules and lessons for every story we add to the 3D globe, so it runs well on all devices (judges' laptops, integrated GPUs, mid-range phones), not just on an M-series Mac.
Learned while building story C4 "The Planet Breathing" (`breathing.html`).

## Budget (respect these for every story)

| Budget | Limit | Why |
|---|---|---|
| Frame time | ≤ 16.7 ms desktop (60 fps), ≤ 33 ms phone (30 fps) | Smooth motion |
| Triangles per frame | ≤ 0.5–1 M | Integrated and mobile GPUs |
| Vertex shader runs per frame | ≤ 1–2 M | Each run is real work (see "indexed geometry") |
| Draw calls | < 100 | CPU overhead per call |
| Pixel ratio | cap at 1.5 (desktop), 1.0–1.5 (phone) | Ratio 2 = 4× the pixels of ratio 1 |
| Full-screen effects (bloom, blur) | half resolution, off on phones | They cost per pixel, every frame |
| GPU memory | ≤ 200–250 MB total | iOS Safari kills the 3D scene ("context lost") above this |
| Max texture size | ≤ 4096 px | Some Android GPUs refuse larger |
| Page download | < 10 MB | Judges open it on unknown networks |

Measure on a Mac M4, then assume a typical judge laptop is 3–5× slower. So the M4 target is **≤ 5–8 ms per frame**.

## C4 results (reference point)

Mac M4, browser pane, forced GPU sync, median of 40 frames.

| Step | Triangles | Frame | GPU memory (est.) |
|---|---|---|---|
| First version: 98k detailed trees (trunk + 3 cones / 2 blobs), ratio 2 | 5.0 M | 32 ms | ~350 MB |
| Minimal indexed tree shapes + skip far side of globe | 0.88 M | 14.3 ms | ~350 MB |
| + pixel ratio 1.5, half-res bloom, 4096 single-channel mask, 3 resident month textures | 0.88 M | **8.8 ms** | **~85 MB** |

Cost breakdown of the final version: trees ~1 ms, smog shells ~3 ms, bloom ~2–3 ms, globe + atmosphere + rest ~3 ms.

## Techniques that worked (reuse them)

### Many objects (trees, markers, particles)
- **One draw call for all of them**: `InstancedBufferGeometry` with per-instance attributes (direction on the sphere, data values, random seed). Never one mesh per object.
- **Do the per-object maths in the vertex shader**, driven by uniforms (`uMonth`, `uTime`). Then animating 100k objects costs nothing on the CPU: no per-frame JS loops, no buffer re-uploads.
- **Pack time series into attributes**: 12 monthly values = 3 × `vec4`. Interpolate between months in the shader.
- **Keep shapes minimal**: 5–8 triangles each (a 5-sided cone, an octahedron). At globe scale extra detail is invisible but costs linearly.
- **Indexed geometry** (`mergeVertices`, `geo.index`): a shape with shared corners runs the vertex shader once per corner, not 3 times per triangle. Our detailed tree was ~150 shader runs; the indexed minimal one is 6.
- **Skip the far side of the globe** in the vertex shader: if the object is beyond the horizon, output a position off screen and `return` before the heavy work.
- **Rough cost**: instances × corners per shape = vertex shader runs. Keep that under ~1 M.

### Textures
- **Time-varying maps** (monthly data): keep only the current, next and following frame on the GPU, `dispose()` the rest, and `renderer.initTexture()` the next one ahead of time. 12 × 2048² RGBA = 134 MB; 3 of them = 33 MB.
- **Masks and single-value maps**: `texture.format = THREE.RedFormat` (1 byte per pixel instead of 4).
- **Crisp coastlines without huge textures**: a separate land mask with soft (resampled) edges, sharpened in the shader with `smoothstep` + `fwidth`. The colour texture can then stay at 2048.
- **Fill water pixels with nearby land colour** before shrinking a land-only texture, so colours don't bleed at coasts.
- **Ship JPEG for colour, PNG only for masks.**

### Full-screen and transparent layers
- **Bloom at half resolution**: `bloom.setSize(w * PR * .5, h * PR * .5)` after `composer.setSize`.
- **Haze, smog, clouds = 1–2 sphere shells with a noise shader**, not thousands of particle sprites. Cheaper, and it reads as one continuous layer. (Our sprite version looked like scattered puffs.)
- **Transparent layers cost per pixel they cover**: every extra full-globe shell adds ~1–1.5 ms at ratio 1.5. Budget 2–3 shells max.

## Checklist for a new story

1. Estimate before building: instances × corners per shape, number of textures × size × 4 bytes × 1.33 (mipmaps), number of transparent full-globe layers.
2. Build at full quality, then measure (snippet below).
3. If over budget, cut in this order: pixel ratio → bloom → shape detail → instance count → texture resolution → number of transparent layers.
4. Keep data processing offline (Python pipeline). Ship small pre-processed files; never parse large rasters in the browser.
5. Inline data into the HTML only while the page stays < 10 MB; above that, load files next to the page.

## How to measure

The page exposes `window.__dbg = {renderer, composer}`. Paste in the browser console:

```js
const {renderer, composer} = window.__dbg, gl = renderer.getContext(), px = new Uint8Array(4);
const run = (f, n = 40) => { const t = []; for (let i = 0; i < n; i++){ const a = performance.now(); f();
  gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); t.push(performance.now() - a); }
  t.sort((x, y) => x - y); return t[n >> 1].toFixed(1) + ' ms'; };
run(() => composer.render(), 10);
console.log('frame', run(() => composer.render()), renderer.info.render, renderer.info.memory);
```

- `readPixels` forces the GPU to finish, so the time is real GPU + CPU time per frame.
- Toggle objects (`obj.visible = false`) and re-run to get each layer's cost.
- A hidden browser tab throttles `requestAnimationFrame`, so fps counters lie there; the forced-sync loop above does not.

## Not done yet (next steps)

- **Automatic quality levels**: measure frame time in the first 2 s, then step down (pixel ratio → bloom → half the instances → fewer shells).
- **Phone test**: never run on a real phone yet.
- **Level of detail** (detailed shapes near the camera, minimal far away) if close-up views become important.

## All 12 stories (measured 2026-11-15, overnight build)

How: Chrome headless (`--headless=new --use-angle=metal`, real GPU) driven by Puppeteer on this Mac, page opened with `?perf#<story>`.
The page plays the story for 5 s, then logs `window.__perf`: the median of 30 forced-sync renders (render + `gl.readPixels`, so GPU time is included),
the median JS time of one frame before rendering (particles, streaks, chart, labels), and `renderer.info` for one full composed frame.
Headless reports a small screen, so by default the page runs its mobile settings there (9k particles, pixel ratio 1.25);
`&desktop` forces desktop settings (20k particles, pixel ratio 1.5 on a 2x display).

Desktop window 1440x900, device pixel ratio 1 (render pixel ratio 1, mobile settings):

| Story | GPU+render (ms) | JS per frame (ms) | Draw calls | Triangles | Points |
|---|---|---|---|---|---|
| E1 Canada smoke | 3.7 | 3.4 | 21 | 50k | 44k |
| E2 Hurricane Ian | 4.0 | 1.7 | 24 | 67k | 5k |
| E3 Hunga Tonga | 4.0 | | 21 | 52k | 5k |
| E4 Black Summer | 3.5 | 3.4 | 20 | 51k | 44k |
| E5 Po Valley | 3.5 | 1.2 | 20 | 69k | 5k |
| C1 Tides | 4.3 | | 19 | 52k | 5k |
| C2 City breathing | 3.0 | | 20 | 51k | 5k |
| C3 Monsoon | 3.7 | 1.2 | 20 | 82k | 5k |
| C4 Africa fire belt | 4.5 | | 19 | 66k | 35k |
| C5 Snow | 4.9 | | 19 | 59k | 5k |
| C0 Planet Breathing | 8.0 | 0.9 | 21 | 530k | 5k |
| E0 Wuhan | 6.7 | | 18 | 69k | 5k |

Blank JS cells: that run happened before the JS timer was added (these stories have no smoke particles; the measured stories without particles take 0.9 to 1.7 ms).

Worst cases at device pixel ratio 2 with desktop settings (`&desktop`, render pixel ratio 1.5, 20k particles):

| Story | GPU+render (ms) | JS per frame (ms) | Total |
|---|---|---|---|
| E1 Canada smoke | 5.4 | 5.9 | ~11 ms |
| E4 Black Summer | 5.5 | 5.9 | ~11 ms |
| C0 Planet Breathing (2 trees per cell, 0.97 M triangles) | 14.9 | 0.9 | ~16 ms |

All stories are under 16 ms on this Mac. The Breathing story is at the edge only in desktop mode on a Retina screen (headless; the earlier in-browser measure was 8.8 ms).
If it stutters for real, the first cut is 1 tree per cell (already used on phones, halves the triangles).
Smoke particles cost JS time (CPU advection, ~0.3 ms per 1,000 particles): 20k desktop, 9k phone, 6k reduced motion.

First load: `breathing.html` 1.8 MB + three.js from the CDN. Story files 0.1 to 4.6 MB, loaded on demand. Sound bundles 9.1 MB, loaded on the first tap.

## Phone checklist (to test on a real iPhone)

1. Open the page in Safari (local file via AirDrop/Files may block scripts: serve it, `python3 -m http.server 8765 --directory playground`, and open `http://<mac-ip>:8765/breathing.html`).
2. Landing: cards readable, one tap starts a story AND the sound (silent switch on: sound must still play, we set `audioSession.type = playback`).
3. Sound: no crackle while the globe moves; the loops stay in time when the intensity changes; mute and volume work.
4. Memory: switch through all 12 stories twice; the page must not reload or show a black globe ("WebGL context lost"). Breathing (trees) and Wuhan (4 MB) are the heaviest.
5. Frame rate: drag the globe during E1 and E4 (smoke particles) and Breathing (trees); it should feel smooth (30 fps or better).
6. Chart: lanes readable at phone width, scrubbing with a finger works, layer chips switch layers and their voices.
7. Rotation to landscape and back: the layout and the chart resize correctly.
8. VoiceOver: the story announcements are read, the layer chips and buttons have names, the Sources panel can be opened and closed.
9. Reduced motion (Settings > Accessibility > Motion): no auto-rotation, no camera flight.
10. Battery/heat after 5 minutes of playback.
