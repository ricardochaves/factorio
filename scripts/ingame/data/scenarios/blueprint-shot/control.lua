-- Photos of any blueprint or blueprint book, taken with the game's own renderer (needs the GUI build, not headless). Each
-- blueprint is built on its own grass field, powered and photographed whole, framed by its own extent; a book gives one photo
-- per blueprint, the first MAX_SHOTS of them. The power source (a big pole and an energy interface) sits outside the frame;
-- only its copper wire enters it. Nothing is fed to the machines, so the photo shows the build, not a running factory.
-- Test data: scripts/run_blueprint_shot.sh writes bp.lua. Photos go to script-output/blueprint_<n>.png and the report to
-- script-output/blueprint_shot_done.txt, which is written even when a step fails. Its first line is
-- `shots=<photos taken> total=<blueprints in the string>`; then one line per blueprint (`<built> of <all> entities built`, the
-- names of those not built, the pole groups the power source does not reach) and one per photo (size in tiles with its margin,
-- zoom), or the error text.
local BP = require("bp")

local MAX_SHOTS = 4
local SHOT_DELAY = 120                  -- ticks between the build and the photo
local LONG_SIDE = 2048                  -- px of the photo's longer side (the API's advice with anti-aliasing); a small build zooms in, at most MAX_ZOOM
local MAX_ZOOM, MIN_ZOOM = 2, 0.05
local MARGIN = 3                        -- tiles of grass around the build
local TALL = 1                          -- one more above it: a pole or a tower is drawn above its collision box
local SOURCE_GAP = 5                    -- tiles between the build and the power source, east of it: outside the frame and the pole's shadow, close enough for a pole's wire
local GRASS = {"grass-1", "grass-2", "grass-3", "grass-4"}

-- The blueprints inside `stack`: itself, or every one in a book, nested books included.
local function collect(stack, found)
  if stack.is_blueprint_book then
    local inv = stack.get_inventory(defines.inventory.item_main)
    for i = 1, #inv do
      if inv[i].valid_for_read then collect(inv[i], found) end
    end
  elseif stack.is_blueprint and stack.is_blueprint_setup() then
    found.total = found.total + 1
    if #found < MAX_SHOTS then found[#found + 1] = stack end
  end
end

-- How far from its center the blueprint can reach, in tiles, plus its snapping grid, which can shift where it lands.
local function reach(stack)
  local r = 0
  for _, e in pairs(stack.get_blueprint_entities() or {}) do
    r = math.max(r, math.abs(e.position.x), math.abs(e.position.y))
  end
  for _, t in pairs(stack.get_blueprint_tiles() or {}) do
    r = math.max(r, math.abs(t.position.x), math.abs(t.position.y))
  end
  local grid = stack.blueprint_snap_to_grid
  return r + (grid and math.max(grid.x, grid.y) or 0)
end

local function grass_surface(name, radius)
  local s = game.create_surface(name, {
    seed = 20260920,
    default_enable_all_autoplace_controls = false,
    autoplace_controls = {},
    autoplace_settings = {
      tile = {treat_missing_as_default = false,
              settings = {["grass-1"] = {}, ["grass-2"] = {}, ["grass-3"] = {}, ["grass-4"] = {}}},
      entity = {treat_missing_as_default = false, settings = {}},
      decorative = {treat_missing_as_default = true, settings = {}},
    },
    starting_area = "none",
    peaceful_mode = true,
    no_enemies_mode = true,
  })
  s.always_day = true
  s.request_to_generate_chunks({0, 0}, math.ceil((radius + SOURCE_GAP + 16) / 32) + 1)
  s.force_generate_chunk_requests()
  return s
end

-- Gives every machine that asked for modules or fuel what the blueprint requested.
local function fill_requests(s)
  for _, proxy in pairs(s.find_entities_filtered{name = "item-request-proxy"}) do
    local target, plan = proxy.proxy_target, proxy.insert_plan
    if target and target.valid and plan then
      for _, p in pairs(plan) do
        for _, loc in pairs(p.items.in_inventory or {}) do
          local inv = target.get_inventory(loc.inventory)
          if inv then inv.insert{name = p.id.name, count = loc.count or 1} end
        end
      end
    end
    if proxy.valid then proxy.destroy() end
  end
end

local function revive_all(ghosts)
  for _, g in pairs(ghosts) do
    if g.valid then g.revive() end
  end
end

-- Builds the blueprint on a new surface.
local function build(stack, n)
  local s = grass_surface("blueprint-" .. n, reach(stack))
  revive_all(stack.build_blueprint{surface = s, force = "player", build_mode = defines.build_mode.forced, position = {0, 0}})
  revive_all(s.find_entities_filtered{name = {"entity-ghost", "tile-ghost"}})   -- ghosts that waited for a neighbour
  fill_requests(s)
  return s
end

