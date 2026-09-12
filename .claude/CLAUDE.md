# CLAUDE.md

Bilingual Quarto book: `zh-TW/` (Traditional Chinese, the primary language,
authored by hand) and `en-US/` (English, AI-translated from the Chinese in one
batch once the book is written, then human-reviewed). Each built edition
renders to HTML + PDF and deploys to GitHub Pages - but publishing is paused
for now: Pages is off and the "Build and deploy" workflow is disabled. Never
re-enable either without asking.

## Rules

- **Only `zh-TW/**/*.qmd` is written by hand.** Both chapter lists in
  `*/_quarto.yml`, the sidebar language switch, the page dates and (once the
  English edition is on) the en-US pages are derived by `tools/sync.py`.
  Never hand-edit a `chapters:` or `sidebar:` block or a `created:` /
  `updated:` key.
- **The English edition is off until the author turns it on** (`english: false`
  in `book.yml`): no en-US pages are created, built, deployed or linked. Never
  flip the switch without asking - it publishes the English site.
- **Images only ever go in `_shared/images/`.** `tools/sync.py` mirrors them
  into real file copies at `<edition>/images/` for every built edition (not
  symlinks - Typst's PDF renderer refuses any path, symlinked or not, that
  resolves outside its project directory). Never hand-edit those copies.
- **Never edit `zh-TW/` when translating**, and never mark a translation as
  reviewed for the user - only they approve translations.
- A page's part is its folder (`zh-TW/<part-id>/page.qmd`, ids declared in
  `book.yml`); pages directly in `zh-TW/` have no part. Its front matter holds
  `order`, `level` (authored, Chinese only) and `created`, `updated` (machine-
  managed); en-US pages add `translation-of`, `reviewed` (machine-managed;
  `level` and the dates are mirrored to en-US by `sync.py`). There is no
  `part:` key.
- File names, URLs and `{#sec-...}` labels use an English slug
  (`new_page.py --slug`), never Chinese, and carry no number prefix.
- `level:` is one of `basic` / `beginner` / `intermediate` / `advanced`, on
  chapters only (never `index.qmd`). Ids live in `bookutil.LEVELS`, display
  labels in `tools/page-meta.lua` - change both together.
- Chapter numbers are Quarto's book-wide ones. Parts are numbered "第一部分" /
  "Part I" by `_shared/part-numbers.html` (HTML) and the PDF template, so
  part titles in `book.yml` carry no number.
- Code blocks must be byte-identical across both editions; `{#sec-...}` labels
  must match. These are enforced once the English edition is on and break the
  build (only warnings on OUTDATED pages, whose translation predates the
  current Chinese).
- Untranslated pages are fine: they deploy with a notice. Translation progress
  never blocks publishing.

## Commands

```bash
python3 tools/new_page.py "命令列基礎" --slug command-line-basics --part basics
                                                   # add zh-TW/basics/command-line-basics.qmd (does everything else)
python3 tools/sync.py                              # derive chapter lists, dates, en-US stubs (English on)
python3 tools/check_translations.py                # status; --pending, --strict, --export-batch
python3 tools/check_translations.py --stamp FILE   # author marks a translation reviewed
python3 tools/build.py --serve                     # full build + local site at :8000, live reload on save
```

Use the `translate` skill for batch translation. Parts and the English switch
are declared in `book.yml`. Human-facing docs: `README.md`.

## Commits

Subject line is `<type>: <short summary>` (lowercase type, English summary),
e.g. `cont: update system page`. Pick the type by what changed:

- `cont` - book content: pages under `zh-TW/` / `en-US/`, images, translations.
- `feat` - a new feature of the site, PDF, or tooling (e.g. level badges,
  part numbering).
- `fix` - a bug fix in the site, PDF, build, or tooling.
- `docs` - other updates to scripts under `tools/` or to documentation
  (`README.md`, `CLAUDE.md`, skills) that are neither a feature nor a fix.
- `chore` - routine maintenance: config, `.gitignore`, build/preview settings,
  dependency bumps.
