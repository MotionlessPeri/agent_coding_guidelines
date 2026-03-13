# Private Docs Policy

## What Belongs Out of the Project Tree

Keep the following **outside** the project directory (e.g. in a sibling `_agent_private/<project>/` directory):

- Agent debug logs
- Temporary analysis scratch files
- One-off investigation notes
- MCP/tool-generated artifacts not relevant to the codebase

This keeps the project clean for sharing, export, and code review.

## What Is Project-Dependent

**Progress notes** (task tracking, implementation plans, refactoring progress):
- May stay **in-tree** and be committed during active work, then removed in a cleanup commit.
- Or may go **out-of-tree** if you prefer to keep the repo pristine.
- Document the project's choice in its `AGENTS.md`.

**Agent collaboration docs** (CLAUDE.md, AGENTS.md, conversation guides):
- Whether to commit these to git is project-dependent.
- Some projects want agent rules tracked in git (portable, version-controlled).
- Others prefer to keep them local-only.
- Document the project's choice in its `AGENTS.md`.

## Recommended Directory Layout

```
<workspace>/
├── MyProject/                  ← shared project tree (clean)
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   └── src/
└── _agent_private/
    └── MyProject/
        ├── docs/               ← agent progress notes, proposals
        └── artifacts/          ← generated files, debug logs
```

## Export Policy

If the project is shared or exported (e.g. as a sample), exclude agent-related files
by default. Only include AGENTS.md / CLAUDE.md if the recipient explicitly needs them.
