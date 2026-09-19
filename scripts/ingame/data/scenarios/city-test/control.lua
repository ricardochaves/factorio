-- Checks the 100 x 100 city block blueprints in the real game (headless): the string imports, every entity and tile is
-- built where the blueprint puts it, the wires are the blueprint's, the block is one electric network that powers its
-- roboports and lamps, and the roboports and chests join into logistic networks, both for one block and for a 2 x 2 city.
-- Test data: scripts/export_city.py writes strings.lua (blueprint strings plus the counts to expect).
local CASES = require("strings")
-- A roboport's energy buffer takes a while to fill after the power is connected, and it reads "low power" until then,
-- so the energy is sampled at SAMPLE_TICKS and the checks that need a full buffer run at POWER_TICK (40 s).
local SAMPLE_TICKS = {[120] = true, [300] = true, [600] = true, [900] = true, [1200] = true}
local POWER_TICK, NIGHT_TICK, END_TICK = 2400, 2520, 2640

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

local function new_surface(name)
  local s = game.create_surface(name)
  s.generate_with_lab_tiles = true
  s.always_day = true
  s.request_to_generate_chunks({100, 100}, 8)
  s.force_generate_chunk_requests()
  return s
end

-- Builds the blueprint on grid cell (cx, cy) and revives every ghost (entities and tiles). Returns the ghost count.
-- The build position is deliberately far from the cell's center: with absolute snapping the blueprint still lands on
-- the cell that contains it, so "misplaced" below fails if the snapping is lost.
local function build(s, stack, cx, cy, cell)
  local ghosts = stack.build_blueprint{surface = s, force = "player", build_mode = defines.build_mode.forced,
                                       position = {cx * cell + 13.7, cy * cell + 71.3}}
  for _, g in pairs(ghosts) do if g.valid then g.revive() end end
  return #ghosts
end

-- Entities by name in the area, and how many ghosts are left.
local function survey(s, area)
  local counts = {}
  for _, e in pairs(s.find_entities_filtered{area = area, force = "player"}) do
    counts[e.name] = (counts[e.name] or 0) + 1
  end
  local left = #s.find_entities_filtered{area = area, name = {"entity-ghost", "tile-ghost"}}
  return counts, left
end

local function tile_counts(s, area, names)
  local counts = {}
  for name in pairs(names) do counts[name] = s.count_tiles_filtered{area = area, name = name} end
  return counts
end

-- Blueprint entities and tiles that are not on the surface at their blueprint position + (ox, oy).
local function misplaced(s, stack, ox, oy)
  local missing, wrong = 0, 0
  for _, e in pairs(stack.get_blueprint_entities()) do
    if not s.find_entity(e.name, {e.position.x + ox, e.position.y + oy}) then missing = missing + 1 end
  end
  for _, t in pairs(stack.get_blueprint_tiles()) do
    if s.get_tile(t.position.x + ox, t.position.y + oy).name ~= t.name then wrong = wrong + 1 end
  end
  return missing, wrong
end

-- Network ids of a list of entities: how many distinct ones, how many entities per id, and how many have no network.
local function networks(list, id_of)
  local ids, n, none = {}, 0, 0
  for _, e in pairs(list) do
    local id = id_of(e)
    if id == nil then
      none = none + 1
    else
      if not ids[id] then ids[id] = 0; n = n + 1 end
      ids[id] = ids[id] + 1
    end
  end
  return n, ids, none
end

local function electric_id(e) return e.electric_network_id end
local function logistic_id(e) return e.logistic_network and e.logistic_network.network_id end

local function connector(pole, id) return pole.get_wire_connector(id, true) end
local function pole_links(pole) return connector(pole, defines.wire_connector_id.pole_copper).real_connection_count end

-- Wires of one kind among the poles: each wire is counted at both of its ends.
local function wire_count(poles, id)
  local n = 0
  for _, p in pairs(poles) do n = n + connector(p, id).real_connection_count end
  return n / 2
end

-- Poles wired with the given circuit wire: how many, and in how many circuit networks.
local function circuit_networks(poles, id)
  local ids, n, wired = {}, 0, 0
  for _, p in pairs(poles) do
    local c = connector(p, id)
    if c.real_connection_count > 0 then
      wired = wired + 1
      if not ids[c.network_id] then ids[c.network_id] = true; n = n + 1 end
    end
  end
  return wired, n
