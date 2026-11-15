"""Shared helpers for the fire / smoke stories (e1_canada_smoke, e4_black_summer, c4_africa_fire).

- geoscf(): GEOS-CF (NASA GMAO Composition Forecast, assimilation run, a model) subsets over public OPeNDAP, cached as .npy
- openaq_hourly(): OpenAQ hourly station values from the public S3 archive (no auth), cached per day
- firms(): FIRMS VIIRS SNPP country CSVs (standard/science product), reduced to numpy arrays and cached
- link_dir(): storylib.link restricted to lags where the partner leads (or follows) the hero
"""
import csv
import datetime as dt
import gzip
import os
import subprocess
import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402

GEOSCF = "https://opendap.nccs.nasa.gov/dods/gmao/geos-cf/assim/"
GEOSCF_T0 = dt.datetime(2018, 1, 1)  # hour index 0 = 2018-01-01 00:00-01:00 UTC (time stamp 00:30)
OPENAQ = "https://openaq-data-archive.s3.amazonaws.com/records/csv.gz/locationid={i}/year={y}/month={m:02d}/location-{i}-{d}.csv.gz"
FIRMS = "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/{y}/viirs-snpp_{y}_{c}.csv"


# ---------------------------------------------------------------- GEOS-CF (model)
def _dods_get(url, shape, tries=5):
    """One DAP2 binary (.dods) request for a single Grid/array variable -> float32 array of `shape`."""
    for k in range(tries):
        r = subprocess.run(["curl", "-sgf", "--max-time", "600", url], capture_output=True)
        raw = r.stdout
        i = raw.find(b"\nData:\n")
        if r.returncode == 0 and i > 0:
            raw = raw[i + 7:]
            n = int(np.frombuffer(raw[:4], ">u4")[0])
            if n == int(np.prod(shape)):
                return np.frombuffer(raw[8:8 + 4 * n], ">f4").reshape(shape).astype(np.float32)
        print("  retry dods", k, r.returncode, flush=True)
    raise RuntimeError("DAP request failed: " + url[:160])


