"""E3 Hunga Tonga-Hunga Ha'apai pressure wave, 2022-01-14 00Z .. 2022-01-18 23Z, hourly steps (n = 120).

Origin: USGS event us7000gc8r (volcanic eruption, 2022-01-15 04:14:45 UTC, 20.546S 175.390W).
Layers
  ring      expected Lamb wave front at 315 m/s from the origin (reference, not data; published 310 to 320 m/s)
  pressure  ERA5 hourly surface pressure (model) via Open-Meteo at the grid cell nearest 15 CO-OPS gauges,
            high-passed: least squares fit (constant, linear, quadratic, 24 h, 12 h, 8 h harmonics) over 11-21 Jan removed,
            then a centred 7 hour running mean removed. Lane = mean anomaly of the 15 points.
  gauges    NOAA CO-OPS 6 minute water level minus the CO-OPS tide prediction, minus a centred 3 hour running mean
            (keeps periods under ~3 h: tsunami / meteotsunami). Station series = hourly maximum |residual| (amplitude envelope).
Check: a transect of 30 ERA5 points along the great circle Tonga to San Francisco (Hovmoller), arrival fit.

Run: /Users/mykhayloolefirenko/.venvs/omi/bin/python data-pipeline/e3_tonga.py
"""
import datetime as dt
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402

ID = "e3_tonga"
T0 = dt.datetime(2022, 1, 14, tzinfo=dt.timezone.utc)
N = 5 * 24
OM = "https://archive-api.open-meteo.com/v1/archive"
COOPS = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=us7000gc8r&format=geojson"
SPEED = 315.0  # m/s
GAUGES = ["1770000", "1820000", "1890000", "1630000", "1619910", "1612340", "1617760", "9461380", "9457292",
          "9419750", "9414290", "9412110", "9410230", "8724580", "9755371"]
