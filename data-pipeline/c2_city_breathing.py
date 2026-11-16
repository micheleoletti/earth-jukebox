"""C2 City breathing: 4 weeks of hourly NO2 in Milan (and Paris), Mon 2019-01-14 .. Sun 2019-02-10 (no public holidays).

Layers
  milan  EEA E1a (verified) hourly NO2, urban stations inside the Milan municipality (pillars), series = mean of stations.
  paris  EEA E1a hourly NO2, urban stations in Paris and the inner suburbs (within about 6 km of the centre), series = mean of stations.
  wind   ERA5 10 m wind (model, Open-Meteo archive), hourly; lane = wind speed at Milan; streaks on a 1 deg grid
         around Milan, 3-hourly.
Hours: EEA times are a fixed UTC+01 (station time zone, no DST; in Jan/Feb that equals local time). Step 0 = Mon 2019-01-14
00:00 local = 2019-01-13T23:00Z.
Link: hourly Milan NO2 vs Milan wind speed, lags -12..12 h, with the daily cycle removed (storylib.remove_cycle, 24) and raw.

Usage: python c2_city_breathing.py
"""
import datetime as dt
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402
import eea_lib as EEA  # noqa: E402

ID = "c2_city_breathing"
L0 = pd.Timestamp("2019-01-14 00:00")            # local (UTC+01)
NH = 28 * 24
IDX = pd.date_range(L0, periods=NH, freq="h")
T0_UTC = "2019-01-13T23:00Z"
MIN_COVER = 0.8
MILAN = (45.464, 9.190)
PARIS = (48.853, 2.349)
OM = "https://archive-api.open-meteo.com/v1/archive"


def stations(country, city, keep):
    meta = EEA.meta(ID)
    out = []
    for u in EEA.urls(country, city, ID):
        code = EEA.eoi(u)
        mt = meta.get(code)
        if mt is None or mt[4] != "urban" or not keep(mt):
            continue
        s = EEA.hourly(u, ID).reindex(IDX)
        cover = float(s.notna().mean())
        print(f"  {city[:6]} {code} {mt[0][:36]:36s} {mt[3]:10s} {mt[5].split('/')[-1]} cover {cover:.2f}", flush=True)
        if cover >= MIN_COVER:
            out.append({"code": code, "name": mt[0], "lat": mt[1], "lon": mt[2], "type": mt[3], "s": s.values.astype(float)})
    return out


def mean_series(sts, min_frac=0.5):
    """mean over stations, only for hours where at least half the stations report (no station-set jumps hidden)."""
    a = np.array([s["s"] for s in sts])
    n = np.sum(~np.isnan(a), 0)
    with np.errstate(all="ignore"):
        m = np.nanmean(a, 0)
    m[n < max(1, int(np.ceil(min_frac * len(sts))))] = np.nan
    return m


def om(lats, lons, name):
    url = (f"{OM}?latitude={','.join(f'{x:g}' for x in lats)}&longitude={','.join(f'{x:g}' for x in lons)}"
           f"&start_date=2019-01-13&end_date=2019-02-10&hourly=wind_speed_10m,wind_direction_10m&wind_speed_unit=ms&models=era5&timezone=GMT")
    js = SL.fetch_json(url, ID, name=name, min_bytes=1000)
    return js if isinstance(js, list) else [js]


def uv(js):
    t = pd.DatetimeIndex(js["hourly"]["time"]) + pd.Timedelta(hours=1)       # UTC -> UTC+01
    sp = np.array([np.nan if x is None else x for x in js["hourly"]["wind_speed_10m"]], float)
    di = np.array([np.nan if x is None else x for x in js["hourly"]["wind_direction_10m"]], float)
    df = pd.DataFrame({"u": -sp * np.sin(np.radians(di)), "v": -sp * np.cos(np.radians(di)), "s": sp}, index=t).reindex(IDX)
    return df


def diurnal(x, mask):
    h = np.array([t.hour for t in IDX])
    return np.array([np.nanmean(x[(h == k) & mask]) for k in range(24)])


def r3(x):
    return None if x is None or not np.isfinite(x) else round(float(x), 3)


