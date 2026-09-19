-- In-game measurement of a refinery blueprint: build it, replace producers by infinity pipes (done in the blueprint),
-- fulfil module requests, feed coal to plastic plants, clear outputs, power everything, count plastic crafts.
local tests = require("tests")
local CELL_W, CELL_H = 260, 200
local WARM, MEAS, STEP = 18000, 18000, 120
local RATE_MAX = 1.2 * 1.2 -- products_finished per second per plastic plant (speed 1.2, +20% productivity)

local STATUS = {}
for k, v in pairs(defines.entity_status) do STATUS[v] = k end

local function fulfil_requests(s, area, rec)
  local n = 0
  for _, proxy in pairs(s.find_entities_filtered{area = area, name = "item-request-proxy"}) do
    local target = proxy.proxy_target
    local plan = proxy.insert_plan
    if target and target.valid and plan then
      for _, p in pairs(plan) do
        local name = p.id.name
        for _, loc in pairs(p.items.in_inventory or {}) do
          local inv = target.get_inventory(loc.inventory)
          if inv then n = n + inv.insert{name = name, count = loc.count or 1} end
        end
      end
    end
    if proxy.valid then proxy.destroy() end
  end
  rec.modules = n
end

local function build_all()
  local s = game.create_surface("lab")
  s.generate_with_lab_tiles = true
  s.always_day = true
  local cx, cy = #tests * CELL_W / 2, CELL_H / 2
  s.request_to_generate_chunks({cx, cy}, math.ceil(math.max(cx, cy) / 32) + 3)
  s.force_generate_chunk_requests()
  local inv = game.create_inventory(1)
  local stack = inv[1]
  storage.t = {}
  for i, t in pairs(tests) do
    local rec = {label = t.label, errors = {}, plants = {}, pumps = {}, tanks = {}, machines = {}}
    if t.clear then rec.clear = {}; for _, r in pairs(t.clear) do rec.clear[r] = true end end
    local ox, oy = (i - 1) * CELL_W, 0
    rec.ox, rec.oy = ox, oy
    local pos = {ox + CELL_W / 2, oy + CELL_H / 2}
    stack.clear()
    local r = stack.import_stack(t.bp)
    if r ~= 0 then rec.errors[#rec.errors+1] = "import_stack=" .. r end
    local ghosts = stack.build_blueprint{surface = s, force = "player", position = pos, build_mode = defines.build_mode.forced}
    rec.ghosts = #ghosts
    local revived, failed = 0, {}
    for _, g in pairs(ghosts) do
      if g.valid then
        local name = g.ghost_name
        local _, e = g.revive()
        if e then revived = revived + 1 else failed[#failed+1] = name end
      end
    end
    rec.revived = revived
    if #failed > 0 then rec.errors[#rec.errors+1] = "revive failed: " .. #failed .. " e.g. " .. failed[1] end
    local area = {{ox, oy}, {ox + CELL_W, oy + CELL_H}}
    fulfil_requests(s, area, rec)
    rec.infinity = 0
    for _, e in pairs(s.find_entities_filtered{area = area, name = "infinity-pipe"}) do rec.infinity = rec.infinity + 1 end
    local plants = s.find_entities_filtered{area = area, name = "chemical-plant"}
    local np = 0
    for _, p in pairs(plants) do
      if p.get_recipe() and p.get_recipe().name == "plastic-bar" then
        np = np + 1
        rec.plants[np] = {e = p, x = p.position.x - ox, y = p.position.y - oy, c0 = 0}
      end
      rec.machines[#rec.machines+1] = p
    end
    for _, m in pairs(s.find_entities_filtered{area = area, name = {"oil-refinery", "assembling-machine-3"}}) do rec.machines[#rec.machines+1] = m end
    rec.byrecipe = {}
    for _, m in pairs(rec.machines) do
      local r = m.get_recipe()
      if r then
        rec.byrecipe[r.name] = rec.byrecipe[r.name] or {}
        local l = rec.byrecipe[r.name]; l[#l+1] = {e = m, c0 = 0}
      end
    end
    if np ~= t.plants then rec.errors[#rec.errors+1] = "plastic plants " .. np .. " expected " .. t.plants end
    for k, p in pairs(s.find_entities_filtered{area = area, name = "pump"}) do
      rec.pumps[k] = {e = p, x = p.position.x - ox, y = p.position.y - oy}
    end
    for k, p in pairs(s.find_entities_filtered{area = area, name = "storage-tank"}) do
      rec.tanks[k] = {e = p, x = p.position.x - ox, y = p.position.y - oy}
    end
    rec.pipes = {}
    for _, p in pairs(s.find_entities_filtered{area = area, name = {"pipe", "pipe-to-ground", "storage-tank", "pump", "infinity-pipe"}}) do
      rec.pipes[#rec.pipes+1] = {e = p, x = p.position.x - ox, y = p.position.y - oy}
    end
    -- locked fluids of one refinery and one sulfur plant (port order check)
    local refi = s.find_entities_filtered{area = area, name = "oil-refinery", limit = 1}[1]
    if refi then rec.refinery_ports = {}; for k = 1, #refi.fluidbox do rec.refinery_ports[k] = refi.fluidbox.get_locked_fluid(k) or "-" end end
    for _, p in pairs(plants) do
      if p.get_recipe() and p.get_recipe().name == "sulfur" then
        rec.sulfur_ports = {}; for k = 1, #p.fluidbox do rec.sulfur_ports[k] = p.fluidbox.get_locked_fluid(k) or "-" end; break
      end
    end
    local poles = s.find_entities_filtered{area = area, name = {"medium-electric-pole", "big-electric-pole", "substation", "small-electric-pole"}}
    rec.poles, rec.eei = #poles, 0
    for _, pole in pairs(poles) do
      local p2 = s.find_non_colliding_position("electric-energy-interface", pole.position, 2.5, 0.5)
      if p2 then
        local eei = s.create_entity{name = "electric-energy-interface", position = p2, force = "player"}
        if eei then eei.power_production = 1e9; eei.energy = 1e12; eei.electric_buffer_size = 1e12; rec.eei = rec.eei + 1 end
      end
    end
    if rec.eei == 0 then rec.errors[#rec.errors+1] = "no eei" end
    storage.t[i] = rec
  end
  inv.destroy()
end

local function sample()
  for _, rec in pairs(storage.t) do
    for _, l in pairs(rec.byrecipe) do
      for _, m in pairs(l) do
        if m.e.valid then
          local k = STATUS[m.e.status]; m.st = m.st or {}; m.st[k] = (m.st[k] or 0) + 1
          if m.e.name == "oil-refinery" then
            m.low = m.low or {water = 0, crude = 0}
            local w, c = m.e.fluidbox[1], m.e.fluidbox[2]
            if not w or w.amount < 50 then m.low.water = m.low.water + 1 end
            if not c or c.amount < 100 then m.low.crude = m.low.crude + 1 end
          elseif m.e.name == "chemical-plant" then
            m.low = m.low or {water = 0, other = 0}
            local nb = #m.e.fluidbox
            local a = nb >= 1 and m.e.fluidbox[1] or nil
            local b = nb >= 2 and m.e.fluidbox[2] or nil
            if not a or a.amount < 30 then m.low.water = m.low.water + 1 end
            if not b or b.amount < 30 then m.low.other = m.low.other + 1 end
          end
        end
      end
    end
  end
end

local function service()
  for _, rec in pairs(storage.t) do
    for _, m in pairs(rec.machines) do
      if m.valid then
        local r = m.get_recipe()
        if r and (not rec.clear or rec.clear[r.name]) then
          local out = m.get_output_inventory(); if out then out.clear() end
        end
        if r and (not rec.feed_only_plastic or r.name == "plastic-bar") then
          for _, g in pairs(r.ingredients) do
            if g.type == "item" then
              local c = m.get_item_count(g.name)
              if c < 50 then m.insert{name = g.name, count = 100 - c} end
            end
          end
        end
      end
    end
  end
end

local function snapshot()
  for _, rec in pairs(storage.t) do
    for _, p in pairs(rec.plants) do p.c0 = p.e.products_finished end
    for _, l in pairs(rec.byrecipe) do for _, m in pairs(l) do m.c0 = m.e.products_finished end end
  end
end

local function dump()
  local out = {}
  for _, rec in pairs(storage.t) do
    local plants, pumps, tanks = {}, {}, {}
    for k, p in pairs(rec.plants) do
      plants[k] = {x = p.x, y = p.y, crafts = p.e.products_finished - p.c0, status = STATUS[p.e.status], net = p.e.electric_network_id,
                   speed = p.e.crafting_speed, gas = (p.e.fluidbox[1] and p.e.fluidbox[1].amount or 0)}
    end
    for k, p in pairs(rec.pumps) do
      local f = p.e.fluidbox[1]
      local cb = p.e.get_control_behavior()
      local cond = cb and cb.circuit_condition
      pumps[k] = {x = p.x, y = p.y, status = STATUS[p.e.status], amount = f and f.amount or 0, fluid = f and f.name or "-",
                  cond = cond and cond.first_signal and (cond.first_signal.name .. (cond.comparator or "") .. tostring(cond.constant)) or nil,
                  enabled = cb and cb.circuit_enable_disable or nil}
    end
    for k, p in pairs(rec.tanks) do
      local f = p.e.fluidbox[1]
      tanks[k] = {x = p.x, y = p.y, amount = f and f.amount or 0, fluid = f and f.name or "-"}
    end
    local recipes = {}
    for name, l in pairs(rec.byrecipe) do
      local crafts, st, samples, expect, per = 0, {}, {}, 0, {}
      for _, m in pairs(l) do
        crafts = crafts + (m.e.products_finished - m.c0); local k = STATUS[m.e.status]; st[k] = (st[k] or 0) + 1
        for sk, sv in pairs(m.st or {}) do samples[sk] = (samples[sk] or 0) + sv end
        local r = m.e.get_recipe()
        local ex = r and (m.e.crafting_speed / r.energy * (1 + m.e.productivity_bonus)) or 0
        expect = expect + ex
        per[#per+1] = {x = m.e.position.x - rec.ox, y = m.e.position.y - rec.oy, crafts = m.e.products_finished - m.c0, expect = ex, speed = m.e.crafting_speed, prod = m.e.productivity_bonus, st = m.st, low = m.low}
      end
      recipes[name] = {n = #l, crafts = crafts, status = st, samples = samples, expect_per_s = expect, per = per}
    end
    local fl, mixed = {}, 0
    for _, p in pairs(rec.pipes) do
      if p.e.valid then
        local names = {}
        for fname, _ in pairs(p.e.fluidbox.get_fluid_segment_contents(1) or {}) do names[#names+1] = fname end
        table.sort(names)
        if #names > 1 then mixed = mixed + 1 end
        fl[p.x .. "," .. p.y] = p.e.name .. ":" .. table.concat(names, "+") .. ":" .. tostring(p.e.fluidbox.get_fluid_segment_id(1))
      end
    end
    local tankconn = {}
    for _, p in pairs(rec.pipes) do
      if p.e.valid and p.e.name == "storage-tank" and not tankconn[tostring(p.e.direction)] then
        local c = {}
        for _, pc in pairs(p.e.fluidbox.get_pipe_connections(1)) do
          c[#c+1] = {dx = pc.position.x - p.e.position.x, dy = pc.position.y - p.e.position.y, tx = pc.target_position.x - p.e.position.x, ty = pc.target_position.y - p.e.position.y}
        end
        tankconn[tostring(p.e.direction)] = c
      end
    end
    local pumpseg = {}
    for _, p in pairs(rec.pipes) do
      if p.e.valid and p.e.name == "pump" then
        local segs = {}
        for k = 1, #p.e.fluidbox do
          local id = p.e.fluidbox.get_fluid_segment_id(k)
          segs[k] = id and tostring(id) or "nil"
        end
        pumpseg[p.x .. "," .. p.y] = table.concat(segs, "|")
      end
    end
    local mstat = {}
    for _, m in pairs(rec.machines) do
      if m.valid then mstat[(m.position.x - rec.ox) .. "," .. (m.position.y - rec.oy)] = STATUS[m.status] end
    end
    local rdata = {}
    for name, _ in pairs(rec.byrecipe) do
      local r = prototypes.recipe[name]
      local ing, prd = {}, {}
      for _, g in pairs(r.ingredients) do ing[#ing+1] = {name = g.name, type = g.type, amount = g.amount} end
      for _, g in pairs(r.products) do prd[#prd+1] = {name = g.name, type = g.type, amount = g.amount or ((g.amount_min or 0) + (g.amount_max or 0)) / 2} end
      rdata[name] = {energy = r.energy, ingredients = ing, products = prd}
    end
    out[#out+1] = {label = rec.label, recipes = recipes, recipe_data = rdata, tank_connections = tankconn, pump_segments = pumpseg, fluids = fl, mixed_segments = mixed, machine_status = mstat, errors = rec.errors, ghosts = rec.ghosts, revived = rec.revived, infinity = rec.infinity,
                   modules = rec.modules, poles = rec.poles, eei = rec.eei, refinery_ports = rec.refinery_ports, sulfur_ports = rec.sulfur_ports,
                   meas_ticks = MEAS, rate_max = RATE_MAX, plants = plants, pumps = pumps, tanks = tanks}
  end
  helpers.write_file("fluid_results.json", helpers.table_to_json(out), false)
end

script.on_init(function()
  game.speed = 1000
  game.forces.player.research_all_technologies()
  build_all()
  storage.start = game.tick
  service()
end)

script.on_nth_tick(STEP, function(e)
  if not storage.t or storage.done then return end
  local rel = e.tick - storage.start
  service()
  if rel == WARM then snapshot()
  elseif rel > WARM and rel < WARM + MEAS then sample()
  elseif rel >= WARM + MEAS then
    dump()
    storage.done = true
    helpers.write_file("fluid_done.txt", "done at tick " .. e.tick, false)
  end
end)
