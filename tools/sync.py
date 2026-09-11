#!/usr/bin/env python3
"""
Derive everything that is not the English prose from the English pages.

For every en-US/**/*.qmd it will:
  1. refresh `created:` / `updated:` in the front matter (git dates, mtime before
     `git init`), which is what the page-dates filter renders on the page;
  2. create the matching zh-TW/**/*.qmd if it is missing (a copy of the English
     body, marked UNTRANSLATED so the site shows a notice);
  3. mirror the dates onto the zh-TW page;
  4. rewrite the `chapters:` block of BOTH _quarto.yml files from book.yml,
     each page's folder (the folder name is its part id) and `order:` front
     matter. Part titles stay plain: the PDF template numbers parts itself
     ("Part I") and _shared/part-numbers.html does the same in the HTML sidebar.
  5. mirror `_shared/images/` into `en-US/images/` and `zh-TW/images/` as real
     file copies (Typst's PDF renderer can't reach outside its project
     directory, so images can't just live in `_shared/` and be referenced
     from there - and can't be symlinked either, since Typst resolves the
     symlink target and rejects it the same way).

So adding a page means adding one file, and adding an image means dropping it
into `_shared/images/` - nothing else has to be kept in step.

Usage:
  python tools/sync.py            # do it (safe to run any time; idempotent)
  python tools/sync.py --check    # report what is out of date, change nothing, exit 1
  python tools/sync.py --prune    # also delete zh-TW pages whose English source is gone
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bookutil as bu  # noqa: E402

STUB_NOTE = "PLACEHOLDER"


def chapter_tree(pages: dict[Path, dict[str, str]]) -> tuple[list, list[str]]:
    """Return (ordered structure, warnings). Structure entries are either a page
    path string or a dict {"part": {...}, "pages": [...]}.

    A page's part is its top-level folder (en-US/basics/x.qmd -> part `basics`);
    pages directly in the edition directory are top-level chapters."""
    parts = bu.load_parts()
    known = {p["id"]: p for p in parts}
    buckets: dict[str, list[Path]] = {p["id"]: [] for p in parts}
    loose: list[Path] = []
    index: list[Path] = []
    warnings: list[str] = []

    for rel, fm in pages.items():
        if rel.as_posix() == "index.qmd":
            index.append(rel)
            continue
        if "part" in fm:
            warnings.append(f"page {rel.as_posix()} has a `part:` key, which is ignored now - "
                            f"the folder decides the part. Delete the line.")
        part = bu.part_of(rel)
        if not part:
            loose.append(rel)
        elif part in buckets:
            buckets[part].append(rel)
        else:
            warnings.append(
                f"folder {bu.EN.name}/{part}/ is not a part in book.yml. "
                f"Add it there; using the folder name as its title for now."
            )
            known.setdefault(part, {"id": part, "en-US": part, "zh-TW": part})
            buckets.setdefault(part, []).append(rel)

    key = lambda rel: bu.sort_key(rel, pages[rel])  # noqa: E731
    tree: list = [rel.as_posix() for rel in sorted(index, key=key)]
    tree += [rel.as_posix() for rel in sorted(loose, key=key)]
    declared = [p["id"] for p in parts]
    for pid in dict.fromkeys(declared + [k for k in buckets if k not in declared]):
        if buckets.get(pid):
            tree.append({"part": known[pid], "pages": [r.as_posix() for r in sorted(buckets[pid], key=key)]})
    return tree, warnings


def render_chapters(tree: list, lang: str) -> str:
    out = ["  chapters:"]
    for node in tree:
        if isinstance(node, str):
            out.append(f"    - {node}")
        else:
            title = node["part"].get(lang) or node["part"]["id"]
            out.append(f'    - part: "{title}"')
            out.append("      chapters:")
            out += [f"        - {p}" for p in node["pages"]]
    return "\n".join(out)


def replace_chapters_block(text: str, block: str) -> str:
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if re.match(r"^  chapters:\s*$", l)), None)
    if start is None:
        raise SystemExit("ERROR  no `  chapters:` key found under `book:` - restore it and re-run.")
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith("   ")):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():   # keep trailing blank lines outside
        end -= 1
    return "\n".join(lines[:start] + block.split("\n") + lines[end:])


def sync_images(check: bool) -> list[str]:
    """Mirror `_shared/images/` into `en-US/images/` and `zh-TW/images/` as real
    files (Typst's PDF sandbox refuses paths - and so refuses symlinks that
    resolve outside the project - so each edition needs its own copy)."""
    changes: list[str] = []
    src_files = {
        p.relative_to(bu.SHARED_IMAGES): p
        for p in bu.SHARED_IMAGES.rglob("*") if p.is_file()
    } if bu.SHARED_IMAGES.exists() else {}

    for lang in bu.LANGS:
        dest_dir = bu.ROOT / lang / "images"
        for rel, src in src_files.items():
            dst = dest_dir / rel
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                if not check:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(src.read_bytes())
                changes.append(f"image   {lang}/images/{rel.as_posix()}")
        if dest_dir.exists():
            for p in dest_dir.rglob("*"):
                if p.is_file() and p.relative_to(dest_dir) not in src_files:
                    if not check:
                        p.unlink()
                    changes.append(f"removed {lang}/images/{p.relative_to(dest_dir).as_posix()} (no longer in _shared/images)")
    return changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    ap.add_argument("--prune", action="store_true", help="delete orphaned zh-TW pages")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    changes: list[str] = []
    warnings: list[str] = []

    def note(msg: str) -> None:
        changes.append(msg)

    pages: dict[Path, dict[str, str]] = {}

    for rel in bu.en_pages():
        src = bu.EN / rel
        text = bu.read(src)
        fm = bu.get_fm(text)
        created = bu.created_date(src, fm.get("created"))
        updated = bu.modified_date(src, fm.get("updated"))
        if updated < created:
            updated = created
        new_text = bu.set_fm(text, {"created": created, "updated": updated})
        if new_text != text:
            if not args.check:
                bu.write(src, new_text, keep_mtime=True)
            note(f"dates   {bu.EN.name}/{rel.as_posix()} (created {created}, updated {updated})")
        fm.update({"created": created, "updated": updated})
        pages[rel] = fm

        # --- zh-TW counterpart -------------------------------------------------
        dst = bu.ZH / rel
        if not dst.exists():
            stub = bu.set_fm(
                bu.body_of(new_text),
                {"translation-of": STUB_NOTE, "created": created, "updated": updated},
            )
            if not args.check:
                bu.write(dst, stub)
            note(f"created {bu.ZH.name}/{rel.as_posix()} (untranslated stub)")
        else:
            zt = bu.read(dst)
            nzt = bu.set_fm(zt, {"created": created, "updated": updated})
            if nzt != zt:
                if not args.check:
                    bu.write(dst, nzt, keep_mtime=True)
                note(f"dates   {bu.ZH.name}/{rel.as_posix()}")

    # --- orphaned translations -------------------------------------------------
    for p in sorted(bu.ZH.rglob("*.qmd")):
        if "_book" in p.parts:
            continue
        rel = p.relative_to(bu.ZH)
        if rel in pages:
            continue
        if args.prune and not args.check:
            p.unlink()
            note(f"deleted {bu.ZH.name}/{rel.as_posix()} (no English source)")
        else:
            warnings.append(f"{bu.ZH.name}/{rel.as_posix()} has no English source (run with --prune to delete)")

    # --- shared images -----------------------------------------------------
    changes += sync_images(args.check)

    # --- chapter lists ---------------------------------------------------------
    tree, tree_warnings = chapter_tree(pages)
    warnings += tree_warnings
    for lang in bu.LANGS:
        cfg = bu.ROOT / lang / "_quarto.yml"
        text = bu.read(cfg)
        new_text = replace_chapters_block(text, render_chapters(tree, lang))
        if new_text != text:
            if not args.check:
                bu.write(cfg, new_text)
            note(f"updated {lang}/_quarto.yml chapter list")

    if not args.quiet:
        for w in warnings:
            print(f"WARNING  {w}")
        for c in changes:
            print(("would " if args.check else "") + c)
        print(f"sync: {len(pages)} pages, {len(changes)} change(s)"
              + (", run `python tools/sync.py` to apply" if args.check and changes else ""))
    return 1 if (args.check and changes) else 0


if __name__ == "__main__":
    sys.exit(main())
