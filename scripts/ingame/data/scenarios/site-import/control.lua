-- Imports blueprint strings published on the website (build/site/files/) and checks each one against the numbers
-- the site generator computed. Test data comes from scripts/site_import_test.py (strings.lua, generated).
local CASES = require("strings")

local function count_book(stack)
  local inv = stack.get_inventory(defines.inventory.item_main)
  local books, prints, entities = 0, 0, 0
  for i = 1, #inv do
    local s = inv[i]
    if s.valid_for_read then
      if s.is_blueprint_book then
        local b, p, e = count_book(s)
        books, prints, entities = books + 1 + b, prints + p, entities + e
      elseif s.is_blueprint and s.is_blueprint_setup() then
        prints = prints + 1
        entities = entities + s.get_blueprint_entity_count()
      end
    end
  end
  return books, prints, entities
end

script.on_init(function()
  local inv = game.create_inventory(1)
  local st = inv[1]
  local lines, failed = {}, 0
  for _, c in ipairs(CASES) do
    st.clear()
    local result = st.import_stack(c.str)
    local prints, entities = 0, 0
    if result == 0 and st.is_blueprint_book then
      local _
      _, prints, entities = count_book(st)
    elseif result == 0 and st.is_blueprint and st.is_blueprint_setup() then
      prints, entities = 1, st.get_blueprint_entity_count()
    end
    local ok = result == 0 and prints == c.prints and entities == c.entities
    if not ok then failed = failed + 1 end
    lines[#lines + 1] = string.format("%s %s import=%d blueprints=%d/%d entities=%d/%d",
      ok and "OK  " or "FAIL", c.name, result, prints, c.prints, entities, c.entities)
  end
  lines[#lines + 1] = string.format("checked=%d failed=%d", #CASES, failed)
  helpers.write_file("site_import.txt", table.concat(lines, "\n") .. "\n", false)
  helpers.write_file("site_import_done.txt", "done\n", false)
  inv.destroy()
end)
