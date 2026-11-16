"""C1 Tides: 31 days (2024-03-01 .. 2024-03-31 UTC) of hourly observed water level at ~22 NOAA CO-OPS stations
on the US East and West coasts. The cycle is the story: no cycle removal on the lanes.

Hero = Boston 8443970, partner = The Battery, New York 8518750 (same coast, clear phase lag).
Datum MLLW (mean lower low water, each station's own), metric (m). product=hourly_height (verified hourly heights).
Link: Pearson r on the raw hourly series, lags -12..12 h; also on the non-tidal residual (observed minus the
CO-OPS harmonic prediction). Phase lag along the coast: least-squares M2 fit (12.4206 h) per station.

Run: /Users/mykhayloolefirenko/.venvs/omi/bin/python data-pipeline/c1_tides.py
"""
import datetime as dt
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402

ID = "c1_tides"
T0 = dt.datetime(2024, 3, 1, tzinfo=dt.timezone.utc)
N = 31 * 24
API = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
HERO, PARTNER = "8443970", "8518750"
M2_H = 12.4206012

STATIONS = [  # (id, coast) ; names/coords come from the API metadata
    ("8410140", "east"), ("8413320", "east"), ("8418150", "east"), ("8443970", "east"), ("8447930", "east"),
    ("8452660", "east"), ("8518750", "east"), ("8534720", "east"), ("8557380", "east"), ("8638610", "east"),
    ("8651370", "east"), ("8658120", "east"), ("8665530", "east"), ("8670870", "east"), ("8720218", "east"),
    ("8724580", "east"),
    ("9410170", "west"), ("9410660", "west"), ("9414290", "west"), ("9419750", "west"), ("9439040", "west"),
    ("9443090", "west"), ("9447130", "west"), ("9455920", "west"),
]


