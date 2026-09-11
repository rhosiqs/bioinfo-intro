#!/usr/bin/env python3
"""
Translation status and consistency checker for the en / zh-TW Quarto books.

Status of each zh-TW page, from its `translation-of:` front matter key compared
with the hash of the current English page BODY (front matter, i.e. dates and
part/order, is deliberately excluded - housekeeping never invalidates a review):

  OK            reviewed against exactly this English text
  OUTDATED      the English text changed after the review
  DRAFT         AI draft of the current English text, not reviewed by a human yet
  UNTRANSLATED  still the English text (a stub created by sync.py)
  MISSING       no zh-TW file at all (sync.py normally prevents this)

Structural checks (errors, because they break the book or mislead readers -
except on OUTDATED pages, where a stale translation is expected to differ and
they are only warnings, so translation progress never blocks publishing):
  - fenced code blocks must be byte-identical and in the same order
  - cross-reference labels ({#sec-...}, {#fig-...}, ...) must be the same set
  - image paths must be the same list
  - both _quarto.yml files must list the same chapter files in the same order

Usage:
  python tools/check_translations.py                  # report; exit 1 on structural errors
  python tools/check_translations.py --strict         # also fail on anything not OK
  python tools/check_translations.py --pending        # list pages needing translation
  python tools/check_translations.py --export-batch   # write one paste-ready AI batch file
  python tools/check_translations.py --mark-draft FILE...   # "this is an AI draft"
  python tools/check_translations.py --stamp FILE...        # "I reviewed this"
  python tools/check_translations.py --stamp-all            # review-stamp every pending page
  python tools/check_translations.py --annotate       # CI only: insert notices into zh-TW pages
No third-party dependencies.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bookutil as bu  # noqa: E402

SRC, DST = bu.EN, bu.ZH
KEY = "translation-of"
DRAFT_PREFIX = "draft:"
BATCH_FILE = bu.ROOT / "_translation-batch.md"
PROMPT_FILE = bu.ROOT / "tools" / "translation-prompt.md"

LABEL_RE = re.compile(r"\{#((?:sec|fig|tbl|lst|eq|thm|lem|cor|prp|cnj|def|exm|exr)-[\w-]+)")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
CHAPTER_RE = re.compile(r"^\s*-\s*(?:file:\s*)?([\w./-]+\.qmd)\s*$", re.M)
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")

NOTICE = """
::: {{.callout-note}}
{msg}
:::
"""
MESSAGES = {
    "OUTDATED": "此頁的英文原文在翻譯審閱後已更新，中文內容可能有落差，請以英文版為準（左側選單可切換語言）。",
    "DRAFT": "此頁為 AI 翻譯初稿，尚未經人工審閱，用字可能不精確；如有疑義請以英文版為準。",
    "UNTRANSLATED": "此頁尚未翻譯，以下顯示英文原文。",
}
PENDING = ("OUTDATED", "DRAFT", "UNTRANSLATED", "MISSING")


def read(p: Path) -> str:
    return bu.read(p)


def code_blocks(text: str) -> list[str]:
    blocks, buf, fence = [], [], None
    for line in text.split("\n"):
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(2)
                buf = [line]
        else:
            buf.append(line)
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence) and not m.group(3).strip():
                blocks.append("\n".join(buf))
                fence = None
    return blocks


def chapters(cfg: Path) -> list[str]:
    return CHAPTER_RE.findall(read(cfg))


def pages() -> list[Path]:
    return bu.en_pages()


def status(rel: Path) -> str:
    dst = DST / rel
    if not dst.exists():
        return "MISSING"
    h = bu.get_fm(read(dst)).get(KEY)
    cur = bu.body_digest(SRC / rel)
    if not h or h == "PLACEHOLDER":
        return "UNTRANSLATED"
    if h.startswith(DRAFT_PREFIX):
        return "DRAFT" if h[len(DRAFT_PREFIX):] == cur else "OUTDATED"
    return "OK" if h == cur else "OUTDATED"


def structural_errors(rel: Path) -> list[str]:
    dst = DST / rel
    if not dst.exists() or status(rel) == "UNTRANSLATED":
        return []
    a, b = bu.body_of(read(SRC / rel)), bu.body_of(read(dst))
    errs = []
    ca, cb = code_blocks(a), code_blocks(b)
    if len(ca) != len(cb):
        errs.append(f"code block count differs: en={len(ca)} zh-TW={len(cb)}")
    else:
        for i, (x, y) in enumerate(zip(ca, cb), 1):
            if x != y:
                errs.append(f"code block #{i} differs (code must be identical in both languages)")
    la, lb = set(LABEL_RE.findall(a)), set(LABEL_RE.findall(b))
    if la != lb:
        errs.append(f"cross-ref labels differ: only en={sorted(la - lb)} only zh-TW={sorted(lb - la)}")
    ia, ib = IMAGE_RE.findall(a), IMAGE_RE.findall(b)
    if ia != ib:
        errs.append(f"image paths differ: en={ia} zh-TW={ib}")
    return errs


def annotate(rel: Path, st: str) -> None:
    dst = DST / rel
    text = read(dst)
    fm, body = bu.split_front_matter(text)
    lines = body.split("\n")
    for i, line in enumerate(lines):          # insert right after the first H1
        if line.startswith("# "):
            lines.insert(i + 1, NOTICE.format(msg=MESSAGES[st]))
            break
    head = f"---\n{fm}\n---\n" if fm is not None else ""
    dst.write_text(head + "\n".join(lines), encoding="utf-8")


def rel_of(arg: str) -> Path:
    """Accept a path in either edition directory, absolute or repo-relative."""
    p = Path(arg)
    p = p if p.is_absolute() else (bu.ROOT / p)
    p = p.resolve()
    for base in (DST, SRC):
        try:
            return p.relative_to(base)
        except ValueError:
            continue
    raise SystemExit(f"ERROR  {arg} is not inside {bu.EN.name}/ or {bu.ZH.name}/")


def set_marker(rel: Path, value: str, reviewed: str | None) -> None:
    dst = DST / rel
    if not dst.exists():
        raise SystemExit(f"ERROR  {bu.ZH.name}/{rel.as_posix()} does not exist - run tools/sync.py first")
    bu.write(dst, bu.set_fm(read(dst), {KEY: value, "reviewed": reviewed}))


def pending_pages() -> list[tuple[Path, str]]:
    return [(rel, st) for rel in pages() if (st := status(rel)) in PENDING]


def export_batch() -> None:
    items = pending_pages()
    if not items:
        print("nothing pending - every zh-TW page is reviewed and current.")
        return
    prompt = read(PROMPT_FILE)
    prompt = prompt.split("\n---\n", 1)[-1].strip()
    out = ["# Translation batch", "",
           f"{len(items)} page(s) need a zh-TW translation. Give the AI the instructions",
           "below, then the English source of each page. Paste each translated body back",
           "into the matching zh-TW file (front matter is managed by the tools - leave it",
           "out), then run:  python tools/check_translations.py --mark-draft <files>", "",
           "## Instructions", "", prompt, "", "## Pages", ""]
    for rel, st in items:
        out += [f"### {bu.ZH.name}/{rel.as_posix()}  ({st})", "",
                "````````markdown", bu.body_of(read(SRC / rel)).strip(), "````````", ""]
    BATCH_FILE.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {BATCH_FILE.relative_to(bu.ROOT)} with {len(items)} page(s)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--annotate", action="store_true")
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--export-batch", action="store_true")
    ap.add_argument("--stamp", nargs="+", metavar="FILE")
    ap.add_argument("--stamp-all", action="store_true")
    ap.add_argument("--mark-draft", nargs="+", metavar="FILE")
    args = ap.parse_args()

    if args.mark_draft:
        for f in args.mark_draft:
            rel = rel_of(f)
            set_marker(rel, DRAFT_PREFIX + bu.body_digest(SRC / rel), None)
            print(f"draft   {bu.ZH.name}/{rel.as_posix()}")
        return 0

    if args.stamp or args.stamp_all:
        targets = [rel_of(f) for f in (args.stamp or [])]
        if args.stamp_all:
            targets += [rel for rel, st in pending_pages() if st != "MISSING"]
        for rel in dict.fromkeys(targets):
            h = bu.body_digest(SRC / rel)
            set_marker(rel, h, bu.TODAY)
            print(f"reviewed {bu.ZH.name}/{rel.as_posix()} <- {bu.EN.name}/{rel.as_posix()} @ {h}")
        if not targets:
            print("nothing to stamp.")
        return 0

    if args.pending or args.export_batch:
        if args.export_batch:
            export_batch()
        else:
            for rel, st in pending_pages():
                print(f"{st:<13}{bu.ZH.name}/{rel.as_posix()}")
        return 0

    failed = False
    ch_en, ch_zh = chapters(SRC / "_quarto.yml"), chapters(DST / "_quarto.yml")
    if ch_en != ch_zh:
        print(f"ERROR  _quarto.yml chapter lists differ (run tools/sync.py):"
              f"\n  en:    {ch_en}\n  zh-TW: {ch_zh}")
        failed = True

    counts: dict[str, int] = {}
    for rel in pages():
        st = status(rel)
        counts[st] = counts.get(st, 0) + 1
        errs = structural_errors(rel)
        if st != "OK" or errs:
            print(f"{st:<13}{rel.as_posix()}")
        # An OUTDATED page is a translation of an older English text, so its
        # code / labels / images are expected to lag behind. It still ships
        # (with a notice); the mismatch is fixed when the page is re-translated.
        fatal = st != "OUTDATED"
        for e in errs:
            print(f"  {'ERROR' if fatal else 'WARN '}  {e}")
            failed = failed or fatal
        if args.strict and st != "OK":
            failed = True
        if args.annotate and st in MESSAGES:
            annotate(rel, st)

    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
