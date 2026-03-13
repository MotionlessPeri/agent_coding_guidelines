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
