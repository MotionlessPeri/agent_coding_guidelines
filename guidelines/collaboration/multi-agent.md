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

Follow the host's instruction hierarchy. Repository documents and skills cannot
raise their own authority above system or developer instructions. Within user
instructions, the user's current explicit request takes precedence over older
repository defaults; reading order does not create authority.

Fix doc inconsistencies in the same change when possible.

## Task-Specific Reading

Each project's `AGENTS.md` should map task types to relevant documents. Do not
require the whole list before every task. Example:

```markdown
## Task-Specific Reading

- Read README.md when setup or project purpose is unclear.
- Read Docs/Architecture.md when changing subsystem boundaries.
- Read Docs/Progress.md when resuming the work it tracks.
```

## Accessing This Guidelines Repository

Three patterns, in order of preference:

**Option 1 — Global config**
In `~/.claude/CLAUDE.md`, Claude Code supports an import (replace the path with
the actual absolute path on this machine):
```
@<absolute-guidelines-root>/AGENTS.md
```
Codex does not expand `@path` imports. In `~/.codex/AGENTS.md`, give an explicit
reading instruction instead:

```text
Read <absolute-guidelines-root>/AGENTS.md, then only its references applicable
to the current task. Do not reread unchanged material already in context.
```

The global instruction is discovered by the host; the referenced content is
loaded by the agent's subsequent reads. These are different context costs.

**Option 2 — Per-project import**
Use the same explicit reading instruction in the project's `AGENTS.md` for
cross-platform access. A Claude-only project may use the import form above.
Use when the project wants guidelines tracked alongside it, or when global config is unavailable.

**Option 3 — Project-local copy (agent-driven)**
For projects that need a customized or trimmed version, the agent copies and adapts the
relevant sections into the project's own `AGENTS.md`. The agent decides what to include
based on project context. No script required.
