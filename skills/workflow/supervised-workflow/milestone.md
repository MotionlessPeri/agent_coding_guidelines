# Implement one delivery unit — Phase 3

Workflow material. Read for the unit currently authorized by the accepted plan.

## Inputs

The accepted plan and current unit; original baseline and ownership; applicable
project verification; prior evidence and outstanding failure history.

## Actions

1. Implement the unit within its accepted boundary, using its canonical milestone
   ID/name in status and review records. Do not silently combine units across the
   user's checkpoints.
2. Use meaningful verification suited to the change. For a defect fix, observe
   the target failure before the fix and success afterward with the same input
   and criterion; reliable recorded pre-fix evidence may be reused. New behavior
   retains applicable TDD discipline; refactors use regression checks covering
   changed paths. Documentation/mechanical changes use content/link/syntax
   checks rather than invented failing tests. Required manual cases need actual
   observations and reproducible fixtures.
3. Run appropriate build/tests/smoke checks and verify the changed artifact was
   exercised. Reuse evidence only while the covered source, artifact, environment
   and procedure remain applicable. Missing coverage or unperformed human
   verification cannot be replaced by a passing unrelated test.
4. Triage review findings under `guidelines/workflow/agent-lifecycle.md` before
   editing: tie necessary corrections to an accepted criterion or user constraint.
   Reviewer severity does not authorize new behavior or architecture. Optional
   audits/review skills serve a specific uncovered need or user request; installed
   availability alone is not a trigger.
5. Record results, deviations, outstanding findings and actual commits. Make
   coherent verified local commits when authorized, respecting user restrictions
   and project commit rules. Include only task-owned changes.

## Failure and scope handling

Follow `agent-lifecycle.md` for recurring failures: the same root cause and
observable failure surviving three consecutive targeted repairs ends that method.
Report attempts, remaining evidence and options before another edit for that
signature. Different failures keep separate histories; unrelated green tests,
commits and reviewer changes do not reset an unresolved one.

An infeasible accepted design or newly needed process, protocol, public interface,
schema, dependency, trust boundary or lifecycle change outside the plan needs a
decision immediately; do not wait for Gate 3 after implementing it. Pause dependent
work, preserve evidence and continue independent work within existing checkpoints.
Follow real host denials and user pauses; this Markdown is not a bypass mechanism.

## Output and continue — Gate 3

Present the unit's actual behavior, changed files, commits, verification and any
deviation. A failing required check or unverified required manual case means the
unit is not complete; fix within scope or explain the remaining blocker.

Wait for the user's review before starting the next unit, unless a still-applicable
explicit decision already covers this result. A plan approval alone does not.
Redirection applies to the affected result and may require further verification.
After the last reviewed unit, use [overall-review.md](overall-review.md).
