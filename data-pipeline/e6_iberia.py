"""E6 Iberia: heat and fire, summer 2022 (2022-06-01 .. 2022-08-31, daily).

Built from the team's historias/05_iberia (origin/main): there the monthly NASA POWER / FIRMS record (1981 to 2025)
flags summer 2022 as the disruptor of the Iberian fire trend. This story zooms into that summer, day by day.

Layers:
  heat   (pillars) NOAA GHCN-Daily maximum temperature at Spanish and Portuguese weather stations (observed);
                   ghost pillars = each station's 1991 to 2020 normal for that day
  fires  (points)  NASA FIRMS VIIRS S-NPP active fires, Spain + Portugal country files (observed)
  smoke  (particles) GEOS-CF surface PM2.5 + 10 m wind, daily means (NASA GMAO, model)
  tmax   (field)   GEOS-CF 2 m air temperature, daily highest of 8 three-hourly values (model)
hero = heat (network mean of station daily maxima), partner = fires (daily total FRP).
Link: daily, fires following the heat by 0..5 days.

Run (network + cache outside the repo): <python with numpy> data-pipeline/e6_iberia.py
"""
import csv
import datetime as dt
import pathlib
import sys
import warnings

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402
import fire_helpers as FH  # noqa: E402

warnings.simplefilter("ignore")
ID = "e6_iberia"
T0 = dt.datetime(2022, 6, 1)
N = 92  # 2022-06-01 .. 2022-08-31
BASE = (1991, 2020)
FIRE_BOX = dict(lat0=35.8, lat1=44.0, lon0=-9.8, lon1=3.6)    # mainland Spain + Portugal (no Canaries, no Azores, no Madeira)
GRID_BOX = dict(lat0=35.0, lat1=45.0, lon0=-11.0, lon1=5.0)
GHCN = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{}.csv"
PM_VMAX, PM_FLOOR = 60.0, 8.0
T_MIN, T_MAX = 20.0, 44.0
PILLAR_FLOOR = 20.0
# GHCN-Daily stations: complete (or nearly) June to August 2022 and at least 75% of the 1991 to 2020 summer days
STATIONS = [
    ("SP000003195", "Madrid"), ("SPE00120512", "Seville"), ("SP000008410", "Córdoba"), ("SP000004452", "Badajoz"),
    ("SPE00119918", "Cáceres"), ("SPE00120566", "Toledo"), ("SP000008280", "Albacete"), ("SPE00120089", "Granada"),
    ("SP000008202", "Salamanca"), ("SPE00120620", "Zamora"), ("SPE00120224", "León"), ("SPE00120233", "Ponferrada"),
    ("SPE00120368", "Ourense"), ("SPE00120611", "Bilbao"), ("SP000009434", "Zaragoza"), ("SPE00120242", "Lleida"),
    ("SP000008181", "Barcelona"), ("SP000008416", "Valencia"), ("PO000008535", "Lisbon"), ("PO000008575", "Bragança"),
]
# named fires checked against the FIRMS detections (centre, radius km, story-step window): reported only if the data shows them there
NAMED_FIRES = [("Sierra de la Culebra", "Zamora, Spain", 41.93, -6.25, 30, 0, 30), ("Losacio", "Zamora, Spain", 41.92, -6.05, 25, 30, 61),
               ("Serra da Estrela", "Portugal", 40.35, -7.55, 30, 61, 92)]


def day_list(y):
    s = dt.date(y, 6, 1)
    return [s + dt.timedelta(k) for k in range(N)]


def ghcn_tmax(sid):
    """{date: daily max temperature C} for one GHCN-Daily station; values with a quality flag are dropped."""
    p = SL.fetch(GHCN.format(sid), ID, name=f"ghcn/{sid}.csv", min_bytes=10000)
    out, meta = {}, None
    with open(p, newline="") as fh:
        for r in csv.DictReader(fh):
            if meta is None:
                meta = (float(r["LATITUDE"]), float(r["LONGITUDE"]), float(r["ELEVATION"]), r["NAME"])
            v = (r.get("TMAX") or "").strip()
            if not v or (r.get("TMAX_ATTRIBUTES") or ",,").split(",")[1].strip():
                continue
            d = dt.date.fromisoformat(r["DATE"])
            if 5 <= d.month <= 9:
                out[d] = int(v) / 10.0
    return out, meta


