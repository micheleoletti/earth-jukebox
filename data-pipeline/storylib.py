"""Shared helpers for story pipelines: encode grids / winds / series, compute links, write playground/stories/<id>.js.

Format: see data-pipeline/STORY_FORMAT.md. Every story pipeline imports this module:

    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent)); import storylib as SL

Rules (owner's, non-negotiable): gaps stay None (never bridged), linear scales with a stated floor,
models labelled "model", real numbers only.
"""
import base64
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import subprocess
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = REPO.parent / "earth-jukebox-cache"


def cache_dir(story_id):
    p = CACHE / story_id
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------- downloads
def fetch(url, story_id, name=None, headers=None, token=False, retries=4, min_bytes=1):
    """Download url into the cache (once). token=True adds the Earthdata bearer header (never printed)."""
    name = name or hashlib.sha1(url.encode()).hexdigest()[:16] + "_" + url.split("?")[0].rstrip("/").split("/")[-1][-60:]
    out = cache_dir(story_id) / name
    if out.exists() and out.stat().st_size >= min_bytes:
        return out
    cmd = ["curl", "-sfL", "--retry", "3", "--max-time", "600", "-o", str(out) + ".part"]
    for h in (headers or []):
        cmd += ["-H", h]
    if token:
        tok = (pathlib.Path.home() / ".earthdata_token").read_text().strip()
        cmd += ["-H", "Authorization: Bearer " + tok]
    cmd.append(url)
    for k in range(retries):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and os.path.exists(str(out) + ".part") and os.path.getsize(str(out) + ".part") >= min_bytes:
            os.replace(str(out) + ".part", out)
            return out
        time.sleep(2 + 3 * k)
    raise RuntimeError(f"download failed ({r.returncode}): {url[:120]}")


def fetch_json(url, story_id, **kw):
    return json.loads(fetch(url, story_id, **kw).read_text())


# ---------------------------------------------------------------- cleaning / encoding
def clean(a, nd=3):
    """list/array -> JSON list, NaN/inf/None -> None, rounded."""
    out = []
    for v in np.asarray(a, dtype=float).ravel().tolist() if not isinstance(a, list) else a:
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            out.append(None)
        else:
            out.append(round(float(v), nd))
    return out


def enc_grid(arr, vmin, vmax, lat0, lat1, lon0, lon1, t, unit, kind="observed", floor=None):
    """arr: (nt, nlat, nlon) float with NaN = no data; rows south->north, cols west->east, cell centres.
    lat0/lat1/lon0/lon1 = centres of the first/last row/col. t = story step index of each frame (float list).
    Byte 0 = no data, 1..255 = linear vmin..vmax (clamped). floor: value below which the page draws nothing (stated)."""
    a = np.asarray(arr, dtype=float)
    q = np.where(np.isnan(a), 0, 1 + np.round(np.clip((a - vmin) / (vmax - vmin), 0, 1) * 254)).astype(np.uint8)
    return {"lat0": lat0, "lat1": lat1, "lon0": lon0, "lon1": lon1, "nlat": a.shape[1], "nlon": a.shape[2],
            "nt": a.shape[0], "t": clean(t, 3), "min": vmin, "max": vmax, "unit": unit, "kind": kind,
            "floor": floor if floor is not None else vmin, "data": base64.b64encode(q.tobytes()).decode()}


def enc_wind(u, v, lat0, lat1, lon0, lon1, t, scale=0.25, source="ERA5 10 m wind (reanalysis model)"):
    """u, v: (nt, nlat, nlon) m/s, NaN allowed (-> 0, flagged -128). int8 = value / scale."""
    def q(x):
        x = np.asarray(x, dtype=float)
        return np.where(np.isnan(x), -128, np.clip(np.round(x / scale), -127, 127)).astype(np.int8)
    U, V = q(u), q(v)
    return {"lat0": lat0, "lat1": lat1, "lon0": lon0, "lon1": lon1, "nlat": U.shape[1], "nlon": U.shape[2],
            "nt": U.shape[0], "t": clean(t, 3), "scale": scale, "source": source,
            "u": base64.b64encode(U.tobytes()).decode(), "v": base64.b64encode(V.tobytes()).decode()}


