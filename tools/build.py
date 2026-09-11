#!/usr/bin/env python3
"""
Build both language editions (HTML + PDF) and assemble one static site in _site/.
Cross-platform (Windows / macOS / Linux); only needs Python 3.8+ and Quarto on PATH.

  python tools/build.py            # sync, check translations, render both editions, assemble _site/
  python tools/build.py --serve    # same, then serve _site/ at http://localhost:8000
"""
import argparse
import functools
import http.server
import os
import shutil
import subprocess
import sys
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
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

    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
        print(f"Serving http://localhost:{args.port}/  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
