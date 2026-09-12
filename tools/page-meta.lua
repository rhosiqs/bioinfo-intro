--[[
  Render the per-page meta line kept in the front matter by tools/sync.py, just
  under the chapter title: the chapter's level badge, then "created / last
  updated".

  These are metadata, not prose, so they live outside the page body: that keeps
  them out of the translation hash and means a date refresh or a level change
  never marks a reviewed English page as outdated. The English page additionally
  shows when its translation was last reviewed by a human.

  `level:` is set by the author on Chinese chapters only (never on index.qmd);
  sync.py copies it to the English page. The valid ids are bookutil.LEVELS -
  keep that list and LEVELS below in step.
]]

local stringify = pandoc.utils.stringify

local LABELS = {
  en      = { created = "Created",  updated = "Last updated", reviewed = "Translation reviewed" },
  ["zh-TW"] = { created = "建立於", updated = "最後更新",     reviewed = "譯文審閱" },
}

local LEVELS = {
  en        = { basic = "Basic", beginner = "Beginner", intermediate = "Intermediate", advanced = "Advanced" },
  ["zh-TW"] = { basic = "基礎",  beginner = "初學者",   intermediate = "進階",         advanced = "高階" },
}

local function pick(tbl, lang)
  -- exact tag first (zh-TW), then the primary subtag (en-US -> en), then English
  return tbl[lang] or tbl[lang:match("^[^-]+") or "en"] or tbl.en
end

local function value(meta, key)
  local v = meta[key]
  if v == nil then return nil end
  local s = stringify(v)
  if s == "" then return nil end
  return s
end

function Pandoc(doc)
  local meta = doc.meta
  local lang = value(meta, "lang") or "en"
  local labels = pick(LABELS, lang)
  local html = FORMAT:match("html")

  local parts = {}
  for _, key in ipairs({ "created", "updated", "reviewed" }) do
    local v = value(meta, key)
    if v then table.insert(parts, labels[key] .. " " .. v) end
  end

  local level = value(meta, "level")
  local level_label = level and pick(LEVELS, lang)[level]
  if #parts == 0 and not level_label then return nil end

  local inlines = {}
  if level_label then
    if html then
      table.insert(inlines, pandoc.Span(level_label, pandoc.Attr("", { "level-badge", "level-" .. level })))
      table.insert(inlines, pandoc.Str(" "))
    else
      table.insert(inlines, pandoc.Strong(level_label))
      if #parts > 0 then table.insert(inlines, pandoc.Str(" \u{00B7} ")) end
    end
  end
  for i, text in ipairs(parts) do
    if i > 1 then table.insert(inlines, pandoc.Str(" \u{00B7} ")) end
    table.insert(inlines, pandoc.Str(text))
  end

  local block
  if html then
    block = pandoc.Div({ pandoc.Plain(inlines) }, pandoc.Attr("", { "page-meta" }))
  else
    block = pandoc.Para({ pandoc.Emph(inlines) })
  end

  -- after the chapter's own H1 when it is still in the body, otherwise at the
  -- very top (Quarto may already have lifted the title into the metadata).
  local pos = 1
  for i, el in ipairs(doc.blocks) do
    if el.t == "Header" and el.level == 1 then
      pos = i + 1
      break
    end
  end
  table.insert(doc.blocks, pos, block)
  return doc
end
