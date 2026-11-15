# Story data format (playground/stories/<id>.js)

Each story pipeline `data-pipeline/<id>.py` writes one file with `storylib.write_story(id, obj)`:

```js
(window.STORY_DATA = window.STORY_DATA || {})['<id>'] = { ...obj };
```

The globe page loads it with a `<script>` tag when the story is selected (works from `file://`).
Keep each file **under 3 MB** (target 0.5 to 2 MB). Presentation (camera, insight line, footer, annotations text)
lives in the page preset; the data file carries data, numbers and sources.

## Top level

| key | type | meaning |
|---|---|---|
| `title` | str | working title |
| `timebase` | `"hour"` \| `"day"` \| `"month"` | one story step |
| `t0` | ISO UTC string | time of step 0 (`"2023-05-25T00:00Z"`; for months the 1st of the month) |
| `step_s` | int | seconds per step (3600 hourly, 86400 daily, 360 for 6-minute data); for `"month"` use 0 (calendar months) |
| `n` | int | number of steps (series length) |
| `region` | `{lat0, lat1, lon0, lon1}` | area of interest (for camera, bbox) |
| `hero` | layer id | the signal that drives the music intensity |
| `partner` | layer id | the main partner signal for the connection thread |
| `link` | dict | output of `storylib.link(hero_series, partner_series, ...)`: r, lag (in `lag_unit`, positive = partner follows hero), n, method, strength, curve. Add `lag_steps` (the lag in story steps) when the link was computed at a coarser step than the story (e.g. daily means of an hourly story) |
| `hero_norm` | dict | events: `{mean, sd, n, years, method}` of the hero over the baseline years (same calendar window); cycles: `{min, max, method}` of the hero series itself. Optional `base: [n]` per-step baseline mean if it varies inside the window |
| `stats` | dict | headline numbers, human readable keys, real values (e.g. `"NYC PM2.5 peak (ug/m3)": 165.4`, `"peak vs 2018-22 mean (%)": 1240`) |
| `gaps` | [str] | every gap and caveat in plain words |
| `beats` | [{t, text}] | announcements for screen readers at story step t, with real numbers, no em dashes |
| `events` | [{t, label}] and/or `bands: [{t0, t1, label}]` | annotation marks for the chart (step indices) |
| `sources` | [{name, producer, resolution, kind, period, baseline, url}] | every dataset used; `kind` = `"observed"` or `"model"` (reanalysis = model) |
| `layers` | [layer] | see below; one layer = one chart lane = one 3D layer |
| `script` | str | the pipeline file name |

## Layers

Every layer has: `id`, `type`, `name` (short lane name), `what` (one line: dataset, producer, observed/model), `color` (hex), `unit`,
`series: [n]` (the chart lane, one value per step, `null` = gap, never bridged), optional `baseline: [n]` (normal years, grey dashed), optional `band: [[lo, hi] | null]`.
Plus type-specific geometry:

| type | extra keys | 3D look |
|---|---|---|
| `points` | `points: {lat:[], lon:[], t:[], v:[]}`, `vmax` | fires: flame sprites appear at step t and fade over ~1 day; size linear in v (FRP, MW). At most 30,000 points (subsample evenly in time and say so in `gaps`) |
| `particles` | `grid` (density, see below) + `wind` (see below) | smoke: particles moved by the wind grid; a particle's opacity = density at its place (linear above `grid.floor`) |
| `pillars` | `stations: [{id, name, lat, lon, series:[n]}]` | station bars, height linear in value (0 at ground), labelled |
| `field` | `grid`, `palette` (`"rain"`, `"heat"`, `"cold"`, `"snow"`, `"drought"`, `"green"`, `"water"`) | ground tint |
| `streaks` | `wind` | wind streaks |
| `track` | `track: [{t, lat, lon, wind_kt, pres_hpa}]` | hurricane track + spiral at the current position |
| `ring` | `ring: {lat, lon, t, speed_kmh, label}` | dashed expanding reference front, labelled "expected front", not data |
| `columns` | `stations: [{id, name, lat, lon, series:[n]}]` | water columns + ripple rings (tide gauges) |

`grid` = `storylib.enc_grid(arr[nt, nlat, nlon], vmin, vmax, lat0, lat1, lon0, lon1, t, unit, kind, floor)`:
base64 uint8, byte 0 = no data, 1..255 linear vmin..vmax; `t` = story step of each frame (frames may be coarser than steps). Keep nlat*nlon*nt under ~1.5 M bytes.

`wind` = `storylib.enc_wind(u, v, ...)`: base64 int8, value * scale = m/s, -128 = no data. Keep it coarse (1 deg, 3 to 6 hourly or daily).

## Rules (from the owner, non-negotiable)

- Never fake timings, never bridge gaps (null stays null), never use scales that exaggerate a correlation.
- Linear scales with a stated floor. Models (ERA5, GEOS-CF, MERRA-2) are labelled `model`.
- If a link is weak, report it weak. Print the real numbers (`storylib.print_headline`).
- No em dashes in any text that ends up on screen (`what`, `beats`, `gaps`, `stats` keys, `sources`).
- Raw downloads go to `../earth-jukebox-cache/<id>/` (outside the repo). Never put the Earthdata token in a file in the repo.
