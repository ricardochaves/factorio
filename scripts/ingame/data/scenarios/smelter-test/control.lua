-- Checks the stone brick smelter in the real game (headless): the string imports, every entity and module is where the
-- blueprint puts it, one electric network powers all of it, and a full express belt of stone gives the expected stone
-- bricks per second. It is measured twice in the same run, on two surfaces: with every technology researched and with
-- none (the inserter capacity bonuses are research), so the README can say what the design needs.
-- The stone comes from an infinity chest and an express loader, the bricks leave through another loader and chest (both
-- STUB tiles from the design), and the power comes from a second substation and an energy interface 16 to 19 tiles
-- south of the design's own substation.
-- Test data: scripts/export_smelter.py writes strings.lua (the blueprint string plus the counts to expect).
local D = require("strings")
local STUB = 8                    -- belt tiles between the design and the loaders
local WARM, WINDOW = 3600, 3600   -- ticks: warm-up before measuring, then the measuring window (60 s each)
local E0, POWER_TICKS = 1e11, 600 -- joules given to the energy interface for the power reading, and how long it lasts
local BELT = 45                   -- stone per second on one full express belt
local PRODUCTIVITY = 0.2          -- 2 x productivity-module-3 (+10 % each) in every furnace
local S = defines.direction
local WORKING = defines.entity_status.working
local BAD = {}                    -- statuses that mean a machine has no (or too little) power
for _, k in pairs({"no_power", "low_power", "not_plugged_in_electric_network", "disabled_by_control_behavior"}) do
  BAD[defines.entity_status[k]] = k
end
local POWERED = {}                -- kinds of entity that must be on the electric network
for _, k in pairs({"electric-furnace", "beacon", "bulk-inserter", "fast-inserter", "small-lamp", "medium-electric-pole", "substation"}) do
  POWERED[k] = true
end
local REGIMES = {
  {tag = "all-research", force = "player", surface = "lab-all"},
  {tag = "no-research", force = "plain", surface = "lab-none"},
}

