#!/usr/bin/env python3
"""
Build both language editions (HTML + PDF) and assemble one static site in _site/.
Cross-platform (Windows / macOS / Linux); only needs Python 3.8+ and Quarto on PATH.

  python tools/build.py                # sync, check translations, render both editions, assemble _site/
  python tools/build.py --serve        # same, then serve _site/ at http://localhost:8000 and
                                       # live-reload: every save re-renders just that page (HTML)
  python tools/build.py --serve --no-watch   # serve the one-off build, no live reload
"""
import argparse
import functools
import hashlib
import http.server
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bookutil as bu  # noqa: E402

ROOT = bu.ROOT
LANGS = list(bu.LANGS)



def find_quarto():
    """Quarto on PATH, else $QUARTO_PATH, else the copy bundled with Positron /
    RStudio - which is not on the terminal PATH, so the build task would
    otherwise fail even though the editor's Preview button works."""
    found = shutil.which("quarto")
    if found:
        return found

    env = os.environ.get("QUARTO_PATH")
    if env and Path(env).exists():
        return env

    exe = "quarto.exe" if os.name == "nt" else "quarto"
    patterns = [
        Path.home() / ".positron-server/bin/*/quarto/bin" / exe,   # Positron remote / WSL
        Path.home() / ".vscode-server/bin/*/quarto/bin" / exe,
        Path("/usr/lib/rstudio/resources/app/bin/quarto/bin") / exe,
        Path("/Applications/Positron.app/Contents/Resources/app/quarto/bin") / exe,
        Path("/Applications/RStudio.app/Contents/Resources/app/quarto/bin") / exe,
    ]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        patterns.append(Path(local) / "Programs/Positron/resources/app/quarto/bin" / exe)

    candidates = []
    for pat in patterns:
        root = Path(pat.anchor)
        candidates += [c for c in root.glob(str(pat.relative_to(root))) if c.is_file()]
    if not candidates:
        return None
    newest = max(candidates, key=lambda c: c.stat().st_mtime)   # several versions may linger
    print(f"using bundled Quarto: {newest}", flush=True)
    return str(newest)


def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


# ------------------------------------------------------------------ live reload

# Injected into every HTML page the dev server hands out (never into _site/
# itself): polls the server and reloads the tab once a rebuild has finished.
RELOAD_JS = b"""<script>
(function () {  // live reload - injected by tools/build.py --serve
  var gen = null;
  setInterval(function () {
    fetch("/__livereload", { cache: "no-store" })
      .then(function (r) { return r.text(); })
      .then(function (g) { if (gen !== null && g !== gen) location.reload(); gen = g; })
      .catch(function () {});
  }, 1000);
})();
</script>
"""

# Where edits can happen, relative to each edition directory: pages, configs,
# bibliographies, styles. `images/` is excluded because sync.py writes it
# (from _shared/images/, which is watched instead).
EDITION_SUFFIXES = {".qmd", ".yml", ".yaml", ".bib", ".csl", ".css", ".scss"}
EDITION_SKIP = {"_book", ".quarto", "_freeze", "images"}


class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    generation = str(time.time_ns())   # bumped after every rebuild

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send(self, body: bytes, ctype: str):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = self.path.split("?", 1)[0].split("#", 1)[0]
        if url == "/__livereload":
            return self._send(self.generation.encode(), "text/plain")
        path = Path(self.translate_path(self.path))
        if url.endswith("/") and path.is_dir():
            path = path / "index.html"
        if path.suffix == ".html" and path.is_file():
            html = path.read_bytes()
            cut = html.rfind(b"</body>")
            html = html[:cut] + RELOAD_JS + html[cut:] if cut != -1 else html + RELOAD_JS
            return self._send(html, "text/html; charset=utf-8")
        return super().do_GET()

    def log_request(self, code="-", size="-"):
        # Keep the terminal for render output: only report failed requests.
        if str(code).isdigit() and int(code) >= 400:
            super().log_request(code, size)


def watched_files() -> list[Path]:
    files = [bu.BOOK_YML, ROOT / "index.html", ROOT / "tools" / "page-dates.lua"]
    shared = ROOT / "_shared"
    if shared.exists():
        files += [p for p in shared.rglob("*") if p.is_file()]
    for lang in LANGS:
        d = ROOT / lang
        files += [
            p for p in d.rglob("*")
            if p.suffix in EDITION_SUFFIXES and p.is_file()
            and not EDITION_SKIP.intersection(p.relative_to(d).parts[:-1])
        ]
    return [p for p in files if p.exists()]


def stat_snapshot() -> dict[Path, tuple[int, int]]:
    out = {}
    for p in watched_files():
        try:
            st = p.stat()
        except FileNotFoundError:   # deleted between listing and stat
            continue
        out[p] = (st.st_mtime_ns, st.st_size)
    return out


def hash_snapshot() -> dict[Path, str]:
    out = {}
    for p in watched_files():
        try:
            out[p] = hashlib.sha1(p.read_bytes()).hexdigest()
        except FileNotFoundError:
            continue
    return out


