# Real-time generation vs pre-rendered stems (Earth Jukebox)

Researched 2026-11-14. Scope: client-only Tone.js, laptop browsers + iOS Safari, 1-2 day build.

## TL;DR

1. Go hybrid: short pre-rendered loops per instrument family (vertical layering, gain = data level x on-screen weight) + live Tone.js one-shots for event data (lightning strikes) + live filter/detune/playbackRate modulation from continuous data.
2. Memory is the binding constraint, not CPU: decoded AudioBuffer = float32, **~21 MB per stereo minute at 44.1k (23 MB at 48k)**, ~22x the AAC file. Keep loops 8 bars (~20 s), mono where possible, total decoded budget < ~150 MB.
3. All loops in AudioBuffers (Tone.Player synced to Tone.Transport), never `<audio>`/MediaElementSource for layered stems: media elements are not sample-accurate and drift.
4. Zoom = gain automation (`rampTo` 0.3-1 s), not start/stop; all stems same BPM/key/length so anything can fade in anytime and stay in sync.
5. iOS: `Tone.start()` inside a tap, set `navigator.audioSession.type = "playback"` (else ringer switch mutes Web Audio), ship AAC `.m4a` (or FLAC for gapless loops), not WebM Opus or MP3.

## 1. Adaptive music architectures

| Pattern | How it works | Maps to "data drives music" | Maps to "zoom shrinks orchestra" | Hackathon cost |
|---|---|---|---|---|
| Vertical layering (re-orchestration) | N synchronized stems of one piece; per-stem gain driven by state/RTPC. Wwise: tracks inside a Music Segment; FMOD: tracks on one timeline + parameter-automated volume | Data value -> stem gain (and filter cutoff). Smooth, continuous | Perfect fit: each instrument = stem; viewport weight multiplies gain | Low. Needs stems composed to the same grid |
| Horizontal resequencing | Switch between clips/sections on bar/beat boundaries. Wwise: Music Switch/Playlist Containers + transition rules; FMOD: transition markers/regions + quantization | Data thresholds pick section (calm / storm). Discrete, coarse | Weak: changes section, not instrumentation | Medium: many clips, transition logic |
| Fully generative | Notes computed live (MIDI-like events) -> Tone.Synth/Sampler | Richest: data -> pitch, density, rhythm, velocity directly | Fit: voices for off-screen regions simply not scheduled | Medium-high: musical quality takes composing time; samplers need sample sets anyway |
| Hybrid (common in games) | Bounced bed loops + live percussion/stingers + live DSP (filter, detune, playbackRate) | Bed = continuous signals; events = discrete data (strikes, quakes) | Bed stems fade; events filtered by viewport | Low-medium. Best quality per hour of work |

Notes:
- Vertical layering's known weakness: layers must work in every combination, so compose them sparse and in the same key/register lane per family.
- Horizontal switching needs quantized transitions (next bar) to sound musical; Tone.Transport `scheduleOnce(t, "@1m")` gives that for free if wanted later.

## 2. Browser memory and formats

### Decoded AudioBuffer cost (float32, non-interleaved, per MDN)

bytes = sampleRate x channels x 4 x seconds

| Content | 44.1 kHz | 48 kHz |
|---|---|---|
| 1 min mono | 10.6 MB | 11.5 MB |
| 1 min stereo | 21.2 MB | 23.0 MB |
| 8-bar loop @ 90 BPM (21.3 s) stereo | 7.5 MB | 8.2 MB |
| 16-bar loop @ 90 BPM (42.7 s) stereo | 15.1 MB | 16.4 MB |
| 12 stems x 8 bars stereo | 90 MB | 98 MB |
| 12 stems x 8 bars mono (pan in Web Audio) | 45 MB | 49 MB |
| 12 stems x 3 min stereo | 762 MB | 829 MB (too much for iOS) |

Compressed on the wire: AAC 128 kbps ~0.96 MB/min, Opus 96 kbps ~0.72 MB/min, FLAC ~50-60% of WAV (~5 MB/min stereo). Decoded/compressed ratio ~20-25x for lossy.

### Limits and gotchas

