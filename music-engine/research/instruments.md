# Instruments: orchestral sound in the browser, legally

Researched 2026-11-14. Primary sources (repo READMEs, license files, npm registry, live HTTP checks) listed at the bottom.

## TL;DR

1. VST/AU cannot run in a browser. Only source-recompiled WASM plugins (WAM 2.0, Faust) work; no orchestral WAM exists. Skip.
2. Best legal source: **VSCO 2 Community Edition (CC0)**. Has strings (violin/viola/cello sections + solo bass: sus vib, pizz, spic, trem), woodwinds (flute, oboe, clarinet, bassoon), timpani + rolls, orchestral perc. Self-host a trimmed subset (every 3rd note, 1 velocity, mp3/ogg) in `public/samples/`, play with **Tone.Sampler**. Target 5 to 10 MB total.
3. Fastest zero-prep path for the first demo: **`smplr`** (MIT). `Soundfont(ctx, { instrument, kit: "FluidR3_GM" })` for flute/strings/oboe (FluidR3 = MIT), `Versilian` / `Mallet` for CC0 VCSL percussion + timpani. Force `kit: "FluidR3_GM"`: the default MusyngKite has a disputed license.
4. Avoid: Philharmonia samples (terms forbid making them available "as a sampler instrument"), MusyngKite and FatBoy (license unclear or non-commercial), WebAudioFont (GPL-3.0 code). SSO is CC Sampling Plus 1.0 with self-admitted uncertain provenance: usable, but second choice.
5. Fallback / pads / pollution detune: pure synthesis in Tone.js (FMSynth/AMSynth pads, MembraneSynth/MetalSynth/NoiseSynth for lightning percussion, PluckSynth). Faust `physmodels.lib` (violin, flute, clarinet) via `@grame/faustwasm` if time allows; generated code is free to license.

## 1. Native plugins in the browser

| Option | Real? | Notes |
|---|---|---|
| Load a .vst3/.component/.dll in browser | No | Browsers cannot load native binaries. Period. |
| WAM 2.0 (Web Audio Modules) | Yes | "VSTs for the Web" standard (2021). Plugins written in JS/TS, or C/C++ / Faust compiled to WASM. Community registry: 58 plugins, almost all effects; only sampler is a "Soundfont Player" (Sequencer Party). No orchestral library. |
| Recompile open-source plugin to WASM | Partly | iPlug2 has a web target; sfizz has `sfizz-webaudio` (SFZ prototyping demo, Chrome only, not a WAM). Too much risk for a 1-day build. |
| Faust to WASM | Yes | `@grame/faustwasm` 0.20.2. Compiles Faust DSP (incl. physical models) to AudioWorklet in browser or at build time. |

Verdict: not worth it for the hackathon. Use Web Audio samplers + synthesis.

## 2. Sample libraries

