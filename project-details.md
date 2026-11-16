Our mission
We want anyone, including a child or someone who cannot see, to feel how our planet is connected. Rain feeds forests, forests breathe in CO2, a dry season sets the savanna on fire. These links are in NASA data, but they are hidden in charts and maps that most people cannot read or do not want to. We turn them into something you can hear, see and experience.
This way we can connect people with the planet they live on, and inspire the next generation of scientists, explorers and caretakers of the Earth.

What it does
Earth Breathing is a 3D globe in the browser. You pick a story and the camera flies in, the data plays on the globe and in a chart below, and you hear it. There are five stories:

- The Monsoon, Through NASA Eyes (India, 2025): rain arrives, and two months later the land turns green.
- Hurricane Ian (Florida, 2022): the wind grows and a few hours later the sea climbs onto the coast.
- Hunga Tonga (2022): the eruption's air wave reaches tide gauges around the Pacific, and the sea wobbles after it.
- The Planet Breathing (2021 to 2023): northern forests green up and CO2 in the air drops, every year a bit higher than the last.
- Africa's Fire Belt (2019): when the rain stops, the fires start about a month later.

How it works
1. Data. Each story is built by a small Python script from public NASA and NOAA data: GPM IMERG rain, MODIS greenness, GRACE-FO stored water, MERRA-2 wind, FIRMS fire detections, NOAA tide gauges and Mauna Loa CO2. Nothing is made up. Gaps stay empty and model data is labelled "model".
2. Connections. For each pair of signals we measure how strongly they move together and with what delay (for example rain and greenness, r 0.85, two months apart). Each link is drawn as a thread between the two chart lines. It lights up when the two are moving together right now.
3. Sound. There are two layers:
   - Nature: real recordings of rain, fire, wind, waves, thunder and a volcano. Each one gets louder or softer with the data under the centre of the screen. Point at the fires and you hear them crackle.
   - Harmony: a soft chord. Every connection adds a voice that swells when its two signals move together. When the planet moves away from normal, a tension note creeps in. Harmony means balance, dissonance means change.
4. NASA Earth Information Center images. In the monsoon story we wrap SVS item 4897, "Seasonal Global Precipitation Variation", around the globe. These daily maps show where it rained more or less than usual. We turn each frame's colours back into numbers using its own colour bar (8 colours, from 20 mm/day drier to 20 mm/day wetter than usual). The colour under the centre of the screen drives the tension note. Next to it plays the real GPM IMERG rain measurement, so you can check the picture against the data behind it.

Who it is for
Blind and low-vision people, kids, students, teachers and museums. A Simple mode uses plain words for a five-year-old, and a Science mode shows dataset names, units and correlation values. It works with a screen reader and a keyboard, and the sound tells the story on its own.

What we were careful about
- No fake data, timings or scales. Every visual exaggeration is written in the story notes.
- A correlation is not a cause. For example, forests and CO2 match at r -0.93, but only 0.30 once the seasons are removed, and the story says so.
- Music, not noise: soft scales and pleasant chords, and every layer can be switched off.
- It runs in any modern browser, phones included, with no install.

Tools
Python (NumPy, h5py, Pillow), NASA Earthdata, JavaScript, three.js, Web Audio API, Cloudflare Pages, GitHub.
