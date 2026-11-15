"""E2 Hurricane Ian landfall, SW Florida, 2022-09-23 00Z .. 2022-10-01 23Z, hourly steps (n = 216).

Layers
  track     IBTrACS v04r01 (NHC best track inside IBTrACS), 3-hourly positions (6-hourly best track + IBTrACS interpolation, flagged)
  wind      ERA5 10 m wind (model) via Open-Meteo: series at the Fort Myers grid cell (hero), streaks grid 0.5 deg 3-hourly
  surge     NOAA CO-OPS water level above MHHW, 6-minute averaged to hourly (hour = null if < 6 of 10 samples), 10 gauges;
            series = Fort Myers 8725520 (complete record, it recorded the surge peak)
  pressure  ERA5 surface pressure (model): series at Fort Myers, field grid 0.5 deg 3-hourly (palette cold)
  rain      GPM IMERG V07B half-hourly (Final run, observed satellite estimate) via GES DISC OPeNDAP, 0.2 deg 3-hourly frames;
            series = mean hourly rain rate over SW Florida (25.8-27.6N, 82.6-80.8W, land and sea)

Run: /Users/mykhayloolefirenko/.venvs/omi/bin/python data-pipeline/e2_ian.py
"""
import csv
import datetime as dt
import json
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402

ID = "e2_ian"
T0 = dt.datetime(2022, 9, 23, tzinfo=dt.timezone.utc)
N = 9 * 24
FMY = (26.648, -81.871)  # Fort Myers gauge 8725520
OM = "https://archive-api.open-meteo.com/v1/archive"
COOPS = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
IBT = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NA.list.v04r01.csv"
GAUGES = ["8725520", "8725110", "8723970", "8724580", "8726384", "8726520", "8726607", "8726724", "8727520", "8721604", "8720218"]
LAT_G = np.arange(24.0, 30.01, 0.5)
LON_G = np.arange(-86.0, -78.99, 0.5)
SWFL = (25.8, 27.6, -82.6, -80.8)


def step(t):
    return (t - T0).total_seconds() / 3600


