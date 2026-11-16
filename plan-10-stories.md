# Overnight plan: 10 new stories (5 events + 5 cycles)

Excluded: E6 Iberia (Jose), long arcs, C4 Breathing and E9 Wuhan (already built).
All stories live in the same globe (`playground/breathing.html`), selectable from the story tabs.
Rules carried over: 1 dataset = 1 3D representation = 1 chart lane; gaps stay gaps; linear scales with stated floors; models labelled as models; every exaggeration written in the footer.

## Endpoint check (2026-11-14, all reached)
FIRMS country CSV, OpenAQ S3 archive, Open-Meteo ERA5, NOAA CO-OPS, IBTrACS, USGS, EEA, GEOS-CF OPeNDAP, GIBS, CMR. Earthdata token present here and on the Air. Air: up, 59 GB free.

## The 10 stories

### Events
| # | Story | Window / place | Data (all reachable) | 3D layers | Risk |
|---|---|---|---|---|---|
| E1 | Canada fires → NYC orange sky | 2023-05-25 to 06-15, Quebec + NYC | FIRMS VIIRS Canada 2023 CSV; OpenAQ NYC PM2.5 (S3); ERA5 wind (Open-Meteo); GEOS-CF PM2.5 grid (model) | fire points (flames, size = FRP), smoke particles drifting on wind, station pillars | OpenAQ station ids to pick; GEOS-CF is a model: label it |
| E2 | Hurricane Ian landfall | 2022-09-23 to 10-01, SW Florida | IBTrACS track; ERA5 pressure + wind; CO-OPS Fort Myers 8725520 water level (6 min); IMERG daily rain (Earthdata) | storm spiral on track, sea-level column at gauge, rain field | none |
| E3 | Hunga Tonga pressure wave | 2022-01-14 to 01-18, global | USGS event; CO-OPS 6-min at ~15 Pacific/Atlantic gauges; ERA5 hourly surface pressure at those points | expanding ring (computed from blast time at 1,000 km/h, drawn as a reference, not data), gauge columns | ERA5 hourly may smooth the ~2 hPa wave: if not visible, drop that lane and say so |
| E4 | Australia Black Summer | 2019-11-01 to 2020-02-15, SE Australia | FIRMS VIIRS Australia 2019+2020 CSV; OpenAQ Sydney/Canberra PM2.5; ERA5 temp + wind | fire points, smoke particles, station pillars | OpenAQ coverage in AU: verify |
| E5 | Po Valley lockdown | 2020-01-01 to 05-31, N Italy | OMI NO2 (reuse Wuhan pipeline, 2015-19 baseline aligned on calendar); EEA hourly NO2 Milan/Turin/Bologna; ERA5 wind | NO2 fog (existing), station pillars, wind streaks | none (pipeline exists) |

### Cycles
| # | Story | Period / place | Data | 3D layers | Risk |
|---|---|---|---|---|---|
| C1 | Tides | 31 days (spring/neap), US East + West coasts | CO-OPS hourly water level, ~20 stations | animated sea-level columns or wave rings per station, phase visible along the coast | none |
| C2 | City breathing | 4 weeks, Milan (+ Paris) | EEA hourly NO2; ERA5 wind | station pillars pulsing hourly, wind streaks | none |
| C3 | India monsoon | 1 year (2019), India | ERA5 rain + wind direction (point grid); MOD13C2 NDVI (existing pipeline); GRACE mascon (44 MB, Earthdata) | rain field, wind streaks flipping, green-up (existing NDVI ground), water-mass tint | GRACE is monthly ~300 km: label resolution |
| C4 | Africa fire belt | 1 year (2019), sub-Saharan Africa | FIRMS VIIRS country CSVs (~25 countries); ERA5 rain grid; NDVI | fire points sweeping N then S, rain field | download size (~200 MB, do on Air) |
| C5 | Snow vs temperature | 1 year (2019-20), Northern Hemisphere | MOD10CM monthly snow CMG (Earthdata, 0.4 GB); ERA5 2 m temp grid | snow cover on ground (white), temperature tint | NSIDC may need a one-time Earthdata app approval (like GES DISC did); fallback: ERA5 snow depth via Open-Meteo |

## New engine pieces (shared, built once)
1. **Story data out of the HTML.** Page is already 10.4 MB. Each story becomes `playground/stories/<id>.js` (`window.STORY_DATA['id'] = {...}`), loaded by `<script>` on select. Works from file://, keeps first load small.
2. **Generic layer types** (each = one chart lane, toggle, fade in/out like trees/fog):
   - `points` (fires, quakes): instanced, size = value, staggered pop
   - `particles` (smoke, dust): advected by a wind grid, density = value
   - `pillars` (stations: PM2.5, NO2, sea level): height = value, linear, labelled
   - `field` (rain, temperature, snow, NO2): ground tint or existing fog
   - `streaks` (wind)
   - `track` + `spiral` (hurricane)
   - `ring` (reference wave front, drawn dashed, labelled "expected front")
