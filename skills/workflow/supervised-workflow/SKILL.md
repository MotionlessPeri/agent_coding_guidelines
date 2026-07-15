---
name: supervised-workflow
description: High-touch workflow orchestrator for substantial tasks with three mandatory user-review gates (plan, impl-plan, per-milestone). Composes superpowers brainstorming, writing-plans, executing-plans, and requesting-code-review into a gated chain. Use when the user explicitly requests supervised / gated / high-touch workflow, or when the user asks the agent to evaluate workflow choice on a task with substantial architecture or design decisions. Do NOT use for trivial tasks (single-file mechanical changes, typo fixes, single-commit bug fixes) or when the user has selected autonomous workflow.
---

# Supervised Workflow

Orchestrator skill. Composes existing skills with **three hard user-review gates** between phases. Does NOT reimplement the composed skills' content — invoke them at each phase and add the gate behavior on top.

## Platform Paths

Resolve these placeholders once at workflow start:

| Placeholder | Claude Code | Codex |
|---|---|---|
| `<project-skill-root>` | `<project>/.claude/skills` | `<project>/.agents/skills` |
| `<agent-state-root>` | `~/.claude` | `${CODEX_HOME}` when set, otherwise `~/.codex` |

Do not mix roots within one run. Project-local Codex skills and Codex private state intentionally use different roots.

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
  → ★ Pattern recognition (if project has it). Check whether the project has
    `<project-skill-root>/pattern-recognition-prep/SKILL.md`. If yes,
    invoke it on the task statement before GATE 1. Capture findings in the
    Phase 1 output:
      - Strong Established match → "Reuse Pattern X" (drives Phase 2 plan)
      - Partial / Watching match → note as candidate
      - Novel pattern candidate → record draft; Phase 4 audit revisits
    Findings are visible to user at GATE 1 review — user can redirect plan
    if pattern fit is wrong. If skill absent, skip silently.

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
    → validate (build / tests / smoke as appropriate). Reading code is NOT
      validation — run commands and observe output.
    → commit. Format: `<type>: <subject>`. One theme per commit. Commit only at
      stable points (build passes, tests pass).

    [GATE 3 — fires per Milestone] User reviews this Milestone.
      Output: what was done, files changed, commits made, test results,
      any deviations from plan with reason.
      Wait for user confirmation before starting next Milestone.

Phase 4: Overall Review
  → CONSISTENCY GATE (run FIRST — a DIFFERENT lens than code-review: "做的 ↔ 当初说的对得上吗",
    not "代码质量好不好"). Even with per-Milestone GATE 3, do a final cross-Milestone coverage pass:
      - Coverage, both directions: does every Acceptance Criterion + Milestone in the plan have
        corresponding implementation? AND was anything built that the plan did NOT ask for?
      - Spec-quality leftovers: any vague/unmeasurable acceptance criteria, or unresolved
        TODO / ??? / placeholder shipped?
      - Surface gaps with severity (CRITICAL / HIGH / MEDIUM / LOW) in the review output; a
        CRITICAL coverage gap blocks completion.
  → invoke superpowers:requesting-code-review
  → cover all Milestones together, focus on cross-Milestone consistency,
    architecture coherence, and integration risks not visible at Milestone scope.
  → SKILL-WORTHY LESSON AUDIT: self-question against the work done —
    "Did anything emerge during this task that should fire automatically for
     FUTURE work (a pattern, contract, anti-pattern, or convention)?"
    For each candidate, classify:
      - **Project skill candidate**: only makes sense in THIS project. Target
        location: `<project-skill-root>/<name>/SKILL.md`. Low bar.
      - **Global skill candidate**: applies across projects. Target location:
        `agent_coding_guidelines/skills/`. Higher bar (knowledge-promotion.md
        criteria: two-strike rule / hidden contract / validated pattern).
    Surface candidates in the overall review output for user to act on.
    DO NOT auto-create skill files — propose only. User decides.
    If nothing skill-worthy emerged, explicitly say so (avoids ambiguity).
  → ★ Pattern catalog audit (if project has pattern-recognition-prep skill).
    Invoke it in WRITE direction on the work just done:
       - Did the implementation touch an existing Established / Watching
         pattern? → add this task as a new "Uses" entry (user approve)
       - Did a novel architectural pattern emerge? → draft a Watching entry
         (three-question check: generic / architectural-level / abstraction-
         level reasonable), surface for user approval
       - Did a Watching pattern hit its 3rd use this task? → propose promotion
         to Established with a full entry draft
     Surface findings in overall review output. DO NOT auto-write to catalog —
     drafts only, user decides. If skill absent or no updates, say so.
  → DAILY LOG + OPEN-ITEMS SYNC: per `guidelines/workflow/daily-and-open-items.md`:
    - Append entry to today's `<agent-state-root>/daily/YYYY-MM-DD.md` under the
      relevant project section, with reference to commits made and key decisions
    - Sync task status to `<agent-state-root>/projects/<project>/open-items.md`:
      task done → close item; task incomplete → ensure in-flight entry exists
    - Record changes under daily's "Open Items Δ"
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
- Project-side `pattern-recognition-prep` skill (optional, design-time prep) — if `<project-skill-root>/pattern-recognition-prep/SKILL.md` exists, invoke it at Phase 1 (read direction: surface reusable Established / Watching patterns before GATE 1) and Phase 4 (write direction: audit novel pattern → Watching / Watching → Established promotion). Findings drive Milestone breakdown to favor reuse. User approve required before any catalog write.

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
