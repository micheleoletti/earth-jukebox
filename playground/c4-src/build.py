# Inline the C4 data (textures, tree cells, series) so the page works from file:// in Safari.
import base64, json, pathlib

root = pathlib.Path(__file__).resolve().parent
data = root.parent.parent / "data" / "c4"
series = json.loads((data / "series.json").read_text())
series.pop("mauna_loa", None)  # full record not needed on this page
payload = {
    "mask": "data:image/png;base64," + base64.b64encode((data / "textures" / "landmask.png").read_bytes()).decode(),
    "tex": ["data:image/jpeg;base64," + base64.b64encode((data / "textures" / f"ndvi_2021_{m:02d}.jpg").read_bytes()).decode()
            for m in range(1, 13)],
    "trees": base64.b64encode((data / "trees_0p5deg_2021.bin").read_bytes()).decode(),
    "series": series,
}
html = (root / "template.html").read_text().replace("/*__DATA__*/", json.dumps(payload))
out = root.parent / "breathing.html"
out.write_text(html)
print(out, round(len(html) / 1e6, 2), "MB")
