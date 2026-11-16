"""Local dev server for music-engine/prototype.

- static files
- PUT /bounces/<name>.wav      : bounce.html saves browser-rendered loops
- PUT /taiko-patterns.json     : piano-roll.html saves the taiko patterns
- PUT /engine-config.json      : loop-player.html saves its current mix (rhythm, synth layers, drones, volume)
- POST /bounce-taiko           : renders the patterns through Kontakt (bounce_taiko.py), returns the log
- PUT /bounces/sets/<slug>/loop-iN.wav + POST /encode-sets : browser-rendered (synth) loops -> AAC + loop-bounces.js

Usage: python3 music-engine/tools/serve.py 8766
"""
import http.server, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "prototype")
PY = os.path.join(HERE, ".venv", "bin", "python")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def _reply(self, code, text=b""):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text)

    def do_PUT(self):
        m = re.fullmatch(r"/bounces/((?:sets/[a-z0-9-]+/)?[a-z0-9_.-]+\.wav)", self.path)
        if m:
            path = os.path.join(ROOT, "bounces", m.group(1)); os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").write(self._body())
            return self._reply(204)
        if self.path == "/engine-config.json":
            open(os.path.join(ROOT, "engine-config.json"), "wb").write(self._body())
            return self._reply(204)
        if self.path == "/taiko-patterns.json":
            open(os.path.join(ROOT, "taiko-patterns.json"), "wb").write(self._body())
            return self._reply(204)
        self._reply(400, b"bad path")

    def do_POST(self):
        if self.path not in ("/bounce-taiko", "/encode-sets"):
            return self._reply(400, b"bad path")
        args = [PY, "bounce_taiko.py"] + (["--encode"] if self.path == "/encode-sets" else [])
        r = subprocess.run(args, cwd=HERE, capture_output=True, text=True)
        log = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "qml" not in l and "Type error" not in l and "ScrollBar" not in l)
        ok = r.returncode == 0 or "\ndone:" in "\n" + log   # Kontakt segfaults on teardown after a finished render
        self._reply(200 if ok else 500, log.encode())


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
