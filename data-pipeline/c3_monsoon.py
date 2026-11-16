"""C3 India monsoon, 2019-01-01 .. 2019-12-31 (daily story, 365 steps).

Layers
  rain   NASA GPM IMERG Final Run daily v07 (GPM_3IMERGDF, GES DISC, observed satellite + gauge calibration), 0.1 deg
         averaged to 0.5 deg over 5-35N, 65-100E. Map frames: 8-day means. Lane: all-India land mean daily rain (mm/day),
         cos(latitude) weighted over 0.5 deg cells whose centre is inside India (Natural Earth 1:50m outline).
  wind   MERRA-2 tavg1_2d_slv_Nx (M2T1NXSLV, GMAO, model) hourly U850/V850 -> daily means, 2x2 blocks (1 x 1.25 deg).
         Map frames: 7-day means. Lane: daily mean u850 over the Arabian Sea box 10-20N, 65-72.5E (m/s, + = westerly).
  green  MODIS/Terra MOD13C2 v061 monthly NDVI (LP DAAC, 0.05 deg, observed) averaged to 0.5 deg. 12 frames at mid-month.
         Lane: India land mean NDVI, the monthly value held on every day of its month (not interpolated).
  water  GRACE/GRACE-FO JPL mascon RL06.3 v04 CRI (PO.DAAC, observed) land water equivalent thickness (cm), India mean.
         Real resolution about 3 deg (~300 km) mascons on a 0.5 deg grid; lane = monthly value held over its own days.
Link: rain vs NDVI, monthly means 2018-2020 (36 months), NDVI lagging rain by 0..3 months; rain vs GRACE water likewise.

Usage: python c3_monsoon.py
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402

ID = "c3_monsoon"
LOCK = threading.Lock()     # netCDF4 / HDF5 are not thread safe: parse one file at a time
CACHE = SL.cache_dir(ID)
D0 = dt.date(2019, 1, 1)
NT = 365
DAYS = [D0 + dt.timedelta(k) for k in range(NT)]
YEARS = [2018, 2019, 2020]
MN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

# common 0.5 deg grid: centres 5.25..34.75 N, 65.25..99.75 E
LATC = 5.25 + 0.5 * np.arange(60)
LONC = 65.25 + 0.5 * np.arange(70)
NG = (60, 70)


def cmr(short_name, a, b, version=None, host="https://opendap.earthdata.nasa.gov"):
    out, page = [], 1
    while True:
        q = (f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name={short_name}"
             + (f"&version={version}" if version else "") + f"&temporal={a},{b}&page_size=500&page_num={page}&sort_key=start_date")
        raw = subprocess.run(["curl", "-sf", "--retry", "5", q], capture_output=True, check=True).stdout
        ent = json.loads(raw)["feed"]["entry"]
        for e in ent:
            u = next((l["href"] for l in e["links"] if l["href"].startswith(host)), None)
            if u:
                out.append((e["time_start"][:10], u))
        if len(ent) < 500:
            return out
        page += 1


def walk_var(ds, suffix):
    found = None

    def w(g):
        nonlocal found
        for name, var in g.variables.items():
            if name.endswith(suffix):
                found = var
        for s in g.groups.values():
            w(s)
    w(ds)
    return found


# ---------------------------------------------------------------- India mask (Natural Earth 1:50m)
def india_mask():
    gj = SL.fetch("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
                  ID, name="ne50.geojson", min_bytes=100000)
    feat = next(f for f in json.loads(gj.read_text())["features"] if f["properties"]["ADMIN"] == "India")
    lon, lat = np.meshgrid(LONC, LATC)
    inside = np.zeros(NG, bool)
    for poly in feat["geometry"]["coordinates"]:
        ring = np.array(poly[0])           # outer ring (India polygons have no holes that matter at 0.5 deg)
        x, y = ring[:, 0], ring[:, 1]
        x2, y2 = np.roll(x, -1), np.roll(y, -1)
        c = np.zeros(NG, bool)
        for k in range(len(x)):
            cond = (y[k] > lat) != (y2[k] > lat)
            with np.errstate(all="ignore"):
                xi = x[k] + (lat - y[k]) * (x2[k] - x[k]) / (y2[k] - y[k])
            c ^= cond & (lon < xi)
        inside |= c
    return inside


MASK = None
W = np.cos(np.radians(LATC))[:, None] * np.ones(NG)


def india_mean(a):
    m = MASK & np.isfinite(a)
    if m.sum() < 0.8 * MASK.sum():
        return None
    return float((a[m] * W[m]).sum() / W[m].sum())


def block(a, f):
    h, w = a.shape
    with np.errstate(all="ignore"):
        return np.nanmean(a.reshape(h // f, f, w // f, f), axis=(1, 3))


# ---------------------------------------------------------------- IMERG daily
IM_DIR = CACHE / "imerg"


def imerg_one(job):
    day, url = job
    npy = IM_DIR / f"imerg_{day}.npy"
    if npy.exists():
        return day, True
    # lon index 2450..2799 = 65.05..99.95 E, lat index 950..1249 = 5.05..34.95 N (0.1 deg)
    ce = urllib.parse.quote("/precipitation[0][2450:2799][950:1249]", safe="")
    try:
        p = SL.fetch(f"{url}.dap.nc4?dap4.ce={ce}", ID, name=f"imerg/tmp_{day}.nc4", token=True, min_bytes=20000)
    except RuntimeError:
        return day, False
    with LOCK:
        import netCDF4
        ds = netCDF4.Dataset(p)
        v = walk_var(ds, "precipitation")
        a = np.ma.filled(np.ma.masked_invalid(v[0]).astype(np.float32), np.nan).T   # (lat, lon)
        ds.close()
        a[a < 0] = np.nan
        np.save(npy, block(a, 5).astype(np.float32))   # 0.5 deg mean of 25 cells
        os.remove(p)
        return day, True


def imerg_download():
    IM_DIR.mkdir(exist_ok=True)
    jobs = cmr("GPM_3IMERGDF", "2019-01-01", "2019-12-31T23:59:59Z", version="07")
    todo = [j for j in jobs if not (IM_DIR / f"imerg_{j[0]}.npy").exists()]
    print(f"IMERG: {len(jobs)} days listed, {len(todo)} to fetch", flush=True)
    with ThreadPoolExecutor(10) as ex:
        for day, ok in ex.map(imerg_one, todo):
            if not ok:
                print("  IMERG failed", day, flush=True)


def imergm_one(job):
    day, url = job
    npy = IM_DIR / f"imergm_{day[:7]}.npy"
    if npy.exists():
        return day, True
    ce = urllib.parse.quote("/Grid/precipitation[0][2450:2799][950:1249]", safe="")
    try:
        p = SL.fetch(f"{url}.dap.nc4?dap4.ce={ce}", ID, name=f"imerg/tmpm_{day[:7]}.nc4", token=True, min_bytes=20000)
    except RuntimeError:
        return day, False
    with LOCK:
        import netCDF4
        ds = netCDF4.Dataset(p)
        v = walk_var(ds, "precipitation")
        assert v.units == "mm/hr", v.units
        a = np.ma.filled(np.ma.masked_invalid(v[0]).astype(np.float32), np.nan).T * 24.0   # mm/hr -> mm/day
        ds.close()
        a[a < 0] = np.nan
        np.save(npy, block(a, 5).astype(np.float32))
        os.remove(p)
        return day, True


def imergm_download():
    jobs = cmr("GPM_3IMERGM", "2018-01-01", "2020-12-31T23:59:59Z", version="07")
    print(f"IMERG monthly: {len(jobs)} months listed", flush=True)
    with ThreadPoolExecutor(4) as ex:
        for day, ok in ex.map(imergm_one, jobs):
            if not ok:
                print("  IMERG monthly failed", day, flush=True)


def imergm(y, m):
    f = IM_DIR / f"imergm_{y}-{m:02d}.npy"
    return np.load(f) if f.exists() else None


def imerg_day(d):
    f = IM_DIR / f"imerg_{d.isoformat()}.npy"
    return np.load(f) if f.exists() else None


# ---------------------------------------------------------------- MERRA-2 850 hPa wind
M2_DIR = CACHE / "merra2"
# M2 grid: lat -90 + 0.5 i, lon -180 + 0.625 j. rows 190..249 = 5.0..34.5 N, cols 392..447 = 65.0..99.375 E
WI0, WI1, WJ0, WJ1 = 190, 249, 392, 447
WLATC = -90 + 0.5 * np.arange(WI0, WI1 + 1).reshape(-1, 2).mean(1)        # 5.25 .. 34.25
WLONC = -180 + 0.625 * np.arange(WJ0, WJ1 + 1).reshape(-1, 2).mean(1)     # 65.3125 .. 99.0625
AS_BOX = (10, 20, 65, 72.5)     # Arabian Sea box for the u lane


def m2_one(job):
    day, url = job
    npy = M2_DIR / f"m2_{day}.npy"
    if npy.exists():
        return day, True
    ce = urllib.parse.quote(f"/U850[0:23][{WI0}:{WI1}][{WJ0}:{WJ1}];/V850[0:23][{WI0}:{WI1}][{WJ0}:{WJ1}]", safe="")
    try:
        p = SL.fetch(f"{url}.dap.nc4?dap4.ce={ce}", ID, name=f"merra2/tmp_{day}.nc4", token=True, min_bytes=20000)
    except RuntimeError:
        return day, False
    with LOCK:
        import netCDF4
        ds = netCDF4.Dataset(p)
        out = []
        for nm in ("U850", "V850"):
            v = np.ma.filled(np.ma.masked_invalid(ds[nm][:]).astype(np.float32), np.nan)
            v[np.abs(v) > 1e10] = np.nan
            with np.errstate(all="ignore"):
                out.append(np.nanmean(v, 0))          # daily mean of 24 hourly means (UTC day)
        ds.close()
        np.save(npy, np.array(out, np.float32))       # (2, 60, 56) native 0.5 x 0.625
        os.remove(p)
        return day, True


def m2_download():
    M2_DIR.mkdir(exist_ok=True)
    jobs = cmr("M2T1NXSLV", "2019-01-01", "2019-12-31T23:59:59Z")
    todo = [j for j in jobs if not (M2_DIR / f"m2_{j[0]}.npy").exists()]
    print(f"MERRA-2: {len(jobs)} days listed, {len(todo)} to fetch", flush=True)
    with ThreadPoolExecutor(10) as ex:
        for day, ok in ex.map(m2_one, todo):
            if not ok:
                print("  MERRA-2 failed", day, flush=True)


# ---------------------------------------------------------------- MODIS NDVI monthly
ND_DIR = CACHE / "ndvi"


def ndvi_one(job):
    day, url = job
    npy = ND_DIR / f"ndvi_{day[:7]}.npy"
    if npy.exists():
        return day, True
    # 0.05 deg CMG, rows from 90N: rows 1100..1699 = 35..5 N, cols 4900..5599 = 65..100 E
    ce = urllib.parse.quote("/MOD_Grid_monthly_CMG_VI/Data_Fields/CMG_0_05_Deg_Monthly_NDVI[1100:1699][4900:5599]", safe="")
    try:
        p = SL.fetch(f"{url}.dap.nc4?dap4.ce={ce}", ID, name=f"ndvi/tmp_{day[:7]}.nc4", token=True, min_bytes=100000)
    except RuntimeError:
        return day, False
    with LOCK:
        import h5py
        with h5py.File(p, "r") as f:
            found = []
            f.visititems(lambda n, o: found.append(o[()]) if n.endswith("Monthly_NDVI") and hasattr(o, "shape") else None)
        raw = found[0].astype(np.float32)
        a = np.where((raw < -2000) | (raw > 10000), np.nan, raw * 1e-4)   # fill -3000, valid -2000..10000, scale 1e-4
        a = a[::-1]                                                         # south -> north
        h = a.reshape(60, 10, 70, 10)
        n = np.isfinite(h).sum(axis=(1, 3))
        with np.errstate(all="ignore"):
            m = np.nanmean(h, axis=(1, 3))
        m[n < 50] = np.nan                                                  # need >= half of the 100 sub-cells (land)
        np.save(npy, m.astype(np.float32))
        os.remove(p)
        return day, True


def ndvi_download():
    ND_DIR.mkdir(exist_ok=True)
    jobs = cmr("MOD13C2", "2018-01-01", "2020-12-31T23:59:59Z", version="061")
    todo = [j for j in jobs if not (ND_DIR / f"ndvi_{j[0][:7]}.npy").exists()]
    print(f"NDVI: {len(jobs)} months listed, {len(todo)} to fetch", flush=True)
    with ThreadPoolExecutor(4) as ex:
        for day, ok in ex.map(ndvi_one, todo):
            if not ok:
                print("  NDVI failed", day, flush=True)


def ndvi_month(y, m):
    f = ND_DIR / f"ndvi_{y}-{m:02d}.npy"
    return np.load(f) if f.exists() else None


# ---------------------------------------------------------------- GRACE / GRACE-FO mascons
GRACE_URL = None


def grace_monthly():
    """-> dict {(y, m): India mean cm} using the solution month's centre date; plus 2019 grids at 0.5 deg."""
    global GRACE_URL
    js = json.loads(subprocess.run(["curl", "-sf", "--retry", "5",
                                    "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4&page_size=10&sort_key=-start_date"],
                                   capture_output=True, check=True).stdout)
    GRACE_URL = next(l["href"] for l in js["feed"]["entry"][0]["links"] if l["href"].endswith(".nc") and "protected" in l["href"])
    p = SL.fetch(GRACE_URL, ID, name=GRACE_URL.split("/")[-1], token=True, min_bytes=10_000_000)
    import netCDF4
    ds = netCDF4.Dataset(p)
    lat, lon = ds["lat"][:], ds["lon"][:]
    i0, j0 = int(np.argmin(np.abs(lat - LATC[0]))), int(np.argmin(np.abs(lon - LONC[0])))
    assert abs(lat[i0] - LATC[0]) < 1e-3 and abs(lon[j0] - LONC[0]) < 1e-3
    t = ds["time"][:]
    tb = ds["time_bounds"][:]
    base = dt.datetime(2002, 1, 1)
    lwe = ds["lwe_thickness"]
    out = {}
    for k in range(len(t)):
        c = (base + dt.timedelta(days=float(t[k]))).date()
        if c.year not in YEARS and not (c.year == 2017 and c.month >= 10):
            continue
        g = np.ma.filled(lwe[k, i0:i0 + 60, j0:j0 + 70].astype(np.float32), np.nan)
        a = (base + dt.timedelta(days=float(tb[k, 0]))).date()
        b = (base + dt.timedelta(days=float(tb[k, 1]))).date()
        out[(c.year, c.month)] = {"mean": india_mean(g), "grid": g, "a": a, "b": b, "c": c}
    ds.close()
    return out


