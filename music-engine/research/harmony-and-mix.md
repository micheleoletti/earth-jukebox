# Harmony and mix for Earth Information Jukebox

Research date: 2026-11-14. Primary sources linked at bottom; claims marked (inferred) are design judgment, not sourced.

## TL;DR

1. Pleasant sonifications quantize to a fixed key/scale (TwoTone, Handbook pentatonic example, Highcharts scale presets) and split data into **drones for continuous fields + discrete notes for point events** (Chandra Galactic Center). Copy that: wind/temp/CO2/sea temp/currents = beds, lightning/PM2.5 spikes = notes.
2. Harmony: **pedal-tone modal base (one tonic, never moves) + slow brightness axis** (Lydian/Ionian -> Dorian/Aeolian -> Phrygian) driven by ONE global "planet stress" index. Reserve **one chromatic-mediant shift** for threshold events (record heat, extreme AQI). Chord progressions per signal = mud and illegible.
3. Legibility ceiling is low: Highcharts says >3 changing params gets messy, people track ~2; McGookin & Brewster: earcon ID drops 70% -> 30% from 1 to 4 concurrent; Murch "Law of Two-and-a-half". So zoomed out = **3 audible groups max**, not 10 instruments.
4. Mix: fixed register lane + fixed timbre family per signal, loudness-based priority/culling (DICE HDR audio), sidechain ducking under the "conductor" signal, staggered onsets. Zoom out = summarize to 3 stems (Air / Heat / Water); zoom in = unfold stems into individual instruments.
5. Accessibility: positive polarity by default (more = higher/louder) but avoid pitch-up for "worse" where it reads as "better"; redundant coding (pitch+volume+timbre), stereo never sole cue, G4-F6 most accurate pitch band, acoustic instruments preferred by BLV and sighted listeners (Arcand 2024, n=3,184), explain mappings in words, offer solo/isolate per signal.

## 1. Prior art: what made it pleasant vs noisy

| Project | Mapping | Why it works / fails |
|---|---|---|
| NASA SVS 13786, Caldwell 73 (Hubble globular cluster) | Radar-sweep scan; distance from center -> pitch; whole image = choir; red/orange stars = marimba, blue = glockenspiel | Choir = harmonic bed that never clashes; 2 tuned-percussion families for discrete points. Timbre = category, pitch = one continuous dim. |
| Chandra Galactic Center (Russo/Santaguida/Arcand) | Left->right scan; vertical position -> pitch; brightness -> volume; **stars = individual notes, gas/dust = evolving drone**; each telescope = own instrument, solo or ensemble | Points vs fields split is the key pattern. "Solo or ensemble" = exactly our zoom-in/zoom-out. |
| Chandra sonify releases (2023, 2024) | Brightness -> volume (sometimes also pitch); color -> pitch band (red low, blue high) | Brightness on volume is the most consistent convention. |
| Kepler (Georgia Tech Sonification Lab + Echo Movement, 2012) | Binary-star light curves played as waveforms/tremolo inside a reggae track; MATLAB curve fitting to remove noise | Data as texture inside a human-written song. Smoothing raw data before mapping was needed to avoid artifacts. |
| Listen to Wikipedia (Hatnote) | Bells = additions, string plucks = subtractions; larger edit = deeper note; new user = string swell | Category -> timbre, magnitude -> pitch (bigger = lower), rare event -> distinctive gesture. Pentatonic-feeling bells never clash, so dense random events stay pleasant. |
| TwoTone (Datavized/Sonify, GNI) | Column -> track; row -> note; values quantized to chosen tonic+mode; octave span per track; tracks can occupy different octave zones "like left and right hands" | Scale lock + register zoning per track = layered tracks stay consonant. |
| A Song of Our Warming Planet (Crawford, 2013) | 1 note/year 1880-2012 NASA GISS; temp anomaly -> pitch, ~0.03 C per semitone, 3 octaves, coldest year = open C on cello | One signal, one instrument, one dimension: maximally legible, emotionally strong. Follow-up "Planetary Bands" = one string instrument per latitude band (string quartet = register separation for free). |
| Loud Numbers (Geere & Quick) | Time series only; music/story/imagery first, data second; louder/rougher = hotter; insect count -> number of buzzing sources, fades to silence | Cited failure: mapping ice-breakup timing to tempo "too complicated to follow". Test mappings at the extremes. Genre/harmonic tricks set mood. Earlier they called most sonification "plinky-plonky". |
| Brian Foo, Two Trains | Route split into 48 segments; median income -> number and dynamics of instruments (3 to 30 playing) | **Density itself as the data variable**: orchestration grows/thins rather than pitch. Composed, sample-based, synced to animation. |
| Eno Bloom / generative.fm / Music for Airports | Fixed palette per "mood", delay/echo, loops of unequal length phasing (Discreet Music 63 s vs 68 s loops) | Never repeats, never resolves, no chord changes needed: pleasantness from fixed scale + slow evolution + space. Good model for the zoomed-out idle state. |
| NASA Earthdata warming stripes sonification | Blue/red stripes -> sound, rise audible over recent years | Earth-science precedent from NASA itself. |

