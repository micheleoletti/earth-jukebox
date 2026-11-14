# Inline the local textures as data URIs so the page works from file:// in Safari (no CORS).
import base64, json, pathlib
root = pathlib.Path(__file__).resolve().parent
img_dir = root.parent / "3d"
keys = ["globe_3912", "globe_5313", "globe_5011"] + [f"card_{i}" for i in
        ["5313", "3912", "5011", "5425", "5196", "4950", "5669", "5533", "4960", "13786"]]
imgs = {}
for k in keys:
    p = img_dir / f"{k}.jpg"
    imgs[k] = "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()
html = (root / "template.html").read_text().replace("/*__IMAGES__*/", json.dumps(imgs))
out = root.parent.parent / "datasets-3d.html"
out.write_text(html)
print(out, round(len(html) / 1e6, 2), "MB")
