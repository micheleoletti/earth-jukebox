"""E4 Australia Black Summer (2019-11-01 .. 2020-02-15, daily).

Layers: fires (FIRMS VIIRS SNPP, SE Australia), smoke (GEOS-CF PM2.5 daily mean + 10 m wind, model),
sydney_pm25 (pillars: NSW DPCCEW Sydney monitors + ACT Health Canberra monitors, daily mean PM2.5, observed),
heat (field: GEOS-CF 2 m temperature daily mean, model).
hero = sydney_pm25 (mean of Sydney monitors), partner = fires. Link: daily, fires leading by 0..5 days.

OpenAQ's archive has Sydney PM2.5 only from 2019-12-23 (checked: locations 304..913), so the station data comes
straight from the publishers: NSW Air Quality API (data.airquality.nsw.gov.au) and ACT open data (data.act.gov.au).

Run: /Users/mykhayloolefirenko/.venvs/omi/bin/python data-pipeline/e4_black_summer.py
"""
import datetime as dt
import json
import pathlib
import subprocess
import sys
import urllib.parse
import warnings

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402
import fire_helpers as FH  # noqa: E402

warnings.simplefilter("ignore")
ID = "e4_black_summer"
T0 = dt.datetime(2019, 11, 1)
N = 107  # 2019-11-01 .. 2020-02-15
BASE_STARTS = [2015, 2016, 2017, 2018]  # seasons starting Nov 1 of these years
FIRE_BOX = dict(lat0=-39.0, lat1=-28.0, lon0=140.0, lon1=154.0)
GRID_BOX = dict(lat0=-40.0, lat1=-26.0, lon0=138.0, lon1=158.0)
NSW_API = "https://data.airquality.nsw.gov.au/api/Data/"
ACT_API = "https://www.data.act.gov.au/resource/94a5-zqnn.json"
PM_VMAX, PM_FLOOR = 150.0, 15.0


def nsw_sites():
    p = SL.fetch(NSW_API + "get_SiteDetails", ID, name="nsw_sites.json")
    return [s for s in json.loads(p.read_text()) if str(s.get("Region", "")).startswith("Sydney") and s.get("Latitude")]


def nsw_daily(site, start, end):
    """Daily mean PM2.5 (24 h average from 1 h averages, local days) for one NSW site; {date: value}."""
    out = SL.cache_dir(ID) / "nsw" / f"pm25_{site}_{start}_{end}.json"
    out.parent.mkdir(exist_ok=True)
    if not out.exists():
        body = json.dumps({"Parameters": ["PM2.5"], "Sites": [site], "StartDate": start, "EndDate": end,
                           "Categories": ["Averages"], "SubCategories": ["Daily"],
                           "Frequency": ["24h average derived from 1h average"]})
        for k in range(4):
            r = subprocess.run(["curl", "-sf", "--max-time", "300", "-X", "POST", NSW_API + "get_Observations",
                                "-H", "Content-Type: application/json", "-d", body, "-o", str(out) + ".part"])
            if r.returncode == 0:
                json.loads(open(str(out) + ".part").read())
                pathlib.Path(str(out) + ".part").rename(out)
                break
        else:
            raise RuntimeError(f"NSW API failed for site {site}")
    d = {}
    for rec in json.loads(out.read_text()):
        if rec.get("Value") is not None:
            d[dt.date.fromisoformat(rec["Date"][:10])] = float(rec["Value"])
    return d