Patterns (inferred from above):
- Every pleasant one locks pitch to a scale or uses non-clashing timbres (bells, choir, glockenspiel).
- Category -> timbre, magnitude -> pitch or volume or density. Never more than 1-2 data dims per voice.
- Noisy ones: raw continuous frequency mapping, synthetic sine tones, many dims per voice, tempo mappings.

## 2. Harmony approaches compared

| Approach | Pleasantness | Legibility (can you hear which signal changed?) | Fit |
|---|---|---|---|
| A. Static drone / modal (one key, pentatonic or Lydian, no chord changes) | High; nothing can clash; Eno/generative.fm proven | High per-voice: any change is a change in that voice's pitch/volume/density, not masked by harmonic motion | Base layer. Risk: monotony over minutes. |
| B. Slow cinematic progression over pedal (Interstellar: organ, ostinato, few chords, unexpected changes) | High, emotional | Medium: harmonic motion is itself a change, so listener can't tell if data or score moved | Only if chords are **driven by data**, not by clock. |
| C. Threshold-triggered shifts (chromatic mediants, Williams-style "wonder" moves; e.g. I -> bIII or I -> III) | Dramatic | High for the event that triggers it (rare + salient), zero for small changes | Use sparingly: 1 trigger class (e.g. global stress crosses threshold). Lehman ties chromatic/pantriadic moves to wonder in film. |
| D. Data -> mode brightness (Lydian -> Ionian -> Mixolydian -> Dorian -> Aeolian -> Phrygian -> Locrian) | Good if slow; Locrian unstable (avoid as resting state) | Medium: conveys "mood" of the planet, not which signal. Temperley & Tan: happiness falls as scale degrees are lowered; caveat Lydian rated slightly less happy than Ionian, and effect depends on Western familiarity | Map one aggregate index, not individual signals. Change one scale degree at a time (adjacent modes differ by one note) so transitions are smooth. |

Recommendation (inferred):
- Fixed tonic pedal (e.g. D) for whole app. Never modulate the tonic except event C.
- Mode = f(aggregate anomaly index): calm/clean -> Lydian/Ionian; stressed -> Dorian/Aeolian; extreme -> Phrygian. Step through adjacent modes only, with ~5-10 s crossfade.
- Every voice quantizes to current mode. Pentatonic subset for dense event voices (lightning) so random note pile-ups stay consonant.
- Individual signals carry pitch/volume/density/brightness changes within the mode, never their own chords.
- Chromatic mediant reserved for "headline" moments (record value, zoom into hotspot).

## 3. Mix density with 10 signals

Evidence on limits:
- Highcharts: >3 simultaneously changing params gets messy; most people reliably track 2.
- McGookin & Brewster (2004): concurrent earcon identification 70% (1) -> 30% (4). Improved by differing timbre and staggered onsets (onset stagger examined; exact ms value not confirmed).
- Murch: clarity/density balance at "not quite three" layers of a kind of sound.
- Bregman: no hard stream limit; attention is top-down; synchronous onsets fuse streams (bad for separation).

