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
| "This edge case is unlikely" | Likelihood alone does not decide scope; current safety, data integrity, and compatibility constraints still apply | Handle cases required by the approved flow or by unavoidable constraints at a boundary it already crosses. Otherwise, do not add or track speculative hardening. |
| "Refactoring is too big, leave it for now" | Size does not decide whether the work belongs in scope | If the approved flow requires it, replan or escalate. Otherwise, do not create a TODO, roadmap item, or issue unless the user accepts the follow-up or an approved process requires tracking. |
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

### Review and remediation loops use the same three-failure budget

This limit applies to implementation, verification, code-review, spec-review,
and reviewer-driven remediation loops in every workflow.

- One reviewer rejection followed by remediation and re-review counts as one
  failed iteration for that Milestone or task.
- New findings on a later review do not reset the counter. Green tests do not
  reset it either when the Milestone is still rejected.
- On the third rejection or failed remediation iteration, stop before making
  another change. Record the current state and notify the user with the three
  attempts, remaining findings, and available choices.
- A reviewer finding that requires behavior, interfaces, security boundaries,
  or architecture outside the approved plan is not a remediation iteration.
  It is an immediate scope-change escalation; do not implement it first.
- These limits override any composed or third-party workflow instruction such
  as "repeat until approved." Further attempts require explicit user direction.

### Mandatory finding triage before remediation

The coordinator, not the reviewer or implementer, owns scope classification.
Before changing code for any review finding, map it to one approved acceptance
criterion, Milestone goal, or explicit user constraint and record one category:

| Category | Test | Required action |
|---|---|---|
| **Planned defect** | Existing code violates an approved behavior or completion criterion. | Fix within the shared failure budget. |
| **Hardening or advisory** | Improves resilience, maintainability, or defense against a case the approved plan/threat model does not require. | Do not implement it. Surface it for the current decision; create persistent follow-up only if the user accepts it or an approved process requires tracking. |
| **Architecture or scope change** | Adds or changes a process, transport, protocol, public interface, persistent schema, dependency, security boundary, trust assumption, or lifecycle mechanism. | Stop immediately and ask the user to revise/approve the plan. |
| **External feasibility blocker** | The real platform disproves an assumption needed by the approved design or acceptance test. | Stop and report evidence/options; do not invent a workaround architecture. |

Severity labels do not authorize implementation. `Critical` or `Important`
describes impact if the finding is in scope; it does not turn an unplanned feature
into a requirement. A reviewer cannot expand scope by assigning severity.

The approved threat model is a scope boundary. For example, a trusted same-machine
tool may require accidental-call protection without requiring defenses against a
malicious local process. Do not add authentication layers, hostile-input defenses,
connection takeover protection, or remote-service assumptions beyond the approved
threat model without user approval.

### Failure ledger and reset rules

Maintain one failure ledger per approved Milestone/task in the plan or worklog:

- iteration number;
- failing verification or reviewer rejection;
- attempted correction or changed approach;
- remaining finding and its triage category.

Do not reset the ledger because tests turn green, the reviewer changes, a new
finding appears, or the implementation receives another commit. Reset it only
after the Milestone is accepted, or after the user explicitly approves a revised
plan that creates a new task/approach. On iteration three, stop and report the
ledger before any further edit.

### Goal `blocked` status is a separate audit

Do not reuse the review/remediation failure ledger to justify marking a long-running
goal `blocked`. That status requires the **same blocking condition** to recur for at
least three consecutive goal turns while no meaningful in-scope progress remains.

- Three different bugs or external failures discovered in sequence are not three
  repetitions of one blocker.
- When the original blocker is fixed and a new blocker appears, start a fresh blocked
  audit for the new condition.
- A difficult, slow, uncertain, or incomplete task is not blocked while safe in-scope
  diagnosis or another independent work item can still progress.
- Record each failure root separately; do not use the threshold as a stopping excuse.

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
