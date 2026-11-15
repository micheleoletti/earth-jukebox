"""C4 Africa fire belt, 2019 (monthly cycle, 12 steps).

Layers: fires (FIRMS VIIRS SNPP 2019 country CSVs for 32 sub-Saharan countries, points carry fractional month t),
rain (field: NASA GPM IMERG Final monthly precipitation V07, observed, 0.5 deg over Africa).
hero = fires (monthly detection count), partner = rain (mean over the fire belt).
Links: whole belt, north of the equator, south of the equator; rain leading by 0..3 months.

Run: /Users/mykhayloolefirenko/.venvs/omi/bin/python data-pipeline/c4_africa_fire.py
"""
import calendar
import pathlib
import sys
import warnings

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402
import fire_helpers as FH  # noqa: E402

warnings.simplefilter("ignore")
ID = "c4_africa_fire"
YEAR = 2019
N = 12
COUNTRIES = ("Nigeria Chad Sudan South_Sudan Central_African_Republic Cameroon Democratic_Republic_of_the_Congo "
             "Republic_of_Congo Angola Zambia Mozambique Tanzania Ethiopia Mali Burkina_Faso Ghana Guinea Cote_d_Ivoire "
             "Benin Gabon Uganda Malawi Zimbabwe Madagascar Botswana Namibia South_Africa Senegal Togo Sierra_Leone "
             "Guinea-Bissau Kenya").split()
LAT0, LAT1, LON0, LON1 = -35.0, 25.0, -20.0, 52.0  # rain grid box (0.5 deg cells)
RES = 0.5
BELT_MIN = 20  # a 0.5 deg cell belongs to the fire belt if it had at least this many 2019 detections
IMERG = "https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/{y}/3B-MO.MS.MRG.3IMERG.{y}{m:02d}01-S000000-E235959.{m:02d}.V07B.HDF5"
MONTHS = [calendar.month_name[m] for m in range(1, 13)]


def imerg_month(m):
    """IMERG monthly mean rate (mm/h) -> mm per month on the 0.5 deg box grid (mean of 5 x 5 0.1 deg cells)."""
    import netCDF4
    p = SL.fetch(IMERG.format(y=YEAR, m=m), ID, name=f"imerg_{YEAR}{m:02d}.HDF5", token=True, min_bytes=1000000)
    ds = netCDF4.Dataset(p)
    g = ds["Grid"]
    lat, lon = g["lat"][:], g["lon"][:]
    ia = np.where((lat > LAT0) & (lat < LAT1))[0]
    io = np.where((lon > LON0) & (lon < LON1))[0]
    x = np.ma.filled(g["precipitation"][0, io[0]:io[-1] + 1, ia[0]:ia[-1] + 1].astype(float), np.nan).T  # (lat, lon)
    ds.close()
    x[x < 0] = np.nan
    hours = calendar.monthrange(YEAR, m)[1] * 24
    f = int(round(RES / 0.1))
    xb = FH.block_mean(x[None] * hours, f)[0]
    return xb, FH.block_centres(lat[ia], f), FH.block_centres(lon[io], f)


