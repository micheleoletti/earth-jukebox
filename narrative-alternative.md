**slogan**
"Hear how the planet is connected."


**narrative**
beauty through connection

jose research highlighted a different approach: if we search for beauty, there is beauty in data correlation

if two data signals are correlated, the planet is not a pile of separate datasets but one system: ocean, air, fire, life and cities pulling on each other.
music is the oldest way humans have to hear things moving together.
correlated signals play in harmony, unrelated ones drift apart, and a broken link sounds out of tune.
you don't just hear Earth's data, you hear how it's connected.

why this is beauty from first principles (not a metaphor):
- two notes sound consonant when their sound waves line up regularly (a fifth = 3:2, they realign every 3 cycles). consonance IS correlation between waves
- rhythm/groove = events landing together. also correlation
- so: correlated data -> correlated sound waves -> the ear hears one thing -> beauty. the harmony is earned by the data, not decoration

each relationship between two signals is mapped to a musical relationship
- move together (positive correlation) => consonance: unison, octave, fifth
- weak link => softer consonance: third, fourth
- unrelated (no correlation) => voices drift, slow detune, no shared key
- opposite (negative correlation) => counterpoint: one melody rises while the other falls, call and response
- one follows the other later (lag) => canon/echo: second voice repeats the first after a delay, delay length = lag
- link that weakens over the years => slowly goes out of tune (climate change arc, coming from the data itself)

the instruments from the original narrative stay (lightning => percussion, winds => woodwinds, currents => strings...).
the original decides WHO plays, this one decides HOW they are tuned to each other.

dissonance must stay tasteful (gentle detune, clusters that resolve), never harsh. polish over mapping fidelity.


**ux: what changes**
original: viewport = which instruments play
alternative: viewport = which relationships are measured. the correlation is recomputed only on what is on screen

- zoom out => the whole planet, global correlations, broad chords
- pan over a region => the harmony changes because the local relationship changes
  - over india / po valley: night lights and pollution sit in the same places => they lock into unison
  - over the amazon or central africa: few lights but heavy smoke (fires) => the two voices pull apart, a "story" moment
  - over the gulf stream / kuroshio: warm currents and lightning line up => strings and drums lock in
- connection lines on screen: thin glowing threads between layer labels in the legend, thickness = how strong the link is, pulse in time with the music
- "lock-in" moment: when a link crosses a threshold, the chord resolves + the thread glows. this is the 30s demo shot
- untuned / tuned toggle: play two layers ignoring correlation, then flip to tuned. the A/B makes the idea obvious in 5 seconds
- pair mode: pick any two layers and hear just their relationship
- accessibility: screen reader announces links in words ("night lights and air pollution: strongly linked in this view"), so blind users get the same discovery as sighted ones


**temporal window: what data, over what time**
short answer: there is no single time window where all datasets overlap. so correlation works in two ways:

1. across SPACE (main mode, no time window needed)
   same moment, two maps: do they light up in the same places?
   works even with stills, and it is exactly what the viewport UX needs (pan = new region = new correlation)
   - night lights (2023 frame) x GEOS aerosols (still, 2025-08-19)
   - ISS lightning (2017-2023 average) x ocean currents (perpetual ocean 2)
   - GEDI forest height (2019-04 to 2020-04 composite) x lightning or aerosols
   caveat: the maps are from different dates. ok for slow-changing things (cities, forests), say so in the text

2. across TIME (secondary, only one usable window)
   same place, two signals over time: do they rise and fall together?
   needs both datasets to cover the same period. only one real overlap:
   - window A: 2021-01-15 to 2023-07-31 (~2.5 years)
     - ISS lightning: 10-day steps => ~92 points
     - perpetual ocean 2: daily, resample to 10-day => ~92 points
     - night lights: only 3 yearly frames (2021, 2022, 2023) => too few points to correlate, use as background only
   - 2020 jan to mar (CO2 + lightning): ~9 lightning steps, too short
   - 2019-04 to 2020-04 (GEDI + lightning): GEDI is a still, so this is really mode 1

   playback: window A played at the shared 10-day step. correlation computed on a sliding window (e.g. last 12 steps = ~4 months) so the harmony evolves while it plays.
   caveat: almost everything moves with the seasons, so remove the yearly cycle first or every pair will look "linked". with only 2.5 years this is weak, which is why space is the main mode.

open questions
- which 2-3 pairs are physically real (check literature) and look/sound good. candidates above, to verify with jose
- perpetual ocean 2: which variable do the frames encode (speed? temperature?), and frame index != time (camera zooms)
- do we need extra NASA data outside the EIC frames (e.g. MODIS fire, OCO-2 CO2) to get a second long time series?