# ---------------------------------------------------------------- helpers
def month_of(d):
    return d.year, d.month


def rnd(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def run_mean(x, w):
    """forward window mean over [k, k+w), None if any value missing (no bridging)."""
    out = [None] * len(x)
    for k in range(len(x) - w + 1):
        s = x[k:k + w]
        if all(v is not None for v in s):
            out[k] = sum(s) / w
    return out


def lag_link(a, b, maxlag, method, min_n=8):
    """Pearson r for b lagging a by 0..maxlag (positive only), best r; plus full curve from SL.link."""
    full = SL.link(np.array(a, float), np.array(b, float), maxlag, "month", method, min_n=min_n)
    rows = [c for c in full.get("curve", []) if c[0] >= 0]
    if not rows:
        return full
    k, r = max(rows, key=lambda c: c[1])
    x, y = SL._pairs(np.array(a, float), np.array(b, float), k)
    full.update({"r": r, "lag": k, "n": int(len(x)), "sign": "positive" if r > 0 else "negative",
                 "strength": "strong" if abs(r) >= .6 else "moderate" if abs(r) >= .3 else "weak",
                 "curve": [c for c in full["curve"]]})
    return full


# ---------------------------------------------------------------- main
def main():
    global MASK
    MASK = india_mask()
    print("India 0.5 deg cells:", int(MASK.sum()), flush=True)
    imerg_download()
    imergm_download()
    m2_download()
    ndvi_download()
    grace = grace_monthly()

    # ---- rain, daily 2018-2020 India mean
    rain_all = {}
    d = D0
    while d <= dt.date(2019, 12, 31):
        g = imerg_day(d)
        rain_all[d] = None if g is None else india_mean(g)
        d += dt.timedelta(1)
    rain = [rnd(rain_all[d]) for d in DAYS]
    rain_grids = np.array([g if (g := imerg_day(d)) is not None else np.full(NG, np.nan, np.float32) for d in DAYS])

    # 8-day frames (46 frames; last one Dec 27..31 = 5 days)
    rf, rt = [], []
    for s in range(0, NT, 8):
        w = rain_grids[s:s + 8]
        nvalid = np.isfinite(w).sum(0)
        with np.errstate(all="ignore"):
            m = np.nanmean(w, 0)
        m[nvalid < min(6, len(w))] = np.nan
        rf.append(m)
        rt.append(s + (len(w) - 1) / 2)
    rf = np.array(rf)
    rain_vmax = 40.0
    p995 = float(np.nanpercentile(rf, 99.5))

    # ---- monthly rain: 2019 from the daily lane (for stats); 2018-2020 from IMERG monthly (for the link)
    def mmean(y, m):
        v = [rain_all[dd] for dd in rain_all if dd.year == y and dd.month == m]
        ok = [x for x in v if x is not None]
        return float(np.mean(ok)) if len(ok) >= 0.8 * len(v) else None
    months = [(y, m) for y in YEARS for m in range(1, 13)]
    rmon19 = [mmean(2019, m) for m in range(1, 13)]
    rain_m = [None if (g := imergm(y, m)) is None else india_mean(g) for y, m in months]
    print("2019 monthly rain, daily-derived vs IMERG monthly:", [rnd(a) for a in rmon19], [rnd(b) for b in rain_m[12:24]], flush=True)

    # ---- NDVI
    nd_m = []
    for y, m in months:
        g = ndvi_month(y, m)
        nd_m.append(None if g is None else india_mean(g))
    nd19 = [ndvi_month(2019, m) for m in range(1, 13)]
    nd_grid = np.array([g if g is not None else np.full(NG, np.nan, np.float32) for g in nd19])
    mid = [(dt.date(2019, m, 15) - D0).days for m in range(1, 13)]
    green = [rnd(nd_m[12 + DAYS[k].month - 1], 4) for k in range(NT)]

    # ---- GRACE
    gr_m = []
    for y, m in months:
        e = grace.get((y, m))
        gr_m.append(None if e is None else e["mean"])
    water = [None] * NT
    gr19 = {k: v for k, v in grace.items() if k[0] == 2019}
    for (y, m), e in sorted(grace.items()):
        for k in range(NT):
            if e["a"] <= DAYS[k] < e["b"] and e["mean"] is not None:
                water[k] = rnd(e["mean"], 2)
    gr_frames = sorted(gr19.items())
    gr_grid = np.array([e["grid"] for _, e in gr_frames])
    gr_t = [(e["c"] - D0).days for _, e in gr_frames]

    # ---- wind
    U = np.full((NT, 30, 28), np.nan, np.float32)
    V = np.full((NT, 30, 28), np.nan, np.float32)
    as_u = [None] * NT
    nlat = -90 + 0.5 * np.arange(WI0, WI1 + 1)
    nlon = -180 + 0.625 * np.arange(WJ0, WJ1 + 1)
    bi = (nlat >= AS_BOX[0]) & (nlat <= AS_BOX[1])
    bj = (nlon >= AS_BOX[2]) & (nlon <= AS_BOX[3])
    bw = np.cos(np.radians(nlat[bi]))[:, None] * np.ones(bj.sum())
    for k, dday in enumerate(DAYS):
        f = M2_DIR / f"m2_{dday.isoformat()}.npy"
        if not f.exists():
            continue
        a = np.load(f)
        U[k] = block(a[0], 2)
        V[k] = block(a[1], 2)
        sub = a[0][np.ix_(bi, bj)]
        as_u[k] = rnd((sub * bw).sum() / bw.sum(), 2)
    wf_u, wf_v, wt = [], [], []
    for s in range(0, NT, 7):
        with np.errstate(all="ignore"):
            wf_u.append(np.nanmean(U[s:s + 7], 0))
            wf_v.append(np.nanmean(V[s:s + 7], 0))
        wt.append(s + (min(7, NT - s) - 1) / 2)
    wf_u, wf_v = np.array(wf_u), np.array(wf_v)

    # ---- links (monthly, 2018-2020)
    lk = lag_link(rain_m, nd_m, 3, "Pearson r, monthly means 2018-2020 (36 months): all-India land rain (IMERG Final monthly, observed) vs India land NDVI (MODIS MOD13C2), NDVI lagging by 0 to 3 months; best positive lag reported")
    lk["lag_steps"] = round(lk["lag"] * 30.44) if lk.get("lag") is not None else None
    lk["lag_days_note"] = "lag_steps = lag in months x 30.44 days (monthly resolution, so +/- about 15 days)"
    lk_w = lag_link(rain_m, gr_m, 3, "Pearson r, monthly means 2018-2020: all-India land rain (IMERG) vs India mean GRACE/GRACE-FO water thickness (JPL mascons), water lagging by 0 to 3 months; missing GRACE months skipped", min_n=6)
    lk_w["lag_steps"] = round(lk_w["lag"] * 30.44) if lk_w.get("lag") is not None else None
    # 2019 alone (12 months, only lags 0..3 inside the year)
    lk19 = lag_link(rain_m[12:24], nd_m[12:24], 3, "Pearson r, 2019 only, monthly", min_n=8)

    # ---- monsoon numbers
    THR = 5.0          # mm/day all-India land mean
    r7 = run_mean(rain, 7)
    onset = None
    for k in range(90, NT - 21):
        if all(r7[j] is not None and r7[j] >= THR for j in range(k, k + 15)):
            onset = k
            break
    withdraw = None
    if onset is not None:
        for k in range(onset + 15, NT - 7):
            if all(r7[j] is not None and r7[j] < THR for j in range(k, min(NT - 6, k + 15))):
                withdraw = k
                break
    u7 = run_mean(as_u, 7)
    uflip = None
    for k in range(60, NT - 37):
        if all(u7[j] is not None and u7[j] > 5.0 for j in range(k, k + 30)):
            uflip = k
            break
    kpk = int(np.nanargmax([np.nan if v is None else v for v in rain]))
    jjas = [rain[k] for k in range((dt.date(2019, 6, 1) - D0).days, (dt.date(2019, 10, 1) - D0).days) if rain[k] is not None]
    nd19m = nd_m[12:24]
    nmin, nmax = int(np.nanargmin(np.array(nd19m, float))), int(np.nanargmax(np.array(nd19m, float)))
    ukmax = int(np.nanargmax(np.array(u7[:NT - 6], dtype=float)))
    ann = sum(v for v in rain if v is not None)
    wmon19 = gr_m[12:24]
    wmin = int(np.nanargmin(np.array([np.nan if v is None else v for v in wmon19])))
    wmax = int(np.nanargmax(np.array([np.nan if v is None else v for v in wmon19])))

    iso = lambda k: DAYS[k].isoformat()
    stats = {
        "monsoon onset (all-India 7-day mean rain stays at or above 5 mm/day for 15 days)": iso(onset) if onset is not None else None,
        "end of wet spell (7-day mean back below 5 mm/day for 15 days)": iso(withdraw) if withdraw is not None else None,
        "Arabian Sea 850 hPa westerly sets in (7-day mean u above 5 m/s for 30 days)": iso(uflip) if uflip is not None else None,
        "peak rain day": iso(kpk), "peak all-India rain (mm/day)": rain[kpk],
        "June to September mean all-India rain (mm/day)": round(float(np.mean(jjas)), 2),
        "2019 all-India land rain total (mm)": round(ann, 0),
        "wettest month (mm/day)": rnd(max(rmon19), 2), "wettest month": MONTH_NAMES[int(np.argmax(rmon19))],
        "driest month (mm/day)": rnd(min(rmon19), 2), "driest month": MONTH_NAMES[int(np.argmin(rmon19))],
        "strongest 7-day Arabian Sea westerly (m/s)": rnd(u7[ukmax], 1), "strongest westerly week starts": iso(ukmax),
        "Arabian Sea u850 January mean (m/s)": rnd(np.mean([v for v in as_u[:31] if v is not None]), 1),
        "NDVI min month": MONTH_NAMES[nmin], "NDVI min": rnd(nd19m[nmin], 3),
        "NDVI max month": MONTH_NAMES[nmax], "NDVI max": rnd(nd19m[nmax], 3),
        "link r rain to NDVI (monthly, 2018-2020)": lk["r"], "link lag (months, NDVI after rain)": lk["lag"],
        "link lag (days, approx)": lk["lag_steps"], "link n (months)": lk["n"], "link r at lag 0": lk["r_lag0"],
        "link r rain to NDVI, 2019 only": lk19.get("r"), "link lag 2019 only (months)": lk19.get("lag"),
        "link r rain to GRACE water (monthly)": lk_w.get("r"), "link lag rain to GRACE water (months)": lk_w.get("lag"),
        "link n rain to GRACE water (months)": lk_w.get("n"),
        "GRACE water min month 2019": MONTH_NAMES[wmin], "GRACE water min (cm)": rnd(wmon19[wmin], 1),
        "GRACE water max month 2019": MONTH_NAMES[wmax], "GRACE water max (cm)": rnd(wmon19[wmax], 1),
        "rain map 8-day mean 99.5th percentile (mm/day)": round(p995, 1),
    }
    print(json.dumps({"rain_m": [rnd(x) for x in rain_m], "nd_m": [rnd(x, 3) for x in nd_m], "gr_m": [rnd(x) for x in gr_m],
                      "curve": lk["curve"], "curve_w": lk_w.get("curve"), "curve19": lk19.get("curve")}), flush=True)

    imerg_missing = SL.gap_count(rain)
    m2_missing = SL.gap_count(as_u)
    nd_missing = sum(1 for g in nd19 if g is None)
    gr_missing_19 = [MONTH_NAMES[m - 1] for m in range(1, 13) if (2019, m) not in grace]
    gaps = [
        "Onset here is a data rule on the all-India land mean (7-day mean rain at or above 5 mm/day for 15 days in a row), not the India Meteorological Department onset over Kerala; the all-India mean rises later than the first rains in the south.",
        "Rain is IMERG Final Run v07: satellite microwave and infrared estimates calibrated to monthly rain gauges; daily values over mountains (Himalaya, Western Ghats) carry larger errors.",
        f"Rain map frames are 8-day means at 0.5 deg (46 frames, the last covers 5 days); the colour scale is linear 0 to {rain_vmax:g} mm/day with a floor of 1 mm/day, values above {rain_vmax:g} are drawn at full colour (99.5th percentile of the frames: {p995:.1f} mm/day).",
        "Wind is MERRA-2 reanalysis (a model) at 850 hPa, about 1.5 km up, daily means of hourly fields, drawn as 7-day means at 1 x 1.25 deg; the lane is the Arabian Sea box 10 to 20 N, 65 to 72.5 E.",
        "NDVI is a monthly MODIS composite: the lane holds each month's value on every day of that month (a step, not interpolated); the map changes once a month. Cells need at least half of their 0.05 deg pixels to be valid land.",
        "India means use 0.5 deg cells whose centre falls inside the Natural Earth 1:50m outline of India (cosine latitude weighted); coastal cells and small islands are partly missed.",
        "The rain to NDVI link uses monthly means 2018 to 2020 (36 months), rain from the IMERG Final monthly product (GPM_3IMERGM v07), the lane and 2019 numbers from the daily product. Both follow the seasonal cycle, so the correlation mostly says that vegetation greens after the rains; it is not a measure of year to year sensitivity. Lag resolution is one month (about 30 days).",
        "GRACE and GRACE-FO water thickness is shown on a 0.5 deg grid but its real resolution is about 300 km (3 deg mascons); it measures total water (soil, ground, surface) change relative to a 2004 to 2009 mean, not rain.",
    ]
    gaps.append("Wind at 850 hPa does not exist where the ground is higher than that level (Tibetan Plateau, high Himalaya): those cells are empty, not filled.")
    gaps.append("Water map: linear scale -40 to 40 cm (anomaly against the 2004 to 2009 mean), no floor; values beyond are drawn at the end colours. The lane holds each GRACE-FO solution over its own date range.")
    gr_missing_link = [f"{y}-{m:02d}" for (y, m), v in zip(months, gr_m) if v is None]
    if gr_missing_link:
        gaps.append("GRACE / GRACE-FO months without a solution, skipped in the rain to water link: " + ", ".join(gr_missing_link) + " (the GRACE to GRACE-FO gap and early GRACE-FO months).")
    wnull = SL.gap_count(water)
    if wnull:
        gaps.append(f"Water lane: {wnull} days of 2019 fall between GRACE-FO solution date ranges and stay empty (not bridged).")
    if gr_missing_19:
        gaps.append("GRACE-FO has no solution for " + ", ".join(gr_missing_19) + " 2019: those days are empty in the water lane, not bridged.")
    if imerg_missing:
        gaps.append(f"IMERG: {imerg_missing} days without data in 2019 (left empty).")
    if m2_missing:
        gaps.append(f"MERRA-2: {m2_missing} days without data in 2019 (left empty).")
    if nd_missing:
        gaps.append(f"MODIS NDVI: {nd_missing} months missing in 2019.")
    gaps.append(f"Link strength: rain to NDVI r {lk['r']} ({lk['strength']}) at {lk['lag']} month lag, n {lk['n']}; rain to GRACE water r {lk_w.get('r')} ({lk_w.get('strength')}) at {lk_w.get('lag')} month lag, n {lk_w.get('n')}.")

    t_jun1 = (dt.date(2019, 6, 1) - D0).days
    t_oct1 = (dt.date(2019, 10, 1) - D0).days
    beats = [
        {"t": 0, "text": f"January 2019 over India. The land is dry, about {rnd(rmon19[0], 1)} millimetres of rain a day on average, and the low-level wind over the Arabian Sea blows from the east: the westerly component is {stats['Arabian Sea u850 January mean (m/s)']} metres per second. Vegetation index {rnd(nd19m[0], 2)}."},
        {"t": mid[nmin], "text": f"{MONTH_NAMES[nmin]}. The hottest, driest weeks: vegetation index falls to its low, {rnd(nd19m[nmin], 2)} in {MONTH_NAMES[nmin]}."},
    ]
    if uflip is not None:
        beats.append({"t": uflip, "text": f"{DAYS[uflip].strftime('%d %B')}: the wind over the Arabian Sea has turned westerly and holds above 5 metres per second, carrying ocean moisture onto the land."})
    if onset is not None:
        beats.append({"t": onset, "text": f"{DAYS[onset].strftime('%d %B')}: monsoon onset in the all-India average, rain holds at or above 5 millimetres a day."})
    beats.append({"t": kpk, "text": f"{DAYS[kpk].strftime('%d %B')}: the wettest day of the year, {rain[kpk]} millimetres averaged over all of India. The westerly peaks near {stats['strongest 7-day Arabian Sea westerly (m/s)']} metres per second."})
    beats.append({"t": mid[nmax], "text": f"{MONTH_NAMES[nmax]}: India is greenest, vegetation index {rnd(nd19m[nmax], 2)}. Across 2018 to 2020 greenness follows the rain by about {lk['lag']} month, r {lk['r']} over {lk['n']} months."})
    if withdraw is not None:
        beats.append({"t": withdraw, "text": f"{DAYS[withdraw].strftime('%d %B')}: the rains fade below 5 millimetres a day. June to September averaged {stats['June to September mean all-India rain (mm/day)']} millimetres a day."})
    beats.append({"t": mid[wmax] if wmax < 12 else 300, "text": f"{MONTH_NAMES[wmax]}: GRACE-FO weighs the stored water, {rnd(wmon19[wmax], 1)} centimetres above the 2004 to 2009 mean, up from {rnd(wmon19[wmin], 1)} in {MONTH_NAMES[wmin]}."})
    beats.sort(key=lambda b: b["t"])

    events = [{"t": kpk, "label": "peak rain day"}]
    if onset is not None:
        events.append({"t": onset, "label": "monsoon onset (all-India)"})
    if uflip is not None:
        events.append({"t": uflip, "label": "westerly sets in"})
    if withdraw is not None:
        events.append({"t": withdraw, "label": "rains fade"})
    events.append({"t": mid[nmax], "label": "greenest month"})
    events.sort(key=lambda e: e["t"])

    rain_enc = SL.enc_grid(rf, 0, rain_vmax, float(LATC[0]), float(LATC[-1]), float(LONC[0]), float(LONC[-1]), rt, "mm/day", "observed", floor=1.0)
    nd_enc = SL.enc_grid(nd_grid, 0, 0.9, float(LATC[0]), float(LATC[-1]), float(LONC[0]), float(LONC[-1]), mid, "NDVI", "observed", floor=0.1)
    gr_enc = SL.enc_grid(gr_grid, -40, 40, float(LATC[0]), float(LATC[-1]), float(LONC[0]), float(LONC[-1]), gr_t, "cm", "observed", floor=-40)
    wind_enc = SL.enc_wind(wf_u, wf_v, float(WLATC[0]), float(WLATC[-1]), float(WLONC[0]), float(WLONC[-1]), wt, 0.25,
                           "MERRA-2 850 hPa wind, 7-day means (reanalysis model)")

    valid = [v for v in rain if v is not None]
    obj = {
        "title": "India monsoon 2019: rain, wind, green",
        "script": "c3_monsoon.py",
        "timebase": "day", "t0": "2019-01-01T00:00Z", "step_s": 86400, "n": NT,
        "region": {"lat0": 5, "lat1": 35, "lon0": 65, "lon1": 100},
        "hero": "rain", "partner": "green",
        "link": lk,
        "links_extra": {"rain_water": lk_w, "rain_green_2019_only": lk19},
        "hero_norm": {"min": round(min(valid), 2), "max": round(max(valid), 2),
                      "method": "min..max of the hero series itself (all-India land mean daily rain, IMERG, 2019)"},
        "stats": stats, "gaps": gaps, "beats": beats, "events": events,
        "bands": [{"t0": t_jun1, "t1": t_oct1 - 1, "label": "June to September monsoon season"}],
        "monthly": {"months": [f"{y}-{m:02d}" for y, m in months], "rain_mm_day": [rnd(x) for x in rain_m],
                    "ndvi": [rnd(x, 4) for x in nd_m], "grace_cm": [rnd(x) for x in gr_m]},
        "sources": [
            {"name": "GPM IMERG Final Precipitation L3 1 day 0.1 x 0.1 deg V07 (GPM_3IMERGDF)", "producer": "NASA GPM (Huffman et al.), distributed by GES DISC",
             "resolution": "0.1 deg daily, shown at 0.5 deg, 8-day map frames", "kind": "observed", "period": "2019",
             "baseline": "none (cycle: own min..max)", "url": "https://doi.org/10.5067/GPM/IMERGDF/DAY/07"},
            {"name": "GPM IMERG Final Precipitation L3 1 month 0.1 x 0.1 deg V07 (GPM_3IMERGM)", "producer": "NASA GPM (Huffman et al.), distributed by GES DISC",
             "resolution": "0.1 deg monthly, India mean at 0.5 deg", "kind": "observed", "period": "2018-01 to 2020-12 (link only)",
             "baseline": "none", "url": "https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07"},
            {"name": "MERRA-2 tavg1_2d_slv_Nx hourly single-level diagnostics, U850 and V850 (M2T1NXSLV v5.12.4)", "producer": "NASA GMAO, distributed by GES DISC",
             "resolution": "0.5 x 0.625 deg hourly, shown at 1 x 1.25 deg, daily lane, 7-day map frames", "kind": "model", "period": "2019",
             "baseline": "none", "url": "https://doi.org/10.5067/VJAFPLI1CSIV"},
            {"name": "MODIS/Terra Vegetation Indices Monthly L3 Global 0.05 deg CMG V061 (MOD13C2)", "producer": "NASA LP DAAC (Didan)",
             "resolution": "0.05 deg monthly, shown at 0.5 deg", "kind": "observed", "period": "2018-01 to 2020-12 (map 2019)",
             "baseline": "none", "url": "https://doi.org/10.5067/MODIS/MOD13C2.061"},
            {"name": "JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent Water Height RL06.3 CRI v04", "producer": "NASA JPL (Watkins et al., Wiese et al.), distributed by PO.DAAC",
             "resolution": "about 3 deg (300 km) mascons on a 0.5 deg grid, monthly", "kind": "observed", "period": "2017-10 to 2020-12 (map 2019)",
             "baseline": "anomaly relative to the 2004.0 to 2009.999 mean", "url": "https://doi.org/10.5067/TEMSC-3JC634"},
            {"name": "Natural Earth 1:50m admin 0 countries (India outline for land means)", "producer": "Natural Earth",
             "resolution": "1:50 million", "kind": "observed", "period": "static", "baseline": "none",
             "url": "https://www.naturalearthdata.com/downloads/50m-cultural-vectors/"},
        ],
        "layers": [
            {"id": "rain", "type": "field", "name": "Rain", "palette": "rain",
             "what": "Daily rain, NASA GPM IMERG Final v07 (observed, satellite with gauge calibration); lane = all-India land mean",
             "color": "#4aa3ff", "unit": "mm/day", "series": rain, "grid": rain_enc},
            {"id": "wind", "type": "streaks", "name": "Monsoon wind",
             "what": "850 hPa wind, MERRA-2 reanalysis (model); lane = westerly component over the Arabian Sea, positive = from the west",
             "color": "#c8d6e5", "unit": "m/s", "series": as_u, "wind": wind_enc},
            {"id": "green", "type": "field", "name": "Green", "palette": "green",
             "what": "Vegetation index NDVI, MODIS Terra MOD13C2 monthly (observed); lane = India land mean, one value per month",
             "color": "#5cc46a", "unit": "NDVI", "series": green, "grid": nd_enc},
            {"id": "water", "type": "field", "name": "Stored water", "palette": "water",
             "what": "Total water storage change, GRACE-FO JPL mascons (observed, about 300 km real resolution); lane = India mean, one value per month",
             "color": "#2fb9c4", "unit": "cm", "series": water, "grid": gr_enc},
        ],
    }
    SL.write_story(ID, obj)


if __name__ == "__main__":
    main()
