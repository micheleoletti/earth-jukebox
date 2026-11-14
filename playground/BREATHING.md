# The Planet Breathing (story C4)

A 3D globe showing how northern forests "breathe" carbon dioxide over one year (2021).
Tree height = how green each place is that month. The atmosphere haze and amber specks follow CO₂ in the air.
No sound yet.

## Start it

The page is a single self-contained file. All data is inlined; only three.js is loaded from a CDN, so you need internet.

```bash
open -a Safari playground/breathing.html
```

Any browser works. If one refuses to open it from disk, serve the folder instead:

```bash
python3 -m http.server 8765 --directory playground
```

then open http://localhost:8765/breathing.html

## Controls

- Drag to rotate, scroll to zoom.
- Drag on the chart to scrub through the months.
- Play / pause button or Space.

## Data

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
