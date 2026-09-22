# Stone brick smelter

A blueprint that turns stone into stone bricks: eight electric furnaces with productivity module 3, surrounded by eighteen beacons with speed module 3. It is fed by a full express transport belt of stone and delivers the bricks on another express transport belt.

- File: [`stone-brick-smelter.txt`](stone-brick-smelter.txt) — blueprint string; in-game, its name is `Stone smelter`.
- This is always the current version. Earlier versions are in the git history.

![The whole smelter, with all eight electric furnaces running between the beacons, captured in-game](images/overview-all-working.webp)

## What's inside

| Item | Value |
|---|---|
| Entities | 73 |
| Area | 11 × 29 tiles |
| Electric furnaces (`electric-furnace`) | 8 |
| Beacons (`beacon`) | 18 |
| Modules | 36 × `speed-module-3`, 16 × `productivity-module-3` |
| Fast inserters (`fast-inserter`) | 8 |
| Bulk inserters (`bulk-inserter`) | 8 |

## Inputs and outputs

The blueprint has one input and one output, both on express transport belts running north (blueprint coordinates, unrotated):

- Input: stone, at the south end of the right-hand column. Connect a belt that carries only stone: no inserter in the blueprint has a filter, so if another item the furnaces accept is on the belt, nothing stops the inserters from putting it into the furnaces.
- Output: stone bricks, at the north end of the left-hand column (the output express underground belt).
- Power: the blueprint does not include power generation. The substation (`substation`) at the south end is the connection point to the electric network.
- Modules: they come as item requests (36 × `speed-module-3` and 16 × `productivity-module-3`); they must be delivered by robots or inserted by hand.

## Consumption and production

In items per second, with the input belt full and every technology researched:

| Items per second | Calculated | Measured in-game |
|---|---|---|
| Stone consumed | 45 | 44.93 |
| Stone bricks produced | 27 | 26.95 |

The consumption of 45/s is the limit of an express transport belt. Production comes from 45 ÷ 2 × 1.2: 2 stone make 1 brick, and the 2 productivity module 3s in each furnace add up to 20%. The output is 60% of an express transport belt. The electric power measured in this regime is 20.53 MW.

## Results measured in-game

Automated test in Factorio 2.0.77 without graphics (scenario `smelter-test`): a belt of stone that is always full (infinity chest and express loader), the output draining and power coming from an electric energy interface, with 60 s of warm-up and 60 s of measurement. Electric power is read after that: the electric energy interface stops producing and the test measures, for 10 s, how much of the interface's buffer the blueprint consumes. The test runs on two surfaces at the same time: with every technology researched and with none.

| Metric | All technologies | No technologies |
|---|---|---|
| Stone consumed | 44.93/s | 21.83/s |
| Stone bricks produced | 26.95/s | 13.12/s |
| Working time of the last furnace in the row | 53.9% | 47.8% |
| Working time of the other seven furnaces | 93.4% to 100% | 43.1% to 47.6% |
| Electric power | 20.53 MW | 15.12 MW |

With no technology researched, at the end of the measurement the eight bulk inserters were working and four furnaces had no ingredients: the limit becomes those inserters, and output drops to 13.12/s.

## How it was tested

In-game test, with the `smelter-test` scenario: 17 checks, all passed.

- The string imports without errors, and the game reads its name and description.
- The 73 entities and the 52 modules match the string, counted from the decoded JSON.
- A single electric network connects the blueprint to the power source, and no machine is left without power.
- The full belt results in the consumption and production calculated above, and all furnaces work.

The main image was captured in-game, with graphics, in a lab scenario with the blueprint built, powered and fed, at the moment when all eight furnaces were running. This capture scenario is not part of the repository.

The catalog validator also confirmed that the string is valid and uses only base-game items (version 2.0.77).

## How to test

To run the test on macOS, with Factorio installed through Steam (the tested version is 2.0.77), from the repository root:

```
scripts/run_smelter_test.sh
```

The script exports the string, runs the scenario without graphics (the server only listens on 127.0.0.1) and exits with code 0 only if every check passes. It is written in zsh; to use a different executable path, set the `FACTORIO_BIN` variable (more details in [scripts/README.md](../../scripts/README.md)).

## Known limitations

- The blueprint needs researched technologies: with none, output drops to 13.12 bricks/s. The test does not isolate which technology makes the difference.
- The last furnace in the row, the northern one, at the end of the stone belt, only gets the stone that is left over: with every technology researched, it worked 53.9% of the time, against 93.4% to 100% for the other seven.
- The blueprint does not include power generation; at full production, it consumes 20.53 MW.
