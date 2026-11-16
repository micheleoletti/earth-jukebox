"""Fetch GEOS-CF surface NO2 over East China for the Wuhan lockdown story.

NASA GEOS-CF v1 assimilation, hourly, 0.25 deg, public OPeNDAP (no login).
We take 4 samples per day (00:30, 06:30, 12:30, 18:30 UTC) for:
  2019-12-01 .. 2020-04-30  (lockdown winter)
  2018-12-01 .. 2019-04-30  (baseline, same dates one year earlier)
Region: 22-42N, 105-125E (Wuhan, Beijing, Shanghai, Pearl River edge).

Output: one .npy per week chunk, float32 [samples][81][81] mol/mol, in <out_dir>.
Usage: python wuhan_fetch.py <out_dir>   (needs TMPDIR/HOME writable for the DAP cookie file)
"""
import datetime as dt
import os
import sys
import time

import numpy as np

URL = "https://opendap.nccs.nasa.gov/dods/gmao/geos-cf/assim/chm_tavg_1hr_g1440x721_v1"
T0 = dt.datetime(2018, 1, 1)  # index 0 = 2018-01-01 00:30 UTC
LA = slice(448, 529)  # 22N .. 42N
LO = slice(1140, 1221)  # 105E .. 125E
PERIODS = [(dt.date(2019, 12, 1), dt.date(2020, 4, 30)), (dt.date(2018, 12, 1), dt.date(2019, 4, 30))]


def chunks():
    for a, b in PERIODS:
        d = a
        while d <= b:
            n = min(7, (b - d).days + 1)
            yield d, n
            d += dt.timedelta(days=n)


def fetch(job):
    d, n, out = job
    f = os.path.join(out, f"no2_{d.isoformat()}_{n}d.npy")
    if os.path.exists(f):
        return f, "cached"
    import netCDF4

    t = int((dt.datetime(d.year, d.month, d.day) - T0).total_seconds() // 3600)
    for attempt in range(5):
        try:
            ds = netCDF4.Dataset(URL)
            x = np.asarray(ds["no2"][t : t + 24 * n : 6, 0, LA, LO], dtype=np.float32)
            ds.close()
            assert x.shape == (4 * n, 81, 81), x.shape
            np.save(f, x)
            return f, "ok"
        except Exception as e:  # server often answers 504; back off and retry
            time.sleep(5 + 10 * attempt)
            err = e
    return f, f"FAILED {err}"


if __name__ == "__main__":
    # python wuhan_fetch.py <out_dir>            -> list chunks ("YYYY-MM-DD N" per line)
    # python wuhan_fetch.py <out_dir> DATE N     -> fetch one chunk (run several in parallel, e.g. xargs -P 4)
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    if len(sys.argv) == 4:
        f, status = fetch((dt.date.fromisoformat(sys.argv[2]), int(sys.argv[3]), out))
        print(status, os.path.basename(f), flush=True)
    else:
        for d, n in chunks():
            print(d.isoformat(), n)
