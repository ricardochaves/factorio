---
paths:
  - "**/blueprints/**"
  - "**/scripts/ingame/**"
  - "**/scripts/run_*.sh"
---

# Blueprint entries

These rules apply when you add, correct or test an entry under `blueprints/`.

- You have access to the game: use it to validate every blueprint, and never skip that validation. Validating means at least the placement run of `scripts/run_blueprint_shot.sh` (the design imports and builds, and its shot report says how the design's poles were powered); the harness in `scripts/` measures what a design does, and only a measurement earns the test status `in-game`
- Every new blueprint entry gets exactly one image: a real screenshot from the game that shows the entire blueprint, powered (unless the design has no poles) and without any "not working" icon (a red circle with a bar across it). Take it yourself with `scripts/run_blueprint_shot.sh`, which builds the blueprint (it skips a pumpjack and an offshore pump, which need oil or water under them), powers it from a source outside the frame, wires that source to every pole group its reach leaves out, and frames it; or take it with a scenario of your own that does the same. For a book, the image shows its first blueprint. An entry already in the catalog keeps its images, unless a correction changes what they show: then the images that no longer match are replaced by new ones of the corrected design
- Finish the image in one go, without stopping to ask: choose the zoom and the framing yourself and carry the task through to the end, so that the owner gets the image and not a question. When `/add-blueprint` stops because the runner's photo cuts the build or frames it wrongly, take the photo with a scenario of your own. The review gates and the push gate still apply to what follows
- The rules live in the system's code (`scripts/catalog/validate.py` for the catalog): follow the business rules in the code
- When it is a blueprint where the output is only a single product, always calculate everything it consumes and everything it produces, in items per second, and document it in the three READMEs of the entry and in the blueprint's in-game description (in English, like every description in the catalog's strings)
- If you identify any incorrect information in the blueprints (in the string, in its label and description or in the READMEs), you must correct it: the whole point of importing them here is to fix things, not to accept whatever comes in. That holds for a design that someone else made: correct it, credit the original author in `credits` and say there what was corrected, and record each correction in the three READMEs
- `CONTRIBUTING.md` is written for third-party contributors, not for your work: do not follow it to the letter. Where it differs from these rules or the agent files (the state of the screenshot, the number of images, optional testing), they decide; the rest of it still applies
- `/add-blueprint <file.txt | file.json | url | pasted text> [--allow-duplicate]` (`.claude/commands/add-blueprint.md`) adds a new entry from a blueprint string and does the whole job that its file describes, in the three languages: it validates and photographs the design in the game, corrects what is wrong in it, writes the entry and runs the reviewers. It leaves to you the consumption and production rates of a single-product design (the rule above; calculate them before the push, and `blueprint-reviewer` accepts them as still to do only inside the command's run) and the commit, push and PR
