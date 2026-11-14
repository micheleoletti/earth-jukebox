# Candidate events: stories we could tell

Every candidate below is a "multi-angle" story: one real phenomenon seen by 2+ data sources from `data_map.csv`.
The goal of the stats step is to **confirm and measure** each link (strength, lag, sign), not to discover new ones.

Legend
- **Sources**: ids from `data_map.csv`. **Bold** = no auth (free, ready now). Plain = needs free Earthdata login (most are huge: always take a small regional slice).
- **Link**: the expected relationship between the signals.
- **Shape**: how it would sound (from `narrative-alternative.md`): unison (move together), counterpoint (opposite), canon (one follows another after a lag), detune (link breaks), crescendo.
- **Confidence**: `known` = well documented in literature/news · `plausible` = physically expected, check data · `verify` = unsure our sources capture it.

Not in the data map but would help: NOAA Mauna Loa CO2 (daily), NOAA ONI El Niño index (monthly), NSIDC sea ice index.

---

## Shortlist (recommended first)

| # | Story | Why | Auth |
|---|---|---|---|
| 1 | Canada fires → NYC smoke (Jun 2023) | iconic image, clean multi-day lag, all no-auth | none |
| 2 | Hurricane landfall (Ian 2022) | pressure/wind/surge/rain all lock together, crescendo | none |
| 3 | Tides around a coastline | literal rhythm, canon between stations, zero risk | none |
| 4 | City breathing: rush hour + weekend NO2 | daily + weekly rhythm = bars and beats | none |
| 5 | Po Valley lockdown (Mar 2020) | the "out of tune" story: link breaks, then retunes | none |

---

## One-off events

