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
| `skills/` | Agent Skills shared by Claude Code and Codex. Sync via `scripts/sync-skills.ps1` |
| `scripts/` | Repo maintenance scripts (skill sync, etc.) |

## How to Connect to Your Projects

Claude Code can import the canonical entry point globally or per project:

```text
# ~/.claude/CLAUDE.md or a project's AGENTS.md
@/path/to/agent_coding_guidelines/AGENTS.md
```

Codex discovers `AGENTS.md` but does not expand Claude Code's `@file` imports. Put an instruction like this in `~/.codex/AGENTS.md` or a project's `AGENTS.md`:

```text
Before working, read /path/to/agent_coding_guidelines/AGENTS.md and the applicable guideline files it references.
```

For projects that need customized rules, copy and adapt the relevant sections into the project's own `AGENTS.md`.

## Using the Skills

Skills under `skills/` use the shared Agent Skills format: each skill is a directory containing `SKILL.md` and optional resources or scripts. The repository is the source of truth.

The default command installs every skill for the current user on both platforms:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1
```

The targets are:

- Claude Code: `%USERPROFILE%\.claude\skills\<name>`
- Codex: `%USERPROFILE%\.agents\skills\<name>`

Limit installation to one platform with `-Targets`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1 -Targets Codex
```

Use `-ProjectPath` for project-level installation. The script writes `.claude\skills` and `.agents\skills` inside that project:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1 -ProjectPath E:\some_project
```

The script validates every skill before writing, replaces only same-named managed skills, and leaves unrelated target skills untouched. Re-run it after pulling repository updates. This installer currently supports Windows only.

## Adding New Content

1. **Guideline** (declarative rule): create a `.md` under the appropriate `guidelines/` subdirectory; add a `@` reference in `AGENTS.md`.
2. **Technique** (procedural pattern): create a `.md` under `techniques/`; add a `@` reference in `AGENTS.md`.
3. **Skill** (shared Agent Skill): create `skills/<category>/<name>/SKILL.md` with matching `name` and a self-contained `description`; add a line under AGENTS.md's Skills section; run the sync script.

Keep each file focused on one topic. See `AGENTS.md` for the full organization rules. Codex uses `description` for implicit skill discovery, so do not put required trigger information only in optional platform-specific metadata such as `when_to_use`.
