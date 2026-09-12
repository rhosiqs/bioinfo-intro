# Bioinformatics Handbook for Plant Wet-Lab Researchers

雙語（繁體中文 / English）Quarto book：同一個 repo 產出兩種語言的網站與 PDF，
部署在 GitHub Pages。**繁體中文是主要語言**，也是唯一手寫的版本；英文版等全書寫完後
再一次翻譯。

**你只做一件事：寫中文頁。**
兩份 `_quarto.yml` 的章節清單、頁面日期都由 `tools/sync.py` 從中文頁推導，
而 `sync.py` 會在新增頁面與每次建置時自動執行。

## 英文版開關

`book.yml` 的 `english:` 決定英文版是否存在：

- `english: false`（目前）：只建置、部署中文版，網站首頁直接導向中文版，側欄沒有語言切換鈕。
  `en-US/` 只保留設定檔，章節清單仍會跟著中文版同步，架構隨時可用。
- `english: true`（全書寫完後）：下一次 sync 會把每一頁複製成英文存根（標記為未翻譯），
  開始建置、部署英文版，側欄出現語言切換鈕，接著用 `/translate` 批次翻譯（見下方）。

## 新增一頁

Command Palette → Tasks: Run Task → **New page**，依序輸入標題、英文代稱、part id 與程度。

```bash
python3 tools/new_page.py "命令列基礎" --slug command-line-basics --part basics
```

它會建立 `zh-TW/basics/command-line-basics.qmd`，並同時完成：把這一頁加進兩份章節清單、
寫入日期。你只要開始寫內容。

```markdown
---
order: 30         # 同一分區內的順序，建議留 10 的間隔
level: basic      # 章節程度：basic / beginner / intermediate / advanced
created: 2026-09-12
updated: 2026-09-12
---

# 命令列基礎 {#sec-command-line-basics}
```

- **代稱（slug）用英文**：它會成為檔名、網址與 `{#sec-...}` 標籤，只能用小寫英文、數字與連字號。
  標題本身是英文時可以省略 `--slug`。
- **每個分區（part）就是一個資料夾**：`zh-TW/<part id>/`，資料夾名稱就是 `book.yml`
  裡的 id。把檔案搬到另一個資料夾就是換分區（但網址也會跟著改變）。
  直接放在 `zh-TW/` 底下的頁面不屬於任何分區，排在前言後面。
- 第一行是 `# 標題 {#sec-xxx}`，引用其他章節寫成 `第 -@sec-xxx 章`。
- `created` / `updated` 由工具維護，不要手改。
- `level:` 由你設定（只用於章節，前言不用），標題下方會顯示對應的標籤：

  | `level:` | 中文 | English |
  |---|---|---|
  | `basic` | 基礎 | Basic |
  | `beginner` | 初學者 | Beginner |
  | `intermediate` | 進階 | Intermediate |
  | `advanced` | 高階 | Advanced |

  新增頁面時預設為 `basic`（task 會讓你選，或用 `--level advanced`）。
  漏寫或拼錯時 `sync.py` 會提出警告。
- 檔名不加數字前綴：順序由 `order:` 決定，所以調整順序不會改到網址。
- 編號：章號是全書連續的（1, 2, 3…，這是 Quarto 的規則），分區則自動以
  「第一部分 / Part I」編號，順序照 `book.yml`。分區標題不要自己加數字。
- 圖片只放共用的 `_shared/images/`，各語言版的 `images/` 是 `tools/sync.py`
  自動鏡射出來的實體複本（Typst PDF 不能引用專案根目錄外的檔案，連 symlink
  也會被拒絕，所以用複本而非共用路徑或連結）——不要手動編輯這些複本，引用方式
  不變：`![說明](../images/xxx.png){#fig-xxx}`。
- 新增分區時才需要改根目錄的 `book.yml`（id + 兩種語言的標題），分區的先後也在那裡調整。

## 翻譯成英文（全書寫完後）

1. 把 `book.yml` 改成 `english: true`，跑一次 **Sync book**：每一頁都會產生英文存根。
   英文存根沒翻譯也能照常發布，網站會顯示中文原文並自動加上提示。
2. 產生初稿：
   - **Claude Code**：執行 `/translate`，所有待翻頁面會產生英文初稿並標記為 DRAFT。
   - **網頁版 AI**：Tasks → **Translation: export AI batch** 產生 `_translation-batch.md`，
     整份貼給 AI，結果貼回對應的 `en-US/` 檔案，再跑
     Tasks → **Translation: mark current file as AI draft**。
3. 審核：程式碼區塊必須與中文版一字不差、`{#sec-...}` 標籤不可翻譯或刪除、
   引用章節寫成 `Chapter -@sec-xxx`。審完一頁跑
   **Translation: stamp current file as reviewed**，或全部審完後跑 **stamp ALL pending**。