| # | Event | When / where | Sources | Link | Shape | Confidence |
|---|---|---|---|---|---|---|
| E1 | Canada wildfires → NYC orange sky | 2023-06-05 to 06-09, Quebec → NYC | **N05 FIRMS**, **N09 GEOS-CF**, **E02 OpenAQ**, **E01 ERA5**, **N12 EONET**, **N13 GIBS**, N23 MAIAC | fire power in Quebec, then PM2.5 spike in NYC ~1-3 days later when wind turns north | canon | known |
| E2 | Hurricane Ian landfall | 2022-09-26 to 09-30, SW Florida | **E04 IBTrACS**, **E01 ERA5**, **E10 NOAA tides**, **N12 EONET**, **N13 GIBS**, N03 IMERG | pressure falls as wind rises; storm surge at Fort Myers gauge peaks at landfall; rain bands follow | counterpoint + crescendo | known |
| E3 | Hurricane Milton (alt. to Ian) | 2024-10-07 to 10-10, Gulf → Tampa | **E04**, **E01**, **E10**, **N12**, **N13** | same as E2; note reverse surge (water pulled out of Tampa Bay) | counterpoint | known |
| E4 | Hurricane Harvey rain | 2017-08-25 to 09-01, Houston | **E04**, **E01**, **E10**, N03 IMERG, N18 SMAP | storm stalls; rain accumulates; soil saturates days later | canon (slow) | known |
| E5 | Maui / Lahaina fire | 2023-08-08, Maui; Hurricane Dora passing far south | **E04** (Dora track), **E01** (wind gusts), **N05 FIRMS**, **N12** | distant hurricane + high pressure north drive downslope winds, then fire explodes | canon | known |
| E6 | Spain / SW Europe heatwave + fires | 2022-07-10 to 07-20, Iberia | **E01 ERA5**, **N02 POWER**, **N05 FIRMS** (Spain CSV already downloaded), **E07 EEA** (ozone, PM), N20 MOD11 LST, N14 MCD64A1 | heat rises, fires multiply, ozone and PM follow | voices join one by one (crescendo) | known |
| E7 | Pacific NW heat dome | 2021-06-25 to 07-02, BC / Washington | **E01**, **N02**, **N05** (Lytton fire), **E02 OpenAQ** | record heat, then fire, then smoke | crescendo + canon | known |
| E8 | Po Valley COVID lockdown | 2020-03-09 to 05-04, N Italy | **E07 EEA** NO2, **N09 GEOS-CF**, **E01** wind, N25 OMI NO2, N07 Black Marble | NO2 normally follows weather/traffic; traffic drops, NO2 falls while weather stays normal: the link breaks | detune, then retune | known |
| E9 | Wuhan lockdown | 2020-01-23 to 04-08 | **N09 GEOS-CF**, **E02 OpenAQ** (sparse), N25 OMI | same as E8, earlier and stronger | detune | known (OpenAQ coverage: verify) |
| E10 | Australia Black Summer fires | 2019-12 to 2020-01, SE Australia | **N05**, **N09** (CO, PM), **E01**, **E02** (Sydney, Canberra), **N12**, N14 MCD64A1 | fire power vs city smoke vs hot/dry wind days | canon | known |
| E11 | Hunga Tonga eruption pressure wave | 2022-01-15, ripples around the globe for days | **E09 USGS**, **E10 NOAA tides** (meteotsunami at Pacific/Atlantic gauges), **E01** (surface pressure) | one blast; pressure wave + sea-level wobble arrive at each station by distance | one note rippling around the planet (canon across stations) | known (ERA5 capturing the wave: verify) |
| E12 | Tohoku tsunami | 2011-03-11, Japan → Pacific | **E09 USGS**, **E10 NOAA tides** (Hawaii, California gauges) | quake, then tsunami arriving at each gauge hours later, by distance | canon | known (pre-2012: no FIRMS/Black Marble) |
| E13 | Turkey-Syria earthquake | 2023-02-06 | **E09 USGS** (aftershocks), N07 Black Marble (lights out), **N12** | quake + aftershock decay; city lights dim, slowly recover | rhythm decays + detune | known (Black Marble: auth, slice only) |
| E14 | Texas freeze blackout | 2021-02-13 to 02-20 | **E01**, **N02** (temp), N07 Black Marble | temperature drops, then lights go out | canon | known |
| E15 | Pakistan floods | 2022-07 to 2022-09 | **E01**, **N12**, N03 IMERG, N18 SMAP, N28 GRACE | rain, then soil saturation, then water mass (GRACE) weeks later | slow canon chain | known |
| E16 | Amazon drought 2023 | 2023-09 to 2023-11, Manaus | **E01**, **N05**, **E02** (Manaus smoke: verify), N19 SWOT (river height), N28 GRACE | rain deficit, then record low Rio Negro + fires + smoke | counterpoint (water down, fire up) | known (SWOT coverage: verify) |
| E17 | Saharan dust "Godzilla" plume | 2020-06-14 to 06-28, Sahara → Caribbean → US | **N09 GEOS-CF**, **E02** (Puerto Rico), **E01** wind, N23 MAIAC AOD | dust leaves Africa, crosses the Atlantic in ~1 week | canon (long) | known (GEOS-CF dust: verify) |
| E18 | Storm Daniel / Derna | 2023-09-04 to 09-11, Greece → Libya | **E01**, **N12**, **E04** (if listed as medicane), N03 IMERG | extreme rain in Greece, then dam collapse in Libya | canon | plausible |
| E19 | Hurricane Otis rapid intensification | 2023-10-22 to 10-25, Acapulco | **E04**, **E01**, **N12** | wind jumps from tropical storm to Cat 5 in ~24 h | sudden crescendo | known |

---

## Cyclical patterns

