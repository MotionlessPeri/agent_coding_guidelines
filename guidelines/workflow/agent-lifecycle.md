# Agent Lifecycle Guidelines

## Before Starting Any Task

1. Read the mandatory documents in the order specified by the project's AGENTS.md.
2. Confirm which subsystem or component is being changed before touching code.
3. If the project has a progress/plan document, check current state before proceeding.

## Autonomous Actions (Permitted Without User Confirmation)

The agent may perform the following autonomously when required by the task:

- Save and close the editor before a rebuild.
- Run a cold rebuild (compile) after plugin or C++ code changes.
- Restart the editor/server after a rebuild.
- Stage files and create commits **only when the user has explicitly requested a commit**.

## Actions Requiring User Confirmation

Always confirm with the user before:

- Force-pushing or resetting git history.
- Deleting files, branches, or database tables.
- Pushing to a remote repository.
- Creating or closing issues/PRs.
- Any action visible to others or affecting shared infrastructure.

If in doubt, ask first. The cost of asking is low; the cost of an unwanted action is high.

## Validation Before Completion

- Never claim work is "done" or "fixed" without running verification.
- Evidence before assertions: run the build, run the tests, check the logs.
- If build or tests fail, diagnose and fix — do not report completion.
- For tool/command additions: verify both the implementation layer and interface layer.

## Handling Blockers

- If an approach is blocked, do not retry the same action in a loop.
- Consider alternative approaches or ask the user for direction.
- Do not use destructive actions (e.g., `--no-verify`, `reset --hard`) as shortcuts.

## Common Failure Modes

Agent self-deception patterns to watch for:

### Execution Failures

| Excuse | Truth | Correct Action |
|--------|-------|----------------|
| "Code looks correct" | Reading code is not verification | Run it |
| "Probably fine" | "Probably" is not evidence | Verify it |
| "This would take too long" | Not your call — inform the user of estimated time, then do it | Inform and proceed |
| "Let me read the code first" | May be procrastinating action | Run a command directly |

### Quality Failures

| Excuse | Truth | Correct Action |
|--------|-------|----------------|
| "Tests already pass" | Tests can be self-referential | Verify independently |
| "This edge case is unlikely" | Anything can happen in production | Handle it or document why not |
| "Refactoring is too big, leave it for now" | Tech debt does not resolve itself | At minimum, record a TODO |
| "I'll add docs/comments later" | "Later" usually means never | Do it now |

### Delegation Failures

| Excuse | Truth | Correct Action |
|--------|-------|----------------|
| "Let the worker figure it out" | Avoiding synthesis work | Understand first, then give precise instructions |
| "Based on earlier research" | Worker cannot see earlier context | Provide complete information |

## Failure Escalation

- First failure: retry once with a focused fix based on the error.
- Second failure: change approach entirely — do not repeat the same strategy.
- Third failure: report to the user with a summary of what was tried and why each approach failed.
- Never let a failing approach loop more than three times.

## Related Techniques

- See `techniques/coordination-patterns.md` for multi-agent coordination and worker failure handling.
- See `techniques/worker-instructions.md` for writing effective sub-agent prompts.
