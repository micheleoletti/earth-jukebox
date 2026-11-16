"""C3 India monsoon 2025 with NASA EIC rain anomaly frames, 2025-01-01 .. 2025-12-31 (daily story, 365 steps).

Second version of the monsoon story (the 2019 story c3_monsoon stays). Same layers as c3_monsoon.py, rebuilt for 2025,
plus one new layer:

  eic    NASA Scientific Visualization Studio item 4897, "Seasonal Global Precipitation Variation from the Global
         Precipitation Measurement Constellation" (shown in the NASA Earth Information Center). Daily global flat maps,
         3600 x 1800 equirectangular, transparent PNG (frames/3600x1800_2x1_15p/flatalpha/imergvar_alpha.YYYY.MM.DD.png).
         What a pixel means (verified on the frames and the item's colour bar): IMERG precipitation ANOMALY, the departure
         from the IMERG climatology, in mm/day. Each day's departure is added to the map and then fades over about three
         months, so a frame is a slowly fading memory of recent departures, not that day's rain. The frames use exactly
         8 flat colours, one per colour-bar bin (-20 -15 -10 -5 -2 | 2 5 10 15 20 mm/day); pixels within -2..+2 mm/day are
         transparent (near normal). The page reads the pixel under the listening point with the colour table below and
         turns |anomaly| into the harmony tension.
         Frames embedded: every 3rd day June to October plus the 1st of the other months, re-centred to -180..180,
         nearest-neighbour resized to 2048 x 1024, 9-colour indexed PNG with transparency (colours stay exact).
         Lane: India land mean of the frame anomaly (bin mid values, transparent = 0), from all 365 daily frames.

  rain   NASA GPM IMERG Late Run daily v07 (GPM_3IMERGDL). The Final Run daily product used for 2019 ends on 2025-09-30,
         so 2025 uses the Late Run for the whole year (one consistent product).
  wind   MERRA-2 850 hPa wind (model), as c3_monsoon.
  green  MODIS Terra MOD13C2 monthly NDVI, as c3_monsoon.
  water  GRACE-FO JPL mascons RL06.3 v04, as c3_monsoon.
Link: rain vs NDVI, monthly means 2023-01 .. 2025-09 (IMERG Final monthly, which ends 2025-09).

Earthdata token: read from the file named by $EARTHDATA_TOKEN_FILE (default ~/.earthdata_token), never printed.
Usage: EARTHDATA_TOKEN_FILE=/path/to/token python c3_monsoon_eic.py
"""
import base64
import datetime as dt
import io
import json
import os
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402
import c3_monsoon as M  # noqa: E402  (re-use the 2019 pipeline's readers; its module globals are re-pointed below)

ID = "c3_monsoon_eic"
CACHE = SL.cache_dir(ID)
Y = 2025
D0 = dt.date(Y, 1, 1)
NT = 365
DAYS = [D0 + dt.timedelta(k) for k in range(NT)]
LINK_MONTHS = [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13) if (y, m) <= (2025, 9)]
MONTH_NAMES = M.MONTH_NAMES
LATC, LONC, NG = M.LATC, M.LONC, M.NG

EIC_BASE = "https://svs.gsfc.nasa.gov/vis/a000000/a004800/a004897/frames/3600x1800_2x1_15p"
EIC_DIR = CACHE / "eic_alpha"
# colour bar of item 4897 (read from imergvar_1080p.now.png): flat colour -> bin [lo, hi] mm/day, mid value used for numbers.
# The end bins also hold everything beyond +/-20 (the colour bar's end triangles have the same colours).
EIC_BINS = [
    ((242, 226, 185), None, -15.0, -17.5),
    ((211, 170, 94), -15.0, -10.0, -12.5),
    ((161, 103, 18), -10.0, -5.0, -7.5),
    ((95, 54, 3), -5.0, -2.0, -3.5),
    ((0, 69, 56), 2.0, 5.0, 3.5),
    ((11, 125, 118), 5.0, 10.0, 7.5),
    ((102, 187, 177), 10.0, 15.0, 12.5),
    ((189, 230, 225), 15.0, None, 17.5),
]
EIC_MID = np.array([0.0] + [b[3] for b in EIC_BINS], np.float32)     # class 0 = transparent = within +/-2 mm/day
TENSION_FULL = 17.5     # |anomaly| (mm/day, bin mid) that gives full tension


