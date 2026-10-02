# 40-reactor nuclear power plant

Nuclear power plant with 40 reactors in two columns of 20, 640 heat exchangers and 1,292 steam turbines that delivers up to 6,240 MW. Logistic robots bring the uranium fuel cells, and a circuit at the center of the south edge sends power to the base only while the base does not ask for more than the plant makes.

- File: [`nuclear-power-plant-40-reactors-v1.txt`](nuclear-power-plant-40-reactors-v1.txt) — blueprint string; in-game, its name is `Nuclear power plant - 40 reactors`.
- Origin: the repository owner's design, adapted from a ready-made design by an unknown author; a web search did not find the original author, so no license is known.
- This is always the current version. Earlier versions live in the git history.

![Overview, captured in-game](images/shot-1.webp)

## What's inside

| Item | Value |
|---|---|
| Entities | 8,574 |
| Area | 370 × 159 tiles |
| Heat pipe | 2,294 |
| Pipe | 2,137 |
| Pipe to ground | 1,321 |
| Steam turbine | 1,292 |
| Heat exchanger | 640 |

## Bill of materials

Everything the blueprint uses, counted by the catalog validator from the string:

| Item | Quantity |
|---|---|
| Heat pipe | 2,294 |
| Pipe | 2,137 |
| Pipe to ground | 1,321 |
| Steam turbine | 1,292 |
| Heat exchanger | 640 |
| Medium electric pole | 488 |
| Inserter | 80 |
| Storage tank | 68 |
| Pump | 66 |
| Roboport | 44 |
| Requester chest | 40 |
| Active provider chest | 40 |
| Nuclear reactor | 40 |
| Big electric pole | 19 |
| Accumulator | 2 |
| Decider combinator | 1 |
| Power switch | 1 |
| Solar panel | 1 |
| Concrete | 57,740 |
| Hazard concrete | 1,090 |

All four edges end in a one-tile strip of hazard concrete; right inside it, and across the rest of the floor, the ground is concrete, except for a 6 × 6 square of hazard concrete under the circuit.

## Inputs

- Water: 64 pipes to ground, 32 on the north edge and 32 on the south edge. Connect each one to a water source; at full power the plant needs about 6,430 units of water per second (calculated: 10.3 per second for each of the 624 heat exchangers needed for 6,240 MW).
- Fuel: 40 requester chests ask for 10 uranium fuel cells each; the logistic robots of the 44 roboports bring the cells, and the depleted uranium fuel cells leave through the 40 active provider chests. The blueprint brings no robots: the logistic network needs logistic robots, a chest with uranium fuel cells and a chest that takes the depleted cells.
- Base: connect the base only to the big electric pole at the center of the south edge, which sits after the power switch (see the next section).
- Start-up: a reactor gets fuel from its chest only after a depleted cell leaves it, so the plant does not start on its own. Put one uranium fuel cell by hand into each of the 40 reactors and connect a power source to one of the plant's poles (not to the output pole): the blueprint comes with the power switch open and the accumulators empty, and the steam pumps and inserters work only with power. In the test, the source stayed on for 20 minutes, until the plant's accumulator was full.

## How the plant saves fuel

In the base game, a reactor with fuel burns nonstop, even when nobody uses the heat. Here each reactor gets a new cell only after its depleted cell is taken out, and the 40 inserters that take out the depleted cells are wired with a green wire to a storage tank of the east column of tanks, near the south edge. Each pair of reactors has a threshold: the first is refueled only while that tank holds less than 24,000 units of steam, the next less than 23,000, and so on in steps of 1,000, down to 5,000 for the last pair. At low load the stored steam rises and only some reactors burn; all 40 burn together only with the tank below 5,000 units. That tank must stay in the steam network.

## How the circuit protects the plant

The pumps that carry steam from the tanks to the turbines and the inserters that put fuel into the reactors run on the plant's own power. If the base were on the same electric network and asked for more than the plant makes, the shortage would reach those pumps and inserters too: steam stops reaching the turbines, output drops, the shortage grows, and the plant collapses.

That is why the output to the base goes through a power switch at the center of the south edge:

- An accumulator on the plant's network reports its charge to the decider combinator over a red wire.
- The combinator closes the switch when the charge goes above 90% and keeps it closed while the charge is 50% or more; its own output signal goes back to its input over a green wire and holds that state.
- When the base asks for more than the plant makes, the accumulator drains; below 50%, the switch opens and the base loses power, while the plant keeps powering its pumps and inserters. Once the accumulator is back above 90%, the base gets power again.
- The combinator has its own electric network, with a medium electric pole, a solar panel and another accumulator, apart from the plant and the base.

