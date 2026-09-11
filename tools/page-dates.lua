--[[
  Render the per-page "created / last updated" line kept in the front matter by
  tools/sync.py, just under the chapter title.

  The dates are metadata, not prose, so they live outside the page body: that
  keeps them out of the translation hash and means a date refresh never marks a
  reviewed Chinese page as outdated. The Chinese page additionally shows when
  its translation was last reviewed by a human.
]]

local stringify = pandoc.utils.stringify

local LABELS = {
  en      = { created = "Created",  updated = "Last updated", reviewed = "Translation reviewed" },
  ["zh-TW"] = { created = "建立於", updated = "最後更新",     reviewed = "譯文審閱" },
}

local function value(meta, key)
  local v = meta[key]
  if v == nil then return nil end
  local s = stringify(v)
  if s == "" then return nil end
  return s
end

function Pandoc(doc)
  local meta = doc.meta
  -- exact tag first (zh-TW), then the primary subtag (en-US -> en), then English
  local lang = value(meta, "lang") or "en"
  local labels = LABELS[lang] or LABELS[lang:match("^[^-]+") or "en"] or LABELS.en

  local parts = {}
  for _, key in ipairs({ "created", "updated", "reviewed" }) do
    local v = value(meta, key)
    if v then table.insert(parts, labels[key] .. " " .. v) end
  end
  if #parts == 0 then return nil end

  local inlines = {}
  for i, text in ipairs(parts) do
    if i > 1 then table.insert(inlines, pandoc.Str(" \u{00B7} ")) end
    table.insert(inlines, pandoc.Str(text))
  end

  local block
  if FORMAT:match("html") then
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
