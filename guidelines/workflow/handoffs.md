# Handoff Workflow Guidelines

## Purpose

- Keep the main chat focused on analysis, task selection, and acceptance.
- Keep execution details in durable handoff documents instead of long chat threads.
- Make task boundaries explicit when work is split across a planning chat and an execution chat.

## Roles

- The main chat owns analysis, decomposition, acceptance, and promotion of accepted results into durable project docs.
- The sub-chat owns execution of one bounded task package.

## Recommended Structure

When a project uses a main-chat / sub-chat workflow, prefer a dedicated handoff directory such as:

```text
docs/handoffs/
  <task-slug>/
    brief.md
    context.md
    worklog.md
    result.md
```

The exact path may vary by project, but the role split should stay the same.

## Required Task Documents

### `brief.md`

Defines:

- what the task must do
- what it must not do
- expected inputs
- expected outputs
- acceptance criteria

### `context.md`

Provides only the minimum background the execution chat needs:

- relevant files
- constraints
- current state
- known risks

### `worklog.md`

Append-only execution log that records:

- meaningful work chunks
- modified files
- verification steps
- current blockers or risks

### `result.md`

Final handoff back to the main chat that records:

- conclusion
- files changed
- verification run
- known limitations
- recommended next step

## Main Chat Rules

- Create the task package before handing work to a sub-chat.
- Keep the task bounded. One active package is better than a broad mixed brief.
- Do not start the next task until the current package's `result.md` has been reviewed.
- Promote accepted conclusions from the handoff package into the project's durable docs.

## Sub-Chat Rules

- Read the active task package before acting.
- Stay within the boundaries in `brief.md`.
- Update `worklog.md` after each meaningful work chunk.
- Write `result.md` before claiming completion in chat.
- Do not treat handoff docs as the final knowledge base.

## Promotion Rule

- Handoff docs are transport artifacts, not the final source of truth.
- Once the main chat accepts a result, the project must sync durable conclusions into formal docs such as research docs, specs, plans, or indexes.

## Project Integration

- If a project adopts this workflow, document the chosen handoff directory and task-file conventions in that project's `AGENTS.md`.
- If the project already has progress-log rules, the handoff workflow should extend them rather than replace them.