Techniques:
- **Summarize when zoomed out**: 10 signals -> 3 stems (inferred grouping):
  - Air: wind, PM2.5, NO2, aerosol depth, CO2
  - Heat/Energy: temperature, lightning
  - Water: sea temp, ocean currents
  - Each stem = one instrument family; zoom in "unfolds" a stem into its member instruments (Chandra solo/ensemble model).
- **Register lanes**: each signal owns an octave band (TwoTone "left/right hand" zoning; Crawford string quartet by latitude). Bass = slow global (CO2, sea temp), mid = temp/wind pads, high = events (lightning bells).
- **Timbre families**: one family per stem (strings, winds/choir, mallets). Same family inside stem = fusion; across stems = segregation.
- **Rhythmic separation**: drones (fields) vs plucked/struck (events) vs pulses. Stagger onsets; never quantize all events to the same beat.
- **Loudness priority / culling**: DICE HDR audio: priority by loudness, quiet sounds culled when loud ones play, restored when alone; DICE later deliberately played fewer simultaneous sounds for clarity. Port: rank signals by anomaly (|z-score|), top 2-3 audible in front, rest attenuated/culled.
- **Conductor**: the highest-anomaly signal gets the "melody" role + sidechain ducking of others by 3-6 dB (inferred numbers); others become pad/texture.
- **Density as data** (Foo, Loud Numbers insects): number of active voices, not pitch, can represent magnitude. Good for aerosols/PM2.5.
- **Voice cap**: hard limit on simultaneous note events (e.g. 16-24 voices, inferred) with oldest/quietest stolen.
- Master bus limiter + reverb send shared across stems to glue.

## 4. Accessibility guidelines

- **Polarity**: Walker & Kramer (magnitude estimation): preferred polarity and scaling depend on the data concept; frequency suits temperature. Walker & Mauney (2010, 45 BLV): polarity choices mostly agree with sighted, but early-onset blind participants preferred negative polarity for money. Highcharts supports inverted polarity (`pitch: '-y'`) and notes lower pitch often read as "bigger". Rule (inferred): temperature up = pitch up; pollution/severity up = louder + rougher/denser (not higher), to avoid "higher = brighter = better".
- **Pitch range**: G4-F6 most accurate for most humans (Highcharts). Use for the signal being inspected when zoomed in.
- **Dual/redundant coding**: map one variable to pitch + volume + duration to emphasize change (Highcharts).
- **Volume**: small differences hard to hear, device-dependent; not sole cue. **Pan**: needs stereo; never sole cue. **Tempo/tremolo**: small changes easily detected, good for intensity.
- **Time-series framing**: listeners follow change over time best (Loud Numbers; Apple Audio Graphs: time on x, value on pitch).
- **Interactive inspection**: Apple Audio Graphs lets VoiceOver users scrub to the highest pitch then hear the exact value. Port: keyboard-scrub a region, speak values via ARIA live region on demand.
- **Instrument choice**: Arcand et al. 2024 (n=3,184): BLV and sighted enjoyed equally; BLV reported more learning; **participants preferred instrumental over synthetic sounds**; many misunderstood how data maps to sound; asked for clearer, standardized mappings. Words: calm, curious, wonder.
- **Explain mappings**: Loud Numbers podcast format = story, method explanation, then piece. Provide spoken legend + per-signal solo button.
- Zanella et al. 2022: ~100 astronomy sonification projects reviewed; field lacks evidence-based design and evaluation; push for standardization.

## Sources

