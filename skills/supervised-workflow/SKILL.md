---
name: supervised-workflow
description: High-touch workflow orchestrator for substantial tasks with three mandatory user-review gates (plan, impl-plan, per-milestone). Composes superpowers brainstorming, writing-plans, executing-plans, and requesting-code-review into a gated chain. Use when the user explicitly requests supervised / gated / high-touch workflow, or when the user asks the agent to evaluate workflow choice on a task with substantial architecture or design decisions. Do NOT use for trivial tasks (single-file mechanical changes, typo fixes, single-commit bug fixes) or when the user has selected autonomous workflow.
when_to_use: User explicitly says "use supervised / gated / 高介入 / 仔细 review" workflow, OR user asks agent to evaluate workflow choice and the task carries substantial design weight (architecture decisions, multi-file changes with cross-cutting effects, scope-ambiguous features). Skip for trivial tasks and skip when autonomous workflow is selected.
---

# Supervised Workflow

Orchestrator skill. Composes existing skills with **three hard user-review gates** between phases. Does NOT reimplement the composed skills' content — invoke them at each phase and add the gate behavior on top.

## When This Fires

**Triggers (any one):**
- User explicitly invokes: "use supervised workflow", "走 supervised", "走高介入", "仔细 review 一下", "I want gated review", or equivalent
- User asks agent to choose workflow ("你看怎么走") AND the task has at least one of:
  - Architecture or interface design decisions
  - Cross-cutting changes (>2 files, or changes that affect multiple subsystems)
  - Scope ambiguity that brainstorming should resolve
  - User explicitly wants to be involved at design level

**Does NOT fire when:**
- User selected autonomous workflow
- Task is trivial: single-file mechanical change, typo fix, single-commit bug fix with clear cause, doc-only edit
- User explicitly says "just do it" / "你直接来" / "skip review"

If in doubt about trigger, **ask the user** which workflow they want — do not silently default.

## The Chain

Five phases, three gates. Gates are **hard** — agent must stop and wait for user response before advancing.

```
Phase 1: Brainstorm
  → invoke superpowers:brainstorming
  → output: problem framing, scope boundaries, alternatives considered, recommended approach

[GATE 1] User reviews brainstorm output.
  Wait for explicit user confirmation. Do NOT proceed on silence or vague replies.
  If user redirects, restart Phase 1 with updated framing.

Phase 2: Implementation Plan
  → invoke superpowers:writing-plans
  → REQUIREMENT: plan must be broken into discrete Milestones or commits.
    Each Milestone = a coherent unit of work that ends at a stable point
    (code compiles, tests pass, intermediate state is reviewable).
  → output: ordered Milestone list, each with: goal, files touched,
    test/verification approach, completion criteria.

[GATE 2] User reviews impl-plan.
  Wait for explicit user confirmation on Milestone breakdown.
  If user adjusts Milestones, regenerate plan with the adjustments.

Phase 3: Per-Milestone Implementation
  For each Milestone in order:
    → invoke superpowers:executing-plans for THIS Milestone only
    → invoke superpowers:test-driven-development AND tdd-with-fixtures
      for test discipline — milestone NOT done if tests fail
    → run validation per guidelines/code/validation.md
    → commit (per guidelines/workflow/commits.md format)

    [GATE 3 — fires per Milestone] User reviews this Milestone.
      Output: what was done, files changed, commits made, test results,
      any deviations from plan with reason.
      Wait for user confirmation before starting next Milestone.

Phase 4: Overall Review
  → invoke superpowers:requesting-code-review
  → cover all Milestones together, focus on cross-Milestone consistency,
    architecture coherence, and integration risks not visible at Milestone scope.
```

## Gate Behavior

Each gate is a hard checkpoint. At each gate:

1. **Output a focused summary** for the user to review. Keep it under what fits in one screen — bullet points, files changed, decisions made. Don't dump the full plan or full diff; the user can ask if they want detail.

2. **Stop and wait.** Do not proceed to the next phase until the user gives a response that either:
   - confirms (e.g., "ok", "go", "looks good", "继续", "认可")
   - redirects (which restarts the current phase with adjustments)

3. **On silence**: do not proceed. Do not assume default. If the user has been silent for a long stretch and you genuinely need to make progress, ask explicitly: "I'm at [gate name], waiting for your review — should I proceed or wait?"

4. **On vague reply** ("hmm", "let me think"): ask for explicit confirm/redirect. Do not interpret vague replies as approval.

## Milestone Granularity

Agent proposes Milestone breakdown in Phase 2. User confirms or adjusts at Gate 2. Guidelines:

- A Milestone should produce a **commit-able state**: code compiles, existing tests pass, intermediate scope is coherent.
- Prefer 3-7 Milestones for a substantial feature. Fewer means too coarse (hard to review); more means too fine (gate overhead dominates).
- A Milestone that introduces a new public interface should include at least one consumer or test.
- If you propose <3 or >8 Milestones, justify in the plan why this granularity is right.

## Trivial-Task Exclusion

If during the chain you discover the task is trivial (e.g., brainstorm reveals it's a one-line fix), **say so** and ask the user if they want to drop into trivial mode (skip gates, just implement). Do not force the chain on trivial work.

## Interaction with Other Skills

This skill is an **orchestrator** — it invokes other skills, does not replace them:

- `superpowers:brainstorming` — owns Phase 1 content
- `superpowers:writing-plans` — owns Phase 2 content
- `superpowers:executing-plans` — owns Phase 3 implementation
- `superpowers:requesting-code-review` — owns Phase 4
- `superpowers:test-driven-development` — base red/green/refactor cycle, invoked inside Phase 3
- `tdd-with-fixtures` — milestone-level test discipline + fixture/manual escape hatch for behaviors auto-tests can't cover; invoked inside Phase 3 alongside superpowers:TDD. Non-negotiable: workflow gates do not suspend its rules.

When invoking each composed skill, **follow that skill's own discipline fully**. Do not skip steps of a composed skill because this orchestrator is also running.

## Failure Modes to Watch

| Failure | What it looks like | Correct action |
|---|---|---|
| Skipping a gate | Going straight from impl-plan to next Milestone without user confirm | Stop, request user review |
| Bundling multiple Milestones | "I did Milestones 2 and 3 together" | Don't. One Milestone, one gate. |
| Misreading vague reply as approval | "hmm ok" treated as confirm | Ask for explicit confirm |
| Forcing chain on trivial task | Running brainstorm for a typo fix | Detect early, ask user to switch to trivial mode |
| Over-summarizing at gates | Output is too vague for user to actually review | Include concrete file paths, decisions, deviations |
| Under-summarizing at gates | Dumping full diff or full plan | One-screen summary; user can request detail |

## Related

- `guidelines/workflow/agent-lifecycle.md` — baseline for "what needs user confirmation"
- `guidelines/workflow/commits.md` — commit format used at each Milestone
- `guidelines/workflow/handoffs.md` — different topology (multi-chat); not used by this workflow
- `guidelines/code/validation.md` — verification required at each Milestone before declaring done
- `skills/tdd-with-fixtures/SKILL.md` — test discipline invoked at each Milestone
- `skills/autonomous-workflow/SKILL.md` — sibling workflow with only a plan gate (no per-milestone gates); switch to this when user wants the strategic checkpoint but not per-milestone review