蓋章後只要中文檔再被修改，英文頁的狀態會自動變回 OUTDATED。

### 翻譯狀態

| 狀態 | 意義 | 影響 |
|---|---|---|
| OK | 已對照目前中文版審閱 | 無 |
| DRAFT | AI 初稿，尚未人工審閱 | 英文頁顯示「AI 初稿」提示 |
| OUTDATED | 審閱後中文原文又改過 | 英文頁顯示「可能過時」提示 |
| UNTRANSLATED | 只有中文存根 | 英文頁顯示「尚未翻譯」提示 |
| ERROR | 程式碼區塊／標籤／圖片路徑／章節清單不一致 | **建置失敗** |

狀態記在英文檔的 `translation-of`，它是**中文內文**的雜湊（不含 front matter），
所以更新日期或調整 `order:` 不會讓已審閱的翻譯變成 OUTDATED。
`--strict` 可讓非 OK 狀態也視為失敗（正式發布前使用）。
英文版關閉時，翻譯檢查一律略過。

## 本地預覽

兩種模式，用途不同：

### 單頁即時預覽（寫作時用）

打開任一 `.qmd`，按編輯器右上角 **Preview** 或 **Ctrl/Cmd+Shift+K**。存檔就自動重新整理，速度最快。

限制：只 render 那一個檔案，不會經過 `sync.py`，所以新增的頁面不會出現在側欄、
剛改完的「最後更新」日期還是舊的。這些都要整站建置才會更新。

### 整站預覽（要看側欄順序、PDF 時用）

**Ctrl/Cmd+Shift+B**（Tasks → **Build and serve**），完成後開
`http://localhost:8000`。用 WSL 或遠端連線時，Positron 會自動轉發 8000 port，
右下角會跳通知讓你直接點開。停止：在該終端機按 Ctrl+C。

伺服器啟動後會持續監看檔案，**存檔即自動更新**：先跑 `sync.py`，再只重新 render
改到的那一頁（HTML，約 1–2 秒），瀏覽器分頁自動重新整理。新增／刪除頁面、改
`order:`、`book.yml` 或 `_shared/` 時，會重新 render 整個語言版的 HTML（側欄要跟著變）。
PDF 只在一開始的完整建置產生，想更新 PDF 就重新按一次 Ctrl+Shift+B。
監看期間 render 失敗或翻譯檢查出錯只會印在終端機，伺服器不會停，修好再存檔即可。
切換 `english:` 開關後請重新啟動伺服器。

```bash
python3 tools/build.py --serve              # 等同上面那個 task（含即時更新）
python3 tools/build.py --serve --no-watch   # 只提供一次性建置結果，不監看
python3 tools/build.py                      # 只建置不啟動伺服器，輸出在 _site/
```

它會依序做：`sync.py` → 翻譯檢查 → render 已開啟的語言版 HTML 與 PDF → 組成 `_site/`
（首頁 `index.html` 由 `build.py` 自動產生）。
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

`git push` 到 main → GitHub Actions 自動建置已開啟的語言版 HTML + PDF 並部署到
`https://USER.github.io/REPO/`。

## 頁面日期

每頁標題下方顯示建立日期與最後修改日期（英文頁再加譯文審閱日期），由
`tools/page-meta.lua` 渲染。日期存在 front matter，由 `sync.py` 維護：
有 git 時取自 commit 紀錄（CI 已設 `fetch-depth: 0`），否則取檔案修改時間。
`created:` 寫入後不再變動。

## 結構

```
book.yml            英文版開關、分區定義（id + 兩種語言的標題）
.claude/CLAUDE.md   給 AI agent 的專案規則
zh-TW/              中文版（唯一手寫處）— 獨立的 Quarto book 專案
en-US/              英文版 — 設定檔常駐，頁面在開啟英文版後由 sync.py 建立
_shared/            圖片、語言切換 script、日期列樣式
tools/              new_page / sync / check_translations / build / page-meta.lua
                    translation-prompt.md（AI 提示詞與術語表，單一事實來源）
.claude/skills/translate/   /translate 批次翻譯 skill
```

## 已知限制（Quarto 1.10 + Typst orange-book）

- 中文 PDF 章節頁首顯示「章 1.」而非「第 1 章」；PDF 內章節引用會多一個句點。HTML 不受影響。
- 建置時的 `Could not load translations for zh-TW` 與 `The term Abstract has no translation defined`
  是 Pandoc 警告，不影響輸出。
- PDF 會把所有章節合併成一份文件，各章的 front matter 在合併時被捨棄，所以日期與程度標籤
  在 PDF 裡只有前言那一行會出現；HTML 每一章都有。


This work is licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a><img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/nc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">