| Library | License (exact) | Redistribute in public web app? | Woodwinds | Strings | Perc / timpani | Pads | Size | Articulations / vel layers | Hosted CDN |
|---|---|---|---|---|---|---|---|---|---|
| **VSCO 2 CE** | CC0 1.0 Universal | **Yes**, no attribution needed (credit anyway) | Flute (sus NV, sus vib, exp vib, stac), Oboe, Clarinet (sus, stac), Bassoon (sus, vib, stac) | Violin/Viola/Cello sections (sus vib, pizz, spic, trem), solo violin, solo contrabass, harp | Timpani (hits + rolls), snare, bass drum, sus cymbal, gong, triangle, glock, marimba, xylo, tamb, many hand perc | No (organ only) | ~2.3 GB repo (WAV); per instrument tens of MB raw | 1 to 7 vel layers, some round robins (`_v1.._v7`, `_rr1/rr2`) | None official. Self-host. |
| **VCSL** (Versilian Community Sample Library) | CC0 1.0 ("do whatever you want... no credit, no special terms") | **Yes** | Recorders, sax, ocarina, harmonica. No orchestral flute/oboe/clarinet | Harp, psaltery (bowed), pianos, harpsichords. No orchestral strings | Timpani 1/2 (hit, roll), bass drums, snares, toms, cymbals, gongs, tubular bells, glock, marimba, vibes (incl. bowed), xylo, triangles, wine glasses, ocean drum | Pipe organ, bowed vibes, wine glasses work as pads | ~4 GB repo raw; hosted m4a set 4231 files | Mostly 2 to 3 vel layers, 1 RR; perc more | **Yes**: `smpldsnds.github.io/sgossner-vcsl/` (m4a + SFZ), used by `smplr` |
| Sonatina Symphonic Orchestra (SSO 4.0) | Creative Commons Sampling Plus 1.0 | Yes for non-commercial sharing; but author states some old sources have unknown licensing | Full: flutes, oboes, clarinets, bassoons, piccolo, cor anglais, bass clarinet, contrabassoon | Full sections + solos: sus, marcato, stac, legato, pizz, col legno, trem, harmonics | Timpani (hits, rolls, cresc), full orchestral perc | No | SFZ release, several hundred MB (not verified) | Many articulations, looped sustains | None. Self-host |
| Philharmonia Orchestra samples | Custom terms: free use, "must not be sold or made available 'as is' (i.e. as samples or as a sampler instrument)" | **No** for a web sampler (shipping the files to the browser = making them available as samples) | All | All | Yes | No | Large | Many | No |
| Univ. of Iowa MIS | No formal license: "may be downloaded and used for any projects, without restrictions" | Yes (informal), credit Iowa EMS | All orchestral woodwinds | Violin, viola, cello, bass (arco, pizz) | Some perc | No | Large, mono anechoic (pre-2011) | pp / mf / ff per note | No. Raw chromatic scales, need cutting |
| FluidR3_GM (General MIDI SF2) | MIT (Frank Wen, per Debian copyright). gleitz repo labels it CC BY 3.0 | **Yes** | All GM: flute, oboe, clarinet, bassoon, piccolo, etc. | Violin, viola, cello, contrabass, tremolo/pizz strings, string ensembles 1/2, synth strings | GM drum kit, timpani (GM 48), orchestra hit | GM pads 89 to 96, choir | SF2 148 MB; per instrument ~2.9 MB (mp3-in-js, all 88 notes) | 1 layer in rendered set | **Yes**: `gleitz.github.io/midi-js-soundfonts/FluidR3_GM/`, CORS `*` |
| MusyngKite (GM) | Disputed: gleitz says CC BY-SA 3.0; Polyphone lists "personal use"; Gentoo tags `free-noncomm` | **Avoid** (unclear) | All GM | All GM | Yes | Yes | 1.75 GB SF2; ~2.8 MB/instrument hosted | Better quality | Yes (gleitz), but legal risk |
| FatBoy (GM) | gleitz says CC BY-SA 3.0; author page says "free, non commercial", no license file found | **Avoid** | All GM | All GM | Yes | Yes | 320 MB SF2 | | Yes (gleitz) |
| tonejs-instruments (nbrosowsky) | Code MIT, samples "CC-by 3.0" (sources mostly VSCO2 CE, plus Freesound cello, Karoryfer, Iowa) | Yes with attribution | Flute, clarinet, bassoon, sax | Violin, cello, contrabass, harp | Xylophone only | Organ, harmonium | ~340 KB per mp3 note; `minify` option | 1 layer | **Yes**: `nbrosowsky.github.io/tonejs-instruments/samples/`, CORS `*` |

## 3. JS players

| Player | License | Status | What it plays | Effort for woodwinds + strings + perc |
|---|---|---|---|---|
| **Tone.js `Sampler`** | MIT (tone 15.1.22) | Active | Any URL map `{ "C4": "C4.mp3", ... }`, pitch-shifts to fill gaps, attack/release, plugs into Tone Transport + effects (Reverb, Chorus, detune) | Low once samples are prepped. Best fit since the app already uses Tone.js (Transport, effects, `detune` for pollution). |
| **`smplr`** | MIT (1.2.0) | Active, replaces soundfont-player | `Soundfont` (gleitz GM, kits `MusyngKite` default or `FluidR3_GM`), `SplendidGrandPiano`, `ElectricPiano`, `DrumMachine`, `DrumAbuse`, `Mallet` (VCSL), `Mellotron`, `Smolken` double bass (CC0), `Versilian` (VCSL, "partial support"), `Soundfont2` (.sf2 direct), generic `Sampler` with SFZ-like presets. Samples streamed from `smpldsnds.github.io`. Has own `Sequencer`, `CacheStorage`, reverb. | **Lowest today**: 3 lines per instrument, no asset prep. Uses its own AudioContext graph; route into Tone via `Tone.getContext().rawContext` (pass same context). |
| soundfont-player | MIT (0.12.0) | **Archived**; README points to smplr | gleitz GM soundfonts | Do not use. |
| WebAudioFont | **GPL-3.0-or-later** (code); instruments from FluidR3, GeneralUser GS, others | Active | Huge GM catalog incl. many string/pad variants | GPL obligation on our code; skip unless repo is GPL anyway. |

