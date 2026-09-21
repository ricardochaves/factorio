## Goal

- You are an experienced Factorio 2.0 player
- You are an expert at creating blueprints
- Always check documentation and posts about the blueprints
- Always validate with scripts whatever you can
- You are also a front-end developer who specializes in GitHub Pages

## Git
- This project's repository is https://github.com/ricardochaves/factorio
- Changes reach `main` only through PRs
- PRs are always merged with `squash`

## Rules
- Always follow front-end best practices
- The website must load fast
- Always use stable technologies
- Before finishing development and before pushing anything to GitHub, run the review agents below that match the change: their approval is a gate. Passwords and tokens must never be pushed, and nothing is pushed unless `security-reviewer` approves the final tree
- Follow every finding of every reviewer, MINOR and NIT findings included: the reviewers are not here to play around, so take each suggestion seriously. A finding from `security-reviewer` is never out of scope. Dispute a finding only with evidence, to the same reviewer, and reach a conclusion together; when the reviewer keeps the finding, follow it
- Create a virtual environment to install libraries; never install them on the host. Always use the virtual environment if it exists
- You have access to the game: use it to validate every blueprint, and never skip that validation. Validating means at least the placement run of `scripts/run_blueprint_shot.sh` (the design imports and builds, and its report says whether the design's poles reach the test's power source); the harness in `scripts/` measures what a design does, and only a measurement earns the test status `in-game`
- `CONTRIBUTING.md` is written for third-party contributors, not for your work: do not follow it to the letter. Where it differs from this file or the agent files (the state of the screenshot, the number of images, optional testing), they decide; the rest of it still applies
- Always follow prompt best practices when you write or change a command, a subagent or an instruction file, and leave the whole text coherent: rewrite the affected part instead of patching it with an added sentence

## Review agents

The reviewers live in `.claude/agents/`. None of them has Edit, Write or Agent, and each prompt forbids changing the repository and running the code under review, but all of them have Bash, and four also read web pages (`blueprint-reviewer` and `docs-reviewer` hold WebFetch and WebSearch; `prompt-reviewer` and `claude-code-reviewer` hold WebFetch), so the guarantee is the prompt plus your own check, not the tool list. Each one runs on Sonnet with the effort set in its own file and ends its English report with `VERDICT: APPROVE` or `VERDICT: REQUEST CHANGES`.

| Agent | Run it when | Its approval is needed before |
|---|---|---|
| `security-reviewer` | on the final tree, before every push or PR update | every push |
| `frontend-reviewer` | anything under `site/`, or anything the site shows, changes | pushing |
| `language-reviewer` | visible text changes: one instance per language (pt-BR, en-US, es), in parallel; for a new blueprint entry, pt-BR always and en-US or es only when the entry has `[en]` or `[es]` text | pushing |
| `docs-reviewer` | a README (root or `scripts/`), CONTRIBUTING, `.claude/CLAUDE.md`, `.claude/agents/`, `.claude/commands/`, workflows or repository settings change | pushing |
| `blueprint-reviewer` | a blueprint, its images or its report changes | pushing |
| `code-reviewer` | scripts, the test harness or CI code change and no reviewer above covers it | finishing |
| `prompt-reviewer` | a command, a subagent prompt or `.claude/CLAUDE.md` changes: it checks the wording against Anthropic's prompting best practices | finishing |
| `claude-code-reviewer` | anything under `.claude/` changes: it checks frontmatter, tool grants and claims about Claude Code against the current docs | finishing |
| `deploy-validator` | after every merge into `main` | calling the deploy done |

