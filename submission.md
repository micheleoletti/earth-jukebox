# Earth Jukebox: submission text (NASA Space Apps 2026)

Challenge: The Earth Information Jukebox

## Project name

Earth Jukebox

## High-level summary

Earth Jukebox lets anyone hear how the planet is connected. It plays twelve real Earth stories, from Canadian wildfire smoke reaching New York to the tides travelling along a coast, on a 3D globe and as music at the same time. Every sound comes from measured data: the music grows louder and busier the further the planet is from normal, and when two signals are linked (fire and smoke, wind and storm surge, snow and temperature) the link itself chooses the harmony. Moving together sounds like unison, opposite signals answer each other in counterpoint, a delay becomes a canon, and a weak link drifts gently out of tune. Because the story is carried by sound, spoken announcements and keyboard control, blind and low-vision users get the same discovery as sighted users. It answers the challenge by turning NASA Earth Information Center themes into sonifications that are both musically pleasing and scientifically honest.

## Detailed description

### What it does

Earth Jukebox is a web page with a 3D globe and a music engine. The first screen is the jukebox: twelve stories, each a card. Tap one and the camera flies to the place, the data starts to play, and the music starts.

Stories (events are one-off moments, cycles repeat):

| # | Story | Place and time | Main signal (drives the music) | Partner signal (the link) |
|---|---|---|---|---|
| E1 | Smoke Across a Continent | Quebec to New York, May to June 2023 | New York PM2.5 | Quebec fire power (FIRMS) |
| E2 | Hurricane Ian Makes Landfall | Southwest Florida, September 2022 | wind at Fort Myers | storm surge at the tide gauges |
| E3 | The Day the Air Rang | Hunga Tonga, global, January 2022 | air-pressure jump at 15 points | water level at 15 tide gauges |
| E4 | Black Summer | Southeast Australia, 2019 to 2020 | Sydney PM2.5 | fire power (FIRMS) |
| E5 | Italy Holds Its Breath | Po Valley, January to May 2020 | ground NO2 vs the 2015 to 2019 normal | wind speed |
| C1 | The Breathing Coast | US East and West coasts, March 2024 | water level at Boston | water level at a second gauge |
| C2 | The City Breathes | Milan and Paris, 4 weeks of January 2019 | hourly NO2 in Milan | wind speed |
| C3 | The Monsoon Arrives | India, 2019 | rain | vegetation greenness |
| C4 | Africa's Fire Belt | Sub-Saharan Africa, 2019 | monthly fire count | rain |
| C5 | Snow Follows the Cold | Northern Hemisphere, 2019 to 2020 | snow-covered area | air temperature |
| C0 | The Planet Breathing | Global, 2021 | northern forest greenness | CO2 seasonal swing at Mauna Loa |
| E0 | The City That Went Quiet | Wuhan, 2019 to 2020 | satellite NO2 vs the 2015 to 2019 normal | (single signal) |

On the globe each dataset has one 3D form: fires are flames (area proportional to fire power), smoke is particles moved by the real wind, stations are labelled pillars, rain, snow and temperature tint the ground, wind is drawn as streaks, a hurricane is a spiral on its best track, tide gauges are water columns with ripples. Under the globe, a chart shows one lane per dataset; a glowing thread joins the main signal and its partner, with the measured correlation r and the delay written on it.

### How it works

