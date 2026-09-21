-- Photo and measurements of the iron/copper smelter for the site (needs the GUI build, not headless; run it with
-- scripts/run_iron_copper_shot.sh, which writes bp.lua from blueprints/iron-copper-smelter/iron-copper-smelter.txt).
-- Builds the blueprint on grass, fulfils its module requests, powers it through an energy interface, feeds iron ore with an
-- express loader and an infinity chest and drains the plates the same way (both 6 belts away from the blueprint, outside
-- the frame). For each non-stack inserter capacity bonus (+0, +1, +2, which the research gives at none, at inserter
-- capacity bonus 2 and at inserter capacity bonus 7) it warms up, then measures ore consumed, plates produced and electric
-- power over a window; when all the furnaces are working it takes the photo.
-- Output: script-output/iron_copper_shot_done.txt (the measurements; a line starting with FAIL: means that a check did not hold
-- and the run must not be trusted) and script-output/iron_copper_overview.png.
local BP = require("bp")
local STUB, WARM, MEAS = 6, 18000, 3600
local S = defines.direction
local ORE, PLATE = "iron-ore", "iron-plate"
-- a window is steady when the plates and the ore waiting in the furnaces moved by less than this share of what went through
local DRIFT = 0.02

local STATUS = {}
for name, value in pairs(defines.entity_status) do STATUS[value] = name end

local function grass_surface(name)
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
  s.request_to_generate_chunks({0, 0}, 5)
  s.force_generate_chunk_requests()
  return s
end

local function belt_count(b)
  return b.get_transport_line(1).get_item_count() + b.get_transport_line(2).get_item_count()
end

