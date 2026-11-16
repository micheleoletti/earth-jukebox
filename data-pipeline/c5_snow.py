"""C5 Snow vs temperature, Northern Hemisphere, Aug 2019 .. Jul 2020 (12 calendar months).

Layers
  snow  MODIS/Terra MOD10CM v061 monthly snow cover CMG (0.05 deg, NSIDC, observed) -> 1 deg mean snow percent over
        land cells with a valid observation (night, cloud, no-decision and water cells excluded), 0-90N.
        Lane: NH snow-covered area (million km2) = sum(snow fraction x cell area) over observed land cells.
  temp  MERRA-2 M2TMNXSLV monthly 2 m air temperature (GMAO, model), 1 x 1.25 deg (2x2 blocks of the 0.5 x 0.625 grid), 0-90N.
        Lane: NH land mean (area weighted, MERRA-2 land + land ice fraction >= 0.5).
Link: monthly, snow extent vs land temperature, lags -3..3 months (n is only 9 to 12).

Usage: python c5_snow.py
"""
import datetime as dt
import json
import pathlib
import subprocess
import sys
import urllib.parse

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import storylib as SL  # noqa: E402

ID = "c5_snow"
MONTHS = [(2019, m) for m in range(8, 13)] + [(2020, m) for m in range(1, 8)]
NT = len(MONTHS)
R_EARTH = 6371.0088
MNAME = [dt.date(y, m, 1).strftime("%b %Y") for y, m in MONTHS]


def cmr(short, ver, y, m):
    a = dt.date(y, m, 1)
    b = (a.replace(day=28) + dt.timedelta(4)).replace(day=1) - dt.timedelta(1)
    q = (f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name={short}&version={ver}"
         f"&temporal={a.isoformat()},{b.isoformat()}T23:59:59Z&page_size=20")
    raw = subprocess.run(["curl", "-sf", "--retry", "5", q], capture_output=True, check=True).stdout
    return json.loads(raw)["feed"]["entry"]


# ---------------------------------------------------------------- snow (MOD10CM)
def snow_month(y, m):
    """-> 1 deg (90 x 360) mean snow percent over observed land, plus observed-land and unobserved-land area per 1 deg cell (km2)."""
    from pyhdf.SD import SD
    e = [g for g in cmr("MOD10CM", "61", y, m) if g["title"].startswith(f"MOD10CM.A{y}")][0]
    url = next(l["href"] for l in e["links"] if l["href"].startswith("https://data.nsidc") and l["href"].endswith(".hdf"))
    p = SL.fetch(url, ID, token=True, min_bytes=100000)
    a = SD(str(p)).select("Snow_Cover_Monthly_CMG").get()[:1800]      # rows 0..1799 = 90N .. 0N (row 0 centre 89.975N)
    a = a[::-1]                                                           # south -> north
    land_valid = a <= 100
    unobs = (a == 211) | (a == 250) | (a == 253)                          # night, cloud, no decision (land without a value)
    lat_c = 0.025 + 0.05 * np.arange(1800)
    cell = (R_EARTH * np.radians(0.05)) ** 2 * np.cos(np.radians(lat_c))[:, None] * np.ones((1, 7200))
    frac = np.where(land_valid, a, 0).astype(float) / 100
    blk = lambda x: x.reshape(90, 20, 360, 20).sum(axis=(1, 3))
    snow_area, obs_area, un_area = blk(frac * cell), blk(land_valid * cell), blk(unobs * cell)
    with np.errstate(all="ignore"):
        pct = np.where(obs_area > 0, 100 * snow_area / obs_area, np.nan)
    return pct, snow_area.sum() / 1e6, obs_area.sum() / 1e6, un_area.sum() / 1e6, url


# ---------------------------------------------------------------- temperature (MERRA-2)
def opendap(coll, gran, ce, name):
    u = f"https://opendap.earthdata.nasa.gov/collections/{coll}/granules/{urllib.parse.quote(gran, safe='')}.dap.nc4?dap4.ce=" + \
        urllib.parse.quote(ce, safe="")
    return SL.fetch(u, ID, name=name, token=True, min_bytes=10000)


def land_mask():
    import netCDF4
    p = opendap("C1276812819-GES_DISC", "M2C0NXASM.5.12.4:MERRA2_101.const_2d_asm_Nx.00000000.nc4",
                "/FRLAND[0:0][180:1:359][0:1:575];/FRLANDICE[0:0][180:1:359][0:1:575]", "merra2_const_nh.nc4")
    d = netCDF4.Dataset(p)
    fl = np.asarray(d["FRLAND"][0] + d["FRLANDICE"][0], float)
    d.close()
    return fl          # (180, 576): lat 0.0 .. 89.5, lon -180 .. 179.375


