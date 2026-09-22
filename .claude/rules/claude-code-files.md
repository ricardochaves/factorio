---
paths:
  - "**/.claude/CLAUDE.md"
  - "**/.claude/rules/**"
  - "**/.claude/agents/**"
  - "**/.claude/commands/**"
  - "**/.claude/skills/**"
---

# Claude Code files

These rules apply when you write or change the project's instructions, rules, subagents, commands or skills under `.claude/`.

- Always follow prompt best practices, and leave the whole text coherent: rewrite the affected part instead of patching it with an added sentence
- Each text has one home. `.claude/CLAUDE.md` holds what every session needs. A rule in `.claude/rules/` holds what matters only for some files and names them in `paths`: Claude Code loads it when a session reads a matching file, and, as observed on Claude Code 2.1.278, also into a review agent that reads one, so write each rule for the agent that changes the repository (the reviewers judge by it and never act on it). The rules that all the review agents share live in the skill `.claude/skills/review-ground-rules/SKILL.md`, which each agent preloads through its `skills` field, and an agent file holds only what is its own
- The review agents do not load CLAUDE.md or the rules at startup (`omitClaudeMd: true`, which needs Claude Code 2.1.271 or later), so every rule a reviewer needs lives in its agent file or in the shared skill. When a rule changes, update the agent files, the shared skill and `.claude/commands/add-blueprint.md` to match, in the same change
- Claude Code loads the subagents and skills from the `.claude/` folders between the session's working directory and the repository root, and picks up later edits only in the folders it watched from the start. A session that started in the main checkout keeps running the main checkout's reviewers after it enters a worktree (observed on Claude Code 2.1.278; the docs do not say that entering a worktree reloads them). So when the change edits or adds a file in `.claude/agents/` or `.claude/skills/`, run each affected reviewer as a `general-purpose` agent with `model: sonnet`, whose brief tells it to read the worktree's copy of its agent file and of `.claude/skills/review-ground-rules/SKILL.md` and to follow both, or start Claude Code inside the worktree
- When you test these agents, plant only inert defects in a scratch copy: a reviewer that runs a seeded script runs it on the real machine, so a seed never deletes, overwrites or downloads anything
- Restart Claude Code after `.claude/commands/add-blueprint.md` is created or edited: the docs promise live reload only for skills directories
