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

## GitHub Remote Protocol and Push Authority

- On this machine, use GitHub remotes through the user's existing SSH key. Do not invent or switch to an HTTPS remote, and do not trigger Git Credential Manager or browser login.
- Push only to an already configured remote for which the user has write authority. An upstream repository is not a writable destination merely because it is the local checkout's `origin`.
- If a required fork or writable remote does not exist, do not guess a fork URL or attempt the push. Ask the user to create the fork and provide its SSH remote, or leave the commit local when pushing is unnecessary.

## Pre-Commit Checks

Before committing, confirm:
1. The commit has exactly one theme.
2. Stable conclusions are written into formal documents (not only present in chat).
3. The index file is updated if new documents were added.
4. The commit message clearly states the increment.