end

-- Plugs the block (or city) into a power source: a big pole 20 tiles west of the area with an energy interface next
-- to it, as a player would connect the block to the rest of the base.
local function plug(s, tag, x, y)
  local pole = s.create_entity{name = "big-electric-pole", position = {x - 20, y + 5}, force = "player"}
  local eei = s.create_entity{name = "electric-energy-interface", position = {x - 22, y + 5}, force = "player"}
  eei.electric_buffer_size = 1e12
  eei.power_production = 1e9
  eei.energy = 1e12
  local auto = pole_links(pole)
  if auto == 0 then
    local best, dist
    for _, p in pairs(s.find_entities_filtered{name = "big-electric-pole"}) do
      local d = (p.position.x - pole.position.x) ^ 2 + (p.position.y - pole.position.y) ^ 2
      if p ~= pole and (not dist or d < dist) then best, dist = p, d end
    end
    connector(pole, defines.wire_connector_id.pole_copper).connect_to(
      connector(best, defines.wire_connector_id.pole_copper), false, defines.wire_origin.player)
  end
  note("%s: source pole linked to %d pole(s) on placement%s", tag, auto, auto == 0 and "; connected by hand to the nearest block pole" or "")
  return pole, eei
end

local function fill_robots(roboports)
  for _, r in pairs(roboports) do
    local inv = r.get_inventory(defines.inventory.roboport_robot)
    inv.insert{name = "construction-robot", count = 10}
    inv.insert{name = "logistic-robot", count = 10}
  end
end

-- Robot job: four ghosts of wooden chests in the middle of the first block, where the construction areas of its four
-- roboports overlap, and, to build them, four wooden chests stored in one of the block's storage chests.
local JOB_ITEM, JOB_COUNT = "wooden-chest", 4
local function job_area(cell) return {{cell / 2 - 3, cell / 2 - 1}, {cell / 2 + 3, cell / 2 + 1}} end
local function queue_job(s, cell)
  local chest = s.find_entities_filtered{name = "storage-chest", limit = 1}[1]
  chest.insert{name = JOB_ITEM, count = JOB_COUNT}
  for i = 0, JOB_COUNT - 1 do
    s.create_entity{name = "entity-ghost", inner_name = JOB_ITEM, position = {cell / 2 - 1.5 + i, cell / 2 + 0.5}, force = "player"}
  end
end

-- Static part of a scenario "block" (one block or a 2 x 2 city): counts, positions and wires. Runs before plug(), so the
-- wire to the power source is not counted.
local function inspect(tag, s, stack, c, cells, ghosts_built)
  local area = {{0, 0}, {100 * cells, 100 * cells}}
  local blocks = cells * cells
  local counts, left = survey(s, area)
  local want = {}
  for k, v in pairs(c.entities) do want[k] = v * blocks end
  note("%s: build_blueprint returned %d ghosts for %d entities and %d tiles", tag, ghosts_built, c.n_entities * blocks, c.n_tiles * blocks)
  check(left == 0, "%s: %d ghosts left after reviving", tag, left)
  -- the power source that plug() adds later is outside the area, so the counts below are exactly the blueprint's
  check(same_counts(counts, want), "%s: entities built: %s", tag, fmt_counts(counts))
  local tiles = tile_counts(s, area, c.tiles)
  local want_tiles = {}
  for k, v in pairs(c.tiles) do want_tiles[k] = v * blocks end
  check(same_counts(tiles, want_tiles), "%s: tiles built: %s", tag, fmt_counts(tiles))
  local bad = 0
  for cy = 0, cells - 1 do
    for cx = 0, cells - 1 do
      local missing, wrong = misplaced(s, stack, cx * 100, cy * 100)
      bad = bad + missing + wrong
    end
  end
  check(bad == 0, "%s: %d blueprint entities/tiles not at their blueprint position", tag, bad)
  local poles = s.find_entities_filtered{area = area, name = "big-electric-pole"}
  local red, green = wire_count(poles, defines.wire_connector_id.circuit_red), wire_count(poles, defines.wire_connector_id.circuit_green)
  local cu = wire_count(poles, defines.wire_connector_id.pole_copper)
  check(red == c.wires.red * blocks and green == c.wires.green * blocks, "%s: %d red and %d green wires (blueprint: %d and %d per block)",
        tag, red, green, c.wires.red, c.wires.green)
  -- neighboring blocks link their four facing edge poles on build: 4 copper wires per shared side, 2 * n * (n - 1) sides
  local between = 4 * 2 * cells * (cells - 1)
  check(cu == c.wires.copper * blocks + between, "%s: %d copper wires: %d from the blueprint plus %d between neighboring blocks",
        tag, cu, c.wires.copper * blocks, between)