local lines, failed, ran = {}, 0, 0
local function check(ok, fmt, ...)
  ran = ran + 1
  if not ok then failed = failed + 1 end
  lines[#lines + 1] = (ok and "OK   " or "FAIL ") .. string.format(fmt, ...)
end
local function note(fmt, ...) lines[#lines + 1] = "     " .. string.format(fmt, ...) end

local STATUS = {}
for k, v in pairs(defines.entity_status) do STATUS[v] = k end

local function fmt_counts(t)
  local r = {}
  for k, v in pairs(t) do r[#r + 1] = k .. "=" .. v end
  table.sort(r)
  return table.concat(r, ", ")
end

local function same_counts(a, b)
  for k, v in pairs(a) do if b[k] ~= v then return false end end
  for k, v in pairs(b) do if a[k] ~= v then return false end end
  return true
end

-- Builds the design and its harness on a fresh lab surface for one regime and checks what is static about it.
local function build(rg, stack)
  local s = game.create_surface(rg.surface)
  s.generate_with_lab_tiles = true
  s.always_day = true
  s.request_to_generate_chunks({0, 0}, 4)
  s.force_generate_chunk_requests()
  local ghosts = stack.build_blueprint{surface = s, force = rg.force, position = {0, 0}, build_mode = defines.build_mode.forced}
  local revived = 0
  for _, g in pairs(ghosts) do if g.valid then local _, e = g.revive(); if e then revived = revived + 1 end end end
  -- The modules ride in item-request proxies: put them in and remove the proxy.
  for _, proxy in pairs(s.find_entities_filtered{name = "item-request-proxy"}) do
    local target, plan = proxy.proxy_target, proxy.insert_plan
    if target and target.valid and plan then
      for _, p in pairs(plan) do
        for _, loc in pairs(p.items.in_inventory or {}) do
          local inv = target.get_inventory(loc.inventory); if inv then inv.insert{name = p.id.name, count = loc.count or 1} end
        end
      end
    end
    if proxy.valid then proxy.destroy() end
  end
  check(#ghosts == D.n_entities and revived == D.n_entities, "[%s] %d ghosts, %d revived, %d expected", rg.tag, #ghosts, revived, D.n_entities)

  local names, mods, design = {}, {}, {}
  for _, e in pairs(s.find_entities_filtered{force = rg.force}) do
    names[e.name] = (names[e.name] or 0) + 1
    design[#design + 1] = e
    local inv = e.get_module_inventory()
    if inv then for _, c in pairs(inv.get_contents()) do mods[c.name] = (mods[c.name] or 0) + c.count end end
  end
  check(same_counts(names, D.entities), "[%s] entities by name match the blueprint (%s)", rg.tag, fmt_counts(names))
  check(same_counts(mods, D.modules), "[%s] modules inserted match the blueprint (%s)", rg.tag, fmt_counts(mods))

  local furn, inb, outu, sub = {}, nil, nil, nil
  for _, e in pairs(design) do
    if e.name == "electric-furnace" then furn[#furn + 1] = e end
    if e.name == "express-transport-belt" and (not inb or e.position.y > inb.position.y) then inb = e end
    if e.name == "express-underground-belt" and (not outu or e.position.y < outu.position.y) then outu = e end
    if e.name == "substation" then sub = e end
  end
  table.sort(furn, function(a, b) return a.position.y < b.position.y end)   -- the last furnace in belt order first
  local ix, iy, ox, oy = inb.position.x, inb.position.y, outu.position.x, outu.position.y
  for k = 1, STUB do s.create_entity{name = "express-transport-belt", position = {ix, iy + k}, direction = S.north, force = rg.force} end
  s.create_entity{name = "express-loader", position = {ix, iy + STUB + 1.5}, direction = S.north, type = "output", force = rg.force}
  local feed = s.create_entity{name = "infinity-chest", position = {ix, iy + STUB + 3}, force = rg.force}
  feed.set_infinity_container_filter(1, {index = 1, name = "stone", count = 100, mode = "exactly"})
  for k = 1, STUB do s.create_entity{name = "express-transport-belt", position = {ox, oy - k}, direction = S.north, force = rg.force} end
  s.create_entity{name = "express-loader", position = {ox, oy - STUB - 1.5}, direction = S.north, type = "input", force = rg.force}
  local drain = s.create_entity{name = "infinity-chest", position = {ox, oy - STUB - 3}, force = rg.force}
  drain.remove_unfiltered_items = true

  local sub2 = s.create_entity{name = "substation", position = {sub.position.x, sub.position.y + 16}, force = rg.force}
  sub.get_wire_connector(defines.wire_connector_id.pole_copper, true).connect_to(sub2.get_wire_connector(defines.wire_connector_id.pole_copper, true))
  local eei = s.create_entity{name = "electric-energy-interface", position = {sub.position.x, sub.position.y + 19}, force = rg.force}
  eei.electric_buffer_size = 1e12; eei.power_production = 1e9; eei.energy = 1e12

  -- Every powered entity, lamps and poles included, must be on the one network that the power source is on.
  local ids, n_ids, outside = {}, 0, 0
  for _, e in pairs(design) do
    if POWERED[e.name] then
      local id = e.electric_network_id
      if not id then outside = outside + 1
      elseif not ids[id] then ids[id] = true; n_ids = n_ids + 1 end
    end
  end
  check(outside == 0 and n_ids == 1 and ids[eei.electric_network_id],
    "[%s] one electric network joins every powered entity and the power source (%d networks, %d entities outside)", rg.tag, n_ids, outside)
  return {tag = rg.tag, force = rg.force, surface = rg.surface, furn = furn, design = design, duty = {}, eei = eei}
end

-- Electric power drawn: after the measuring window the energy interface stops producing and gives the network only the
-- energy in its buffer; what is missing from the buffer POWER_TICKS later is what the design drew.
local function start_power_reading(r)
  r.eei.power_production = 0
  r.eei.energy = E0
end

local function power(r)
  return (E0 - r.eei.energy) / (POWER_TICKS / 60)   -- watts
end

local function measure(r)
  local s = game.surfaces[r.surface]
  local stats = game.forces[r.force].get_item_production_statistics(s)
  local secs = WINDOW / 60
  local stone = (stats.get_output_count("stone") - r.s0) / secs
  local bricks = (stats.get_input_count("stone-brick") - r.b0) / secs
  local tally, bad = {}, 0
  -- Lamps are left out of the status tally: they only draw power in the dark and the surface is always day (their
  -- network is checked in build).
  for _, e in pairs(r.design) do
    if e.valid and e.name ~= "small-lamp" then
      local st = e.status
      if st then
        local k = e.name .. ":" .. STATUS[st]
        tally[k] = (tally[k] or 0) + 1
        if BAD[st] then bad = bad + 1 end
      end
    end
  end
  note("[%s] stone consumed %.2f/s, stone bricks produced %.2f/s over %d s (a full express belt is %d/s)", r.tag, stone, bricks, secs, BELT)
  local duty = {}
  for i, f in ipairs(r.furn) do duty[i] = 100 * (r.duty[f.unit_number] or 0) / WINDOW end
  local d = {}
  for i, v in ipairs(duty) do d[i] = string.format("%.1f%%", v) end
  note("[%s] share of the window each furnace worked, last in belt order first: %s", r.tag, table.concat(d, ", "))
  note("[%s] furnace crafting speeds: %.3f (last) %.3f (second) %.3f (middle), productivity bonus %.3f", r.tag,
    r.furn[1].crafting_speed, r.furn[2].crafting_speed, r.furn[4].crafting_speed, r.furn[1].productivity_bonus)
  note("[%s] statuses at the end: %s", r.tag, fmt_counts(tally))
  check(bad == 0, "[%s] no machine reports missing or low power (%d)", r.tag, bad)
  return stone, bricks, duty
end

script.on_init(function()
  game.speed = 16
  game.forces.player.research_all_technologies()
  game.create_force("plain")   -- a force with no technology researched
  local inv = game.create_inventory(1)
  local stack = inv[1]
  check(stack.import_stack(D.bp) == 0, "the blueprint string imports")
  check(stack.label == D.label, "label in game is %q", tostring(stack.label))
  note("description in game: %s", (stack.blueprint_description:gsub("\n", "\\n")))
  storage.r = {}
  for i, rg in ipairs(REGIMES) do storage.r[i] = build(rg, stack) end
  inv.destroy()
  storage.t0 = game.tick
end)

script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done then return end
  local rel = e.tick - storage.t0
  if rel == WARM then
    for _, r in ipairs(storage.r) do
      local stats = game.forces[r.force].get_item_production_statistics(game.surfaces[r.surface])
      r.b0, r.s0 = stats.get_input_count("stone-brick"), stats.get_output_count("stone")
    end
  elseif rel > WARM and rel <= WARM + WINDOW then
    for _, r in ipairs(storage.r) do
      for _, f in pairs(r.furn) do r.duty[f.unit_number] = (r.duty[f.unit_number] or 0) + (f.status == WORKING and 1 or 0) end
    end
  end
  if rel == WARM + WINDOW + POWER_TICKS then
    for _, r in ipairs(storage.r) do
      local watts = power(r)
      note("[%s] electric power drawn: %.2f MW", r.tag, watts / 1e6)
      check(watts > 1e6, "[%s] the design draws power from the energy interface", r.tag)
    end
    note("with no technology researched the design makes %.2f bricks/s, with all of them %.2f bricks/s", storage.none_bricks, storage.all_bricks)
    lines[#lines + 1] = string.format("checked failed=%d ran=%d", failed, ran)
    helpers.write_file("smelter_test.txt", table.concat(lines, "\n") .. "\n", false)
    helpers.write_file("smelter_done.txt", "done\n", false)
    storage.done = true
    return
  end
  if rel ~= WARM + WINDOW then return end
  local all_bricks, none_bricks
  for _, r in ipairs(storage.r) do
    local stone, bricks, duty = measure(r)
    if r.tag == "all-research" then   -- only this regime asserts the throughput; the other one is informational
      all_bricks = bricks
      check(stone >= 0.98 * BELT and stone <= 1.01 * BELT, "[%s] the design takes a full express belt of stone: %.2f/s of %d/s", r.tag, stone, BELT)
      local expect = BELT / 2 * (1 + PRODUCTIVITY)
      check(bricks >= 0.98 * expect and bricks <= 1.01 * expect, "[%s] stone bricks match %d / 2 x %.1f = %.1f/s: %.2f/s",
        r.tag, BELT, 1 + PRODUCTIVITY, expect, bricks)
      local least = 100
      for _, v in ipairs(duty) do least = math.min(least, v) end
      check(least >= 25, "[%s] every furnace works: the least busy one worked %.1f%% of the window", r.tag, least)
    else
      none_bricks = bricks
    end
  end
  storage.all_bricks, storage.none_bricks = all_bricks, none_bricks
  for _, r in ipairs(storage.r) do start_power_reading(r) end
end)
