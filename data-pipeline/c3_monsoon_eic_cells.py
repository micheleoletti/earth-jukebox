"""Add a numeric 2-degree grid to the EIC layer of playground/stories/c3_monsoon_eic.js, read from the EIC frames' own
colours (exact match to the colour bar), so the page never has to read image pixels (browsers may block that on file://).

cells: {"w": 180, "h": 90, "lon0": -180, "lat0": 90, "values": [bin mid values, index 1..8], "frames": [base64 uint8 per frame]}
cell byte: 0 = clear (within about 2 mm/day of usual), 1..8 = colour-bar bin (value = values[byte - 1]).
Each cell takes the colour found most often among its pixels (ties: the larger |anomaly|).
Usage: python data-pipeline/c3_monsoon_eic_cells.py   (needs Pillow and numpy)
"""
import base64
import io
import json
import pathlib
import re

import numpy as np
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent.parent
JS = REPO / "playground" / "stories" / "c3_monsoon_eic.js"


def main():
    txt = JS.read_text()
    m = re.search(r"\]\s*=\s*(\{.*\});\s*$", txt, re.S)
    obj = json.loads(m.group(1))
    eic = next(l for l in obj["layers"] if l["id"] == "eic")
    stops = eic["colorbar"]["stops"]          # [r, g, b, value]
    cols = np.array([s[:3] for s in stops], int)
    W, H = 180, 90
    out = []
    for f in eic["frames"]:
        im = Image.open(io.BytesIO(base64.b64decode(f["img"].split(",", 1)[1]))).convert("RGBA")
        a = np.asarray(im).astype(int)                       # (1024, 2048, 4)
        h, w = a.shape[:2]
        idx = np.zeros((h, w), np.uint8)
        opaque = a[..., 3] >= 128
        for i, c in enumerate(cols):
            idx[opaque & (np.abs(a[..., :3] - c).sum(-1) <= 6)] = i + 1
        # down to 1 degree: most frequent non-zero bin per cell if at least a third of the cell is coloured, else 0
        ry, rx = h // H, w // W
        blk = idx[:H * ry, :W * rx].reshape(H, ry, W, rx).transpose(0, 2, 1, 3).reshape(H, W, ry * rx)
        cell = np.zeros((H, W), np.uint8)
        for b in range(1, len(cols) + 1):
            cnt = (blk == b).sum(-1)
            better = (cnt * 3 >= ry * rx) & ((cell == 0) | (cnt > (blk == cell[..., None]).sum(-1)) |
                                            ((cnt == (blk == cell[..., None]).sum(-1)) & (abs(stops[b - 1][3]) > np.abs(np.array([0] + [s[3] for s in stops])[cell]))))
            cell[better] = b
        out.append(base64.b64encode(cell.tobytes()).decode())
    eic["cells"] = {"w": W, "h": H, "lon0": -180, "lat0": 90, "values": [s[3] for s in stops], "frames": out,
                    "note": "2 degree cells, most frequent colour-bar bin among the frame's pixels (0 = clear, within about 2 mm/day of usual)"}
    JS.write_text(txt[:m.start(1)] + json.dumps(obj, separators=(",", ":"), allow_nan=False) + txt[m.end(1):])
    print("frames", len(out), "bytes", sum(len(x) for x in out))


if __name__ == "__main__":
    main()
