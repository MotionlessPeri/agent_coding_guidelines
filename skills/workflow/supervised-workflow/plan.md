# Plan delivery units — Phase 2

Workflow material. Read when converting an accepted design into executable units,
or reviewing a material plan change.

## Inputs

Accepted design and acceptance criteria; relevant source and project checks;
existing task records, original baseline and ownership decisions.

## Actions

1. Confirm the design decision and task ownership. For a new Git task, record
   starting HEAD and initial status; retain the original baseline on resumption.
   Identify pre-existing changes overlapping planned edits. Resolve uncertain
   ownership before those edits, without blocking unrelated authorized work.
2. Choose coherent, verifiable delivery units; one is valid. Record each goal,
   affected files, dependencies, verification and completion condition. A new
   public interface needs a consumer or test that exercises its contract.
3. Preserve any established milestone IDs/names. Compare the plan with the design
   and disclose scope/architecture deltas, rather than hiding them in implementation
   detail. Split independent subsystems only when it improves delivery or review.
4. Match verification to the change: behavior tests for behavior changes, covered
   regression for refactors, reproducible manual cases where necessary, content
   checks for documentation/mechanical changes. Do not invent TDD for unchanged
   behavior or require a full implementation listing in the plan.
5. Identify actual host restrictions relevant to execution. Do not change
   permission settings, bypass denial or run empty commit probes.

Plan location follows project convention. Implementation plans can be tracked
project deliverables; private logs and handoffs remain private. Reuse existing
records rather than creating another mandatory set. Consult a planning skill only
if a concrete unresolved planning need warrants it.

## Output

Ordered units, verification/acceptance, relevant ownership and scope decisions,
plus any execution limitation. Present enough detail for the user to approve
what will be built and how it will be checked.

## Continue — Gate 2

Reuse an explicit approval covering this plan, or wait for confirmation/redirection.
A newly added public surface or changed outcome is a new decision, not a routine
review fix. Once covered, proceed to [milestone.md](milestone.md). Gate 2 approves
the plan; it does not pre-approve the result later reviewed at Gate 3.
