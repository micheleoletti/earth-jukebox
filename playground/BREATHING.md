# Earth Jukebox globe (all stories)

`playground/breathing.html` is the whole app: a jukebox landing screen with 12 stories on one 3D globe, with sound.
(The file name is kept from the first story, C4 "The Planet Breathing".)

## Start it

```bash
open -a Safari playground/breathing.html          # or Chrome; works from file://
open "playground/breathing.html#e1_canada_smoke"  # open one story directly (sound starts on the first tap)
```

## What loads when

| File | Size | When |
|---|---|---|
| `breathing.html` | ~1.8 MB | first load (page + land mask + Blue Marble backdrop) |
| `stories/<id>.js` | 0.1 to 4.6 MB | when a story is picked (`<script>` tag, works from file://) |
| `audio/drums.js`, `audio/synth-layers.js`, `audio/engine-config.js` | ~9 MB | on the first tap that starts sound |
| three.js 0.160 | ~0.6 MB | CDN (jsdelivr) |

`stories/breathing.js` and `stories/wuhan.js` and the `audio/` bundles are written by `playground/c4-src/build.py`;
the other story files are written by `data-pipeline/<id>.py` (format: `data-pipeline/STORY_FORMAT.md`).

## Controls

Tap a card (or keys `1`…`0`, `-`, `=`). `Space` play/pause, `←`/`→` step, `Home` restart, `M` mute, `Shift+1…6` layers,
`R` rotate, `D` pixel ground, `I` sources panel, `J` jukebox, `Esc` close. Drag the globe, drag the chart to scrub, click a lane name to switch a layer.

URL options: `?reduced` forces reduced motion, `?perf` logs a frame-time report to the console after 5 s (`window.__perf`).

## Original story C4: data

| Source | What | Used for |
|---|---|---|
| NASA MODIS MOD13C2 v061 | Monthly NDVI (greenness), 0.05° grid, 2021 | Globe colours, 3D trees, greenness curve |
| NOAA GML Mauna Loa | Monthly CO₂ (ppm) | CO₂ curve, haze, readouts |

Derived by our scripts: area-weighted greenness per latitude band, 0.5° tree cells, CO₂ seasonal swing (value minus NOAA's deseasonalized value), correlation and lag.
Limits: one year (12 points), one CO₂ station, greenness includes farmland, no data over Antarctica and ice sheets. Tree height and haze are exaggerated.

## Files

| Path | What |
|---|---|
| `playground/breathing.html` | Built page (open this) |
| `playground/c4-src/template.html` | Page source |
| `playground/c4-src/build.py` | Inlines `data/c4` into the template and writes `breathing.html` |
| `data/c4/` | Processed data (textures, tree cells, series.json), ~4 MB |
| `data-pipeline/c4_breathing.py` | Raw NASA/NOAA files to textures, grids, series and correlations |
| `data-pipeline/c4_trees.py` | Raw NDVI to 0.5° tree cells |

## Rebuild the page only (after editing the template)

```bash
python3 playground/c4-src/build.py
```

## Rebuild the data from scratch

Only needed to change year or processing. Raw download is ~1.2 GB.

1. Get a free Earthdata account (https://urs.earthdata.nasa.gov), then Profile → Generate Token. Save the token to a file outside the repo, e.g. `~/.earthdata_token`. Never commit it.
2. Download the 12 monthly MOD13C2 files for the year into a raw folder outside the repo (file URLs from the CMR search: `https://cmr.earthdata.nasa.gov/search/granules.json?short_name=MOD13C2&version=061&temporal=2021-01-01,2021-12-31&page_size=50`):
   ```bash
   curl -L -H "Authorization: Bearer $(cat ~/.earthdata_token)" -O <granule url>
   ```
3. Download Mauna Loa CO₂ into the same folder:
   ```bash
   curl -O https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv
   ```
4. Python env (3.12) with `numpy pyhdf netCDF4 pillow`, then:
   ```bash
   python data-pipeline/c4_breathing.py <raw_dir> data/c4
   python data-pipeline/c4_trees.py <raw_dir> data/c4/trees_0p5deg_2021.bin
   python3 playground/c4-src/build.py
   ```

Optional: OCO-2 GEOS L3 monthly CO₂ maps (`oco2_GEOS_L3CO2_month_2021*.nc4`, GES DISC) in the raw folder add regional CO₂ to `series.json`. Requires approving the GES DISC app in your Earthdata profile.

## AI use

Code and data processing written with Claude Code (Anthropic).
