# Task records and evidence — reference

Knowledge/reference material, not a required sequence or new state schema. Read
only when a task needs a record layout, recovery context or evidence-reuse guidance.

## Ownership and location

`guidelines/collaboration/private-docs-policy.md` is the canonical policy:
private execution logs, scratch notes and inter-agent handoffs stay outside the
project tree and are not committed. Project design/implementation plans and
progress notes may be tracked or private according to the project's convention
and the user's direction. A plan need not already be committed to qualify as a
project deliverable. Test fixtures/manual cases belong in the project test archive.

Reuse the existing location and layout. If new private records are useful, a
workspace sibling `_agent_private/<project>/handoffs/<task>/` is a portable choice.
Existing host-managed layouts can also be used:

| Host | Private state root | Project skill root |
|---|---|---|
| Claude Code | `~/.claude` | `<project>/.claude/skills` |
| Codex | `CODEX_HOME` when set, otherwise `~/.codex` | `<project>/.agents/skills` |

The private root and skill discovery root have different purposes. Do not invent
a project-directory mapping from a host's internal encoding. A date-prefixed task
name is a useful convention, not a prerequisite to working. Do not move or
reorganize ongoing records merely to match this example.

## Optional compact layout

For substantial work needing recovery, two records usually suffice:

- `brief.md`: task, scope, observable acceptance, decisions, delivery units,
  original Git baseline/status, ownership and relevant references.
- `worklog.md`: progress, actual commands/results, recurring failures, decisions
  and a final result. Append corrections to preserve the failure/decision history.

An existing plan, issue-linked record or four-file handoff can hold the same
information. Link to it rather than duplicating it. Include only relevant fields;
the names above do not prescribe a storage protocol or require new files.

When resuming, retain the original baseline and unresolved failure history.
Current checkout status is an additional observation, not a replacement baseline.
Use the approved milestone IDs where present, so records and user reports agree.

## Git baseline and ownership queries

These are read-only examples for a Git task, used when its baseline or change
attribution needs checking. At the start of a new task, retain both original
outputs in the existing task record:

```sh
git rev-parse HEAD
git status --short
```

On resumption, keep that original commit as `TASK_BASELINE` and preserve the
initial status; record the current status separately. Replace `<TASK_BASELINE>`
below with the recorded original commit before running the commands.

| Change category | List affected paths | Inspect relevant content |
|---|---|---|
| Committed since task start | `git diff --name-status <TASK_BASELINE>..HEAD` | `git diff <TASK_BASELINE>..HEAD` |
| Staged | `git diff --cached --name-status` | `git diff --cached` |
| Unstaged tracked | `git diff --name-status` | `git diff` |
| Untracked | `git ls-files --others --exclude-standard` | Read the relevant task-owned files; tracked diffs do not contain them |

These commands expose changes, not ownership. Compare them with the initial
status and recorded ownership decisions before attributing edits. Inspect the
necessary task-owned content in all four categories; do not reset the baseline,
exclude an entire pre-dirty file, or reread unrelated material just to repeat a
completed check.

## Evidence reuse

A reusable result identifies the command/procedure, observed outcome, tested source
(including uncommitted changes), artifact and relevant environment. Use content or
artifact identity appropriate to the project. Changed covered inputs require
targeted re-verification; a commit of the same content or an unrelated change does
not by itself invalidate the result. Untracked files and generated artifacts are
not established by a tracked-source diff alone.

A manual case should retain its fixture, steps, expected result and actual
observation in the project test archive. A private worklog can link to that record;
it must not become the only copy of a reusable project test.

## Why separate these concerns

A short phase description makes the current inputs and continuation decision
visible without loading every later procedure. Norm references identify where
authority comes from; record examples explain how to retain evidence. Neither
Markdown wording nor a saved "approved" label is a runtime permission boundary.
No scheduler, approval parser, new database or external workflow engine is assumed.
