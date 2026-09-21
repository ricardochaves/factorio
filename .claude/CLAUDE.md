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
- Always fix the problems the review brings up; discuss them with the reviewer and reach a conclusion together
- Create a virtual environment to install libraries; never install them on the host. Always use the virtual environment if it exists
- You have access to the game: use it to validate every blueprint, and never skip that validation
- The reviewers are not here to play around: take every suggestion seriously. A finding from `security-reviewer` is never out of scope and must be followed, MINOR and NIT findings included, unless you refute it with evidence to that same reviewer
- `CONTRIBUTING.md` is written for third-party contributors, not for your work: do not follow it to the letter, and let this file and the agent files decide where they differ from it
- Always follow prompt best practices when you write or change a command, a subagent or an instruction file, and leave the whole text coherent: rewrite the affected part instead of patching it with an added sentence

## Review agents

The reviewers live in `.claude/agents/`. None of them has Edit, Write or Agent, and each prompt forbids changing the repository and running the code under review, but all of them have Bash, and four also read web pages (`blueprint-reviewer` and `docs-reviewer` hold WebFetch and WebSearch; `prompt-reviewer` and `claude-code-reviewer` hold WebFetch), so the guarantee is the prompt plus your own check, not the tool list. Each one runs on Sonnet with the effort set in its own file and ends its English report with `VERDICT: APPROVE` or `VERDICT: REQUEST CHANGES`.

| Agent | Run it when | Its approval is needed before |
|---|---|---|
| `security-reviewer` | on the final tree, before every push or PR update | every push |
| `frontend-reviewer` | anything under `site/`, or anything the site shows, changes | pushing |
| `language-reviewer` | visible text changes: one instance per language (pt-BR, en-US, es), in parallel; for a new blueprint entry, pt-BR always and en-US or es only when the entry has `[en]` or `[es]` text | pushing |
| `docs-reviewer` | the README, CONTRIBUTING, `.claude/CLAUDE.md`, `.claude/agents/`, workflows or repository settings change | pushing |
| `blueprint-reviewer` | a blueprint, its images or its report changes | pushing |
| `code-reviewer` | scripts, the test harness or CI code change and no reviewer above covers it | finishing |
| `prompt-reviewer` | a command, a subagent prompt or `.claude/CLAUDE.md` changes: it checks the wording against Anthropic's prompting best practices | finishing |
| `claude-code-reviewer` | anything under `.claude/` changes: it checks frontmatter, tool grants and claims about Claude Code against the current docs | finishing |
| `deploy-validator` | after every merge into `main` | calling the deploy done |

How to use them:
- Start each reviewer with the Agent tool, using its file name as `subagent_type`. Do not pass `name`, `model` or `isolation`. A named call launches a teammate when agent teams are enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), and a teammate takes the lead's `effort`; an in-process one also appends the body to the default system prompt instead of replacing it. `model` overrides the file's `model: sonnet`, and `isolation` branches the worktree from the default branch, so the reviewer would not see the uncommitted work. A teammate spawn shows in the Agent tool's result: it says `Spawned successfully`, names a mailbox and gives an `agent_id` of the form `<name>@session-...`, where an ordinary subagent's result says `Async agent launched successfully` and gives a bare hexadecimal `agentId`. If you see the first form, stop that agent and start it again without a name. A change can need several reviewers: run every one that matches, in parallel.
- Tell each reviewer the worktree path, the commit range (`origin/main..HEAD`; uncommitted work counts), the built site (`build/site`) when it matters, and the deliberate decisions that are not defects. Reviewers cannot ask questions, and given an empty range and a clean tree they answer `REQUEST CHANGES`.
- Fix what they report. Discuss a finding you dispute with the same reviewer, resumed with SendMessage addressed to the agent ID the Agent tool returned, until you agree; a finding is withdrawn only with evidence. With several `language-reviewer` instances, note which agent ID took which language.
- Every change made after a review, even a small optional one, goes back to the reviewer that asked for it. Push only when the latest state has `VERDICT: APPROVE`, and run `security-reviewer` again on the final tree right before the push.
- A reviewer must leave the tree untouched: check `git status --short --ignored` after each review, and again before you push.
- When a report comes back marked partial, or cut off by an API error, resume that reviewer with SendMessage to finish it.
- Reviewers do not load this file (`omitClaudeMd: true`): when a rule here changes, update the agent files and `.claude/commands/add-blueprint.md` to match, in the same change.
- When you test these agents, plant only inert defects in a scratch copy: a reviewer that runs a seeded script runs it on the real machine, so a seed never deletes, overwrites or downloads anything.

## Deploy
Every time you merge into `main`, run `deploy-validator` to monitor the deployment and validate it:
- It opens the website and checks that everything in the diff really works
- It is not enough for a change to exist in the code: if the CSS changes, check transparency, positioning, and the mobile and desktop layouts. Be careful, and look at the validator's screenshots yourself when the CSS changed.

## Blueprints

- Every new blueprint entry gets exactly one image: a real screenshot from the game that shows the entire blueprint, powered and without any "not working" icon (a red circle with a bar across it). Open the game and take it yourself, and change the zoom until the whole blueprint fits. For a book, the image shows its first blueprint. Entries already in the catalog keep the images they have
- Finish the image without stopping to ask: choose the zoom and the framing yourself and carry the task through to the end. The review gates and the push gate still apply to what follows
- The rules live in the system's code: follow the business rules in the code
- When it is a blueprint where the output is only a single product, always calculate everything it consumes and everything it produces, and document this in both the blueprint and the website. The unit of measurement is items per second.
- Run `blueprint-reviewer` on every blueprint change
- If you identify any incorrect information in the blueprints (in the string, in its label and description or in the README), you must correct it: the whole point of importing them here is to fix things, not to accept whatever comes in. That holds for a design that someone else made: correct it, credit the original author in `credits` and record each correction in the README
- `/add-blueprint <file.txt | file.json | url | pasted text>` (`.claude/commands/add-blueprint.md`) adds a new entry from a blueprint string and does the whole job itself: it validates the design in the game, photographs it (`scripts/run_blueprint_shot.sh`) without asking for a screenshot, and corrects what is wrong in it (`scripts/catalog/edit_blueprint.py`). It stops before any commit or push, and `--allow-duplicate` adds a second copy of a design the catalog already holds
- Claude Code needs a restart after `.claude/commands/add-blueprint.md` is created or edited, because live reload is documented for `.claude/skills/` only

## Website

- Always support 3 languages: pt-BR, en-US and es
- Before pushing anything to GitHub, run `language-reviewer` as the table above defines it for the change, and fix what it reports
