# Bioinformatics Handbook for Plant Wet-Lab Researchers

雙語（English / 繁體中文）Quarto book：同一個 repo 產出兩種語言的網站與 PDF，
部署在 GitHub Pages，側欄的翻譯圖示可在兩語言的「同一頁」之間切換。

**你只做兩件事：寫英文頁、審核中文翻譯。**
中文對應檔、兩份 `_quarto.yml` 的章節清單、頁面日期都由 `tools/sync.py` 從英文頁推導，
而 `sync.py` 會在新增頁面與每次建置時自動執行。

## 新增一頁

Command Palette → Tasks: Run Task → **New page (English)**，輸入英文標題與 part id。

```bash
python3 tools/new_page.py "Command-line basics" --part basics
```

它會建立 `en-US/chapters/command-line-basics.qmd`，並同時完成：建立中文存根、
把這一頁加進兩份章節清單、寫入日期。你只要開始寫內容。

```markdown
---
part: basics      # book.yml 裡的分區 id
order: 30         # 同一分區內的順序，建議留 10 的間隔
created: 2026-09-11
updated: 2026-09-11
---

# Command-line basics {#sec-command-line-basics}
```

- 第一行是 `# 標題 {#sec-xxx}`，ID 用英文，中文版必須完全相同。
- `created` / `updated` 由工具維護，不要手改。
- 檔名不加數字前綴：順序由 `order:` 決定，所以調整順序不會改到網址。
- 圖片只放共用的 `_shared/images/`，`en-US/images/` 與 `zh-TW/images/` 是 `tools/sync.py`
  自動鏡射出來的實體複本（Typst PDF 不能引用專案根目錄外的檔案，連 symlink
  也會被拒絕，所以用複本而非共用路徑或連結）——不要手動編輯這兩個複本，引用方式
  不變：`![說明](../images/xxx.png){#fig-xxx}`。
- 新增分區時才需要改根目錄的 `book.yml`（id + 兩種語言的標題）。

## 翻譯與審核

英文頁沒翻譯也能照常發布，中文頁會顯示英文原文並自動加上提示。想翻時再批次處理：

- **Claude Code**：執行 `/translate`，所有待翻頁面會產生初稿並標記為 DRAFT。
- **網頁版 AI**：Tasks → **Translation: export AI batch** 產生 `_translation-batch.md`，
  整份貼給 AI，結果貼回對應的 `zh-TW/` 檔案，再跑
  Tasks → **Translation: mark current file as AI draft**。

審核時注意：程式碼區塊必須與英文版一字不差、`{#sec-...}` 標籤不可翻譯或刪除、
引用章節寫成 `第 -@sec-xxx 章`。審完一頁跑
**Translation: stamp current file as reviewed**，或全部審完後跑 **stamp ALL pending**。

蓋章後只要英文檔再被修改，狀態會自動變回 OUTDATED。

## 本地預覽

兩種模式，用途不同：

### 單頁即時預覽（寫作時用）

打開任一 `.qmd`，按編輯器右上角 **Preview** 或 **Ctrl/Cmd+Shift+K**。存檔就自動重新整理，速度最快。

限制：只 render 那一個檔案，不會經過 `sync.py`，所以側欄的語言切換鈕無效、
新增的頁面不會出現在側欄、剛改完的「最後更新」日期還是舊的。這些都要整站建置才會更新。

### 整站預覽（要看語言切換、側欄順序、PDF 時用）

**Ctrl/Cmd+Shift+B**（Tasks → **Build both editions and serve**），完成後開
`http://localhost:8000`。用 WSL 或遠端連線時，Positron 會自動轉發 8000 port，
右下角會跳通知讓你直接點開。停止：在該終端機按 Ctrl+C。

```bash
python3 tools/build.py --serve      # 等同上面那個 task
python3 tools/build.py              # 只建置不啟動伺服器，輸出在 _site/
```

它會依序做：`sync.py` → 翻譯檢查 → render 兩種語言的 HTML 與 PDF → 組成 `_site/`。
任何檢查沒過都會中止並指出是哪個檔案、哪一條規則。

`quarto` 不需要在 PATH 上：找不到時 `build.py` 會自動使用 Positron 內建的那份
（也支援 `QUARTO_PATH` 環境變數，以及 RStudio、macOS、Windows 的常見安裝位置）。

要在本機檢查**中文 PDF** 的話，需要另外安裝 CJK 字型，否則會缺字（CI 會自動安裝）：

```bash
sudo apt-get install fonts-noto-cjk
```

### 其他 Task

| 想做的事 | Task | 終端機指令 |
|---|---|---|
| 手動重新同步 | Sync book | `python3 tools/sync.py` |
| 看翻譯進度 | Translation: status | `python3 tools/check_translations.py` |

## 部署

`git push` 到 main → GitHub Actions 自動建置兩版 HTML + PDF 並部署到
`https://USER.github.io/REPO/`。

## 翻譯狀態

| 狀態 | 意義 | 影響 |
|---|---|---|
| OK | 已對照目前英文版審閱 | 無 |
| DRAFT | AI 初稿，尚未人工審閱 | 中文頁顯示「AI 初稿」提示 |
| OUTDATED | 審閱後英文原文又改過 | 中文頁顯示「可能過時」提示 |
| UNTRANSLATED | 只有英文存根 | 中文頁顯示「尚未翻譯」提示 |
| ERROR | 程式碼區塊／標籤／圖片路徑／章節清單不一致 | **建置失敗** |

狀態記在中文檔的 `translation-of`，它是**英文內文**的雜湊（不含 front matter），
所以更新日期或調整 `order:` 不會讓已審閱的翻譯變成 OUTDATED。
`--strict` 可讓非 OK 狀態也視為失敗（正式發布前使用）。

## 頁面日期

每頁標題下方顯示建立日期與最後修改日期（中文頁再加譯文審閱日期），由
`tools/page-dates.lua` 渲染。日期存在 front matter，由 `sync.py` 維護：
有 git 時取自 commit 紀錄（CI 已設 `fetch-depth: 0`），否則取檔案修改時間。
`created:` 寫入後不再變動。

## 結構

```
book.yml            分區定義：id + 兩種語言的標題
CLAUDE.md           給 AI agent 的專案規則
en-US/              英文版（唯一手寫處）— 獨立的 Quarto book 專案
zh-TW/              中文版 — 檔案由 sync.py 建立，內容由你審核
_shared/            語言切換 script、日期列樣式
tools/              new_page / sync / check_translations / build / page-dates.lua
                    translation-prompt.md（AI 提示詞與術語表，單一事實來源）
.claude/skills/translate/   /translate 批次翻譯 skill
index.html          依瀏覽器語言導向 en-US/ 或 zh-TW/
```

## 已知限制（Quarto 1.10 + Typst orange-book）

- 中文 PDF 章節頁首顯示「章 1.」而非「第 1 章」；PDF 內章節引用會多一個句點。HTML 不受影響。
- 建置時的 `Could not load translations for zh-TW` 是 Pandoc 警告，不影響輸出。
