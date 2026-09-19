-- Build the blueprint on a lab surface and render screenshots with the game's own renderer (needs the GUI build).
local BP = require("bp")
local CX, CY = 0, 0
local SHOTS = {
  {name = "refinaria_v3_full.png",   zoom = 0.75, pos = {0, 0},     res = {4800, 3300}},   -- whole blueprint (192 x 128 tiles)
  {name = "refinaria_v3_plastico.png", zoom = 2,  pos = {-31, 20},  res = {1600, 1200}},   -- plastic-right feed pumps
  {name = "refinaria_v3_agua_p1.png",  zoom = 2,  pos = {91, 45},   res = {1600, 1200}},   -- water P1 near (-115.5, 485)
  {name = "refinaria_v3_agua_p2.png",  zoom = 2,  pos = {85, 16},   res = {1600, 1200}},   -- water P2 near (-126, 454.5)
}
script.on_init(function()
  game.forces.player.research_all_technologies()
  local s = game.create_surface("lab")
  s.generate_with_lab_tiles = true
  s.always_day = true
  s.request_to_generate_chunks({CX, CY}, 8)
  s.force_generate_chunk_requests()
  local inv = game.create_inventory(1)
  local st = inv[1]
  st.import_stack(BP)
  local ghosts = st.build_blueprint{surface = s, force = "player", position = {CX, CY}, build_mode = defines.build_mode.forced}
  for _, g in pairs(ghosts) do if g.valid then g.revive() end end
  for _, proxy in pairs(s.find_entities_filtered{name = "item-request-proxy"}) do
    local target, plan = proxy.proxy_target, proxy.insert_plan
    if target and target.valid and plan then
      for _, p in pairs(plan) do
        for _, loc in pairs(p.items.in_inventory or {}) do
          local i = target.get_inventory(loc.inventory); if i then i.insert{name = p.id.name, count = loc.count or 1} end
        end
      end
    end
    if proxy.valid then proxy.destroy() end
  end
  inv.destroy()
  -- blueprint bounding box on the surface (to report the offset between blueprint and screenshot coordinates)
  local minx, miny, maxx, maxy = 1e9, 1e9, -1e9, -1e9
  for _, e in pairs(s.find_entities_filtered{force = "player"}) do
    local b = e.bounding_box
    minx = math.min(minx, b.left_top.x); miny = math.min(miny, b.left_top.y); maxx = math.max(maxx, b.right_bottom.x); maxy = math.max(maxy, b.right_bottom.y)
  end
  storage.bbox = {minx, miny, maxx, maxy}
  storage.t0 = game.tick
end)
script.on_event(defines.events.on_tick, function(e)
  if not storage.t0 or storage.done then return end
  local rel = e.tick - storage.t0
  if rel == 120 then
    local s = game.surfaces["lab"]
    for _, sh in pairs(SHOTS) do
      game.take_screenshot{surface = s, position = sh.pos, resolution = sh.res, zoom = sh.zoom, path = sh.name,
                           show_entity_info = true, daytime = 0, water_tick = 0, force_render = true, anti_alias = true, quality = 100}
    end
  elseif rel == 130 or rel == 260 or rel == 400 then
    -- status experiment on one refinery: no power / power / power + fluids
    local s = game.surfaces["lab"]
    local STATUS = {}; for k, v in pairs(defines.entity_status) do STATUS[v] = k end
    local r = s.find_entities_filtered{name = "oil-refinery", position = {86, 46}, radius = 4, limit = 1}[1]
    if rel == 130 then
      storage.log = "step1 no power: " .. STATUS[r.status] .. "\n"
      game.take_screenshot{surface = s, position = r.position, resolution = {600, 600}, zoom = 2, path = "status_1_nopower.png", show_entity_info = true, daytime = 0, force_render = true}
      for _, pole in pairs(s.find_entities_filtered{name = {"medium-electric-pole", "big-electric-pole", "substation"}}) do
        local p2 = s.find_non_colliding_position("electric-energy-interface", pole.position, 2.5, 0.5)
        if p2 then local e = s.create_entity{name = "electric-energy-interface", position = p2, force = "player"}; if e then e.power_production = 1e9; e.energy = 1e12; e.electric_buffer_size = 1e12 end end
      end
    elseif rel == 260 then
      storage.log = storage.log .. "step2 power: " .. STATUS[r.status] .. "\n"
      game.take_screenshot{surface = s, position = r.position, resolution = {600, 600}, zoom = 2, path = "status_2_power.png", show_entity_info = true, daytime = 0, force_render = true}
      r.fluidbox[1] = {name = "water", amount = 1000}; r.fluidbox[2] = {name = "crude-oil", amount = 1000}
      storage.refi = r
    else
      storage.log = storage.log .. "step3 power+fluids: " .. STATUS[r.status] .. "\n"
      game.take_screenshot{surface = s, position = r.position, resolution = {600, 600}, zoom = 2, path = "status_3_fluids.png", show_entity_info = true, daytime = 0, force_render = true}
    end
  elseif rel == 600 then
    helpers.write_file("shot_done.txt", "bbox " .. table.concat(storage.bbox, ",") .. "\n" .. (storage.log or ""), false)
    storage.done = true
  end
end)
