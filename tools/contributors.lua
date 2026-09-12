--[[
  PDF fallback for the contributor wall. On the website,
  _shared/contributors.html turns <div class="contributors" data-repo="...">
  into GitHub avatars; the PDF has no JavaScript, so there the noted people are
  listed as "login: note" instead (the GitHub-only contributors are left out).
]]

local function attr(el, name)
  return el.attributes["data-" .. name] or el.attributes[name]
end

function Div(el)
  if quarto.doc.is_format("html") or not el.classes:includes("contributors") then
    return nil
  end
  local items = {}
  for _, child in ipairs(el.content) do
    local login = child.t == "Div" and attr(child, "login")
    if login then
      local line = pandoc.Inlines({ pandoc.Strong(login), pandoc.Str("：") })
      line:extend(pandoc.utils.blocks_to_inlines(child.content))
      table.insert(items, { pandoc.Plain(line) })
    end
  end
  return pandoc.BulletList(items)
end
