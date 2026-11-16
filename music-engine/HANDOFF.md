# Music engine: handoff notes (2026-11-14)

Context for a new agent. Read `README.md`, `plan.md`, `narrative ideas.md` first.

## Work split
- Jose: data side (dataset catalog, real feeds).
- Us: music engine. Build it now against **mocked signals**, swap in real feeds later.

## Signal contract
Every signal sample: `{ id, unit, raw, norm (0..1), region, t }`.
Engine reads only `norm` (+ discrete events). Data source agnostic.

## Mock signals (realistic, likely to arrive)

| # | Signal | Unit / range | How it moves | Real source | Musical role (first guess) |
|---|---|---|---|---|---|
| 1 | Wind speed | 0-25 m/s, mean ~6 | Slow random drift + gusts (+30-80%, 2-10 s); stronger afternoons | MERRA-2, GEOS | Woodwinds: breath, volume, vibrato |
| 2 | Wind direction | 0-360 deg | Slow drift, occasional 90 deg swing (front); wraps | MERRA-2 | Stereo pan |
| 3 | Air temperature | -10-40 C | Daily sine (+-6) on yearly sine (+-12) + noise | MERRA-2 | Key/mode (warm major/lydian, cold minor), filter brightness |
| 4 | PM2.5 | 0-300 ug/m3, usually 5-35 | Calm; 2 rush-hour bumps/day; rare episodes (fire/dust) to 150+ over hours, decay over days | GEOS-CF (SVS 5533) | Detune, dissonance, grit |
| 5 | NO2 | 0-80 ppb | Two daily traffic peaks, lower at weekends | GEOS-CF | Second dissonance layer, beating |
| 6 | Aerosol optical depth | 0-3, usually 0.1-0.4 | Smooth, multi-day dust/smoke plumes | GEOS (SVS 5669) | Haze: reverb wet, low-pass |
| 7 | CO2 | 410-425 ppm | Steady trend (+2.5/yr), yearly cycle (+-3), tiny noise | DYAMOND (SVS 5196), OCO-2 | Drone pitch, slow rising tension |
| 8 | Lightning flash rate | 0-50 flashes/min | Events: long zeros, storm cells (~20 min rise, peak, decay); afternoons, summer | ISS LIS (SVS 5011) | Percussion: flash = hit, intensity = velocity |
| 9 | Sea surface temp | 0-30 C | Very slow: yearly sine (+-3) + months-long anomalies (El Nino-like) | ECCO2 (3912), Perpetual Ocean | Strings register, pad warmth |
| 10 | Ocean current speed | 0-2 m/s | Slow eddy swirls (days-weeks period), occasional quick pulses | Perpetual Ocean (5425) | String bow speed, arpeggio rate |

Optional: humidity / precipitable water (atmospheric river swells -> texture density); night lights (yearly steps -> harmonic density).

### Movement primitives (every signal = mix of these)
1. `trend`: linear rise (CO2)
2. `cycle`: sine, daily/yearly period (temp, NO2, SST)
3. `drift`: mean-reverting random walk (wind, AOD)
4. `gust`: short random spikes (wind)
5. `episode`: rare slow rise + slow decay (PM2.5 smoke, storm cells)
6. `events`: discrete hits, rate driven by another signal (lightning)

### Regions (for "zoom in shrinks the orchestra")
Po Valley (high PM2.5/NO2), Sahara (AOD dust), Congo (lightning), Open Pacific (clean, steady wind).

## Timing: approaches considered

| # | Approach | Pros | Cons |
|---|---|---|---|
| A | Fixed tempo + quantize (Myky's original idea): one BPM, events snap to grid | Always musical, layers in sync, scrub speed doesn't touch tempo | Timing slightly off; events pile up at fast playback; data's own rhythm lost |
| B | Data time locked to bars (e.g. 1 day = 16 bars) at fixed BPM | Cycles become form (dawn = phrase start, peak = chorus); learnable | Playback speed tied to tempo; awkward for irregular steps (10-day, yearly) |
| C | Tempo driven by data (wind or scrub speed -> BPM) | Dramatic, legible | Drift, lurching, loops break, tiring |
| D | Free time, no grid | Most faithful, good for ambient/science | Not song-like; dense data = noise |
| E | Event-driven form: data events trigger sections, snapped to 8-bar phrases | Strong narrative arc, great for 30 s demo | Needs detection (thresholds, hysteresis); dead stretches |
| F | Hybrid, three update rates on one fixed tempo | Musical yet responsive; nothing jumps mid-bar; scales to 10+ signals | 3 schedulers; smoothing lag on continuous controls |

Clarification given: the proposal was never tempo-changing (C); it was B (fixed tempo, data day mapped to N bars).

## Recommendation (not yet confirmed by user)
**F (= A refined) + E for demo moments.**
- Fixed BPM (~96) on a Tone.js Transport.
- Three rates:
  - events (lightning) -> quantized to 1/16
  - continuous (wind, PM2.5) -> smoothed free-flowing control (filter, detune, volume)
  - harmony/structure (temp -> mode, CO2 -> drone) -> change only on bar/phrase lines
- Default speed ~1 data day = 16 bars (borrowed from B); user scrub changes data density per bar, never tempo.
- Pile-up: cap hits per step, overflow becomes velocity/roll density.
- Pitch always snaps to current scale; scale/key changes wait for bar line.
- E (section changes) only for headline moments (storm build -> drop).

## Proposed next step
1. `music-engine/signals.ts`: the 6 primitives + 10 signal definitions, region baselines, `speed` param.
2. Engine skeleton on F: one Transport, three schedulers.
3. Tiny Tone.js page: lightning -> percussion, wind -> woodwind pad, temperature -> mode. Listen early.

Open question to the user: confirm approach F before building.
