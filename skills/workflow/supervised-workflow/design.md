# Resolve design choices — Phase 1

Workflow material. Read only when the design is unfinished or a new decision needs
review. An existing approved design can satisfy this phase.

## Inputs

The user's goal, constraints and chosen review arrangement; relevant project
context; existing decisions; material unresolved product or architecture questions.

## Actions

1. Establish the intended user flow, observable acceptance and boundaries. Examine
   existing structure before suggesting changes. Resolve routine details from the
   user's delegation; ask focused questions for decisions they need to make.
2. Compare alternatives where a meaningful choice remains. Present the recommended
   design with its consequences, affected interfaces and required verification.
   Do not manufacture alternatives for settled questions.
3. Check scope against the request. New processes, public interfaces, persistent
   state, dependencies, trust boundaries or lifecycle mechanisms must serve the
   authorized outcome. Preserve agreed threat assumptions; surface any proposed
   expansion explicitly.
4. Reuse the project's design record. Design exploration or scope-audit skills may
   help a matching unresolved issue, but there is no automatic skill invocation or
   separate per-section approval sequence.

## Output

A reviewable design: problem framing, scope, material choices, recommendation,
acceptance criteria, risks and decisions needed. Keep the user summary concise
and link supporting detail when useful.

## Continue — Gate 1

Use an explicit approval of this design, or wait for the user's decision.
Approval permits planning; redirection updates only the affected decisions.
A previously approved design does not need approval again solely because a new
session or this skill has begun. Continue with [plan.md](plan.md) when covered.
