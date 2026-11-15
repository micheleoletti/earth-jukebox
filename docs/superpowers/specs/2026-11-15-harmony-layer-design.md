# Harmony layer: "Harmony expresses balance. Dissonance reveals change."

## Why
The pitch line promises that harmony expresses balance and dissonance reveals change, but today's Nature mode (drone + real recordings) has no tuned material, so nothing is consonant or dissonant. The challenge also asks for sonification generated from NASA EIC visual frames. A quiet chord on top of the nature sounds can make the pitch line literally true, tied to what is on screen.

## Goals
- A: the interval between two voices says whether the story's two linked signals move together right now (same rolling link the chart thread shows).
- B: a tension note says how far the main signal is from normal (the grey normal-years band).
- Pleasant: slow, soft, low; nature sounds stay the main bed.
- EIC: in the monsoon, B is read from the NASA EIC anomaly image under the centre of the screen.

## Non-goals / anti-goals
- No melodies, no percussion, no high voices.
- No direction in the tension (wetter and drier are the same tension).
- Never invent a "normal": stories without a normal band get no tension.
- Must not sound like a clash or alarm; dissonance is a gentle rub or slight detune.

## Approaches (picked: A)
- **A. Live Web Audio pads (picked):** smooth pitch slides, exact data following, tiny, about 1 to 1.5 h.
- B. Pre-recorded pad samples crossfaded: warmer but no smooth detune, 2 to 3 h.
- C. Reuse D-major pad loops with pitch shift: clashes with per-story scales, artificial.

## Design
- Lives in Nature mode, on top of recordings and the space drone; rooted on D in each story's scale (STORY_MODE).
- Four soft pad voices (filtered detuned saws/triangles through the existing reverb), low register (D2 to D4):
  - root D (always),
  - main-signal voice,
  - partner voice,
  - tension voice.
- **A, interval:** rolling link strength s (as for the thread: grey below 0.3, full at 0.7). Partner sits a consonant interval from the main voice (fifth, octave or third of the scale). As s falls, the partner slides over several seconds toward a half-step rub plus a few cents of detune; it slides back as s returns. At the lock-in moment the chord swells slightly.
- **B, tension:** distance of the main signal from its normal band (in sigma, as the music intensity uses). Inside the band: silent. Outside: a soft tension voice (the scale's unstable note, a half-step from a chord tone) fades in, louder further from normal, and fades out when back inside. A faint glow on the normal band shows it.
- Stories without a normal band (Snow, Africa, Breathing, Tides): A only.
- **EIC (monsoon, phase 2):** the monsoon moves to the 2025 season; EIC item 4897 anomaly frames (daily, global flat maps) become the rain layer; B reads the frame's pixel at the listening point, converted with its colour scale into "how far from usual". To verify first: frame projection, burned-in date text, colour scale (one 0.3 MB frame).
- All changes slow (seconds), nothing jumps; layer volume respects the master volume and mute.

## Two versions (owner's request, 2026-11-15)
- **Version 1 (charts only):** everything above except the EIC part: A interval from the live link, B tension from the normal band, tension glow, A only where there is no normal band. Applies to every visible story.
- **Version 2 (charts + EIC):** Version 1 plus a second monsoon story, `c3_monsoon_eic` (2025 season), where NASA EIC item 4897 anomaly frames are shown on the globe and drive the tension at the listening point. The original 2019 monsoon stays, so the two can be compared side by side. The owner finds the EIC mapping possibly forced and wants to judge it by seeing and hearing it.

## Left to the builder
Exact voicings per scale, pad timbre and levels, how the tension glow looks, smoothing constants.
