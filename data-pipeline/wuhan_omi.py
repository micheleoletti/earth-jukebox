"""Fetch NASA OMI satellite NO2 (OMNO2d v003, daily L3, 0.25 deg) for the Wuhan lockdown story.

Observed tropospheric NO2 column (cloud-screened), not a model, so it shows the real lockdown drop.
Periods: each winter 2015..2020, from 62 days before to 100 days after Lunar New Year (so every year can be
aligned on the holiday). Region: 22-42N, 105-125E.
Each 11 MB daily file is downloaded, the region is cut out and saved (.npy, ~25 KB), the file is deleted.

Usage: python wuhan_omi.py <token_file> <out_dir>      (Earthdata bearer token; GES DISC app approved)
"""
import datetime as dt
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

# Lunar New Year (Spring Festival) dates
LNY = {2015: "2015-02-19", 2016: "2016-02-08", 2017: "2017-01-28", 2018: "2018-02-16", 2019: "2019-02-05", 2020: "2020-01-25"}
PERIODS = [((dt.date.fromisoformat(d) - dt.timedelta(62)).isoformat(), (dt.date.fromisoformat(d) + dt.timedelta(100)).isoformat())
           for d in LNY.values()]
# OMNO2d grid: 720 x 1440, cell centres -89.875 .. 89.875, -179.875 .. 179.875
LA = slice(int((22 + 90) / .25), int((42 + 90) / .25))     # 80 rows: 22.125N .. 41.875N
LO = slice(int((105 + 180) / .25), int((125 + 180) / .25))  # 80 cols: 105.125E .. 124.875E
VAR = "HDFEOS/GRIDS/ColumnAmountNO2/Data Fields/ColumnAmountNO2TropCloudScreened"


def granules(a, b):
    q = f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name=OMNO2d&version=003&temporal={a},{b}T23:59:59Z&page_size=200&sort_key=start_date"
    out = []
    raw = subprocess.run(["curl", "-sf", "--retry", "5", q], capture_output=True, check=True).stdout  # curl: robust to proxies
    for e in json.loads(raw)["feed"]["entry"]:
        url = next(l["href"] for l in e["links"] if l["href"].startswith("https://data.gesdisc") and l["href"].endswith(".he5"))
        out.append((e["time_start"][:10], url))
    return out


def fetch(job):
    day, url, token, out = job
    npy = os.path.join(out, f"omi_{day}.npy")
    if os.path.exists(npy):
        return day, "cached"
    tmp = os.path.join(out, f"tmp_{day}.he5")
    for _ in range(4):
        r = subprocess.run(["curl", "-sfL", "-H", f"Authorization: Bearer {token}", "-o", tmp, url])
        if r.returncode == 0 and os.path.getsize(tmp) > 1e6:
            break
    else:
        return day, "FAILED download"
    return day, tmp


def main(token_file, out):
    os.makedirs(out, exist_ok=True)
    token = open(token_file).read().strip()
    jobs = [(d, u, token, out) for a, b in PERIODS for d, u in granules(a, b)]
    print(len(jobs), "days", flush=True)
    import netCDF4  # read in the main thread only (netCDF/HDF5 are not thread safe)

    with ThreadPoolExecutor(6) as ex:
        for day, res in ex.map(fetch, jobs):
            if not res.endswith(".he5"):
                print(day, res, flush=True)
                continue
            ds = netCDF4.Dataset(res)
            x = ds[VAR][LA, LO]
            ds.close()
            np.save(os.path.join(out, f"omi_{day}.npy"), np.ma.filled(x.astype(np.float32), np.nan))
            os.remove(res)
            print(day, "ok", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