FIT0 = dt.datetime(2022, 1, 11, tzinfo=dt.timezone.utc)  # ERA5 fetch window 11..21 Jan (fit), story = 14..18 Jan
OFF = int((T0 - FIT0).total_seconds() // 3600)


def gc_km(a, b, c, d):
    a, b, c, d = map(math.radians, (a, b, c, d))
    return 6371.0 * math.acos(max(-1, min(1, math.sin(a) * math.sin(c) + math.cos(a) * math.cos(c) * math.cos(b - d))))


def highpass_p(p):
    t = np.arange(len(p), dtype=float)
    A = np.array([np.ones_like(t), t / 100, (t / 100) ** 2] + [f(2 * np.pi * t / P) for P in (24, 12, 8) for f in (np.cos, np.sin)]).T
    ok = np.isfinite(p)
    c, *_ = np.linalg.lstsq(A[ok], p[ok], rcond=None)
    q = p - A @ c
    W = 7
    r = q - np.convolve(q, np.ones(W) / W, "same")
    r[:W // 2] = np.nan
    r[-(W // 2):] = np.nan
    return r


def era5(lats, lons, name):
    url = (f"{OM}?latitude={','.join(f'{x:.3f}' for x in lats)}&longitude={','.join(f'{x:.3f}' for x in lons)}"
           f"&start_date=2022-01-11&end_date=2022-01-21&hourly=surface_pressure&models=era5&timezone=GMT")
    d = SL.fetch_json(url, ID, name=name)
    return d if isinstance(d, list) else [d]


def coops(sid, product):
    url = (f"{COOPS}?product={product}&station={sid}&begin_date=20220114&end_date=20220118%2023:59"
           f"&datum=MSL&units=metric&time_zone=gmt&format=json&application=earthjukebox")
    d = SL.fetch_json(url, ID, name=f"{product}_{sid}.json")
    if "error" in d:
        return None, None
    x = np.full(N * 10, np.nan)
    for r in d.get("data") or d.get("predictions"):
        t = dt.datetime.strptime(r["t"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
        k = int(round((t - T0).total_seconds() / 360))
        if 0 <= k < N * 10 and r["v"] not in ("", None):
            x[k] = float(r["v"])
    return d.get("metadata"), x


def running_mean_nan(x, w):
    v = np.where(np.isfinite(x), x, 0.0)
    c = np.convolve(v, np.ones(w), "same")
    n = np.convolve(np.isfinite(x).astype(float), np.ones(w), "same")
    with np.errstate(all="ignore"):
        out = c / n
    out[n < w * 0.7] = np.nan
    return out


def parabolic_peak(r, k):
    y0, y1, y2 = r[k - 1], r[k], r[k + 1]
    den = y0 - 2 * y1 + y2
    return k + (0.5 * (y0 - y2) / den if den not in (0,) and np.isfinite(den) else 0.0)


def transect(ev):
    la1, lo1 = 37.8, -122.5
    a1, b1, a2, b2 = map(math.radians, (ev["lat"], ev["lon"], la1, lo1))
    dd = math.acos(math.sin(a1) * math.sin(a2) + math.cos(a1) * math.cos(a2) * math.cos(b2 - b1))
    fs = np.linspace(0.06, 1, 30)
    pts = []
    for f in fs:
        A, B = math.sin((1 - f) * dd) / math.sin(dd), math.sin(f * dd) / math.sin(dd)
        x = A * math.cos(a1) * math.cos(b1) + B * math.cos(a2) * math.cos(b2)
        y = A * math.cos(a1) * math.sin(b1) + B * math.cos(a2) * math.sin(b2)
        z = A * math.sin(a1) + B * math.sin(a2)
        pts.append((math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x)), dd * 6371 * f))
    d = era5([p[0] for p in pts], [p[1] for p in pts], "era5_transect.json")
    rows = []
    for (la, lo, dist), x in zip(pts, d):
        r = highpass_p(np.array(x["hourly"]["surface_pressure"], float))
        eta = OFF + ev["t"] + dist * 1000 / SPEED / 3600
        k0 = int(round(eta))
        w = np.arange(k0 - 2, k0 + 3)
        k = int(w[np.nanargmax(r[w])])
        rows.append((dist, parabolic_peak(r, k) - OFF - ev["t"], eta - OFF - ev["t"], float(r[k])))
    rows = np.array(rows)
    far = rows[rows[:, 0] > 4000]
    # Theil-Sen slope (robust) of distance vs arrival time
    sl = [(far[j, 0] - far[i, 0]) / (far[j, 1] - far[i, 1]) for i in range(len(far)) for j in range(i + 1, len(far)) if far[j, 1] != far[i, 1]]
    speed = float(np.median(sl)) * 1000 / 3600
    return {"points": len(rows), "fit_range_km": "4000 to 8520", "speed_ms_theil_sen": round(speed, 1),
            "mean_peak_hpa": round(float(far[:, 3].mean()), 2),
            "mean_abs_arrival_error_h": round(float(np.mean(np.abs(far[:, 1] - far[:, 2]))), 2),
            "rows": [[round(a, 0), round(b, 2), round(c, 2), round(e, 2)] for a, b, c, e in rows],
            "rows_note": "distance km, ERA5 peak arrival h after eruption (parabolic sub-hour), expected at 315 m/s, peak high-passed hPa"}


def main():
    q = SL.fetch_json(USGS, ID, name="usgs_us7000gc8r.json")
    lon, lat, _ = q["geometry"]["coordinates"]
    te = dt.datetime.fromtimestamp(q["properties"]["time"] / 1000, dt.timezone.utc)
    ev = {"lat": lat, "lon": lon, "t": (te - T0).total_seconds() / 3600, "time": te}
    print("eruption", te, lat, lon, "step", ev["t"])

    metas, wl = {}, {}
    for sid in GAUGES:
        m, x = coops(sid, "water_level")
        _, p = coops(sid, "predictions")
        if m is None or p is None:
            print("drop", sid)
            continue
        metas[sid], wl[sid] = m, (x, p)
    sids = list(metas)
    pts = era5([float(metas[s]["lat"]) for s in sids], [float(metas[s]["lon"]) for s in sids], "era5_gauges.json")

    stations_p, stations_g, table = [], [], []
    P = []  # hourly pressure anomalies (N)
    G = []  # hourly envelopes (N)
    for sid, x in zip(sids, pts):
        m = metas[sid]
        la, lo = float(m["lat"]), float(m["lon"])
        dist = gc_km(lat, lon, la, lo)
        eta = ev["t"] + dist * 1000 / SPEED / 3600  # story hours
        raw = np.array(x["hourly"]["surface_pressure"], float)
        r_full = highpass_p(raw)
        r = r_full[OFF:OFF + N]
        k0 = int(round(eta))
        w = np.arange(k0 - 1, k0 + 2)
        kk = int(w[np.nanargmax(r[w])])
        t_peak = parabolic_peak(r, kk)
        pre = r[:int(ev["t"])]
        sd_pre = float(np.nanstd(pre))
        # gauges
        obs, pred = wl[sid]
        res = obs - pred
        hp = res - running_mean_nan(res, 31)
        env = np.array([np.nanmax(np.abs(hp[h * 10:(h + 1) * 10])) if np.isfinite(hp[h * 10:(h + 1) * 10]).sum() >= 6 else np.nan
                        for h in range(N)])
        e0 = int(ev["t"] * 10)
        sd_g = float(np.nanstd(hp[:e0]))
        over = np.where(np.abs(hp[e0:]) > 5 * sd_g)[0]
        g_arr = (e0 + over[0]) / 10 if len(over) else None
        gmax_i = int(np.nanargmax(np.abs(hp[e0:]))) + e0
        P.append(r)
        G.append(env)
        name = m["name"].split(",")[0]
        stations_p.append({"id": sid, "name": name, "lat": x["latitude"], "lon": x["longitude"], "series": SL.clean(r, 3)})
        stations_g.append({"id": sid, "name": name, "lat": la, "lon": lo, "series": SL.clean(env, 3),
                           "residual_6min": SL.clean(hp, 3)})
        table.append({"station": name, "id": sid, "distance_km": round(dist), "expected_h_after": round(eta - ev["t"], 2),
                      "era5_peak_h_after": round(t_peak - ev["t"], 2), "era5_peak_hpa": round(float(r[kk]), 2),
                      "era5_noise_sd_hpa": round(sd_pre, 2), "era5_peak_over_noise": round(float(r[kk]) / sd_pre, 1),
                      "gauge_first_h_after": None if g_arr is None else round(g_arr - ev["t"], 2),
                      "gauge_max_abs_m": round(float(abs(hp[gmax_i])), 3), "gauge_max_h_after": round(gmax_i / 10 - ev["t"], 2),
                      "gauge_noise_sd_m": round(sd_g, 3), "gauge_gaps_6min": int(np.isnan(obs).sum())})
        print(table[-1])
    P, G = np.array(P), np.array(G)

    tr = transect(ev)
    print("transect", {k: v for k, v in tr.items() if k != "rows"})

    with np.errstate(all="ignore"):
        hero = np.nanmean(P, 0)
        gl = np.nanmean(G, 0)
    # pooled link: per-station pressure anomaly vs the same station's gauge envelope, lags 0..6 h
    curve = []
    for k in range(0, 7):
        xs, ys = [], []
        for i in range(len(sids)):
            a, b = SL._pairs(P[i], G[i], k)
            xs.append(a); ys.append(b)
        a, b = np.concatenate(xs), np.concatenate(ys)
        curve.append([k, round(float(np.corrcoef(a, b)[0, 1]), 3), int(len(a))])
    kb, rb, nb = max(curve, key=lambda c: c[1])
    lk_lane = SL.link(SL.clean(hero), SL.clean(gl), 6, "hour", "lanes: mean ERA5 anomaly vs mean gauge envelope")
    lk = {"r": rb, "lag": kb, "n": nb, "lag_unit": "hour", "sign": "positive" if rb > 0 else "negative",
          "strength": "strong" if abs(rb) >= .6 else "moderate" if abs(rb) >= .3 else "weak",
          "method": "pooled Pearson r over 15 stations: ERA5 high-passed pressure anomaly at each gauge vs that gauge's hourly max |water residual|, gauge lagged 0..6 h",
          "curve": [[c[0], c[1]] for c in curve], "lanes": {k: lk_lane.get(k) for k in ("r", "lag", "n", "strength", "method")}}

    # arrival link across stations: ERA5 air-wave peak time vs first clear water response at the same gauge
    ta = np.array([[t["era5_peak_h_after"], t["gauge_first_h_after"]] for t in table if t["gauge_first_h_after"] is not None])
    r_arr = float(np.corrcoef(ta[:, 0], ta[:, 1])[0, 1])
    delay = float(np.median(ta[:, 1] - ta[:, 0]))
    lk["arrivals"] = {"r": round(r_arr, 3), "n": int(len(ta)), "median_water_after_air_h": round(delay, 2),
                      "method": "Pearson r across gauges: ERA5 pressure peak time vs time the gauge residual first exceeds 5 x its pre-eruption sd"}
    print("arrival link", lk["arrivals"])

    # numbers
    pk = np.array([t["era5_peak_h_after"] - t["expected_h_after"] for t in table])
    over = [t for t in table if t["era5_peak_hpa"] >= 0.5]
    big = max(table, key=lambda t: t["gauge_max_abs_m"])
    hon = next(t for t in table if t["id"] == "1612340")
    sfo = next(t for t in table if t["id"] == "9414290")
    e_step = ev["t"]
    stats = {
        "eruption (USGS us7000gc8r)": te.strftime("%d %b %Y %H:%M:%S UTC"),
        "reference front speed (m/s)": SPEED,
        "ERA5 transect speed fit, 4000 to 8520 km (m/s, model)": tr["speed_ms_theil_sen"],
        "ERA5 transect mean peak (hPa, model)": tr["mean_peak_hpa"],
        "ERA5 transect mean arrival error vs 315 m/s (h)": tr["mean_abs_arrival_error_h"],
        "gauge points with ERA5 peak of 0.5 hPa or more near the expected time": f"{len(over)} of {len(table)}",
        "ERA5 peak timing vs expected, median (h)": round(float(np.median(pk)), 2),
        "Honolulu ERA5 peak (hPa)": hon["era5_peak_hpa"],
        "Honolulu expected arrival (h after eruption)": hon["expected_h_after"],
        "San Francisco ERA5 peak (hPa)": sfo["era5_peak_hpa"],
        "largest water oscillation": f"{big['station']} {big['gauge_max_abs_m']} m at {big['gauge_max_h_after']} h after the eruption",
        "pooled link r (pressure to water)": rb,
        "pooled link lag (h)": kb,
        "arrival link r (air peak time vs first water response, across gauges)": round(r_arr, 2),
        "median water response after the ERA5 air peak (h)": round(delay, 2),
        "stations": len(table),
    }
    gaps = [
        "ERA5 is a reanalysis model, hourly at about 31 km. Barometers measured a jump of roughly 2 hPa thousands of km away; ERA5 shows a smoothed bump of about 0.3 to 0.8 hPa, so the pressure lane underestimates the real wave.",
        "The pressure lane is high-passed (fit of 24, 12 and 8 hour cycles plus a slow trend removed, then a 7 hour running mean removed): weather fronts also leave wiggles of a few tenths of hPa.",
        "The ring is a reference front drawn at 315 m/s from the USGS origin, not data.",
        "Gauge series = hourly maximum of |water level minus tide prediction minus a 3 hour running mean|, from 6 minute data: it keeps the amplitude of the oscillation, not its sign.",
        "Ocean tsunami waves travel slower than the air wave; at far gauges the water responds first to the air wave (meteotsunami), then to the ocean tsunami hours later.",
        "The ERA5 point is the 0.25 deg grid cell nearest each gauge.",
        "The arrival link (r across gauges) is high partly because both the air wave and the water response arrive later at farther gauges; the hour by hour pooled link is weak because the water keeps ringing for many hours after a one hour air pulse.",
        "Key West and San Juan (Atlantic side) show no clear ERA5 pressure peak; their water response comes about a day later.",
    ]
    for t in table:
        if t["gauge_gaps_6min"]:
            gaps.append(f"{t['station']}: {t['gauge_gaps_6min']} missing 6 minute readings (left empty)")
    if len(sids) < len(GAUGES):
        gaps.append(f"{len(GAUGES) - len(sids)} gauges dropped (no data or no tide prediction)")

    events = [{"t": round(e_step, 3), "label": "eruption 04:14 UTC"}]
    for t in sorted(table, key=lambda t: t["expected_h_after"]):
        if t["id"] in ("1612340", "9414290", "8724580", "1770000"):
            events.append({"t": round(e_step + t["expected_h_after"], 2), "label": f"expected front at {t['station']}"})
    beats = [
        {"t": 0, "text": "14 January 2022. Fifteen tide gauges across the Pacific and the US coasts, the air pressure above them from ERA5."},
        {"t": round(e_step, 2), "text": f"15 January, 04:14 UTC: Hunga Tonga erupts. A pressure wave leaves at about {SPEED:.0f} metres per second."},
        {"t": round(e_step + hon["expected_h_after"], 2), "text": f"About {hon['expected_h_after']:.1f} hours later the front reaches Honolulu, {hon['distance_km']} km away. ERA5 shows a bump of {hon['era5_peak_hpa']:.2f} hectopascals."},
        {"t": round(e_step + sfo["expected_h_after"], 2), "text": f"San Francisco, {sfo['expected_h_after']:.1f} hours after the eruption: {sfo['era5_peak_hpa']:.2f} hectopascals in ERA5. Across the Pacific the model wave travels at {tr['speed_ms_theil_sen']:.0f} metres per second."},
        {"t": round(e_step + big["gauge_max_h_after"], 2), "text": f"The largest water swing: {big['station']}, {big['gauge_max_abs_m']:.2f} metres, {big['gauge_max_h_after']:.1f} hours after the eruption."},
        {"t": round(e_step + 30, 2), "text": f"The wave keeps circling the planet. Hour by hour the pressure to water link is {lk['strength']} (r {rb:.2f}), but the arrival times line up: r {r_arr:.2f} across the gauges, water moving a median {delay:.1f} hours after the air wave."},
    ]
    beats.sort(key=lambda b: b["t"])

    layers = [
        {"id": "ring", "type": "ring", "name": "Expected front", "color": "#ffd27a", "unit": "km",
         "what": "Reference Lamb wave front at 315 m/s from the USGS eruption origin (expected front, not data)",
         "series": SL.clean([max(0.0, (h - e_step) * SPEED * 3.6) if h >= e_step else None for h in range(N)], 0),
         "ring": {"lat": lat, "lon": lon, "t": round(e_step, 3), "speed_kmh": round(SPEED * 3.6, 1), "label": "expected front (315 m/s)"}},
        {"id": "pressure", "type": "pillars", "name": "Pressure jump", "color": "#ff8a65", "unit": "hPa",
         "what": "ERA5 hourly surface pressure at 15 gauges, high-passed anomaly (model, via Open-Meteo); lane = mean of the 15",
         "series": SL.clean(hero, 3), "stations": stations_p,
         "pillar_note": "anomaly can be negative; pillar height linear in the anomaly, 0 at ground"},
        {"id": "gauges", "type": "columns", "name": "Water", "color": "#4fb3ff", "unit": "m",
         "what": "NOAA CO-OPS 6 minute water level minus tide prediction, short period part, hourly max amplitude (observed); lane = mean of the 15",
         "series": SL.clean(gl, 3), "stations": stations_g},
    ]
    obj = {
        "title": "Hunga Tonga: the sky rang like a bell",
        "timebase": "hour", "t0": "2022-01-14T00:00Z", "step_s": 3600, "n": N,
        "region": {"lat0": -30, "lat1": 65, "lon0": 140, "lon1": 295},
        "hero": "pressure", "partner": "gauges",
        "link": lk,
        "hero_norm": SL.norm_stats(P[:, :int(e_step)].ravel(), "2022-01-14 00Z to 2022-01-15 04Z (pre-eruption)",
                                   "high-passed ERA5 anomaly at the 15 points before the eruption (no other baseline year makes sense for one eruption)"),
        "arrivals": table, "check_transect": tr,
        "stats": stats, "gaps": gaps, "beats": beats, "events": events,
        "sources": [
            {"name": "USGS earthquake catalog, event us7000gc8r (volcanic eruption)", "producer": "USGS", "resolution": "event origin",
             "kind": "observed", "period": "2022-01-15", "baseline": "none",
             "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000gc8r"},
            {"name": "ERA5 hourly surface pressure", "producer": "ECMWF Copernicus C3S, served by Open-Meteo", "resolution": "0.25 deg, hourly",
             "kind": "model", "period": "2022-01-11 to 2022-01-21 (fit), shown 14 to 18 Jan", "baseline": "pre-eruption hours",
             "url": "https://open-meteo.com/en/docs/historical-weather-api"},
            {"name": "CO-OPS water level and tide predictions", "producer": "NOAA CO-OPS", "resolution": "6 minute, 15 gauges",
             "kind": "observed", "period": "2022-01-14 to 2022-01-18", "baseline": "tide prediction removed; datum MSL",
             "url": "https://tidesandcurrents.noaa.gov/"},
            {"name": "Lamb wave speed (reference front)", "producer": "Matoza et al. 2022, Science 377, 95 to 100; Wright et al. 2022, Nature 609, 741 to 746",
             "resolution": "published speed about 310 to 320 m/s", "kind": "observed", "period": "2022-01-15", "baseline": "none",
             "url": "https://doi.org/10.1126/science.abo7063"},
        ],
        "layers": layers,
        "script": "e3_tonga.py",
    }
    SL.write_story(ID, obj)
    print("arrival table:")
    for t in table:
        print(f"  {t['station']:20s} {t['distance_km']:6d} km exp {t['expected_h_after']:5.2f} h  ERA5 {t['era5_peak_h_after']:5.2f} h {t['era5_peak_hpa']:+.2f} hPa (x{t['era5_peak_over_noise']} noise)  gauge first {t['gauge_first_h_after']} h max {t['gauge_max_abs_m']} m at {t['gauge_max_h_after']} h")


if __name__ == "__main__":
    main()