local function fail(log, fmt, ...)
  log[#log + 1] = "FAIL: " .. string.format(fmt, ...)
end

script.on_init(function()
  game.speed = 16
  game.forces.player.inserter_stack_size_bonus = 0
  local s = grass_surface("shot")
  local inv = game.create_inventory(1)
  local stack = inv[1]
  assert(stack.import_stack(BP) == 0, "import failed")
  local ghosts = stack.build_blueprint{surface = s, force = "player", position = {0, 0}, build_mode = defines.build_mode.forced}
  local revived = 0
  for _, g in pairs(ghosts) do
    if g.valid then local _, ent = g.revive(); if ent then revived = revived + 1 end end
  end
  inv.destroy()
  -- reviving ghosts by script leaves the blueprint's module requests as item-request-proxies: fulfil them here
  local placed = 0
  for _, p in pairs(s.find_entities_filtered{type = "item-request-proxy"}) do
    local target = p.proxy_target
    for _, plan in pairs(p.insert_plan) do
      for _, pos in pairs(plan.items.in_inventory or {}) do
        local count = pos.count or 1
        target.get_inventory(pos.inventory)[pos.stack + 1].set_stack{name = plan.id.name, count = count}
        placed = placed + count
      end
    end
  end
  local nb, nf = 0, 0
  for _, b in pairs(s.find_entities_filtered{name = "beacon"}) do nb = nb + b.get_module_inventory().get_item_count("speed-module-3") end
  for _, f in pairs(s.find_entities_filtered{name = "electric-furnace"}) do nf = nf + f.get_module_inventory().get_item_count("productivity-module-3") end
  local left = s.count_entities_filtered{name = {"entity-ghost", "tile-ghost"}}
  local log = {
    string.format("modules: %d placed from requests; %d speed-module-3 in beacons, %d productivity-module-3 in furnaces", placed, nb, nf),
    string.format("%d ghosts, %d revived, %d ghosts left", #ghosts, revived, left),
  }
  if left > 0 or revived < #ghosts then fail(log, "%d of %d ghosts revived, %d ghosts left", revived, #ghosts, left) end
  if placed ~= nb + nf then fail(log, "%d modules requested but %d found in the machines", placed, nb + nf) end

  local minx, miny, maxx, maxy = 1e9, 1e9, -1e9, -1e9
  local belts_in, belts_out, pole
  for _, e in pairs(s.find_entities_filtered{force = "player"}) do
    local b = e.bounding_box
    minx = math.min(minx, b.left_top.x); miny = math.min(miny, b.left_top.y)
    maxx = math.max(maxx, b.right_bottom.x); maxy = math.max(maxy, b.right_bottom.y)
    if e.name == "express-transport-belt" then
      if not belts_in or e.position.y > belts_in.position.y then belts_in = e end
      if not belts_out or e.position.y < belts_out.position.y then belts_out = e end
    elseif e.name == "medium-electric-pole" then
      if not pole or e.position.y > pole.position.y or (e.position.y == pole.position.y and e.position.x < pole.position.x) then pole = e end
    end
  end
  assert(belts_in and belts_out and pole, "the blueprint needs express belts and a medium electric pole")
  log[#log + 1] = string.format("box x %.1f..%.1f y %.1f..%.1f; in belt (%.1f,%.1f) out belt (%.1f,%.1f) pole (%.1f,%.1f)",
    minx, maxx, miny, maxy, belts_in.position.x, belts_in.position.y, belts_out.position.x, belts_out.position.y,
    pole.position.x, pole.position.y)

  -- ore in, plates out (express loaders + infinity chests, outside the frame)
  local ix, iy = belts_in.position.x, belts_in.position.y
  for k = 1, STUB do s.create_entity{name = "express-transport-belt", position = {ix, iy + k}, direction = S.north, force = "player"} end
  s.create_entity{name = "express-loader", position = {ix, iy + STUB + 1.5}, direction = S.north, type = "output", force = "player"}
  local ch = s.create_entity{name = "infinity-chest", position = {ix, iy + STUB + 3}, force = "player"}
  ch.set_infinity_container_filter(1, {index = 1, name = ORE, count = 100, mode = "exactly"})
  local ox, oy = belts_out.position.x, belts_out.position.y
  for k = 1, STUB do s.create_entity{name = "express-transport-belt", position = {ox, oy - k}, direction = S.north, force = "player"} end
  s.create_entity{name = "express-loader", position = {ox, oy - STUB - 1.5}, direction = S.north, type = "input", force = "player"}
  local dr = s.create_entity{name = "infinity-chest", position = {ox, oy - STUB - 3}, force = "player"}
  dr.remove_unfiltered_items = true

  -- power: a big pole 8.5 tiles south of the southern medium pole (inside the wire reach of 9), an energy interface next to
  -- it (both outside the frame)
  local bpole = s.create_entity{name = "big-electric-pole", position = {pole.position.x + 0.5, pole.position.y + 8.5}, force = "player"}
  local eei = s.create_entity{name = "electric-energy-interface", position = {pole.position.x - 1.5, pole.position.y + 8.5}, force = "player"}
  eei.electric_buffer_size = 1e12
  eei.power_production = 1e9
  eei.energy = 1e12
  local conn = bpole.get_wire_connector(defines.wire_connector_id.pole_copper, true).connection_count
  log[#log + 1] = string.format("big pole at (%.1f,%.1f), %d copper connections", bpole.position.x, bpole.position.y, conn)
  if conn == 0 then fail(log, "the big pole is not wired to the blueprint's poles") end
  storage.h = {minx = minx, miny = miny, maxx = maxx, maxy = maxy, ix = ix, iy = iy, ox = ox, oy = oy, eei = eei}
  storage.log, storage.t0 = log, game.tick
end)

-- Phases: non-stack inserter capacity bonus +0, +1 and +2, given by no research, by inserter capacity bonus 2 and by inserter
-- capacity bonus 7. Every phase warms up for WARM ticks, long enough for the furnaces' output slots to reach their steady
-- state, and is then measured over MEAS ticks.
local PHASES = {}
for i, p in ipairs({{bonus = 0, research = "none"}, {bonus = 1, research = "inserter capacity bonus 2"},
                    {bonus = 2, research = "inserter capacity bonus 7"}}) do
  local set = (i - 1) * (WARM + MEAS)
  PHASES[i] = {bonus = p.bonus, research = p.research, set = set, from = set + WARM, to = set + WARM + MEAS}
end
local END = PHASES[#PHASES].to

-- plates waiting in the furnaces' output slots and ore in their input slots: steady state means these stop moving
local function buffers(s)
  local plates, ore = 0, 0
  for _, f in pairs(s.find_entities_filtered{name = "electric-furnace"}) do
    plates = plates + f.get_output_inventory().get_item_count(PLATE)
    ore = ore + f.get_inventory(defines.inventory.furnace_source).get_item_count(ORE)
  end
  return plates, ore
end

local function working_furnaces(s)
  local working, total = 0, 0
  for _, f in pairs(s.find_entities_filtered{name = "electric-furnace"}) do
    total = total + 1
    if f.status == defines.entity_status.working then working = working + 1 end
  end
  return working, total
end

local function measure_start(s, h)
  local st = game.forces.player.get_item_production_statistics(s)
  local bp, bo = buffers(s)
  storage.m0 = {ore = st.get_output_count(ORE), plate = st.get_input_count(PLATE), bplates = bp, bore = bo}
  h.eei.power_production = 0
  h.eei.energy = 1e12
end

local function measure_end(s, h, log, p)
  local st = game.forces.player.get_item_production_statistics(s)
  local secs = MEAS / 60
  local ore = st.get_output_count(ORE) - storage.m0.ore
  local plate = st.get_input_count(PLATE) - storage.m0.plate
  local bp, bo = buffers(s)
  local counts = {}
  for _, f in pairs(s.find_entities_filtered{name = "electric-furnace"}) do
    local k = STATUS[f.status] or tostring(f.status)
    counts[k] = (counts[k] or 0) + 1
  end
  local names = {}
  for k in pairs(counts) do names[#names + 1] = k end
  table.sort(names)
  local cs = {}
  for _, k in ipairs(names) do cs[#cs + 1] = k .. "=" .. counts[k] end
  local label = string.format("inserter stack bonus +%d (research: %s)", p.bonus, p.research)
  log[#log + 1] = string.format("%s, window %d s: %s consumed %d (%.2f/s), %s produced %d (%.2f/s); power %.3f MW; furnaces at the end: %s",
    label, secs, ORE, ore, ore / secs, PLATE, plate, plate / secs, (1e12 - h.eei.energy) / secs / 1e6, table.concat(cs, " "))
  log[#log + 1] = string.format("%s buffers: plates in furnace output slots %d -> %d, ore in furnace input slots %d -> %d",
    label, storage.m0.bplates, bp, storage.m0.bore, bo)
  if ore == 0 or plate == 0 then fail(log, "%s: no ore consumed or no plates produced", label) end
  if math.abs(bp - storage.m0.bplates) > DRIFT * plate or math.abs(bo - storage.m0.bore) > DRIFT * ore then
    fail(log, "%s: the furnace buffers moved by more than %.0f%% of the flow, so this is not a steady state", label, DRIFT * 100)
  end
  h.eei.power_production = 1e9
  h.eei.energy = 1e12
end

script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done then return end
  local rel = e.tick - storage.t0
  local s, h, log = game.surfaces["shot"], storage.h, storage.log
  for _, p in ipairs(PHASES) do
    if rel == p.set then game.forces.player.inserter_stack_size_bonus = p.bonus end
    if rel == p.from then
      local nin = belt_count(s.find_entity("express-transport-belt", {h.ix, h.iy + 1}))
      local nout = belt_count(s.find_entity("express-transport-belt", {h.ox, h.oy - 1}))
      log[#log + 1] = string.format("stack bonus +%d at %d ticks: input stub tile holds %d items, output stub tile holds %d items", p.bonus, rel, nin, nout)
      -- a full straight belt tile holds 8 items: the ore line must be full, or the furnaces are not fed at the full belt rate
      if nin < 8 then fail(log, "stack bonus +%d: the ore line is not full (%d items on the last tile)", p.bonus, nin) end
      measure_start(s, h)
    elseif rel == p.to then
      measure_end(s, h, log, p)
    end
  end
  if rel == END - 60 then game.speed = 1 end
  -- the photo waits for a moment when all the furnaces are working (checked every 15 ticks, at most 900 ticks after the last window)
  if rel >= END + 60 and not storage.shot and (rel - END) % 15 == 0 then
    local working, total = working_furnaces(s)
    if working == total or rel >= END + 900 then
      local w, zoom = 22, 1
      local y0, y1 = h.miny - 3, h.maxy + 2
      local hh = math.ceil(y1 - y0)
      local cx, cy = (h.minx + h.maxx) / 2, (y0 + y1) / 2
      game.take_screenshot{surface = s, position = {cx, cy}, resolution = {math.floor(w * 32 * zoom), math.floor(hh * 32 * zoom)},
                           zoom = zoom, path = "iron_copper_overview.png", show_entity_info = false, daytime = 0, water_tick = 0,
                           force_render = true, anti_alias = true, quality = 100}
      storage.shot = rel
      log[#log + 1] = string.format("shot at +%d ticks with %d of %d furnaces working, centered (%.1f,%.1f), %dx%d tiles", rel - END, working, total, cx, cy, w, hh)
      if working < total then fail(log, "the photo was taken with only %d of %d furnaces working", working, total) end
    end
  elseif storage.shot and rel == storage.shot + 120 then
    helpers.write_file("iron_copper_shot_done.txt", table.concat(log, "\n") .. "\n", false)
    storage.done = true
  end
end)
