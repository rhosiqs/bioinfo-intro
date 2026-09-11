---
name: translate
description: Batch-translate the book's pending English pages into Traditional Chinese (zh-TW) drafts for the author to review later. Use when the user asks to translate pages, produce Chinese drafts, or clear the translation backlog in this Quarto book.
allowed-tools: Bash, Read, Write, Edit
---

# Batch translation (en-US -> zh-TW)

Produce AI drafts only. The author reviews and approves them later; never stamp a
page as reviewed on their behalf, and never edit anything under `en-US/`.

## Steps

1. `python3 tools/sync.py --quiet && python3 tools/check_translations.py --pending`
   gives the work list. If the user named specific files, use those instead.
2. Read `tools/translation-prompt.md` and follow its rules and glossary exactly.
3. For each pending page, read `en-US/<path>` and write the Traditional Chinese
   (Taiwan usage) translation to `zh-TW/<path>`:
   - Write the **body only**. No YAML front matter - it is machine-managed and
     would be overwritten. The first line is `# 標題 {#sec-...}`.
   - Fenced code blocks must be byte-identical to the English, comments included.
   - Never translate or drop `{#sec-...}` / `{#fig-...}` labels. Cross-references
     to chapters are written `第 -@sec-xxx 章`.
4. `python3 tools/check_translations.py --mark-draft <files written>`, then
   `python3 tools/sync.py --quiet && python3 tools/check_translations.py`.
   Fix any ERROR (code block / label / image path mismatch) until it passes.
5. Report which pages were drafted and remind the user to review them, then run
   the "Translation: stamp current file as reviewed" task (or `--stamp-all` once
   the whole batch is reviewed).
