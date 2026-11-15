"""C4 "planet breathing": raw NASA files -> slim artifacts for the prototype.

Inputs (raw dir, not in repo):
  MOD13C2.A2021*.hdf            MODIS monthly NDVI, 0.05 deg (LP DAAC)
  oco2_GEOS_L3CO2_month_2021*.nc4  OCO-2 GEOS L3 monthly XCO2, 0.5x0.625 deg (GES DISC), optional
  co2_mm_mlo.csv                NOAA Mauna Loa monthly CO2

Outputs (repo, small):
  ndvi_2deg_2021.bin   uint8 [12][90][180], 0 = no data, 1..255 = NDVI -0.2..1.0 (row 0 = 89N band)
  xco2_2deg_2021.bin   uint16 [12][90][180], ppm*100 (only if OCO-2 files present)
  textures/ndvi_2021_MM.png  1024x512 equirectangular colour textures for the globe
  series.json          band means per month, Mauna Loa record, correlations + lags

Usage: python c4_breathing.py <raw_dir> <out_dir>
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

YEAR = 2021
BANDS = {  # name: (lat_min, lat_max)
    "boreal_50_70N": (50, 70),
    "temperate_30_50N": (30, 50),
    "subtropics_10_30N": (10, 30),
    "tropics_10S_10N": (-10, 10),
    "south_10_40S": (-40, -10),
}


def month_of_doy(doy):
    return int(np.searchsorted(np.cumsum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]), doy, side="left"))


def load_ndvi(raw):
    from pyhdf.SD import SD, SDC

    out = np.full((12, 3600, 7200), np.nan, dtype=np.float32)
    for f in sorted(glob.glob(os.path.join(raw, f"MOD13C2.A{YEAR}*.hdf"))):
        doy = int(os.path.basename(f)[13:16])
        m = month_of_doy(doy)
        sds = SD(f, SDC.READ).select("CMG 0.05 Deg Monthly NDVI")
        a = sds.get().astype(np.float32)
        a[a <= -2000] = np.nan  # fill -3000 (water / no data)
        out[m] = a / 10000.0
        print("ndvi", YEAR, m + 1, os.path.basename(f))
    return out  # [12][3600][7200], row 0 = 90N


def coarsen(a, fy, fx):
    t, h, w = a.shape
    a = a[:, : h - h % fy, : w - w % fx].reshape(t, h // fy, fy, w // fx, fx)
    with np.errstate(all="ignore"):
        return np.nanmean(a, axis=(2, 4))


def lat_weights(nlat):
    lat = 90 - (np.arange(nlat) + 0.5) * 180 / nlat
    return lat, np.cos(np.deg2rad(lat))


def band_means(grid):  # grid [12][nlat][nlon], row 0 = north
    lat, w = lat_weights(grid.shape[1])
    res = {}
    for name, (lo, hi) in BANDS.items():
        sel = (lat >= lo) & (lat < hi)
        g = grid[:, sel, :]
        ww = np.broadcast_to(w[sel][None, :, None], g.shape)
        ok = ~np.isnan(g)
        res[name] = [round(float((g[i][ok[i]] * ww[i][ok[i]]).sum() / ww[i][ok[i]].sum()), 4) for i in range(12)]
    return res


def ndvi_colour(v):  # v in -0.2..1 -> brown/beige -> green
    stops = np.array([[-0.2, 60, 45, 30], [0.1, 170, 150, 110], [0.3, 190, 190, 90], [0.5, 90, 160, 60], [0.8, 20, 100, 30], [1.0, 5, 60, 15]])
    rgb = np.stack([np.interp(v, stops[:, 0], stops[:, k]) for k in (1, 2, 3)], -1)
    return rgb


def fill_water(v):
    """Replace NaN (water) with nearby land values so colour doesn't bleed blue at coasts."""
    out = v.copy()
    for f in (8, 32, 128):
        h, w = v.shape
        c = coarsen(v[None, : h - h % f, : w - w % f], f, f)[0]
        up = np.repeat(np.repeat(c, f, 0), f, 1)
        up = np.pad(up, ((0, h - up.shape[0]), (0, w - up.shape[1])), mode="edge")
        hole = np.isnan(out)
        out[hole] = up[hole]
    out[np.isnan(out)] = 0.0
    return out


