#!/usr/bin/env python3
"""
Create a new English page, then let sync.py do the rest (zh-TW stub, chapter
lists, dates). This is the only step that should need a decision from you.

  python tools/new_page.py "Command-line basics" --part basics   # -> en-US/basics/command-line-basics.qmd
  python tools/new_page.py "Genome assembly" --part workflows --slug assembly
  python tools/new_page.py "About this book"                     # -> en-US/about-this-book.qmd (no part)

The part is the folder: each part id from book.yml is a folder in en-US/.
The slug becomes both the file name and the URL, so it carries no number
prefix: chapter order lives in the front matter (`order:`), which means
reordering the book never breaks a link somebody bookmarked.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bookutil as bu  # noqa: E402

TEMPLATE = """# {title} {{#sec-{slug}}}

Write the chapter here.

## References {{.unnumbered}}

- Author A, Author B. (Year). Title. *Journal*, Volume(Issue), Pages. <https://doi.org/...>
"""


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "page"


def next_order(part: str | None) -> int:
    orders = []
    for rel in bu.en_pages():
        if rel.as_posix() != "index.qmd" and bu.part_of(rel) == part:
            try:
                orders.append(float(bu.get_fm(bu.read(bu.EN / rel))["order"]))
            except (KeyError, ValueError):
                pass
    return int(max(orders) + 10) if orders else 10


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("title", help="English chapter title")
    ap.add_argument("--part", default=None,
                    help="part id from book.yml = the folder the page goes in (omit for a top-level page)")
    ap.add_argument("--slug", default=None, help="file name without .qmd (default: from the title)")
    args = ap.parse_args()

    part = args.part or None
    if part and part not in {p["id"] for p in bu.load_parts()}:
        print(f"WARNING  part '{part}' is not declared in book.yml - add it there to give it a Chinese title.")

    slug = args.slug or slugify(args.title)
    rel = Path(part or ".") / f"{slug}.qmd"
    dst = bu.EN / rel
    if dst.exists():
        raise SystemExit(f"ERROR  {bu.EN.name}/{rel.as_posix()} already exists")

    body = TEMPLATE.format(title=args.title, slug=slug)
    bu.write(dst, bu.set_fm(body, {"order": next_order(part)}))
    print(f"created {bu.EN.name}/{rel.as_posix()}")

    subprocess.run([sys.executable, str(Path(__file__).with_name("sync.py"))], cwd=bu.ROOT, check=True)
    print(f"\nNow write {bu.EN.name}/{rel.as_posix()}. The Chinese page, both chapter lists and the")
    print("dates are already taken care of; translate later with the translation tasks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
