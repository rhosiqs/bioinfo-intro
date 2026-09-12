# Prompt template for AI-assisted zh-TW → en translation

Used by `tools/check_translations.py --export-batch` and by the `/translate` skill
for Claude Code. To do it by hand, paste everything below the line into your AI tool,
followed by the Chinese .qmd file.

---

Translate the following Quarto Markdown (.qmd) file from Traditional Chinese (Taiwan)
into English. The audience is plant wet-lab researchers who are new to bioinformatics;
write clear, plain English and keep the author's tone.

Hard rules:
1. Do NOT change anything inside fenced code blocks (``` ... ```), including comments,
   strings, file names and indentation. Copy them byte-for-byte, even when a comment
   is written in Chinese.
2. Do NOT change cross-reference labels or references: {#sec-...}, {#fig-...}, @sec-..., @fig-...
3. Do NOT change image paths, URLs, or Quarto syntax (:::, {.callout-...}).
   Do NOT output YAML front matter at all: it is machine-managed (dates, translation
   status) and would be overwritten. Start at the `# Title {#sec-...}` line.
4. Inline code (`like_this`) stays as is.
5. A chapter reference written 第 -@sec-xxx 章 becomes Chapter -@sec-xxx.
6. In the `## 參考資料 {.unnumbered}` section, translate only the heading (References);
   copy every reference entry (authors, titles, journals, DOIs) unchanged.
7. Output only the translated body, no commentary.

Glossary (zh-TW → English):
- 定序 → sequencing
- 基因體 / 轉錄體 → genome / transcriptome
- 讀段（read）→ read
- 序列比對 / 定位（mapping）→ alignment / mapping
- 註解 → annotation
- 引子 → primer
- 質體 → plasmid
- 資料 / 檔案 / 軟體 / 程式 → data / file / software / program
- 預設 / 參數 → default / parameter
- 伺服器 / 叢集 → server / cluster
- 命令列 / 終端機 → command line / terminal
- Already English in the source, keep as is: FASTQ, FASTA, BAM, VCF, BLAST, contig,
  scaffold, k-mer, E-value, p-value

(Extend this glossary as the book grows; keep it the single source of truth.)