def main():
    gaps = []
    # ------------------------------------------------------------ fires
    lat, lon, frp, tm = [], [], [], []
    per_country = {}
    for c in COUNTRIES:
        f = FH.firms(ID, YEAR, c)
        k = (f["type"] == 0) & (f["conf"] != "l")
        lat.append(f["lat"][k]); lon.append(f["lon"][k]); frp.append(f["frp"][k]); tm.append(f["time"][k])
        per_country[c] = int(k.sum())
    lat, lon, frp, tm = (np.concatenate(x) for x in (lat, lon, frp, tm))
    yr = tm.astype("datetime64[Y]").astype(int) + 1970
    keep = yr == YEAR
    lat, lon, frp, tm = lat[keep], lon[keep], frp[keep], tm[keep]
    mon = tm.astype("datetime64[M]").astype(int) - (YEAR - 1970) * 12  # 0..11
    mstart = tm.astype("datetime64[M]").astype("datetime64[m]")
    dim = np.array([calendar.monthrange(YEAR, m + 1)[1] for m in range(12)])
    tfrac = mon + (tm - mstart).astype(float) / (dim[mon] * 1440.0)
    cnt = np.array([int((mon == m).sum()) for m in range(N)])
    north, south = lat >= 0, lat < 0
    cnt_n = np.array([int(((mon == m) & north).sum()) for m in range(N)])
    cnt_s = np.array([int(((mon == m) & south).sum()) for m in range(N)])
    frp_m = [float(frp[mon == m].sum()) for m in range(N)]
    sub = FH.even_subsample(tfrac, 30000)
    sub = sub[np.argsort(tfrac[sub])]
    vmax_frp = float(np.percentile(frp, 99))
    total = len(lat)
    gaps.append(f"Fire points: {total:,} VIIRS detections in {len(COUNTRIES)} countries in 2019; {len(sub):,} drawn "
                f"(1 in {total / len(sub):.0f}, subsampled evenly in time, so every month keeps its share). Monthly counts use all detections.")
    gaps.append(f"Countries: {', '.join(c.replace('_', ' ').replace('Cote d Ivoire', "Cote d'Ivoire") for c in COUNTRIES)}. Fires in other African countries (for example Liberia, Niger, Equatorial Guinea, Rwanda, Burundi, Eswatini, Lesotho, Somalia) are not included.")
    gaps.append(f"Fire point size is linear in FRP up to {vmax_frp:.0f} MW (99th percentile). Only nominal and high confidence vegetation fire detections; "
                "VIIRS passes about twice a day, so short fires and fires under cloud are missed.")
    fires = {"id": "fires", "type": "points", "name": "Fires (Africa)",
             "what": "VIIRS SNPP active fire detections, NASA FIRMS (observed); lane = detections per month",
             "color": "#ff7a1a", "unit": "detections per month", "series": [int(x) for x in cnt],
             "series_north": [int(x) for x in cnt_n], "series_south": [int(x) for x in cnt_s],
             "points": {"lat": SL.clean(lat[sub], 2), "lon": SL.clean(lon[sub], 2), "t": SL.clean(tfrac[sub], 3),
                        "v": SL.clean(frp[sub], 1)},
             "vmax": round(vmax_frp, 1)}

    # ------------------------------------------------------------ rain (IMERG, observed)
    rain, rlat, rlon = [], None, None
    for m in range(1, 13):
        x, rlat, rlon = imerg_month(m)
        rain.append(x)
    rain = np.array(rain)
    # fire belt mask: 0.5 deg cells with >= BELT_MIN detections in 2019
    iy = np.floor((lat - (rlat[0] - RES / 2)) / RES).astype(int)
    ix = np.floor((lon - (rlon[0] - RES / 2)) / RES).astype(int)
    ok = (iy >= 0) & (iy < len(rlat)) & (ix >= 0) & (ix < len(rlon))
    dens = np.zeros((len(rlat), len(rlon)), int)
    np.add.at(dens, (iy[ok], ix[ok]), 1)
    belt = dens >= BELT_MIN
    bn, bs = belt & (rlat[:, None] >= 0), belt & (rlat[:, None] < 0)
    w = np.cos(np.radians(rlat))[:, None] * np.ones_like(dens)

    def area_mean(mask):
        return np.array([float(np.nansum(rain[m] * w * mask) / np.sum(w * mask * np.isfinite(rain[m]))) for m in range(N)])

    r_all, r_n, r_s = area_mean(belt), area_mean(bn), area_mean(bs)
    gaps.append(f"Fire belt for the rain lane = the {int(belt.sum()):,} cells of 0.5 deg with at least {BELT_MIN} fire detections in 2019 "
                f"({int(bn.sum()):,} north, {int(bs.sum()):,} south of the equator); rain lane = area-weighted mean over them, mm per month.")
    rvmax = 400.0
    gaps.append(f"Rain field drawn linear from 0 to {rvmax:.0f} mm per month with a floor of 25 mm (drier cells drawn bare); wetter cells drawn at full colour.")
    rain_layer = {"id": "rain", "type": "field", "palette": "rain", "name": "Rain (IMERG)",
                  "what": "GPM IMERG Final monthly precipitation V07, NASA (observed, satellites calibrated with rain gauges)",
                  "color": "#4aa3ff", "unit": "mm per month", "series": SL.clean(r_all, 1),
                  "series_north": SL.clean(r_n, 1), "series_south": SL.clean(r_s, 1), "series_label": "mean over the fire belt",
                  "grid": SL.enc_grid(rain, 0.0, rvmax, float(rlat[0]), float(rlat[-1]), float(rlon[0]), float(rlon[-1]),
                                      [m + 0.5 for m in range(N)], "mm/month", kind="observed", floor=25.0)}

    # ------------------------------------------------------------ links (12 months: indicative only)
    meth = "Pearson r of monthly values, rain leading fires by 0 to 3 months (12 months, indicative only)"
    lk = FH.link_dir(cnt.astype(float), r_all, 3, "months", "fire detections per month vs fire-belt rain; " + meth,
                     partner_leads=True, min_n=8, sign=None)
    lk["lag_steps"] = lk.get("lag")
    lk_n = FH.link_dir(cnt_n.astype(float), r_n, 3, "months", "north", partner_leads=True, min_n=8, sign=None)
    lk_s = FH.link_dir(cnt_s.astype(float), r_s, 3, "months", "south", partner_leads=True, min_n=8, sign=None)

    def curve_txt(l):
        return "; ".join(f"rain {-k} mo before: r {r:+.2f}" for k, r in l["curve"] if k <= 0)

    pn, ps = int(np.argmax(cnt_n)), int(np.argmax(cnt_s))
    pk = int(np.argmax(cnt))
    switch = [m for m in range(N) if (cnt_s[m] > cnt_n[m]) != (cnt_s[m - 1] > cnt_n[m - 1])] if N > 1 else []
    stats = {
        "fire detections 2019 (32 countries)": total,
        "peak month (all)": MONTHS[pk], "peak month detections": int(cnt[pk]),
        "lowest month": MONTHS[int(np.argmin(cnt))], "lowest month detections": int(cnt.min()),
        "north of equator detections": int(cnt_n.sum()), "south of equator detections": int(cnt_s.sum()),
        "north peak month": MONTHS[pn], "north peak detections": int(cnt_n[pn]),
        "south peak month": MONTHS[ps], "south peak detections": int(cnt_s[ps]),
        "months when the south burns more than the north": ", ".join(MONTHS[m] for m in range(N) if cnt_s[m] > cnt_n[m]),
        "north detections by month, Jan to Dec": ", ".join(f"{int(x):,}" for x in cnt_n),
        "south detections by month, Jan to Dec": ", ".join(f"{int(x):,}" for x in cnt_s),
        "fire-belt rain by month, north, Jan to Dec (mm)": ", ".join(f"{x:.0f}" for x in r_n),
        "fire-belt rain by month, south, Jan to Dec (mm)": ", ".join(f"{x:.0f}" for x in r_s),
        "link r, all fires vs belt rain": lk.get("r"), "link lag, rain before fires (months)": None if lk.get("lag") is None else -lk["lag"],
        "link n (months)": lk.get("n"),
        "link r, north fires vs north rain": lk_n.get("r"), "link lag north (months)": None if lk_n.get("lag") is None else -lk_n["lag"],
        "link n north": lk_n.get("n"),
        "link r, south fires vs south rain": lk_s.get("r"), "link lag south (months)": None if lk_s.get("lag") is None else -lk_s["lag"],
        "link n south": lk_s.get("n"),
        "all lags, all fires": curve_txt(lk), "all lags, north": curve_txt(lk_n), "all lags, south": curve_txt(lk_s),
        "detections per country (top 8)": ", ".join(f"{c.replace('_', ' ')} {v:,}" for c, v in sorted(per_country.items(), key=lambda x: -x[1])[:8]),
    }
    gaps.append("Links use only 12 monthly values (8 to 12 pairs depending on the lag), so every r here is indicative, not a statistical test. "
                "Fires and rain both follow the seasons, so a strong r mostly says they share the same yearly rhythm.")
    gaps.append("Months are calendar months; a point's t is its day of the month scaled into that month.")
    lag_n = stats["link lag north (months)"]
    lag_s = stats["link lag south (months)"]
    beats = [{"t": 0, "text": f"January 2019. The dry season north of the equator: {cnt_n[0]:,} fire detections in the northern savannas, {cnt_s[0]:,} in the south."}]
    if pn == 0:
        beats[0]["text"] += f" This is the northern peak of the year, with only {r_n[0]:.0f} mm of rain over the northern fire belt."
    else:
        beats.append({"t": pn, "text": f"{MONTHS[pn]}: the northern belt peaks with {cnt_n[pn]:,} detections while its rain is {r_n[pn]:.0f} mm a month."})
    if switch:
        m = next((m for m in switch if cnt_s[m] > cnt_n[m]), switch[0])
        beats.append({"t": m, "text": f"{MONTHS[m]}: the rains move north and the fires move south. The south now burns more than the north."})
    beats.append({"t": ps, "text": f"{MONTHS[ps]}: the southern belt peaks, {cnt_s[ps]:,} detections, the most of the year, with {r_s[ps]:.0f} mm of rain."})
    back = next((m for m in switch if cnt_n[m] > cnt_s[m] and m > ps), None)
    if back is not None:
        beats.append({"t": back, "text": f"{MONTHS[back]}: rain returns to the south and the fires swing back north."})
    def lag_txt(k):
        return "same month" if k == 0 else f"rain {k} month{'s' if k != 1 else ''} earlier"
    beats.append({"t": N - 1, "text": f"Over 2019, {total:,} detections. More rain, fewer fires: r = {lk_n['r']} in the north ({lag_txt(lag_n)}), "
                                      f"r = {lk_s['r']} in the south ({lag_txt(lag_s)}), from 12 months only, so indicative."})
    beats.sort(key=lambda b: b["t"])
    events = [{"t": pn, "label": "northern fire peak"}, {"t": ps, "label": "southern fire peak"}]
    bands, b0 = [], None
    for m in range(N + 1):
        on = m < N and cnt_s[m] > cnt_n[m]
        if on and b0 is None:
            b0 = m
        if not on and b0 is not None:
            bands.append({"t0": b0, "t1": m, "label": "south burns more than north"})
            b0 = None
    hero_norm = {"min": int(cnt.min()), "max": int(cnt.max()), "method": "cycle: min and max of the 2019 monthly detection count itself"}
    sources = [
        {"name": "VIIRS S-NPP 375 m active fires (VNP14IMG), country yearly CSVs", "producer": "NASA FIRMS (LANCE / EOSDIS)",
         "resolution": "375 m, about 2 overpasses per day", "kind": "observed", "period": "2019", "baseline": "none (cycle)",
         "url": "https://firms.modaps.eosdis.nasa.gov/country/"},
        {"name": "GPM IMERG Final Precipitation L3 1 month 0.1 deg V07 (GPM_3IMERGM)", "producer": "NASA GSFC / GES DISC",
         "resolution": "0.1 deg monthly, used at 0.5 deg", "kind": "observed", "period": "2019", "baseline": "none (cycle)",
         "url": "https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07"},
    ]
    obj = {"title": "Africa fire belt", "timebase": "month", "t0": f"{YEAR}-01-01T00:00Z", "step_s": 0, "n": N,
           "region": {"lat0": -35.0, "lat1": 20.0, "lon0": -20.0, "lon1": 52.0}, "hero": "fires", "partner": "rain",
           "link": lk, "link_north": lk_n, "link_south": lk_s, "hero_norm": hero_norm, "stats": stats, "gaps": gaps,
           "beats": beats, "events": events, "bands": bands, "sources": sources, "layers": [fires, rain_layer],
           "script": "c4_africa_fire.py"}
    SL.write_story(ID, obj)


if __name__ == "__main__":
    main()
