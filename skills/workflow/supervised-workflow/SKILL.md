---
name: supervised-workflow
description: Use when the user explicitly chooses staged approval for substantial work, including design, implementation-plan and delivery-unit reviews. Skip ordinary reviews, trivial edits and autonomous work; "you decide" alone does not select this workflow.
---

# Supervised Workflow

## Selection and authority

This is the workflow the user selects when they want to review decisions between
stages. Complexity, file count, architecture work or an ambiguous request alone
does not select it. Clarify a missing material decision without imposing the whole
workflow. Existing user-selected checkpoints remain in force unless changed.

Host instructions and the user's direction determine authority. This skill
organizes their checkpoints; it cannot grant permissions or override either.
A "gate" here means an agent obligation to wait for the specified user decision.
It is not a mechanically enforced barrier unless an actual host/tool implements it.

## Load only the current phase

Reuse completed work and applicable explicit approvals. Start at the first
unfinished phase; do not read every attachment or restart the chain on resumption.

| Current phase | Workflow material | Review boundary |
|---|---|---|
| 1. Resolve design choices | [design.md](design.md) | Gate 1: the concrete design |
| 2. Plan delivery units | [plan.md](plan.md) | Gate 2: implementation plan |
| 3. Implement and verify a unit | [milestone.md](milestone.md) | Gate 3: each unit's result before the next |
| 4. Review the whole result | [overall-review.md](overall-review.md) | Final report; no additional default approval |

Normal route: design → approved design → plan → approved plan → verified unit
→ unit review → next unit or overall review. Each approval covers its own decision;
design approval is not approval of an unseen result.

## At an agreed checkpoint

Present a concise, concrete summary with its decisions, evidence and deviations.
Reuse an explicit approval that covers that same decision/result. If it does not
exist, wait for approval or redirection; silence or an ambiguous response supplies
neither. A newly requested review still occurs even if an older approval exists.
Continue independent authorized work only where doing so does not cross the
checkpoint. Do not repeatedly ask the same pending question.

## Knowledge and norm references

- For record layout or evidence-reuse details only, see the sibling skill's
  [records reference](../autonomous-workflow/records-reference.md). Existing
  project plans are valid records; private logs and handoffs remain private.
- Canonical norms: `guidelines/workflow/agent-lifecycle.md` for authorization,
  recurring failures and finding triage; `guidelines/workflow/commits.md` for
  local commits; `guidelines/code/validation.md` and `guidelines/code/test-purpose.md` for
  verification; `guidelines/collaboration/private-docs-policy.md` for ownership.
  These paths resolve from the project's guidelines-repository pointer, not from
  this skill's installation directory.

Preserve the task baseline, ownership, decisions and failure history across
resumption. Required independent or human verification remains required. Use other
skills only for a clearly matched unresolved need in the current phase or an
explicit request; they do not add default approval rounds to the user's workflow.
If the task becomes trivial, offer to simplify the selected checkpoints; do not
silently discard the review arrangement the user explicitly chose.