- NASA SVS 13786, Data Sonification: Caldwell 73: https://svs.gsfc.nasa.gov/13786
- Chandra Galactic Center sonification: https://chandra.si.edu/sound/gcenter.html
- Chandra sonification release 2023: https://chandra.harvard.edu/photo/2023/sonify7/
- Chandra sonification release 2024: https://chandra.si.edu/photo/2024/sonify8/animations.html
- Kepler star data melody (Georgia Tech): https://phys.org/news/2012-06-kepler-telescope-star-musical-melody.pdf ; https://repository.gatech.edu/entities/publication/4da8be66-3d9e-4965-a7b3-13c324e56227
- Listen to Wikipedia: http://listen.hatnote.com/ ; https://github.com/hatnote/listen-to-wikipedia
- TwoTone README: https://raw.githubusercontent.com/sonifydata/twotone/master/README.md
- A Song of Our Warming Planet: https://ensia.com/videos/a-song-of-our-warming-planet/ ; https://agu.confex.com/agu/fm14/preliminaryview.cgi/Paper8221.html ; https://hyperallergic.com/climate-change-data-set-to-music-to-serenade-a-warming-planet
- Loud Numbers / Ableton "Sound the Alarm": https://www.ableton.com/zh-cn/blog/sound-the-alarm-data-sonification-as-a-tool-for-climate-action/ ; https://datajournalism.com/read/newsletters/exploring-the-sound-of-data ; https://buttondown.com/loudnumbers/archive/devlog-6/
- Brian Foo, Two Trains: https://www.untappedcities.com/fun-maps-in-data-driven-city-a-soundtrack-of-income-inequality-on-nyc-subways ; https://viewing.nyc/meet-brian-foo-the-data-driven-dj-using-city-data-and-statistics-to-create-music
- generative.fm: https://generative.fm/
- Bloom (Eno/Chilvers): https://apps.apple.com/us/app/-/id292792586
- Eno loop phasing (Discreet Music, Music for Airports): https://reverbmachine.com/blog/deconstructing-brian-enos-discreet-music ; https://reverbmachine.com/blog/deconstructing-brian-eno-music-for-airports/
- NASA Earthdata sonification blog: https://www.earthdata.nasa.gov/learn/blog/data-sonification-open-science
- Interstellar score: https://www.slate.com/articles/arts/culturebox/2014/11/interstellar_score_hans_zimmer_composes_music_for_the_universe_brilliantly.2.html ; https://grantland.com/hollywood-prospectus/brothers-in-brong-how-hans-zimmer-and-christopher-nolan-make-the-boldest-scores-in-hollywood/
- Lehman, Hollywood Harmony (OUP 2018), "Pantriadic Wonder": https://www.sciencegate.app/document/10.1093/oso/9780190606398.003.0006 ; https://now.tufts.edu/2018/01/12/professor-turns-dark-side
- Mode happiness (Temperley & Tan, cited): https://arxiv.org/pdf/1306.6458 ; https://durham-repository.worktribe.com/OutputFile/3948119
- Highcharts sonification mapping: https://www.highcharts.com/docs/sonification/mapping ; https://www.highcharts.com/docs/sonification/advanced-mapping ; https://www.highcharts.com/samples/highcharts/sonification/polarity-invert
- Grond & Berger, Parameter Mapping Sonification (Sonification Handbook ch. 15): https://sonification.de/handbook/chapters/chapter15
- Walker & Kramer 2003 (polarity/scaling): https://pubmed.ncbi.nlm.nih.gov/12570096/
- Walker & Mauney 2010 (BLV mappings): https://wirelessrerc.gatech.edu/sites/default/files/publications/walker_et_al_-_a_comparison_of_sonification_mappings.pdf
- McGookin & Brewster, concurrent earcons: https://www.dcs.gla.ac.uk/~stephen/papers/ICAD2003_david.pdf ; https://theses.gla.ac.uk/14/
- Bregman on concurrent streams (AUDITORY list): https://auditory.org/postings/2004/492.html
- Murch, Law of Two-and-a-half: https://wrightonfilm.com/2010/10/28/rules-and-anarchy/
- DICE HDR audio / Frostbite: https://www.slideshare.net/slideshow/adaptive-mixing-in-frostbite/3128152 ; https://designingsound.org/2013/06/finding-your-way-with-high-dynamic-range-audio-in-wwise/
- Arcand et al. 2024, A Universe of Sound (Frontiers in Communication): https://www.frontiersin.org/articles/10.3389/fcomm.2024.1288896
- Apple Audio Graphs: https://developer.apple.com/documentation/accessibility/audio-graphs.md ; https://developer.apple.com/wwdc21/10122
- Zanella et al. 2022, Nature Astronomy: https://arxiv.org/pdf/2206.13542
