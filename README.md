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

## Adding New Guidelines

1. Create a `.md` file in the appropriate `guidelines/` subdirectory.
2. Add a `@` reference to it in `AGENTS.md`.
3. Keep each file focused on one topic.

See `AGENTS.md` for the full organization rules.
