#!/usr/bin/env python3
"""
Create a new Chinese page, then let sync.py do the rest (chapter lists, dates,
and the English stub once the English edition is on). This is the only step
that should need a decision from you.

  python tools/new_page.py "命令列基礎" --slug command-line-basics --part basics
      # -> zh-TW/basics/command-line-basics.qmd
  python tools/new_page.py "基因體組裝" --slug assembly --part workflows --level advanced
  python tools/new_page.py "關於本書" --slug about                # -> zh-TW/about.qmd (no part)

The part is the folder: each part id from book.yml is a folder in zh-TW/.
The slug becomes the file name, the URL and the `{#sec-...}` label, so it is
written in English (lowercase letters, digits, hyphens) and carries no number
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

在這裡撰寫本章內容。

## 參考資料 {{.unnumbered}}

- Author A, Author B. (Year). Title. *Journal*, Volume(Issue), Pages. <https://doi.org/...>
"""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def next_order(part: str | None) -> int:
    orders = []
    for rel in bu.src_pages():
        if rel.as_posix() != "index.qmd" and bu.part_of(rel) == part:
            try:
                orders.append(float(bu.get_fm(bu.read(bu.SRC / rel))["order"]))
            except (KeyError, ValueError):
                pass
    return int(max(orders) + 10) if orders else 10


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("title", help="chapter title (Chinese)")
    ap.add_argument("--slug", default=None,
                    help="English file name without .qmd, e.g. command-line-basics "
                         "(required unless the title is already English)")
    ap.add_argument("--part", default=None,
                    help="part id from book.yml = the folder the page goes in (omit for a top-level page)")
    ap.add_argument("--level", default=bu.DEFAULT_LEVEL, choices=bu.LEVELS,
                    help=f"chapter level (default: {bu.DEFAULT_LEVEL})")
    args = ap.parse_args()

    part = args.part or None
    if part and part not in {p["id"] for p in bu.load_parts()}:
        print(f"WARNING  part '{part}' is not declared in book.yml - add it there to give it its titles.")

    slug = slugify(args.slug or args.title)
    if not slug:
        raise SystemExit("ERROR  give the page an English slug, e.g. --slug command-line-basics "
                         "(it becomes the file name and the URL)")
    rel = Path(part or ".") / f"{slug}.qmd"
    dst = bu.SRC / rel
    if dst.exists():
        raise SystemExit(f"ERROR  {bu.SRC.name}/{rel.as_posix()} already exists")

    body = TEMPLATE.format(title=args.title, slug=slug)
    bu.write(dst, bu.set_fm(body, {"order": next_order(part), "level": args.level}))
    print(f"created {bu.SRC.name}/{rel.as_posix()}")

    subprocess.run([sys.executable, str(Path(__file__).with_name("sync.py"))], cwd=bu.ROOT, check=True)
    print(f"\nNow write {bu.SRC.name}/{rel.as_posix()}. The chapter lists and the dates are")
    print("already taken care of.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