def act_hourly(start, end):
    """ACT Health hourly PM2.5 (pm2_5_1_hr) for all Canberra stations; {name: {date: [values]}}, meta."""
    out = SL.cache_dir(ID) / "act" / f"act_{start}_{end}.json"
    out.parent.mkdir(exist_ok=True)
    if not out.exists():
        rows, off = [], 0
        while True:
            q = {"$select": "name,gps,datetime,pm2_5_1_hr", "$where": f"datetime between '{start}T00:00:00' and '{end}T23:59:59'",
                 "$order": "datetime", "$limit": "50000", "$offset": str(off)}
            url = ACT_API + "?" + urllib.parse.urlencode(q)
            r = subprocess.run(["curl", "-sf", "--max-time", "300", url], capture_output=True)
            if r.returncode:
                raise RuntimeError("ACT API failed")
            part = json.loads(r.stdout)
            rows += part
            if len(part) < 50000:
                break
            off += 50000
        out.write_text(json.dumps(rows))
    by, meta = {}, {}
    for rec in json.loads(out.read_text()):
        v = rec.get("pm2_5_1_hr")
        if v is None:
            continue
        try:
            v = float(v)
        except ValueError:
            continue
        if not (-5 <= v <= 3000):
            continue
        nm = rec["name"]
        meta.setdefault(nm, (float(rec["gps"]["latitude"]), float(rec["gps"]["longitude"])))
        by.setdefault(nm, {}).setdefault(dt.date.fromisoformat(rec["datetime"][:10]), []).append(v)
    return by, meta


def season_days(y):
    s = dt.date(y, 11, 1)
    return [s + dt.timedelta(d) for d in range(N)]


