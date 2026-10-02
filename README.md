# Factorio blueprints

My personal collection of blueprints for **vanilla Factorio 2.0** (base game, no Space Age), shared to help other
players. Each blueprint says how it was tested: see the *Tested* column below and the report on the blueprint's page.

Website: <https://ricardochaves.github.io/factorio/>, in Brazilian Portuguese, English (`/en/`) and Spanish (`/es/`).
Every blueprint can be copied from there with one click.

## Blueprints

<!-- catalog:start -->
| Blueprint | Category | What is inside | Files | Tested |
|---|---|---|---|---|
| [N × M belt balancers](blueprints/belt-balancers/) | Belts | 3 books, 1,731 blueprints | [`yellow-belt.txt`](blueprints/belt-balancers/yellow-belt.txt) · [`red-belt.txt`](blueprints/belt-balancers/red-belt.txt) · [`blue-belt.txt`](blueprints/belt-balancers/blue-belt.txt) | in game, 2.0.77 |
| [Stone brick smelter](blueprints/stone-brick-smelter/) | Mining & smelting | 73 entities, 11 × 29 tiles | [`stone-brick-smelter.txt`](blueprints/stone-brick-smelter/stone-brick-smelter.txt) | in game, 2.0.77 |
| [Iron/copper smelter](blueprints/iron-copper-smelter/) | Mining & smelting | 133 entities, 13 × 47 tiles | [`iron-copper-smelter.txt`](blueprints/iron-copper-smelter/iron-copper-smelter.txt) | in game, 2.0.77 |
| [Oil refinery](blueprints/oil-refinery/) | Oil processing | 9,899 entities, 193 × 129 tiles | [`oil-refinery.txt`](blueprints/oil-refinery/oil-refinery.txt) | in game, 2.0.77 |
| [Low density structure factory](blueprints/low-density-structure-factory/) | Production | 255 entities, 20 × 34 tiles | [`low-density-structure-factory.txt`](blueprints/low-density-structure-factory/low-density-structure-factory.txt) | in game, 2.0.77 |
| [40-reactor nuclear power plant](blueprints/nuclear-power-plant-40-reactors-v1/) | Power | 8,574 entities, 370 × 159 tiles | [`nuclear-power-plant-40-reactors-v1.txt`](blueprints/nuclear-power-plant-40-reactors-v1/nuclear-power-plant-40-reactors-v1.txt) | in game, 2.0.77 |
| [40-reactor nuclear power plant with solar panels and accumulators](blueprints/nuclear-power-plant-40-reactors-v2/) | Power | 8,809 entities, 370 × 159 tiles | [`nuclear-power-plant-40-reactors-v2.txt`](blueprints/nuclear-power-plant-40-reactors-v2/nuclear-power-plant-40-reactors-v2.txt) | in game, 2.0.77 |
| [100 × 100 robot-only city block, partial concrete](blueprints/city-block-100x100-partial-concrete/) | City blocks | 120 entities, 100 × 100 tiles | [`city-block-100x100-partial-concrete.txt`](blueprints/city-block-100x100-partial-concrete/city-block-100x100-partial-concrete.txt) | in game, 2.0.77 |
| [100 × 100 robot-only city block, full concrete](blueprints/city-block-100x100-full-concrete/) | City blocks | 120 entities, 100 × 100 tiles | [`city-block-100x100-full-concrete.txt`](blueprints/city-block-100x100-full-concrete/city-block-100x100-full-concrete.txt) | in game, 2.0.77 |
<!-- catalog:end -->

This table is generated from each folder's `blueprint.toml` and the blueprint strings themselves. Every folder has a
README, in Portuguese (`README.md`), English (`README.en.md`) and Spanish (`README.es.md`), with what was
measured, how it was built and known limits.

## How to import

1. Get the file's text: the **Copy** button on the website, or on GitHub **Copy raw file** (or **Download raw file** and
   open it). The balancer books are 3 to 6 MB of text, too large to select by hand; on the website each balancer and
   each sub-book can also be copied on its own.
2. In the game, press **Import string** in the shortcut bar (or in the blueprint library) and paste. That shortcut
   requires the Construction robotics technology, unless you have researched it in another save (a shortcut that is
   unlocked in one save stays unlocked in later ones).

Each file is always the latest version. Older versions live in the git history:

```
git log -p -- blueprints/oil-refinery/oil-refinery.txt
```

## Contributing

Want to add or improve a blueprint? [CONTRIBUTING.md](CONTRIBUTING.md) explains how to add one, preview the website
and get a pull request merged.

## License

The code and the blueprints made in this repository are released under the [MIT License](LICENSE). Some parts come
from elsewhere and keep their own terms:

- Balancer designs taken from Raynquist's balancer book: that repository does not state a license (see Credits below).
- The iron/copper smelter in [`blueprints/iron-copper-smelter/`](blueprints/iron-copper-smelter/), a design by Nilaus:
  the FactorioBin post it links to does not state a license (see Credits below).
- The 40-reactor nuclear power plant in
  [`blueprints/nuclear-power-plant-40-reactors-v1/`](blueprints/nuclear-power-plant-40-reactors-v1/): the repository
  owner's adaptation of a design by an unknown author, with no known license (see Credits below).
- The fonts in [`site/static/fonts/`](site/static/fonts/): SIL Open Font License, with the license files next to them.
- The item, fluid, recipe and entity names in [`scripts/catalog/vanilla-locale.json`](scripts/catalog/vanilla-locale.json)
  and the prototype data in [`scripts/catalog/vanilla-prototypes.json`](scripts/catalog/vanilla-prototypes.json), both
  extracted from the game: Factorio's own data, © Wube Software.
- The in-game screenshots in `blueprints/*/images/`: they show Factorio's graphics, © Wube Software.

## Credits

- Several balancers come from, or are built from blocks of, **Raynquist's balancer book**
  (<https://github.com/raynquist/balancer>). That repository does not state a license; its designs are credited here and
  each blueprint's in-game description says where it came from.
- The iron/copper smelter is a design by **Nilaus**, from his Master Class series
  ("Advanced Smelting (8 Beacon) 45 / sec output"). The credit links to the FactorioBin post that holds the design, the
  book "Advanced Smelting - FACTORIO MASTER CLASS" (<https://factoriobin.com/post/SnAX6v23>), which does not state a
  license; Nilaus lists that post on his own page,
  [Factorio - Master Class Blueprints](https://nilaus.atlassian.net/wiki/spaces/PM/pages/2852782081/Factorio+-+Master+Class+Blueprints).
  The entities, positions and modules of the book's first blueprint are identical to the catalog's blueprint, which has
  its own name in the game and an in-game description written for this catalog (credit, link and figures). The book was
  saved in Factorio 1.0.0, before 2.0; the catalog's copy is saved and tested in 2.0.77. It is published here with
  credit and the link although the source states no license; Nilaus can ask for its removal by opening an issue.
- The 40-reactor nuclear power plant is the repository owner's adaptation of a ready-made design whose author is
  unknown; a web search did not find the original author, so no license is known. It is published here by the owner's
  decision, with the corrections listed in the entry's README
  ([Corrections made here](blueprints/nuclear-power-plant-40-reactors-v1/README.en.md#corrections-made-here)). Its
  original author can ask for credit or for its removal by opening an issue.
- [tzwaan/factorio_balancers](https://github.com/tzwaan/factorio_balancers) (MIT) was used as an independent checker.
  It is not redistributed here.

The tools used to generate and test the blueprints are in [`scripts/`](scripts/).
