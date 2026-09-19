-- Photos of the belt balancers for the site, taken with the game's own renderer (needs the GUI build, not headless).
-- Builds the same balancer from each book side by side (shots.lua, written by scripts/export_shots.py), feeds every
-- input and drains every output with loaders and infinity chests placed STUB tiles away from the balancer, so only the
-- balancer and straight belt stubs of its own tier are inside the frames.
local SHOTS = require("shots")
local STUB = 8           -- straight belt tiles between the balancer and the hidden loaders
local GAP = 4            -- tiles between neighbouring balancers
local WARM = 3600        -- ticks before the photos: every belt full and compressed
local S = defines.direction

local function box(s, area)
  local minx, miny, maxx, maxy = 1e9, 1e9, -1e9, -1e9
  for _, e in pairs(s.find_entities_filtered{area = area, type = {"transport-belt", "underground-belt", "splitter"}}) do
    local b = e.bounding_box
    minx = math.min(minx, math.floor(b.left_top.x + 0.01)); miny = math.min(miny, math.floor(b.left_top.y + 0.01))
    maxx = math.max(maxx, math.floor(b.right_bottom.x - 0.01)); maxy = math.max(maxy, math.floor(b.right_bottom.y - 0.01))
  end
  return {minx = minx, miny = miny, maxx = maxx, maxy = maxy}   -- tile indices of the outermost columns / rows
end

local function feed(s, t, b)
  local made = {}
  local function add(e) if e then made[#made + 1] = e end return e end
  for _, c in pairs(t.ins) do
    local x = b.minx + c + 0.5
    for k = 1, STUB do add(s.create_entity{name = t.belt, position = {x, b.maxy + k + 0.5}, direction = S.north, force = "player"}) end
    add(s.create_entity{name = t.loader, position = {x, b.maxy + STUB + 2}, direction = S.north, type = "output", force = "player"})
    local ch = add(s.create_entity{name = "infinity-chest", position = {x, b.maxy + STUB + 3.5}, force = "player"})
    ch.set_infinity_container_filter(1, {index = 1, name = t.item, count = 100, mode = "exactly"})
  end
  for _, c in pairs(t.outs) do
    local x = b.minx + c + 0.5
    for k = 1, STUB do add(s.create_entity{name = t.belt, position = {x, b.miny - k + 0.5}, direction = S.north, force = "player"}) end
    add(s.create_entity{name = t.loader, position = {x, b.miny - STUB - 1}, direction = S.north, type = "input", force = "player"})
    local ch = add(s.create_entity{name = "infinity-chest", position = {x, b.miny - STUB - 2.5}, force = "player"})
    ch.remove_unfiltered_items = true
  end
  return #made
end

local function shot(s, name, x0, y0, x1, y1, zoom)
  -- x0..x1, y0..y1 are tile edges; 32 px per tile at zoom 1
  game.take_screenshot{surface = s, position = {(x0 + x1) / 2, (y0 + y1) / 2},
                       resolution = {math.floor((x1 - x0) * 32 * zoom), math.floor((y1 - y0) * 32 * zoom)}, zoom = zoom,
                       path = name, show_entity_info = false, daytime = 0, water_tick = 0, force_render = true,
                       anti_alias = true, quality = 100}
end

script.on_init(function()
  game.speed = 16
  local s = game.create_surface("lab")
  s.generate_with_lab_tiles = true
  s.always_day = true
  s.request_to_generate_chunks({0, 0}, 4)
  s.force_generate_chunk_requests()
  local inv = game.create_inventory(1)
  local stack = inv[1]
  storage.boxes, storage.log = {}, ""
  local step = 0
  for _, t in pairs(SHOTS) do step = math.max(step, t.w) end
  step = step + GAP
  for i, t in pairs(SHOTS) do
    local cx = (i - (#SHOTS + 1) / 2) * step
    stack.clear()
    assert(stack.import_stack(t.bp) == 0, t.tier .. ": import failed")
    local ghosts = stack.build_blueprint{surface = s, force = "player", position = {cx, 0}, build_mode = defines.build_mode.forced}
    local revived = 0
    for _, g in pairs(ghosts) do
      if g.valid then local _, ent = g.revive(); if ent then revived = revived + 1 end end
    end
    local b = box(s, {{cx - step / 2, -40}, {cx + step / 2, 40}})
    local made = feed(s, t, b)
    storage.boxes[i] = b
    storage.log = storage.log .. string.format("%s %s: %d ghosts, %d revived, box x %d..%d y %d..%d, %d harness entities\n",
      t.tier, t.label, #ghosts, revived, b.minx, b.maxx, b.miny, b.maxy, made)
  end
  inv.destroy()
  storage.t0 = game.tick
end)

script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done then return end
  if e.tick - storage.t0 == WARM - 60 then game.speed = 1 end   -- render the photos at normal speed
  if e.tick - storage.t0 ~= WARM then return end
  local s = game.surfaces["lab"]
  -- compression check: items on every output stub tile (a full straight belt tile holds 8)
  for i, t in pairs(SHOTS) do
    local b, lo, hi = storage.boxes[i], 1e9, -1
    for _, c in pairs(t.outs) do
      for k = 1, 5 do
        local belt = s.find_entity(t.belt, {b.minx + c + 0.5, b.miny - k + 0.5})
        local n = belt and (belt.get_transport_line(1).get_item_count() + belt.get_transport_line(2).get_item_count()) or -1
        lo, hi = math.min(lo, n), math.max(hi, n)
      end
    end
    storage.log = storage.log .. string.format("%s output stubs: %d..%d items per tile\n", t.tier, lo, hi)
  end
  local first, last = storage.boxes[1], storage.boxes[#SHOTS]
  local y0 = math.min(first.miny, last.miny)
  local y1 = math.max(first.maxy, last.maxy) + 1
  shot(s, "balancer_overview.png", first.minx - 3, y0 - 5, last.maxx + 1 + 3, y1 + 6, 1.5)
  for i, t in pairs(SHOTS) do
    local b = storage.boxes[i]
    shot(s, "balancer_" .. t.tier .. ".png", b.minx - 2, b.miny - 3, b.maxx + 1 + 2, b.maxy + 1 + 3, 2)
  end
  storage.shot_tick = e.tick
end)

script.on_nth_tick(60, function(e)
  if storage.shot_tick and not storage.done and e.tick >= storage.shot_tick + 120 then
    helpers.write_file("balancer_shot_done.txt", storage.log, false)
    storage.done = true
  end
end)
