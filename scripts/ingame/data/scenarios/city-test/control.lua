-- Checks the 100 x 100 city block blueprints in the real game (headless), alone and next to each other: 1x1, 2x1, 1x2, 2x2
-- and 3x3 of each variant, plus partial and full concrete side by side. For every arrangement: the strings import, every
-- entity, tile and wire is where the blueprint puts it, the two faces of every seam mirror each other tile by tile (and the
-- street between blocks is paved without gaps), the poles form one electric network that powers the roboports and lamps,
-- the roboports and chests join into one logistic network and, where blocks meet, robots build ghosts across the seam.
-- Test data: scripts/export_city.py writes strings.lua (blueprint strings plus the counts to expect).
local CASES = require("strings")
local CELL = 100
-- A roboport's energy buffer takes a while to fill after the power is connected, and it reads "low power" until then,
-- so the energy is sampled at SAMPLE_TICKS and the checks that need a full buffer run at POWER_TICK (40 s).
local SAMPLE_TICKS = {[120] = true, [300] = true, [600] = true, [900] = true, [1200] = true}
local POWER_TICK, NIGHT_TICK, END_TICK = 2400, 2520, 2640
local BAND = 6            -- width of the paved edge band of each block, in tiles
local FAR = 50            -- how deep into each block the seam check looks when all blocks are alike: half a block, every tile

