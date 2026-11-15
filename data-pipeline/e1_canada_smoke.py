"""E1 Canada fires to the New York orange sky (2023-05-25 .. 2023-06-15, hourly).

Layers: fires (FIRMS VIIRS SNPP, Quebec + Ontario), smoke (GEOS-CF PM2.5 surface + GEOS-CF 10 m wind, model),
nyc_pm25 (OpenAQ hourly PM2.5, NYC regulatory monitors), wind streaks (GEOS-CF, model).
hero = nyc_pm25, partner = fires. Link on daily means: NYC PM2.5 vs Quebec FRP, Quebec leading by 0..5 days.

Run: /Users/mykhayloolefirenko/.venvs/omi/bin/python data-pipeline/e1_canada_smoke.py   (network, cache outside repo)
"""
import datetime as dt
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402
import fire_helpers as FH  # noqa: E402

ID = "e1_canada_smoke"
T0 = dt.datetime(2023, 5, 25)
NDAY = 22
N = NDAY * 24
BASE_YEARS = [2018, 2019, 2020, 2021, 2022]
BBOX = dict(lat0=35.0, lat1=60.0, lon0=-95.0, lon1=-60.0)
# NYC (five boroughs) regulatory PM2.5 monitors in the OpenAQ archive (AirNow feed), ids found by scanning the archive
NYC = [384, 625, 626, 628, 631, 648, 664, 665, 673]
PM_VMAX, PM_FLOOR = 150.0, 15.0


def in_quebec(lat, lon):
    q = (lat >= 45) & (lat <= 63) & (lon >= -79.5) & (lon <= -57)
    maritimes = (lat < 47.5) & (lon > -69.5)  # New Brunswick / Nova Scotia (incl. the Halifax/Shelburne fires)
    return q & ~maritimes


def in_ontario(lat, lon):
    return (lat >= 41.6) & (lat <= 57) & (lon >= -95.2) & (lon < -79.5)


def daily_hold(daily):
    return [None if v is None else v for v in daily for _ in range(24)]