| Topic | Fact / number | Implication |
|---|---|---|
| AudioBuffer intended size | MDN: designed for snippets "typically less than 45 s"; longer -> MediaElementAudioSourceNode | Loops 8-16 bars fit the intended use |
| decodeAudioData spike | Encoded ArrayBuffer + full decoded float32 output resident at once; output resampled to the AudioContext rate (iOS hardware often 48k, so 44.1k files get resampled) | Decode sequentially, not 12 in parallel; export stems at 48 kHz to skip resampling |
| iOS Safari tab memory | No documented per-tab cap; WebKit/iOS kill the content process under memory pressure (page reloads). Anecdotally ~1-1.5 GB on recent iPhones, far less on old/low-RAM devices | Target < 150 MB decoded audio total; test on a real iPhone |
| Chrome desktop | Large renderer budget (GBs on 64-bit); AudioBuffers live outside JS heap | Laptops are not the problem |
| MediaElementSource streaming | Low memory (decoded progressively), but start time not sample-accurate, N elements drift apart, `<audio loop>` seam often audible, needs CORS (`crossorigin`) or outputs silence | OK for one long ambient bed; wrong for synced stems |
| Keeping N stems in sync | AudioBufferSourceNodes started with the same `when` on the audio clock are sample-locked. Tone: `player.sync().start(0)` on Transport | Start all stems at once, mute with gain; or start late with offset (Tone handles offset on synced players) |
| Gapless loops | MP3 encoders add padding (hundreds to 1000+ samples); AAC adds priming (typically 2112 samples) -> click/gap at loop point | Use FLAC/WAV for loops, or AAC with measured `loopStart`/`loopEnd` trims |
| Opus | WebM Opus in `decodeAudioData` on Safari: inconsistent across 15.x-17.x, reported consistent from ~17.4; multichannel still refused on iOS 18 (WebKit bugs 226922, 238546, 327697) | Avoid as sole format; AAC `.m4a` is the safe universal lossy choice |
| MP3 / AAC / FLAC support | All three decode in Chrome, Firefox, Safari (macOS + iOS) | AAC for long beds, FLAC for short gapless loops |
| Lazy loading | Load "core" stems first (start playing), stream the rest after; release far-off-region buffers by dropping references | Time-to-first-sound < 2-3 s on 4G with ~3-5 MB first payload |

## 3. CPU, latency, iOS unlock

| Topic | Fact / number | Implication |
|---|---|---|
| Render quantum | Web Audio renders in 128-frame blocks: 2.9 ms @ 44.1k, 2.67 ms @ 48k. Whole graph must finish inside that or you get glitches | Budget nodes, not samples |
| Sampler voices | `Tone.Sampler` = one native AudioBufferSourceNode (+ gain) per note, pitch-shifted from nearest sample via playbackRate. Cheap. `Tone.PolySynth` default `maxPolyphony` 32 | Sampler polyphony is rarely the bottleneck; dozens of voices fine on iPhone, hundreds on laptop (rule of thumb, not a spec) |
| Expensive nodes | ConvolverNode (long IR), many oscillator synths with filters/LFOs, per-voice effects, analyzers | One shared reverb bus; prefer samplers over complex synths on mobile |
| Muted stems | A playing source at gain 0 still costs CPU (small for buffer sources) | 12 always-running buffer stems is fine; stop only if > ~20 |
| AudioWorklet | Custom DSP on audio thread (Chrome 66+, Safari 14.1+). Tone.js core uses native nodes, few worklets | Not needed for this project; skip |
| Scheduling latency | Tone.Context `lookAhead` default 0.1 s; `latencyHint` "interactive" | Events scheduled ~100 ms ahead; fine for data-driven music, set lookAhead lower only for tap-to-play |
| Autoplay unlock | AudioContext starts "suspended" until a user gesture; must call `resume()` (`Tone.start()`) inside click/tap handler (Chrome policy, same in Safari) | "Tap to listen" splash screen, mandatory |
| iOS ringer switch | Default audio session type `ambient`: Web Audio muted when phone is on silent. `navigator.audioSession.type = "playback"` (Safari 16.4+) fixes it; regressions reported on some 17.x | Set it before `Tone.start()`; tell users to unmute as fallback |
| iOS interruptions | Context goes "interrupted"/"suspended" on calls, backgrounding, lock screen | On `visibilitychange`/`statechange`, call `Tone.context.resume()` from next tap |

## 4. Recommendation for a 1-2 day build