1. **Data pipelines** (Python, one script per story) download the raw data from NASA and partner archives, cut the region and period, compute a normal (for events: the same calendar window in earlier years; for cycles: the signal's own range), measure the link between the two signals (Pearson r over a range of lags, with daily or yearly cycles removed where they would fake a link; the method is written in each story), and write a small data file per story.
2. **The globe** (JavaScript, three.js, WebGL) loads a story file only when the story is picked, so the first page load is about 2 MB. Layers fade in and out, every lane has an on/off switch.
3. **Music**: pre-rendered seamless loops (D major, 96 BPM, 8 bars), all synthesized by our own code: 5 drum intensities and 14 synth layers. One intensity knob (0 to 1) crossfades them. The knob is driven by the story's main signal every frame: normal = 0.35, 4 standard deviations above normal = 1, 2 below = 0, linear. For cycles, intensity is the position in the signal's own range. Data gaps ease back to normal and never invent a peak. Switching a 3D layer off mutes its voice.
4. **Connection voices**: two live Web Audio voices sing the main signal and its partner. The measured link chooses how they relate: positive = a fifth above in unison, negative = counterpoint, a delay = a canon delayed by the lag, weak (|r| below 0.3) = a gentle detune. When the rolling correlation is at its strongest, a resolving chord swells and the thread glows (the "lock-in").
5. **Honesty rules** built into every story: gaps stay gaps, scales are linear with a stated floor, models are labelled as models, every visual exaggeration (pillar height, smoothing, particle motion) is written in the footer, weak links are reported as weak, and playback speed never changes with the music.

### Accessibility

- Screen-reader announcements (aria-live) at each story beat, with real numbers.
- Full keyboard control: 1 to 0, minus and equals pick stories, Space plays or pauses, arrows step through time, M mutes, Shift plus 1 to 6 switch layers, I opens the sources panel.
- A text description of every story (period, layers, link, key numbers).
- Reduced-motion mode (no auto-rotation, no camera flights, fewer particles), high-contrast text.

### Benefits and goals

- Makes Earth science perceivable without sight, and memorable with it.
- Shows connections instead of isolated datasets: the planet as one system.
- Keeps the science honest: every number on screen and in sound is measured or clearly labelled as a model.
- Goal: an open jukebox where anyone can add a story with one pipeline script and one preset.

### Tools and languages

Python (numpy, netCDF4, pandas, h5py), JavaScript (three.js, Web Audio API), HTML and CSS. Headless Chrome (Puppeteer) for automated screenshots and frame-time checks.

## Use of AI (SI)

- The idea, the stories, the narrative ("hear how the planet is connected", links chosen as harmony) and every design decision are human.
- AI coding tools (Claude Code by Anthropic) wrote most of the code and data-processing scripts under human direction and review.
- No AI-generated audio: all music is synthesized by our own code (Web Audio, rendered offline in the browser). No AI-generated images or video.

## NASA data used

| Dataset | Stories | Link |
|---|---|---|
| FIRMS VIIRS S-NPP 375 m active fires (VNP14IMG), country yearly archives | E1, E4, C4 | https://firms.modaps.eosdis.nasa.gov/country/ |
| GEOS-CF v1 assimilation (model): surface PM2.5, 10 m wind, 2 m temperature | E1, E4 | https://gmao.gsfc.nasa.gov/weather_prediction/GEOS-CF/ |
| GPM IMERG Final V07: half-hourly (GPM_3IMERGHH), daily (GPM_3IMERGDF), monthly (GPM_3IMERGM) | E2, C3, C4 | https://doi.org/10.5067/GPM/IMERGDF/DAY/07 , https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07 |
| OMI/Aura OMNO2d v003 tropospheric NO2 | E5, E0 | https://doi.org/10.5067/Aura/OMI/DATA3007 |
| MODIS/Terra MOD10CM v061 monthly snow cover | C5 | https://doi.org/10.5067/MODIS/MOD10CM.061 |
| MODIS/Terra MOD13C2 v061 monthly NDVI | C0, C3 | https://doi.org/10.5067/MODIS/MOD13C2.061 |
| MERRA-2 (model): M2T1NXSLV (850 hPa wind), M2TMNXSLV (2 m temperature), M2C0NXASM (land fraction) | C3, C5 | https://doi.org/10.5067/VJAFPLI1CSIV , https://doi.org/10.5067/AP1B0BA5PD2K |
| GRACE and GRACE-FO JPL mascon RL06.3 CRI v04 (water storage) | C3 | https://doi.org/10.5067/TEMSC-3JC634 |
| GIBS Blue Marble shaded relief (backdrop, not data) | all | https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api |
| NASA SVS / Earth Information Center visuals (linked from each story's Sources panel) | all | https://svs.gsfc.nasa.gov/gallery/earth-information-center/ |

## Other references

- NOAA CO-OPS tide gauges: water level, hourly heights, tide predictions: https://tidesandcurrents.noaa.gov/
- NOAA NCEI IBTrACS v04r01 best tracks: https://www.ncei.noaa.gov/products/international-best-track-archive
- NOAA NHC Hurricane Ian Tropical Cyclone Report: https://www.nhc.noaa.gov/data/tcr/AL092022_Ian.pdf
- NOAA GML Mauna Loa CO2: https://gml.noaa.gov/ccgg/trends/
- USGS earthquake catalog, event us7000gc8r (Hunga Tonga eruption): https://earthquake.usgs.gov/earthquakes/eventpage/us7000gc8r
- Lamb wave speed for the reference ring: Matoza et al. 2022, Science 377, https://doi.org/10.1126/science.abo7063 ; Wright et al. 2022, Nature 609
- ECMWF ERA5 reanalysis (model), via the Open-Meteo historical weather API: https://open-meteo.com/en/docs/historical-weather-api
- OpenAQ archive (New York monitors, US EPA AirNow feed): https://openaq.org/
- NSW Government Air Quality Monitoring Network: https://www.airquality.nsw.gov.au/
- ACT Health air quality monitoring data: https://www.data.act.gov.au/
- European Environment Agency air quality e-reporting, verified E1a: https://eeadmz1-downloads-webapp.azurewebsites.net/
- US Naval Observatory moon phases: https://aa.usno.navy.mil/data/MoonPhases
- Natural Earth 1:50m countries: https://www.naturalearthdata.com/
- three.js 0.160 (MIT), loaded from jsDelivr: https://threejs.org/
- Fonts: system fonts only (San Francisco, Helvetica, Menlo). No web fonts.
- Music: all loops synthesized by our own code (music-engine/prototype/loop-engine.js, synth-drums.js), live connection voices with the Web Audio API. No samples are shipped.

## 30 second video script (draft)

| Time | Picture | Words (spoken or subtitle) |
|---|---|---|
| 0:00 | Logo on the spinning globe | "Earth Jukebox, by team [name]." |
| 0:02 | Jukebox screen with the twelve cards | "For the Earth Information Jukebox challenge: data you can hear, for everyone." |
| 0:05 | Title over the globe | "Hear how the planet is connected." |
| 0:10 | Story 1: Quebec flames, smoke drifting south, New York pillars rising, the music building | "Real NASA fire data, real smoke, real air in New York. The music gets louder as the air gets worse." |
| 0:16 | The thread between the lanes glows, the chord resolves (lock-in) | "When two signals move together, you hear them lock in." |
| 0:20 | Quick cuts: tides travelling up the coast, snow and cold | "Twelve stories, all measured, nothing invented." |
| 0:25 | Back to the jukebox | "Anyone, sighted or not, can now hear the planet as one system." |
