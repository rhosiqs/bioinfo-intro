#!/usr/bin/env python3
"""
Shared helpers for the bilingual Quarto book tooling (sync.py / check_translations.py).

Design notes
------------
* Only the English page is authored by hand. Everything else (the zh-TW stub,
  both chapter lists, the created / last-modified dates) is derived from it.
* All machine-managed state lives in the YAML front matter of the .qmd files,
  so the repository stays self-describing and no side-car database can drift.
* The translation hash covers the page BODY only, so refreshing a date,
  changing `order:` or moving a page to another part folder never marks a
  reviewed translation as outdated.
* No third-party dependencies: the tiny YAML reader below only has to cope with
  the flat `key: value` front matter this project writes itself.
"""
from __future__ import annotations

import datetime
import functools
import hashlib
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "en-US"
ZH = ROOT / "zh-TW"
LANGS = (EN.name, ZH.name)
BOOK_YML = ROOT / "book.yml"
SHARED_IMAGES = ROOT / "_shared" / "images"

# Front matter keys we manage, in the order they are written back.
FM_ORDER = ["order", "created", "updated", "translation-of", "reviewed"]

TODAY = datetime.date.today().isoformat()


# --------------------------------------------------------------------------- io

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def write(p: Path, text: str, keep_mtime: bool = False) -> bool:
    """Write only when the content actually changed. Returns True if written.

    keep_mtime restores the previous modification time, so that the tools
    rewriting their own front matter is not mistaken for you editing the page
    (the mtime is the fallback "last modified" source before `git init`)."""
    if p.exists() and read(p) == text:
        return False
    before = p.stat().st_mtime if p.exists() else None
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    if keep_mtime and before is not None:
        os.utime(p, (before, before))
    return True


# ------------------------------------------------------------------ front matter

def split_front_matter(text: str) -> tuple[str | None, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[4:end], text[end + 5:]
        if text.rstrip().endswith("\n---"):
            return text[4:text.rstrip().rfind("\n---")], ""
    return None, text


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v.split("  #")[0].strip()


def parse_fm(fm: str | None) -> dict[str, str]:
    """Flat `key: value` pairs only; nested blocks are ignored (and preserved
    verbatim by set_fm, which keeps unknown lines)."""
    out: dict[str, str] = {}
    if not fm:
        return out
    for line in fm.split("\n"):
        if not line.strip() or line.startswith((" ", "\t", "#")):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = _unquote(v)
    return out


def get_fm(text: str) -> dict[str, str]:
    return parse_fm(split_front_matter(text)[0])


def body_of(text: str) -> str:
    return split_front_matter(text)[1]


def set_fm(text: str, updates: dict[str, str | None]) -> str:
    """Merge `updates` into the front matter. A None value removes the key.
    Unknown keys already present are kept; known keys are written in FM_ORDER."""
    fm, body = split_front_matter(text)
    data = parse_fm(fm)
    for k, v in updates.items():
        if v is None:
            data.pop(k, None)
        else:
            data[k] = str(v)
    if not data:
        return body.lstrip("\n")
    keys = [k for k in FM_ORDER if k in data] + [k for k in data if k not in FM_ORDER]
    lines = "\n".join(f"{k}: {data[k]}" for k in keys)
    return f"---\n{lines}\n---\n\n{body.lstrip(chr(10))}"


def body_digest(text_or_path) -> str:
    text = read(text_or_path) if isinstance(text_or_path, Path) else text_or_path
    return hashlib.sha256(body_of(text).strip().encode("utf-8")).hexdigest()[:12]


# -------------------------------------------------------------------------- git

def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


@functools.lru_cache(maxsize=1)
def in_git_repo() -> bool:
    return (ROOT / ".git").exists() and _git("rev-parse", "--is-inside-work-tree").returncode == 0


def _tracked(rel: str) -> bool:
    return in_git_repo() and _git("ls-files", "--error-unmatch", rel).returncode == 0


def _dirty(rel: str) -> bool:
    return bool(_git("status", "--porcelain", "--", rel).stdout.strip())


def _log_dates(rel: str) -> list[str]:
    r = _git("log", "--format=%cs", "--", rel)
    return [l for l in r.stdout.split("\n") if l.strip()] if r.returncode == 0 else []


def _mtime_date(p: Path) -> str:
    return datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()


def created_date(p: Path, current: str | None) -> str:
    """First commit date once the file is in git, else its mtime. Never moves
    after it has been written once - history rewrites must not change it."""
    if current:
        return current
    rel = p.relative_to(ROOT).as_posix()
    if _tracked(rel):
        dates = _log_dates(rel)
        if dates:
            return dates[-1]
    return _mtime_date(p)


def modified_date(p: Path, current: str | None) -> str:
    """Last commit date when the file is committed and clean; today while it has
    uncommitted edits. Before `git init` we fall back to the file's mtime."""
    rel = p.relative_to(ROOT).as_posix()
    if _tracked(rel):
        if _dirty(rel):
            return TODAY
        dates = _log_dates(rel)
        if dates:
            return dates[0]
    mt = _mtime_date(p)
    return max(current, mt) if current else mt


# ---------------------------------------------------------------------- book.yml

def load_parts() -> list[dict[str, str]]:
    """Parts declared in book.yml, in the order the book presents them."""
    parts: list[dict[str, str]] = []
    if not BOOK_YML.exists():
        return parts
    in_parts, cur = False, None
    for raw in read(BOOK_YML).split("\n"):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if not raw.startswith((" ", "\t", "-")):
            in_parts = s.startswith("parts:")
            continue
        if not in_parts:
            continue
        if s.startswith("- "):
            cur = {}
            parts.append(cur)
            s = s[2:].strip()
            if not s:
                continue
        if cur is not None and ":" in s:
            k, v = s.split(":", 1)
            cur[k.strip()] = _unquote(v)
    return [p for p in parts if p.get("id")]


# ------------------------------------------------------------------------- pages

def en_pages() -> list[Path]:
    """English pages, as paths relative to the English edition directory."""
    return sorted(
        p.relative_to(EN) for p in EN.rglob("*.qmd")
        if "_book" not in p.parts and not p.name.startswith("_")
    )


def part_of(rel: Path) -> str | None:
    """A page's part id is its top-level folder; pages directly in the edition
    directory belong to no part."""
    return rel.parts[0] if len(rel.parts) > 1 else None


def sort_key(rel: Path, fm: dict[str, str]) -> tuple[float, str]:
    try:
        order = float(fm.get("order", ""))
    except ValueError:
        order = 1e9
    return (order, rel.as_posix())
