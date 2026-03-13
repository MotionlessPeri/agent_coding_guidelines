# Multi-Agent Collaboration

## Single-Source Policy

- Use `AGENTS.md` as the canonical instruction file for both Claude and Codex.
- `CLAUDE.md` should be a thin pointer:
  ```markdown
  @AGENTS.md

  > Single-source policy: this file imports AGENTS.md. Maintain only AGENTS.md.
  ```
- Do not maintain two separate rule sets. If the files ever conflict, `AGENTS.md` wins.

## Conflict Resolution Order

When instructions conflict, apply this precedence (lower = higher authority):
1. Chat/session instructions (lowest)
2. Project repo documents
3. Earlier document in the project's mandatory reading list (highest among docs)

Fix doc inconsistencies in the same change when possible.

## Mandatory Reading

Each project's `AGENTS.md` should specify a mandatory reading list — an ordered list of
documents the agent must read before starting any task. Example:

```markdown
## Read Before Work

1. README.md
2. Docs/Architecture.md
3. Docs/Progress.md
```

## Accessing This Guidelines Repository

Three patterns, in order of preference:

**Option 1 — Global config**
Add to `~/.claude/CLAUDE.md` (Claude) or `~/.codex/AGENTS.md` (Codex):
```
@E:/xd_projects/agent_coding_guidelines/AGENTS.md
```
All sessions on this machine load the guidelines automatically.

**Option 2 — Per-project import**
Add to the project's `AGENTS.md`:
```
@E:/xd_projects/agent_coding_guidelines/AGENTS.md
```
Use when the project wants guidelines tracked alongside it, or when global config is unavailable.

**Option 3 — Project-local copy (agent-driven)**
For projects that need a customized or trimmed version, the agent copies and adapts the
relevant sections into the project's own `AGENTS.md`. The agent decides what to include
based on project context. No script required.
