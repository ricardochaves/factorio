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
- You have access to the game: use it to validate the blueprints whenever possible
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
- Reviewers do not load this file (`omitClaudeMd: true`): when a rule here changes, update the agent files to match.
- When you test these agents, plant only inert defects in a scratch copy: a reviewer that runs a seeded script runs it on the real machine, so a seed never deletes, overwrites or downloads anything.

## Deploy
Every time you merge into `main`, run `deploy-validator` to monitor the deployment and validate it:
- It opens the website and checks that everything in the diff really works
- It is not enough for a change to exist in the code: if the CSS changes, check transparency, positioning, and the mobile and desktop layouts. Be careful, and look at the validator's screenshots yourself when the CSS changed.

## Blueprints

- Always add images to the blueprint: take real in-game screenshots so that every page of a blueprint has a realistic image. The blueprint must have power and everything else it needs, to avoid the "not working" icon (a red circle with a bar across it) shown when it does not work. The photos that `scripts/run_blueprint_shot.sh` takes for `/add-blueprint` show the build placed and, where its power source reaches the poles, powered, with no ingredients fed to the machines, and it takes them without alt mode (`show_entity_info = false`), so they carry no status icon. Check the image before pushing
- The rules live in the system's code: follow the business rules in the code
- When it is a blueprint where the output is only a single product, always calculate everything it consumes and everything it produces, and document this in both the blueprint and the website. The unit of measurement is items per second.
- Run `blueprint-reviewer` on every blueprint change
- `/add-blueprint <file.txt | file.json | url | pasted text>` (`.claude/commands/add-blueprint.md`) adds a new entry from a blueprint string. It photographs the whole build in the game itself (`scripts/run_blueprint_shot.sh`) and never asks for a screenshot; it stops before any commit or push; `--allow-duplicate` adds a second copy of a design the catalog already holds
- Claude Code needs a restart after `.claude/commands/add-blueprint.md` is created or edited, because live reload is documented for `.claude/skills/` only

## Website

- Always support 3 languages: pt-BR, en-US and es
- Before pushing anything to GitHub, run `language-reviewer` as the table above defines it for the change, and fix what it reports