end

local function status_counts(list)
  local states = {}
  for _, e in pairs(list) do
    local name = STATUS[e.status] or "?"
    states[name] = (states[name] or 0) + 1
  end
  return states
end

local function sample(tag, s, cells, seconds)
  local ports = s.find_entities_filtered{area = {{0, 0}, {100 * cells, 100 * cells}}, name = "roboport"}
  note("%s: after %d s the roboports read %s, first one has %.1f of %.1f MJ", tag, seconds, fmt_counts(status_counts(ports)),
       ports[1].energy / 1e6, ports[1].electric_buffer_size / 1e6)
end

local function dynamic(tag, s, cells, c, source)
  local area = {{0, 0}, {100 * cells, 100 * cells}}
  local blocks = cells * cells
  local ports = s.find_entities_filtered{area = area, name = "roboport"}
  local lamps = s.find_entities_filtered{area = area, name = "small-lamp"}
  local poles = s.find_entities_filtered{area = area, name = "big-electric-pole"}
  local chests = s.find_entities_filtered{area = area, name = "storage-chest"}
  local n_el, _, none = networks(poles, electric_id)
  check(n_el == 1 and none == 0, "%s: the %d big poles form %d electric network(s)", tag, #poles, n_el)
  check(source.electric_network_id ~= nil and source.electric_network_id == poles[1].electric_network_id,
        "%s: the power source is on the poles' network", tag)
  local list = {}
  for _, e in pairs(ports) do list[#list + 1] = e end
  for _, e in pairs(lamps) do list[#list + 1] = e end
  local n_list, _, none_list = networks(list, electric_id)
  check(n_list == 1 and none_list == 0 and list[1].electric_network_id == poles[1].electric_network_id,
        "%s: %d roboports and %d lamps are on the poles' network", tag, #ports, #lamps)
  local states = status_counts(ports)
  check(states.working == #ports or states.normal == #ports, "%s: roboport status after 40 s: %s", tag, fmt_counts(states))
  local low = 0
  for _, r in pairs(ports) do if r.energy < 0.99 * r.electric_buffer_size then low = low + 1 end end
  check(low == 0, "%s: %d roboports with a buffer below 99%% (%.1f of %.1f MJ)", tag, low, ports[1].energy / 1e6, ports[1].electric_buffer_size / 1e6)
  -- each block keeps its own red and green circuit network: only the 12 edge poles are wired, and blocks are not joined
  for _, wire in ipairs({{"red", defines.wire_connector_id.circuit_red}, {"green", defines.wire_connector_id.circuit_green}}) do
    local wired, n = circuit_networks(poles, wire[2])
    check(wired == 12 * blocks and n == blocks, "%s: %d poles on the %s wire, %d network(s)", tag, wired, wire[1], n)
  end
  local n_log, ids, none_log = networks(ports, logistic_id)
  check(n_log == 1 and none_log == 0, "%s: the %d roboports form %d logistic network(s) %s", tag, #ports, n_log, fmt_counts(ids))
  local nw = ports[1].logistic_network
  if nw then
    note("%s: logistic network has %d cells, %d construction and %d logistic robots", tag, #nw.cells,
         nw.all_construction_robots, nw.all_logistic_robots)
  end
  local in_net = 0
  for _, ch in pairs(chests) do if ch.logistic_network then in_net = in_net + 1 end end
  check(in_net == #chests, "%s: %d of %d storage chests are inside a logistic network", tag, in_net, #chests)
  local built = s.count_entities_filtered{area = job_area(c.cell), name = JOB_ITEM}
  local ghosts = s.count_entities_filtered{area = job_area(c.cell), name = "entity-ghost"}
  check(built == JOB_COUNT and ghosts == 0, "%s: robots built %d of %d ghosts of %s from a storage chest (%d ghosts left)", tag, built, JOB_COUNT, JOB_ITEM, ghosts)
end

local function night(tag, s, cells)
  local lamps = s.find_entities_filtered{area = {{0, 0}, {100 * cells, 100 * cells}}, name = "small-lamp"}
  local states = status_counts(lamps)
  check(states.working == #lamps, "%s: lamps at night: %s", tag, fmt_counts(states))
end

script.on_init(function()
  game.speed = 20
  local rp = prototypes.entity["roboport"]
  local function try(f) local ok, v = pcall(f); return ok and tostring(v) or "n/a" end
  local pole_proto = prototypes.entity["big-electric-pole"]
  note("roboport: logistic radius %s, construction radius %s; big pole: supply area distance %s, wire reach %s",
       try(function() return rp.logistic_radius end), try(function() return rp.construction_radius end),
       try(function() return pole_proto.get_supply_area_distance() end),
       try(function() return pole_proto.get_max_wire_distance() end))
  check(#CASES == 2, "%d variants under test", #CASES)
  storage.jobs = {}
  local inv = game.create_inventory(1)
  local stack = inv[1]
  for _, c in ipairs(CASES) do
    stack.clear()
    local result = stack.import_stack(c.bp)
    check(result == 0 and stack.is_blueprint and stack.is_blueprint_setup(), "%s: import_stack result %d", c.name, result)
    check(stack.get_blueprint_entity_count() == c.n_entities, "%s: %d entities in the blueprint", c.name, stack.get_blueprint_entity_count())
    check(#stack.get_blueprint_tiles() == c.n_tiles, "%s: %d tiles in the blueprint", c.name, #stack.get_blueprint_tiles())
    local snap = stack.blueprint_snap_to_grid
    check(stack.blueprint_absolute_snapping and snap and snap.x == c.cell and snap.y == c.cell,
          "%s: absolute snapping to a %dx%d grid", c.name, snap and snap.x or 0, snap and snap.y or 0)
    check(stack.label == c.label, "%s: label \"%s\"", c.name, tostring(stack.label))
    for _, cells in ipairs({1, 2}) do
      local tag = string.format("%s %dx%d", c.name, cells, cells)
      local s = new_surface(c.name .. "-" .. cells)
      local ghosts = 0
      for cy = 0, cells - 1 do for cx = 0, cells - 1 do ghosts = ghosts + build(s, stack, cx, cy, c.cell) end end
      inspect(tag, s, stack, c, cells, ghosts)
      local _, source = plug(s, tag, 0, 0)
      local ports = s.find_entities_filtered{name = "roboport"}
      note("%s: a new roboport holds %.1f of %.1f MJ", tag, ports[1].energy / 1e6, ports[1].electric_buffer_size / 1e6)
      fill_robots(ports)
      queue_job(s, c.cell)
      storage.jobs[#storage.jobs + 1] = {tag = tag, surface = s, cells = cells, c = c, source = source}
    end
  end
  inv.destroy()
  storage.t0 = game.tick
end)

script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done then return end
  local rel = e.tick - storage.t0
  if SAMPLE_TICKS[rel] then
    for _, j in ipairs(storage.jobs) do if j.cells == 1 then sample(j.tag, j.surface, j.cells, rel / 60) end end
  end
  if rel == POWER_TICK then
    for _, j in ipairs(storage.jobs) do dynamic(j.tag, j.surface, j.cells, j.c, j.source) end
  elseif rel == NIGHT_TICK - 1 then
    for _, j in ipairs(storage.jobs) do j.surface.always_day = false; j.surface.freeze_daytime = true; j.surface.daytime = 0.5 end
  elseif rel == NIGHT_TICK then
    for _, j in ipairs(storage.jobs) do night(j.tag, j.surface, j.cells) end
  elseif rel == END_TICK then
    lines[#lines + 1] = string.format("checked failed=%d ran=%d", failed, ran)
    helpers.write_file("city_test.txt", table.concat(lines, "\n") .. "\n", false)
    helpers.write_file("city_done.txt", "done\n", false)
    storage.done = true
  end
end)
