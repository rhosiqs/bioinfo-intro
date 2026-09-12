# CLAUDE.md

Bilingual Quarto book: `en-US/` (English, authored by hand) and `zh-TW/`
(Traditional Chinese, AI-drafted then human-reviewed). Both editions build to
HTML + PDF and deploy to GitHub Pages.

## Rules

- **Only `en-US/**/*.qmd` is written by hand.** The zh-TW page, both chapter
  lists in `*/_quarto.yml`, and the page dates are derived by `tools/sync.py`.
  Never hand-edit a `chapters:` block or a `created:` / `updated:` key.
- **Images only ever go in `_shared/images/`.** `tools/sync.py` mirrors them
  into real file copies at `en-US/images/` and `zh-TW/images/` (not symlinks -
  Typst's PDF renderer refuses any path, symlinked or not, that resolves
  outside its project directory). Never hand-edit those two copies.
- **Never edit `en-US/` when translating**, and never mark a translation as
  reviewed for the user - only they approve translations.
- A page's part is its folder (`en-US/<part-id>/page.qmd`, ids declared in
  `book.yml`); pages directly in `en-US/` have no part. Its front matter holds
  `order`, `level` (authored, English only) and `created`, `updated`,
  `translation-of`, `reviewed` (machine-managed; `level` is mirrored to zh-TW
  by `sync.py`). There is no `part:` key.
- `level:` is one of `basic` / `beginner` / `intermediate` / `advanced`, on
  chapters only (never `index.qmd`). Ids live in `bookutil.LEVELS`, display
  labels in `tools/page-meta.lua` - change both together.
- Chapter numbers are Quarto's book-wide ones. Parts are numbered "Part I" /
  "第一部分" by `_shared/part-numbers.html` (HTML) and the PDF template, so
  part titles in `book.yml` carry no number.
- Code blocks must be byte-identical across both editions; `{#sec-...}` labels
  must match. These are enforced and break the build (only warnings on
  OUTDATED pages, whose translation predates the current English).
- Untranslated pages are fine: they deploy with a notice. Translation progress
  never blocks publishing.

## Commands

```bash
python3 tools/new_page.py "Title" --part basics   # add en-US/basics/title.qmd (does everything else)
python3 tools/sync.py                             # derive zh-TW stubs, chapter lists, dates
python3 tools/check_translations.py               # status; --pending, --strict, --export-batch
python3 tools/check_translations.py --stamp FILE   # author marks a translation reviewed
python3 tools/build.py --serve                     # full build + local site at :8000, live reload on save
```

Use the `translate` skill for batch translation. Parts are declared in `book.yml`.
Human-facing docs: `README.md`.

## Commits

Subject line is `<type>: <short summary>` (lowercase type, English summary),
e.g. `cont: update system page`. Pick the type by what changed:

- `cont` - book content: pages under `en-US/` / `zh-TW/`, images, translations.
- `docs` - scripts under `tools/` or other documentation (`README.md`,
  `CLAUDE.md`, skills).
- `chore` - routine maintenance: config, `.gitignore`, build/preview settings,
  dependency bumps.