# ---------------------------------------------------------------- downloads (token from a file outside the repo)
def fetch(url, story_id, name=None, headers=None, token=False, retries=4, min_bytes=1):
    """storylib.fetch with the token file path taken from $EARTHDATA_TOKEN_FILE (never printed)."""
    name = name or url.split("?")[0].rstrip("/").split("/")[-1][-60:]
    out = SL.cache_dir(story_id) / name
    if out.exists() and out.stat().st_size >= min_bytes:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["curl", "-sfL", "--retry", "3", "--max-time", "600", "-o", str(out) + ".part"]
    for h in (headers or []):
        cmd += ["-H", h]
    if token:
        tok = pathlib.Path(os.environ.get("EARTHDATA_TOKEN_FILE", str(pathlib.Path.home() / ".earthdata_token"))).read_text().strip()
        cmd += ["-H", "Authorization: Bearer " + tok]
    cmd.append(url)
    r = None
    for k in range(retries):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and os.path.exists(str(out) + ".part") and os.path.getsize(str(out) + ".part") >= min_bytes:
            os.replace(str(out) + ".part", out)
            return out
        time.sleep(2 + 3 * k)
    raise RuntimeError(f"download failed ({r.returncode}): {url[:120]}")


SL.fetch = fetch          # c3_monsoon's readers call SL.fetch(..., token=True)
M.ID = ID
M.CACHE = CACHE
M.IM_DIR = CACHE / "imerg"
M.M2_DIR = CACHE / "merra2"
M.ND_DIR = CACHE / "ndvi"
for d in (M.IM_DIR, M.M2_DIR, M.ND_DIR, EIC_DIR):
    d.mkdir(exist_ok=True)


def run_pool(name, fn, jobs, n):
    print(f"{name}: {len(jobs)} to fetch", flush=True)
    bad = []
    with ThreadPoolExecutor(n) as ex:
        for day, ok in ex.map(fn, jobs):
            if not ok:
                bad.append(day)
    if bad:
        print(f"  {name} failed:", bad, flush=True)
    return bad


def downloads():
    jobs = M.cmr("GPM_3IMERGDL", f"{Y}-01-01", f"{Y}-12-31T23:59:59Z", version="07")
    run_pool("IMERG Late daily", M.imerg_one, [j for j in jobs if not (M.IM_DIR / f"imerg_{j[0]}.npy").exists()], 10)
    jobs = M.cmr("GPM_3IMERGM", "2023-01-01", "2025-12-31T23:59:59Z", version="07")
    run_pool("IMERG Final monthly", M.imergm_one, [j for j in jobs if not (M.IM_DIR / f"imergm_{j[0][:7]}.npy").exists()], 4)
    jobs = M.cmr("M2T1NXSLV", f"{Y}-01-01", f"{Y}-12-31T23:59:59Z")
    run_pool("MERRA-2", M.m2_one, [j for j in jobs if not (M.M2_DIR / f"m2_{j[0]}.npy").exists()], 10)
    jobs = M.cmr("MOD13C2", "2023-01-01", "2025-12-31T23:59:59Z", version="061")
    run_pool("NDVI", M.ndvi_one, [j for j in jobs if not (M.ND_DIR / f"ndvi_{j[0][:7]}.npy").exists()], 4)


# ---------------------------------------------------------------- EIC 4897 frames
def eic_one(d):
    name = f"imergvar_alpha.{d.year}.{d.month:02d}.{d.day:02d}.png"
    try:
        fetch(f"{EIC_BASE}/flatalpha/{name}", ID, name=f"eic_alpha/{name}", min_bytes=10000)
        return d, True
    except RuntimeError:
        return d, False


def eic_classes(path):
    """alpha PNG -> uint8 class map (0 = transparent, 1..8 = EIC_BINS) and the count of pixels with an unknown colour."""
    a = np.asarray(Image.open(path).convert("RGBA"))
    assert a.shape == (1800, 3600, 4), a.shape
    rgb = a[..., :3].astype(np.int32)
    key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    cls = np.zeros(key.shape, np.uint8)
    known = np.zeros(key.shape, bool)
    for i, (c, *_rest) in enumerate(EIC_BINS):
        m = key == ((c[0] << 16) | (c[1] << 8) | c[2])
        cls[m] = i + 1
        known |= m
    opaque = a[..., 3] > 0
    unknown = opaque & ~known
    if unknown.any():   # nearest colour-bar colour (none expected: the frames use only the 8 flat colours)
        pal = np.array([b[0] for b in EIC_BINS], np.int32)
        d2 = ((rgb[unknown][:, None, :] - pal[None]) ** 2).sum(-1)
        cls[unknown] = 1 + d2.argmin(1)
    cls[~opaque] = 0
    return cls, int(unknown.sum()), int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())