| # | Pattern | Period | Sources | Link | Shape | Confidence |
|---|---|---|---|---|---|---|
| C1 | Tides | ~12.4 h (+ spring/neap ~14.8 d) | **E10 NOAA tides** (many stations) | the Moon's pull; each station along a coast is phase-shifted | canon between stations; literal pulse | known |
| C2 | City breathing: rush hour + weekend effect | 24 h + 7 d | **E07 EEA** (hourly NO2), **E02 OpenAQ**, **E01** wind, N24 TEMPO (US, hourly) | NO2 peaks at rush hours, drops at weekends; strong wind dilutes it (opposite) | rhythm: day = bar, week = phrase; wind as counterpoint | known |
| C3 | Daily heat cycle | 24 h | **N02 POWER** (sun + temp), **E01** | temperature follows sunlight ~2-3 h later | canon | known |
| C4 | Planet breathing (CO2 vs vegetation) | 1 yr | N15 MOD13 NDVI, N16 MOD17 GPP, N26 OCO-2; (+ Mauna Loa, not in map) | northern forests green up in spring, CO2 drops; leaves fall, CO2 rises | counterpoint | known |
| C5 | Monsoon (India) | 1 yr | **E01** (rain, wind reversal), **N02**, N03 IMERG, N18 SMAP, N15 NDVI, N28 GRACE | wind flips, rain arrives, soil wets, land greens, water mass rises: each a few weeks later | canon chain (5 voices) | known |
| C6 | Africa fire belt | 1 yr | **N05 FIRMS**, **E01** rain, N14 MCD64A1 | fires sweep north and south of the equator with the dry season; opposite of rain | counterpoint + a sweep across the map | known |
| C7 | Green wave + bird migration | 1 yr (spring) | **E06 GBIF** (occurrences), **E01** temp, N15 NDVI | birds arrive as land greens northward | canon | plausible (GBIF = observer counts, weekend bias) |
| C8 | Snow vs temperature | 1 yr | N21 MOD10 snow, **E01**, **N02** | snow cover rises as temp falls | counterpoint | known |
| C9 | Hurricane season | 1 yr | **E04 IBTrACS** (storm counts), E03 Copernicus Marine SST (free account) | storms peak when sea is warmest (Aug-Oct) | unison (lagged) | known |
| C10 | North Atlantic spring bloom | 1 yr | N22 PACE chl (2024+), E03 SST, **N02** radiation | light + stratification, then phytoplankton bloom | canon | known |
| C11 | Lightning: afternoon + summer | 24 h + 1 yr | N06 ISS LIS (2017-2023), **E01** temp | storms fire in the afternoon heat and in summer | canon (daily) | known |
| C12 | El Niño years | 2-7 yr | **N08 GISTEMP**, **N05 FIRMS** (Indonesia fires 2015, 2019, 2023), **E04**; (+ NOAA ONI, not in map) | El Niño, then global temp up ~3 months later, Indonesian fires spike | slow canon | known |
| C13 | Festival lights (Ramadan, Diwali, Christmas) | 1 yr (moving dates) | N07 Black Marble | night lights brighten on cultural calendars | human rhythm on top of nature | known (Black Marble: auth) |
| C14 | Aftershock decay | days to years after a quake | **E09 USGS** | aftershock rate decays over time (Omori law) | rhythm that slows down | known (single source: not a correlation story) |

---

## Long arcs (backdrop, not events)

| # | Arc | Period | Sources | Link | Shape |
|---|---|---|---|---|---|
| L1 | Global warming | 1880-2026 | **N08 GISTEMP**, N27 CERES (energy imbalance) | temperature rises as Earth keeps more energy | rising drone under everything |
| L2 | Ice loss | 2002-2026 | N28 GRACE (Greenland, Antarctica mass), N29 ICESat-2 | mass falls year after year | descending bass line |
| L3 | Forest loss | 2001-2025 | **E05 Global Forest Watch**, **N05 FIRMS** | fire and deforestation hotspots overlap (Amazon, Indonesia) | unison (spatial) |
| L4 | Cities growing at night | 2012-2026 | N07 Black Marble, **E07** / **E02** (pollution) | new lights where pollution grows | unison (spatial) |

---

## Next step
For each shortlisted story:
1. Fix the exact dates, bounding box, and stations/points.
2. Pull the small slice in the signal format `{id, unit, raw, norm, region, t}` (see `music-engine/HANDOFF.md`).
3. Run one shared script: remove the daily/yearly cycle if needed, then correlation + best lag.
4. Keep only links that pass; their numbers (strength, lag, sign) drive the music.
