"""E5 Po Valley COVID lockdown, 2020-01-01 .. 2020-05-31 (daily), N Italy.

Layers
  no2       NASA OMI/Aura OMNO2d v003 tropospheric NO2 column (cloud-screened), 0.25 deg, observed. Same encoding as the
            Wuhan fog: 15-day centred composites, small holes (<= 1 deg) filled, byte = 1 + sqrt(min(col/5e14, 80)/80)*254.
            Lane: Milan box (5x5 cells), daily pooled clear-sky pixels (null on cloudy days); normal = 2015-2019 mean on the
            same calendar dates (pixels pooled over +/-7 days, like wuhan_baseline.py), band = min..max of those years.
  stations  EEA E1a (verified) hourly NO2 at urban stations of Milan, Turin, Brescia, Bologna, Venice -> daily means (ug/m3).
  wind      ERA5 10 m wind (model, via Open-Meteo archive), 1 deg grid over N Italy, daily vector means; lane = Milan daily
            mean wind speed.
Link: daily ground NO2 (mean of the 5 cities) vs Milan wind speed, 2020 and 2015-2019 (Jan-May) separately.

Usage: python e5_po_valley.py
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402
import eea_lib as EEA  # noqa: E402

ID = "e5_po_valley"
D0, D1 = dt.date(2020, 1, 1), dt.date(2020, 5, 31)
DAYS = [D0 + dt.timedelta(k) for k in range((D1 - D0).days + 1)]
N_T = len(DAYS)
YEARS_BASE = [2015, 2016, 2017, 2018, 2019]
EV = {"2020-02-23": "first Lombardy measures (11 towns closed)", "2020-03-09": "national lockdown", "2020-05-04": "phase 2 reopening"}
T = lambda iso: (dt.date.fromisoformat(iso) - D0).days

# ---------------------------------------------------------------- OMI
# OMNO2d grid 720 x 1440, centres -89.875.., -179.875..; square tile rows 524..559 (41.125N..49.875N), cols 742..777 (5.625E..14.375E)
I0, J0, N = 524, 742, 36
LAT0, LON0, STEP = -89.875 + I0 * .25, -179.875 + J0 * .25, 0.25
VAR = "/HDFEOS/GRIDS/ColumnAmountNO2/Data_Fields/ColumnAmountNO2TropCloudScreened"
MILAN = (45.464, 9.190)
WIN, HALF, R_BOX, MIN_OBS, MIN_YEARS = 15, 7, 2, 5, 3
OMI_DIR = SL.cache_dir(ID) / "omi"


def omi_granules(a, b):
    q = (f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name=OMNO2d&version=003&temporal={a},{b}T23:59:59Z"
         "&page_size=500&sort_key=start_date")
    raw = subprocess.run(["curl", "-sf", "--retry", "5", q], capture_output=True, check=True).stdout
    out = []
    for e in json.loads(raw)["feed"]["entry"]:
        u = next((l["href"] for l in e["links"] if l["href"].startswith("https://opendap.earthdata.nasa.gov")), None)
        if u:
            out.append((e["time_start"][:10], u))
    return out


def omi_fetch_one(job):
    day, url = job
    npy = OMI_DIR / f"omi_{day}.npy"
    if npy.exists():
        return day, "cached"
    ce = urllib.parse.quote(f"{VAR}[{I0}:1:{I0 + N - 1}][{J0}:1:{J0 + N - 1}]", safe="")
    try:
        p = SL.fetch(f"{url}.dap.nc4?dap4.ce={ce}", ID, name=f"omi/tmp_{day}.nc4", token=True, min_bytes=4000)
    except RuntimeError as e:
        return day, "FAILED " + str(e)[:60]
    return day, str(p)


def omi_download():
    OMI_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []
    for y in YEARS_BASE + [2020]:
        a, b = dt.date(y - 1, 12, 24).isoformat(), dt.date(y, 6, 8).isoformat()
        jobs += omi_granules(a, b)
    todo = [j for j in jobs if not (OMI_DIR / f"omi_{j[0]}.npy").exists()]
    print(f"OMI: {len(jobs)} days listed, {len(todo)} to fetch", flush=True)
    import netCDF4
    with ThreadPoolExecutor(6) as ex:
        for day, res in ex.map(omi_fetch_one, todo):
            if not res.endswith(".nc4"):
                print(" ", day, res, flush=True)
                continue
            ds = netCDF4.Dataset(res)
            v = None
            def walk(g):
                nonlocal v
                for name, var in g.variables.items():
                    if name.endswith("ColumnAmountNO2TropCloudScreened"):
                        v = var[:]
                for s in g.groups.values():
                    walk(s)
            walk(ds)
            ds.close()
            a = np.ma.filled(np.ma.masked_invalid(v).astype(np.float32), np.nan)
            a[a < -1e29] = np.nan
            np.save(OMI_DIR / f"omi_{day}.npy", a)
            os.remove(res)


def omi_tile(d):
    f = OMI_DIR / f"omi_{d.isoformat()}.npy"
    return np.load(f) if f.exists() else None


def omi_grid_2020():
    """Wuhan method: 15-day centred composite (>= 3 obs), small holes filled, encoded uint8 (days x n x n)."""
    m = WIN // 2
    days = [D0 + dt.timedelta(k) for k in range(-m, N_T + m)]
    g = np.array([t if (t := omi_tile(d)) is not None else np.full((N, N), np.nan, np.float32) for d in days])
    comp = []
    for k in range(m, len(g) - m):
        w = g[k - m: k + m + 1]
        n = np.sum(~np.isnan(w), 0)
        with np.errstate(all="ignore"):
            c = np.nanmean(w, 0)
        c[n < 3] = np.nan
        comp.append(c)
    comp = np.array(comp)
    out = comp.copy()
    for f in (2, 4):     # close holes <= 1 degree only (OMI row-anomaly stripes)
        t, h, w = out.shape
        c = out.reshape(t, h // f, f, w // f, f)
        with np.errstate(all="ignore"):
            c = np.nanmean(c, axis=(2, 4))
        up = np.repeat(np.repeat(c, f, 1), f, 2)
        hole = np.isnan(out)
        out[hole] = up[hole]
    u = out / 5e14
    q = np.where(np.isnan(u), 0, 1 + np.round(np.sqrt(np.clip(np.nan_to_num(u), 0, 80) / 80) * 254)).astype(np.uint8)
    return q, float(np.isnan(u).mean())


def omi_box(d, lat, lon):
    t = omi_tile(d)
    if t is None:
        return np.array([])
    i, j = int(round((lat - LAT0) / STEP)), int(round((lon - LON0) / STEP))
    b = t[i - R_BOX: i + R_BOX + 1, j - R_BOX: j + R_BOX + 1].ravel()
    return b[~np.isnan(b)]


def omi_series(lat, lon):
    """2020 daily (pooled box, that day only), per-year +/-7 day pooled values for 2015-2019 and 2020 on the same calendar dates."""
    daily = []
    for d in DAYS:
        v = omi_box(d, lat, lon)
        daily.append(round(float(v.mean() / 1e15), 2) if v.size >= MIN_OBS else None)
    pooled = {}
    for y in YEARS_BASE + [2020]:
        ser = []
        for d in DAYS:
            try:
                dy = d.replace(year=y)
            except ValueError:      # Feb 29 in a non-leap year: no such date
                ser.append(None)
                continue
            v = np.concatenate([omi_box(dy + dt.timedelta(k), lat, lon) for k in range(-HALF, HALF + 1)])
            ser.append(round(float(v.mean() / 1e15), 2) if v.size >= MIN_OBS else None)
        pooled[y] = ser
    return daily, pooled


def normal_band(per_year):
    normal, band = [], []
    for k in range(N_T):
        v = [per_year[y][k] for y in YEARS_BASE if per_year[y][k] is not None]
        ok = len(v) >= MIN_YEARS
        normal.append(round(float(np.mean(v)), 2) if ok else None)
        band.append([round(float(min(v)), 2), round(float(max(v)), 2)] if ok else None)
    return normal, band


# ---------------------------------------------------------------- EEA stations
CITIES = [("Milan", "Milano (greater city)"), ("Turin", "Torino"), ("Brescia", "Brescia"), ("Bologna", "Bologna"), ("Venice", "Venezia")]
MIN_HOURS = 18           # valid hours for a daily mean
MIN_COVER = 0.75         # station kept if it has a daily mean on >= 75% of days in every Jan-May 2015..2020


def jan_may(y):
    return pd.date_range(f"{y}-01-01", f"{y}-05-31", freq="D")


def eea_daily():
    meta = EEA.meta(ID)
    cities = {}
    for name, eea_city in CITIES:
        sts = []
        for u in EEA.urls("IT", eea_city, ID):
            code = EEA.eoi(u)
            mt = meta.get(code)
            if mt is None or mt[4] != "urban":
                continue
            # Milan list = greater city: keep stations inside the Milan municipality only (names start with MILANO)
            if name == "Milan" and not mt[0].upper().startswith("MILANO"):
                continue
            s = EEA.hourly(u, ID)
            cnt = s.groupby(s.index.floor("D")).count()
            day = s.groupby(s.index.floor("D")).mean()[cnt >= MIN_HOURS]
            cover = min(day.reindex(jan_may(y)).notna().mean() for y in YEARS_BASE + [2020])
            print(f"  {name:8s} {code} {mt[0][:34]:34s} {mt[3]:10s} cover {cover:.2f}", flush=True)
            if cover >= MIN_COVER:
                sts.append({"code": code, "name": mt[0], "lat": mt[1], "lon": mt[2], "type": mt[3], "day": day})
        if sts:
            cities[name] = sts
    return cities


def city_mean(sts, idx):
    a = np.array([s["day"].reindex(idx).values for s in sts], dtype=float)
    with np.errstate(all="ignore"):
        m = np.nanmean(a, 0)
    return m


# ---------------------------------------------------------------- wind (ERA5 via Open-Meteo)
OM = "https://archive-api.open-meteo.com/v1/archive"
WLAT = [43.0, 44.0, 45.0, 46.0, 47.0]
WLON = [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0]


def om_hourly(lats, lons, a, b, name):
    url = (f"{OM}?latitude={','.join(f'{x:g}' for x in lats)}&longitude={','.join(f'{x:g}' for x in lons)}"
           f"&start_date={a}&end_date={b}&hourly=wind_speed_10m,wind_direction_10m&wind_speed_unit=ms&models=era5&timezone=GMT")
    js = SL.fetch_json(url, ID, name=name, min_bytes=1000)
    return js if isinstance(js, list) else [js]


def uv_daily(js):
    """hourly speed + direction -> daily mean u, v, scalar speed (needs >= 20 hours)."""
    t = pd.DatetimeIndex(js["hourly"]["time"])
    sp = np.array([np.nan if x is None else x for x in js["hourly"]["wind_speed_10m"]], float)
    di = np.array([np.nan if x is None else x for x in js["hourly"]["wind_direction_10m"]], float)
    u, v = -sp * np.sin(np.radians(di)), -sp * np.cos(np.radians(di))
    df = pd.DataFrame({"u": u, "v": v, "s": sp}, index=t)
    g = df.groupby(df.index.floor("D"))
    out = g.mean()
    out[g.count()["s"] < 20] = np.nan
    return out


def wind_grid():
    lats = [la for la in WLAT for _ in WLON]
    lons = [lo for _ in WLAT for lo in WLON]
    js = om_hourly(lats, lons, D0.isoformat(), D1.isoformat(), "om_grid_2020.json")
    U = np.full((N_T, len(WLAT), len(WLON)), np.nan)
    V = U.copy()
    idx = pd.DatetimeIndex([pd.Timestamp(d) for d in DAYS])
    for k, p in enumerate(js):
        d = uv_daily(p).reindex(idx)
        i, j = divmod(k, len(WLON))
        U[:, i, j], V[:, i, j] = d.u.values, d.v.values
    return U, V


def wind_milan():
    out = {}
    for y in YEARS_BASE + [2020]:
        js = om_hourly([MILAN[0]], [MILAN[1]], f"{y}-01-01", f"{y}-05-31", f"om_milan_{y}.json")[0]
        out[y] = uv_daily(js)["s"]
    return out


# ---------------------------------------------------------------- main
def same_dates(series_by_year):
    """{year: pd.Series by date} -> per-year lists aligned on the 2020 calendar dates (Feb 29 only exists in 2016/2020)."""
    res = {}
    for y, s in series_by_year.items():
        vals = []
        for d in DAYS:
            try:
                v = s.get(pd.Timestamp(d.replace(year=y)), np.nan)
            except ValueError:
                v = np.nan
            vals.append(None if v is None or not np.isfinite(v) else float(v))
        res[y] = vals
    return res


def mean_ok(vals):
    v = [x for x in vals if x is not None]
    return float(np.mean(v)) if v else None


def matched_pct(a, b, idx):
    k = [i for i in idx if a[i] is not None and b[i] is not None]
    if not k:
        return None, 0
    return SL.pct(np.mean([a[i] for i in k]), np.mean([b[i] for i in k])), len(k)


def main():
    omi_download()

    # ---- OMI
    q, nodata = omi_grid_2020()
    print(f"OMI composite no-data after small-hole fill: {100 * nodata:.1f}%")
    omi_daily, omi_pooled = omi_series(*MILAN)
    omi_norm, omi_band = normal_band(omi_pooled)

    # ---- EEA
    cities = eea_daily()
    city_years = {}
    for name, sts in cities.items():
        city_years[name] = {y: pd.Series(city_mean(sts, jan_may(y)), index=jan_may(y)) for y in YEARS_BASE + [2020]}
    names = list(cities)
    per_city = {c: same_dates(city_years[c]) for c in names}

    def all_cities(y):   # mean of the city means, only on days with every city present (no composition jumps)
        out = []
        for k in range(N_T):
            v = [per_city[c][y][k] for c in names]
            out.append(None if any(x is None for x in v) else round(float(np.mean(v)), 2))
        return out
    st = {y: all_cities(y) for y in YEARS_BASE + [2020]}
    st_norm, st_band = normal_band(st)
    hero = st[2020]

    # ---- wind
    U, V = wind_grid()
    wm = same_dates(wind_milan())
    w20 = [None if x is None else round(x, 2) for x in wm[2020]]
    w_norm, w_band = normal_band({y: [None if x is None else round(x, 2) for x in wm[y]] for y in wm})

    # ---- link
    nn = lambda a: np.array([np.nan if x is None else x for x in a], float)
    lk20 = SL.link(nn(hero), nn(w20), 3, "day", "Pearson r, daily mean ground NO2 (5 cities, EEA) vs ERA5 Milan daily wind speed, "
                   "2020-01-01..05-31, lags -3..3 days", sign_hint=-1)
    # 2015-2019: years concatenated with a 4-day NaN spacer so lagged pairs never cross years
    sp = [np.nan] * 4
    hb = np.concatenate([np.r_[nn(st[y]), sp] for y in YEARS_BASE])
    wb = np.concatenate([np.r_[nn(wm[y]), sp] for y in YEARS_BASE])
    lkb = SL.link(hb, wb, 3, "day", "same, Jan-May 2015-2019 pooled", sign_hint=-1)
    pre = list(range(0, T("2020-02-23")))
    lock = list(range(T("2020-03-09"), T("2020-05-04") + 1))
    r_pre, n_pre = SL.pearson(nn(hero)[pre], nn(w20)[pre])
    r_lock, n_lock = SL.pearson(nn(hero)[lock], nn(w20)[lock])
    # anomalies vs the normal remove the shared Jan->May season (NO2 falls, wind rises in spring)
    an_h = nn(hero) - nn(st_norm)
    an_w = nn(w20) - nn(w_norm)
    r_an20, n_an20 = SL.pearson(an_h, an_w)
    lk20.update({"r_2015_2019": lkb["r"], "lag_2015_2019": lkb["lag"], "n_2015_2019": lkb["n"], "strength_2015_2019": lkb["strength"],
                 "curve_2015_2019": lkb["curve"],
                 "r_2020_before_lockdown": None if r_pre is None else round(r_pre, 3), "n_2020_before_lockdown": n_pre,
                 "r_2020_lockdown": None if r_lock is None else round(r_lock, 3), "n_2020_lockdown": n_lock,
                 "r_2020_anomalies_lag0": None if r_an20 is None else round(r_an20, 3), "n_2020_anomalies": n_an20})

    # ---- hero norm: 2015-2019 same dates, daily station NO2
    base_vals = [x for y in YEARS_BASE for x in st[y] if x is not None]
    hero_norm = SL.norm_stats(base_vals, YEARS_BASE, "mean and sd of daily ground NO2 (mean of 5 cities, EEA), Jan 1..May 31 of 2015-2019")
    hero_norm["base"] = st_norm

    # ---- stats
    before = list(range(0, T("2020-02-23")))
    s_lock, n1 = matched_pct(hero, st_norm, lock)
    s_before, n2 = matched_pct(hero, st_norm, before)
    o_lock, n3 = matched_pct(omi_daily, omi_norm, lock)
    o_before, n4 = matched_pct(omi_daily, omi_norm, before)
    o_lock_pooled, _ = matched_pct(omi_pooled[2020], omi_norm, lock)
    w_lock, _ = matched_pct(w20, w_norm, lock)
    mil = [None if x is None else round(x, 2) for x in per_city["Milan"][2020]] if "Milan" in per_city else None
    mil_n, _ = normal_band({y: per_city["Milan"][y] for y in YEARS_BASE}) if mil else (None, None)
    m_lock, _ = matched_pct(mil, mil_n, lock) if mil else (None, 0)
    lock_mean = mean_ok([hero[k] for k in lock])
    norm_lock = mean_ok([st_norm[k] for k in lock if hero[k] is not None])
    lo_day = min((k for k in lock if hero[k] is not None), key=lambda k: hero[k])
    stats = {
        "ground NO2, lockdown Mar 9 to May 4 (ug/m3)": round(lock_mean, 1),
        "ground NO2, 2015-19 same dates (ug/m3)": round(norm_lock, 1),
        "ground NO2 lockdown vs 2015-19 (%)": s_lock,
        "ground NO2 Jan 1 to Feb 22 vs 2015-19 (%)": s_before,
        "Milan stations lockdown vs 2015-19 (%)": m_lock,
        "OMI satellite NO2 over Milan, lockdown vs 2015-19 (%)": o_lock,
        "OMI lockdown vs 2015-19, days compared": n3,
        "OMI satellite NO2, Jan 1 to Feb 22 vs 2015-19 (%)": o_before,
        "OMI lockdown vs 2015-19, 15-day pooled (%)": o_lock_pooled,
        "lowest lockdown day ground NO2 (ug/m3)": round(hero[lo_day], 1), "lowest lockdown day": DAYS[lo_day].isoformat(),
        "Milan wind, lockdown vs 2015-19 (%)": w_lock,
        "link NO2 vs wind 2020 (r)": lk20["r"], "link NO2 vs wind 2015-19 (r)": lkb["r"],
        "link 2020 before measures (r)": lk20["r_2020_before_lockdown"], "link 2020 lockdown (r)": lk20["r_2020_lockdown"],
        "OMI cloudy days over Milan in 2020 (no value)": SL.gap_count(omi_daily),
    }

    ncity = {c: len(s) for c, s in cities.items()}
    station_list = [f"{c}: " + ", ".join(f"{s['name']} ({s['code']}, {s['type']})" for s in sts) for c, sts in cities.items()]
    gaps = [
        f"OMI satellite NO2 needs clear sky: the Milan lane is empty on {SL.gap_count(omi_daily)} of {N_T} days (clouds, fog, snow); those days stay empty.",
        "The NO2 map is a 15-day centred composite of OMI overpasses (needed to see anything in a cloudy winter); holes up to 1 degree are filled from neighbours, larger holes stay empty.",
        "OMI normal: mean of 2015-2019 on the same calendar dates, pixels pooled over +/-7 days in a 5x5 cell box (about 125 km); band = lowest..highest of those years.",
        "Ground stations: daily mean of hourly EEA E1a (verified) values, a day needs at least 18 valid hours; only urban stations with daily data on at least 75% of days in every Jan-May 2015-2020 are used, so the set is the same in every year.",
        "The ground series is the mean of the 5 city means and is left empty on any day a city is missing (no mixing of station sets).",
        "Feb 29 exists only in 2016 and 2020, so there is no 2015-2019 normal for that day.",
        "Wind is ERA5 reanalysis (a model), not a measurement, read at 1 degree from the Open-Meteo archive.",
        "Winter to spring, NO2 falls and wind rises every year, so part of the negative NO2 vs wind link is the season itself; the anomaly correlation (each minus its 2015-19 normal) is reported too.",
        "EEA times are taken as the station time zone (UTC+01, no daylight saving) before averaging to days.",
    ]
    beats = [
        {"t": 0, "text": f"January 2020 in the Po Valley. Ground NO2 averages {round(mean_ok(hero[:31]), 1)} micrograms per cubic metre across Milan, Turin, Brescia, Bologna and Venice, {abs(s_before):.0f} percent {'below' if s_before < 0 else 'above'} the 2015 to 2019 normal for those dates, before any measures."},
        {"t": T("2020-02-23"), "text": "February 23: first measures in Lombardy, eleven towns closed, schools shut."},
        {"t": T("2020-03-09"), "text": f"March 9: national lockdown. Ground NO2 during the lockdown averages {round(lock_mean, 1)}, against {round(norm_lock, 1)} on the same dates in 2015 to 2019: {-s_lock:.0f} percent lower."},
        {"t": lo_day, "text": f"{DAYS[lo_day].strftime('%B %d')}: lowest lockdown day, {round(hero[lo_day], 1)} micrograms per cubic metre."},
        {"t": T("2020-03-25"), "text": f"From space, OMI sees NO2 over Milan {-o_lock:.0f} percent below normal during the lockdown, on the {n3} clear days it could see."},
        {"t": T("2020-04-15"), "text": f"Wind dilutes NO2: in 2015 to 2019 daily ground NO2 and Milan wind speed correlate weakly, r {lkb['r']}. In 2020 r is {lk20['r']}, and {lk20['r_2020_lockdown']} during the lockdown: the link holds. The drop is not the wind: Milan wind during the lockdown was within {abs(w_lock):.0f} percent of normal ({w_lock:+.1f} percent)."},
        {"t": T("2020-05-04"), "text": "May 4: phase 2, factories and building sites reopen; traffic starts to return."},
    ]
    beats.sort(key=lambda b: b["t"])
    obj = {
        "title": "Po Valley lockdown: the air goes quiet",
        "timebase": "day", "t0": "2020-01-01T00:00Z", "step_s": 86400, "n": N_T,
        "region": {"lat0": 43.0, "lat1": 47.5, "lon0": 6.0, "lon1": 14.5},
        "hero": "stations", "partner": "wind", "link": lk20, "hero_norm": hero_norm,
        "stats": stats, "gaps": gaps, "beats": beats,
        "events": [{"t": T(k), "label": v} for k, v in EV.items()],
        "bands": [{"t0": T("2020-03-09"), "t1": T("2020-05-04"), "label": "national lockdown"}],
        "sources": [
            {"name": "OMI/Aura NO2 tropospheric column, daily L3 global 0.25 deg (OMNO2d v003)", "producer": "NASA GSFC / KNMI, GES DISC",
             "resolution": "0.25 deg, daily (one overpass about 13:45 local)", "kind": "observed", "period": "2020-01-01 to 2020-05-31",
             "baseline": "2015-2019, same calendar dates", "url": "https://doi.org/10.5067/Aura/OMI/DATA3007"},
            {"name": "EEA air quality e-reporting, verified hourly NO2 (E1a)", "producer": "European Environment Agency, data from ARPA Lombardia, ARPA Piemonte, ARPAE Emilia-Romagna, ARPA Veneto via ISPRA",
             "resolution": "hourly, urban stations", "kind": "observed", "period": "2020-01-01 to 2020-05-31",
             "baseline": "2015-2019, same calendar dates", "url": "https://eeadmz1-downloads-webapp.azurewebsites.net/"},
            {"name": "ERA5 hourly 10 m wind (via Open-Meteo historical weather API)", "producer": "ECMWF Copernicus Climate Change Service, served by Open-Meteo",
             "resolution": "0.25 deg model grid read at 1 deg, hourly, averaged to days", "kind": "model", "period": "2015-2020, Jan to May",
             "baseline": "2015-2019, same calendar dates", "url": "https://open-meteo.com/en/docs/historical-weather-api"},
        ],
        "layers": [
            {"id": "stations", "type": "pillars", "name": "Ground NO2", "unit": "ug/m3", "color": "#ffb347",
             "what": "Daily mean NO2 at urban stations of 5 Po Valley cities, EEA verified hourly data (observed)",
             "series": hero, "baseline": st_norm, "band": st_band,
             "stations": [{"id": c.lower(), "name": f"{c} ({ncity[c]} station{'s' if ncity[c] > 1 else ''})",
                           "lat": round(float(np.mean([s["lat"] for s in sts])), 4), "lon": round(float(np.mean([s["lon"] for s in sts])), 4),
                           "series": [None if x is None else round(x, 1) for x in per_city[c][2020]],
                           "members": [{"code": s["code"], "name": s["name"], "type": s["type"], "lat": s["lat"], "lon": s["lon"]} for s in sts]}
                          for c, sts in cities.items()]},
            {"id": "no2", "type": "no2fog", "name": "NO2 from space", "unit": "1e15 molecules/cm2", "color": "#c98bff",
             "what": "Tropospheric NO2 column, NASA OMI on Aura, cloud-screened (observed); lane = Milan area, clear days only",
             "no2": __import__("base64").b64encode(q.tobytes()).decode(), "n": N, "lat0": LAT0, "lon0": LON0, "step": STEP, "days": N_T,
             "encoding": "0 = no data; 1 + sqrt(min(col/5e14, 80)/80)*254; rows south to north; 15-day centred composites",
             "series": omi_daily, "baseline": omi_norm, "band": omi_band},
            {"id": "wind", "type": "streaks", "name": "Wind", "unit": "m/s", "color": "#8fd3ff",
             "what": "10 m wind, ERA5 reanalysis (model), daily mean; lane = Milan wind speed",
             "wind": SL.enc_wind(U, V, WLAT[0], WLAT[-1], WLON[0], WLON[-1], list(range(N_T)), scale=0.1,
                                 source="ERA5 10 m wind, daily vector mean (reanalysis model, via Open-Meteo)"),
             "series": w20, "baseline": w_norm, "band": w_band},
        ],
        "stations_used": station_list,
        "script": "e5_po_valley.py",
    }
    SL.write_story(ID, obj)


if __name__ == "__main__":
    main()
