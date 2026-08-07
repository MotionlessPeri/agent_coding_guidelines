# Code Constraints

## Architecture First

- Read and understand the relevant architecture documentation before modifying code.
- Identify which subsystem, flow, or module is being changed. Confirm scope before acting.
- Do not make changes that span unrelated components in one step.

## Correctness

- Avoid silent success: surface actionable errors when command or function preconditions
  are not met.
- Validate at system boundaries (user input, external APIs, tool interfaces).
- Do not add error handling for scenarios that cannot happen in practice.

## Commit Integrity

- Every commit must leave the repository in a usable state:
  - Code compiles.
  - Server/tool starts.
  - Existing tests pass.
- Do not commit partial implementations unless they are behind a feature flag or clearly
  marked as stubs.

## Simplicity

- Avoid over-engineering. Only make changes that are directly requested or clearly necessary.
- Don't add features, abstractions, or configurability beyond what the current task needs.
- Three similar lines of code is better than a premature abstraction.

### Plan scope integrity

- Whole-plan approval does not make every item in the plan a justified requirement.
  Before approval, trace each new or expanded product surface to an explicit current
  user flow and apply a deletion test: if removing it still satisfies the request and
  acceptance criteria, remove it from the plan.
- Treat processes, transports, protocols, persistent state, public interfaces,
  commands, configuration, security or trust boundaries, and lifecycle mechanisms
  as product surface, even when described as implementation details.
- Reviewer preference, possible future use, test convenience, existing code, and
  sunk effort are not sufficient justification by themselves.
- Autonomous authority never authorizes a broader plan than the user's request.
- A temporary validation surface may enter an approved plan only with a closure
  point and verification method. At that point, delete it, internalize it, or make
  it test-only; re-audit it before keeping it as a long-term product surface.

## Edit Scope Discipline

- Every changed line must trace directly to the user's request. If you cannot explain
  why a specific line is in your diff, remove it.
- Do not "improve" adjacent code, comments, formatting, or type annotations while
  making an unrelated change. Drive-by refactoring inflates diffs and hides the real
  change from review.
- Match existing style even when you would write it differently. Style inconsistencies
  you notice should be raised separately, not silently corrected during another task.
- Only remove imports, variables, or helpers that **your changes** made unused.
  Pre-existing dead code: mention it, do not delete it without an explicit ask.
- If you find a real bug while editing for an unrelated reason, surface it to the user
  and let them decide whether to fold the fix in or split it off — do not silently
  expand scope.
