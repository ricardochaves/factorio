local book = require("book")
script.on_init(function()
  local inv = game.create_inventory(1)
  local st = inv[1]
  local r = st.import_stack(book)
  local lines = {"import_stack result=" .. r .. " is_blueprint_book=" .. tostring(st.is_blueprint_book) .. " label=" .. tostring(st.label)}
  local main = st.get_inventory(defines.inventory.item_main)
  lines[#lines+1] = "sub items: " .. #main
  local total, setup = 0, 0
  for i = 1, #main do
    local sub = main[i]
    if sub.valid_for_read then
      local si = sub.get_inventory(defines.inventory.item_main)
      local n, ok = 0, 0
      for j = 1, #si do if si[j].valid_for_read then n = n + 1; if si[j].is_blueprint_setup() then ok = ok + 1 end end end
      total = total + n; setup = setup + ok
      lines[#lines+1] = string.format("  sub-book %-3s blueprints=%d first=%s last=%s", tostring(sub.label), n, tostring(si[1].label), tostring(si[n].label))
    end
  end
  lines[#lines+1] = "total blueprints=" .. total .. " with entities=" .. setup
  helpers.write_file("bookimport.txt", table.concat(lines, "\n") .. "\n", false)
end)
