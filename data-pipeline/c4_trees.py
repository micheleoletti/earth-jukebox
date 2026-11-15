"""Vegetated 0.5 deg cells with monthly NDVI, for 3D tree instances on the globe.

Output binary (little endian), per cell: int16 lat*100, int16 lon*100, 12 x uint8 NDVI (0..255 = 0..1).
Cells kept: max monthly NDVI >= THRESH.

Usage: python c4_trees.py <raw_dir> <out_file>

Three-year variant: data/c4/trees_0p5deg_2021_2023.bin has the same cells, 36 x uint8 per cell (Jan 2021 to Dec 2023),
from Jose's c4-breathing-v2 run (its 2021 months equal trees_0p5deg_2021.bin byte for byte).
"""
import glob
import os
import sys

import numpy as np
from pyhdf.SD import SD, SDC

YEAR, CELL, THRESH = 2021, 10, 0.25  # 10 x 0.05 deg = 0.5 deg


def main(raw, out):
    files = sorted(glob.glob(os.path.join(raw, f"MOD13C2.A{YEAR}*.hdf")))
    assert len(files) == 12, len(files)
    months = []
    for f in files:
        a = SD(f, SDC.READ).select("CMG 0.05 Deg Monthly NDVI").get().astype(np.float32)
        a[a <= -2000] = np.nan
        a = (a / 10000.0).reshape(3600 // CELL, CELL, 7200 // CELL, CELL)
        with np.errstate(all="ignore"):
            land = np.mean(~np.isnan(a), axis=(1, 3))
            m = np.nanmean(a, axis=(1, 3))
        m[land < 0.5] = np.nan  # mostly water: drop
        months.append(m)
    v = np.array(months)  # [12][360][720]
    with np.errstate(all="ignore"):
        mx = np.nanmax(v, axis=0)
    keep = np.argwhere(mx >= THRESH)
    lat = 90 - (keep[:, 0] + 0.5) * 0.5
    lon = -180 + (keep[:, 1] + 0.5) * 0.5
    nd = np.nan_to_num(v[:, keep[:, 0], keep[:, 1]].T, nan=0.0)  # [n][12]
    rec = np.zeros(len(keep), dtype=[("lat", "<i2"), ("lon", "<i2"), ("ndvi", "u1", 12)])
    rec["lat"] = np.round(lat * 100)
    rec["lon"] = np.round(lon * 100)
    rec["ndvi"] = np.clip(np.round(nd * 255), 0, 255)
    rec.tofile(out)
    print(out, len(keep), "cells", os.path.getsize(out) / 1e6, "MB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
