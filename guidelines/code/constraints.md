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