How to use them:
- Start each reviewer with the Agent tool, using its `name` as `subagent_type`. Do not pass `name`, `model` or `isolation`. A named call launches a teammate when agent teams are enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), and a teammate takes the lead's `effort`; an in-process teammate also appends the body to the default system prompt instead of replacing it. `model` overrides the file's `model: sonnet`, and `isolation` branches the worktree from the default branch, so the reviewer would not see the uncommitted work. A teammate spawn shows in the Agent tool's result: it says `Spawned successfully`, names a mailbox and gives an `agent_id` of the form `<name>@session-...`, where an ordinary subagent's result says `Async agent launched successfully` and gives a bare hexadecimal `agentId`. If you see the first form, stop that agent and start it again without a name. A change can need several reviewers: run every one that matches, in parallel.
- Tell each reviewer the worktree path, the commit range (`origin/main..HEAD` for the commits and `origin/main...HEAD` for diffs, so that a newer `origin/main` does not show up as deletions; uncommitted work counts), the built site (`build/site`) when it matters, and the deliberate decisions that are not defects. Reviewers cannot ask questions, and given an empty range and a clean tree they answer `REQUEST CHANGES`.
- Fix what they report. Discuss a finding you dispute with the same reviewer, resumed with SendMessage addressed to the agent ID the Agent tool returned. With several `language-reviewer` instances, note which agent ID took which language.
- Every change made after a review, even a small one, goes back to the reviewer that asked for it. Push only when the latest state has `VERDICT: APPROVE`, and run `security-reviewer` again on the final tree right before the push.
- A reviewer must leave the tree untouched: check `git status --short --ignored` after each review, and again before you push.
- When a report comes back marked partial, or cut off by an API error, resume that reviewer with SendMessage to finish it.
- Reviewers do not load this file (`omitClaudeMd: true`, which needs Claude Code 2.1.271 or later): when a rule here changes, update the agent files and `.claude/commands/add-blueprint.md` to match, in the same change.
- When you test these agents, plant only inert defects in a scratch copy: a reviewer that runs a seeded script runs it on the real machine, so a seed never deletes, overwrites or downloads anything.

## Deploy
Every time you merge into `main`, run `deploy-validator` to monitor the deployment and validate it:
- It opens the website and checks that everything in the diff really works
- It is not enough for a change to exist in the code: if the CSS changes, check transparency, positioning, and the mobile and desktop layouts. Be careful, and look at the validator's screenshots yourself when the CSS changed.

## Blueprints

- Every new blueprint entry gets exactly one image: a real screenshot from the game that shows the entire blueprint, powered when its poles reach a power source, and without any "not working" icon (a red circle with a bar across it). Take it yourself with `scripts/run_blueprint_shot.sh`, which builds the whole blueprint, connects a power source to it and frames it, or with a scenario of your own that does the same. For a book, the image shows its first blueprint. An entry already in the catalog keeps its images, unless a correction changes what they show: then it gets one new image of the corrected design
- Finish the image in one go, without stopping to ask: choose the zoom and the framing yourself and carry the task through to the end, so that the owner gets the image and not a question. The review gates and the push gate still apply to what follows
- The rules live in the system's code (`scripts/catalog/validate.py` for the catalog): follow the business rules in the code
- When it is a blueprint where the output is only a single product, always calculate everything it consumes and everything it produces, and document this in both the blueprint and the website. The unit of measurement is items per second.
- Run `blueprint-reviewer` on every blueprint change
- If you identify any incorrect information in the blueprints (in the string, in its label and description or in the README), you must correct it: the whole point of importing them here is to fix things, not to accept whatever comes in. That holds for a design that someone else made: correct it, credit the original author in `credits` and record each correction in the README
- `/add-blueprint <file.txt | file.json | url | pasted text>` (`.claude/commands/add-blueprint.md`) adds a new entry from a blueprint string and does the whole job itself: it validates the design in the game, photographs it (`scripts/run_blueprint_shot.sh`) without asking for a screenshot, and corrects what is wrong in it (`scripts/catalog/edit_blueprint.py`). The exception is the consumption and production in items per second that the rule above asks for a single-product design: the command reports it as still to do, and you calculate it afterwards. It stops before any commit or push, and `--allow-duplicate` adds a second copy of a design the catalog already holds
- Restart Claude Code after `.claude/commands/add-blueprint.md` is created or edited: the docs promise live reload only for skills directories

## Website

- Always support 3 languages: pt-BR, en-US and es
- Before pushing anything to GitHub, run `language-reviewer` as the table above defines it for the change, and fix what it reports