# ---------------------------------------------------------------- statistics
def _pairs(a, b, lag):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if lag > 0:
        a, b = a[:-lag], b[lag:]
    elif lag < 0:
        a, b = a[-lag:], b[:lag]
    m = ~(np.isnan(a) | np.isnan(b))
    return a[m], b[m]


def pearson(a, b):
    a, b = _pairs(a, b, 0)
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return None, len(a)
    return float(np.corrcoef(a, b)[0, 1]), len(a)


def link(a, b, max_lag, step_label, method, min_n=8, sign_hint=None):
    """Pearson r between hero a and partner b for b lagging a by 0..max_lag steps (and leading by up to max_lag).
    Positive lag = b follows a. Returns the best |r| (or best in the expected sign if sign_hint given)."""
    rows = []
    for k in range(-max_lag, max_lag + 1):
        x, y = _pairs(a, b, k)
        if len(x) >= min_n and x.std() > 0 and y.std() > 0:
            rows.append((k, float(np.corrcoef(x, y)[0, 1]), len(x)))
    if not rows:
        return {"r": None, "lag": None, "n": 0, "method": method, "lag_unit": step_label, "note": "not enough overlapping data"}
    key = (lambda r: r[1] * sign_hint) if sign_hint else (lambda r: abs(r[1]))
    k, r, n = max(rows, key=key)
    r0 = next((x for x in rows if x[0] == 0), (0, None, 0))
    strength = "strong" if abs(r) >= .6 else "moderate" if abs(r) >= .3 else "weak"
    return {"r": round(r, 3), "lag": k, "n": n, "r_lag0": None if r0[1] is None else round(r0[1], 3),
            "sign": "positive" if r > 0 else "negative", "strength": strength,
            "method": method, "lag_unit": step_label, "curve": [[x[0], round(x[1], 3)] for x in rows]}


def remove_cycle(x, period):
    """Subtract the mean of each phase of a cycle (e.g. 24 for hour of day on hourly data). NaN-safe."""
    x = np.asarray(x, dtype=float).copy()
    for p in range(period):
        s = x[p::period]
        if np.isfinite(s).any():
            x[p::period] = s - np.nanmean(s)
    return x


def norm_stats(baseline_values, years, method):
    """Hero normal from baseline years: mean and standard deviation (sigma) for the music intensity mapping."""
    b = np.asarray(baseline_values, dtype=float)
    b = b[np.isfinite(b)]
    return {"mean": round(float(b.mean()), 4), "sd": round(float(b.std(ddof=1)), 4), "n": int(len(b)),
            "years": years, "method": method}


def pct(a, b):
    return None if (a is None or b is None or b == 0) else round((a / b - 1) * 100, 1)


def gap_count(series):
    return int(sum(1 for v in series if v is None or (isinstance(v, float) and math.isnan(v))))


# ---------------------------------------------------------------- output
def write_story(story_id, obj):
    obj = dict(obj)
    obj["id"] = story_id
    obj["generated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    js = REPO / "playground" / "stories" / f"{story_id}.js"
    js.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(obj, separators=(",", ":"), allow_nan=False)
    js.write_text(f"// generated by data-pipeline/{obj.get('script', story_id + '.py')}, do not edit\n"
                  f"(window.STORY_DATA = window.STORY_DATA || {{}})['{story_id}'] = {body};\n")
    d = REPO / "data" / story_id
    d.mkdir(parents=True, exist_ok=True)
    summary = {k: obj.get(k) for k in ("id", "title", "timebase", "t0", "n", "hero", "partner", "link", "stats", "gaps", "hero_norm", "sources")}
    (d / "summary.json").write_text(json.dumps(summary, indent=1, allow_nan=False))
    print(f"wrote {js.relative_to(REPO)} {js.stat().st_size / 1e6:.2f} MB")
    print_headline(obj)
    return js


def print_headline(obj):
    print("=" * 70)
    print("STORY", obj["id"], "|", obj.get("title"))
    lk = obj.get("link") or {}
    print(f"  link {obj.get('hero')} -> {obj.get('partner')}: r={lk.get('r')} lag={lk.get('lag')} {lk.get('lag_unit')} n={lk.get('n')} ({lk.get('strength')}) method: {lk.get('method')}")
    for k, v in (obj.get("stats") or {}).items():
        print(f"  {k}: {v}")
    print("  gaps:")
    for g in obj.get("gaps") or ["none"]:
        print("   -", g)
    print("=" * 70)