def get(station, product, extra=""):
    url = (f"{API}?product={product}&station={station}&begin_date=20240301&end_date=20240331%2023:59"
           f"&datum=MLLW&units=metric&time_zone=gmt&format=json&application=earthjukebox{extra}")
    d = SL.fetch_json(url, ID, name=f"{product}_{station}.json")
    if "error" in d:
        raise RuntimeError(f"{station} {product}: {d['error']}")
    rows = d.get("data") or d.get("predictions")
    s = [None] * N
    for r in rows:
        t = dt.datetime.strptime(r["t"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
        k = (t - T0).total_seconds() / 3600
        if k == int(k) and 0 <= k < N and r["v"] not in ("", None):
            s[int(k)] = float(r["v"])
    return d.get("metadata"), s


def arr(s):
    return np.array([np.nan if v is None else v for v in s], float)


def m2_fit(s):
    """Least squares fit mean + M2 + S2 + K1 + O1; returns M2 amplitude (m) and phase (hours of M2 cycle lag)."""
    y = arr(s)
    t = np.arange(N, dtype=float)
    ok = np.isfinite(y)
    cols = [np.ones(N)]
    for P in (M2_H, 12.0, 23.9344696, 25.8193417):
        w = 2 * np.pi / P
        cols += [np.cos(w * t), np.sin(w * t)]
    A = np.array(cols).T
    c, *_ = np.linalg.lstsq(A[ok], y[ok], rcond=None)
    amp = float(np.hypot(c[1], c[2]))
    ph = float(np.arctan2(c[2], c[1]))  # cos(wt - ph): peak at t = ph / w
    return amp, ph


def main():
    stations, fallback = [], []
    for sid, coast in STATIONS:
        try:
            meta, s = get(sid, "hourly_height")
        except Exception as e:  # noqa: BLE001
            try:  # verified hourly heights missing: 6 minute water level sampled on the hour (interval=h)
                meta, s = get(sid, "water_level", "&interval=h")
                fallback.append(meta["name"])
            except Exception as e2:  # noqa: BLE001
                print("skip", sid, e, e2)
                continue
        if SL.gap_count(s) > N * 0.5:
            print("skip", sid, "too many gaps", SL.gap_count(s))
            continue
        stations.append({"id": sid, "name": meta["name"], "lat": float(meta["lat"]), "lon": float(meta["lon"]),
                         "coast": coast, "series": SL.clean(s, 3)})
        print(sid, meta["name"], "gaps", SL.gap_count(s))

    by = {s["id"]: s for s in stations}
    hero, partner = by[HERO], by[PARTNER]
    _, hp = get(HERO, "predictions", "&interval=h")
    _, pp = get(PARTNER, "predictions", "&interval=h")
    h_res = arr(hero["series"]) - arr(hp)
    p_res = arr(partner["series"]) - arr(pp)

    lk = SL.link(hero["series"], partner["series"], 12, "hour",
                 "Pearson r, hourly observed water level (raw, tide cycle kept), partner lagged -12..12 h")
    # The semidiurnal cycle repeats every 12.42 h, so the raw curve has two peaks; report the one nearest 0.
    near = [c for c in lk["curve"] if abs(c[0]) <= 6]
    kbest, rbest = max(near, key=lambda c: c[1])
    lk_res = SL.link(SL.clean(h_res, 3), SL.clean(p_res, 3), 12, "hour",
                     "Pearson r, residual (observed minus CO-OPS harmonic prediction), partner lagged -12..12 h")

    # M2 phase along the coast, relative to the hero
    amp_h, ph_h = m2_fit(hero["series"])
    w = 2 * np.pi / M2_H
    phase_rows = []
    for s in stations:
        a, ph = m2_fit(s["series"])
        lag_h = ((ph - ph_h) / w + M2_H / 2) % M2_H - M2_H / 2  # wrap to -6.2..6.2 h
        s["m2_amp_m"] = round(a, 3)
        s["m2_lag_vs_hero_h"] = round(lag_h, 2)
        y = arr(s["series"])
        s["range_m"] = round(float(np.nanmax(y) - np.nanmin(y)), 3)
        phase_rows.append((s["name"], s["coast"], round(lag_h, 2), round(a, 3), s["range_m"]))

    # spring vs neap at the hero: daily (UTC day) max - min
    y = arr(hero["series"])
    daily = []
    for d in range(31):
        seg = y[d * 24:(d + 1) * 24]
        daily.append(float(np.nanmax(seg) - np.nanmin(seg)) if np.isfinite(seg).sum() >= 20 else np.nan)
    daily = np.array(daily)
    ds, dn = int(np.nanargmax(daily)), int(np.nanargmin(daily))

    # moon phases (USNO)
    mp = SL.fetch_json("https://aa.usno.navy.mil/api/moon/phases/date?date=2024-02-28&nump=6", ID, name="usno_moon.json")
    events = []
    for p in mp["phasedata"]:
        t = dt.datetime(p["year"], p["month"], p["day"], *map(int, p["time"].split(":")), tzinfo=dt.timezone.utc)
        k = (t - T0).total_seconds() / 3600
        if 0 <= k < N:
            events.append({"t": round(k, 2), "label": p["phase"]})
    events.append({"t": ds * 24 + 12, "label": f"largest daily range at Boston ({daily[ds]:.2f} m)"})
    events.append({"t": dn * 24 + 12, "label": f"smallest daily range at Boston ({daily[dn]:.2f} m)"})
    bands = [{"t0": ds * 24, "t1": ds * 24 + 24, "label": "spring tide day"},
             {"t0": dn * 24, "t1": dn * 24 + 24, "label": "neap tide day"}]

    ranges = {s["name"]: s["range_m"] for s in stations}
    big = max(stations, key=lambda s: s["range_m"])
    small = min(stations, key=lambda s: s["range_m"])
    hmin, hmax = float(np.nanmin(y)), float(np.nanmax(y))
    dstr = lambda d: (T0 + dt.timedelta(days=d)).strftime("%d %b")  # noqa: E731
    pres = arr(partner["series"])

    stats = {
        "Boston tidal range over the month (m)": hero["range_m"],
        "Boston spring day range (m)": round(daily[ds], 3),
        "Boston spring day": dstr(ds),
        "Boston neap day range (m)": round(daily[dn], 3),
        "Boston neap day": dstr(dn),
        "spring vs neap range at Boston (%)": SL.pct(daily[ds], daily[dn]),
        "New York (The Battery) tidal range (m)": partner["range_m"],
        "New York high water before Boston (h, M2 fit)": -next(s["m2_lag_vs_hero_h"] for s in stations if s["id"] == PARTNER),
        "West coast high water travel San Diego to Astoria (h, M2 fit)": round(by["9439040"]["m2_lag_vs_hero_h"] - by["9410170"]["m2_lag_vs_hero_h"], 2),
        "best raw lag Boston to New York (h, hourly steps)": kbest,
        "raw r at that lag": rbest,
        "residual link r": lk_res["r"],
        "residual link lag (h)": lk_res["lag"],
        "largest range station": f"{big['name']} {big['range_m']} m",
        "smallest range station": f"{small['name']} {small['range_m']} m",
        "stations": len(stations),
    }

    gaps = [f"{s['name']}: {SL.gap_count(s['series'])} missing hours (left empty)" for s in stations if SL.gap_count(s["series"])]
    gaps += [f"{n}: verified hourly heights not offered, used the 6 minute water level sampled on the hour" for n in fallback]
    gaps += [
        "Water level relative to each station's own MLLW datum (mean lower low water), so column heights compare tidal swing, not absolute sea level between stations.",
        "Hourly heights: the true high and low water can fall between hours, so ranges here are slightly smaller than the 6 minute record.",
        "No cycle removal on the lanes: the tide is the story. The residual link uses observed minus the CO-OPS harmonic prediction.",
        "Raw lag is limited to whole hours; the sub-hour coast phase uses a least squares M2 (12.42 h) fit per station.",
        "The tide repeats every 12.42 h, so a raw lag of k hours also matches k plus or minus 12.42 h; the reported lag is the one nearest zero.",
    ]
    for sid, coast in STATIONS:
        if sid not in by:
            gaps.append(f"station {sid} dropped (no data from the API)")

    beats = [
        {"t": 0, "text": f"March 2024, {len(stations)} tide gauges on the US East and West coasts. Boston swings about {daily[0]:.1f} metres twice a day."},
        {"t": events[0]["t"] if events else 0, "text": f"{events[0]['label']}. The tidal swing grows toward the new moon."},
        {"t": ds * 24 + 12, "text": f"Spring tide: Boston ranges {daily[ds]:.2f} metres in one day, on {dstr(ds)}."},
        {"t": dn * 24 + 12, "text": f"Neap tide on {dstr(dn)}: Boston ranges only {daily[dn]:.2f} metres. "
                                    f"The spring tide day was {SL.pct(daily[ds], daily[dn])} percent larger."},
        {"t": 24 * 5, "text": f"The tide moves along the coast: high water reaches New York about {-next(s['m2_lag_vs_hero_h'] for s in stations if s['id'] == PARTNER):.1f} hours before Boston. On the West Coast it travels north, San Diego to Astoria in about {by['9439040']['m2_lag_vs_hero_h'] - by['9410170']['m2_lag_vs_hero_h']:.1f} hours."},
        {"t": 24 * 12, "text": f"Biggest swing of the month: {big['name']}, {big['range_m']} metres. Smallest: {small['name']}, {small['range_m']} metres."},
        {"t": 24 * 24, "text": f"Full moon brings the second spring tide. Boston to New York raw link r {rbest:.2f}."},
    ]
    beats.sort(key=lambda b: b["t"])

    layer = {
        "id": "tides", "type": "columns", "name": "Tides",
        "what": f"NOAA CO-OPS observed hourly water level at {len(stations)} gauges, metres above station MLLW (observed)",
        "color": "#4fb3ff", "unit": "m above MLLW",
        "series": hero["series"], "series_station": hero["name"],
        "partner_series": partner["series"], "partner_station": partner["name"],
        "stations": stations,
    }
    obj = {
        "title": "Tides: the coast breathes twice a day",
        "timebase": "hour", "t0": "2024-03-01T00:00Z", "step_s": 3600, "n": N,
        "region": {"lat0": 24, "lat1": 62, "lon0": -152, "lon1": -66},
        "hero": "tides", "partner": "tides",
        "hero_station": {"id": HERO, "name": hero["name"]}, "partner_station": {"id": PARTNER, "name": partner["name"]},
        "lanes": {"hero": {"layer": "tides", "station": HERO, "name": hero["name"], "series": hero["series"]},
                  "partner": {"layer": "tides", "station": PARTNER, "name": partner["name"], "series": partner["series"]}},
        "link": {**lk, "lag_nearest_zero": kbest, "r_nearest_zero": rbest,
                 "m2_phase_lag_h": next(s["m2_lag_vs_hero_h"] for s in stations if s["id"] == PARTNER),
                 "residual": {k: lk_res.get(k) for k in ("r", "lag", "n", "r_lag0", "strength", "method", "curve")}},
        "hero_norm": {"min": round(hmin, 3), "max": round(hmax, 3),
                      "method": "Boston observed hourly water level min and max over the story month (cycle story: intensity = position in this range)"},
        "phase_table": [{"name": r[0], "coast": r[1], "m2_lag_vs_hero_h": r[2], "m2_amp_m": r[3], "range_m": r[4]} for r in phase_rows],
        "phase_note": "m2_lag_vs_hero_h: hours after Boston that M2 high water arrives (negative = earlier), least squares fit over the month",
        "stats": stats, "gaps": gaps, "beats": beats, "events": events, "bands": bands,
        "sources": [
            {"name": "CO-OPS hourly heights (water level)", "producer": "NOAA Center for Operational Oceanographic Products and Services",
             "resolution": f"hourly, {len(stations)} tide gauges", "kind": "observed", "period": "2024-03-01 to 2024-03-31 UTC",
             "baseline": "none (cycle story); datum MLLW per station", "url": "https://api.tidesandcurrents.noaa.gov/api/prod/"},
            {"name": "CO-OPS tide predictions (harmonic)", "producer": "NOAA CO-OPS",
             "resolution": "hourly, Boston and The Battery", "kind": "model", "period": "2024-03-01 to 2024-03-31 UTC",
             "baseline": "used only to compute the non-tidal residual", "url": "https://tidesandcurrents.noaa.gov/web_services_info.html"},
            {"name": "Moon phases", "producer": "US Naval Observatory", "resolution": "minute", "kind": "observed",
             "period": "March 2024", "baseline": "none", "url": "https://aa.usno.navy.mil/data/MoonPhases"},
        ],
        "layers": [layer],
        "script": "c1_tides.py",
    }
    SL.write_story(ID, obj)
    print("phase table (name, coast, M2 lag vs Boston h, M2 amp m, range m):")
    for r in sorted(phase_rows, key=lambda r: (r[1], r[2])):
        print("  ", r)
    print("residual link:", {k: lk_res.get(k) for k in ("r", "lag", "n", "r_lag0", "strength")})


if __name__ == "__main__":
    main()