def geoscf(story_id, coll, var, start, nhours, stride, lat0, lat1, lon0, lon1, lev=0, chunk=8, workers=6):
    """Hourly GEOS-CF field at 0.25 deg, every `stride` hours from `start` (datetime, hour start), nhours long.
    Returns (frames, lats, lons) with NaN for fill. Rows south->north. Cached in the story cache dir.
    Uses raw DAP2 requests (the GrADS server costs ~1.5 s per time step, so chunks run in parallel)."""
    from concurrent.futures import ThreadPoolExecutor
    i0 = int((start - GEOSCF_T0).total_seconds() // 3600)
    a, b = int(round((lat0 + 90) * 4)), int(round((lat1 + 90) * 4))
    c, d = int(round((lon0 + 180) * 4)), int(round((lon1 + 180) * 4))
    key = f"geoscf_{coll}_{var}_{lev}_{i0}_{nhours}_{stride}_{a}_{b}_{c}_{d}.npy"
    out = SL.cache_dir(story_id) / key
    lats = -90 + np.arange(a, b + 1) * .25
    lons = -180 + np.arange(c, d + 1) * .25
    if out.exists():
        return np.load(out), lats, lons
    idx = list(range(i0, i0 + nhours, stride))
    chunks = [idx[k:k + chunk] for k in range(0, len(idx), chunk)]
    tmpd = SL.cache_dir(story_id) / ("tmp_" + key[:-4])
    tmpd.mkdir(exist_ok=True)

    def get(sub):
        f = tmpd / f"{sub[0]}.npy"
        if f.exists():
            return np.load(f)
        lev_s = f"[{lev}]" if lev is not None else ""
        url = (f"{GEOSCF}{coll}.dods?{var}[{sub[0]}:{stride}:{sub[-1]}]{lev_s}[{a}:{b}][{c}:{d}]")
        x = _dods_get(url, (len(sub), b - a + 1, d - c + 1))
        np.save(f, x)
        return x

    done = 0
    parts = []
    with ThreadPoolExecutor(workers) as ex:
        for x in ex.map(get, chunks):
            parts.append(x)
            done += len(x)
            if done % (chunk * 10) == 0:
                print(f"  geoscf {var} {done}/{len(idx)}", flush=True)
    arr = np.concatenate(parts)
    arr[arr > 1e14] = np.nan
    np.save(out, arr)
    for f in tmpd.glob("*.npy"):
        f.unlink()
    tmpd.rmdir()
    return arr, lats, lons


def block_mean(arr, f):
    """Average f x f blocks of the last two axes (NaN-aware); trims edges that do not fill a block."""
    nt, ny, nx = arr.shape
    ny2, nx2 = ny // f, nx // f
    x = arr[:, :ny2 * f, :nx2 * f].reshape(nt, ny2, f, nx2, f)
    with np.errstate(invalid="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return np.nanmean(x, axis=(2, 4))


def block_centres(c, f):
    n = len(c) // f
    return np.asarray(c[:n * f]).reshape(n, f).mean(1)


# ---------------------------------------------------------------- OpenAQ (observed)
def _openaq_day(story_id, loc, day):
    d = day.strftime("%Y%m%d")
    out = SL.cache_dir(story_id) / "openaq" / f"{loc}_{d}.csv.gz"
    miss = out.with_suffix(".missing")
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        return out
    if miss.exists():
        return None
    url = OPENAQ.format(i=loc, y=day.year, m=day.month, d=d)
    for k in range(3):
        r = subprocess.run(["curl", "-s", "-w", "%{http_code}", "--max-time", "60", "-o", str(out) + ".part", url],
                           capture_output=True, text=True)
        code = r.stdout.strip()
        if code == "200":
            os.replace(str(out) + ".part", out)
            return out
        if code in ("403", "404"):
            miss.touch()
            if os.path.exists(str(out) + ".part"):
                os.remove(str(out) + ".part")
            return None
    return None


def openaq_hourly(story_id, loc, days, param="pm25", lo=-5.0, hi=1000.0):
    """{utc hour datetime: value} for one OpenAQ location over the given dates (local-day files; we also read
    the day after to catch UTC spill). Multiple sensors in one hour are averaged. Values outside [lo, hi] dropped."""
    from concurrent.futures import ThreadPoolExecutor
    days = sorted(set(days) | {d + dt.timedelta(1) for d in days} | {d - dt.timedelta(1) for d in days})
    with ThreadPoolExecutor(16) as ex:
        files = list(ex.map(lambda d: _openaq_day(story_id, loc, d), days))
    acc = {}
    meta = None
    for f in files:
        if f is None:
            continue
        try:
            lines = gzip.decompress(f.read_bytes()).decode().splitlines()
        except Exception:
            continue
        for row in csv.reader(lines[1:]):
            if len(row) < 9 or row[6] != param:
                continue
            try:
                v = float(row[8])
                t = dt.datetime.fromisoformat(row[3]).astimezone(dt.timezone.utc).replace(tzinfo=None)
            except ValueError:
                continue
            if meta is None:
                meta = {"name": row[2], "lat": float(row[4]), "lon": float(row[5])}
            if not (lo <= v <= hi):
                continue
            acc.setdefault(t, []).append(v)
    return {t: float(np.mean(v)) for t, v in acc.items()}, meta


# ---------------------------------------------------------------- FIRMS (observed)
def firms(story_id, year, country):
    """VIIRS SNPP active fires for one country-year: dict of numpy arrays lat, lon, frp, time (UTC datetime64[m]),
    conf (l/n/h), daynight, type. Cached as .npz next to the CSV."""
    name = f"viirs-snpp_{year}_{country}.csv"
    npz = SL.cache_dir(story_id) / (name + ".npz")
    if npz.exists():
        z = np.load(npz, allow_pickle=False)
        return {k: z[k] for k in z.files}
    p = SL.fetch(FIRMS.format(y=year, c=country), story_id, name=name, min_bytes=1000)
    import pandas as pd
    df = pd.read_csv(p, usecols=["latitude", "longitude", "acq_date", "acq_time", "frp", "confidence", "daynight", "type"],
                     dtype={"acq_time": str})
    t = pd.to_datetime(df.acq_date + " " + df.acq_time.str.zfill(4), format="%Y-%m-%d %H%M").values.astype("datetime64[m]")
    d = {"lat": df.latitude.values.astype(np.float32), "lon": df.longitude.values.astype(np.float32),
         "frp": df.frp.values.astype(np.float32), "time": t, "conf": df.confidence.astype(str).values.astype("U1"),
         "daynight": df.daynight.astype(str).values.astype("U1"), "type": df["type"].values.astype(np.int8)}
    np.savez(npz, **d)
    return d


def even_subsample(order_key, nmax):
    """Indices of at most nmax items taken evenly along order_key (sorted), so the time distribution is kept."""
    idx = np.argsort(order_key, kind="stable")
    if len(idx) <= nmax:
        return idx
    take = np.round(np.linspace(0, len(idx) - 1, nmax)).astype(int)
    return idx[take]


# ---------------------------------------------------------------- link restricted to a direction
def link_dir(hero, partner, max_lag, step_label, method, partner_leads=True, min_n=8, sign=1):
    """storylib.link, but the best lag is chosen only among lags where the partner leads the hero
    (storylib sign convention: negative lag = partner leads) or follows it. Full curve kept."""
    lk = SL.link(hero, partner, max_lag, step_label, method, min_n=min_n, sign_hint=1)
    if lk.get("r") is None:
        return lk
    ok = [c for c in lk["curve"] if (c[0] <= 0 if partner_leads else c[0] >= 0)]
    k, r = max(ok, key=(lambda c: c[1] * sign) if sign else (lambda c: abs(c[1])))
    x, y = SL._pairs(hero, partner, k)
    lk.update({"r": round(r, 3), "lag": k, "n": int(len(x)), "sign": "positive" if r > 0 else "negative",
               "strength": "strong" if abs(r) >= .6 else "moderate" if abs(r) >= .3 else "weak",
               "lag_search": f"lags 0..{max_lag} {step_label}, partner {'leading' if partner_leads else 'following'} the hero only (negative lag = partner leads)"})
    return lk
