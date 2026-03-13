# Commit Guidelines

## Granularity

- One commit = one clear theme. All changed files must serve the same purpose.
- Valid commit themes: feature addition, bug fix, refactor, doc update, governance change, chore.
- Do not mix unrelated themes in one commit.

## Timing

- Commit only at stable points: conclusion reached, code compiles, tests pass.
- Do not commit after every editing step.
- A session may produce zero, one, or multiple commits — each must stand on its own.

## Message Format

Use: `<type>: <subject>`

Allowed types: `feat`, `fix`, `refactor`, `docs`, `governance`, `chore`, `index`, `glossary`

- Subject describes the knowledge or feature increment, not the editing action.
- Prefer concise, single-theme subjects in the project's working language.
- Examples:
  - `feat: add patrol on-arrived callback`
  - `docs: document snapshot capture/apply mechanism`
  - `governance: establish commit and doc rules`

## Agent Behavior

- Do not commit unless the user explicitly requests it.
- Whether to commit agent collaboration docs (CLAUDE.md, AGENTS.md, conversation notes) is
  **project-dependent**. Some projects want agent rules tracked in git; others don't.
  Decide per project and document the choice in that project's AGENTS.md.

## Pre-Commit Checks

Before committing, confirm:
1. The commit has exactly one theme.
2. Stable conclusions are written into formal documents (not only present in chat).
3. The index file is updated if new documents were added.
4. The commit message clearly states the increment.
