-- where do items go for a splitter with the deconstruction-planner filter + output_priority?
local D = defines.direction
local V = {[D.north]={0,-1},[D.east]={1,0},[D.south]={0,1},[D.west]={-1,0}}
script.on_init(function()
  game.speed = 100
  local s = game.create_surface("lab"); s.generate_with_lab_tiles = true
  s.request_to_generate_chunks({0,0}, 6); s.force_generate_chunk_requests()
  storage.c = {}
  local i = 0
  for _, d in pairs({D.north, D.east, D.south, D.west}) do
    for _, pr in pairs({"left", "right"}) do
      local ox, oy = (i % 4) * 20 - 40, math.floor(i / 4) * 20 - 20
      local v = V[d]; local px, py = -v[2], v[1]           -- perpendicular (right-hand side when facing d) 
      -- splitter centre at (ox,oy); halves at +-0.5 along perpendicular
      local sp = s.create_entity{name="express-splitter", position={ox, oy}, direction=d, force="player"}
      sp.splitter_filter = {name="deconstruction-planner", quality="normal"}
      sp.splitter_output_priority = pr
      local rec = {d=d, pr=pr, sides={}}
      for _, side in pairs({-0.5, 0.5}) do
        local hx, hy = ox + px*side, oy + py*side
        -- input belts (3 tiles behind) fed by a chest+loader is complex: just put items by script each tick instead
        local inb = s.create_entity{name="express-transport-belt", position={hx - v[1], hy - v[2]}, direction=d, force="player"}
        local outb = s.create_entity{name="express-transport-belt", position={hx + v[1], hy + v[2]}, direction=d, force="player"}
        local outb2 = s.create_entity{name="express-transport-belt", position={hx + 2*v[1], hy + 2*v[2]}, direction=d, force="player"}
        rec.sides[#rec.sides+1] = {side=side, inb=inb, outb=outb2, count=0}
      end
      storage.c[#storage.c+1] = rec
      i = i + 1
    end
  end
end)
script.on_event(defines.events.on_tick, function(e)
  for _, rec in pairs(storage.c) do
    for _, sd in pairs(rec.sides) do
      for l = 1, 2 do
        local line = sd.inb.get_transport_line(l)
        if line.can_insert_at_back() then line.insert_at_back({name="iron-plate", count=1}) end
        local ol = sd.outb.get_transport_line(l)
        sd.count = sd.count + #ol; ol.clear()
      end
    end
  end
  if e.tick == 900 then
    local out = {}
    for _, rec in pairs(storage.c) do
      out[#out+1] = string.format("dir=%d prio=%s  side(-0.5 = left-hand? )=%d  side(+0.5)=%d", rec.d, rec.pr, rec.sides[1].count, rec.sides[2].count)
    end
    helpers.write_file("filt.txt", table.concat(out, "\n") .. "\n", false)
  end
end)