def main():
    gaps = []
    # ------------------------------------------------------------ fires
    f = FH.firms(ID, 2023, "Canada")
    tt = (f["time"] - np.datetime64(T0, "m")).astype("timedelta64[m]").astype(float) / 60.0  # hours since t0
    keep = (tt >= 0) & (tt < N) & (f["type"] == 0) & (f["conf"] != "l")
    qc = in_quebec(f["lat"], f["lon"]) & keep
    on = in_ontario(f["lat"], f["lon"]) & keep
    sel = qc | on
    day = np.floor(tt / 24).astype(int)
    frp_all = [float(f["frp"][sel & (day == d)].sum()) for d in range(NDAY)]
    frp_qc = [float(f["frp"][qc & (day == d)].sum()) for d in range(NDAY)]
    cnt_qc = [int((qc & (day == d)).sum()) for d in range(NDAY)]
    idx = np.where(sel)[0]
    n_fire = len(idx)
    sub = idx[FH.even_subsample(tt[idx], 30000)]
    sub = sub[np.argsort(tt[sub])]
    if n_fire > 30000:
        gaps.append(f"Fire points: {n_fire:,} VIIRS detections in Quebec and Ontario in the window; 30,000 drawn, "
                    f"subsampled evenly in time. The daily FRP totals use all {n_fire:,}.")
    vmax_frp = float(np.percentile(f["frp"][sel], 99))
    gaps.append(f"Fire point size is linear in FRP up to {vmax_frp:.0f} MW (99th percentile); the few larger detections are drawn at that size.")
    gaps.append("Quebec and Ontario are approximated by boxes (Quebec 45-63N, 79.5-57W without New Brunswick and Nova Scotia, which also takes in a little of Labrador; Ontario 41.6-57N, 95.2-79.5W). Only nominal and high confidence vegetation fire detections are used.")
    gaps.append("VIIRS sees each place about twice a day (around 01:30 and 13:30 local), so fire points arrive in two bursts per day, and smoke or cloud can hide fires.")
    fires = {
        "id": "fires", "type": "points", "name": "Fires (Quebec, Ontario)",
        "what": "VIIRS SNPP active fire detections, NASA FIRMS (observed); lane = daily total fire radiative power",
        "color": "#ff7a1a", "unit": "MW (daily total FRP)",
        "series": SL.clean(daily_hold(frp_all), 1),
        "points": {"lat": SL.clean(f["lat"][sub], 3), "lon": SL.clean(f["lon"][sub], 3),
                   "t": SL.clean(tt[sub], 2), "v": SL.clean(f["frp"][sub], 1)},
        "vmax": round(vmax_frp, 1), "series_label": "daily total (held across the day's hours)",
    }

    # ------------------------------------------------------------ NYC PM2.5 (OpenAQ)
    def nyc_block(year):
        start = T0.replace(year=year)
        days = [(start + dt.timedelta(d)).date() for d in range(NDAY)]
        hours = [start + dt.timedelta(hours=h) for h in range(N)]
        st = []
        for loc in NYC:
            vals, meta = FH.openaq_hourly(ID, loc, days)
            st.append(([vals.get(h) for h in hours], meta, loc))
        return st

    stations = nyc_block(2023)
    mat = np.array([[np.nan if v is None else v for v in s[0]] for s in stations])
    with np.errstate(all="ignore"):
        import warnings
        warnings.simplefilter("ignore")
        nyc = np.nanmean(mat, 0)
    nst = np.isfinite(mat).sum(0)
    nyc[nst == 0] = np.nan
    used = [s for s in stations if np.isfinite(np.array([np.nan if v is None else v for v in s[0]], float)).sum() > 0]
    gaps.append(f"NYC PM2.5 = mean of the {len(used)} reporting OpenAQ monitors in the five boroughs in each hour "
                f"(median {int(np.median(nst))} monitors per hour); {int((nst == 0).sum())} hour(s) with no monitor stay empty. Hour stamps are OpenAQ's, converted to UTC.")
    gaps.append("OpenAQ hourly values are the preliminary AirNow feed (not the final EPA AQS record); values below -5 or above 1000 ug/m3 are dropped as errors.")

    base = []
    for y in BASE_YEARS:
        st = nyc_block(y)
        m = np.array([[np.nan if v is None else v for v in s[0]] for s in st])
        with np.errstate(all="ignore"):
            import warnings
            warnings.simplefilter("ignore")
            b = np.nanmean(m, 0)
        base.append(b)
    base = np.array(base)
    cover = {y: int(np.isfinite(b).sum()) for y, b in zip(BASE_YEARS, base)}
    base_ok = [y for y in BASE_YEARS if cover[y] > 0.25 * N]
    dropped = [y for y in BASE_YEARS if y not in base_ok]
    base = np.array([b for y, b in zip(BASE_YEARS, base) if y in base_ok])
    import warnings
    warnings.simplefilter("ignore")
    base_mean = np.nanmean(base, 0)
    years_lbl = ", ".join(map(str, base_ok))
    gaps.append(f"Normal = NYC monitors in the same window of {years_lbl} (hours with data per year: "
                + ", ".join(f"{y}: {cover[y]}" for y in base_ok) + f" of {N})"
                + (f"; {', '.join(map(str, dropped))} left out, the OpenAQ archive has (almost) no NYC PM2.5 for that window." if dropped else "."))
    hero_norm = SL.norm_stats(base.ravel(), years_lbl,
                              "hourly NYC monitor-mean PM2.5, same calendar window (May 25 to Jun 15) in each baseline year")
    hero_norm["base"] = SL.clean(base_mean, 2)
    pillars = []
    for vals, meta, loc in used:
        pillars.append({"id": str(loc), "name": meta["name"].rsplit("-", 1)[0], "lat": round(meta["lat"], 4),
                        "lon": round(meta["lon"], 4), "series": SL.clean(vals, 1)})
    nyc_layer = {
        "id": "nyc_pm25", "type": "pillars", "name": "New York PM2.5",
        "what": "Hourly PM2.5 at New York City monitors, OpenAQ archive of the AirNow feed (observed)",
        "color": "#ff4fa3", "unit": "ug/m3", "series": SL.clean(nyc, 1), "baseline": SL.clean(base_mean, 1),
        "baseline_label": f"mean of {years_lbl}, same hours", "stations": pillars,
    }

    # ------------------------------------------------------------ GEOS-CF smoke (model)
    pm, la, lo = FH.geoscf(ID, "aqc_tavg_1hr_g1440x721_v1", "pm25_rh35_gcc", T0, N, 3, **BBOX)
    pm2 = FH.block_mean(pm, 2)
    la2, lo2 = FH.block_centres(la, 2), FH.block_centres(lo, 2)
    tpm = [s + 0.5 for s in range(0, N, 3)]
    grid = SL.enc_grid(pm2, 0.0, PM_VMAX, float(la2[0]), float(la2[-1]), float(lo2[0]), float(lo2[-1]), tpm,
                       "ug/m3", kind="model", floor=PM_FLOOR)
    u, la_, lo_ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "u10m", T0, N, 6, **BBOX, lev=None)
    v, _, _ = FH.geoscf(ID, "met_tavg_1hr_g1440x721_x1", "v10m", T0, N, 6, **BBOX, lev=None)
    u4, v4 = FH.block_mean(u, 4), FH.block_mean(v, 4)
    la4, lo4 = FH.block_centres(la_, 4), FH.block_centres(lo_, 4)
    tw = [s + 0.5 for s in range(0, N, 6)]
    wind = SL.enc_wind(u4, v4, float(la4[0]), float(la4[-1]), float(lo4[0]), float(lo4[-1]), tw,
                       source="GEOS-CF 10 m wind, NASA GMAO (model)")
    # model PM2.5 at NYC (nearest 0.25 cell to 40.75N 73.95W), hourly series of the smoke lane = smoke over the
    # box of the five boroughs, every 3 h, None in between (not interpolated)
    iy, ix = int(np.argmin(abs(la - 40.75))), int(np.argmin(abs(lo + 73.95)))
    model_nyc = [None] * N
    for k, s in enumerate(range(0, N, 3)):
        model_nyc[s] = float(pm[k, iy, ix])
    gaps.append(f"Smoke = GEOS-CF surface PM2.5 (a model with satellite data assimilated, not a measurement), every 3 h, "
                f"0.25 deg averaged to 0.5 deg; drawn linear from a floor of {PM_FLOOR:.0f} ug/m3 to {PM_VMAX:.0f} ug/m3 "
                f"(higher values near the fires drawn at full density). Its lane is the model value at New York, every 3 h, empty in between.")
    gaps.append(f"The model and the monitors differ: GEOS-CF peaks at {np.nanmax([x for x in model_nyc if x is not None]):.0f} ug/m3 over New York vs "
                f"{np.nanmax(nyc):.0f} for the hourly monitor mean; use the smoke layer for where the smoke went, the pillars for what was measured.")
    gaps.append("Smoke particles move on GEOS-CF 10 m wind (model, 1 deg, every 6 h); the real smoke also travelled higher up, where winds differ.")
    smoke = {
        "id": "smoke", "type": "particles", "name": "Smoke (model PM2.5)",
        "what": "GEOS-CF surface PM2.5 and 10 m wind, NASA GMAO Composition Forecast assimilation (model)",
        "color": "#c9b38f", "unit": "ug/m3", "series": SL.clean(model_nyc, 1), "series_label": "model PM2.5 at New York",
        "grid": grid, "wind": wind,
    }
    streaks = {"id": "wind", "type": "streaks", "name": "Wind 10 m (model)",
               "what": "GEOS-CF 10 m wind, NASA GMAO (model)", "color": "#9fc6ff", "unit": "m/s",
               "series": SL.clean([None if s % 6 else float(np.hypot(u[s // 6, iy, ix], v[s // 6, iy, ix])) for s in range(N)], 2),
               "series_label": "wind speed at New York, every 6 h", "wind": wind}

    # ------------------------------------------------------------ link (daily means)
    nyc_d = np.array([np.nanmean(nyc[d * 24:(d + 1) * 24]) if np.isfinite(nyc[d * 24:(d + 1) * 24]).sum() >= 18 else np.nan
                      for d in range(NDAY)])
    if np.isnan(nyc_d).any():
        gaps.append(f"{int(np.isnan(nyc_d).sum())} days with fewer than 18 hours of NYC data left out of the daily link.")
    lk = FH.link_dir(nyc_d, np.array(frp_qc), 5, "days",
                     "Pearson r of daily means: NYC PM2.5 (OpenAQ) vs Quebec daily total FRP (VIIRS), Quebec leading by 0 to 5 days",
                     partner_leads=True, min_n=10)
    lk["lag_steps"] = lk["lag"] * 24 if lk.get("lag") is not None else None
    lk_all = FH.link_dir(nyc_d, np.array(frp_all), 5, "days", "same, Quebec + Ontario FRP", partner_leads=True, min_n=10)

    # ------------------------------------------------------------ stats, beats, events
    pk = int(np.nanargmax(nyc))
    pk_t = T0 + dt.timedelta(hours=pk)
    norm = hero_norm["mean"]
    qpk = int(np.argmax(frp_qc))
    nyc_dpk = int(np.nanargmax(nyc_d))
    base_d = np.nanmean(base_mean.reshape(NDAY, 24), 1)
    lag_days = -lk["lag"] if lk.get("lag") is not None else None
    stats = {
        "NYC PM2.5 peak, hourly monitor mean (ug/m3)": round(float(nyc[pk]), 1),
        "NYC peak hour (UTC)": pk_t.strftime("%Y-%m-%d %H:00"),
        "NYC peak hour (New York time, EDT)": (pk_t - dt.timedelta(hours=4)).strftime("%Y-%m-%d %H:00"),
        "NYC highest single monitor hour (ug/m3)": round(float(np.nanmax(mat)), 1),
        f"NYC normal, {hero_norm['years']} same window, mean hourly (ug/m3)": round(norm, 1),
        "peak vs normal (times)": round(float(nyc[pk]) / norm, 1),
        "peak vs normal (%)": SL.pct(float(nyc[pk]), norm),
        "NYC highest daily mean (ug/m3)": round(float(nyc_d[nyc_dpk]), 1),
        "NYC highest daily mean date": (T0 + dt.timedelta(nyc_dpk)).strftime("%Y-%m-%d"),
        "highest daily mean vs same day normal (times)": round(float(nyc_d[nyc_dpk] / base_d[nyc_dpk]), 1),
        "Quebec FRP peak day": (T0 + dt.timedelta(qpk)).strftime("%Y-%m-%d"),
        "Quebec FRP peak, daily total (MW)": round(frp_qc[qpk]),
        "Quebec fire detections on the peak day": cnt_qc[qpk],
        "fire detections in window, Quebec + Ontario": n_fire,
        "link r, NYC daily PM2.5 vs Quebec FRP": lk.get("r"),
        "link lag, NYC after Quebec (days)": lag_days,
        "link r at lag 0": lk.get("r_lag0"),
        "link n (days)": lk.get("n"),
        "link r with Quebec + Ontario FRP": lk_all.get("r"),
        "link lag with Quebec + Ontario FRP (days)": None if lk_all.get("lag") is None else -lk_all["lag"],
        "GEOS-CF model PM2.5 at NYC, peak (ug/m3)": round(float(np.nanmax([x for x in model_nyc if x is not None])), 1),
        "hours with NYC mean above 35 ug/m3": int(np.nansum(nyc > 35)),
    }

    def step_of(d):
        return d * 24

    first_q = next((d for d in range(NDAY) if frp_qc[d] > 0.25 * frp_qc[qpk]), qpk)
    beats = [
        {"t": 0, "text": f"May 25, 2023. New York air is normal for late spring, about {norm:.0f} micrograms of PM2.5 per cubic metre."},
        {"t": step_of(first_q), "text": f"{(T0 + dt.timedelta(first_q)).strftime('%B %-d')}: fires spread across Quebec, {cnt_qc[first_q]:,} satellite fire detections in one day."},
        {"t": step_of(qpk), "text": f"{(T0 + dt.timedelta(qpk)).strftime('%B %-d')}: Quebec fires peak, {frp_qc[qpk] / 1000:.0f} thousand megawatts of fire radiative power in one day."},
        {"t": pk, "text": f"{(pk_t - dt.timedelta(hours=4)).strftime('%B %-d, around %-I %p')} New York time: PM2.5 reaches {nyc[pk]:.0f}, {nyc[pk] / norm:.0f} times the normal for this time of year."},
        {"t": step_of(nyc_dpk) + 23, "text": f"The daily mean on {(T0 + dt.timedelta(nyc_dpk)).strftime('%B %-d')} is {nyc_d[nyc_dpk]:.0f}, the worst day of the window."},
        {"t": N - 1, "text": f"By June 15 the air clears. Daily New York PM2.5 and Quebec fire power line up with r = {lk['r']}, "
                             f"New York {lag_days} day{'s' if lag_days != 1 else ''} after Quebec, a {lk['strength']} link over {lk['n']} days."},
    ]
    beats.sort(key=lambda b: b["t"])
    events = [{"t": step_of(qpk) + 12, "label": "Quebec fire peak"}, {"t": pk, "label": f"NYC peak {nyc[pk]:.0f} ug/m3"}]
    bands, inb = [], None
    for s in range(N):
        hi = np.isfinite(nyc[s]) and nyc[s] > 35
        if hi and inb is None:
            inb = s
        if (not hi or s == N - 1) and inb is not None:
            if s - inb >= 3:
                bands.append({"t0": inb, "t1": s, "label": "NYC above 35 ug/m3"})
            inb = None
    gaps.append("Link is computed on daily means with only 22 days, so r is indicative; lags 0 to 5 days were tried with Quebec leading.")

    sources = [
        {"name": "VIIRS S-NPP 375 m active fires (VNP14IMG), country yearly CSV", "producer": "NASA FIRMS (LANCE / EOSDIS)",
         "resolution": "375 m, about 2 overpasses per day", "kind": "observed", "period": "2023-05-25 to 2023-06-15", "baseline": "none",
         "url": "https://firms.modaps.eosdis.nasa.gov/country/"},
        {"name": "PM2.5 hourly, New York City monitors (AirNow feed via OpenAQ)", "producer": "NYSDEC / US EPA AirNow, archived by OpenAQ",
         "resolution": f"hourly, {len(used)} stations", "kind": "observed", "period": "2023-05-25 to 2023-06-15",
         "baseline": f"same window in {hero_norm['years']}", "url": "https://openaq.org/"},
        {"name": "GEOS-CF v1 assimilation, surface PM2.5 (pm25_rh35_gcc) and 10 m wind", "producer": "NASA GMAO",
         "resolution": "0.25 deg hourly, used at 0.5 deg every 3 h (PM2.5) and 1 deg every 6 h (wind)", "kind": "model",
         "period": "2023-05-25 to 2023-06-15", "baseline": "none", "url": "https://gmao.gsfc.nasa.gov/weather_prediction/GEOS-CF/"},
    ]
    obj = {
        "title": "Canada fires to the New York orange sky", "timebase": "hour", "t0": T0.strftime("%Y-%m-%dT%H:%MZ"),
        "step_s": 3600, "n": N, "region": {"lat0": 38.0, "lat1": 56.0, "lon0": -95.0, "lon1": -60.0},
        "hero": "nyc_pm25", "partner": "fires", "link": lk, "hero_norm": hero_norm, "stats": stats, "gaps": gaps,
        "beats": beats, "events": events, "bands": bands, "sources": sources,
        "layers": [nyc_layer, fires, smoke, streaks], "script": "e1_canada_smoke.py",
    }
    SL.write_story(ID, obj)


if __name__ == "__main__":
    main()
