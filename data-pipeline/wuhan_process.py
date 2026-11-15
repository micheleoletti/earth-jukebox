"""GEOS-CF NO2 chunks (from wuhan_fetch.py) -> slim files for the Wuhan lockdown story.

Outputs in <out_dir>:
  no2_daily_2020.bin  uint8 [152 days][81 lat][81 lon], 2019-12-01..2020-04-30, 5-day smoothed,
                      value = sqrt(min(ppb, 80) / 80) * 255   (lat row 0 = 22N, lon col 0 = 105E, 0.25 deg)
  series.json         daily Wuhan + region means for 2019/20 and the same dates one year earlier, key dates, stats

Usage: python wuhan_process.py <chunk_dir> <out_dir>
"""
import datetime as dt
import glob
import json
import os
import sys

import numpy as np

LAT0, LON0, STEP, N = 22.0, 105.0, 0.25, 81
CITIES = {"Wuhan": (30.59, 114.31), "Beijing": (39.90, 116.41), "Shanghai": (31.23, 121.47), "Chongqing": (29.56, 106.55),
          "Nanjing": (32.06, 118.80), "Zhengzhou": (34.75, 113.63)}
EVENTS = [("2020-01-23", "Wuhan locked down"), ("2020-01-25", "Lunar New Year"), ("2020-04-08", "Lockdown lifted")]
LOCK = ("2020-01-23", "2020-04-08")


def load(chunk_dir, start, end):
    days = []
    for f in sorted(glob.glob(os.path.join(chunk_dir, "no2_*.npy"))):
        d0 = dt.date.fromisoformat(os.path.basename(f)[4:14])
        if start <= d0 <= end:
            x = np.load(f)  # [4*n][81][81] mol/mol
            n = x.shape[0] // 4
            days.extend([(d0 + dt.timedelta(days=i), x[4 * i : 4 * i + 4].mean(0) * 1e9) for i in range(n)])
    days.sort(key=lambda t: t[0])
    return [d for d, _ in days], np.array([g for _, g in days], dtype=np.float32)  # ppb


def smooth(a, k):
    pad = np.concatenate([np.repeat(a[:1], k // 2, 0), a, np.repeat(a[-1:], k // 2, 0)])
    c = np.cumsum(np.concatenate([np.zeros_like(a[:1]), pad]), 0)
    return (c[k:] - c[:-k]) / k


def cell(lat, lon):
    return int(round((lat - LAT0) / STEP)), int(round((lon - LON0) / STEP))


def box_mean(g, lat, lon, r=1):
    i, j = cell(lat, lon)
    return g[:, i - r : i + r + 1, j - r : j + r + 1].mean(axis=(1, 2))


def main(chunk_dir, out):
    os.makedirs(out, exist_ok=True)
    d20, g20 = load(chunk_dir, dt.date(2019, 12, 1), dt.date(2020, 4, 30))
    d19, g19 = load(chunk_dir, dt.date(2018, 12, 1), dt.date(2019, 4, 30))
    assert len(d20) == 152 and len(d19) == 151, (len(d20), len(d19))
    # align baseline by calendar date (Feb 29 2020 -> Feb 28 2019)
    idx19 = {d: k for k, d in enumerate(d19)}
    def prev_year(d):
        try:
            return d.replace(year=d.year - 1)
        except ValueError:
            return d.replace(year=d.year - 1, day=28)
    g19a = g19[[idx19[prev_year(d)] for d in d20]]

    q = np.round(np.sqrt(np.clip(smooth(g20, 5), 0, 80) / 80) * 255).astype(np.uint8)
    q.tofile(os.path.join(out, "no2_daily_2020.bin"))

    def series(g):
        return {name: [round(float(v), 2) for v in box_mean(g, *ll)] for name, ll in CITIES.items()}
    s20, s19 = series(g20), series(g19a)
    reg20 = [round(float(v), 2) for v in g20.mean(axis=(1, 2))]
    reg19 = [round(float(v), 2) for v in g19a.mean(axis=(1, 2))]
    dates = [d.isoformat() for d in d20]
    lk = [k for k, d in enumerate(dates) if LOCK[0] <= d <= LOCK[1]]
    pre = [k for k, d in enumerate(dates) if d < LOCK[0]]
    stats = {}
    for name in CITIES:
        a20, a19 = np.array(s20[name]), np.array(s19[name])
        stats[name] = {
            "lockdown_2020_ppb": round(float(a20[lk].mean()), 2), "same_dates_2019_ppb": round(float(a19[lk].mean()), 2),
            "lockdown_change_pct": round(float((a20[lk].mean() / a19[lk].mean() - 1) * 100), 1),
            "before_change_pct": round(float((a20[pre].mean() / a19[pre].mean() - 1) * 100), 1),
        }
    meta = {"lat0": LAT0, "lon0": LON0, "step": STEP, "n": N, "days": len(dates), "encoding": "sqrt(min(ppb,80)/80)*255",
            "cities": CITIES, "events": EVENTS, "lockdown": LOCK, "dates": dates,
            "no2_2020": s20, "no2_2019_same_dates": s19, "region_2020": reg20, "region_2019_same_dates": reg19, "stats": stats,
            "source": "NASA GEOS-CF v1 assimilation, surface NO2, 0.25 deg, 4 samples/day (00:30, 06:30, 12:30, 18:30 UTC)"}
    json.dump(meta, open(os.path.join(out, "series.json"), "w"))
    print(json.dumps(stats, indent=1))
    print("bin", os.path.getsize(os.path.join(out, "no2_daily_2020.bin")) / 1e6, "MB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
