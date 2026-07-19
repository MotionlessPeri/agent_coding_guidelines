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

### What "change approach" actually means

A new approach must be in a **different layer**, not just a different API in the
same layer. Same-layer API switching is still the same approach — repeating it
just burns the failure budget without buying new information.

Concrete examples of layers (the boundaries are domain-dependent; the point is
each line below is "below" the one above it, with different mechanisms / contracts):

| Layer | Examples of being "in this layer" |
|-------|-----------------------------------|
| UI / widget customization | `IDetailCustomization`, `SClassPropertyEntryBox`, custom Slate widgets, React component re-renders |
| Property handle / proxy API | `IPropertyHandle::SetValue` / `SetValueFromFormattedString` / `SetInstanceMetaData` |
| Data type / schema | `UPROPERTY` declared type, struct fields, type hierarchy, ORM column types |
| Framework reflection contract | UHT-generated metadata, `FProperty::MetaClass`, decorators, annotations |
| Domain logic / business rules | Where conditions / constraints / semantics live |

**Anti-pattern (real case)**: three consecutive attempts that all stay in the *same
layer* (e.g. three different UI / property-handle APIs for one task) count as **one**
failed approach, not three — swapping APIs within a layer is not a real approach change.
Worked UE example (with the actual API sequence): `guidelines/ue/details-customization-prefer-reflection.md`.

**Correct escalation**: After 2 same-layer attempts fail, ask "is the problem
actually in this layer?" If not, switch to a deeper layer (data model, type system,
framework contract) before trying a third UI variant.

Counter-signals you may be stuck in same-layer churn:

- Each new variant adds workarounds for the previous variant's failure mode, not
  for the original root cause
- You can't articulate why the previous variant didn't work — just that it "didn't"
- Each variant feels like "I just need one more tweak"
- The fundamental mechanism / contract you're fighting hasn't been examined
  (re-read the framework source for the layer below)

When stuck, re-read the **framework source** for the layer below. The root cause
is often a compile-time fixity (UHT metadata, codegen output, reflected schema)
that no runtime layer manipulation can defeat.

## Related Techniques

- See `techniques/coordination-patterns.md` for multi-agent coordination and worker failure handling.
- See `techniques/worker-instructions.md` for writing effective sub-agent prompts.
