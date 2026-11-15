"""OMI daily NO2 tiles (from wuhan_omi.py) -> slim files for the Wuhan lockdown story.

OMI daily maps have gaps (clouds, instrument row anomaly), so every day is a 15-day centred composite
(mean of the valid observations, at least 3), then remaining holes are filled from nearby cells.

Outputs in <out_dir> (same layout the page already reads):
  no2_daily_2020.bin  uint8 [152 days][80 lat][80 lon], 2019-12-01..2020-04-30
                      0 = no clear-sky data; 1..255 = 1 + sqrt(min(u, 80) / 80) * 254, u = column / 5e14 molecules/cm2
                      (80 = 4e16). Only small holes (instrument row stripes, <= 1 degree) are filled from neighbours.
  series.json         Wuhan + city series (units of 1e15 molecules/cm2), same dates one year earlier, stats

Usage: python wuhan_process_omi.py <omi_dir> <out_dir>
"""
import datetime as dt
import glob
import json
import os
import sys

import numpy as np

LAT0, LON0, STEP, N = 22.125, 105.125, 0.25, 80
CITIES = {"Wuhan": (30.59, 114.31), "Beijing": (39.90, 116.41), "Shanghai": (31.23, 121.47), "Chongqing": (29.56, 106.55),
          "Nanjing": (32.06, 118.80), "Zhengzhou": (34.75, 113.63)}
LOCK = ("2020-01-23", "2020-04-08")
WIN = 15


def load(d0, d1, src):
    days, grids = [], []
    d = d0
    while d <= d1:
        f = os.path.join(src, f"omi_{d.isoformat()}.npy")
        grids.append(np.load(f) if os.path.exists(f) else np.full((N, N), np.nan, np.float32))
        days.append(d)
        d += dt.timedelta(days=1)
    return days, np.array(grids)


def composite(g, extra_before, extra_after):
    """15-day centred mean of valid obs (>=3); g includes `extra` days of margin on each side."""
    out = []
    for k in range(extra_before, len(g) - extra_after):
        w = g[k - WIN // 2 : k + WIN // 2 + 1]
        n = np.sum(~np.isnan(w), 0)
        with np.errstate(all="ignore"):
            m = np.nanmean(w, 0)
        m[n < 3] = np.nan
        out.append(m)
    return np.array(out)


def fill(a):
    """Close only small holes (<= 4 cells = 1 degree, e.g. OMI row-anomaly stripes); bigger gaps stay missing."""
    out = a.copy()
    for f in (2, 4):
        t, h, w = a.shape
        c = out[:, : h - h % f, : w - w % f].reshape(t, h // f, f, w // f, f)
        with np.errstate(all="ignore"):
            c = np.nanmean(c, axis=(2, 4))
        up = np.repeat(np.repeat(c, f, 1), f, 2)
        up = np.pad(up, ((0, 0), (0, h - up.shape[1]), (0, w - up.shape[2])), mode="edge")
        hole = np.isnan(out)
        out[hole] = up[hole]
    return out


def box(g, lat, lon, r=2):   # 5x5 cells (~125 km): enough valid pixels on cloudy winter days
    i, j = int(round((lat - LAT0) / STEP)), int(round((lon - LON0) / STEP))
    with np.errstate(all="ignore"):
        return np.nanmean(g[:, i - r : i + r + 1, j - r : j + r + 1], axis=(1, 2))


def main(src, out):
    os.makedirs(out, exist_ok=True)
    m = WIN // 2
    # load with margins so the composite exists at the window edges (missing margin days are just gaps)
    d20, g20 = load(dt.date(2019, 12, 1) - dt.timedelta(m), dt.date(2020, 4, 30) + dt.timedelta(m), src)
    d19, g19 = load(dt.date(2018, 12, 1) - dt.timedelta(m), dt.date(2019, 4, 30) + dt.timedelta(m), src)
    c20, c19 = composite(g20, m, m), composite(g19, m, m)
    dates20 = d20[m:-m]
    assert len(dates20) == 152 and len(c19) == 151, (len(dates20), len(c19))
    idx19 = {d: k for k, d in enumerate(d19[m:-m])}
    py = lambda d: d.replace(year=d.year - 1) if not (d.month == 2 and d.day == 29) else d.replace(year=d.year - 1, day=28)
    c19a = c19[[idx19[py(d)] for d in dates20]]

    u = fill(c20) / 5e14
    q = np.where(np.isnan(u), 0, 1 + np.round(np.sqrt(np.clip(np.nan_to_num(u), 0, 80) / 80) * 254)).astype(np.uint8)
    print("no-data cells after small-hole fill: %.1f%%" % (100 * np.isnan(u).mean()))
    q.tofile(os.path.join(out, "no2_daily_2020.bin"))

    E15 = 1e15
    ser = lambda g: {k: [None if np.isnan(v) else round(float(v / E15), 2) for v in box(g, *ll)] for k, ll in CITIES.items()}
    s20, s19 = ser(c20), ser(c19a)
    dates = [d.isoformat() for d in dates20]
    lk = [k for k, d in enumerate(dates) if LOCK[0] <= d <= LOCK[1]]
    pre = [k for k, d in enumerate(dates) if d < "2020-01-10"]
    stats = {}
    for k in CITIES:
        a, b = np.array(s20[k], float), np.array(s19[k], float)
        stats[k] = {"lockdown_2020": round(float(np.nanmean(a[lk])), 2), "same_dates_2019": round(float(np.nanmean(b[lk])), 2),
                    "lockdown_change_pct": round(float((np.nanmean(a[lk]) / np.nanmean(b[lk]) - 1) * 100), 1),
                    "before_change_pct": round(float((np.nanmean(a[pre]) / np.nanmean(b[pre]) - 1) * 100), 1)}
    meta = {"lat0": LAT0, "lon0": LON0, "step": STEP, "n": N, "days": len(dates), "unit": "1e15 molecules/cm2",
            "encoding": "0 = no data; 1 + sqrt(min(col/5e14, 80)/80)*254", "cities": CITIES, "lockdown": LOCK, "dates": dates,
            "no2_2020": s20, "no2_2019_same_dates": s19, "stats": stats,
            "source": "NASA OMI/Aura OMNO2d v003, tropospheric NO2 column (cloud-screened), 0.25 deg, 15-day composites"}
    json.dump(meta, open(os.path.join(out, "series.json"), "w"))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
