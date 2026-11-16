"""EEA air quality download service helpers (hourly NO2 per sampling point, parquet), shared by e5_po_valley and c2_city_breathing.

API: https://eeadmz1-downloads-api-appservice.azurewebsites.net/ (POST /ParquetFile/urls -> list of parquet URLs, one per
sampling point, whole record). dataset 2 = E1a (verified), 1 = E2a (up to date, unverified).
Station names / coordinates: EEA DataExtract (AQ e-Reporting station metadata, zipped CSV).
Times: the parquet Start column has no DST jump (48 rows on 2020-03-29), i.e. a fixed offset; we take it as the station
time zone given in the metadata (UTC+01 for Italy and France). Validity 1, 2, 3 = valid; -1, -99 = invalid (dropped).
"""
import io
import json
import re
import subprocess
import zipfile

import numpy as np
import pandas as pd

import storylib as SL

API = "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
META_URL = "https://discomap.eea.europa.eu/App/AQViewer/download?fqn=Airquality_Dissem.b2g.measurements&f=csv"


def urls(country, city, story_id, pollutant="NO2", dataset=2):
    body = json.dumps({"countries": [country], "cities": [city], "pollutants": [pollutant], "dataset": dataset, "source": "API",
                       "dateTimeStart": "2013-01-01T00:00:00Z", "dateTimeEnd": "2023-01-01T00:00:00Z", "aggregationType": "hour"})
    out = SL.cache_dir(story_id) / f"eea_urls_{country}_{re.sub('[^A-Za-z]', '', city)}_{pollutant}_{dataset}.csv"
    if not out.exists() or out.stat().st_size < 30:
        r = subprocess.run(["curl", "-sf", "--retry", "3", "-X", "POST", API + "/ParquetFile/urls", "-H", "Content-Type: application/json",
                            "-d", body], capture_output=True, check=True)
        out.write_bytes(r.stdout)
    return [l.strip() for l in out.read_text(encoding="utf-8-sig").splitlines() if l.startswith("http")]


_META = {}


def meta(story_id):
    """DataExtract station metadata -> {EoI code: (name, lat, lon, type, area, timezone)} for NO2 sampling points."""
    if story_id in _META:
        return _META[story_id]
    z = SL.fetch(META_URL, story_id, name="eea_DataExtract.zip", min_bytes=10**6)
    with zipfile.ZipFile(z) as zf:
        df = pd.read_csv(io.BytesIO(zf.read("DataExtract.csv")), low_memory=False,
                         usecols=["Air Quality Station EoI Code", "Air Quality Station Name", "Air Pollutant", "Latitude", "Longitude",
                                  "Air Quality Station Type", "Air Quality Station Area", "Timezone"])
    df = df[df["Air Pollutant"] == "NO2"].drop_duplicates("Air Quality Station EoI Code")
    m = {r["Air Quality Station EoI Code"]: (clean_name(r["Air Quality Station Name"]), float(r["Latitude"]), float(r["Longitude"]),
                                              r["Air Quality Station Type"], r["Air Quality Station Area"], r["Timezone"])
         for _, r in df.iterrows()}
    _META[story_id] = m
    return m


def clean_name(n):
    n = str(n).replace("CITT\ufffd", "CITTA").replace("\ufffd", "").replace("?", "").replace("\u2013", "-").replace("\u2014", "-").replace("\"", "")
    return " ".join(n.split())


def eoi(url):
    return re.search(r"SPO[.-]([A-Z]{2}\d+[A-Z]?)(?=[_.-])", url).group(1)


def hourly(url, story_id):
    """One sampling point -> pandas Series of valid hourly values (ug/m3), index = Start (station time, fixed offset)."""
    p = SL.fetch(url, story_id, name="eea_" + url.rstrip("/").split("/")[-1], min_bytes=1000)
    d = pd.read_parquet(p, columns=["Start", "Value", "Validity", "AggType", "Unit"])
    d = d[(d.AggType == "hour") & (d.Validity >= 1)]
    v = pd.to_numeric(d.Value.astype(str), errors="coerce").astype(float)
    s = pd.Series(v.values, index=pd.DatetimeIndex(d.Start)).sort_index()
    s = s[(s >= 0) & s.notna()]
    return s[~s.index.duplicated()]
