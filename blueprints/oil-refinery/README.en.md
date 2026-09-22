# Oil refinery

A single blueprint of a complete refinery for Factorio 2.0.77, base game (no Space Age).

- File: [`oil-refinery.txt`](oil-refinery.txt) — blueprint string; in-game, its name is `refinaria v3 (plastic feed + acid water)`.
- This is always the current version. Earlier versions are in the git history (`git log -p -- blueprints/oil-refinery/`).

![Refinery overview](images/overview.webp)

## What's inside

| Item | Value |
|---|---|
| Entities | 9,899 |
| Area | 193 × 129 tiles |
| Oil refineries (`advanced-oil-processing`) | 36 |
| Chemical plants | 416 |
| Assembling machine 3 | 54 |
| Beacons | 162 |
| Modules | 1,300 × `speed-module-3`, 570 × `productivity-module-3` |
| Pumps / storage tanks | 163 / 38 |
| Roboports | 11 |

Production (machines per recipe): plastic bar 96, solid fuel 120 (from light oil) + 34 (from petroleum gas),
rocket fuel 48, battery 40, sulfur 39, sulfuric acid 12, lubricant 13,
light oil cracking 41 and heavy oil cracking 17, explosives 2, flamethrower ammo 2, and barrels.

Each plastic block has 48 chemical plants (1 `speed-module-3` + 2 `productivity-module-3`, no beacon) and consumes 1,152 petroleum gas/s.

## Inputs

The blueprint has 9 external inputs, all on the south edge (blueprint coordinates):

- Crude oil: 2 pipes to ground, at (-275.5, 499.5), which runs through the tanks, and at (-273.5, 499.5), straight to the west bank,
  and the east bank line (x between -176.5 and -120.5). **Connect both pipes to ground.** The 36 refineries only reach 100%
  with both; with only the first one, the west bank runs at 54–75%. With everything connected, the refineries consume 3,604/s of
  crude oil (measured).
- Water: 5 pipes to ground at y = 499.5 (x from -271.5 to -267.5) and the east bank line (x between -174.5 and -115.5).

## Results measured in-game

Automated test in headless Factorio 2.0.77, with infinite sources only at the 9 external inputs (so the internal inlet
pumps are exercised), every output draining and every item supplied:

| Metric | Result |
|---|---|
| Refineries | 100.0% (36/36) |
| Sulfuric acid | 89%, 0% of the time without water (9% with the output full) |
| Batteries | 100% |
| Water tanks of the acid block | 60% |
| Water delivered | 5,018/s |
| Crude oil consumed | 3,604/s |

In other regimes: with surplus gas at the producers, or with only plastic draining, the 96 plastic plants run at 100%.

## Known limitations

- With everything consuming, gas demand (~4,800/s) exceeds production (~2,160/s + light oil cracking). Result: plastic 49%,
  sulfur 66% and solid fuel from gas 0%. It is not a pump bottleneck; it is the production balance.
- In that scarce regime, the two plastic blocks have the same priority (`petroleum-gas > 95000`); solid fuel
  from gas (`> 97000`) gets less.

## History

Future changes are in the git history. Summary of the versions before it:

- **v3 — doubled water in the sulfuric acid block** (22 entities, 2 wires). Two pumps parallel to the existing ones:
  P1 next to the pump at (-116.5, 485), which carries water from the east bank to the block's branch, and P2 next to the pump at (-127, 453.5),
  which fills the block's water tank (condition `water < 23500`, green wire to the tank). Sulfuric acid went from 66% to 89%,
  batteries from 81% to 100%, water delivered from 4,619/s to 5,018/s.
- **v2 — gas feed for the right-hand plastic block** (7 new entities, 2 changed, 3 wires). The right-hand block only
  received gas through one pump with the condition `petroleum-gas > 99000`, and the tanks sat at ~97k: in the scarce regime it stopped
  (0%) while the left-hand one stayed at 100%. Two parallel pumps with `> 95000`, the same as the left-hand block, and a medium electric pole.
- **Original** — the base blueprint both changes started from.

Each change was verified with the fluid model (no segment gained any pipe or connection beyond the intended ones, no overlapping
tile) and in-game (0 segments with mixed fluids).

## How to test

From the repository root (requires Factorio installed; see [`scripts/README.md`](../../scripts/README.md)):

```
python3 scripts/fluid/make_full_test.py scripts/ingame/data/scenarios/fluid-test/tests.lua atual-inlet=blueprints/oil-refinery/oil-refinery.txt
./scripts/run_fluid.sh 600 && python3 scripts/fluid/balance.py
```

The label suffix selects the regime: `-inlet` (sources only at the external inputs), `-surplus` (infinite gas at the producers),
`-plasticonly` (only plastic drains); with no suffix, real production.