def main():
    milan = stations("IT", "Milano (greater city)", lambda mt: mt[0].upper().startswith("MILANO"))
    paris = stations("FR", "Paris (greater city)", lambda mt: abs(mt[1] - PARIS[0]) < 0.055 and abs(mt[2] - PARIS[1]) < 0.085)
    m = mean_series(milan)
    p = mean_series(paris)

    wm = uv(om([MILAN[0]], [MILAN[1]], "om_milan.json")[0])
    wp = uv(om([PARIS[0]], [PARIS[1]], "om_paris.json")[0])
    GLAT, GLON = [44.0, 45.0, 46.0, 47.0], [7.0, 8.0, 9.0, 10.0, 11.0]
    g = om([la for la in GLAT for _ in GLON], [lo for _ in GLAT for lo in GLON], "om_grid.json")
    sub = np.arange(0, NH, 3)
    U = np.full((len(sub), len(GLAT), len(GLON)), np.nan)
    V = U.copy()
    for k, js in enumerate(g):
        d = uv(js)
        i, j = divmod(k, len(GLON))
        U[:, i, j], V[:, i, j] = d.u.values[sub], d.v.values[sub]

    ws = wm.s.values
    # ---- links
    lk = SL.link(SL.remove_cycle(m, 24), SL.remove_cycle(ws, 24), 12, "hour",
                 "Pearson r, hourly Milan NO2 (EEA, mean of stations) vs ERA5 Milan 10 m wind speed, daily cycle removed from both "
                 "(mean of each hour of day subtracted), lags -12..12 h", sign_hint=-1)
    raw = SL.link(m, ws, 12, "hour", "same, raw hourly values", sign_hint=-1)
    lk_p = SL.link(SL.remove_cycle(m, 24), SL.remove_cycle(p, 24), 12, "hour", "Milan NO2 vs Paris NO2, daily cycle removed")
    dm = pd.Series(m, IDX).groupby(IDX.floor("D")).mean()
    dw = pd.Series(ws, IDX).groupby(IDX.floor("D")).mean()
    r_daily, n_daily = SL.pearson(dm.values, dw.values)
    lk.update({"r_raw": raw["r"], "lag_raw": raw["lag"], "n_raw": raw["n"], "strength_raw": raw["strength"], "curve_raw": raw["curve"],
               "r_daily_means": r3(r_daily), "n_daily_means": n_daily,
               "r_milan_paris_cycle_removed": lk_p["r"], "lag_milan_paris": lk_p["lag"],
               "partner_choice": "wind: it is the physical driver (dilution) of the Milan NO2 swings; Paris shares the human rhythm but not the weather, so Milan vs Paris is reported only as a comparison"})

    # ---- stats
    wk = np.array([t.day_of_week < 5 for t in IDX])
    sat = np.array([t.day_of_week == 5 for t in IDX])
    sun = np.array([t.day_of_week == 6 for t in IDX])
    dc_wd, dc_we = diurnal(m, wk), diurnal(m, ~wk)
    dcp_wd = diurnal(p, wk)
    am, pm = int(np.argmax(dc_wd[4:12]) + 4), int(np.argmax(dc_wd[14:24]) + 14)
    amp, pmp = int(np.argmax(dcp_wd[4:12]) + 4), int(np.argmax(dcp_wd[14:24]) + 14)
    day = pd.DataFrame({"m": m}, index=IDX).groupby(IDX.floor("D")).m
    rng = (day.max() - day.min())[day.count() >= 20]
    pct = lambda a, b: SL.pct(float(np.nanmean(a)), float(np.nanmean(b)))
    stats = {
        "Milan NO2 mean, 4 weeks (ug/m3)": round(float(np.nanmean(m)), 1),
        "Milan weekday mean (ug/m3)": round(float(np.nanmean(m[wk])), 1),
        "Milan weekend mean (ug/m3)": round(float(np.nanmean(m[~wk])), 1),
        "Milan weekend vs weekday (%)": pct(m[~wk], m[wk]),
        "Milan Sunday vs weekday (%)": pct(m[sun], m[wk]),
        "Milan Saturday vs weekday (%)": pct(m[sat], m[wk]),
        "Milan weekday morning peak, hour (local)": am, "Milan morning peak (ug/m3)": round(float(dc_wd[am]), 1),
        "Milan weekday evening peak, hour (local)": pm, "Milan evening peak (ug/m3)": round(float(dc_wd[pm]), 1),
        "Milan weekday low, hour (local)": int(np.argmin(dc_wd)), "Milan weekday low (ug/m3)": round(float(np.min(dc_wd)), 1),
        "Milan mean daily range, max minus min (ug/m3)": round(float(rng.mean()), 1),
        "Milan highest hour (ug/m3)": round(float(np.nanmax(m)), 1), "Milan highest hour (local)": str(IDX[int(np.nanargmax(m))])[:16],
        "Paris NO2 mean (ug/m3)": round(float(np.nanmean(p)), 1),
        "Paris weekend vs weekday (%)": pct(p[~wk], p[wk]),
        "Paris weekday morning peak, hour (local)": amp, "Paris weekday evening peak, hour (local)": pmp,
        "Milan wind mean (m/s)": round(float(np.nanmean(ws)), 2),
        "link r, cycle removed": lk["r"], "link lag (h)": lk["lag"], "link r, raw": raw["r"], "link r, daily means": r3(r_daily),
    }
    hours_m = [round(float(x), 1) for x in dc_wd]
    # windiest stretch and the calmest/most polluted day for beats
    dmax = dm.idxmax()
    dwmax = dw.idxmax()
    t_of = lambda ts: int((ts - L0) / pd.Timedelta(hours=1))
    beats = [
        {"t": 0, "text": f"Monday 14 January 2019, Milan. Four weeks of hourly NO2 from {len(milan)} city stations. The weekday mean is {stats['Milan weekday mean (ug/m3)']} micrograms per cubic metre."},
        {"t": 7, "text": f"Every weekday the city breathes in: NO2 climbs to a morning peak around {am}:00, {stats['Milan morning peak (ug/m3)']} on average, and a second peak in the evening around {pm}:00, {stats['Milan evening peak (ug/m3)']}."},
        {"t": 5 * 24 + 12, "text": f"Weekend: traffic thins and NO2 is {-stats['Milan weekend vs weekday (%)']:.0f} percent lower than on weekdays, Sundays {-stats['Milan Sunday vs weekday (%)']:.0f} percent lower."},
        {"t": t_of(dmax) + 12, "text": f"{dmax.strftime('%A %d %B')}: the most polluted day, daily mean {round(float(dm.max()), 1)}, with the highest hour {stats['Milan highest hour (ug/m3)']}."},
        {"t": t_of(dwmax) + 12, "text": f"{dwmax.strftime('%A %d %B')}: the windiest day in the model, {round(float(dw.max()), 1)} metres per second, and Milan NO2 averages {round(float(dm[dwmax]), 1)}."},
        {"t": 20 * 24, "text": f"Wind and NO2: with the daily rhythm taken out, r is {lk['r']} with the wind leading by {-lk['lag']} hours ({lk['strength']}; {lk['r_lag0']} with no lag); daily means give r {r3(r_daily)} over {n_daily} days."},
        {"t": 27 * 24 + 12, "text": f"Paris breathes on the same clock: morning peak around {amp}:00, evening around {pmp}:00, and weekends {-stats['Paris weekend vs weekday (%)']:.0f} percent lower than weekdays."},
    ]
    beats.sort(key=lambda b: b["t"])
    gaps = [
        "Station hours flagged invalid by the agencies are empty and stay empty; a city lane is empty in any hour where fewer than half of its stations report.",
        f"Stations kept only with at least {int(MIN_COVER * 100)}% valid hours in the 4 weeks.",
        "EEA times are taken as the station time zone (UTC+01, no daylight saving), which is local time in January and February.",
        "Wind is ERA5 reanalysis (a model) at about 25 km, read at points from the Open-Meteo archive; streaks are 3-hourly on a 1 degree grid.",
        "Both NO2 and wind have a daily rhythm (traffic and the night inversion), so the raw hourly correlation partly reflects the clock; the headline link removes the mean daily cycle from both.",
        "Paris has no 2019 holiday in this window either; its lane is a comparison, not a partner of Milan.",
    ]
    lane = lambda a: [None if not np.isfinite(x) else round(float(x), 1) for x in a]
    pil = lambda sts: [{"id": s["code"], "name": s["name"].title() if s["name"].isupper() else s["name"], "lat": s["lat"], "lon": s["lon"], "type": s["type"], "series": lane(s["s"])} for s in sts]
    obj = {
        "title": "City breathing: Milan's daily NO2 pulse",
        "timebase": "hour", "t0": T0_UTC, "step_s": 3600, "n": NH, "local_utc_offset_h": 1,
        "region": {"lat0": 44.5, "lat1": 46.5, "lon0": 8.0, "lon1": 10.5},
        "hero": "milan", "partner": "wind", "link": lk,
        "hero_norm": {"min": round(float(np.nanmin(m)), 1), "max": round(float(np.nanmax(m)), 1),
                      "method": "min..max of the hero series itself (Milan hourly NO2, mean of stations), 4 weeks"},
        "stats": stats, "gaps": gaps, "beats": beats,
        "events": [{"t": d * 24 + 8, "label": "Mon"} for d in (0, 7, 14, 21)],
        "bands": [{"t0": w * 168 + 120, "t1": w * 168 + 167, "label": "weekend"} for w in range(4)],
        "diurnal_weekday_milan": hours_m, "diurnal_weekend_milan": [round(float(x), 1) for x in dc_we],
        "diurnal_weekday_paris": [round(float(x), 1) for x in dcp_wd],
        "sources": [
            {"name": "EEA air quality e-reporting, verified hourly NO2 (E1a), Milan", "producer": "European Environment Agency, data from ARPA Lombardia via ISPRA",
             "resolution": "hourly, urban stations", "kind": "observed", "period": "2019-01-14 to 2019-02-10", "baseline": "none (cycle: own min..max)",
             "url": "https://eeadmz1-downloads-webapp.azurewebsites.net/"},
            {"name": "EEA air quality e-reporting, verified hourly NO2 (E1a), Paris", "producer": "European Environment Agency, data from Airparif via LCSQA",
             "resolution": "hourly, urban stations", "kind": "observed", "period": "2019-01-14 to 2019-02-10", "baseline": "none",
             "url": "https://eeadmz1-downloads-webapp.azurewebsites.net/"},
            {"name": "ERA5 hourly 10 m wind (via Open-Meteo historical weather API)", "producer": "ECMWF Copernicus Climate Change Service, served by Open-Meteo",
             "resolution": "0.25 deg model grid, hourly", "kind": "model", "period": "2019-01-14 to 2019-02-10", "baseline": "none",
             "url": "https://open-meteo.com/en/docs/historical-weather-api"},
        ],
        "layers": [
            {"id": "milan", "type": "pillars", "name": "Milan NO2", "unit": "ug/m3", "color": "#ffb347",
             "what": f"Hourly NO2 at {len(milan)} urban stations in Milan, EEA verified data (observed); lane = mean of stations",
             "series": lane(m), "stations": pil(milan)},
            {"id": "paris", "type": "pillars", "name": "Paris NO2", "unit": "ug/m3", "color": "#c98bff",
             "what": f"Hourly NO2 at {len(paris)} urban stations in and around Paris (within about 6 km of the centre), EEA verified data (observed); lane = mean of stations",
             "series": lane(p), "stations": pil(paris)},
            {"id": "wind", "type": "streaks", "name": "Wind", "unit": "m/s", "color": "#8fd3ff",
             "what": "10 m wind, ERA5 reanalysis (model); lane = hourly wind speed at Milan",
             "series": [None if not np.isfinite(x) else round(float(x), 2) for x in ws],
             "wind": SL.enc_wind(U, V, GLAT[0], GLAT[-1], GLON[0], GLON[-1], [float(x) for x in sub], scale=0.1,
                                 source="ERA5 10 m wind, 3-hourly (reanalysis model, via Open-Meteo)")},
        ],
        "paris_wind_series": [None if not np.isfinite(x) else round(float(x), 2) for x in wp.s.values],
        "script": "c2_city_breathing.py",
    }
    SL.write_story(ID, obj)


if __name__ == "__main__":
    main()
