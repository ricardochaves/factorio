-- Photos of the 100 x 100 city block blueprints for the site, taken with the game's own renderer (needs the GUI build, not
-- headless). Each variant is built on a grass field, plugged into a power source and loaded with robots; the power source
-- (a big pole and an energy interface) sits 20 tiles west of the block, outside every frame except its copper wire, which
-- enters the frames at the top-left corner.
-- Test data: scripts/export_city.py writes strings.lua. Photos go to script-output/city_<name>.png.
local CASES = require("strings")
local CELL = 100
-- The photos wait for the roboports to fill their energy buffers (20 s), so they show the block as it works.
local SHOT_TICK, END_TICK = 1200, 1900

-- Shots per surface, in tiles: {file, center x, center y, width, height, zoom (1 = 32 px per tile), daytime (0 noon, 0.5 midnight)}.
local SHOTS = {
  ["full-concrete-1"] = {
    {"overview_full", 50, 50, 120, 120, 0.5, 0},
    {"roboport", 26, 26, 26, 17, 2, 0},
  },
  ["partial-concrete-1"] = {
    {"overview_partial", 50, 50, 120, 120, 0.5, 0},
    {"corner", 10, 8, 22, 15, 2, 0},
    {"night_corner", 14, 12, 34, 23, 1.4, 0.5},
  },
  ["full-concrete-2"] = {
    {"city_2x2", 100, 100, 220, 220, 0.3, 0},
  },
}

-- Robots at work: 32 ghosts of wooden chests in the middle of the block, built with wooden chests taken from a storage chest
-- next to a roboport. The job starts at JOB_TICK, after the still photos (SHOT_TICK) so that its ghosts are not in them; the
-- robots take off after about 4 s and the photo, taken at FRAME_TICK, catches them in flight. To pick another moment,
-- raise FRAMES: one photo is taken every FRAME_STEP ticks (city_robots_at_work_1.png ...).
local JOB_SURFACE, JOB_TICK, FRAME_TICK, FRAME_STEP, FRAMES = "full-concrete-1", 1300, 1680, 60, 1
local JOB_VIEW = {33, 32, 36, 28, 1.4}   -- center x, y, width, height in tiles, zoom

local function queue_job(s)
  s.find_entity("storage-chest", {27.5, 24.5}).insert{name = "wooden-chest", count = 32}
  for row = 0, 3 do
    for col = 0, 7 do
      s.create_entity{name = "entity-ghost", inner_name = "wooden-chest", position = {34.5 + col, 36.5 + row}, force = "player"}
    end
  end
end

local function grass_surface(name, cells)
  local s = game.create_surface(name, {
    seed = 20260919,
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
  local mid = cells * CELL / 2
  s.request_to_generate_chunks({mid, mid}, math.ceil(cells * CELL / 64) + 4)
  s.force_generate_chunk_requests()
  return s
end

local function build_blocks(s, stack, cells)
  local area = {{-4, -4}, {cells * CELL + 4, cells * CELL + 4}}
  for _, e in pairs(s.find_entities_filtered{area = area}) do e.destroy() end
  s.destroy_decoratives{area = area}
  for cy = 0, cells - 1 do
    for cx = 0, cells - 1 do
      local ghosts = stack.build_blueprint{surface = s, force = "player", build_mode = defines.build_mode.forced,
                                           position = {cx * CELL + CELL / 2, cy * CELL + CELL / 2}}
      for _, g in pairs(ghosts) do if g.valid then g.revive() end end
    end
  end
end

local function power_and_robots(s)
  local pole = s.create_entity{name = "big-electric-pole", position = {-20, 5}, force = "player"}
  local eei = s.create_entity{name = "electric-energy-interface", position = {-22, 5}, force = "player"}
  eei.electric_buffer_size = 1e12
  eei.power_production = 1e9
  eei.energy = 1e12
  for _, r in pairs(s.find_entities_filtered{name = "roboport"}) do
    local inv = r.get_inventory(defines.inventory.roboport_robot)
    inv.insert{name = "construction-robot", count = 10}
    inv.insert{name = "logistic-robot", count = 10}
  end
  return pole
end

script.on_init(function()
  game.speed = 8
  local inv = game.create_inventory(1)
  local stack = inv[1]
  local log = {}
  for _, c in ipairs(CASES) do
    stack.clear()
    assert(stack.import_stack(c.bp) == 0, "import failed: " .. c.name)
    for _, cells in ipairs({1, 2}) do
      local key = c.name .. "-" .. cells
      if SHOTS[key] then
        local s = grass_surface(key, cells)
        build_blocks(s, stack, cells)
        power_and_robots(s)
        local left = #s.find_entities_filtered{name = {"entity-ghost", "tile-ghost"}}
        log[#log + 1] = string.format("%s: %d entities, %d ghosts left", key, #s.find_entities_filtered{force = "player"}, left)
      end
    end
  end
  inv.destroy()
  storage.log, storage.t0 = log, game.tick
end)

script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done then return end
  local rel = e.tick - storage.t0
  if rel == JOB_TICK then
    queue_job(game.surfaces[JOB_SURFACE])
  elseif rel >= FRAME_TICK and rel < FRAME_TICK + FRAME_STEP * FRAMES and (rel - FRAME_TICK) % FRAME_STEP == 0 then
    local x, y, w, h, zoom = table.unpack(JOB_VIEW)
    local n = (rel - FRAME_TICK) / FRAME_STEP + 1
    local s = game.surfaces[JOB_SURFACE]
    local file = FRAMES == 1 and "robots_at_work" or ("robots_at_work_" .. n)
    game.take_screenshot{surface = s, position = {x, y}, resolution = {math.floor(w * 32 * zoom), math.floor(h * 32 * zoom)},
                         zoom = zoom, path = "city_" .. file .. ".png", show_entity_info = false, daytime = 0,
                         water_tick = 0, force_render = true, anti_alias = true, quality = 100}
    storage.log[#storage.log + 1] = string.format("%s at +%d ticks: %d wooden chests built, %d ghosts left", file, rel - JOB_TICK,
      s.count_entities_filtered{name = "wooden-chest"}, s.count_entities_filtered{name = "entity-ghost"})
  end
  if rel == SHOT_TICK then
    for key, list in pairs(SHOTS) do
      local s = game.surfaces[key]
      local port = s.find_entities_filtered{name = "roboport", limit = 1}[1]
      storage.log[#storage.log + 1] = string.format("%s: first roboport has %.1f of %.1f MJ", key, port.energy / 1e6, port.electric_buffer_size / 1e6)
      for _, sh in ipairs(list) do
        local file, x, y, w, h, zoom, daytime = table.unpack(sh)
        game.take_screenshot{surface = s, position = {x, y}, resolution = {math.floor(w * 32 * zoom), math.floor(h * 32 * zoom)},
                             zoom = zoom, path = "city_" .. file .. ".png", show_entity_info = false, daytime = daytime,
                             water_tick = 0, force_render = true, anti_alias = true, quality = 100}
        storage.log[#storage.log + 1] = "shot " .. file
      end
    end
  elseif rel == END_TICK then
    helpers.write_file("city_shot_done.txt", table.concat(storage.log, "\n") .. "\n", false)
    storage.done = true
  end
end)
