"""Wuhan lockdown vs a NORMAL YEAR built from 2015-2019, aligned on Lunar New Year (OMI satellite NO2).

Why: one baseline year is noisy (its own weather/clouds), and calendar alignment mixes the Lunar New Year
holiday dip (which moves by weeks every year) into the lockdown signal. Studies of the 2020 lockdown compare
against several years aligned on the holiday; this does the same.

Method (no invented values):
- Day axis = days relative to Lunar New Year (LNY). 2020 window: LNY-55 .. LNY+96 = 2019-12-01 .. 2020-04-30.
- For each year and day: pool every valid clear-sky pixel observation in a 5x5 cell box (~125 km) around the city
  within +/-7 days, and take their mean. Fewer than MIN_OBS pixel observations -> no value (gap stays a gap).
- Normal year = mean over 2015-2019 of the yearly values available that day (needs >= 3 years); band = min..max.
- Change = 2020 / normal - 1, only where both exist.

Input: omi_YYYY-MM-DD.npy tiles (80x80, 22.125N..41.875N, 105.125E..124.875E) from wuhan_omi.py.
Output: adds a "baseline" block to <out_dir>/series.json (written by wuhan_process_omi.py).

Usage: python wuhan_baseline.py <omi_dir> <out_dir>
"""
import datetime as dt
import json
import os
import sys

import numpy as np

LAT0, LON0, STEP = 22.125, 105.125, 0.25
LNY = {2015: "2015-02-19", 2016: "2016-02-08", 2017: "2017-01-28", 2018: "2018-02-16", 2019: "2019-02-05", 2020: "2020-01-25"}
REL = range(-55, 97)  # 152 days, 2020: Dec 1 .. Apr 30
HALF, R_BOX, MIN_OBS, MIN_YEARS = 7, 2, 5, 3


def tile(src, d):
    f = os.path.join(src, f"omi_{d.isoformat()}.npy")
    return np.load(f) if os.path.exists(f) else None


def city_series(src, year, lat, lon):
    i, j = int(round((lat - LAT0) / STEP)), int(round((lon - LON0) / STEP))
    lny = dt.date.fromisoformat(LNY[year])
    # cache the city box for each day of the year's window (+ margins)
    box = {}
    for r in range(REL.start - HALF, REL.stop + HALF):
        t = tile(src, lny + dt.timedelta(r))
        box[r] = None if t is None else t[i - R_BOX : i + R_BOX + 1, j - R_BOX : j + R_BOX + 1].ravel()
    out, nobs = [], []
    for r in REL:
        vals = np.concatenate([b for k in range(r - HALF, r + HALF + 1) if (b := box.get(k)) is not None] or [np.array([])])
        vals = vals[~np.isnan(vals)]
        nobs.append(int(vals.size))
        out.append(round(float(vals.mean() / 1e15), 2) if vals.size >= MIN_OBS else None)
    return out, nobs


def main(src, out):
    meta_f = os.path.join(out, "series.json")
    meta = json.load(open(meta_f))
    base = {"method": "normal = mean of 2015-2019 aligned on Lunar New Year; band = min..max of those years; "
                      f"pixels pooled in a {2 * R_BOX + 1}x{2 * R_BOX + 1} box over +/-{HALF} days, >= {MIN_OBS} clear-sky obs",
            "years": list(range(2015, 2020)), "lny": LNY, "rel_days": list(REL), "unit": "1e15 molecules/cm2", "cities": {}}
    lk0 = (dt.date(2020, 1, 23) - dt.date.fromisoformat(LNY[2020])).days
    lk1 = (dt.date(2020, 4, 8) - dt.date.fromisoformat(LNY[2020])).days
    for name, (lat, lon) in meta["cities"].items():
        y20, n20 = city_series(src, 2020, lat, lon)
        years = {y: city_series(src, y, lat, lon)[0] for y in range(2015, 2020)}
        normal, lo, hi, pct = [], [], [], []
        for k in range(len(REL)):
            v = [years[y][k] for y in years if years[y][k] is not None]
            ok = len(v) >= MIN_YEARS
            normal.append(round(float(np.mean(v)), 2) if ok else None)
            lo.append(round(float(min(v)), 2) if ok else None)
            hi.append(round(float(max(v)), 2) if ok else None)
            pct.append(round((y20[k] / normal[-1] - 1) * 100, 1) if ok and y20[k] is not None else None)
        def period(a, b):
            idx = [k for k, r in enumerate(REL) if a <= r <= b and y20[k] is not None and normal[k] is not None]
            if not idx:
                return None
            return round((np.mean([y20[k] for k in idx]) / np.mean([normal[k] for k in idx]) - 1) * 100, 1)
        base["cities"][name] = {"y2020": y20, "obs_2020": n20, "normal": normal, "lo": lo, "hi": hi, "pct": pct,
                                "per_year": years,
                                "lockdown_vs_normal_pct": period(lk0, lk1),
                                "before_vs_normal_pct": period(-55, -15),   # weeks before the holiday and lockdown
                                "gap_days_2020": sum(v is None for v in y20)}
    meta["baseline"] = base
    json.dump(meta, open(meta_f, "w"))
    for n, c in base["cities"].items():
        print(f"{n:10s} lockdown vs normal {c['lockdown_vs_normal_pct']}%  before {c['before_vs_normal_pct']}%  gaps2020 {c['gap_days_2020']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