def write_textures(ndvi, out, size=(2048, 1024)):
    """Monthly colour textures (water filled) + one full-res land mask for crisp coastlines."""
    d = os.path.join(out, "textures")
    os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(d, "ndvi_*.png")):
        os.remove(f)
    land = np.any(~np.isnan(ndvi), axis=0)
    # 4096 wide: the safe max texture size on all devices; resampling keeps soft (anti-aliased) coast edges
    Image.fromarray((land * 255).astype(np.uint8)).resize((4096, 2048), Image.LANCZOS).save(os.path.join(d, "landmask.png"), optimize=True)
    for m in range(12):
        rgb = ndvi_colour(fill_water(ndvi[m])).astype(np.uint8)
        Image.fromarray(rgb).resize(size, Image.LANCZOS).save(os.path.join(d, f"ndvi_{YEAR}_{m + 1:02d}.jpg"), quality=86)


def load_xco2(raw):
    import netCDF4

    files = sorted(glob.glob(os.path.join(raw, f"oco2_GEOS_L3CO2_month_{YEAR}*.nc4")))
    files = [f for f in files if os.path.getsize(f) > 100000]
    if len(files) != 12:
        print("xco2: found", len(files), "valid files, skipping OCO-2")
        return None
    arr = []
    for f in files:
        ds = netCDF4.Dataset(f)
        x = np.array(ds.variables["XCO2"][0], dtype=np.float64) * 1e6  # mol/mol -> ppm, [lat][lon], lat ascending
        lat = np.array(ds.variables["lat"][:])
        if lat[0] < lat[-1]:
            x = x[::-1]
        arr.append(x)
    x = np.array(arr)  # [12][361][576]
    # regrid to 2 deg by nearest-mean: 361 lats ~0.5deg, 576 lons 0.625deg
    nlat, nlon = 90, 180
    lat_src = np.linspace(90, -90, x.shape[1])
    lon_src = -180 + np.arange(x.shape[2]) * 0.625
    li = np.clip(((90 - lat_src) / 2).astype(int), 0, nlat - 1)
    lj = np.clip(((lon_src + 180) / 2).astype(int), 0, nlon - 1)
    out = np.zeros((12, nlat, nlon))
    cnt = np.zeros((nlat, nlon))
    for a in range(x.shape[1]):
        for b in range(x.shape[2]):
            out[:, li[a], lj[b]] += x[:, a, b]
            cnt[li[a], lj[b]] += 1
    return out / np.maximum(cnt, 1)


def mauna_loa(raw):
    rows = []
    for line in open(os.path.join(raw, "co2_mm_mlo.csv")):
        if line.startswith("#") or line.startswith("year"):
            continue
        p = line.strip().split(",")
        rows.append({"t": f"{int(p[0])}-{int(p[1]):02d}", "co2": float(p[3]), "deseason": float(p[4])})
    return rows


def lagged_r(a, b, max_lag=4):
    """r between a(t) and b(t+lag): does b follow a after `lag` months? Cyclic over the year."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    out = {}
    for lag in range(0, max_lag + 1):
        out[lag] = round(float(np.corrcoef(a, np.roll(b, -lag))[0, 1]), 3)
    best = max(out, key=lambda k: abs(out[k]))
    return {"by_lag": out, "best_lag": best, "best_r": out[best]}


def main(raw, out):
    os.makedirs(out, exist_ok=True)
    ndvi = load_ndvi(raw)
    write_textures(ndvi, out)
    ndvi2 = coarsen(ndvi, 40, 40)  # 2 deg
    q = np.where(np.isnan(ndvi2), 0, np.clip(np.round((ndvi2 + 0.2) / 1.2 * 254) + 1, 1, 255)).astype(np.uint8)
    q.tofile(os.path.join(out, f"ndvi_2deg_{YEAR}.bin"))
    del ndvi

    series = {"year": YEAR, "bands": BANDS, "ndvi": band_means(ndvi2)}
    mlo = mauna_loa(raw)
    series["mauna_loa"] = mlo
    mlo_year = [r["co2"] for r in mlo if r["t"].startswith(str(YEAR))]
    series["mauna_loa_year"] = mlo_year
    # seasonal part only (NOAA's own deseasonalized column removes the cycle; difference = the breath)
    mlo_season = [round(r["co2"] - r["deseason"], 3) for r in mlo if r["t"].startswith(str(YEAR))]
    series["mauna_loa_season_year"] = mlo_season

    corr = {}
    for name, v in series["ndvi"].items():
        corr[f"ndvi_{name}__vs__mauna_loa"] = lagged_r(v, mlo_season)

    x = load_xco2(raw)
    if x is not None:
        np.round(x * 100).astype(np.uint16).tofile(os.path.join(out, f"xco2_2deg_{YEAR}.bin"))
        series["xco2"] = band_means(x)
        for name in BANDS:
            corr[f"ndvi_{name}__vs__xco2_{name}"] = lagged_r(series["ndvi"][name], series["xco2"][name])
    series["correlations"] = corr
    json.dump(series, open(os.path.join(out, "series.json"), "w"), indent=1)
    print(json.dumps(corr, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
