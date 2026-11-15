# Suno test prompts: intensity spectrum

Goal: hear what quality and range Suno gives from low to high intensity (see `vision.md`).
Emotion: **major, glorious, uplifting** (awe at the planet, not threat).
All prompts share **96 BPM, D major, instrumental**, so outputs can be compared or layered.
AI audio must be declared in the submission text and file metadata if used.

## Test A: one track, full arc (quick quality check)

**Style:**
```
cinematic orchestral film score, uplifting epic, glorious, hopeful, awe-inspiring, instrumental, 96 BPM, D major, warm low D pedal drone, soaring string pads, staccato ostinato strings, taiko drums, heroic brass stabs, triumphant french horns, wide stereo, large concert hall reverb, polished modern film-score mix, slow build from serene ambient to glorious climax
```

**Lyrics (structure tags only):**
```
[Intro]
[serene ambient drone, warm low D pedal, airy shimmering textures, no percussion]

[Build]
[warm string pads swell, gentle hopeful pulse]

[Rise]
[bright staccato ostinato strings, low toms, rising anticipation]

[Climax]
[taiko drums, heroic brass, triumphant horns, full orchestra, glorious and uplifting]

[Outro]
[settle back to the warm drone, peaceful]
```

## Test B: four separate levels (does it hold tempo/key across generations?)

Same Style prefix for all four, then add the level line.

**Prefix:**
```
cinematic orchestral film score, uplifting, glorious, hopeful, instrumental, 96 BPM, D major, wide stereo, large concert hall reverb, polished modern film-score mix, seamless loop, steady tempo,
```

| Level | Add to prefix |
|---|---|
| 1 Serene | `meditative ambient soundscape, warm low D pedal drone, sustained cello and bass, shimmering airy pads, no drums, slow evolving texture, peaceful awe` |
| 2 Awakening | `warm low D drone, rising string pads, gentle pulsing low strings, soft heartbeat-like low percussion, hopeful` |
| 3 Soaring | `warm low D drone, bright driving staccato ostinato strings, taiko drums on downbeats, noble french horn melody, building anticipation` |
| 4 Glorious | `warm low D drone, energetic staccato ostinato strings, thunderous taiko ensemble, heroic brass stabs, triumphant horns, soaring choir, epic full orchestra, euphoric` |

Lyrics field for B: `[Instrumental]`

## Test C: simplified harmony over one bass drone (how much intensity from orchestration alone?)

Everything sits on an unbroken low D. Intensity comes only from rhythm, density, register and dynamics, not chord changes.

### C1: single note (no chord changes at all)

**Style:**
```
minimalist cinematic orchestral score, uplifting, glorious, hopeful, instrumental, 96 BPM, D major, one unbroken low D pedal drone throughout, static harmony, single D major chord the entire track, no chord changes, intensity built only by orchestration, rhythm and dynamics, repeated D octaves in staccato strings, taiko drums, heroic brass on D, wide stereo, large concert hall reverb, polished film-score mix
```

**Lyrics:**
```
[Intro]
[solo low D drone, airy shimmer, no percussion]

[Build]
[strings sustain D octaves, slow swell]

[Rise]
[staccato string ostinato repeating D, soft taiko pulse, crescendo]

[Climax]
[thunderous taiko, brass stabs on D, full orchestra on one chord, glorious]

[Outro]
[drop to the bare low D drone]
```

### C2: chords moving over the drone (pedal point)

**Style:**
```
cinematic orchestral film score, uplifting, glorious, hopeful, awe-inspiring, instrumental, 96 BPM, D major, constant low D pedal drone under every chord, slow chord progression over the pedal D, G/D, Bm/D, A/D, long sustained chords, soaring string pads, staccato ostinato strings, taiko drums, heroic brass, triumphant horns, wide stereo, large concert hall reverb, polished film-score mix, slow build from serene to glorious
```

**Lyrics:** same tags as C1.

## Test D: true static drone (after Test C failed: still moved chords)

Findings online (2026-11-14):
- Suno does not reliably hold one bass note. Someone generated 31 V6 takes asking for a drone, and all 31 changed harmony ([arioso#25](https://github.com/thorwhalen/arioso/issues/25)).
- Wording that worked best for someone after a single D chord: `static, drone, one-chord, no fills, no melody, no drums, no build` ([vishsubramanian.me](https://vishsubramanian.me/suno-backing-track/)).
- "Pedal tone" means a held bass with chords changing on top, so don't use it.
- Genre words (`cinematic`, `epic`, `film score`, `trailer`) and arc words (`build`, `climax`) pull Suno into a full song with a chord progression, so leave them out.
- Generate short pieces and extend, rather than whole songs. Mute moving parts using the stems.

So test low and high **as separate generations**, with no genre words and no arc words.

**D-low Style:**
```
drone, static, one-chord, single sustained low D, deep cello and contrabass drone, airy shimmer, instrumental, no melody, no drums, no fills, no build, no chord changes, 96 BPM, D major
```

**D-high Style:**
```
drone, static, one-chord, relentless low D drone, staccato strings repeating one note D, pounding taiko drums, brass stabs on D, loud, huge hall reverb, instrumental, no melody, no chord changes, no progression, no fills, 96 BPM, D major
```

**Lyrics (both):** `[Instrumental]`

Check each take: does the bass stay on D the whole time? Expect to need several takes.

## What to listen for
- Fidelity: do brass, taiko and strings sound real or smeary?
- Tempo/key: do the 4 levels actually share 96 BPM and D major? Load into a DAW and stack them.
- Loopability: clean 8-bar section you can cut?
- Calm end: is level 1 truly percussion-free and still?
- Emotion: glorious and uplifting, not dark trailer menace (taiko + brass pull toward menace; if so, push "triumphant", "hopeful", "major" harder).
