# Prompt template for AI-assisted en → zh-TW translation

Used by `tools/check_translations.py --export-batch` and by the `/translate` skill
for Claude Code. To do it by hand, paste everything below the line into your AI tool,
followed by the English .qmd file.

---

Translate the following Quarto Markdown (.qmd) file from English to Traditional Chinese
as used in Taiwan (zh-TW). The audience is plant wet-lab researchers in Taiwan.

Hard rules:
1. Do NOT change anything inside fenced code blocks (``` ... ```), including comments,
   strings, file names and indentation. Copy them byte-for-byte.
2. Do NOT change cross-reference labels or references: {#sec-...}, {#fig-...}, @sec-..., @fig-...
3. Do NOT change image paths, URLs, or Quarto syntax (:::, {.callout-...}).
   Do NOT output YAML front matter at all: it is machine-managed (dates, translation
   status) and would be overwritten. Start at the `# Title {#sec-...}` line.
4. Inline code (`like_this`) stays as is.
5. Use Taiwan terminology, not Mainland China terminology (see glossary). Never output Simplified characters.
6. When referring to a chapter, write 第 -@sec-xxx 章 (number only), not @sec-xxx.
7. Output only the translated body, no commentary.

Glossary (English → zh-TW; ✗ = do not use):
- sequencing → 定序（✗ 测序/測序）
- genome / transcriptome → 基因體 / 轉錄體（✗ 基因组/基因組, 转录组）
- read (sequencing read) → read（首次出現可寫「讀段（read）」，之後保留 read）
- alignment / mapping → 序列比對 / 定位（mapping）
- annotation → 註解（✗ 注释）
- primer → 引子（✗ 引物）
- plasmid → 質體（✗ 质粒）
- data / file / software / program → 資料 / 檔案 / 軟體 / 程式（✗ 数据, 文件, 软件, 程序）
- default / parameter → 預設 / 參數（✗ 默认）
- server / cluster → 伺服器 / 叢集（✗ 服务器, 集群）
- command line / terminal → 命令列 / 終端機
- Keep in English: FASTQ, FASTA, BAM, VCF, BLAST, contig, scaffold, k-mer, E-value, p-value

(Extend this glossary as the book grows; keep it the single source of truth.)
