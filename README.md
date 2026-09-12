> 持續撰寫中，Github pages 暫時取消發布

# 植物生物資訊學入門 Introduction to Plant Bioinformatics

一本寫給植物濕實驗室研究人員的生物資訊入門書，從電腦與命令列的基礎開始，
帶領沒有程式背景的讀者踏出分析資料的第一步。

本書以**繁體中文**撰寫，全書完成後將再推出英文版。內容仍在撰寫中，
可能有錯誤或變動，使用時請多加留意。

## 閱讀

線上版目前暫未公開，累積足夠內容後會發布到 GitHub Pages，並在網站側欄提供 PDF 下載。
在此之前，可依照下方「在本機建置」的步驟自行產生網站與 PDF。

## 意見與修正

歡迎透過 [GitHub Issues](https://github.com/rhosiqs/bioinfo-intro/issues) 回報錯誤或提出建議。
網站發布後，每一頁都會附有「編輯此頁」與「回報問題」的連結，直接對應到該頁的原始檔。

## 在本機建置

需要 Python 3.8 以上與 [Quarto](https://quarto.org)（CI 使用 1.10.18）。
找不到 `quarto` 時，建置腳本也會自動使用 Positron 或 RStudio 內建的版本，
或讀取 `QUARTO_PATH` 環境變數。

```bash
python3 tools/build.py            # 建置 HTML 與 PDF，輸出在 _site/
python3 tools/build.py --serve    # 建置後在 http://localhost:8000 預覽，存檔即自動更新
```

中文 PDF 需要 CJK 字型，否則會缺字：

```bash
sudo apt-get install fonts-noto-cjk
```

使用 VS Code 或 Positron 時，也可以從 Command Palette → Tasks: Run Task 執行下文提到的各項工具；
**Ctrl/Cmd+Shift+B** 會建置並啟動預覽伺服器。

### 預覽模式

- **單頁預覽**：在編輯器開啟 `.qmd` 後按 **Preview**（Ctrl/Cmd+Shift+K），速度最快，
  但只會 render 該檔案，側欄與頁面日期不會更新。
- **整站預覽**：`build.py --serve` 會先完整建置一次，之後持續監看檔案，存檔時只重新 render
  改動的頁面（新增頁面、調整順序或修改 `book.yml`、`_shared/` 時會重新 render 整個語言版），
  瀏覽器自動重新整理。PDF 只在啟動時的完整建置產生。

## 專案的運作方式

### 兩種語言版本

| 目錄 | 內容 |
|---|---|
| `zh-TW/` | 繁體中文版，唯一以人工撰寫的版本 |
| `en-US/` | 英文版，由中文版翻譯而來 |

章節清單、頁面日期與英文版的對應檔都由 `tools/sync.py` 從中文頁推導，
這個步驟會在新增頁面與每次建置時自動執行，因此新增一頁只需要建立一個檔案。

英文版是否建置由 `book.yml` 的 `english:` 開關決定：

- `english: false`（目前）：只建置、部署中文版，網站首頁直接導向中文版。
  `en-US/` 只保留設定檔，章節清單仍與中文版同步。
- `english: true`：`sync.py` 為每一頁建立英文對應檔（先標記為未翻譯），
  開始建置英文版，並在側欄加上語言切換鈕。

### 新增頁面

```bash
python3 tools/new_page.py "命令列基礎" --slug command-line-basics --part basics
```

這會建立 `zh-TW/basics/command-line-basics.qmd`，並更新章節清單與日期：

```markdown
---
order: 30         # 同一分區內的順序，建議留 10 的間隔
level: basic      # 章節程度：basic / beginner / intermediate / advanced
created: 2026-09-12
updated: 2026-09-12
---

# 命令列基礎 {#sec-command-line-basics}
```

撰寫慣例：

- **代稱（slug）使用英文**：它是檔名、網址與 `{#sec-...}` 標籤，只能包含小寫英文、數字與連字號，
  也不加數字前綴。章節順序由 `order:` 決定，因此調整順序不會改變網址。
- **分區（part）就是資料夾**：`zh-TW/<part id>/`，id 與兩種語言的標題定義在 `book.yml`，
  分區的先後也在那裡調整。直接放在 `zh-TW/` 底下的頁面不屬於任何分區，排在前言之後。
  把頁面移到另一個資料夾就是換分區，但網址會跟著改變。
- 每頁第一行是 `# 標題 {#sec-xxx}`；引用其他章節寫成 `第 -@sec-xxx 章`。
- `created` / `updated` 由工具維護，不需手動修改。
- `level:` 只用於章節（前言不用），會以標籤顯示在標題下方：

  | `level:` | 中文 | English |
  |---|---|---|
  | `basic` | 基礎 | Basic |
  | `beginner` | 初學者 | Beginner |
  | `intermediate` | 進階 | Intermediate |
  | `advanced` | 高階 | Advanced |

- 章號為全書連續編號（Quarto 的規則）；分區依 `book.yml` 的順序自動編為
  「第一部分 / Part I」，因此分區標題不另加數字。
- **圖片只放在 `_shared/images/`**，引用方式為 `![說明](../images/xxx.png){#fig-xxx}`。
  各語言版的 `images/` 是 `sync.py` 自動產生的複本（Typst 產生 PDF 時不能引用專案目錄以外的檔案，
  連 symlink 也不行），不應手動修改。

### 頁面日期

每頁標題下方顯示建立日期與最後修改日期，英文頁另外顯示譯文審閱日期。
日期存在 front matter，由 `sync.py` 從 git 紀錄取得（尚未 commit 的檔案則用修改時間），
`created:` 寫入後不再變動。CI 以 `fetch-depth: 0` 取得完整紀錄。

### 翻譯流程

英文版開啟後，翻譯分三步進行：

1. **產生初稿**：在 Claude Code 執行 `/translate`，或用
   `python3 tools/check_translations.py --export-batch` 匯出 `_translation-batch.md` 交給其他 AI 工具，
   再把結果貼回對應的 `en-US/` 檔案，並以 `--mark-draft` 標記為初稿。
2. **人工審核**：程式碼區塊必須與中文版完全相同，`{#sec-...}` 標籤不可翻譯或刪除，
   章節引用寫成 `Chapter -@sec-xxx`。
3. **標記為已審閱**：`python3 tools/check_translations.py --stamp <檔案>`，或全部審完後用 `--stamp-all`。

翻譯規則與術語表集中在 `tools/translation-prompt.md`。

每個英文頁的狀態記在 `translation-of`，它是中文**內文**的雜湊值（不含 front matter），
因此更新日期或調整順序不會讓已審閱的翻譯變成過時：

| 狀態 | 意義 | 影響 |
|---|---|---|
| OK | 已對照目前的中文版審閱 | 無 |
| DRAFT | AI 初稿，尚未人工審閱 | 頁面顯示「AI 初稿」提示 |
| OUTDATED | 審閱後中文版又有修改 | 頁面顯示「可能過時」提示 |
| UNTRANSLATED | 尚未翻譯，內容仍是中文 | 頁面顯示「尚未翻譯」提示 |
| ERROR | 程式碼區塊、標籤、圖片路徑或章節清單不一致 | **建置失敗** |

未翻譯或過時的頁面照常發布；`--strict` 可讓非 OK 狀態也視為失敗。
英文版關閉時，翻譯檢查一律略過。

### 部署

部署由 GitHub Actions workflow（`.github/workflows/publish.yml`）負責：推送到 `main` 後，
建置已開啟的語言版（HTML + PDF）並部署到 GitHub Pages；pull request 只建置與檢查，不部署。

網站暫未公開期間，GitHub Pages 已關閉，這個 workflow 也已停用，推送到 `main` 不會觸發建置。

### 目錄結構

```
book.yml            英文版開關、分區定義（id 與兩種語言的標題）
zh-TW/              中文版（人工撰寫）— 獨立的 Quarto book 專案
en-US/              英文版 — 設定檔常駐，頁面在開啟英文版後由 sync.py 建立
_shared/            圖片、語言切換 script、頁面資訊列與分區編號樣式
tools/              new_page / sync / check_translations / build / page-meta.lua
                    translation-prompt.md（翻譯提示詞與術語表）
.claude/            AI agent 的專案規則（CLAUDE.md）與 /translate skill
```

## 已知限制（Quarto 1.10 + Typst orange-book）

- 中文 PDF 的章節頁首顯示「章 1.」而非「第 1 章」，PDF 內的章節引用會多一個句點；HTML 不受影響。
- 建置時出現的 `Could not load translations for zh-TW` 與 `The term Abstract has no translation defined`
  是 Pandoc 的警告，不影響輸出。
- PDF 會把所有章節合併成一份文件，各章的 front matter 在合併時被捨棄，
  因此日期與程度標籤在 PDF 中只出現在前言；HTML 每一章都有。

## 授權

This work is licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a><img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">