# ---------------------------------------------------------------- IBTrACS
def track():
    p = SL.fetch(IBT, ID, name="ibtracs_NA.csv", min_bytes=50_000_000)
    rows = []
    with open(p, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["SEASON"] == "2022" and row["NAME"] == "IAN":
                rows.append(row)
    out, landfalls = [], []
    for row in rows:
        t = dt.datetime.strptime(row["ISO_TIME"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc)
        k = step(t)
        if not (0 <= k < N):
            continue
        w = row["USA_WIND"].strip()
        pr = row["USA_PRES"].strip()
        interp = row["IFLAG"].strip()[:1] in ("P", "I")  # first char = USA: O synoptic fix, V extra fix (e.g. landfall), P/I interpolated
        out.append({"t": round(k, 2), "lat": float(row["LAT"]), "lon": float(row["LON"]),
                    "wind_kt": int(w) if w else None, "pres_hpa": int(pr) if pr else None,
                    "status": row["USA_SSHS"].strip(), "interpolated": interp})
        if row["USA_RECORD"].strip() == "L":
            landfalls.append(out[-1])
    return out, landfalls


# ---------------------------------------------------------------- Open-Meteo ERA5
def om(lats, lons, a, b, var, name):
    url = (f"{OM}?latitude={','.join(f'{x:.2f}' for x in lats)}&longitude={','.join(f'{x:.2f}' for x in lons)}"
           f"&start_date={a}&end_date={b}&hourly={var}&models=era5&wind_speed_unit=ms&timezone=GMT")
    d = SL.fetch_json(url, ID, name=name)
    return d if isinstance(d, list) else [d]


def era5_grid():
    LA, LO = np.meshgrid(LAT_G, LON_G, indexing="ij")
    la, lo = LA.ravel(), LO.ravel()
    ws, wd, ps = [], [], []
    for i in range(0, len(la), 50):
        d = om(la[i:i + 50], lo[i:i + 50], "2022-09-23", "2022-10-01", "wind_speed_10m,wind_direction_10m,surface_pressure", f"era5_grid_{i}.json")
        for x in d:
            h = x["hourly"]
            ws.append(h["wind_speed_10m"]); wd.append(h["wind_direction_10m"]); ps.append(h["surface_pressure"])
    f = lambda a: np.array(a, float).T.reshape(N, len(LAT_G), len(LON_G))  # noqa: E731
    return f(ws), f(wd), f(ps)


def era5_point():
    d = om([FMY[0]], [FMY[1]], "2022-09-23", "2022-10-01", "wind_speed_10m,wind_gusts_10m,surface_pressure", "era5_fmy.json")[0]
    h = d["hourly"]
    return (np.array(h["wind_speed_10m"], float), np.array(h["surface_pressure"], float), (d["latitude"], d["longitude"]))


def era5_baseline():
    vals = []
    per_step = []
    for y in range(2017, 2022):
        d = om([FMY[0]], [FMY[1]], f"{y}-09-23", f"{y}-10-01", "wind_speed_10m", f"era5_fmy_{y}.json")[0]
        v = np.array(d["hourly"]["wind_speed_10m"], float)
        vals.append(v)
    a = np.array(vals)
    return a, np.nanmean(a, 0)


# ---------------------------------------------------------------- CO-OPS
def coops(station, product):
    url = (f"{COOPS}?product={product}&station={station}&begin_date=20220923&end_date=20221001%2023:59"
           f"&datum=MHHW&units=metric&time_zone=gmt&format=json&application=earthjukebox")
    d = SL.fetch_json(url, ID, name=f"{product}_{station}.json")
    if "error" in d:
        return None, None, None
    rows = d.get("data") or d.get("predictions")
    six = np.full(N * 10, np.nan)
    for r in rows:
        t = dt.datetime.strptime(r["t"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
        k = int(round((t - T0).total_seconds() / 360))
        if 0 <= k < N * 10 and r["v"] not in ("", None):
            six[k] = float(r["v"])
    blocks = six.reshape(N, 10)
    ok = np.isfinite(blocks).sum(1)
    with np.errstate(all="ignore"):
        hourly = np.where(ok >= 6, np.nanmean(blocks, 1), np.nan)
    return d.get("metadata"), hourly, six


# ---------------------------------------------------------------- IMERG
def imerg():
    # V07 grid 3600 lon x 1800 lat, 0.1 deg, centres -179.95.., -89.95..; subset 24..30N, -86..-79
    i0, i1, j0, j1 = 940, 1009, 1140, 1199
    jobs = []
    for h in range(N * 2):
        t = T0 + dt.timedelta(minutes=30 * h)
        e = t + dt.timedelta(minutes=29, seconds=59)
        doy = t.timetuple().tm_yday
        mins = h % 48 * 30
        fn = f"3B-HHR.MS.MRG.3IMERG.{t:%Y%m%d}-S{t:%H%M%S}-E{e:%H%M%S}.{mins:04d}.V07B.HDF5"
        url = (f"https://opendap.earthdata.nasa.gov/collections/C2723754847-GES_DISC/granules/GPM_3IMERGHH.07%3A{fn}"
               f".dap.nc4?dap4.ce=/Grid/precipitation%5B0:0%5D%5B{i0}:{i1}%5D%5B{j0}:{j1}%5D")
        jobs.append((h, url, f"imerg_{t:%Y%m%d_%H%M}.nc4"))
    del doy

    def get(j):
        try:
            return j[0], SL.fetch(j[1], ID, name=j[2], token=True, min_bytes=5000)
        except Exception as ex:  # noqa: BLE001
            return j[0], ex
    import netCDF4
    arr = np.full((N * 2, j1 - j0 + 1, i1 - i0 + 1), np.nan)  # (t, lat, lon)
    failed = 0
    with ThreadPoolExecutor(8) as ex:
        for h, p in ex.map(get, jobs):
            if isinstance(p, Exception):
                failed += 1
                continue
            ds = netCDF4.Dataset(p)
            x = np.ma.filled(ds["Grid"]["precipitation"][0].astype(float), np.nan)  # (lon, lat)
            ds.close()
            x[x < 0] = np.nan
            arr[h] = x.T
    lat = -89.95 + 0.1 * np.arange(j0, j1 + 1)
    lon = -179.95 + 0.1 * np.arange(i0, i1 + 1)
    return arr, lat, lon, failed


def main():
    # ---- track
    trk, landfalls = track()
    fl = [l for l in landfalls if l["lon"] > -83.5 and l["lat"] > 25]  # Florida landfall (Cayo Costa)
    lf = fl[0] if fl else None
    print("track points", len(trk), "landfalls", landfalls)

    # ---- ERA5 point and baseline
    wind, pres, cell = era5_point()
    base_all, base_mean = era5_baseline()
    norm = SL.norm_stats(base_all.ravel(), "2017-2021",
                         "ERA5 hourly 10 m wind speed at the Fort Myers grid cell, 23 Sep to 1 Oct of 2017 to 2021 (all hours pooled)")

    # ---- ERA5 grids
    ws, wd, ps = era5_grid()
    rad = np.deg2rad(wd)
    u, v = -ws * np.sin(rad), -ws * np.cos(rad)  # meteorological direction = from
    fr = np.arange(0, N, 3)
    wind_grid = SL.enc_wind(u[fr], v[fr], float(LAT_G[0]), float(LAT_G[-1]), float(LON_G[0]), float(LON_G[-1]), fr.tolist(),
                            scale=0.4, source="ERA5 10 m wind (reanalysis model), Open-Meteo, 0.5 deg sample of the 0.25 deg grid, 3-hourly")
    pmin_grid = float(np.floor(np.nanmin(ps)))
    pres_grid = SL.enc_grid(ps[fr], pmin_grid, 1015.0, float(LAT_G[0]), float(LAT_G[-1]), float(LON_G[0]), float(LON_G[-1]),
                            fr.tolist(), "hPa", "model", floor=1015.0)

    # ---- gauges
    stations, pred_fmy, six_fmy = [], None, None
    meta_by = {}
    for sid in GAUGES:
        meta, hourly, six = coops(sid, "water_level")
        if meta is None:
            print("no data", sid)
            continue
        meta_by[sid] = (meta, hourly, six)
        stations.append({"id": sid, "name": meta["name"], "lat": float(meta["lat"]), "lon": float(meta["lon"]), "series": SL.clean(hourly, 3)})
    _, pred_h, _ = coops("8725520", "predictions")
    fmy_meta, fmy_h, fmy_six = meta_by["8725520"]
    fmy_res = fmy_h - pred_h  # surge residual: observed minus astronomical tide prediction
    ipk = int(np.nanargmax(fmy_six))
    fmy_peak_t = T0 + dt.timedelta(minutes=6 * ipk)
    res_six = None

    # last valid sample per gauge (failures)
    stops = []
    for sid, (meta, h, six) in meta_by.items():
        ok = np.where(np.isfinite(six))[0]
        if len(ok) and ok[-1] < N * 10 - 5:
            stops.append((meta["name"], T0 + dt.timedelta(minutes=6 * int(ok[-1])), float(six[ok[-1]]), int(ok[-1] / 10)))
        print(sid, meta["name"], "hourly gaps", int(np.isnan(h).sum()), "max", round(float(np.nanmax(six)), 3), "min", round(float(np.nanmin(six)), 3))

    # ---- IMERG
    rain_hh, rlat, rlon, failed = imerg()
    rain_h = np.nanmean(rain_hh.reshape(N, 2, *rain_hh.shape[1:]), 1)  # mm/h hourly mean (nan if both missing)
    m = (rlat[:, None] >= SWFL[0]) & (rlat[:, None] <= SWFL[1]) & (rlon[None, :] >= SWFL[2]) & (rlon[None, :] <= SWFL[3])
    with np.errstate(all="ignore"):
        rain_series = np.array([np.nanmean(f[m]) if np.isfinite(f[m]).mean() > 0.5 else np.nan for f in rain_h])
    # 3-hourly frames at 0.2 deg (2x2 block mean of 0.1 deg)
    r3 = np.nanmean(rain_hh.reshape(N // 3, 6, *rain_hh.shape[1:]), 1)
    r3 = np.nanmean(r3.reshape(N // 3, 30, 2, 35, 2), axis=(2, 4))
    rlat2 = rlat.reshape(30, 2).mean(1)
    rlon2 = rlon.reshape(35, 2).mean(1)
    rain_grid = SL.enc_grid(r3, 0.0, 30.0, round(float(rlat2[0]), 3), round(float(rlat2[-1]), 3), round(float(rlon2[0]), 3),
                            round(float(rlon2[-1]), 3), (np.arange(N // 3) * 3).tolist(), "mm/h", "observed", floor=1.0)
    swfl_total_mm = float(np.nansum(rain_series))  # sum of hourly mean rates = mm over the window

    # ---- link: wind (hero) -> Fort Myers water level (partner), lags 0..12 h
    lk_all = SL.link(SL.clean(wind), SL.clean(fmy_h), 12, "hour",
                     "Pearson r, ERA5 hourly wind speed at Fort Myers vs CO-OPS Fort Myers hourly water level above MHHW, partner lagged 0..12 h (tide not removed)")
    pos = [c for c in lk_all["curve"] if 0 <= c[0] <= 12]
    kb, rb = max(pos, key=lambda c: c[1])
    x, y = SL._pairs(SL.clean(wind), SL.clean(fmy_h), kb)
    lk = {**lk_all, "r": rb, "lag": kb, "n": int(len(x)), "curve": pos,
          "strength": "strong" if abs(rb) >= .6 else "moderate" if abs(rb) >= .3 else "weak", "sign": "positive" if rb > 0 else "negative"}
    lk_res = SL.link(SL.clean(wind), SL.clean(fmy_res), 12, "hour", "same, partner = surge residual (observed minus CO-OPS tide prediction)")
    pos_r = [c for c in lk_res["curve"] if 0 <= c[0] <= 12]
    kr, rr = max(pos_r, key=lambda c: c[1])
    lk["residual"] = {"r": rr, "lag": kr, "curve": pos_r, "method": lk_res["method"]}
    lk["edge"] = kb == 12
    if kb == 12:
        lk["note"] = ("r keeps rising up to the 12 h edge: no clear optimum lag. The window correlation is driven by the slow shape "
                      "(wind high for a day before landfall, water high for a day after). Peak to peak timing is given separately.")
    # peak to peak: ERA5 wind max (hourly) to Fort Myers water max (6 minute)
    p2p = round((step(dt.datetime(2022, 9, 23, tzinfo=dt.timezone.utc) + dt.timedelta(minutes=6 * int(np.nanargmax(fmy_six)))) - int(np.nanargmax(wind))), 1)
    lk["peak_to_peak_h"] = p2p

    # ---- numbers
    iw = int(np.nanargmax(wind))
    ip = int(np.nanargmin(pres))
    tstr = lambda t: t.strftime("%d %b %H:%M UTC")  # noqa: E731
    st = lambda k: (T0 + dt.timedelta(hours=k))  # noqa: E731
    best_min_p = min((p for p in trk if p["pres_hpa"]), key=lambda p: p["pres_hpa"])
    best_max_w = max((p for p in trk if p["wind_kt"]), key=lambda p: p["wind_kt"])
    ir = int(np.nanargmax(rain_series))
    sigma = (float(np.nanmax(wind)) - norm["mean"]) / norm["sd"]
    lowest = min(((s["name"], float(np.nanmin(meta_by[s["id"]][2])), int(np.nanargmin(meta_by[s["id"]][2])) / 10) for s in stations), key=lambda x: x[1])
    stats = {
        "landfall (IBTrACS, Cayo Costa)": tstr(st(lf["t"])) if lf else None,
        "landfall wind (kt)": lf["wind_kt"] if lf else None,
        "landfall pressure (hPa)": lf["pres_hpa"] if lf else None,
        "best track minimum pressure (hPa)": best_min_p["pres_hpa"],
        "best track maximum wind (kt)": best_max_w["wind_kt"],
        "ERA5 Fort Myers max wind (m/s, model)": round(float(np.nanmax(wind)), 1),
        "ERA5 Fort Myers max wind time": tstr(st(iw)),
        "ERA5 Fort Myers wind 2017-21 mean (m/s)": norm["mean"],
        "ERA5 Fort Myers peak wind vs normal (sigma)": round(sigma, 1),
        "ERA5 Fort Myers peak wind vs 2017-21 mean (%)": SL.pct(float(np.nanmax(wind)), norm["mean"]),
        "ERA5 Fort Myers min surface pressure (hPa, model)": round(float(np.nanmin(pres)), 1),
        "ERA5 Fort Myers min pressure time": tstr(st(ip)),
        "Fort Myers max water level above MHHW (m, 6 min)": round(float(fmy_six[ipk]), 3),
        "Fort Myers max water level time": tstr(fmy_peak_t),
        "Fort Myers max surge residual (m, hourly)": round(float(np.nanmax(fmy_res)), 3),
        "lowest water (negative surge)": f"{lowest[0]} {lowest[1]:.2f} m below MHHW",
        "peak to peak lag, wind max to water max (h)": p2p,
        "best lag in 0 to 12 h window (h, at the edge)" if kb == 12 else "best lag wind to water level (h)": kb,
        "link r wind to water level": rb,
        "lag wind to surge residual (h)": kr,
        "link r wind to surge residual": rr,
        "IMERG SW Florida max hourly mean rain (mm/h)": round(float(np.nanmax(rain_series)), 2),
        "IMERG SW Florida window total (mm, area mean)": round(swfl_total_mm, 0),
    }
    for name, t, v, _ in stops:
        stats[f"{name} gauge last reading"] = f"{tstr(t)}, {v:.2f} m above MHHW"

    gaps = [
        "ERA5 is a reanalysis model at about 31 km: it smooths the eyewall, so its Fort Myers wind and pressure are far weaker than the measured storm (best track minimum is given for comparison).",
        f"ERA5 point = grid cell {cell[0]}N {cell[1]}E nearest the Fort Myers gauge.",
        "Water levels are 6 minute CO-OPS readings averaged to the hour; an hour with fewer than 6 of 10 readings stays empty (null).",
        "Datum MHHW (mean higher high water) per gauge: values above 0 are above the normal daily high tide.",
        "Fort Myers 8725520 recorded the whole event (no gap); it is the hero partner gauge.",
        "Track: IBTrACS 3-hourly positions; points between the 6-hourly best track fixes are interpolated by IBTrACS (flag interpolated = true).",
        "IMERG V07B Final run half-hourly rain is a satellite estimate (observed, merged microwave and infrared); grid shown at 0.2 deg, 3 hour means.",
        "The wind to water level link includes the tide; the residual link (observed minus tide prediction) is given too.",
        "ERA5 wind and pressure grids are sampled every 0.5 deg from the 0.25 deg ERA5 grid.",
    ]
    for name, t, v, k in stops:
        gaps.insert(0, f"{name} gauge stopped reporting at {tstr(t)} at {v:.2f} m above MHHW during the surge; the gap after that is kept empty, never bridged.")
    if failed:
        gaps.append(f"IMERG: {failed} of {N * 2} half-hour files failed to download (left empty).")

    events = []
    for l in landfalls:
        events.append({"t": l["t"], "label": "landfall Cuba" if l["lon"] < -83 and l["lat"] < 23.5 else "landfall Florida (Cayo Costa)" if l is lf else "second Florida landfall record (near Punta Gorda)" if 26 < l["lat"] < 27.5 else "landfall South Carolina" if l["lat"] > 32 else f"best track landfall record {l['lat']}N {abs(l['lon'])}W"})
    events.append({"t": round(step(fmy_peak_t), 2), "label": f"Fort Myers water peak {fmy_six[ipk]:.2f} m above MHHW"})
    for name, t, v, _ in stops:
        events.append({"t": round(step(t), 2), "label": f"{name} gauge stops"})
    events.sort(key=lambda e: e["t"])
    bands = [{"t0": iw - 3, "t1": iw + 3, "label": "eyewall near Fort Myers"}]

    trk_status = {}
    for p in trk:
        if p["wind_kt"] and p["wind_kt"] >= 64 and "hurricane" not in trk_status:
            trk_status["hurricane"] = p
    beats = [
        {"t": 0, "text": f"23 September 2022: Tropical Depression Nine in the Caribbean, winds {trk[0]['wind_kt']} knots."},
    ]
    if "hurricane" in trk_status:
        beats.append({"t": trk_status["hurricane"]["t"], "text": f"Ian becomes a hurricane, {trk_status['hurricane']['wind_kt']} knots."})
    cuba = [l for l in landfalls if l["lat"] < 23.5]
    if cuba:
        beats.append({"t": cuba[0]["t"], "text": f"Ian crosses western Cuba as a major hurricane, {cuba[0]['wind_kt']} knots."})
    if lf:
        beats.append({"t": lf["t"], "text": f"Landfall at Cayo Costa, {tstr(st(lf['t']))}: {lf['wind_kt']} knots, {lf['pres_hpa']} hectopascals (best track)."})
    beats += [
        {"t": iw, "text": f"Fort Myers wind peaks in ERA5 at {np.nanmax(wind):.1f} metres per second, {sigma:.1f} standard deviations above the 2017 to 2021 normal of {norm['mean']:.1f}."},
        {"t": round(step(fmy_peak_t), 2), "text": f"Fort Myers water reaches {fmy_six[ipk]:.2f} metres above the normal high tide, {p2p:.1f} hours after the strongest wind there."},
        {"t": round(lowest[2], 1), "text": f"North of the eye the wind pushes water out: {lowest[0]} drops to {abs(lowest[1]):.2f} metres below MHHW."},
        {"t": ir, "text": f"Rain over southwest Florida peaks at {np.nanmax(rain_series):.1f} millimetres per hour (IMERG area mean)."},
    ]
    for name, t, v, _ in stops:
        beats.append({"t": round(step(t), 2), "text": f"The {name} gauge stops reporting at {v:.2f} metres above MHHW. The gap stays silent."})
    beats.sort(key=lambda b: b["t"])

    layers = [
        {"id": "track", "type": "track", "name": "Track", "color": "#ffffff", "unit": "kt",
         "what": "IBTrACS v04r01 best track (NHC), 3-hourly positions, wind and pressure (observed analysis)",
         "series": SL.clean(np.interp(np.arange(N), [p["t"] for p in trk if p["wind_kt"]], [p["wind_kt"] for p in trk if p["wind_kt"]],
                                     left=np.nan, right=np.nan), 1),
         "series_note": "lane = best track maximum wind, linearly interpolated between 3-hourly track points for the hourly lane (a track, not a gap)",
         "track": trk},
        {"id": "wind", "type": "streaks", "name": "Wind at Fort Myers", "color": "#9fd3ff", "unit": "m/s",
         "what": "ERA5 10 m wind speed at Fort Myers, hourly, via Open-Meteo (model)",
         "series": SL.clean(wind, 2), "baseline": SL.clean(base_mean, 2), "wind": wind_grid},
        {"id": "surge", "type": "columns", "name": "Water level", "color": "#4fb3ff", "unit": "m above MHHW",
         "what": "NOAA CO-OPS tide gauges, water level above MHHW, 6 minute readings averaged hourly (observed); lane = Fort Myers",
         "series": SL.clean(fmy_h, 3), "series_station": "Fort Myers 8725520",
         "prediction": SL.clean(pred_h, 3), "residual": SL.clean(fmy_res, 3), "stations": stations},
        {"id": "pressure", "type": "field", "name": "Pressure", "color": "#c0a0ff", "unit": "hPa", "palette": "cold",
         "what": "ERA5 surface pressure, hourly at Fort Myers, grid 3-hourly (model)",
         "series": SL.clean(pres, 1), "grid": pres_grid,
         "grid_note": f"linear {pmin_grid:.0f} to 1015 hPa; the tint shows pressure below 1015 hPa (lower = stronger); floor 1015 hPa"},
        {"id": "rain", "type": "field", "name": "Rain", "color": "#5ad18a", "unit": "mm/h", "palette": "rain",
         "what": "NASA GPM IMERG V07B Final half-hourly precipitation (satellite, observed), lane = SW Florida area mean",
         "series": SL.clean(rain_series, 2), "grid": rain_grid, "grid_note": "linear 0 to 30 mm/h, floor 1 mm/h, 3 hour means at 0.2 deg"},
    ]
    obj = {
        "title": "Hurricane Ian: wind, then water",
        "timebase": "hour", "t0": "2022-09-23T00:00Z", "step_s": 3600, "n": N,
        "region": {"lat0": 24, "lat1": 30, "lon0": -86, "lon1": -79},
        "hero": "wind", "partner": "surge",
        "link": lk, "hero_norm": norm, "stats": stats, "gaps": gaps, "beats": beats, "events": events, "bands": bands,
        "sources": [
            {"name": "IBTrACS v04r01 (North Atlantic)", "producer": "NOAA NCEI (best track from NHC)", "resolution": "3-hourly positions",
             "kind": "observed", "period": "2022-09-23 to 2022-10-01", "baseline": "none",
             "url": "https://www.ncei.noaa.gov/products/international-best-track-archive"},
            {"name": "ERA5 hourly 10 m wind and surface pressure", "producer": "ECMWF Copernicus C3S, served by Open-Meteo",
             "resolution": "0.25 deg, hourly (grid sampled at 0.5 deg)", "kind": "model", "period": "2022-09-23 to 2022-10-01",
             "baseline": "Fort Myers wind 23 Sep to 1 Oct, 2017 to 2021", "url": "https://open-meteo.com/en/docs/historical-weather-api"},
            {"name": "CO-OPS water level and tide predictions", "producer": "NOAA CO-OPS", "resolution": "6 minute, averaged hourly",
             "kind": "observed", "period": "2022-09-23 to 2022-10-01", "baseline": "datum MHHW; predictions used for the surge residual",
             "url": "https://tidesandcurrents.noaa.gov/waterlevels.html?id=8725520"},
            {"name": "GPM IMERG Final Precipitation L3 Half Hourly V07 (GPM_3IMERGHH)", "producer": "NASA GES DISC",
             "resolution": "0.1 deg, 30 minute (shown 0.2 deg, 3 hour)", "kind": "observed", "period": "2022-09-23 to 2022-10-01",
             "baseline": "none", "url": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHH_07/summary"},
            {"name": "Hurricane Ian Tropical Cyclone Report (context)", "producer": "NOAA National Hurricane Center", "resolution": "event report",
             "kind": "observed", "period": "2022", "baseline": "none", "url": "https://www.nhc.noaa.gov/data/tcr/AL092022_Ian.pdf"},
        ],
        "layers": layers,
        "script": "e2_ian.py",
    }
    SL.write_story(ID, obj)
    print("residual link", lk["residual"]["r"], lk["residual"]["lag"])


if __name__ == "__main__":
    main()
