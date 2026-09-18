--[[
  Colours the inside of ```{.terminal} blocks in the HTML edition, the way a
  real shell does: prompt (user@host), working directory, the command the
  reader typed, and the program's output each get their own colour. Styling
  lives in _shared/terminal.html.

  A line that looks like a prompt

      user@localhost:~$ pwd
      root@server:/data# ls

  is split into its parts; every other line is treated as output. Other output
  formats (Typst/PDF) are left alone, so the block stays a plain code block
  there.
]]

local function esc(s)
  s = s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;")
  return s
end

local function span(class, text)
  return '<span class="' .. class .. '">' .. esc(text) .. "</span>"
end

local function render(line)
  local host, path, sym, cmd =
    line:match("^([%w%.%_%-]+@[%w%.%_%-]+):([^%$#]*)([%$#])(.*)$")
  if not host then
    return span("term-out", line)
  end
  local out = span("term-user", host)
    .. span("term-punct", ":")
    .. span("term-path", path)
    .. span("term-punct", sym)
  if cmd ~= "" then
    out = out .. span("term-cmd", cmd)
  end
  return out
end

function CodeBlock(el)
  if not quarto.doc.is_format("html") then return nil end
  if not el.classes:includes("terminal") then return nil end

  local lines = {}
  for line in (el.text .. "\n"):gmatch("(.-)\n") do
    lines[#lines + 1] = render(line)
  end
  return pandoc.RawBlock(
    "html",
    '<pre class="terminal"><code>' .. table.concat(lines, "\n") .. "</code></pre>"
  )
end
