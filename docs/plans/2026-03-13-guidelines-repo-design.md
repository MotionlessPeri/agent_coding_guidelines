# Design: Agent Coding Guidelines Repository

**Date:** 2026-03-13
**Status:** Approved

## Goal

A central repository that records universal agent-development guidelines and experience extracted from real projects. Serves two purposes:

1. **Global background knowledge** — agents across all projects share a consistent set of behavioral defaults.
2. **Project bootstrap template** — new projects can reference or adapt the guidelines as a starting point.

## Repository Structure

```
agent_coding_guidelines/
├── CLAUDE.md                          ← thin pointer to AGENTS.md
├── AGENTS.md                          ← canonical entry; imports all guideline files
├── README.md                          ← human-readable index and access instructions
│
└── guidelines/
    ├── workflow/
    │   ├── commits.md                 ← commit granularity, message format, timing
    │   ├── documentation.md           ← doc structure, sync rules, splitting rules
    │   └── agent-lifecycle.md         ← autonomous actions, build/restart, validation
    ├── code/
    │   ├── constraints.md             ← hard behavioral constraints
    │   └── validation.md              ← build verification, "done" criteria
    └── collaboration/
        ├── multi-agent.md             ← CLAUDE.md/AGENTS.md single-source pattern
        └── private-docs-policy.md     ← agent artifact placement policy
```

### Meta-rule: How to Extend This Repo

- New guidelines go into the appropriate subdirectory under `guidelines/`.
- If a new topic does not fit any existing category, create a new subdirectory.
- Every new file must be referenced in `AGENTS.md`.
- Keep each file focused on one topic. Split if a file covers 3+ independent concerns or exceeds ~200-300 lines.
- Document organization rules live in `AGENTS.md` itself so agents can self-navigate.

## Entry Files

### CLAUDE.md
A single-line pointer:
```
@AGENTS.md
```
Plus a note: "Single-source policy: maintain only AGENTS.md."

### AGENTS.md
- Imports all `guidelines/` files via `@` references.
- Contains the meta-section on how this repo is organized and how to extend it.
- Describes the three access patterns (see below).

## Agent Access Patterns

**Option 1 — Global config (recommended for universal rules)**
Write a reference into `~/.claude/CLAUDE.md` so all Claude sessions load the guidelines automatically. Codex equivalent: `~/.codex/AGENTS.md` if supported.

**Option 2 — Per-project import**
Add to a project's `AGENTS.md`:
```
@E:/xd_projects/agent_coding_guidelines/AGENTS.md
```
Use this when the project wants the guidelines tracked alongside it, or when the global config is not available.

**Option 3 — Project-local copy (manual, agent-driven)**
For projects that need a customized or trimmed version, the agent copies and adapts the relevant sections into the project's own `AGENTS.md`. No script — the agent decides what to include based on project context and requirements.

## Guidelines Content Summary

Extracted from three real projects (`unreal-mcp`, `beizermotioninbetween`, `AIPointBuild_5_5_4`, `UE_arpg_server_investigate`). Only universal patterns are included; project-specific content (build commands, file paths, API conventions) is excluded.

### workflow/commits.md
- One commit = one clear theme
- Commit only at stable points (not after every edit)
- `<type>: <subject>` message format; subject describes the increment, not the editing action
- Do not commit unless user explicitly requests it
- Whether to commit agent collaboration docs is project-dependent — decide and document per project

### workflow/documentation.md
- Update docs immediately when new code understanding is gained — do not wait for user prompt
- Conclusions before details
- Structured knowledge over transcript-style notes
- Split documents that cover 3+ independent topics or exceed ~200-300 lines
- Register every new document in the index in the same work step

### workflow/agent-lifecycle.md
- Read mandatory docs in specified order before starting any task
- Verify build/tests pass before claiming work is complete — evidence before assertions
- Agent may autonomously: save/close editor → rebuild → restart (when plugin code changes require it)
- Actions that affect shared state or are hard to reverse require user confirmation first

### code/constraints.md
- Avoid silent success: surface actionable errors when preconditions are not met
- Every commit must leave the repo in a usable state
- Understand architecture before modifying code; read relevant docs first

### code/validation.md
- Run build verification before reporting completion
- For tool/command additions: validate both the implementation layer and the interface layer
- For blueprint/graph commands: validate against a real test asset, check logs for errors

### collaboration/multi-agent.md
- `AGENTS.md` is the canonical instruction file for both Claude and Codex
- `CLAUDE.md` is a thin pointer to `AGENTS.md` — maintain only one rule set
- If the two files conflict, `AGENTS.md` wins
- Conflict resolution order: chat instructions < repo docs; if docs conflict, earlier in reading list wins

### collaboration/private-docs-policy.md
- Agent debug logs and temporary scratch files belong outside the project tree (e.g. a sibling `_agent_private/` directory)
- Progress notes placement is project-dependent — in-tree (committed during active work, cleaned up after) or out-of-tree; document the choice in `AGENTS.md`

## Language

All guideline files are written in English.

## Source Projects

Guidelines were extracted and generalized from:
- `e:/xd_projects/unreal-mcp` — hard constraints, validation baseline, autonomous lifecycle
- `e:/xd_projects/beizermotioninbetween` — doc-sync rules, commit conventions, architecture-first principle
- `h:/Perforce/AIPointDemo/TestProj/AIPointBuild_5_5_4` — single-source CLAUDE/AGENTS pattern, private docs policy
- `e:/xd_projects/UE_arpg_server_investigate` — doc hierarchy, writing rules, commit governance
