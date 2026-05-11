# Agent Coding Guidelines

A central repository of universal guidelines and best practices for agent-assisted development.
Extracted and generalized from real projects. Project-specific rules are excluded.

## What's Here

| File/Directory | Purpose |
|----------------|---------|
| `AGENTS.md` | Canonical entry point for Codex and Claude agents |
| `CLAUDE.md` | Thin pointer to AGENTS.md for Claude |
| `guidelines/workflow/` | Commit, documentation, and lifecycle rules |
| `guidelines/code/` | Code constraints and validation requirements |
| `guidelines/collaboration/` | Multi-agent setup and artifact placement |
| `techniques/` | Procedural patterns and operational guides |
| `skills/` | Claude Code skills (lazy-loaded by Claude Code at invocation, not eager-imported). Sync via `scripts/sync-skills.ps1` |
| `scripts/` | Repo maintenance scripts (skill sync, etc.) |

## How to Connect to Your Projects

**Option 1 — Global (all sessions on this machine):**
Add to `~/.claude/CLAUDE.md`:
```
@/path/to/agent_coding_guidelines/AGENTS.md
```

**Option 2 — Per project:**
Add to the project's `AGENTS.md`:
```
@/path/to/agent_coding_guidelines/AGENTS.md
```

**Option 3 — Project-local copy:**
For projects that need customized rules, the agent copies and adapts relevant sections
into the project's own `AGENTS.md`. The agent decides what to include based on project context.

## Using the Skills

Skills under `skills/` are Claude Code's lazy-loaded skill format (each skill = a directory with a `SKILL.md`). To install them locally:

```
pwsh ./scripts/sync-skills.ps1
```

This copies skill directories from `skills/` to `~/.claude/skills/` (Claude Code's personal-scope discovery location). The script is one-way (repo → local) and never deletes skills you've added manually to `~/.claude/skills/`.

Re-run after pulling repo updates to propagate skill changes.

## Adding New Content

1. **Guideline** (declarative rule): create a `.md` under the appropriate `guidelines/` subdirectory; add a `@` reference in `AGENTS.md`.
2. **Technique** (procedural pattern): create a `.md` under `techniques/`; add a `@` reference in `AGENTS.md`.
3. **Skill** (Claude Code skill): create `skills/<name>/SKILL.md` with frontmatter (`description` + `when_to_use`); add a line under AGENTS.md's Skills section; run the sync script.

Keep each file focused on one topic. See `AGENTS.md` for the full organization rules.
