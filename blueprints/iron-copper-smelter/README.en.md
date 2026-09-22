# Iron/copper smelter

Iron or copper plate smelting in electric furnaces with productivity module 3, sped up by beacons with speed module 3. One line of ore on an express transport belt comes in from the south, and the line of plates leaves to the north.

- File: [`iron-copper-smelter.txt`](iron-copper-smelter.txt) — blueprint string; in-game, its name is `iron/copper smelter`.
- Origin: design by Nilaus, from the Master Class series (“Advanced Smelting (8 Beacon) 45 / sec output”), published by him in [this FactorioBin post](https://factoriobin.com/post/SnAX6v23) (blueprint book “Advanced Smelting - FACTORIO MASTER CLASS”). The post does not state a license. That book was saved in Factorio 1.0.0, before 2.0; this blueprint was saved and tested in Factorio 2.0.77. The blueprint is in the catalog with these credits and this link by decision of the repository owner. The credits also appear, in short form, on the site page.
- This is always the current version. Earlier versions are in the git history.

![The whole smelter at work, powered and fed with iron ore, captured in-game](images/overview.webp)

## What's inside

| Item | Value |
|---|---|
| Entities | 133 |
| Area | 13 × 47 tiles |
| Electric furnaces | 13 |
| Beacons | 31 |
| Fast inserters | 27 |
| Modules | 62 × `speed-module-3`, 26 × `productivity-module-3` |
| Medium electric poles | 16 |

The table lists the main parts. The rest are 24 express underground belts, 14 express transport belts, 7 lamps and 1 express splitter.

## Inputs and outputs

- Input: one line of ore on an express transport belt, in the east column (x 356.5), through the south edge, at (356.5, -246.5) in blueprint coordinates, heading north.
- Output: the line of plates leaves in the west column (x 352.5), four tiles to the left of the input, through the north edge, at (352.5, -292.5), heading north.
- Power: the medium electric poles are already wired to each other. Connect the electric network to any of them.
- No fuel: the furnaces are electric.

## Results measured in-game

Measured in Factorio 2.0.77 (base game, no mods), with the blueprint on grass, infinite iron ore coming in through the input line (the line stayed full) and the output line draining everything. Each research level had 18,000 ticks (5 min) of warm-up before being measured for 3,600 ticks (60 s), counting items with the game's production statistics and power by the drain on an energy buffer. In all three windows, the plates held in the furnace outputs stayed nearly stable (1,191 → 1,192, 293 → 278 and 208 → 207 plates), so the measured production is the throughput of the output line. Throughput depends on the inserter capacity bonus research (fast inserters are the only inserters in the blueprint), so there is one result per level:

| Research | Ore consumed | Plates produced | Electric power |
|---|---|---|---|
| None (bonus 0) | 27.75/s | 33.27/s | 29.8 MW |
| Inserter capacity bonus 2 (bonus +1) | 37.32/s | 44.75/s | 34.0 MW |
| Inserter capacity bonus 7 (bonus +2, the maximum) | 37.47/s | 44.95/s | 34.0 MW |

Plates come out 20% above the ore consumed, because of the productivity module 3s (2 per furnace, +10% each). With bonus +1 or +2, output reaches 44.75 and 44.95 plates/s, practically a full express transport belt (45/s). Only iron ore was measured, but copper has the same recipe in the game (1 ore into 1 plate, 3.2 s), so the copper numbers are the same.

## How it was tested

Tested in-game, as described above, in a scripted setup that differs from a player's build in four ways: the blueprint's ghost entities were built by script; the modules were inserted by script from the blueprint's item requests (construction with robots was not tested); the ore comes from an infinity chest through an express loader; and power comes from an electric energy interface connected to a big electric pole. The chest, the loader, the interface and the pole are outside the image: only the copper wire leaving through the bottom-left corner connects the blueprint to them. The scenario is `iron-copper-shot` (`scripts/ingame/data/scenarios/iron-copper-shot/control.lua`), run by `scripts/run_iron_copper_shot.sh`. The catalog validator also confirmed that the string is valid and uses only base-game items.

## How to test

With the game installed, in the `scripts/` folder: `./run_iron_copper_shot.sh` (with the `SteamAppId=427520` prefix if Steam is open without being logged in). You need the version with graphics, because the image is generated with the game's renderer. The script prints the measurements in the table above (in about 90 s) and regenerates `images/overview.webp`.

## Known limitations

- The description saved in the string that reached the catalog (pasted by the repository owner) said "Consumes 45/s" and "Produces 45/s" (a full express transport belt). The 45/s output is confirmed (44.95 plates/s at most), but the input is not: with +20% productivity, 45 plates/s need 37.5 ore/s, and the maximum measured was 37.47/s.
- That is why the catalog rewrote that description: it now credits Nilaus, includes the link and states 37.5/s input and 45/s output, with the measured values. The string's name (label) was not changed: it was already different from the design's name in the FactorioBin book. The rest of the string's decoded content is identical to that of the string that arrived (checked by script), and the corrected string was imported and measured in-game with the same results.
- An input line with less than 37.47 ore/s keeps the smelter below its maximum.
- Without the inserter capacity bonus research, output drops to 33.27 plates/s.
- The test used only one type of ore on the line (iron).
- The modules come as item requests in the blueprint: when pasting with robots, the logistic network needs 62 `speed-module-3` and 26 `productivity-module-3` in storage.
