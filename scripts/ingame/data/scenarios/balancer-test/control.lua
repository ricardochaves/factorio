-- In-game verification of belt balancers: build every blueprint, feed it with loaders, measure real item flow.
local tests = require("tests")
local TIER = require("tier")
local CELL_W, CELL_H, PER_ROW = 64, 112, 24
for _, t in pairs(tests) do CELL_W = math.max(CELL_W, t.w + 12); CELL_H = math.max(CELL_H, t.h + 20) end
local WARM, MEAS, STEP = TIER.warm, 3600, 600
local ITEM = "iron-plate"
local FULL = 4800

local function build_all()
  local s = game.create_surface("lab")
  s.generate_with_lab_tiles = true
  s.always_day = true
  local rows = math.ceil(#tests / PER_ROW)
  local cx, cy = PER_ROW * CELL_W / 2, rows * CELL_H / 2
  s.request_to_generate_chunks({cx, cy}, math.ceil(math.max(cx, cy) / 32) + 2)
  s.force_generate_chunk_requests()
  local inv = game.create_inventory(1)
  local stack = inv[1]
  storage.t = {}
  for i, t in pairs(tests) do
    local rec = {label = t.label, n = t.n, m = t.m, errors = {}}
    local col, row = (i - 1) % PER_ROW, math.floor((i - 1) / PER_ROW)
    local ox, oy = col * CELL_W, row * CELL_H
    local pos = {ox + CELL_W / 2, oy + CELL_H / 2}
    stack.clear()
    local r = stack.import_stack(t.bp)
    if r ~= 0 then rec.errors[#rec.errors+1] = "import_stack=" .. r end
    local ghosts = stack.build_blueprint{surface = s, force = "player", position = pos, build_mode = defines.build_mode.normal}
    rec.ghosts = #ghosts
    local revived = 0
    for _, g in pairs(ghosts) do
      local _, e = g.revive()
      if e then revived = revived + 1 end
    end
    rec.revived = revived
    local area = {{ox, oy}, {ox + CELL_W, oy + CELL_H}}
    local ents = s.find_entities_filtered{area = area, type = {"transport-belt", "underground-belt", "splitter"}}
    rec.built = #ents
    if #ents ~= t.count then rec.errors[#rec.errors+1] = "built " .. #ents .. " expected " .. t.count end
    local minx, miny, maxy = 1e9, 1e9, -1e9
    for _, e in pairs(ents) do
      local bb = e.bounding_box
      minx = math.min(minx, math.floor(bb.left_top.x + 0.01))
      miny = math.min(miny, math.floor(bb.left_top.y + 0.01))
      maxy = math.max(maxy, math.floor(bb.right_bottom.y - 0.01))
    end
    -- unpaired undergrounds = broken blueprint
    local unpaired = 0
    for _, e in pairs(ents) do
      if e.type == "underground-belt" and not e.neighbours then unpaired = unpaired + 1 end
    end
    if unpaired > 0 then rec.errors[#rec.errors+1] = "unpaired undergrounds " .. unpaired end
    rec.src, rec.snk = {}, {}
    for k, c in pairs(t.ins) do
      local x = minx + c + 0.5
      local l = s.create_entity{name = TIER.loader, position = {x, maxy + 2}, direction = defines.direction.north, type = "output", force = "player"}
      local ch = s.create_entity{name = "steel-chest", position = {x, maxy + 3.5}, force = "player"}
      if not (l and ch) then rec.errors[#rec.errors+1] = "source create failed " .. k else
        ch.insert{name = ITEM, count = FULL}
        rec.src[k] = {loader = l, chest = ch, used = 0, on = true}
      end
    end
    for k, c in pairs(t.outs) do
      local x = minx + c + 0.5
      local l = s.create_entity{name = TIER.loader, position = {x, miny - 1}, direction = defines.direction.north, type = "input", force = "player"}
      local ch = s.create_entity{name = "steel-chest", position = {x, miny - 2.5}, force = "player"}
      if not (l and ch) then rec.errors[#rec.errors+1] = "sink create failed " .. k else
        rec.snk[k] = {loader = l, chest = ch, got = 0, on = true}
      end
    end
    storage.t[i] = rec
  end
  inv.destroy()
end

local function service(count)
  for _, rec in pairs(storage.t) do
    for _, p in pairs(rec.src) do
      local c = p.chest.get_item_count(ITEM)
      if p.on then
        if count then p.used = p.used + (FULL - c) end
        if c < FULL then p.chest.insert{name = ITEM, count = FULL - c} end
      end
    end
    for _, p in pairs(rec.snk) do
      local c = p.chest.get_item_count(ITEM)
      if count then p.got = p.got + c end
      if c > 0 then p.chest.clear_items_inside() end
    end
  end
end

local function reset_counters()
  for _, rec in pairs(storage.t) do
    for _, p in pairs(rec.src) do p.used = 0 end
    for _, p in pairs(rec.snk) do p.got = 0 end
  end
end

local function pick(phase, k, total, salt)
  -- which ports are active in a phase (k = 1..total)
  if total == 1 then return true end
  if phase == "half" then return k % 2 == 1 end
  if phase == "third" then return k <= math.ceil(total / 3) end
  if phase == "random" then
    local on = ((k * 7919 + salt * 104729) % 10) < 5
    if k == (salt % total) + 1 then on = true end          -- never all off
    return on
  end
  if phase == "single" then return k == total end
  return true
end

local IN_MODE  = {A = "all", B = "half", C = "all",  D = "third", E = "all",   F = "random", G = "all",    H = "single", I = "all"}
local OUT_MODE = {A = "all", B = "all",  C = "half", D = "all",   E = "third", F = "all",    G = "random", H = "all",    I = "single"}

local function set_pattern(phase)
  for idx, rec in pairs(storage.t) do
    for k, p in pairs(rec.src) do
      local on = pick(IN_MODE[phase], k, rec.n, idx)
      p.on = on
      if not on then p.chest.clear_items_inside() end
    end
    for k, p in pairs(rec.snk) do
      local on = pick(OUT_MODE[phase], k, rec.m, idx + 1)
      p.on = on
      p.loader.active = on
    end
  end
end

local function dump(phase)
  local out = {}
  for i, rec in pairs(storage.t) do
    local ins, outs, ion, oon = {}, {}, {}, {}
    for k, p in pairs(rec.src) do ins[k] = p.used; ion[k] = p.on end
    for k, p in pairs(rec.snk) do outs[k] = p.got; oon[k] = p.on end
    out[#out+1] = {label = rec.label, n = rec.n, m = rec.m, phase = phase, ins = ins, outs = outs, in_on = ion, out_on = oon,
                   errors = rec.errors, built = rec.built, ghosts = rec.ghosts, revived = rec.revived}
  end
  helpers.write_file("balancer_results_" .. phase .. ".json", helpers.table_to_json(out), false)
end

local PHASES = TIER.phases

script.on_init(function()
  game.speed = 1000
  build_all()
  storage.phase = 1
  storage.phase_start = game.tick
  set_pattern(PHASES[1])
  dump("build")
end)

script.on_nth_tick(STEP, function(e)
  if not storage.t or storage.done then return end
  local rel = e.tick - storage.phase_start
  if rel <= 0 then return end
  if rel < WARM then service(false)
  elseif rel == WARM then service(false); reset_counters()
  elseif rel < WARM + MEAS then service(true)
  else
    service(true)
    dump(PHASES[storage.phase])
    storage.phase = storage.phase + 1
    if storage.phase > #PHASES then
      storage.done = true
      helpers.write_file("balancer_done.txt", "done at tick " .. e.tick, false)
    else
      storage.phase_start = e.tick
      set_pattern(PHASES[storage.phase])
    end
  end
end)