Only the big electric pole after the switch has this protection. Connecting the base to any other pole of the plant joins the two networks and undoes the protection.

## Results measured in-game

Measured in Factorio 2.0.77 with this entry's corrected string. Each row is the average of 18,000 ticks (5 min), after 18,000 ticks (5 min) at the same load; power comes from the game's electric statistics; water, from its fluid statistics; and cells burned, from the average number of reactors burning, divided by 200 s (the life of one cell). The calculated maximum is 6,240 MW: 40 reactors of 40 MW with 116 neighbor bonuses of 100%.

| Load asked by the base (MW) | Delivered to the base (MW) | Cells burned | Water |
|---|---|---|---|
| 3,000 | 3,000 | 0.103/s | 3,177/s |
| 5,000 | 5,000 | 0.164/s | 5,099/s |
| 6,000 | 6,000 | 0.200/s | 6,194/s |
| 6,240 | 6,240 | 0.194/s | 6,232/s |
| 7,000, with the circuit | 6,062 on average | 0.199/s | 6,294/s |
| 7,000, without the circuit | 221 | 0/s | 228/s |

- Consumption at full power: 0.2 uranium fuel cells per second (12 per minute, one every 200 s per reactor) and about 6,430 units of water per second, calculated; the measurement at 6,240 MW gave 6,232/s because part of the steam came from the tanks. Idle, with no load, the plant uses about 2 MW for its own roboports.
- At 6,000 MW the reactors' temperature rose during the measurement (729 → 748 °C). At 6,240 MW it fell a little (760 → 752 °C), with 38.7 of the 40 reactors burning on average: the 6,240 MW held for the 10 minutes of the test with help from the stored steam. With 7,000 MW asked, the turbines generated 6,066 MW while the temperature rose, so the sustained output is close to 6,200 MW.
- With 7,000 MW asked and the circuit on, the switch opened three times in 5 minutes and stayed closed 93% of the time; the steam pumps had power in 91% of the samples, and the plant kept running.
- With the switch forced closed (without the circuit), the same 7,000 MW load collapsed the plant: the steam pumps lost power, no reactor got fuel, and delivery fell to 221 MW. With the load cut to 5,000 MW it stayed at 221 MW; it came back only when the load went to zero. With the circuit restored, the plant delivered 5,000 MW again.

## How it was tested

Three runs in the game. In the first, the catalog's photo runner imported and built the blueprint and connected it to a power source; 1 pole group was out of the power source's reach, and the test connected it with an added wire. The image comes from that run and shows the blueprint built, not running.

In the second, a test scenario made for this entry (not included in the repository) built the blueprint on a lab surface where it is always daytime, put infinite water on the 64 input pipes to ground, and stood in for the logistic robots: every second it topped each requester chest up to 10 uranium fuel cells and emptied the active provider chests. The scenario put one cell into each reactor and connected a temporary power source, removed before the measurements. In the third, with empty reactors, the same source and fuel in the chests, no reactor burned in 5 minutes; with one cell by hand in each reactor, the plant started and then refueled itself. The base was an adjustable electric load connected to the output big electric pole. The catalog validator confirmed that the string is valid and uses only base-game items (version 2.0.77).

## Corrections made here

- In the east column, the turbine row at y = −157.5 had no input pipe to ground at the edge: the 19 turbines of that row never got steam. The test of the original string confirmed it (1,273 of 1,292 turbines working); with the pipe to ground added, all 1,292 work.
- The string had no name and no description. Its name is now `Nuclear power plant - 40 reactors`, and the description, in English, gives the measured power and consumption, the inputs and how to connect the base.
- The original string is the one the repository owner provided; the rest of the decoded content is identical to it, checked by script.
- The in-game description was longer than the 500 bytes that the game keeps when it imports a string, and the game cut the rest without warning. It was shortened so that it fits in full (checked in-game); the details that were cut are in this report.

## Known limitations

- The edges use plain hazard concrete, not refined hazard concrete, by the repository owner's decision.
- The combinator's network depends on a solar panel and an accumulator; the test always ran in daylight, so its behavior at night was not measured.
- The logistic robots were not tested: the test put in and took out the fuel cells by script.
- If the requester chests run out of cells, the plant goes dark: in the test, with the chests emptied and a 5,000 MW load, all 40 reactors stopped and the steam pumps lost power; with 400 cells back in the chests, it stayed down for 5 minutes. It has to be started again, as the first time (that restart was not tested). Keep a stock of cells in the logistic network.
- A start without an external power source was not tested.
