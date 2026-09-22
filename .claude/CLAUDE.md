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
- Write commit titles and PR titles in English and for players: the site shows them, in every language, in each blueprint's history (the commit title, or the PR title when the PR has several commits). Name a blueprint by its `[en] title`

## Rules
- The rules of one area live in `.claude/rules/` and load when you read a file that they cover: `blueprints.md` (the entries under `blueprints/` and their in-game validation), `site.md` (the site and its three languages) and `claude-code-files.md` (the instructions, rules, subagents, commands and skills under `.claude/`). Read the rule of an area before you create files there, because a rule loads only when a file that it covers is read
- Always use stable technologies
- Every review agent whose row in the table below matches the change must approve its final state before you push anything to GitHub or report the work as done: their approval is a gate. Passwords and tokens must never be pushed, and nothing is pushed unless `security-reviewer` approves the final tree
- Follow every finding of every reviewer, MINOR and NIT findings included, also a finding about something the change did not touch: the reviewers are not here to play around, so take each finding seriously. A finding from `security-reviewer` is never out of scope. Dispute a finding only with evidence, to the same reviewer, and reach a conclusion together; when the reviewer keeps the finding, follow it
- Create a virtual environment to install libraries; never install them on the host. Always use the virtual environment if it exists

## Review agents

The reviewers live in `.claude/agents/`, and the rules that all of them share in the skill `.claude/skills/review-ground-rules/SKILL.md`, which each one preloads. None of them has Edit, Write or Agent, and each prompt forbids changing the repository and running the code under review, but all of them have Bash, and four also read web pages (`blueprint-reviewer` holds WebFetch and WebSearch; `docs-reviewer`, `prompt-reviewer` and `claude-code-reviewer` hold WebFetch), so the guarantee is the prompt plus your own check, not the tool list. Each one runs on Sonnet with the effort set in its own file and ends its English review report with `VERDICT: APPROVE` or `VERDICT: REQUEST CHANGES`.

| Agent | Run it when the change touches |
|---|---|
| `security-reviewer` | anything: it runs last, on the final tree, before every push or PR update |
| `frontend-reviewer` | `site/`, or anything the site shows (a blueprint entry, `scripts/bp.py`, `scripts/catalog/`) |
| `language-reviewer` | text that the site shows, including the README templates and fixed sentences in the Reference section of `.claude/commands/add-blueprint.md`, which become the text of every new entry: one instance per language whose text the change adds or edits, in parallel. Every visible text exists in the three languages, so new or rewritten text needs the three instances, and only a fix to one language's wording needs just that one |
| `docs-reviewer` | a README (root or `scripts/`), CONTRIBUTING, anything under `.claude/` (instructions, rules, agents, commands, skills), workflows or repository settings. The catalog table that `scripts/catalog/validate.py --readme` generates in the root README does not count, because CI checks it |
| `blueprint-reviewer` | a blueprint entry: its string, `blueprint.toml`, images or READMEs |
| `code-reviewer` | code under `scripts/`, the in-game harness or the CI workflows (the site generator is `frontend-reviewer`'s) |
| `prompt-reviewer` | a command, a subagent prompt, a skill, a rule or `.claude/CLAUDE.md`: it checks the wording against Anthropic's prompting best practices |
| `claude-code-reviewer` | anything under `.claude/`: it checks frontmatter, tool grants and claims about Claude Code against the current docs |
| `deploy-validator` | a merge into `main`: it runs after the merge, and the deploy is done only when it approves |

How to use them:
- Start each reviewer with the Agent tool, using the `name` from its frontmatter (its file name without `.md`) as `subagent_type`. Do not pass the Agent tool's own `name`, `model` or `isolation` parameters. A named call launches a teammate when agent teams are enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), and a teammate takes the lead's `effort` and loads CLAUDE.md; an in-process teammate also appends the body to the default system prompt instead of replacing it. `model` overrides the file's `model: sonnet`, and `isolation` branches the worktree from the default branch, so the reviewer would not see the uncommitted work. As observed, a teammate spawn says `Spawned successfully` in the Agent tool's result, names a mailbox and gives an `agent_id` of the form `<name>@session-...`, where an ordinary subagent's result says `Async agent launched successfully` and gives a bare hexadecimal `agentId`: if you see the first form, stop that agent and start it again without a name. A change can need several reviewers: run every one that matches, in parallel, and `security-reviewer` after the others' fixes.
- Brief each reviewer narrowly, because it reads whatever the brief leaves open. Give the worktree path; the change, as the merge base with `origin/main` plus the commits after it, the uncommitted work and the untracked files (`/add-blueprint` leaves a new entry untracked); the files of its lane that changed; the built site (`build/site`) when it matters; and the deliberate decisions that are not defects. Each reviewer's file states its lane and its budget of tool calls, and the shared skill the rule that it inspects only the change and what the change can affect, running any whole-project check as a script; `frontend-reviewer` and `deploy-validator` also map the changed files to the pages, languages and widths to check. Reviewers cannot ask questions, and given an empty change the reviewers of a change answer `REQUEST CHANGES` (`deploy-validator` works from the merge commit instead).
- Discuss a finding you dispute with the same reviewer, resumed with SendMessage addressed to the agent ID the Agent tool returned. With several `language-reviewer` instances, note which agent ID took which language.
- Every change made after a review, even a small one, goes back to the reviewer that asked for it, with the earlier findings listed (ID, path, one line each) and the commit of its last verdict. Resume the reviewer with SendMessage for its first two rounds, also to finish a report that came back partial or cut off by an API error; a resumed reviewer carries its whole transcript, so after two rounds start a fresh instance of the same agent with the same brief and the findings instead. Push only when the latest state has `VERDICT: APPROVE`, and run `security-reviewer` again on the final tree right before the push.
- A reviewer must leave the tree untouched: check `git status --short --ignored` after each review, and again before you push.

## Deploy
Every time a PR is merged into `main`, run `deploy-validator` with the merge commit and what the PR should change on the live site, to monitor the deployment and validate it:
- It checks what the merge changed and nothing more: the workflow runs of the merge commit, and every visible or behavioral item of the merged diff on the pages, languages and widths that its file maps the changed files to
- It is not enough for a change to exist in the code: if the CSS changes, it checks transparency, positioning, and the mobile and desktop layouts. Be careful, and look at the validator's screenshots yourself when the CSS changed.