-- How many of the blueprint's entities stand on the surface, out of how many, and " (not built: name x count, ...)". The game
-- builds what it can and skips the rest without a ghost (a pumpjack needs oil under it, an offshore pump water).
local function built_of(stack, s)
  local wanted, all = {}, 0
  for _, e in pairs(stack.get_blueprint_entities() or {}) do
    wanted[e.name] = (wanted[e.name] or 0) + 1
    all = all + 1
  end
  local built, standing = {}, 0
  for _, e in pairs(s.find_entities_filtered{force = "player"}) do
    if e.name ~= "entity-ghost" and e.name ~= "tile-ghost" then
      built[e.name] = (built[e.name] or 0) + 1
      standing = standing + 1
    end
  end
  local missing = {}
  for name, count in pairs(wanted) do
    if count > (built[name] or 0) then missing[#missing + 1] = string.format("%s x%d", name, count - (built[name] or 0)) end
  end
  table.sort(missing)
  return standing, all, #missing > 0 and (" (not built: " .. table.concat(missing, ", ") .. ")") or ""
end

-- The box that holds every entity and every tile that is not grass, or nil for an empty build.
local function extent(s)
  local x0, y0, x1, y1 = math.huge, math.huge, -math.huge, -math.huge
  local function add(l, t, r, b)
    x0, y0, x1, y1 = math.min(x0, l), math.min(y0, t), math.max(x1, r), math.max(y1, b)
  end
  for _, e in pairs(s.find_entities_filtered{force = "player"}) do
    local b = e.bounding_box
    add(b.left_top.x, b.left_top.y, b.right_bottom.x, b.right_bottom.y)
  end
  for _, t in pairs(s.find_tiles_filtered{name = GRASS, invert = true}) do
    add(t.position.x, t.position.y, t.position.x + 1, t.position.y + 1)
  end
  if x0 == math.huge then return nil end
  return {x0 = x0, y0 = y0, x1 = x1, y1 = y1}
end

-- Powers the build from outside the frame; returns "N pole groups without power" and where the first of them are.
local function power(s, box)
  local y = (box.y0 + box.y1) / 2
  local pole = s.create_entity{name = "big-electric-pole", position = {box.x1 + SOURCE_GAP, y}, force = "player"}
  local eei = s.create_entity{name = "electric-energy-interface", position = {box.x1 + SOURCE_GAP + 2, y}, force = "player"}
  if not (pole and eei) then return "the power source could not be placed" end
  eei.electric_buffer_size = 1e12
  eei.power_production = 1e9
  eei.energy = 1e12
  local cut_off, n, poles, where = {}, 0, 0, {}
  for _, p in pairs(s.find_entities_filtered{type = "electric-pole", force = "player"}) do
    if p.unit_number ~= pole.unit_number then
      poles = poles + 1
      local group = p.electric_network_id or ("pole " .. p.unit_number)
      if p.electric_network_id ~= pole.electric_network_id and not cut_off[group] then
        cut_off[group] = true
        n = n + 1
        if n <= 3 then where[n] = string.format("(%.0f, %.0f)", p.position.x, p.position.y) end
      end
    end
  end
  if poles == 0 then return "no poles in the build" end
  return string.format("%d pole groups without power%s", n, n > 0 and (", first at " .. table.concat(where, " ")) or "")
end

local function photo(s, box, n)
  local x0, y0, x1, y1 = box.x0 - MARGIN, box.y0 - MARGIN - TALL, box.x1 + MARGIN, box.y1 + MARGIN
  local w, h = x1 - x0, y1 - y0
  local zoom = math.max(MIN_ZOOM, math.min(MAX_ZOOM, LONG_SIDE / (32 * math.max(w, h))))
  game.take_screenshot{surface = s, position = {(x0 + x1) / 2, (y0 + y1) / 2},
                       resolution = {math.ceil(w * 32 * zoom), math.ceil(h * 32 * zoom)}, zoom = zoom,
                       path = "blueprint_" .. n .. ".png", show_entity_info = false, daytime = 0, water_tick = 0,
                       force_render = true, anti_alias = true, quality = 100}
  return string.format("blueprint_%d.png: %d x %d tiles, zoom %.3f", n, math.ceil(w), math.ceil(h), zoom)
end

-- Imports the string, builds and powers every blueprint it holds; fills storage.shots, storage.log and storage.total.
local function prepare(stack)
  local imported = stack.import_stack(BP)   -- 0 ok, -1 ok with errors, 1 failed
  if imported > 0 then
    storage.log[#storage.log + 1] = "the string could not be imported"
    return
  end
  if imported < 0 then storage.log[#storage.log + 1] = "the import reported errors" end
  local found = {total = 0}
  collect(stack, found)
  storage.total = found.total
  if found.total == 0 then storage.log[#storage.log + 1] = "the string holds no blueprint with entities" end
  for n, bp in ipairs(found) do
    local s = build(bp, n)
    local box = extent(s)
    if box then
      local standing, all, missing = built_of(bp, s)
      local powered = power(s, box)
      storage.shots[#storage.shots + 1] = {surface = s, box = box, n = n}
      storage.log[#storage.log + 1] = string.format("blueprint %d: %d of %d entities built%s, %s", n, standing, all, missing, powered)
    else
      storage.log[#storage.log + 1] = string.format("blueprint %d built nothing", n)
    end
  end
end

script.on_init(function()
  game.forces.player.research_all_technologies()
  storage.shots, storage.log, storage.total, storage.taken = {}, {}, 0, 0
  local inv = game.create_inventory(1)
  local ok, err = pcall(prepare, inv[1])
  if not ok then storage.log[#storage.log + 1] = "error while building: " .. tostring(err) end
  inv.destroy()
  storage.t0 = game.tick
end)

script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done or e.tick - storage.t0 < SHOT_DELAY then return end
  for _, sh in ipairs(storage.shots) do
    local ok, result = pcall(photo, sh.surface, sh.box, sh.n)
    if ok then storage.taken = storage.taken + 1 end
    storage.log[#storage.log + 1] = ok and result or string.format("blueprint %d could not be photographed: %s", sh.n, tostring(result))
  end
  helpers.write_file("blueprint_shot_done.txt",
    string.format("shots=%d total=%d\n%s\n", storage.taken, storage.total, table.concat(storage.log, "\n")), false)
  storage.done = true
end)
