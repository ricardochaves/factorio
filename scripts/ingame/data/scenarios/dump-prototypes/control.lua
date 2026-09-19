-- Dumps the names of every prototype a blueprint can reference, plus entity tile sizes and the items that place
-- each entity/tile, to script-output/vanilla-prototypes.json. Run through scripts/catalog/dump_prototypes.sh
-- (base game only). The catalog validator uses the result to reject anything that is not vanilla.
local function sorted_names(t)
  local out = {}
  for name in pairs(t) do out[#out + 1] = name end
  table.sort(out)
  return out
end

local function placed_by(p)
  local ok, items = pcall(function() return p.items_to_place_this end)
  if not ok or not items then return nil end
  local list = {}
  for _, it in pairs(items) do list[#list + 1] = { name = it.name, count = it.count } end
  if #list == 0 then return nil end
  return list
end

local function dump()
  local result = { active_mods = script.active_mods, entity = {}, tile_items = {} }
  for name, p in pairs(prototypes.entity) do
    local e = { type = p.type, w = p.tile_width, h = p.tile_height }
    e.placed_by = placed_by(p)
    result.entity[name] = e
  end
  for name, p in pairs(prototypes.tile) do
    local items = placed_by(p)
    if items then result.tile_items[name] = items end
  end
  result.item = sorted_names(prototypes.item)
  result.recipe = sorted_names(prototypes.recipe)
  result.fluid = sorted_names(prototypes.fluid)
  result.tile = sorted_names(prototypes.tile)
  result.virtual_signal = sorted_names(prototypes.virtual_signal)
  result.quality = sorted_names(prototypes.quality)
  for _, key in pairs({ "space_location", "asteroid_chunk" }) do
    local ok, t = pcall(function() return prototypes[key] end)
    if ok and t then result[key] = sorted_names(t) end
  end
  helpers.write_file("vanilla-prototypes.json", helpers.table_to_json(result), false)
  helpers.write_file("dump_done.txt", "ok\n", false)
end

script.on_init(dump)