Easiest path today: `smplr` with `kit: "FluidR3_GM"` for flute/clarinet/oboe/strings/pads + `Versilian`/`Mallet` for timpani and percussion. Best sound / cleanest license: VSCO 2 CE subset in Tone.Sampler.

## 4. Pure synthesis

| Technique | Tool | Good for | Notes |
|---|---|---|---|
| FM / AM | Tone `FMSynth`, `AMSynth`, `PolySynth` | Pads, brass-ish, bells | Pads with slow attack + `Chorus` + `Reverb` sound "orchestral-ish". Zero download. |
| Membrane / metal / noise | Tone `MembraneSynth`, `MetalSynth`, `NoiseSynth` | Lightning percussion: timpani-like booms, cymbal crashes, thunder rumble | Fully synthesizable, no samples needed. |
| Karplus-Strong | Tone `PluckSynth` | Pizzicato, harp | Cheap, convincing. |
| Waveguide physical models | Faust `physmodels.lib`: `violin_ui_MIDI`, `flute_ui`, `clarinet_ui_MIDI`, `brass_ui_MIDI`, guitar, marimba | Bowed strings, flute, clarinet | Compile with `@grame/faustwasm` (LGPL-2.1 compiler; GRAME LGPL exception lets generated code be any license). CPU heavier, more setup, sounds synthetic. Only if time remains. |
| Wavetable / additive | `OscillatorNode.setPeriodicWave` | Organ, soft pads | Trivial. |

Fallback strategy: load samples lazily; until loaded (or on low bandwidth) play Tone synth equivalents.

## References block (paste into app)

- VSCO 2 Community Edition, Versilian Studios (Sam Gossner, Simon Dalzell, Elan Hickler), CC0 1.0. https://github.com/sgossner/VSCO-2-CE
- Versilian Community Sample Library (VCSL), Versilian Studios, CC0 1.0. https://github.com/sgossner/VCSL
- FluidR3_GM SoundFont, Frank Wen, MIT License (rendered by B. Gleitzman, midi-js-soundfonts). https://github.com/gleitz/midi-js-soundfonts
- smplr, danigb, MIT. https://github.com/danigb/smplr
- Tone.js, MIT. https://github.com/Tonejs/Tone.js

## Sources

- smplr README: https://github.com/danigb/smplr (npm: https://www.npmjs.com/package/smplr)
- smpldsnds hosted samples org: https://github.com/smpldsnds , VCSL index https://smpldsnds.github.io/sgossner-vcsl/
- VSCO 2 CE README + LICENSE (CC0): https://github.com/sgossner/VSCO-2-CE , https://github.com/sgossner/VSCO-2-CE/blob/master/LICENSE
- VCSL README: https://github.com/sgossner/VCSL
- SSO README / license section: https://github.com/peastman/sso
- CC Sampling Plus 1.0: https://creativecommons.org/licenses/sampling+/1.0/
- Philharmonia sound samples terms: https://philharmonia.co.uk/resources/sound-samples/
- Iowa MIS: https://theremin.music.uiowa.edu/MIS.html
- midi-js-soundfonts (FluidR3, MusyngKite, FatBoy): https://github.com/gleitz/midi-js-soundfonts
- FluidR3 MIT license (Debian): https://metadata.ftp-master.debian.org/changelogs/main/f/fluid-soundfont/unstable_copyright
- MusyngKite license conflict: https://www.polyphone.io/en/soundfonts/instrument-sets/258-musyng-kite , https://www.kvraudio.com/forum/viewtopic.php?p=5285099
- tonejs-instruments README + sample sources: https://github.com/nbrosowsky/tonejs-instruments , https://github.com/nbrosowsky/tonejs-instruments/blob/master/sample-source-info.txt
- soundfont-player (archived): https://github.com/danigb/soundfont-player
- WebAudioFont (GPL-3.0): https://github.com/surikov/webaudiofont/blob/master/LICENSE.md
- Tone.js Sampler: https://tonejs.github.io/docs/15.1.22/classes/Sampler.html
- WAM 2.0: https://www.webaudiomodules.com/docs/intro , registry https://www.webaudiomodules.com/community/plugins.json
- sfizz-webaudio: https://github.com/sfztools/sfizz-webaudio
- Faust physmodels.lib: https://github.com/grame-cncm/faustlibraries/blob/master/physmodels.lib , faustwasm https://github.com/grame-cncm/faustwasm