3. **Time base per story:** hourly (tides, city, Tonga, Ian), daily (fires, lockdown), monthly (monsoon, Africa, snow). The chart and the playback speed adapt.
4. **Performance budget** (PERFORMANCE.md): at most 30k fire points, 30k particles; check frame time per story.

## Execution order (overnight, on the Air: this Mac can sleep)
1. **Job A (engine):** story loader + per-story data files + the generic layer types, Wuhan and Breathing moved to the new format. Must finish first; the other jobs only add files.
2. **Jobs B (data, parallel, 3 at a time):** one pipeline script per story in `data-pipeline/<id>.py`, output in `data/<id>/` and `playground/stories/<id>.js`. Each prints its headline numbers (correlation, lag, % change) and states the gaps.
3. **Job C (integration):** one story at a time: preset (camera, start, length, layers, insight, annotations, footer), build, syntax check, headless screenshot of each story.
4. Report: per story, what works, the headline numbers, what was dropped and why.

Rough time: A ~1.5 h, B ~2 h (in parallel), C ~3 h. Nothing committed; you review in the morning.

## What I still need from you
- Nothing blocking. Possible one click: the NSIDC Earthdata app approval for C5 (fallback ready if not).
- The Air must stay awake (Amphetamine).

## Music: one intensity per story (music-engine knob 0..1)
- Each story names one **hero signal**; intensity is computed from it every frame, never scripted by hand.
- Events: intensity = how far the hero is from normal, in the stress direction: normal = 0.35, +4σ = 1, -2σ = 0 (σ from the baseline years). Lockdowns go calm, fires and storms go loud. The same scale everywhere, so stories are comparable.
- Cycles: the baseline is the cycle itself, so intensity = position in the station's own min..max range (tides breathe, rush hours pulse).
- Linear mapping, stated in the footer. Gaps hold the last intensity and fade toward 0.35, never invent a peak.
- The same value highlights the hero layer on the globe (glow/bloom, chart lane brightness), so ears and eyes point at the same thing.
- Playback speed never changes with intensity (no faked timing).

| Story | Hero signal → intensity |
|---|---|
| E1 Canada→NYC | NYC PM2.5 |
| E2 Ian | wind at landfall gauge (then surge) |
| E3 Tonga / E16 Amazon | gauge pressure jump / rain deficit + fire count |
| E4 Black Summer | Sydney PM2.5 |
| E5 Po Valley | NO2 vs 2015-19 (drops = calm) |
| C1 Tides | water level, station range |
| C2 City breathing | hourly NO2, station range |
| C3 Monsoon | rain |
| C4 Africa fires | fire count in view |
| C5 Snow | snow-cover extent (colder = more intense) |

## Missing for the final delivery (deadline Sun 2026-11-15 23:59)
Must:
1. **Sound wired into the globe.** The music engine exists but the globe page plays nothing. Load loops as `.m4a` (not base64), tap-to-start (iOS), story hero → `setV(intensity)`, layer on/off → its synth layer on/off. Overnight job D.
2. **Connection music (the narrative).** Each story ships its measured link (sign, strength r, lag) and that picks the shape: unison / counterpoint / canon (delay = lag) / detune. Minimum: lane-to-lane "thread" in the chart with r and lag written on it, plus a lock-in chord when the link peaks.
3. **Accessibility** (the challenge is for blind and low-vision users): `aria-live` announcements per story beat ("NYC PM2.5 3x normal, smoke arrived 2 days after the fires"), full keyboard control, text description of every story, reduced-motion mode.
4. **Deploy:** public URL (Cloudflare Pages or GitHub Pages) + public repo; test in a private window; optional FortiGuard classification.
5. **Data / sources panel per story:** dataset, resolution, observed vs model, baseline method. Feeds the Validity score and the References field.
6. **30 s demo video with sound,** English subtitles, official structure (name, challenge, title + tagline, prototype, future). Screen capture of 2 to 3 stories with a lock-in moment.
7. **Project page text:** summary, detailed description, SI use (AI-written code; no AI audio), NASA data list, references (three.js, Blue Marble, every dataset, music tools).

Should:
8. **Relevance to EIC:** the challenge is framed around EIC visuals. Link each story to a matching EIC/SVS visual (e.g. fire smoke, hurricanes) in its sources panel and say the jukebox extends EIC content with live data.
9. **Landing screen:** slogan "Hear how the planet is connected", story picker as the jukebox, one-line how-to.
10. Per-story frame-time check on a phone.

Timing: stories (A, B, C) + sound (D) overnight on the Air; items 2 to 9 Sunday daytime; video + submit by ~20:00 Sunday to keep 4 h margin.