def land_shift():
    """Find the longitude of the frames' left edge: match the grey land of one composite frame with Natural Earth land."""
    p = fetch(f"{EIC_BASE}/flatcomposite/imergvar_composite.{Y}.08.01.png", ID, name="probe_composite_2025_08_01.png", min_bytes=100000)
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
    grey = (np.abs(a[..., 0] - a[..., 1]) < 3) & (np.abs(a[..., 1] - a[..., 2]) < 3) & (a[..., 0] > 40)
    land_img = grey.reshape(360, 5, 720, 5).mean(axis=(1, 3)) > .5
    gj = json.loads(SL.fetch("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
                             "c3_monsoon", name="ne50.geojson", min_bytes=100000).read_text())
    im = Image.new("L", (720, 360), 0)
    dr = ImageDraw.Draw(im)
    for f in gj["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            dr.polygon([((x + 180) * 2, (90 - y) * 2) for x, y in poly[0]], fill=1)
    ne = np.asarray(im).astype(bool)
    band = slice(40, 300)       # 70N..60S: leave out Antarctica / Arctic sea ice that Natural Earth countries do not hold
    scores = [(np.mean(np.roll(land_img, -s, axis=1)[band] == ne[band]), s) for s in range(720)]
    best, s = max(scores)
    vbest = max((np.mean(np.roll(np.roll(land_img, -s, axis=1), dv, axis=0)[band] == ne[band]), dv) for dv in range(-6, 7))
    print(f"EIC frame left edge: shift {s} px at 0.5 deg = frame left edge at {(-s / 2) % 360 - 180:+.1f} deg lon, agreement {best:.3f}; vertical best offset {vbest[1]} px", flush=True)
    assert best > .9 and vbest[1] == 0, (best, vbest)
    return s * 5        # in 0.1 deg pixels of the 3600 x 1800 frame


def frame_png(cls_rolled):
    """class map (1800 x 3600, -180..180) -> 2048 x 1024 indexed PNG, index 0 transparent, exact colours."""
    small = Image.fromarray(cls_rolled, "L").resize((2048, 1024), Image.NEAREST)
    p = Image.frombytes("P", small.size, small.tobytes())
    pal = [0, 0, 0] + [v for b in EIC_BINS for v in b[0]]
    p.putpalette(pal + [0] * (768 - len(pal)))
    buf = io.BytesIO()
    p.save(buf, "PNG", optimize=True, transparency=0)
    return buf.getvalue()


def eic_layer(shift):
    todo = [d for d in DAYS if not (EIC_DIR / f"imergvar_alpha.{d.year}.{d.month:02d}.{d.day:02d}.png").exists()]
    bad = run_pool("EIC 4897 frames", eic_one, todo, 8)
    jun1, oct31 = dt.date(Y, 6, 1), dt.date(Y, 10, 31)
    pick = sorted({d for d in DAYS if jun1 <= d <= oct31 and (d - jun1).days % 3 == 0}
                  | {dt.date(Y, m, 1) for m in range(1, 13)} | {dt.date(Y, 12, 31)})
    series, frames, unknown_px, partial_alpha = [None] * NT, [], 0, 0
    for k, d in enumerate(DAYS):
        p = EIC_DIR / f"imergvar_alpha.{d.year}.{d.month:02d}.{d.day:02d}.png"
        if not p.exists():
            continue
        cls, unk, part = eic_classes(p)
        unknown_px += unk
        partial_alpha += part
        cls = np.roll(cls, -shift, axis=1)                    # column 0 = -180 deg
        val = EIC_MID[cls]
        # India box at 0.1 deg: rows 550..849 = 34.95..5.05 N, cols 2450..2799 = 65.05..99.95 E -> 0.5 deg, south -> north
        box = val[550:850, 2450:2800][::-1]
        g = box.reshape(60, 5, 70, 5).mean(axis=(1, 3))
        series[k] = M.rnd(M.india_mean(g), 2)
        if d in pick:
            frames.append({"t": k, "date": d.isoformat(), "img": "data:image/png;base64," + base64.b64encode(frame_png(cls)).decode()})
    missing = [d.isoformat() for d in DAYS if not (EIC_DIR / f"imergvar_alpha.{d.year}.{d.month:02d}.{d.day:02d}.png").exists()]
    return series, frames, missing, unknown_px, partial_alpha, bad


# ---------------------------------------------------------------- main
def main():
    _id, M.ID = M.ID, "c3_monsoon"          # mask outline and GRACE file are shared with the 2019 story's cache
    M.MASK = M.india_mask()
    M.YEARS = [2023, 2024, 2025]
    grace = M.grace_monthly()
    M.ID = _id
    print("India 0.5 deg cells:", int(M.MASK.sum()), flush=True)
    downloads()
    shift = land_shift()
    eic, frames, eic_missing, eic_unknown, eic_partial, _ = eic_layer(shift)
    print(f"EIC frames embedded: {len(frames)}; days without a frame: {len(eic_missing)}; unknown-colour pixels: {eic_unknown}; partial alpha px: {eic_partial}", flush=True)

    # ---- rain, daily 2025 (IMERG Late)
    rain = [M.rnd(None if (g := M.imerg_day(d)) is None else M.india_mean(g)) for d in DAYS]
    rain_grids = np.array([g if (g := M.imerg_day(d)) is not None else np.full(NG, np.nan, np.float32) for d in DAYS])
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

    def mmean(m):
        v = [rain[k] for k in range(NT) if DAYS[k].month == m]
        ok = [x for x in v if x is not None]
        return float(np.mean(ok)) if len(ok) >= 0.8 * len(v) else None
    rmon = [mmean(m) for m in range(1, 13)]
    rain_m = [None if (g := M.imergm(y, m)) is None else M.india_mean(g) for y, m in LINK_MONTHS]

    # ---- NDVI
    nd_m = [None if (g := M.ndvi_month(y, m)) is None else M.india_mean(g) for y, m in LINK_MONTHS]
    nd_y = [M.ndvi_month(Y, m) for m in range(1, 13)]
    nd_ym = [None if g is None else M.india_mean(g) for g in nd_y]
    nd_grid = np.array([g if g is not None else np.full(NG, np.nan, np.float32) for g in nd_y])
    mid = [(dt.date(Y, m, 15) - D0).days for m in range(1, 13)]
    green = [M.rnd(nd_ym[DAYS[k].month - 1], 4) for k in range(NT)]

    # ---- GRACE
    gr_m = [None if (e := grace.get((y, m))) is None else e["mean"] for y, m in LINK_MONTHS]
    water = [None] * NT
    for (y, m), e in sorted(grace.items()):
        for k in range(NT):
            if e["a"] <= DAYS[k] < e["b"] and e["mean"] is not None:
                water[k] = M.rnd(e["mean"], 2)
    gr_frames = sorted((k, v) for k, v in grace.items() if k[0] == Y)
    gr_grid = np.array([e["grid"] for _, e in gr_frames])
    gr_t = [(e["c"] - D0).days for _, e in gr_frames]
    gr_ym = {m: grace[(Y, m)]["mean"] for m in range(1, 13) if (Y, m) in grace}

    # ---- wind (MERRA-2)
    U = np.full((NT, 30, 28), np.nan, np.float32)
    V = np.full((NT, 30, 28), np.nan, np.float32)
    as_u = [None] * NT
    nlat = -90 + 0.5 * np.arange(M.WI0, M.WI1 + 1)
    nlon = -180 + 0.625 * np.arange(M.WJ0, M.WJ1 + 1)
    bi = (nlat >= M.AS_BOX[0]) & (nlat <= M.AS_BOX[1])
    bj = (nlon >= M.AS_BOX[2]) & (nlon <= M.AS_BOX[3])
    bw = np.cos(np.radians(nlat[bi]))[:, None] * np.ones(bj.sum())
    for k, dday in enumerate(DAYS):
        f = M.M2_DIR / f"m2_{dday.isoformat()}.npy"
        if not f.exists():
            continue
        a = np.load(f)
        U[k] = M.block(a[0], 2)
        V[k] = M.block(a[1], 2)
        as_u[k] = M.rnd((a[0][np.ix_(bi, bj)] * bw).sum() / bw.sum(), 2)
    wf_u, wf_v, wt = [], [], []
    for s in range(0, NT, 7):
        with np.errstate(all="ignore"):
            wf_u.append(np.nanmean(U[s:s + 7], 0))
            wf_v.append(np.nanmean(V[s:s + 7], 0))
        wt.append(s + (min(7, NT - s) - 1) / 2)
    wf_u, wf_v = np.array(wf_u), np.array(wf_v)

    # ---- links (monthly 2023-01 .. 2025-09)
    nm = len(LINK_MONTHS)
    lk = M.lag_link(rain_m, nd_m, 3, f"Pearson r, monthly means 2023-01 to 2025-09 ({nm} months): all-India land rain (IMERG Final monthly, observed) vs India land NDVI (MODIS MOD13C2), NDVI lagging by 0 to 3 months; best positive lag reported")
    lk["lag_steps"] = round(lk["lag"] * 30.44) if lk.get("lag") is not None else None
    lk["lag_days_note"] = "lag_steps = lag in months x 30.44 days (monthly resolution, so +/- about 15 days)"
    lk_w = M.lag_link(rain_m, gr_m, 3, "Pearson r, monthly means 2023-01 to 2025-09: all-India land rain (IMERG Final monthly) vs India mean GRACE-FO water thickness (JPL mascons), water lagging by 0 to 3 months; missing GRACE-FO months skipped", min_n=6)
    lk_w["lag_steps"] = round(lk_w["lag"] * 30.44) if lk_w.get("lag") is not None else None
    # same-day link between the daily rain lane and the EIC anomaly lane (descriptive only)
    r_eic, n_eic = SL.pearson(np.array([np.nan if v is None else v for v in rain], float), np.array([np.nan if v is None else v for v in eic], float))

    # ---- monsoon numbers (same rules as 2019)
    THR = 5.0
    r7 = M.run_mean(rain, 7)
    onset = next((k for k in range(90, NT - 21) if all(r7[j] is not None and r7[j] >= THR for j in range(k, k + 15))), None)
    withdraw = None
    if onset is not None:
        withdraw = next((k for k in range(onset + 15, NT - 7) if all(r7[j] is not None and r7[j] < THR for j in range(k, min(NT - 6, k + 15)))), None)
    u7 = M.run_mean(as_u, 7)
    uflip = next((k for k in range(60, NT - 37) if all(u7[j] is not None and u7[j] > 5.0 for j in range(k, k + 30))), None)
    kpk = int(np.nanargmax([np.nan if v is None else v for v in rain]))
    t_jun1, t_oct1 = (dt.date(Y, 6, 1) - D0).days, (dt.date(Y, 10, 1) - D0).days
    jjas = [rain[k] for k in range(t_jun1, t_oct1) if rain[k] is not None]
    ndv = np.array([np.nan if v is None else v for v in nd_ym], float)
    nmin, nmax = int(np.nanargmin(ndv)), int(np.nanargmax(ndv))
    ukmax = int(np.nanargmax(np.array([np.nan if v is None else v for v in u7[:NT - 6]], dtype=float)))
    ann = sum(v for v in rain if v is not None)
    ea = np.array([np.nan if v is None else v for v in eic], float)
    ewet, edry = int(np.nanargmax(ea)), int(np.nanargmin(ea))
    ejjas = [eic[k] for k in range(t_jun1, t_oct1) if eic[k] is not None]
    wmon = [gr_ym.get(m) for m in range(1, 13)]
    wv = np.array([np.nan if v is None else v for v in wmon], float)
    wmin, wmax = int(np.nanargmin(wv)), int(np.nanargmax(wv))

    iso = lambda k: DAYS[k].isoformat()
    stats = {
        "monsoon onset (all-India 7-day mean rain stays at or above 5 mm/day for 15 days)": iso(onset) if onset is not None else None,
        "end of wet spell (7-day mean back below 5 mm/day for 15 days)": iso(withdraw) if withdraw is not None else None,
        "Arabian Sea 850 hPa westerly sets in (7-day mean u above 5 m/s for 30 days)": iso(uflip) if uflip is not None else None,
        "peak rain day": iso(kpk), "peak all-India rain (mm/day)": rain[kpk],
        "June to September mean all-India rain (mm/day)": round(float(np.mean(jjas)), 2),
        f"{Y} all-India land rain total (mm, IMERG Late)": round(ann, 0),
        "wettest month (mm/day)": M.rnd(max(x for x in rmon if x is not None), 2),
        "wettest month": MONTH_NAMES[int(np.nanargmax(np.array([np.nan if x is None else x for x in rmon], float)))],
        "strongest 7-day Arabian Sea westerly (m/s)": M.rnd(u7[ukmax], 1), "strongest westerly week starts": iso(ukmax),
        "NDVI min month": MONTH_NAMES[nmin], "NDVI min": M.rnd(nd_ym[nmin], 3),
        "NDVI max month": MONTH_NAMES[nmax], "NDVI max": M.rnd(nd_ym[nmax], 3),
        "link r rain to NDVI (monthly, 2023-01 to 2025-09)": lk["r"], "link lag (months, NDVI after rain)": lk["lag"],
        "link lag (days, approx)": lk["lag_steps"], "link n (months)": lk["n"], "link r at lag 0": lk["r_lag0"],
        "link r rain to GRACE water (monthly)": lk_w.get("r"), "link lag rain to GRACE water (months)": lk_w.get("lag"),
        "GRACE water min month": MONTH_NAMES[wmin], "GRACE water min (cm)": M.rnd(wmon[wmin], 1),
        "GRACE water max month": MONTH_NAMES[wmax], "GRACE water max (cm)": M.rnd(wmon[wmax], 1),
        "EIC India mean anomaly, wettest day vs usual (mm/day)": eic[ewet], "EIC wettest anomaly day": iso(ewet),
        "EIC India mean anomaly, driest day vs usual (mm/day)": eic[edry], "EIC driest anomaly day": iso(edry),
        "EIC India mean anomaly, June to September mean (mm/day)": M.rnd(float(np.mean(ejjas)), 2) if ejjas else None,
        "same-day r, rain lane vs EIC anomaly lane (descriptive)": None if r_eic is None else round(r_eic, 3),
        "rain map 8-day mean 99.5th percentile (mm/day)": round(p995, 1),
        "EIC frames embedded": len(frames),
    }
    print(json.dumps({"rain_m": [M.rnd(x) for x in rain_m], "nd_m": [M.rnd(x, 3) for x in nd_m], "gr_m": [M.rnd(x) for x in gr_m],
                      "curve": lk["curve"], "curve_w": lk_w.get("curve")}), flush=True)

    gaps = [
        "EIC layer: NASA SVS item 4897 frames show the IMERG precipitation anomaly, the departure from IMERG's own climatology, in mm/day. Each day's departure is added and then fades over about three months, so a frame is a slowly fading memory of recent weeks, not the rain of that day; it lags the daily rain lane. The climatology period is not stated on the item page.",
        "EIC colours are 8 flat bins of the item's colour bar: -2 to -5, -5 to -10, -10 to -15, beyond -15 (drier) and 2 to 5, 5 to 10, 10 to 15, beyond 15 mm/day (wetter). Within -2 to +2 mm/day the frame is transparent: read as normal (0). A pixel's value is its bin mid value (3.5, 7.5, 12.5, 17.5), so values are steps of a binned map, not measurements.",
        f"Harmony tension in this story = |EIC anomaly| at the listening point divided by {TENSION_FULL:g} mm/day (bin mid value), clamped to 1; wetter and drier count the same; 0 inside the transparent near-normal band.",
        f"EIC frames on the globe: {len(frames)} of 365 daily frames (every 3rd day June to October, the 1st of every other month, and 31 December), each held until the next; shown at 2048 x 1024, nearest-neighbour from 3600 x 1800, so colours are exact. The EIC lane uses all daily frames.",
        "EIC lane: India land mean of the binned anomaly (0.1 deg frame pixels averaged to 0.5 deg cells inside India, cosine latitude weighted). Because near-normal pixels count as 0 and wet and dry bins cancel, the lane is a rough summary of the map, not an IMERG computation.",
        "Rain is IMERG Late Run v07 (GPM_3IMERGDL): satellite estimates with a climatological gauge adjustment, available within about a day. The Final Run with monthly gauge calibration (used for the 2019 story) ends on 30 September 2025, so the Late Run is used for all of 2025 to keep one product. Daily values over mountains carry larger errors.",
        "Onset here is a data rule on the all-India land mean (7-day mean rain at or above 5 mm/day for 15 days in a row), not the India Meteorological Department onset over Kerala.",
        f"Rain map frames are 8-day means at 0.5 deg (46 frames, the last covers 5 days); the colour scale is linear 0 to {rain_vmax:g} mm/day with a floor of 1 mm/day (99.5th percentile of the frames: {p995:.1f} mm/day).",
        "Wind is MERRA-2 reanalysis (a model) at 850 hPa, about 1.5 km up, daily means drawn as 7-day means at 1 x 1.25 deg; the lane is the Arabian Sea box 10 to 20 N, 65 to 72.5 E. Where the ground is above 850 hPa (Tibetan Plateau, high Himalaya) cells are empty.",
        "NDVI is a monthly MODIS composite: the lane holds each month's value on every day of that month (a step, not interpolated).",
        "India means use 0.5 deg cells whose centre falls inside the Natural Earth 1:50m outline of India (cosine latitude weighted).",
        f"The rain to NDVI link uses monthly means 2023-01 to 2025-09 ({nm} months, IMERG Final monthly ends 2025-09). Both follow the seasonal cycle, so the correlation mostly says that vegetation greens after the rains. Lag resolution is one month.",
        "GRACE-FO water thickness is shown on a 0.5 deg grid but its real resolution is about 300 km; it measures total water change relative to a 2004 to 2009 mean, not rain. Water map: linear -40 to 40 cm, no floor.",
    ]
    gr_missing = [MONTH_NAMES[m - 1] for m in range(1, 13) if (Y, m) not in grace]
    if gr_missing:
        gaps.append(f"GRACE-FO has no solution for {', '.join(gr_missing)} {Y}: those days are empty in the water lane, not bridged.")
    wnull = SL.gap_count(water)
    if wnull:
        gaps.append(f"Water lane: {wnull} days of {Y} fall outside GRACE-FO solution date ranges and stay empty (not bridged).")
    for nm_, ser in (("IMERG Late", rain), ("MERRA-2", as_u), ("EIC frames", eic)):
        c = SL.gap_count(ser)
        if c:
            gaps.append(f"{nm_}: {c} days without data in {Y} (left empty).")
    nd_missing = [MONTH_NAMES[m] for m in range(12) if nd_y[m] is None]
    if nd_missing:
        gaps.append("MODIS NDVI: no composite for " + ", ".join(nd_missing) + f" {Y}.")
    if eic_unknown:
        gaps.append(f"EIC frames: {eic_unknown} pixels had a colour outside the colour bar and were given the nearest bin.")
    gaps.append(f"Link strength: rain to NDVI r {lk['r']} ({lk['strength']}) at {lk['lag']} month lag, n {lk['n']}; rain to GRACE water r {lk_w.get('r')} ({lk_w.get('strength')}) at {lk_w.get('lag')} month lag, n {lk_w.get('n')}.")

    beats = [{"t": 0, "text": f"January {Y} over India. The land is dry, about {M.rnd(rmon[0], 1)} millimetres of rain a day on average. The NASA anomaly map shows where rain is above or below its usual amount."}]
    if uflip is not None:
        beats.append({"t": uflip, "text": f"{DAYS[uflip].strftime('%d %B')}: the wind over the Arabian Sea has turned westerly and holds above 5 metres per second."})
    if onset is not None:
        beats.append({"t": onset, "text": f"{DAYS[onset].strftime('%d %B')}: monsoon onset in the all-India average, rain holds at or above 5 millimetres a day."})
    beats.append({"t": kpk, "text": f"{DAYS[kpk].strftime('%d %B')}: the wettest day of the year, {rain[kpk]} millimetres averaged over India."})
    beats.append({"t": ewet, "text": f"{DAYS[ewet].strftime('%d %B')}: on the NASA anomaly map India is at its wettest compared with usual, an average of {eic[ewet]} millimetres a day above normal."})
    if eic[edry] is not None and eic[edry] <= -0.5:
        beats.append({"t": edry, "text": f"{DAYS[edry].strftime('%d %B')}: India is at its driest compared with usual on the anomaly map, {abs(eic[edry])} millimetres a day below normal."})
    beats.append({"t": mid[nmax], "text": f"{MONTH_NAMES[nmax]}: India is greenest, vegetation index {M.rnd(nd_ym[nmax], 2)}."})
    if withdraw is not None:
        beats.append({"t": withdraw, "text": f"{DAYS[withdraw].strftime('%d %B')}: the rains fade below 5 millimetres a day. June to September averaged {stats['June to September mean all-India rain (mm/day)']} millimetres a day."})
    beats.sort(key=lambda b: b["t"])
    events = [{"t": kpk, "label": "peak rain day"}, {"t": ewet, "label": "wettest vs usual (EIC)"}, {"t": mid[nmax], "label": "greenest month"}]
    for k, lab in ((onset, "monsoon onset (all-India)"), (uflip, "westerly sets in"), (withdraw, "rains fade")):
        if k is not None:
            events.append({"t": k, "label": lab})
    events.sort(key=lambda e: e["t"])

    L0, L1, G0, G1 = float(LATC[0]), float(LATC[-1]), float(LONC[0]), float(LONC[-1])
    rain_enc = SL.enc_grid(rf, 0, rain_vmax, L0, L1, G0, G1, rt, "mm/day", "observed", floor=1.0)
    nd_enc = SL.enc_grid(nd_grid, 0, 0.9, L0, L1, G0, G1, mid, "NDVI", "observed", floor=0.1)
    gr_enc = SL.enc_grid(gr_grid, -40, 40, L0, L1, G0, G1, gr_t, "cm", "observed", floor=-40)
    wind_enc = SL.enc_wind(wf_u, wf_v, float(M.WLATC[0]), float(M.WLATC[-1]), float(M.WLONC[0]), float(M.WLONC[-1]), wt, 0.25,
                           "MERRA-2 850 hPa wind, 7-day means (reanalysis model)")
    valid = [v for v in rain if v is not None]
    stops = [[*b[0], b[3]] for b in EIC_BINS]
    obj = {
        "title": f"India monsoon {Y} with NASA rain anomaly frames",
        "script": "c3_monsoon_eic.py",
        "timebase": "day", "t0": f"{Y}-01-01T00:00Z", "step_s": 86400, "n": NT,
        "region": {"lat0": 5, "lat1": 35, "lon0": 65, "lon1": 100},
        "hero": "rain", "partner": "green",
        "link": lk,
        "links_extra": {"rain_water": lk_w, "rain_eic_same_day": {"r": None if r_eic is None else round(r_eic, 3), "n": n_eic,
                        "method": "Pearson r, same day, all-India rain (IMERG Late) vs India mean EIC anomaly; descriptive only, the EIC map fades over months"}},
        "hero_norm": {"min": round(min(valid), 2), "max": round(max(valid), 2),
                      "method": f"min..max of the hero series itself (all-India land mean daily rain, IMERG Late, {Y})"},
        "stats": stats, "gaps": gaps, "beats": beats, "events": events,
        "bands": [{"t0": t_jun1, "t1": t_oct1 - 1, "label": "June to September monsoon season"}],
        "monthly": {"months": [f"{y}-{m:02d}" for y, m in LINK_MONTHS], "rain_mm_day": [M.rnd(x) for x in rain_m],
                    "ndvi": [M.rnd(x, 4) for x in nd_m], "grace_cm": [M.rnd(x) for x in gr_m]},
        "sources": [
            {"name": "Seasonal Global Precipitation Variation from the Global Precipitation Measurement Constellation (SVS 4897), flatalpha frames",
             "producer": "NASA Scientific Visualization Studio, shown in the NASA Earth Information Center; data NASA GPM IMERG",
             "resolution": "3600 x 1800 global equirectangular, daily, shown at 2048 x 1024", "kind": "observed",
             "period": f"{Y}", "baseline": "IMERG climatology (period not stated); anomaly fades over about three months",
             "url": "https://svs.gsfc.nasa.gov/4897"},
            {"name": "GPM IMERG Late Precipitation L3 1 day 0.1 x 0.1 deg V07 (GPM_3IMERGDL)", "producer": "NASA GPM (Huffman et al.), distributed by GES DISC",
             "resolution": "0.1 deg daily, shown at 0.5 deg, 8-day map frames", "kind": "observed", "period": f"{Y}",
             "baseline": "none (cycle: own min..max)", "url": "https://doi.org/10.5067/GPM/IMERGDL/DAY/07"},
            {"name": "GPM IMERG Final Precipitation L3 1 month 0.1 x 0.1 deg V07 (GPM_3IMERGM)", "producer": "NASA GPM (Huffman et al.), distributed by GES DISC",
             "resolution": "0.1 deg monthly, India mean at 0.5 deg", "kind": "observed", "period": "2023-01 to 2025-09 (link only)",
             "baseline": "none", "url": "https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07"},
            {"name": "MERRA-2 tavg1_2d_slv_Nx hourly single-level diagnostics, U850 and V850 (M2T1NXSLV v5.12.4)", "producer": "NASA GMAO, distributed by GES DISC",
             "resolution": "0.5 x 0.625 deg hourly, shown at 1 x 1.25 deg, daily lane, 7-day map frames", "kind": "model", "period": f"{Y}",
             "baseline": "none", "url": "https://doi.org/10.5067/VJAFPLI1CSIV"},
            {"name": "MODIS/Terra Vegetation Indices Monthly L3 Global 0.05 deg CMG V061 (MOD13C2)", "producer": "NASA LP DAAC (Didan)",
             "resolution": "0.05 deg monthly, shown at 0.5 deg", "kind": "observed", "period": f"2023-01 to 2025-12 (map {Y})",
             "baseline": "none", "url": "https://doi.org/10.5067/MODIS/MOD13C2.061"},
            {"name": "JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent Water Height RL06.3 CRI v04", "producer": "NASA JPL, distributed by PO.DAAC",
             "resolution": "about 3 deg (300 km) mascons on a 0.5 deg grid, monthly", "kind": "observed", "period": f"2023-01 to 2025-12 (map {Y})",
             "baseline": "anomaly relative to the 2004.0 to 2009.999 mean", "url": "https://doi.org/10.5067/TEMSC-3JC634"},
            {"name": "Natural Earth 1:50m admin 0 countries (India outline for land means)", "producer": "Natural Earth",
             "resolution": "1:50 million", "kind": "observed", "period": "static", "baseline": "none",
             "url": "https://www.naturalearthdata.com/downloads/50m-cultural-vectors/"},
        ],
        "layers": [
            {"id": "rain", "type": "field", "name": "Rain", "palette": "rain",
             "what": "Daily rain, NASA GPM IMERG Late Run v07 (observed, satellite); lane = all-India land mean",
             "color": "#4aa3ff", "unit": "mm/day", "series": rain, "grid": rain_enc},
            {"id": "eic", "type": "eicframes", "name": "NASA EIC rain anomaly",
             "what": "Rain compared with usual, NASA SVS / Earth Information Center item 4897 (IMERG anomaly, fades over about three months); lane = India land mean",
             "color": "#0b7d76", "unit": "mm/day vs usual", "series": eic, "source": "SVS/EIC 4897",
             "frames": [{"t": f["t"], "img": f["img"]} for f in frames],
             "frame_dates": [f["date"] for f in frames],
             "projection": {"type": "equirectangular", "lon0": -180, "lon1": 180, "lat0": 90, "lat1": -90, "width": 2048, "height": 1024,
                            "note": "row 0 = 90 N, column 0 = 180 W; re-centred from the original frames"},
             "colorbar": {"stops": stops, "unit": "mm/day",
                          "bins": [[*b[0], b[1], b[2]] for b in EIC_BINS],
                          "transparent": "within -2 to +2 mm/day of usual (near normal), value 0",
                          "match": "exact RGB of the frame pixel (indexed PNG, 8 colours + transparent)",
                          "tension": f"min(1, |value| / {TENSION_FULL:g})"}},
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
