-- throughput / input fairness of a 2->1 splitter: naturally blocked output vs filter-blocked output (belt passing in front)
local D = defines.direction
local function lane(s, x, y0, y1, d) for y = y0, y1, (y1 >= y0) and 1 or -1 do s.create_entity{name="express-transport-belt", position={x+0.5, y+0.5}, direction=d, force="player"} end end
local function src(s, x, y) local l = s.create_entity{name="express-loader", position={x+0.5, y+1}, direction=D.north, type="output", force="player"}
  local c = s.create_entity{name="steel-chest", position={x+0.5, y+2.5}, force="player"}; c.insert{name="iron-plate", count=4800}; return c end
local function snk(s, x, y) s.create_entity{name="express-loader", position={x+0.5, y}, direction=D.north, type="input", force="player"}
  return s.create_entity{name="steel-chest", position={x+0.5, y-1.5}, force="player"} end
script.on_init(function()
  game.speed = 100
  local s = game.create_surface("lab"); s.generate_with_lab_tiles = true
  s.request_to_generate_chunks({0,0}, 6); s.force_generate_chunk_requests()
  storage.c = {}
  for i, mode in pairs({"natural", "filter", "filter_supply_one", "natural_supply_one"}) do
    local ox = i * 12 - 30
    lane(s, ox, 5, 2, D.north); lane(s, ox+1, 5, 2, D.north)             -- two inputs, y=5..2
    local sp = s.create_entity{name="express-splitter", position={ox+1, 1.5}, direction=D.north, force="player"}
    lane(s, ox, 0, -3, D.north)                                             -- left output continues north
    if mode:find("filter") then
      -- an unrelated belt passing east in front of the right output
      for x = ox+1, ox+4 do s.create_entity{name="express-transport-belt", position={x+0.5, 0.5}, direction=D.east, force="player"} end
      sp.splitter_filter = {name="deconstruction-planner", quality="normal"}; sp.splitter_output_priority = "right"
    end
    local a, b = src(s, ox, 6), src(s, ox+1, 6)
    if mode:find("supply_one") then b.clear_items_inside() end
    storage.c[i] = {mode=mode, a=a, b=b, out=snk(s, ox, -4), side=(mode:find("filter") and s.find_entity("express-transport-belt", {ox+4.5, 0.5}) or nil)}
  end
end)
script.on_nth_tick(600, function(e)
  if e.tick == 0 then return end
  if e.tick == 1200 then for _, c in pairs(storage.c) do c.a0=c.a.get_item_count(); c.b0=c.b.get_item_count(); c.o0=c.out.get_item_count() end end
  if e.tick == 3000 then
    local out = {}
    for _, c in pairs(storage.c) do
      local leak = 0
      if c.side then leak = #c.side.get_transport_line(1) + #c.side.get_transport_line(2) end
      out[#out+1] = string.format("%-20s usedA=%d usedB=%d out=%d (1800 ticks, full belt = 1350) leaked_on_side_belt=%d", c.mode, c.a0-c.a.get_item_count(), c.b0-c.b.get_item_count(), c.out.get_item_count()-c.o0, leak)
    end
    helpers.write_file("filt2.txt", table.concat(out, "\n") .. "\n", false)
  end
end)
