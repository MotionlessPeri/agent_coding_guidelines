---
name: auditing-plan-scope
description: Use when preparing a non-trivial software design or implementation plan for approval and the proposal may add or expand a process, transport, protocol, persistent state, public interface, command, configuration, security or trust boundary, lifecycle mechanism, or temporary validation surface. Skip implementation-stage findings governed by an already approved plan.
---

# Auditing Plan Scope

Prevent an oversized proposal from becoming legitimate merely because the user
approves the proposal as a whole. Audit the candidate design before asking for
design approval, then audit only plan deltas before implementation-plan approval.

## Phase A: Establish the scope baseline

Before reading or defending candidate mechanisms, record:

1. the user's requested outcome;
2. current user flows and acceptance criteria;
3. the approved threat model and trust assumptions;
4. the smallest observable behavior that would satisfy each flow.

This de-anchoring step is mandatory. Existing code, research effort, reviewer
language, and a polished candidate design must not define the baseline.

A candidate mechanism does not create or become a requirement. Do not promote
a failure mode that exists only because the proposal introduced discovery,
configuration, a session lifecycle, or another mechanism into a current user
flow. Treat a broad quality label such as “safe,” “reliable,” “professional,” or
“avoid accidental calls” as a constraint: define the smallest observable result
in the existing flow before selecting mechanisms. If the label has multiple
material meanings, expose the ambiguity instead of choosing the largest one.
In each Requirement basis, label evidence as explicit or inferred. Inferred
behavior may explain a risk, but it cannot authorize a new public or lifecycle
surface without user approval. A reviewer statement cannot establish a current
user flow, and mention of a proposed mechanism does not prove that mechanism is
an approved part of the baseline. For broad boundary-safety language, first test
validation at the existing request boundary (service/protocol/operation and
input checks); add a session or discovery lifecycle only when an explicit current
flow fails without it.

## Phase B: Prefilter product surface

For every non-trivial design, list any new or expanded:

- process, transport, or protocol;
- persistent state or public interface;
- command or configuration;
- security or trust boundary;
- lifecycle mechanism;
- temporary validation entry point.

If the list is empty, record that result and stop. Otherwise run the full audit.

## Phase C: Run the full audit

Create one row per candidate surface:

| Candidate | Consumer and frequency | Requirement basis | Deletion consequence | Existing alternative | Disposition | Closure condition |
|---|---|---|---|---|---|---|
| Name the concrete surface. | Name the real consumer and whether use is normal-path, first-time setup, low-frequency recovery, or debug-only. | Cite the user's words, an approved scenario, or an acceptance criterion. | State which current flow fails if this is removed. | Name an existing tool, log, configuration, automatic recovery path, or internal entry point. | Keep / Merge / Internalize / Temporary validation / Defer / Delete | Required for temporary validation; otherwise blank. |

Apply these rules:

- `Keep`, `Merge`, `Internalize`, and `Temporary validation` all include work in
  the approved plan. Each therefore requires an explicit current requirement;
  none is an escape hatch for speculative scope. This reverse traceability must
  connect the candidate to a current user flow before disposition.
- An inferred candidate may only be `Defer` or `Delete`, or be shown as an
  unresolved, separate scope choice that is not included by whole-plan approval.
- Apply the deletion test to every row. If removing both the surface and its
  behavior leaves every current requirement satisfied, choose `Defer` or
  `Delete`. If only the independent/public surface is unnecessary but approved
  behavior remains necessary, choose `Merge` or `Internalize`.
- Choose `Merge` when an approved surface can absorb the behavior without a new
  independently supported mechanism.
- Choose `Internalize` when production needs the behavior but users do not need
  a stable public entry point.
- Choose `Temporary validation` only for a time-bounded probe, spike, or test
  entry point with the closure contract below.
- `Defer` records a decision only. Do not create a roadmap item, TODO, issue, or
  future milestone unless the user separately asks for one.
- “The reviewer called it important,” “we may need it later,” “tests are easier,”
  “it already exists,” and “we spent time on it” are evidence to consider, not
  requirement justification.

For a temporary validation surface, record its closure point, closure action
(`Delete`, internalize, or test-only), and verification method. Re-run the row
before keeping the surface beyond that point.

## Phase D: Present the gate summary

Keep the complete table in the design artifact. At the user gate, present a
one-screen summary containing:

- the scope baseline;
- surfaces kept and their consumers;
- surfaces merged or internalized;
- surfaces deferred or deleted;
- temporary surfaces and their closure contracts;
- the scope delta from the previous audit;
- any unresolved choice that genuinely requires the user.

For an implementation plan, do not repeat the full audit. Compare the plan with
the approved design and audit only new, widened, or newly public surfaces. Any
such delta must be visible at the implementation-plan gate.

Use the same agent in two de-anchored phases by default. Ask for a fresh reviewer
only when traceability remains ambiguous or the proposal changes a high-risk
security, trust, data-loss, or compatibility boundary.

After approval, use the finding-triage rules in `agent-lifecycle.md`; this skill
does not replace the approved-plan scope boundary.