def t2m_month(y, m):
    import netCDF4
    stream = "400"
    g = f"M2TMNXSLV.5.12.4:MERRA2_{stream}.tavgM_2d_slv_Nx.{y}{m:02d}.nc4"
    p = opendap("C1276812859-GES_DISC", g, "/T2M[0:0][180:1:359][0:1:575]", f"merra2_t2m_{y}{m:02d}.nc4")
    d = netCDF4.Dataset(p)
    t = np.asarray(d["T2M"][0], float) - 273.15
    d.close()
    return t


def main():
    # ---- snow
    snow_grid, extent, obs, unobs, snow_urls = [], [], [], [], []
    for y, m in MONTHS:
        pct, ext, ob, un, url = snow_month(y, m)
        snow_grid.append(pct)
        extent.append(round(ext, 2))
        obs.append(round(ob, 2))
        unobs.append(round(un, 2))
        snow_urls.append(url)
        print(f"  {y}-{m:02d} snow {ext:6.2f} M km2   observed land {ob:6.2f}   unobserved land (night/cloud) {un:5.2f}", flush=True)
    snow_grid = np.array(snow_grid)
    # ---- temperature
    fl = land_mask()
    lat = 0.0 + 0.5 * np.arange(180)
    w = np.cos(np.radians(lat))[:, None] * np.ones((1, 576))
    land = fl >= 0.5
    temp_grid, tland = [], []
    for y, m in MONTHS:
        t = t2m_month(y, m)
        tland.append(round(float((t * w)[land].sum() / w[land].sum()), 2))
        temp_grid.append(t.reshape(90, 2, 288, 2).mean(axis=(1, 3)))   # 1 x 1.25 deg, centres 0.25N.. / -179.6875E..
        print(f"  {y}-{m:02d} NH land T2M {tland[-1]:6.2f} C", flush=True)
    temp_grid = np.array(temp_grid)

    # ---- link (temperature leads snow is a negative lag: partner = temp before hero = snow)
    lk = SL.link(np.array(extent, float), np.array(tland, float), 3, "month",
                 "Pearson r, monthly NH snow-covered area (MODIS, observed land) vs NH land 2 m temperature (MERRA-2), lags -3..3 months",
                 min_n=8, sign_hint=-1)
    r_anom = None
    # without the shared seasonal shape we cannot say more from one year: say so in gaps
    imax, imin = int(np.argmax(extent)), int(np.argmin(extent))
    tmin = int(np.argmin(tland))
    stats = {
        "max NH snow extent (million km2)": extent[imax], "max snow month": MNAME[imax],
        "min NH snow extent (million km2)": extent[imin], "min snow month": MNAME[imin],
        "NH land temperature at snow max (C)": tland[imax], "NH land temperature at snow min (C)": tland[imin],
        "coldest month (NH land, C)": tland[tmin], "coldest month": MNAME[tmin],
        "months from coldest to max snow": imax - tmin,
        "link r": lk["r"], "link lag (months, negative = temperature leads)": lk["lag"], "link r at lag 0": lk["r_lag0"],
        "unobserved land at snow max, night or cloud (million km2)": unobs[imax],
        "largest unobserved land area (million km2)": max(unobs), "largest unobserved land month": MNAME[int(np.argmax(unobs))],
    }
    gaps = [
        "MODIS needs daylight and clear sky: land in polar night or under cloud all month has no snow value (empty on the map) and is left out of the snow area, so winter snow area is a lower bound; the unobserved land area is given per month in obs_unobserved_mkm2.",
        "Greenland and other ice sheets are mapped as snow all year (about 2 million km2 of the summer minimum).",
        "Snow area = sum over observed land of (snow percent x cell area) at 0.05 deg, 0 to 90N; the map shows the mean snow percent per 1 degree cell.",
        "Temperature is MERRA-2 reanalysis (a model), monthly mean 2 m air temperature; the land mean uses cells with at least 50% land or land ice.",
        "One year only: both lanes follow the seasonal cycle, so the correlation (n 9 to 12 months) mostly says that snow follows the cold season; it is not a trend.",
        "Lag: r is almost the same with no lag and with temperature leading by one month, so the one-month lead is only a hint at monthly resolution.",
        "MODIS gives fractional snow per cell; snow area here is the fraction-weighted area, which is smaller than the snow extent of binary products such as the Rutgers / NOAA snow charts.",
        "Monthly steps: the map jumps once a month, nothing is interpolated between months.",
    ]
    beats = [
        {"t": 0, "text": f"August 2019. Northern Hemisphere snow is near its yearly low, {extent[0]} million square kilometres, mostly Greenland. Land averages {tland[0]} degrees Celsius."},
        {"t": 3, "text": f"November: snow spreads across Siberia and Canada, {extent[3]} million square kilometres; land has cooled to {tland[3]} degrees."},
        {"t": tmin, "text": f"{MNAME[tmin]} is the coldest month on Northern Hemisphere land, {tland[tmin]} degrees Celsius."},
        {"t": imax, "text": f"{MNAME[imax]}: snow peaks at {extent[imax]} million square kilometres seen by MODIS ({unobs[imax]} million more land is hidden by night or cloud)."},
        {"t": 9, "text": f"May: the melt runs north, snow is down to {extent[9]} million square kilometres, land is at {tland[9]} degrees."},
        {"t": imin, "text": f"{MNAME[imin]}: back to the summer minimum, {extent[imin]} million square kilometres. Across the year snow area and land temperature move in opposition: r {lk['r']} with temperature leading by {-lk['lag']} month (r {lk['r_lag0']} with no lag), over {lk['n']} months."},
    ]
    snow_enc = SL.enc_grid(snow_grid, 0, 100, 0.5, 89.5, -179.5, 179.5, list(range(NT)), "% snow cover", "observed", floor=10)
    temp_enc = SL.enc_grid(temp_grid, -40, 35, 0.25, 89.25, -179.6875, 179.0625, list(range(NT)), "C", "model", floor=-40)
    obj = {
        "title": "Snow follows the cold",
        "timebase": "month", "t0": "2019-08-01T00:00Z", "step_s": 0, "n": NT,
        "region": {"lat0": 20.0, "lat1": 80.0, "lon0": -180.0, "lon1": 180.0},
        "hero": "snow", "partner": "temp", "link": lk,
        "hero_norm": {"min": min(extent), "max": max(extent), "method": "min..max of the hero series itself (NH snow area, million km2), Aug 2019 to Jul 2020"},
        "stats": stats, "gaps": gaps, "beats": beats,
        "events": [{"t": imax, "label": "snow maximum"}, {"t": tmin, "label": "coldest month"}, {"t": imin, "label": "snow minimum"}],
        "bands": [{"t0": 4, "t1": 7, "label": "Dec to Mar, winter"}],
        "months": MNAME,
        "obs_unobserved_mkm2": unobs, "obs_observed_land_mkm2": obs,
        "sources": [
            {"name": "MODIS/Terra Snow Cover Monthly L3 Global 0.05Deg CMG, Version 61 (MOD10CM)", "producer": "NASA, Hall and Riggs, distributed by NSIDC DAAC",
             "resolution": "0.05 deg, monthly, shown at 1 deg", "kind": "observed", "period": "2019-08 to 2020-07", "baseline": "none (cycle: own min..max)",
             "url": "https://doi.org/10.5067/MODIS/MOD10CM.061"},
            {"name": "MERRA-2 tavgM_2d_slv_Nx monthly 2 m air temperature (M2TMNXSLV v5.12.4)", "producer": "NASA GMAO, distributed by GES DISC",
             "resolution": "0.5 x 0.625 deg, shown at 1 x 1.25 deg, monthly", "kind": "model", "period": "2019-08 to 2020-07", "baseline": "none",
             "url": "https://doi.org/10.5067/AP1B0BA5PD2K"},
            {"name": "MERRA-2 constant fields (M2C0NXASM), land and land-ice fraction", "producer": "NASA GMAO, distributed by GES DISC",
             "resolution": "0.5 x 0.625 deg", "kind": "model", "period": "constant", "baseline": "none",
             "url": "https://doi.org/10.5067/ME5QX6Q5IGGU"},
        ],
        "layers": [
            {"id": "snow", "type": "field", "palette": "snow", "name": "Snow cover", "unit": "million km2", "color": "#e8f4ff",
             "what": "Snow-covered land, MODIS on Terra, monthly (observed); lane = Northern Hemisphere snow area",
             "series": extent, "grid": snow_enc},
            {"id": "temp", "type": "field", "palette": "heat", "name": "Air temperature", "unit": "C", "color": "#ff8a5c",
             "what": "2 m air temperature, MERRA-2 reanalysis (model), monthly mean; lane = Northern Hemisphere land mean",
             "series": tland, "grid": temp_enc},
        ],
        "script": "c5_snow.py",
    }
    SL.write_story(ID, obj)


if __name__ == "__main__":
    main()