def main():
    gaps = []
    days = season_days(2019)
    # ------------------------------------------------------------ fires
    parts = [FH.firms(ID, 2019, "Australia"), FH.firms(ID, 2020, "Australia")]
    f = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    tt = (f["time"] - np.datetime64(T0, "m")).astype("timedelta64[m]").astype(float) / 1440.0  # days since t0
    b = FIRE_BOX
    sel = ((tt >= 0) & (tt < N) & (f["type"] == 0) & (f["conf"] != "l") & (f["lat"] >= b["lat0"]) & (f["lat"] <= b["lat1"])
           & (f["lon"] >= b["lon0"]) & (f["lon"] <= b["lon1"]))
    day = np.floor(tt).astype(int)
    frp = [float(f["frp"][sel & (day == d)].sum()) for d in range(N)]
    cnt = [int((sel & (day == d)).sum()) for d in range(N)]
    idx = np.where(sel)[0]
    sub = idx[FH.even_subsample(tt[idx], 30000)]
    sub = sub[np.argsort(tt[sub])]
    vmax_frp = float(np.percentile(f["frp"][idx], 99))
    gaps.append(f"Fire points: {len(idx):,} VIIRS detections in south-east Australia (39-28S, 140-154E) in the window; "
                f"{len(sub):,} drawn, subsampled evenly in time. Daily FRP totals use all of them.")
    gaps.append(f"Fire point size is linear in FRP up to {vmax_frp:.0f} MW (99th percentile); larger detections drawn at that size. "
                "Only nominal and high confidence vegetation fire detections; VIIRS passes about twice a day and thick smoke can hide fires.")
    fires = {"id": "fires", "type": "points", "name": "Fires (SE Australia)",
             "what": "VIIRS SNPP active fire detections, NASA FIRMS (observed); lane = daily total fire radiative power",
             "color": "#ff7a1a", "unit": "MW (daily total FRP)", "series": SL.clean(frp, 1),
             "points": {"lat": SL.clean(f["lat"][sub], 3), "lon": SL.clean(f["lon"][sub], 3),
                        "t": SL.clean(tt[sub], 3), "v": SL.clean(f["frp"][sub], 1)},
             "vmax": round(vmax_frp, 1)}

    # ------------------------------------------------------------ Sydney (NSW) + Canberra (ACT) PM2.5
    sites = nsw_sites()

    def sydney(y):
        dd = season_days(y)
        res = {}
        for s in sites:
            d = nsw_daily(s["Site_Id"], dd[0].isoformat(), dd[-1].isoformat())
            ser = [d.get(x) for x in dd]
            if sum(v is not None for v in ser) > 0:
                res[s["Site_Id"]] = (s, ser)
        return res

    syd = sydney(2019)
    mat = np.array([[np.nan if v is None else v for v in ser] for _, ser in syd.values()])
    nst = np.isfinite(mat).sum(0)
    syd_mean = np.where(nst > 0, np.nanmean(mat, 0), np.nan)
    gaps.append(f"Sydney PM2.5 = mean of the {len(syd)} Sydney monitors of the NSW network reporting PM2.5 each day "
                f"(median {int(np.median(nst))} per day); daily values are 24 h means of local calendar days (AEST), aligned on the UTC story day.")
    base_series, base_years = [], []
    for y in BASE_STARTS:
        r = sydney(y)
        if not r:
            continue
        m = np.array([[np.nan if v is None else v for v in ser] for _, ser in r.values()])
        bm = np.where(np.isfinite(m).sum(0) > 0, np.nanmean(m, 0), np.nan)
        if np.isfinite(bm).sum() > N // 2:
            base_series.append(bm)
            base_years.append(f"{y}-{(y + 1) % 100:02d}")
    base_series = np.array(base_series)
    base_mean = np.nanmean(base_series, 0)
    hero_norm = SL.norm_stats(base_series.ravel(), f"{base_years[0]} to {base_years[-1]} summers",
                              "daily mean PM2.5 over Sydney NSW monitors, same window (Nov 1 to Feb 15) of each baseline summer")
    hero_norm["base"] = SL.clean(base_mean, 2)
    gaps.append(f"Normal = Sydney monitors over the same window in the {', '.join(base_years)} summers ({len(base_years)} seasons); "
                "the set of monitors grew over those years.")

    act, act_meta = {}, {}
    try:
        act_h, act_meta = act_hourly(days[0].isoformat(), days[-1].isoformat())
        for nm, byday in act_h.items():
            act[nm] = [float(np.mean(byday[x])) if len(byday.get(x, [])) >= 18 else None for x in days]
        gaps.append("Canberra = ACT Health monitors (Civic, Florey, Monash), daily means of hourly PM2.5 (pm2_5_1_hr) on local days, "
                    "only days with at least 18 hours; drawn as pillars but not part of the Sydney hero lane.")
    except Exception as e:  # pragma: no cover
        gaps.append(f"Canberra monitors dropped: ACT open data could not be read ({e}).")
    stations = [{"id": f"nsw{sid}", "name": s["SiteName"].title(), "lat": round(float(s["Latitude"]), 4),
                 "lon": round(float(s["Longitude"]), 4), "series": SL.clean(ser, 1)} for sid, (s, ser) in syd.items()]
    stations += [{"id": "act_" + nm.lower(), "name": f"{nm} (Canberra)", "lat": round(act_meta[nm][0], 4),
                  "lon": round(act_meta[nm][1], 4), "series": SL.clean(ser, 1)} for nm, ser in act.items()]
    syd_layer = {"id": "sydney_pm25", "type": "pillars", "name": "Sydney PM2.5",
                 "what": "Daily mean PM2.5 at Sydney monitors (NSW Government) and Canberra monitors (ACT Health), observed",
                 "color": "#ff4fa3", "unit": "ug/m3", "series": SL.clean(syd_mean, 1), "baseline": SL.clean(base_mean, 1),
                 "baseline_label": f"{base_years[0]} to {base_years[-1]} mean, same days", "stations": stations,
                 "series_label": "mean of Sydney monitors"}

    # ------------------------------------------------------------ GEOS-CF smoke, wind, heat (model)
    nh = N * 24
    pm, la, lo = FH.geoscf(ID, "aqc_tavg_1hr_g1440x721_v1", "pm25_rh35_gcc", T0, nh, 3, **GRID_BOX)
    pm_d = np.nanmean(pm.reshape(N, 8, *pm.shape[1:]), 1)
    tday = [d + 0.5 for d in range(N)]
    grid = SL.enc_grid(pm_d, 0.0, PM_VMAX, float(la[0]), float(la[-1]), float(lo[0]), float(lo[-1]), tday, "ug/m3",
                       kind="model", floor=PM_FLOOR)
    u, la_, lo_ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "u10m", T0, nh, 6, **GRID_BOX, lev=None)
    v, _, _ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "v10m", T0, nh, 6, **GRID_BOX, lev=None)
    ud, vd = (np.nanmean(x.reshape(N, 4, *x.shape[1:]), 1) for x in (u, v))
    u4, v4 = FH.block_mean(ud, 4), FH.block_mean(vd, 4)
    la4, lo4 = FH.block_centres(la_, 4), FH.block_centres(lo_, 4)
    wind = SL.enc_wind(u4, v4, float(la4[0]), float(la4[-1]), float(lo4[0]), float(lo4[-1]), tday,
                       source="GEOS-CF 10 m wind, daily mean, NASA GMAO (model)")
    iy, ix = int(np.argmin(abs(la + 33.87))), int(np.argmin(abs(lo - 151.0)))
    smoke = {"id": "smoke", "type": "particles", "name": "Smoke (model PM2.5)",
             "what": "GEOS-CF surface PM2.5 and 10 m wind, daily means, NASA GMAO Composition Forecast assimilation (model)",
             "color": "#c9b38f", "unit": "ug/m3", "series": SL.clean(pm_d[:, iy, ix], 1),
             "series_label": "model PM2.5 at Sydney, daily mean", "grid": grid, "wind": wind}
    gaps.append(f"Smoke = GEOS-CF surface PM2.5 (a model with satellite data assimilated, not a measurement), daily mean of 8 three-hourly values, "
                f"0.25 deg; drawn linear from a floor of {PM_FLOOR:.0f} to {PM_VMAX:.0f} ug/m3, higher values at full density. Particles move on GEOS-CF daily mean 10 m wind (1 deg).")
    t2, _, _ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "t2m", T0, nh, 3, **GRID_BOX, lev=None)
    t2d = np.nanmean(t2.reshape(N, 8, *t2.shape[1:]), 1) - 273.15
    t2max = np.nanmax(t2.reshape(N, 8, *t2.shape[1:]), 1) - 273.15
    t2b = FH.block_mean(t2d, 2)
    lab, lob = FH.block_centres(la, 2), FH.block_centres(lo, 2)
    heat = {"id": "heat", "type": "field", "palette": "heat", "name": "Heat 2 m (model)",
            "what": "GEOS-CF 2 m air temperature, daily mean, NASA GMAO (model)", "color": "#ff9d3b", "unit": "deg C",
            "series": SL.clean(t2d[:, iy, ix], 1), "series_label": "daily mean at Sydney, model cell 33.9S 151.0E",
            "grid": SL.enc_grid(t2b, 10.0, 40.0, float(lab[0]), float(lab[-1]), float(lob[0]), float(lob[-1]), tday, "deg C",
                                kind="model", floor=10.0)}
    gaps.append("Heat = GEOS-CF 2 m temperature (model) daily mean of 8 three-hourly values at 0.5 deg, drawn linear 10 to 40 deg C; "
                "daily means hide the afternoon peaks (for example the 48.9 deg C measured at Penrith on 4 January 2020).")

    # ------------------------------------------------------------ link
    lk = FH.link_dir(syd_mean, np.array(frp), 5, "days",
                     "Pearson r of daily values: Sydney mean PM2.5 (NSW monitors) vs SE Australia daily total FRP (VIIRS), fires leading by 0 to 5 days",
                     partner_leads=True, min_n=20)
    lk["lag_steps"] = lk.get("lag")
    can = None
    if act:
        cm = np.array([[np.nan if x is None else x for x in s] for s in act.values()])
        can = np.where(np.isfinite(cm).sum(0) > 0, np.nanmean(cm, 0), np.nan)
        lk_can = FH.link_dir(can, np.array(frp), 5, "days", "Canberra", partner_leads=True, min_n=20)

    # ------------------------------------------------------------ stats, beats, events
    pk = int(np.nanargmax(syd_mean))
    fpk = int(np.argmax(frp))
    norm = hero_norm["mean"]
    over = int(np.nansum(syd_mean > 25))
    datef = lambda d: (T0 + dt.timedelta(d)).strftime("%Y-%m-%d")  # noqa: E731
    stats = {
        "Sydney PM2.5 peak daily mean (ug/m3)": round(float(syd_mean[pk]), 1),
        "Sydney peak day": datef(pk),
        "Sydney highest single monitor day (ug/m3)": round(float(np.nanmax(mat)), 1),
        f"Sydney normal, {hero_norm['years']}, mean daily (ug/m3)": round(norm, 1),
        "peak vs normal (times)": round(float(syd_mean[pk]) / norm, 1),
        "peak vs normal (%)": SL.pct(float(syd_mean[pk]), norm),
        "window mean vs normal (%)": SL.pct(float(np.nanmean(syd_mean)), norm),
        "days Sydney mean above 25 ug/m3 (national daily standard)": over,
        "fire detections in window (SE Australia)": len(idx),
        "fire FRP peak day": datef(fpk),
        "fire FRP peak, daily total (MW)": round(frp[fpk]),
        "fire detections on peak day": cnt[fpk],
        "link r, Sydney PM2.5 vs fire FRP": lk.get("r"),
        "link lag, Sydney after fires (days)": None if lk.get("lag") is None else -lk["lag"],
        "link r at lag 0": lk.get("r_lag0"),
        "link n (days)": lk.get("n"),
        "GEOS-CF model peak daily PM2.5 at Sydney (ug/m3)": round(float(np.nanmax(pm_d[:, iy, ix])), 1),
        "Sydney cell (33.9S 151.0E) hottest daily mean, model (deg C)": round(float(np.nanmax(t2d[:, iy, ix])), 1),
        "Sydney cell (33.9S 151.0E) hottest hourly mean at 3-hourly samples, model (deg C)": round(float(np.nanmax(t2max[:, iy, ix])), 1),
    }
    if can is not None:
        cpk = int(np.nanargmax(can))
        stats.update({"Canberra PM2.5 peak daily mean (ug/m3)": round(float(can[cpk]), 1), "Canberra peak day": datef(cpk),
                      "link r, Canberra PM2.5 vs fire FRP": lk_can.get("r"),
                      "link lag, Canberra after fires (days)": None if lk_can.get("lag") is None else -lk_can["lag"]})
    lag_d = stats["link lag, Sydney after fires (days)"]
    # longest run of days with the Sydney mean above the national standard (25 ug/m3)
    runs, r0 = [], None
    for d in range(N + 1):
        hi = d < N and np.isfinite(syd_mean[d]) and syd_mean[d] > 25
        if hi and r0 is None:
            r0 = d
        if not hi and r0 is not None:
            runs.append((d - r0, r0, d - 1))
            r0 = None
    rl, ra, rb = max(runs)
    beats = [
        {"t": 0, "text": f"November 1, 2019. Fires are already burning in New South Wales. Sydney PM2.5 is {syd_mean[0]:.0f} micrograms per cubic metre today; the summer normal is about {norm:.0f}."},
        {"t": ra, "text": f"{(T0 + dt.timedelta(ra)).strftime('%B %-d')} to {(T0 + dt.timedelta(rb)).strftime('%B %-d')}: Sydney stays above the national daily standard for {rl} days in a row."},
        {"t": pk, "text": f"{(T0 + dt.timedelta(pk)).strftime('%B %-d')}: Sydney's worst day, PM2.5 {syd_mean[pk]:.0f}, {syd_mean[pk] / norm:.0f} times normal."},
        {"t": fpk, "text": f"{(T0 + dt.timedelta(fpk)).strftime('%B %-d')}: the fires peak, {cnt[fpk]:,} satellite detections and {frp[fpk] / 1000:.0f} thousand megawatts in one day."},
    ]
    if can is not None:
        beats.append({"t": cpk, "text": f"{(T0 + dt.timedelta(cpk)).strftime('%B %-d')}: Canberra's worst day of the window, daily PM2.5 {can[cpk]:.0f}."})
    beats.append({"t": N - 1, "text": f"February 15, end of the window. Over the summer Sydney PM2.5 was above the national daily standard on {over} days. "
                                      f"Daily Sydney PM2.5 and fire power: r = {lk['r']}, Sydney {lag_d} day{'s' if lag_d != 1 else ''} after the fires, "
                                      f"{'only a modest' if abs(lk['r']) < 0.4 else 'a ' + lk['strength']} link over {lk["n"]} days: wind direction mattered as much as fire power."})
    beats.sort(key=lambda b: b["t"])
    events = [{"t": pk, "label": f"Sydney peak {syd_mean[pk]:.0f} ug/m3"}, {"t": fpk, "label": "fire peak"}]
    if can is not None:
        events.append({"t": cpk, "label": f"Canberra {can[cpk]:.0f} ug/m3"})
    bands, s0 = [], None
    for d in range(N + 1):
        hi = d < N and np.isfinite(syd_mean[d]) and syd_mean[d] > 25
        if hi and s0 is None:
            s0 = d
        if not hi and s0 is not None:
            bands.append({"t0": s0, "t1": d, "label": "Sydney above 25 ug/m3"})
            s0 = None
    ng = SL.gap_count(SL.clean(syd_mean))
    gaps.append(f"{ng} day{'s' if ng != 1 else ''} without any Sydney PM2.5 value stay{'s' if ng == 1 else ''} empty.")
    gaps.append(f"The model smoke is much thicker over Sydney than measured (GEOS-CF peak daily mean {np.nanmax(pm_d[:, iy, ix]):.0f} vs "
                f"{np.nanmax(syd_mean):.0f} ug/m3 at the monitors): use the smoke layer for where the smoke went, the pillars for how much people breathed.")
    if lk.get("r") is not None and abs(lk["r"]) < 0.4:
        gaps.append(f"The Sydney link is modest (r {lk['r']} at {-lk['lag']} days, r {lk['r_lag0']} same day): Sydney's smoke depended on wind direction more than on "
                    f"total fire power" + (f"; Canberra, closer to the fires, links more clearly (r {lk_can['r']})." if can is not None else "."))
    gaps.append("The link uses all 107 days; long smoky runs make consecutive days similar, so r is indicative, not a test.")

    sources = [
        {"name": "VIIRS S-NPP 375 m active fires (VNP14IMG), country yearly CSV", "producer": "NASA FIRMS (LANCE / EOSDIS)",
         "resolution": "375 m, about 2 overpasses per day", "kind": "observed", "period": "2019-11-01 to 2020-02-15", "baseline": "none",
         "url": "https://firms.modaps.eosdis.nasa.gov/country/"},
        {"name": "PM2.5 daily averages, Sydney monitoring network", "producer": "NSW Government (Air Quality Monitoring Network)",
         "resolution": f"daily, {len(syd)} stations", "kind": "observed", "period": "2019-11-01 to 2020-02-15",
         "baseline": f"same window, {', '.join(base_years)}", "url": "https://www.airquality.nsw.gov.au/air-quality-data-services/data-download-facility"},
        {"name": "Air quality monitoring data (pm2_5_1_hr), Canberra", "producer": "ACT Health", "resolution": "hourly, 3 stations",
         "kind": "observed", "period": "2019-11-01 to 2020-02-15", "baseline": "none",
         "url": "https://www.data.act.gov.au/Environment/Air-Quality-Monitoring-Data/94a5-zqnn"},
        {"name": "GEOS-CF v1 assimilation, surface PM2.5 (pm25_rh35_gcc), 10 m wind, 2 m temperature", "producer": "NASA GMAO",
         "resolution": "0.25 deg hourly, used as daily means of 3- or 6-hourly values", "kind": "model",
         "period": "2019-11-01 to 2020-02-15", "baseline": "none", "url": "https://gmao.gsfc.nasa.gov/weather_prediction/GEOS-CF/"},
    ]
    obj = {"title": "Australia Black Summer", "timebase": "day", "t0": T0.strftime("%Y-%m-%dT%H:%MZ"), "step_s": 86400, "n": N,
           "region": {"lat0": -39.0, "lat1": -28.0, "lon0": 140.0, "lon1": 154.0}, "hero": "sydney_pm25", "partner": "fires",
           "link": lk, "hero_norm": hero_norm, "stats": stats, "gaps": gaps, "beats": beats, "events": events, "bands": bands,
           "sources": sources, "layers": [syd_layer, fires, smoke, heat], "script": "e4_black_summer.py"}
    SL.write_story(ID, obj)


if __name__ == "__main__":
    main()