def station_normal(tx, days):
    """1991 to 2020 normal for each story day: mean of the same calendar day +-7 days over the baseline years."""
    out = []
    for d in days:
        vals = []
        for y in range(BASE[0], BASE[1] + 1):
            c = dt.date(y, d.month, d.day)
            for k in range(-7, 8):
                v = tx.get(c + dt.timedelta(k))
                if v is not None:
                    vals.append(v)
        out.append(float(np.mean(vals)) if len(vals) >= 200 else np.nan)
    return np.array(out)


def network_anom(T, Nm, min_frac=.75):
    """mean over stations of (value - normal) for each day; None where fewer than min_frac of the stations report."""
    a = T - Nm
    ok = np.isfinite(a).sum(0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = np.nanmean(a, 0)
    return np.where(ok >= min_frac * T.shape[0], m, np.nan), ok


def runs(mask):
    out, r0 = [], None
    for d in range(len(mask) + 1):
        hi = d < len(mask) and bool(mask[d])
        if hi and r0 is None:
            r0 = d
        if not hi and r0 is not None:
            out.append((r0, d))
            r0 = None
    return out


def main():
    gaps = []
    days = day_list(2022)
    datef = lambda d: (T0 + dt.timedelta(int(d))).strftime("%B %-d")  # noqa: E731

    # ------------------------------------------------------------ weather stations (hero)
    st_rows, T, Nm = [], [], []
    for sid, nm in STATIONS:
        tx, meta = ghcn_tmax(sid)
        ser = np.array([tx.get(d, np.nan) for d in days])
        nrm = station_normal(tx, days)
        st_rows.append((sid, nm, meta, ser, nrm, tx))
        T.append(ser)
        Nm.append(nrm)
    T, Nm = np.array(T), np.array(Nm)
    base = np.nanmean(Nm, 0)
    anom, nrep = network_anom(T, Nm)
    hero = base + anom
    # normal spread: the same network anomaly on every summer day of the baseline years
    base_anoms = []
    for y in range(BASE[0], BASE[1] + 1):
        Ty = np.array([[r[5].get(d, np.nan) for d in day_list(y)] for r in st_rows])
        ay, _ = network_anom(Ty, Nm)
        base_anoms.append(ay)
    base_anoms = np.array(base_anoms)
    ba = base_anoms[np.isfinite(base_anoms)]
    hero_norm = {"mean": round(float(np.nanmean(base)), 3), "sd": round(float(ba.std(ddof=1)), 3), "n": int(len(ba)),
                 "years": f"{BASE[0]} to {BASE[1]}",
                 "method": "network mean of station daily maximum temperature; normal = each station's 1991 to 2020 mean for that calendar day (+-7 days), "
                           "sd = spread of the daily network anomaly over the June to August days of 1991 to 2020",
                 "base": SL.clean(base, 2)}
    miss = int(np.isnan(T).sum())
    gaps.append(f"Heat = daily maximum temperature at {len(STATIONS)} NOAA GHCN-Daily weather stations in Spain and Portugal (national weather services' "
                f"synoptic stations). The lane is the network mean: the mean of the normals plus the mean departure of the stations reporting that day "
                f"({miss} station-days missing out of {T.size}, none bridged; a day needs 75% of the stations).")
    gaps.append(f"Normal = each station's {BASE[0]} to {BASE[1]} mean for the same calendar day (+-7 days); the faint glass pillars show it at the same scale.")
    stations = [{"id": sid.lower(), "name": nm, "lat": round(meta[0], 4), "lon": round(meta[1], 4), "elev_m": meta[2],
                 "series": SL.clean(ser, 1), "normal": SL.clean(nrm, 1)} for sid, nm, meta, ser, nrm, _ in st_rows]
    heat = {"id": "heat", "type": "pillars", "name": "Heat (stations)",
            "what": "Daily maximum air temperature at weather stations, NOAA GHCN-Daily (observed); lane = network mean",
            "color": "#ff5a3c", "unit": "deg C", "series": SL.clean(hero, 1), "baseline": SL.clean(base, 1),
            "baseline_label": f"{BASE[0]} to {BASE[1]} normal, same days", "normal_label": f"{BASE[0]} to {BASE[1]} mean",
            "series_label": f"mean of {len(STATIONS)} stations", "floor": PILLAR_FLOOR, "stations": stations}

    # ------------------------------------------------------------ fires (partner)
    parts = [FH.firms(ID, 2022, c) for c in ("Spain", "Portugal")]
    f = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    tt = (f["time"] - np.datetime64(T0, "m")).astype("timedelta64[m]").astype(float) / 1440.0
    b = FIRE_BOX
    sel = ((tt >= 0) & (tt < N) & (f["type"] == 0) & (f["conf"] != "l") & (f["lat"] >= b["lat0"]) & (f["lat"] <= b["lat1"])
           & (f["lon"] >= b["lon0"]) & (f["lon"] <= b["lon1"]))
    day = np.floor(tt).astype(int)
    frp = np.array([float(f["frp"][sel & (day == d)].sum()) for d in range(N)])
    cnt = np.array([int((sel & (day == d)).sum()) for d in range(N)])
    idx = np.where(sel)[0]
    P, cell = FH.merge_points(f["lat"][idx], f["lon"][idx], tt[idx], f["frp"][idx], 30000, t_bin=1.0)
    vmax_frp = float(np.percentile(P["v"], 99))
    gaps.append(f"Fire points: all {len(idx):,} VIIRS detections in mainland Spain and Portugal in the window, merged into {len(P['v']):,} flames "
                f"(detections within {cell * 111:.0f} km on the same day become one flame at their strongest detection, size = their summed FRP).")
    gaps.append(f"Flame size is linear in summed FRP up to {vmax_frp:.0f} MW (99th percentile); larger flames drawn at that size. Only nominal and high "
                "confidence vegetation fire detections; VIIRS passes about twice a day, and smoke or cloud can hide fires.")
    fires = {"id": "fires", "type": "points", "name": "Fires",
             "what": "VIIRS S-NPP active fire detections, NASA FIRMS (observed); lane = daily total fire radiative power, mainland Spain and Portugal",
             "color": "#ff8a1f", "unit": "MW (daily total FRP)", "series": SL.clean(frp, 1),
             "points": {"lat": SL.clean(P["lat"], 3), "lon": SL.clean(P["lon"], 3), "t": SL.clean(P["t"], 3), "v": SL.clean(P["v"], 1),
                        "n": [int(x) for x in P["n"]]},
             "vmax": round(vmax_frp, 1)}
    # named fires: daily FRP within a radius of each, from the same detections
    named = {}
    for nm, where, la, lo, km, d0, d1 in NAMED_FIRES:
        dkm = np.hypot((f["lat"] - la) * 111.0, (f["lon"] - lo) * 111.0 * np.cos(np.radians(la)))
        s2 = sel & (dkm <= km) & (day >= d0) & (day < d1)
        ser = np.array([float(f["frp"][s2 & (day == d)].sum()) for d in range(N)])
        named[nm] = {"where": where, "lat": la, "lon": lo, "km": km, "frp": ser, "n": int(s2.sum()),
                     "peak": int(np.argmax(ser)), "days": [int(d) for d in np.where(ser > 0.05 * ser.max())[0]] if ser.max() > 0 else []}

    # ------------------------------------------------------------ GEOS-CF smoke, wind, heat (model)
    nh = N * 24
    pm, la, lo = FH.geoscf(ID, "aqc_tavg_1hr_g1440x721_v1", "pm25_rh35_gcc", T0, nh, 3, **GRID_BOX)
    pm_d = np.nanmean(pm.reshape(N, 8, *pm.shape[1:]), 1)
    tday = [d + 0.5 for d in range(N)]
    u, la_, lo_ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "u10m", T0, nh, 6, **GRID_BOX, lev=None)
    v, _, _ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "v10m", T0, nh, 6, **GRID_BOX, lev=None)
    ud, vd = (np.nanmean(x.reshape(N, 4, *x.shape[1:]), 1) for x in (u, v))
    u4, v4 = FH.block_mean(ud, 4), FH.block_mean(vd, 4)
    la4, lo4 = FH.block_centres(la_, 4), FH.block_centres(lo_, 4)
    wind = SL.enc_wind(u4, v4, float(la4[0]), float(la4[-1]), float(lo4[0]), float(lo4[-1]), tday,
                       source="GEOS-CF 10 m wind, daily mean, NASA GMAO (model)")
    fy = (la >= b["lat0"]) & (la <= b["lat1"])
    fx = (lo >= b["lon0"]) & (lo <= b["lon1"])
    # model PM2.5 lane: the highest daily mean among the model cells near the station sites (where people breathe it)
    cells = sorted({(int(np.argmin(abs(la - s["lat"]))), int(np.argmin(abs(lo - s["lon"])))) for s in stations})
    pm_sites = np.array([pm_d[:, i, j] for i, j in cells])
    # smoke particles drawn grey (default is sand): they sit on an orange heat tint in this story and must read as smoke
    smoke = {"id": "smoke", "type": "particles", "name": "Smoke (model PM2.5)", "particleColor": "#8f8b86",
             "what": "GEOS-CF surface PM2.5 and 10 m wind, daily means, NASA GMAO Composition Forecast assimilation (model)",
             "color": "#aaa59d", "unit": "ug/m3", "series": SL.clean(np.nanmean(pm_sites, 0), 1),
             "series_label": f"model PM2.5, daily mean, average of the {len(cells)} model cells at the weather stations",
             "grid": SL.enc_grid(pm_d, 0.0, PM_VMAX, float(la[0]), float(la[-1]), float(lo[0]), float(lo[-1]), tday, "ug/m3",
                                 kind="model", floor=PM_FLOOR),
             "wind": wind}
    gaps.append(f"Smoke = GEOS-CF surface PM2.5 (a model with satellite data assimilated, not a measurement), daily mean of 8 three-hourly values, 0.25 deg; "
                f"drawn linear from a floor of {PM_FLOOR:.0f} to {PM_VMAX:.0f} ug/m3, higher values at full density. Particles move on GEOS-CF daily mean 10 m wind (1 deg). "
                "Part of the haze over Iberia in summer is Saharan dust, which the model also counts as PM2.5.")
    t2, _, _ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "t2m", T0, nh, 3, **GRID_BOX, lev=None)
    t2x = np.nanmax(t2.reshape(N, 8, *t2.shape[1:]), 1) - 273.15
    tm_sites = np.array([t2x[:, i, j] for i, j in cells])
    t2b = FH.block_mean(t2x, 2)
    lab, lob = FH.block_centres(la, 2), FH.block_centres(lo, 2)
    tmax = {"id": "tmax", "type": "field", "palette": "heat", "name": "Afternoon heat (model)",
            "what": "GEOS-CF 2 m air temperature, highest of 8 three-hourly values each day, NASA GMAO (model)", "color": "#ffb03b", "unit": "deg C",
            "series": SL.clean(np.nanmean(tm_sites, 0), 1), "series_label": f"model daily highest, mean of the {len(cells)} model cells at the weather stations",
            "grid": SL.enc_grid(t2b, T_MIN, T_MAX, float(lab[0]), float(lab[-1]), float(lob[0]), float(lob[-1]), tday, "deg C", kind="model", floor=T_MIN)}
    r_model, n_model = SL.pearson(hero, np.nanmean(tm_sites, 0))
    gaps.append(f"Afternoon heat map = GEOS-CF 2 m temperature (model), the highest of 8 three-hourly values each day at 0.5 deg, colour linear from "
                f"{T_MIN:.0f} (blue) through {(T_MIN + T_MAX) / 2:.0f} (white) to {T_MAX:.0f} deg C (red). Three-hourly samples and 50 km cells miss the "
                f"hottest hour and the hottest valleys, so the map reads a few degrees cooler than the stations (day to day r = {r_model:.2f} with the station lane).")

    # ------------------------------------------------------------ link
    lk = FH.link_dir(hero, frp, 5, "days",
                     "Pearson r of daily values: network mean station maximum temperature (GHCN-Daily) vs daily total fire radiative power in mainland "
                     "Spain and Portugal (VIIRS), fires following the heat by 0 to 5 days", partner_leads=False, min_n=20)
    lk["lag_steps"] = lk.get("lag")
    lk_an = FH.link_dir(anom, frp, 5, "days", "same with the heat as departure from normal", partner_leads=False, min_n=20)

    # ------------------------------------------------------------ stats, beats, events
    pk = int(np.nanargmax(hero))
    apk = int(np.nanargmax(anom))
    fpk = int(np.argmax(frp))
    sd = hero_norm["sd"]
    hot = np.isfinite(anom) & (anom >= 2 * sd)
    waves = [(a, z) for a, z in runs(hot) if z - a >= 3]
    st_max = [(float(np.nanmax(r[3])), r[1], int(np.nanargmax(r[3]))) for r in st_rows]
    smax = max(st_max)
    over40 = int(np.nansum(T >= 40.0))
    stats = {
        "hottest day, network mean (deg C)": round(float(hero[pk]), 1),
        "hottest day": (T0 + dt.timedelta(pk)).strftime("%Y-%m-%d"),
        "normal for that day (deg C)": round(float(base[pk]), 1),
        "largest departure from normal (deg C)": round(float(anom[apk]), 1),
        "largest departure day": (T0 + dt.timedelta(apk)).strftime("%Y-%m-%d"),
        "summer mean departure from normal (deg C)": round(float(np.nanmean(anom)), 2),
        f"days at least 2 sd ({2 * sd:.1f} deg C) above normal": int(hot.sum()),
        "highest station reading (deg C)": round(smax[0], 1),
        "highest station": f"{smax[1]}, {(T0 + dt.timedelta(smax[2])).strftime('%Y-%m-%d')}",
        "station-days at 40 deg C or more": over40,
        "fire detections in window (mainland Spain + Portugal)": len(idx),
        "fire FRP peak day": (T0 + dt.timedelta(fpk)).strftime("%Y-%m-%d"),
        "fire FRP peak, daily total (MW)": round(float(frp[fpk])),
        "fire detections on peak day": int(cnt[fpk]),
        "link r, heat vs fire FRP": lk.get("r"),
        "link lag, fires after heat (days)": lk.get("lag"),
        "link r at lag 0": lk.get("r_lag0"),
        "link n (days)": lk.get("n"),
        "link r, heat departure from normal vs fire FRP": lk_an.get("r"),
        "model vs stations, daily heat r": round(r_model, 3),
    }
    for nm, d in named.items():
        if d["n"]:
            mo = (T0 + dt.timedelta(d["peak"])).strftime("%B")
            stats[f"{nm} fire, {mo}: detections within {d['km']} km"] = d["n"]
            stats[f"{nm} fire: FRP peak day"] = (T0 + dt.timedelta(d["peak"])).strftime("%Y-%m-%d")
    beats = [{"t": 0, "text": f"June 1, 2022. Iberian weather stations average {hero[0]:.0f} degrees C in the afternoon; the normal for the day is {base[0]:.0f}."}]
    for a, z in waves:
        k = a + int(np.nanargmax(anom[a:z]))
        beats.append({"t": a, "text": f"{datef(a)} to {datef(z - 1)}: a heatwave, {z - a} days at least {2 * sd:.1f} degrees above normal; "
                                      f"on {datef(k)} the stations average {hero[k]:.0f} degrees, {anom[k]:.0f} above normal."})
    beats.append({"t": smax[2], "text": f"{datef(smax[2])}: {smax[1]} reaches {smax[0]:.1f} degrees C, the highest reading of the summer at these stations."})
    beats.append({"t": fpk, "text": f"{datef(fpk)}: the fires peak, {cnt[fpk]:,} satellite detections and {frp[fpk] / 1000:.0f} thousand megawatts in one day."})
    for nm, d in named.items():
        if d["n"]:
            beats.append({"t": d["peak"], "text": f"{datef(d['peak'])}: the {nm} fire ({d['where']}) at its strongest in the satellite data, "
                                              f"{d['frp'][d['peak']] / 1000:.1f} thousand megawatts within {d['km']} km."})
    beats.append({"t": N - 1, "text": f"August 31, end of the window. The stations were {np.nanmean(anom):.1f} degrees above normal on average all summer. "
                                      f"Daily heat and fire power: r = {lk['r']}, fires {lk['lag']} day{'s' if lk['lag'] != 1 else ''} after the heat, "
                                      f"a {lk['strength']} link over {lk['n']} days."})
    beats.sort(key=lambda x: x["t"])
    events = [{"t": pk, "label": f"hottest {hero[pk]:.1f} C"}, {"t": fpk, "label": "fire peak"}]
    bands = [{"t0": a, "t1": z, "label": "heatwave (2 sd above normal)"} for a, z in waves]
    gaps.append(f"Heatwave bands = runs of at least 3 days with the network mean at least 2 sd ({2 * sd:.1f} deg C) above its 1991 to 2020 normal "
                "(a simple rule for this story, not the official national definitions).")
    gaps.append("The link uses all 92 days; hot spells last several days and big fires burn for days, so consecutive days are not independent: r is indicative, not a test. "
                "Heat dries the vegetation over weeks and fires need ignitions and wind, so a strong same-week link is not expected.")

    sources = [
        {"name": "GHCN-Daily v3, daily maximum temperature (TMAX)", "producer": "NOAA NCEI, from AEMET and IPMA synoptic stations",
         "resolution": f"daily, {len(STATIONS)} stations", "kind": "observed", "period": "2022-06-01 to 2022-08-31",
         "baseline": f"{BASE[0]} to {BASE[1]}, same calendar days", "url": "https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily"},
        {"name": "VIIRS S-NPP 375 m active fires (VNP14IMG), country yearly CSV (Spain, Portugal)", "producer": "NASA FIRMS (LANCE / EOSDIS)",
         "resolution": "375 m, about 2 overpasses per day", "kind": "observed", "period": "2022-06-01 to 2022-08-31", "baseline": "none",
         "url": "https://firms.modaps.eosdis.nasa.gov/country/"},
        {"name": "GEOS-CF v1 assimilation, surface PM2.5 (pm25_rh35_gcc), 10 m wind, 2 m temperature", "producer": "NASA GMAO",
         "resolution": "0.25 deg hourly, used as daily means or daily highest of 3- or 6-hourly values", "kind": "model",
         "period": "2022-06-01 to 2022-08-31", "baseline": "none", "url": "https://gmao.gsfc.nasa.gov/weather_prediction/GEOS-CF/"},
    ]
    obj = {"title": "Iberia: heat and fire", "timebase": "day", "t0": T0.strftime("%Y-%m-%dT%H:%MZ"), "step_s": 86400, "n": N,
           "region": {"lat0": 36.0, "lat1": 43.8, "lon0": -9.5, "lon1": 3.3}, "hero": "heat", "partner": "fires",
           "link": lk, "hero_norm": hero_norm, "stats": stats, "gaps": gaps, "beats": beats, "events": events, "bands": bands,
           "named_fires": [{"name": nm, "where": d["where"], "lat": d["lat"], "lon": d["lon"], "peak": d["peak"], "days": d["days"]} for nm, d in named.items() if d["n"]],
           "sources": sources, "layers": [heat, fires, smoke, tmax], "script": "e6_iberia.py"}
    SL.write_story(ID, obj)
    print("heatwaves:", [(datef(a), datef(z - 1)) for a, z in waves])
    print("named:", {nm: (datef(d["peak"]), d["n"], [datef(x) for x in d["days"][:1] + d["days"][-1:]]) for nm, d in named.items()})
    print("top fire days:", [(datef(k), round(frp[k])) for k in np.argsort(-frp)[:8]])
    print("anom top:", [(datef(k), round(float(anom[k]), 1)) for k in np.argsort(-np.nan_to_num(anom, nan=-99))[:10]], "sd", sd)
    print("link curve", lk.get("curve"), "anom link", lk_an.get("r"), lk_an.get("lag"))
    print("pm sites max", np.nanmax(pm_sites), "pm grid max", np.nanmax(pm_d), "p99", np.nanpercentile(pm_d, 99))


if __name__ == "__main__":
    main()
