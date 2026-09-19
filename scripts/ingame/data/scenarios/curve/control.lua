-- does a side feed onto a north-facing belt behave as a curve (full belt) or as a sideload (one lane)?
local D = defines.direction
local function B(s, x, y, d) return s.create_entity{name="express-transport-belt", position={x+0.5, y+0.5}, direction=d, force="player"} end
script.on_init(function()
  game.speed = 100
  local s = game.create_surface("lab"); s.generate_with_lab_tiles = true
  s.request_to_generate_chunks({0,0}, 10); s.force_generate_chunk_requests()
  storage.c = {}
  local cases = {"belt_side_nothing_behind", "splitter_side_nothing_behind", "ug_side_nothing_behind",
                 "belt_side_idle_belt_behind", "splitter_side_idle_splitter_behind", "splitter_side_idle_belt_behind", "ug_side_idle_splitter_behind",
                 "splitter_side_idle_ugout_behind", "belt_side_idle_ugin_behind", "splitter_side_idle_ugin_behind"}
  for i, mode in pairs(cases) do
    local ox, oy = (i - 1) * 14 - 70, 0
    -- target column: x = ox+6, flows north from y=0 up to y=-6, sink on top
    for y = 0, -6, -1 do B(s, ox+6, y, D.north) end
    s.create_entity{name="express-loader", position={ox+6.5, -7}, direction=D.north, type="input", force="player"}
    local out = s.create_entity{name="steel-chest", position={ox+6.5, -8.5}, force="player"}
    -- feeder coming from the west along y=0, source = loader facing east at x=ox..ox+1
    local chest = s.create_entity{name="steel-chest", position={ox-0.5, 0.5}, force="player"}; chest.insert{name="iron-plate", count=4800}
    s.create_entity{name="express-loader", position={ox+1, 0.5}, direction=D.east, type="output", force="player"}
    if mode:find("^belt_side") then for x = ox+2, ox+5 do B(s, x, 0, D.east) end
    elseif mode:find("^splitter_side") then
      for x = ox+2, ox+4 do B(s, x, 0, D.east) end
      s.create_entity{name="express-splitter", position={ox+5.5, 0}, direction=D.east, force="player"}   -- tiles y=-1 and y=0 ; y=-1 half faces (ox+6,-1): also a side feed
    else
      B(s, ox+2, 0, D.east)
      s.create_entity{name="express-underground-belt", position={ox+3.5, 0.5}, direction=D.east, type="input", force="player"}
      s.create_entity{name="express-underground-belt", position={ox+5.5, 0.5}, direction=D.east, type="output", force="player"}
    end
    if mode:find("idle_belt_behind") then B(s, ox+6, 1, D.north)
    elseif mode:find("idle_splitter_behind") then s.create_entity{name="express-splitter", position={ox+7, 1.5}, direction=D.north, force="player"}
    elseif mode:find("idle_ugin_behind") then s.create_entity{name="express-underground-belt", position={ox+6.5, 1.5}, direction=D.north, type="input", force="player"}
    elseif mode:find("idle_ugout_behind") then s.create_entity{name="express-underground-belt", position={ox+6.5, 1.5}, direction=D.north, type="output", force="player"} end
    storage.c[i] = {mode=mode, chest=chest, out=out, probe=s.find_entity("express-transport-belt", {ox+6.5, 0.5})}
  end
end)
script.on_nth_tick(600, function(e)
  if e.tick == 1200 then for _, c in pairs(storage.c) do c.o0 = c.out.get_item_count(); c.out.clear_items_inside(); c.o0 = 0 end end
  if e.tick == 3000 then
    local out = {}
    for _, c in pairs(storage.c) do
      out[#out+1] = string.format("%-40s delivered=%4d of 1350  belt_shape=%s", c.mode, c.out.get_item_count(), tostring(c.probe.belt_shape))
    end
    helpers.write_file("curve.txt", table.concat(out, "\n") .. "\n", false)
  end
end)
