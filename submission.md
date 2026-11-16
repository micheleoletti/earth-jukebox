# Earth Jukebox: answers for the NASA Space Apps 2026 project form

Team: **Chopper Team** · Challenge: **The Earth Information Jukebox**

## Project name

Earth Jukebox

## High-level summary

Earth science should not be limited to sight. Earth Jukebox turns NASA Earth Information Center (EIC) visualizations, enriched with open NASA datasets, into a 3D globe you can explore and listen to. Each story follows one real event or natural cycle (a monsoon, a hurricane, a volcanic shock wave, a burning savanna, the planet's yearly breath) and shows how two things in the data are connected. Real nature sounds (rain, fire, wind, waves) follow the data under the centre of the screen, and a soft chord tells the connection: when two signals move together the chord is consonant and full, when the planet moves away from normal a tension note appears. Harmony expresses balance, dissonance reveals change. It answers the challenge by pairing an EIC visualization with a real-time sonification read from its frames, and it matters because it opens Earth data to blind and low-vision people, to children and to anyone who is not a scientist.

## Demo link (video of 30 seconds or less, public)

TODO: Jose's video link (YouTube or Vimeo, public, English subtitles if spoken in another language).

## Final project link (public, no login)

- Live app: https://earth-jukebox-cyd.pages.dev
- Code: https://github.com/micheleoletti/earth-jukebox (branch `c4-breathing`)

## Detailed description

### What it does

Earth Jukebox opens on a slowly turning globe with a glowing point for each story. Tap a point and the camera flies in, the story's data appears on the globe and in a chart under it, and the sound starts. Five stories:

| Story | Where and when | What you see | The connection you hear |
|---|---|---|---|
| The Monsoon, Through NASA Eyes | India, 2025 | The NASA EIC rain anomaly frames wrapped on the globe (where it rains more or less than usual), falling rain, wind, greening land, water stored underground | Rain comes, the land turns green about two months later (r 0.85); stored water follows the rain |
| Hurricane Ian Makes Landfall | Florida, September 2022 | The storm spiral on its real track, wind, tide-gauge water columns, rain from space | Wind rises and the sea climbs onto the land a few hours later (r 0.64) |
| The Day the Air Rang (Hunga Tonga) | Pacific, January 2022 | The volcano, its eruption, the expected shock front circling the planet, real barometer jumps and sea wobbles at 15 NOAA gauges | The air jump arrives at each gauge on time (14 of 15 gauges, 0.9 to 2.2 hPa), the sea wobbles about 3 hours later |
| The Planet Breathing | Northern Hemisphere, 2021 to 2023 | Trees that grow leaves and lose them with each month's greenness, CO2 haze | Forests green up and CO2 in the air drops, about 2 months later (r -0.93); each year a little more CO2 than the last |
| Africa's Fire Belt | Southern Africa, 2019 | Every satellite fire detection as a flame, rain, the equator line | When the rain stops, the fires rise about a month later (r -0.90) |

Two modes: **Simple** (plain words for a five-year-old, no units, a comment under the chart at each key moment) and **Science** (dataset names, units, correlations, lags and every method in the footer).

### How it works

- **Data:** each story is built by a Python pipeline (`data-pipeline/`) from public NASA and NOAA archives into a small data file. The page is a single three.js web app that works offline from a file or online.
- **Honesty rules:** nothing is faked. Gaps stay gaps, models are labelled "model", every visual exaggeration (pillar heights, flame sizes) is written in the story footer, and every connection is measured (Pearson r at the lag with the strongest link) and drawn only if it is at least moderate.
- **Connections:** each measured link is a glowing thread between two chart lines (colour gradient from one to the other), grey when the two are not moving together now and bright and thick when they are.
- **Sound, layer 1 (nature):** nine real public-domain recordings (fire, rain, wind, storm wind, waves, thunder, volcano, birds, city traffic) and a low space drone. Each sound's loudness follows the data at the centre of the screen: point at the fires and they crackle, point at the rain and it pours, zoom in and it gets closer.
- **Sound, layer 2 (harmony):** a soft D major chord. Each connection is one voice (a cluster of chord tones): it fades in when its two signals move together and breathes with how strongly they change together right now. The base lifts when any connection is active. A single tension note fades in as the main signal leaves its normal range. Each story has its own musical scale.
- **EIC frames into sound:** in the monsoon story the tension note is read from the NASA EIC anomaly frame under the centre of the screen: its colour is turned back into "mm per day wetter or drier than usual" with the frame's own colour bar, so the further from usual, the more tension you hear.
- **Event sounds:** at real moments in the data (the eruption, landfall) a matching recording plays.

### Accessibility

- Screen-reader announcements of each story, its key moments and the measured links, plus a full text description of every story.
- Full keyboard control (number keys for stories, Space to play, M to mute, Esc to go back to the globe).
- Sound carries the story without the picture: what is happening (nature sounds) and how things connect (harmony).
- Reduced-motion mode (`?reduced`), large readable text, Simple mode for children and non-scientists.

### Benefits and goals

- Makes Earth science reachable without sight, and without scientific training.
- Shows the planet as one connected system instead of separate datasets.
- Every number is real and traceable, so teachers and scientists can trust it.
- Built to grow: a new story is one data pipeline plus one preset.

### Tools and languages

JavaScript, three.js (WebGL), Web Audio API, HTML/CSS; Python with NumPy, h5py and Pillow for data pipelines; ffmpeg for audio; Cloudflare Pages for hosting.

## Use of AI (SI)

- The idea, the stories, the narrative ("Harmony expresses balance. Dissonance reveals change.") and every design decision are human.
- AI coding tools (Claude Code by Anthropic) wrote most of the code and data-processing scripts under our direction and review.
- No AI-generated audio, images or video. The sounds are real CC0 recordings from Freesound and sounds synthesized by our own code.

## NASA data used

| Dataset | Story | Link |
|---|---|---|
| **NASA Earth Information Center / SVS 4897**, Seasonal Global Precipitation Variation (GPM), daily anomaly frames | Monsoon | https://svs.gsfc.nasa.gov/4897 |
| GPM IMERG V07 precipitation: Late daily (GPM_3IMERGDL), Final monthly (GPM_3IMERGM), Final half-hourly (GPM_3IMERGHH) | Monsoon, Ian, Africa | https://doi.org/10.5067/GPM/IMERGDL/DAY/07 · https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07 · https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHH_07/summary |
| MODIS/Terra MOD13C2 v061 monthly NDVI (vegetation greenness) | Monsoon, Planet Breathing | https://doi.org/10.5067/MODIS/MOD13C2.061 |
| GRACE and GRACE-FO JPL mascons RL06.3 CRI v04 (water stored on land) | Monsoon | https://doi.org/10.5067/TEMSC-3JC634 |
| MERRA-2 M2T1NXSLV (850 hPa wind, model) | Monsoon | https://doi.org/10.5067/VJAFPLI1CSIV |
| FIRMS VIIRS S-NPP 375 m active fires (VNP14IMG) | Africa | https://firms.modaps.eosdis.nasa.gov/country/ |
| GIBS Blue Marble shaded relief (globe backdrop, not data) | all | https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api |

## Other references (data, code, sounds)

- NOAA CO-OPS tide gauges: water level, tide predictions and air pressure (barometers): https://tidesandcurrents.noaa.gov/
- NOAA NCEI IBTrACS v04r01 best tracks: https://www.ncei.noaa.gov/products/international-best-track-archive
- NOAA NHC Hurricane Ian Tropical Cyclone Report: https://www.nhc.noaa.gov/data/tcr/AL092022_Ian.pdf
- NOAA GML Mauna Loa CO2: https://gml.noaa.gov/ccgg/trends/
- USGS earthquake catalog, event us7000gc8r (Hunga Tonga eruption): https://earthquake.usgs.gov/earthquakes/eventpage/us7000gc8r
- Lamb wave speed for the reference front: Matoza et al. 2022, Science 377, https://doi.org/10.1126/science.abo7063 ; Wright et al. 2022, Nature 609
- ECMWF ERA5 reanalysis (model), via the Open-Meteo historical weather API: https://open-meteo.com/en/docs/historical-weather-api
- Natural Earth 1:50m countries: https://www.naturalearthdata.com/
- three.js 0.160 (MIT): https://threejs.org/
- Sound recordings (all CC0, Freesound, found with Openverse):
  - Fire: "Bonfire HQ.wav" by tosha73, https://freesound.org/people/tosha73/sounds/513280
  - Rain: "1 Minute Rain (Medium)" by yzhamua, https://freesound.org/people/yzhamua/sounds/188655
  - Wind: "a gentle breeze, wind 1" by mario1298, https://freesound.org/people/mario1298/sounds/181250
  - Storm wind: "swirling winter wind gusty grains sand" by kyles, https://freesound.org/people/kyles/sounds/454213
  - Waves: "ocean waves 01" by rucisko, https://freesound.org/people/rucisko/sounds/164767
  - Thunder: "Thunder" by Fission9, https://freesound.org/people/Fission9/sounds/465314
  - Volcano: "S35-08 Volcano explosion with debris and lava" by craigsmith, https://freesound.org/people/craigsmith/sounds/675739
  - Birds: "Forest Birds" by NightVoice, https://freesound.org/people/NightVoice/sounds/123999
  - City traffic: "Hamburg City Traffic Ambience" by Kinoton, https://freesound.org/people/Kinoton/sounds/352152
- Synthesized sound (space drone, harmony chord): our own code with the Web Audio API.
- Fonts: system fonts only.

## 30 second video script (for Jose)

| Time | Picture | Words (spoken or subtitle) |
|---|---|---|
| 0:00 | Globe turning, story points glowing | "We are Chopper Team." |
| 0:02 | Close on the globe | "Earth science shouldn't be limited to sight." |
| 0:05 | Monsoon: NASA EIC rain map on India, rain falling, sound rising | "Using NASA Earth Information Center visualizations, enriched with open datasets, Earth Jukebox brings our planet's patterns and events to life." |
| 0:13 | Chart threads lighting up, chord swelling | "We reveal hidden connections and turn them into music. Harmony expresses balance. Dissonance reveals change." |
| 0:21 | Quick cuts: Ian's landfall, Tonga's shock wave, forests breathing | "Because music is a universal human language." |
| 0:27 | Back to the globe, title | "Experience Earth Breathing with Chopper Team." |
