---
name: translate
description: Batch-translate the book's Traditional Chinese (zh-TW) pages into English (en-US) drafts for the author to review later. Use when the user asks to translate pages, produce English drafts, or clear the translation backlog in this Quarto book.
allowed-tools: Bash, Read, Write, Edit
---

# Batch translation (zh-TW -> en-US)

The Chinese pages are the source; produce English AI drafts only. The author
reviews and approves them later; never stamp a page as reviewed on their behalf,
and never edit anything under `zh-TW/`.

## Steps

1. Check `english:` in `book.yml`. If it is `false`, the English edition is off
   and there is nothing to translate yet: ask the user whether to switch it on
   (it also starts building and publishing the English site). Only set it to
   `true` if they agree.
2. `python3 tools/sync.py --quiet && python3 tools/check_translations.py --pending`
   gives the work list. If the user named specific files, use those instead.
3. Read `tools/translation-prompt.md` and follow its rules and glossary exactly.
4. For each pending page, read `zh-TW/<path>` and write the English translation
   to `en-US/<path>`:
   - Write the **body only**. No YAML front matter - it is machine-managed and
     would be overwritten. The first line is `# Title {#sec-...}`.
   - Fenced code blocks must be byte-identical to the Chinese, comments included.
   - Never translate or drop `{#sec-...}` / `{#fig-...}` labels. Cross-references
     to chapters are written `Chapter -@sec-xxx`.
5. `python3 tools/check_translations.py --mark-draft <files written>`, then
   `python3 tools/sync.py --quiet && python3 tools/check_translations.py`.
   Fix any ERROR (code block / label / image path mismatch) until it passes.
6. Report which pages were drafted and remind the user to review them, then run
   the "Translation: stamp current file as reviewed" task (or `--stamp-all` once
   the whole batch is reviewed).