def rebuild(quarto: str, site: Path, changed: set[Path]) -> None:
    """Re-render only what `changed` affects, HTML only, into _site/.

    A changed page re-renders just that page. Anything that shows up on every
    page (a _quarto.yml - which sync.py rewrites when a page is added, removed
    or reordered - book.yml, _shared/, the dates filter) re-renders that whole
    edition. The PDFs are only refreshed by a full build."""
    full: set[str] = set()
    pages: dict[str, set[str]] = {lang: set() for lang in LANGS}
    for p in changed:
        rel = p.relative_to(ROOT)
        lang = rel.parts[0]
        if p == ROOT / "index.html":
            if p.exists():
                shutil.copy2(p, site / "index.html")
        elif lang in LANGS and p.suffix == ".qmd" and p.exists() and not p.name.startswith("_"):
            pages[lang].add(rel.as_posix())
        elif lang in LANGS:
            full.add(lang)
        else:
            full.update(LANGS)

    for lang in LANGS:
        targets = [lang] if lang in full else sorted(pages[lang])
        for target in targets:
            print(f"+ quarto render {target} --to html", flush=True)
            r = subprocess.run([quarto, "render", target, "--to", "html"], cwd=ROOT)
            if r.returncode != 0:
                print(f"!! render failed for {target} - fix it and save again", flush=True)
        if targets:
            # dirs_exist_ok: keeps the PDF from the initial build in place.
            shutil.copytree(ROOT / lang / "_book", site / lang, dirs_exist_ok=True)


def watch(quarto: str, site: Path, handler_cls, interval: float = 0.5) -> None:
    stats, hashes = stat_snapshot(), hash_snapshot()
    print("Watching for changes - save a page and the browser reloads it.", flush=True)
    while True:
        time.sleep(interval)
        now = stat_snapshot()
        if now == stats:
            continue
        while True:   # wait until the editor has finished writing (e.g. "Save All")
            time.sleep(0.3)
            again = stat_snapshot()
            if again == now:
                break
            now = again

        # Same bookkeeping as a full build: zh-TW stubs, chapter lists, dates.
        # Unlike a full build, a failure is reported and the server keeps running.
        r = subprocess.run([sys.executable, "tools/sync.py"], cwd=ROOT,
                           capture_output=True, text=True)
        noise = [l for l in r.stdout.splitlines() if l and not l.startswith("sync:")]
        if noise or r.returncode:
            print("\n".join(noise) + r.stderr, flush=True)

        # Snapshot AFTER sync, so its own writes don't trigger another round,
        # but compare contents, so they still count as changes (sync keeps the
        # mtime when it rewrites the dates).
        stats = stat_snapshot()
        new_hashes = hash_snapshot()
        changed = {p for p in new_hashes.keys() | hashes.keys() if new_hashes.get(p) != hashes.get(p)}
        hashes = new_hashes
        if not changed:
            continue

        r = subprocess.run([sys.executable, "tools/check_translations.py"], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout + r.stderr + "!! translation check failed (a full build would stop here)",
                  flush=True)

        started = time.time()
        rebuild(quarto, site, changed)
        handler_cls.generation = str(time.time_ns())
        print(f"Rebuilt in {time.time() - started:.1f}s - browser reloading.", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--no-watch", action="store_true",
                    help="with --serve: serve the one-off build without re-rendering on save")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    quarto = find_quarto()
    if not quarto:
        sys.exit("Quarto not found. Install it from https://quarto.org, or set QUARTO_PATH "
                 "to the quarto executable. Positron's bundled copy is picked up automatically.")

    # Derive the zh-TW stubs, both chapter lists and the page dates from the
    # English pages, so a forgotten bookkeeping step can never fail the build.
    run([sys.executable, "tools/sync.py"])

    checker = [sys.executable, "tools/check_translations.py"]
    run(checker)
    if os.environ.get("CI") == "true":
        # CI only: add "outdated / not yet reviewed" notices to zh-TW pages
        # in the throwaway checkout. Never runs on your working copy.
        run(checker + ["--annotate"])

    for lang in LANGS:
        run([quarto, "render", lang])

    site = ROOT / "_site"
    shutil.rmtree(site, ignore_errors=True)
    for lang in LANGS:
        shutil.copytree(ROOT / lang / "_book", site / lang)
    shutil.copy2(ROOT / "index.html", site / "index.html")
    (site / ".nojekyll").touch()
    print(f"Site assembled in {site}")

    if not args.serve:
        return 0

    live = not args.no_watch
    handler_cls = LiveReloadHandler if live else http.server.SimpleHTTPRequestHandler
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", args.port), functools.partial(handler_cls, directory=str(site)))
    print(f"Serving http://localhost:{args.port}/  (Ctrl+C to stop)", flush=True)
    try:
        if live:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            watch(quarto, site, handler_cls)
        else:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
