# Implement and verify — Phase 3

Workflow material. Read for the current delivery unit; do not preload final-review
or documentation templates.

## Inputs

Authorized scope and acceptance criteria; the current delivery unit; the original
task baseline and ownership decisions; applicable project checks and prior evidence.

## Actions

1. Implement the current unit within its accepted boundaries. Carry forward its
   canonical milestone ID/name when one exists.
2. Choose verification by the behavior at risk, following the applicable project
   verification and test-purpose rules:

   | Change | Evidence |
   |---|---|
   | New behavior | A meaningful behavior check; demonstrate failure before implementation when applying TDD, then passing with the change |
   | Defect fix | An actually observed failure from the target defect before the fix, then success with the same input and criterion; reliable recorded pre-fix evidence may be reused |
   | Pure refactor | Existing regression evidence covering changed paths; add a focused check where needed to cover a real gap |
   | Documentation or mechanical change without behavioral impact | Content, links, syntax or other relevant checks; no invented failing test |
   | Behavior not observable by automation | A reproducible fixture/manual procedure and its actual result; required human observation remains necessary |

3. Run relevant build/tests/smoke procedures and inspect their outcomes. Verify that
   the result comes from the changed source/artifact, not a stale binary. Reuse
   recorded evidence only when its inputs, environment and coverage remain valid.
4. Review findings against an acceptance criterion, milestone goal or explicit
   user constraint before remediation. Apply the canonical finding triage in
   `guidelines/workflow/agent-lifecycle.md`: a required fix is actionable;
   advisory hardening is not automatic scope; reviewer severity grants no authority.
   Independent reviews and project audit skills are used when requested or when
   their specific perspective is needed, not merely because they are installed.
5. Record what changed, the checks and results, any deviation, remaining failures,
   and actual commits. Commit coherent, verified task-owned changes when authorized,
   following project commit rules and user restrictions; do not include others' work.
6. Continue to the next authorized unit without a new approval pause. Give useful
   status updates; do not treat a status question as a request to stop.

## Failure and scope handling

Use the recurring-failure policy in `agent-lifecycle.md`. For the same root cause
and observable failure surviving three consecutive targeted repairs, stop that
method and report the attempts, evidence and options. Keep separate histories for
different failures; commits, new reviewers or unrelated green tests do not reset
an unresolved signature. There is no cumulative cap across unrelated findings.

A disproved architectural premise or an infeasible accepted approach needs a
decision about that approach, not more iterations or a silent replacement design.
Likewise, new behavior, interfaces, dependencies, schemas or trust/lifecycle changes
outside the authorized scope need authorization before implementation. Pause only
dependent work. Respect an explicit pause or revoked authorization immediately.

Follow actual host denials. Do not switch tools or weaken checks to bypass them.
A blocked action is not evidence that a task or commit was completed.

## Output and continuation

Record a verifiable delivery result, its evidence and any outstanding issue.
Failing required checks or unperformed required manual validation prevent calling
that unit complete; fix within scope or report the limitation. After all units are
ready, use [review-result.md](review-result.md).
