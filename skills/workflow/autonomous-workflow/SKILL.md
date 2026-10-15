---
name: autonomous-workflow
description: Use for substantial work the user delegates for autonomous completion, including an existing authorized plan or a requested single plan review. Skip trivial work and user-selected staged approval; clarify only unresolved decisions that exceed delegated judgment.
---

# Autonomous Workflow

## Purpose and authority

This is a workflow for completing authorized work with proportionate records and
verification. It does not grant authority, select a new approval policy, or install
a runtime. Host instructions, the user's current direction, and applicable project
constraints determine what is permitted.

A prose checkpoint is an instruction for the agent to follow. It is not a
mechanically enforced gate unless an actual host or tool implements one. Report
real host denials as such; do not bypass them or claim that this skill enforces them.

Use an existing applicable approval or delegated scope. Ask for a plan review only
when the user requested that checkpoint or a concrete decision exceeds existing
authorization. Silence does not supply a missing approval. A request such as
"you decide" delegates routine judgment; it does not select staged supervision.
An unresolved architecture question calls for that decision, not an automatic
switch to a different workflow.

## Load only the current phase

Start at the first unfinished phase. Do not read all attachments on entry.

| Current need | Workflow material | Output and continuation |
|---|---|---|
| Establish or recover scope; plan remaining work (Phases 0–2) | [prepare-plan.md](prepare-plan.md) | Usable acceptance criteria and plan; continue within current authorization |
| Implement the next delivery unit (Phase 3) | [implement.md](implement.md) | Verified result and current progress; continue while authorized work remains |
| Check the whole result and deliver it (Phase 4) | [review-result.md](review-result.md) | Evidence against acceptance criteria and a candid completion report |

Normal route: prepare or resume → implement and verify → review the whole result.
A missing decision pauses only its dependent work. A status request calls for an
update, then continuation; it does not revoke the task.

## Knowledge and norm references

- [records-reference.md](records-reference.md) is knowledge: record layout,
  platform path examples, and evidence-reuse rationale. Read it only when an
  existing record is insufficient or a new record/handoff needs a format.
- Norms remain in the host/user instructions and canonical project guidelines.
  Consult the relevant section when needed: `guidelines/workflow/agent-lifecycle.md`
  for authorization, finding triage and recurring failures;
  `guidelines/collaboration/private-docs-policy.md` for record ownership;
  `guidelines/workflow/commits.md` for local commits;
  `guidelines/code/validation.md` and `guidelines/code/test-purpose.md` for verification.
- Those guideline paths are relative to the guidelines repository identified by
  the project's AGENTS.md/CLAUDE.md. Attachments above are relative to this skill.
  Do not substitute the skill install directory for the guidelines root.

## Preserve across phases

Keep the original task baseline, decisions, outstanding failures and evidence when
resuming. Reuse existing records and approvals; do not restart completed preparation.
Required independent review or human verification cannot be replaced by self-review.
New optional work is a proposal, not an amendment to the authorized task.

Use another skill only for a clear unresolved need in the current phase or an
explicit user request. A workflow reference is not a command to invoke its entire
dependency chain. Doc-only and mechanical work do not require invented red tests;
behavior changes still require meaningful verification.