1. **Grid**: one tempo (e.g. 90 BPM), one key, 8-bar loops (21.3 s), all exported 48 kHz, same length. Mono stems for anything that will be panned by region.
2. **Bed stems (vertical layering)**: ~8-12 `Tone.Player`s, `loop: true`, `.sync().start(0)`, each through its own `Tone.Gain` -> family bus -> shared reverb send -> master + `Tone.Limiter`. Format: FLAC (gapless) or AAC with trimmed `loopStart/loopEnd`. Decoded total ~45-100 MB.
3. **Data mapping**: continuous signals (wind speed, SST, ocean currents) -> stem gain, `Tone.Filter` cutoff, small `playbackRate`/detune. Discrete events (lightning strikes) -> live `Tone.Sampler` or `MembraneSynth`/`NoiseSynth` hits, quantized to 16ths (`Transport.scheduleOnce(cb, "@16n")`), velocity = strike intensity.
4. **Zoom**: for each instrument, `weight = share of its region's data inside viewport` (0-1); `gain.rampTo(dataLevel * weight, 0.5)`. Off-screen = gain 0, keep playing (stays in sync, instant fade-in). Lightning events outside viewport simply not triggered.
5. **Start**: splash "Tap to listen" -> `navigator.audioSession && (navigator.audioSession.type = "playback")`; `await Tone.start()`; load 3-4 core stems first, start Transport, lazy-load the rest sequentially.
6. **Skip**: horizontal resequencing, AudioWorklet, MediaElementSource, WebM Opus, long (> 45 s) stems, per-voice effects.
7. **Fallback if stems are not ready**: fully generative bed with `Tone.PolySynth` pads + `Tone.Sampler` from a small sample set; same gain/zoom plumbing, swap source later.

## Sources

- MDN, AudioBuffer (float32 PCM, < 45 s guidance): https://developer.mozilla.org/en-US/docs/Web/API/AudioBuffer
- MDN, BaseAudioContext.decodeAudioData (resamples to context rate, detaches buffer): https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/decodeAudioData
- MDN, MediaElementAudioSourceNode: https://developer.mozilla.org/en-US/docs/Web/API/MediaElementAudioSourceNode
- MDN, AudioBufferSourceNode (loopStart/loopEnd, start(when, offset)): https://developer.mozilla.org/en-US/docs/Web/API/AudioBufferSourceNode
- MDN, Web audio codec guide (AAC, MP3, Opus, FLAC support): https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Audio_codecs
- MDN, Audio Session API / AudioSession.type: https://developer.mozilla.org/en-US/docs/Web/API/Audio_Session_API , https://developer.mozilla.org/docs/Web/API/AudioSession/type
- MDN, Autoplay guide: https://developer.mozilla.org/en-US/docs/Web/Media/Autoplay_guide
- MDN, AudioWorklet: https://developer.mozilla.org/en-US/docs/Web/API/AudioWorklet
- W3C Web Audio API spec (render quantum 128 frames): https://www.w3.org/TR/webaudio/
- Chrome, Web Audio autoplay policy: https://developer.chrome.com/blog/web-audio-autoplay
- Web features explorer, Audio session (Safari 16.4): https://web-platform-dx.github.io/web-features-explorer/features/audio-session
- WebKit bug 237322, Web Audio muted by iOS ringer: https://bugs.webkit.org/show_bug.cgi?id=237322
- WebKit bug 252746, inconsistent playback when muted: https://bugs.webkit.org/show_bug.cgi?id=252746
- WebKit bug 262781, silent mode compressed vs uncompressed: https://bugs.webkit.org/show_bug.cgi?id=262781
- WebKit bug 226922, Safari 15 breaks Web Audio WebM Opus: https://bugs.webkit.org/show_bug.cgi?id=226922
- WebKit bug 238546, WebM Opus inconsistent in Safari 15.4+: https://bugs.webkit.org/show_bug.cgi?id=238546
- WebKit bug 327697, multichannel Opus refused by decodeAudioData on iOS 18: https://bugs.webkit.org/show_bug.cgi?id=327697
- Tone.js docs (Player, Players, Sampler, Transport, Context lookAhead): https://tonejs.github.io/docs/
- Tone.js wiki, Performance: https://github.com/Tonejs/Tone.js/wiki/Performance
- Audiokinetic, About dynamic music design, design classification: https://blog.audiokinetic.com/about-dynamic-music-design-part-1-design-classification/
- Audiokinetic, Wwise interactive music structures tutorial: https://www.audiokinetic.com/learn/videos/zvnt3tbl3ou/
- FMOD Studio manual (glossary; transition markers/regions, quantization): https://www.fmod.com/docs/2.00/studio/glossary.html
- FMOD transition/quantization walkthrough (community): https://limulo.github.io/game-sound-sae2017/fmod.html
- Apple, Technical Note TN2258 (AAC encoder priming / gapless): https://developer.apple.com/library/archive/technotes/tn2258/_index.html
- LAME, gapless/encoder delay notes: https://lame.sourceforge.io/tech-FAQ.txt

Unverified (rule of thumb, test on device): iOS per-tab memory ceiling, sampler voice counts per device.