local lines, failed, ran = {}, 0, 0
local function check(ok, fmt, ...)
  ran = ran + 1
  if not ok then failed = failed + 1 end
  lines[#lines + 1] = (ok and "OK   " or "FAIL ") .. string.format(fmt, ...)
end
local function note(fmt, ...) lines[#lines + 1] = "     " .. string.format(fmt, ...) end

local STATUS = {}
for k, v in pairs(defines.entity_status) do STATUS[v] = k end

local BY_NAME, PAVED = {}, {}
for _, c in ipairs(CASES) do
  BY_NAME[c.name] = c
  for tile in pairs(c.tiles) do PAVED[tile] = true end
end
-- A mirror image flips the hazard stripes.
local SWAP = {["refined-hazard-concrete-left"] = "refined-hazard-concrete-right",
              ["refined-hazard-concrete-right"] = "refined-hazard-concrete-left"}

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

local function new_surface(name, cols, rows)
  local s = game.create_surface(name)
  s.generate_with_lab_tiles = true
  s.always_day = true
  s.request_to_generate_chunks({CELL * cols / 2, CELL * rows / 2}, math.ceil(CELL * math.max(cols, rows) / 64) + 4)
  s.force_generate_chunk_requests()
  return s
end

-- Builds the blueprint on grid cell (cx, cy) and revives every ghost (entities and tiles). Returns the ghost count.
-- The build position is deliberately far from the cell's center: with absolute snapping the blueprint still lands on
-- the cell that contains it, so "misplaced" below fails if the snapping is lost.
local function build(s, stack, cx, cy)
  local ghosts = stack.build_blueprint{surface = s, force = "player", build_mode = defines.build_mode.forced,
                                       position = {cx * CELL + 13.7, cy * CELL + 71.3}}
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

-- Robot jobs: four ghosts of wooden chests and, to build them, four wooden chests stored in one of the block's storage chests.
--  * "middle": in the middle of the first block, where the construction areas of its four roboports overlap;
--  * "seam": straddling the seam between the first block and its neighbor (east if there is one, else south), with the
--    chests taken from a storage chest of the first block, so the robots must cross the street between the blocks.
local JOB_ITEM, JOB_COUNT = "wooden-chest", 4
local function jobs_of(arr)
  local jobs = {{name = "middle of the first block", chest = {27.5, 24.5}, area = {{47, 49}, {53, 51}}, ghosts = {}}}
  for i = 0, JOB_COUNT - 1 do jobs[1].ghosts[#jobs[1].ghosts + 1] = {48.5 + i, 50.5} end
  if arr.cols >= 2 or arr.rows >= 2 then
    local seam = {name = "seam", ghosts = {}}
    if arr.cols >= 2 then
      seam.chest, seam.area = {94.5, 33.5}, {{98, 50}, {102, 51}}
      for i = 0, JOB_COUNT - 1 do seam.ghosts[#seam.ghosts + 1] = {98.5 + i, 50.5} end
    else
      seam.chest, seam.area = {33.5, 94.5}, {{50, 98}, {51, 102}}
      for i = 0, JOB_COUNT - 1 do seam.ghosts[#seam.ghosts + 1] = {50.5, 98.5 + i} end
    end
    jobs[2] = seam
  end
  return jobs
end
local function queue_jobs(s, arr)
  for _, job in ipairs(jobs_of(arr)) do
    s.find_entity("storage-chest", job.chest).insert{name = JOB_ITEM, count = JOB_COUNT}
    for _, p in ipairs(job.ghosts) do
      s.create_entity{name = "entity-ghost", inner_name = JOB_ITEM, position = p, force = "player"}
    end
  end
end

-- An arrangement: cols x rows blocks on a surface, each cell holding one variant.
local function arrangement(tag, cols, rows, uniform, pick)
  local cells = {}
  for cy = 0, rows - 1 do
    for cx = 0, cols - 1 do cells[#cells + 1] = {cx = cx, cy = cy, name = pick(cx, cy)} end
  end
  return {tag = tag, cols = cols, rows = rows, uniform = uniform, cells = cells}
end

local function shared_sides(arr) return (arr.cols - 1) * arr.rows + arr.cols * (arr.rows - 1) end

-- Tile names that are not part of the blueprint (lab floor, grass) count as "no paving".
local function paved(name) return PAVED[name] and name or "-" end

-- The two faces of every seam must mirror each other: a tile at distance d before the seam is the mirror image of the
-- tile at distance d after it (hazard stripes flip). The street (BAND tiles on each side) must be paved without gaps.
-- Uniform arrangements are looked at FAR tiles deep (half a block, every tile); mixed ones only at the band, because
-- the inside of the lot differs between the two variants (export_city.py asserts that every tile of the partial
-- concrete blueprint is also in the full concrete one, so the pole pads that lie beyond the band match too).
local function check_seams(arr, s)
  local depth = arr.uniform and FAR or BAND
  local seams, off, gaps = 0, 0, 0
  local function compare(a, b, d)
    a, b = paved(a), paved(b)
    if (SWAP[a] or a) ~= b then off = off + 1 end
    if d < BAND and (a == "-" or b == "-") then gaps = gaps + 1 end
  end
  for cy = 0, arr.rows - 1 do
    for cx = 0, arr.cols - 1 do
      if cx < arr.cols - 1 then       -- vertical seam between (cx, cy) and (cx + 1, cy)
        seams = seams + 1
        local x = (cx + 1) * CELL
        for y = cy * CELL, cy * CELL + CELL - 1 do
          for d = 0, depth - 1 do compare(s.get_tile(x - 1 - d, y).name, s.get_tile(x + d, y).name, d) end
        end
      end
      if cy < arr.rows - 1 then       -- horizontal seam between (cx, cy) and (cx, cy + 1)
        seams = seams + 1
        local y = (cy + 1) * CELL
        for x = cx * CELL, cx * CELL + CELL - 1 do
          for d = 0, depth - 1 do compare(s.get_tile(x, y - 1 - d).name, s.get_tile(x, y + d).name, d) end
        end
      end
    end
  end
  return seams, off, gaps, depth
end

-- Static part of an arrangement: counts, positions, seams and wires. Runs before plug(), so the wire to the power source
-- is not counted.
local function inspect(arr, s, stacks, ghosts_built)
  local tag = arr.tag
  local area = {{0, 0}, {CELL * arr.cols, CELL * arr.rows}}
  local blocks = #arr.cells
  local want, want_tiles, wires = {}, {}, {red = 0, green = 0, copper = 0}
  local n_entities, n_tiles = 0, 0
  for _, cell in ipairs(arr.cells) do
    local c = BY_NAME[cell.name]
    for k, v in pairs(c.entities) do want[k] = (want[k] or 0) + v end
    for k, v in pairs(c.tiles) do want_tiles[k] = (want_tiles[k] or 0) + v end
    for k, v in pairs(c.wires) do wires[k] = wires[k] + v end
    n_entities, n_tiles = n_entities + c.n_entities, n_tiles + c.n_tiles
  end
  local counts, left = survey(s, area)
  note("%s: build_blueprint returned %d ghosts for %d entities and %d tiles", tag, ghosts_built, n_entities, n_tiles)
  check(left == 0, "%s: %d ghosts left after reviving", tag, left)
  -- the power source that plug() adds later is outside the area, so the counts below are exactly the blueprints'
  check(same_counts(counts, want), "%s: entities built: %s", tag, fmt_counts(counts))
  local tiles = tile_counts(s, area, want_tiles)
  check(same_counts(tiles, want_tiles), "%s: tiles built: %s", tag, fmt_counts(tiles))
  local bad = 0
  for _, cell in ipairs(arr.cells) do
    local missing, wrong = misplaced(s, stacks[cell.name], cell.cx * CELL, cell.cy * CELL)
    bad = bad + missing + wrong
  end
  check(bad == 0, "%s: %d blueprint entities/tiles not at their blueprint position", tag, bad)
  local seams, off, gaps, depth = check_seams(arr, s)
  if seams > 0 then
    check(off == 0 and gaps == 0, "%s: %d seams: %d tiles do not mirror the tile facing them (%d deep), %d unpaved tiles in the street",
          tag, seams, off, depth, gaps)
  end
  local poles = s.find_entities_filtered{area = area, name = "big-electric-pole"}
  local red, green = wire_count(poles, defines.wire_connector_id.circuit_red), wire_count(poles, defines.wire_connector_id.circuit_green)
  local cu = wire_count(poles, defines.wire_connector_id.pole_copper)
  check(red == wires.red and green == wires.green, "%s: %d red and %d green wires (blueprints: %d and %d)", tag, red, green, wires.red, wires.green)
  -- neighboring blocks link their four facing edge poles on build: 4 copper wires per shared side
  local between = 4 * shared_sides(arr)
  check(cu == wires.copper + between, "%s: %d copper wires: %d from the blueprints plus %d between neighboring blocks",
        tag, cu, wires.copper, between)
end

local function status_counts(list)
  local states = {}
  for _, e in pairs(list) do
    local name = STATUS[e.status] or "?"
    states[name] = (states[name] or 0) + 1
  end
  return states
end

local function sample(tag, s, seconds)
  local ports = s.find_entities_filtered{area = {{0, 0}, {CELL, CELL}}, name = "roboport"}
  note("%s: after %d s the roboports read %s, first one has %.1f of %.1f MJ", tag, seconds, fmt_counts(status_counts(ports)),
       ports[1].energy / 1e6, ports[1].electric_buffer_size / 1e6)
end

local function dynamic(arr, s, source)
  local tag = arr.tag
  local area = {{0, 0}, {CELL * arr.cols, CELL * arr.rows}}
  local blocks = #arr.cells
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
  for _, job in ipairs(jobs_of(arr)) do
    local built = s.count_entities_filtered{area = job.area, name = JOB_ITEM}
    local ghosts = s.count_entities_filtered{area = job.area, name = "entity-ghost"}
    check(built == JOB_COUNT and ghosts == 0, "%s: robots built %d of %d ghosts of %s at the %s (%d ghosts left)",
          tag, built, JOB_COUNT, JOB_ITEM, job.name, ghosts)
  end
end

local function night(arr, s)
  local lamps = s.find_entities_filtered{area = {{0, 0}, {CELL * arr.cols, CELL * arr.rows}}, name = "small-lamp"}
  local states = status_counts(lamps)
  check(states.working == #lamps, "%s: lamps at night: %s", arr.tag, fmt_counts(states))
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
  local inv = game.create_inventory(#CASES)
  local stacks = {}
  for i, c in ipairs(CASES) do
    local stack = inv[i]
    local result = stack.import_stack(c.bp)
    check(result == 0 and stack.is_blueprint and stack.is_blueprint_setup(), "%s: import_stack result %d", c.name, result)
    check(stack.get_blueprint_entity_count() == c.n_entities, "%s: %d entities in the blueprint", c.name, stack.get_blueprint_entity_count())
    check(#stack.get_blueprint_tiles() == c.n_tiles, "%s: %d tiles in the blueprint", c.name, #stack.get_blueprint_tiles())
    local snap = stack.blueprint_snap_to_grid
    check(stack.blueprint_absolute_snapping and snap and snap.x == c.cell and snap.y == c.cell,
          "%s: absolute snapping to a %dx%d grid", c.name, snap and snap.x or 0, snap and snap.y or 0)
    check(stack.label == c.label, "%s: label \"%s\"", c.name, tostring(stack.label))
    stacks[c.name] = stack
  end
  local arrangements = {}
  for _, c in ipairs(CASES) do
    for _, size in ipairs({{1, 1}, {2, 1}, {1, 2}, {2, 2}, {3, 3}}) do
      arrangements[#arrangements + 1] = arrangement(string.format("%s %dx%d", c.name, size[1], size[2]), size[1], size[2], true,
                                                    function() return c.name end)
    end
  end
  -- partial and full concrete side by side, in a checkerboard so that every seam joins one of each
  for _, size in ipairs({{2, 1}, {2, 2}, {3, 3}}) do
    arrangements[#arrangements + 1] = arrangement(string.format("mixed %dx%d", size[1], size[2]), size[1], size[2], false,
      function(cx, cy) return (cx + cy) % 2 == 0 and "partial-concrete" or "full-concrete" end)
  end
  for _, arr in ipairs(arrangements) do
    local s = new_surface(arr.tag, arr.cols, arr.rows)
    local ghosts = 0
    for _, cell in ipairs(arr.cells) do ghosts = ghosts + build(s, stacks[cell.name], cell.cx, cell.cy) end
    inspect(arr, s, stacks, ghosts)
    local _, source = plug(s, arr.tag, 0, 0)
    local ports = s.find_entities_filtered{name = "roboport"}
    if #arr.cells == 1 then note("%s: a new roboport holds %.1f of %.1f MJ", arr.tag, ports[1].energy / 1e6, ports[1].electric_buffer_size / 1e6) end
    fill_robots(ports)
    queue_jobs(s, arr)
    storage.jobs[#storage.jobs + 1] = {arr = arr, surface = s, source = source}
  end
  inv.destroy()
  storage.t0 = game.tick
end)

script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done then return end
  local rel = e.tick - storage.t0
  if SAMPLE_TICKS[rel] then
    for _, j in ipairs(storage.jobs) do if #j.arr.cells == 1 then sample(j.arr.tag, j.surface, rel / 60) end end
  end
  if rel == POWER_TICK then
    for _, j in ipairs(storage.jobs) do dynamic(j.arr, j.surface, j.source) end
  elseif rel == NIGHT_TICK - 1 then
    for _, j in ipairs(storage.jobs) do j.surface.always_day = false; j.surface.freeze_daytime = true; j.surface.daytime = 0.5 end
  elseif rel == NIGHT_TICK then
    for _, j in ipairs(storage.jobs) do night(j.arr, j.surface) end
  elseif rel == END_TICK then
    lines[#lines + 1] = string.format("checked failed=%d ran=%d", failed, ran)
    helpers.write_file("city_test.txt", table.concat(lines, "\n") .. "\n", false)
    helpers.write_file("city_done.txt", "done\n", false)
    storage.done = true
  end
end)
