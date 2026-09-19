-- find out loader orientation semantics
local function setup()
  local s = game.create_surface("lab")
  s.generate_with_lab_tiles = true
  s.request_to_generate_chunks({0,0}, 3)
  s.force_generate_chunk_requests()
  storage.cases = {}
  local i = 0
  for _, sd in pairs({defines.direction.north, defines.direction.south}) do
    for _, kd in pairs({defines.direction.north, defines.direction.south}) do
      local x = i * 4
      -- belts flowing north from y=10 up to y=1
      for y = 1, 10 do s.create_entity{name="express-transport-belt", position={x+0.5, y+0.5}, direction=defines.direction.north, force="player"} end
      local src = s.create_entity{name="express-loader", position={x+0.5, 12}, direction=sd, type="output", force="player"}
      local chest = s.create_entity{name="steel-chest", position={x+0.5, 13.5}, force="player"}
      chest.insert{name="iron-plate", count=4000}
      local snk = s.create_entity{name="express-loader", position={x+0.5, 0}, direction=kd, type="input", force="player"}
      local out = s.create_entity{name="steel-chest", position={x+0.5, -1.5}, force="player"}
      storage.cases[#storage.cases+1] = {sd=sd, kd=kd, chest=chest, out=out, src=src, snk=snk}
      i = i + 1
    end
  end
end
script.on_init(setup)
script.on_nth_tick(600, function(e)
  if e.tick == 0 then return end
  local lines = {}
  for _, c in pairs(storage.cases) do
    lines[#lines+1] = string.format("src_dir=%d snk_dir=%d src_valid=%s snk_valid=%s src_left=%d sink_got=%d src_type=%s snk_type=%s",
      c.sd, c.kd, tostring(c.src and c.src.valid), tostring(c.snk and c.snk.valid), c.chest.get_item_count("iron-plate"), c.out.get_item_count("iron-plate"),
      c.src and c.src.valid and c.src.loader_type or "?", c.snk and c.snk.valid and c.snk.loader_type or "?")
  end
  helpers.write_file("smoke.txt", table.concat(lines, "\n") .. "\n", false)
end)
