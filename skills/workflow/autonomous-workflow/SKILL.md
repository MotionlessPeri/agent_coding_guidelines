---
name: autonomous-workflow
description: Use when the user requests autonomous work on a substantial task or wants only one implementation-plan approval. Skip trivial edits, unclear acceptance criteria, user-selected supervised work, and unresolved architecture or interface decisions.
---

# Autonomous Workflow

Orchestrator skill. Same composition chain as `supervised-workflow` but only **one user-review gate** — at the plan stage. After plan approval, execution runs without further gates. Three safety nets:

1. **Plan gate** — catches strategic bias (wrong scope / wrong approach / wrong milestone breakdown) BEFORE any code is written. Cheapest possible insurance, highest leverage of the three.
2. **Documentation** — durable handoff artifacts (brief / context / worklog / result) let the user audit afterward. Worklog is append-only and readable as a status check anytime.
3. **TDD discipline** — `tdd-with-fixtures` is mandatory; failing tests block milestone advancement. Acts as the safety net during the gateless execution phase.

## Platform Paths

Resolve these placeholders once at workflow start and use them throughout:

| Placeholder | Claude Code | Codex |
|---|---|---|
| `<project-skill-root>` | `<project>/.claude/skills` | `<project>/.agents/skills` |
| `<agent-state-root>` | `~/.claude` | `${CODEX_HOME}` when set, otherwise `~/.codex` |

Do not mix roots within one run. Project-local Codex skills come from `.agents/skills`; Codex configuration and private state remain under `.codex` / `CODEX_HOME`.

**Diff vs `supervised-workflow`:**

| Phase | supervised | autonomous |
|---|---|---|
| Brainstorm output | gate | folded into plan; no separate gate |
| Impl-plan | gate | **gate (only one in this workflow)** |
| Per-milestone | gate per Milestone | no gate; tests + worklog cover |
| Final | requesting-code-review w/ user | self-review + result.md for user to read later |

## When This Fires

**Triggers (any one):**
- User explicitly invokes: "use autonomous / 自主 / agent-led / 你自己来 / 你直接做", or equivalent
- User asks agent to choose ("你看怎么走") AND **all** of:
  - Task is functional-only (no architecture / interface design decisions)
  - Pipeline / pattern is clear from project conventions or prior work
  - User signals they will not be available for mid-task review

**Does NOT fire when:**
- User selected supervised workflow
- Task is trivial (single-file mechanical change, typo fix, doc-only edit) — drop to default just-do-it behavior
- Architectural decisions are present (interface design, schema changes, cross-cutting refactor) — escalate to supervised
- Acceptance criteria are ambiguous — clarify with user first

If unsure, **ask the user** which workflow to use. Do not silently default to autonomous.

## The Chain

Five phases. **Exactly one hard gate** — after Phase 2 (plan). Phases 3 and 4 run without further interruption. Each phase has explicit doc artifacts.

```
Phase 0: Setup
  → generate task slug: YYYY-MM-DD-<short-kebab-case>
    e.g. "2026-05-11-fix-session-expiry", "2026-05-11-add-patrol-callback"
    (date prefix is mandatory — see "Task Slug Convention" below)
  → create handoff dir at <handoff-root>/<task-slug>/
  → initialize four files: brief.md, context.md, worklog.md, result.md (placeholder)
  → record `TASK_BASELINE = git rev-parse HEAD` and the output of
    `git status --short` verbatim in context.md. If a planned Milestone overlaps a
    pre-existing dirty path, surface the overlap at the plan gate and do not start
    implementation until the user resolves it or explicitly defines ownership.
  → PRE-FLIGHT: check host constraints on local commits (see "Commit Permission
    Pre-Flight" below). If the active policy may interrupt unattended work,
    explain that limitation at the plan gate; do not change permission settings.

Phase 1: Self-Brainstorm
  → invoke superpowers:brainstorming mentally — do NOT pause for user
  → write brief.md: task statement, in scope, out of scope, acceptance criteria
  → write context.md: relevant files, constraints, known risks,
    framework references (engine source pointers, related guidelines)
  → ★ Pattern recognition (if project has it). Check whether the project has
    `<project-skill-root>/pattern-recognition-prep/SKILL.md`. If yes,
    invoke it on the task statement. Capture findings in context.md under
    "Related Patterns" section:
      - Strong Established match → "Reuse Pattern X" (drives Phase 2 plan
        to NOT re-implement from scratch)
      - Partial / Watching match → note as candidate; may inform Phase 4 audit
      - Novel pattern candidate → record draft in brief.md "Novel Pattern
        Candidates" section; Phase 4 audit will revisit
    If skill absent, skip silently.
  → run the full scope audit after Self-Brainstorm using
    `auditing-plan-scope` when its product-surface prefilter finds any
    expansion signal. Store the complete table in brief.md.

Phase 2: Self-Plan
  → invoke superpowers:writing-plans
  → break into 3-7 Milestones (see supervised-workflow for granularity guidance)
  → if the work contains independently deliverable subsystems, split them into
    separate plans/runs unless the user explicitly approves one combined run
  → append plan section to brief.md with Milestone list:
    each Milestone has goal, files touched, test approach, completion criteria
  → record the approved threat model and architecture boundaries, including
    which processes, transports, protocols, persistent schemas, public
    interfaces, authentication layers, and lifecycle mechanisms are allowed
  → run the delta scope audit after Self-Plan using `auditing-plan-scope`.
    Compare the plan with the audited design and add any new, widened, or newly
    public surface to the scope summary for the only user gate.

[GATE — the only gate in this workflow]
  → output to user: framing summary (from brief.md) + Milestone list,
    plus the one-screen scope-audit summary, one-screen total. Concise, not the
    full file dump.
  → wait for explicit user response:
    - confirms → advance to Phase 3
    - redirects (scope wrong / milestones wrong / approach wrong)
      → restart at Phase 1 or 2 with adjustments
    - aborts → stop, leave the handoff dir intact for next attempt
  → DO NOT proceed on silence. DO NOT interpret vague replies as approval.
    Wait until you get a clear confirm.

Phase 3: Per-Milestone Implementation (TDD-strict, no gates)
  For each Milestone in order:
    0. Use the exact canonical Milestone ID and name from the approved brief in
       plans, commentary, worklog entries, reviewer prompts, and status reports.
       Never renumber from a private checklist. If two representations disagree,
       stop and reconcile them with the user-visible approved plan.
    a. Invoke superpowers:test-driven-development AND tdd-with-fixtures
       — tests come BEFORE implementation, milestone NOT done if tests fail
    b. Implement to pass tests
    c. Validate (build / tests / smoke as appropriate). Reading code is NOT
       validation — run commands and observe output. If failure, fix or escalate;
       do not advance to next Milestone with red state.
    c.5. Audit (if project-side audit skills exist). After build/tests pass
       and BEFORE commit, check whether the project has audit skills under
       `<project-skill-root>/` (typical: `code-size-audit`,
       `code-clarity-audit`). For each existing one, invoke it on files
       modified by this Milestone. Findings are **non-blocking** — they do
       NOT stop the commit. Record findings in worklog.md "Audit Findings"
       sub-entry as input for a future cleanup commit or refactor task. If
       no such skill exists, skip silently. When multiple audit skills
       overlap on the same finding (e.g. size + clarity both report a long
       function), one main report + cross-reference is enough — do not
       duplicate the finding text.
    d. Commit. Format: `<type>: <subject>` (e.g. `feat:` / `fix:` / `refactor:` /
       `docs:`). One theme per commit. Commit only at stable points
       (build passes, tests pass).
    e. Append entry to worklog.md (format below). Maintain the Milestone
       failure ledger required by `agent-lifecycle.md`; reviewer changes, new findings,
       green tests, and new commits do not reset it.

  Before every reviewer-driven edit:
    - perform the mandatory finding triage in `agent-lifecycle.md`;
    - cite the exact approved acceptance criterion/Milestone goal it implements;
    - treat `Critical` / `Important` only as severity, never as scope authority;
    - stop immediately for a new process, transport, protocol, public interface,
      persistent schema, dependency, authentication/trust boundary, threat model,
      or lifecycle mechanism that the approved brief did not authorize;
    - stop on a real platform result that disproves an architectural assumption;
      report the evidence and options instead of designing around it silently.

  Escalation conditions (stop and notify user):
    - Same milestone fails verification 3 times in a row → escalate per agent-lifecycle.md
    - Same milestone is rejected by spec/code review 3 times → stop before a
      fourth remediation, even if every intermediate test run is green and
      each review reports different findings
    - Build broken and can't be fixed within one fix attempt → escalate
    - Scope ambiguity discovered (acceptance criteria insufficient) → escalate
    - Reviewer asks for an interface, security boundary, behavior, or
      architecture not traceable to the approved brief → treat as a scope
      change and escalate immediately; do not convert it into a requirement
    - User explicitly pauses or revokes the task → honor that instruction

  A status question alone: respond with current worklog state, then continue
  authorized work; it is not an escalation or a new approval gate.

Phase 4: Self-Review and Result
  → CONSISTENCY GATE (do this FIRST — autonomous has no per-Milestone gate, so this is
    the coverage backstop; it is a DIFFERENT lens than code-review: "做的 ↔ 当初说的对得上吗",
    not "代码质量好不好"):
      - Coverage, both directions: does every Acceptance Criterion + Milestone in brief.md
        have corresponding implementation? AND was anything built that brief.md did NOT
        ask for (silent scope creep)?
      - Spec-quality leftovers: any vague/unmeasurable acceptance criteria, or unresolved
        TODO / ??? / placeholder shipped?
      - Record gaps in result.md with severity (CRITICAL / HIGH / MEDIUM / LOW). A CRITICAL
        coverage gap means the task is NOT done — fix or escalate, do not write result.md as complete.
  → SCOPE ATTRIBUTION (all tasks; never skip):
      Compare every task-owned change with the approved Milestones:
        - committed: `git diff --name-status <TASK_BASELINE>..HEAD` and
          `git diff <TASK_BASELINE>..HEAD`;
        - staged: `git diff --cached --name-status` and `git diff --cached`;
        - unstaged: `git diff --name-status` and `git diff`;
        - untracked: `git ls-files --others --exclude-standard`, then inspect each
          task-owned file's content.
      Pre-existing dirty paths are already resolved at the plan gate; do not exclude
      them wholesale or guess which edits belong to the task afterward. Every change
      must trace to a Milestone goal. Flag silent scope creep in result.md and fix it
      before completion.
  → CHAIN VALIDATION (if the task had 2+ Milestones that touched shared files):
      The Milestone-level validation (build / tests / smoke) only checks current-Milestone
      correctness. When multiple Milestones touch the same checkout sequentially, cumulative
      damage — cross-Milestone interference, stale artifacts, unnoticed side effects — can
      escape per-Milestone checks. Validate:
        1. Run the full test suite (not just the last Milestone's tests). All tests that
           passed before must still pass. If the project has no test suite, run a full build
           and a smoke test end-to-end.
        2. Check for stale / orphaned code: any code path that an earlier Milestone added
           but a later Milestone bypassed or replaced should be cleaned up, not left dormant.
        3. Check for test pollution: if tests are stateful (shared databases, caches, temp
           directories, environment variables), verify that earlier Milestone tests did not
           leave residues that affect later test results.
        4. Record findings in worklog.md under a "Chain Validation" entry.
      If any of these fail, do not declare completion — fix the cumulative damage first.
      If the task had only 1 Milestone, or Milestones touched entirely disjoint files,
      this step can be skipped (document why briefly in result.md).
  → PERSISTENT-RULE EVIDENCE CHECK (when the task proposes a new workflow rule, test
    constraint, guardrail, or memory entry):
      Treat the proposed rule as a separate deliverable from the code change. Classify
      the evidence before proposing it for an AGENTS.md, CLAUDE.md, skill, or other
      persistent rule store:
        - confirmed: a reproducible triggering trace plus an independent oracle,
          authoritative source / documentation, or other trustworthy external evidence;
        - provisional: credible log / incident evidence exists but reproduction or scope
          is unstable or environment-dependent;
        - suggestion: only a plausibility argument or a single unverified observation.
      Evidence level does not authorize promotion. Evaluate eligibility exclusively under
      `guidelines/workflow/knowledge-promotion.md`, then surface the candidate for user
      approval; never auto-write a promoted rule. Record the proposed rule, evidence level,
      policy route, and disposition in result.md. A rule cannot become confirmed merely
      because adding it leaves the current tests green.
  → invoke superpowers:requesting-code-review adversarially against your own work
    (focus: cross-Milestone consistency, integration risks not visible per Milestone)
  → SKILL-WORTHY LESSON AUDIT: self-question against the worklog —
       "Did anything emerge during this task that should fire automatically
        for FUTURE work (a pattern, contract, anti-pattern, or convention)?"
     For each candidate, classify:
       - **Project skill candidate**: the rule only makes sense in THIS project
         (uses project helpers / business invariants / data conventions).
         Target location: `<project-skill-root>/<name>/SKILL.md`. Low bar.
       - **Global skill candidate**: rule applies across projects / framework
         level. Target location: `agent_coding_guidelines/skills/`. Higher bar:
         needs evidence per knowledge-promotion.md (two-strike rule, hidden
         contract, validated workflow pattern, etc.)
     Surface candidates in result.md "Skill Candidates" section.
     DO NOT auto-create skill files — propose only. User decides whether/how
     to create.
     If nothing skill-worthy emerged, explicitly say so in result.md (avoids
     ambiguity between "nothing emerged" and "agent forgot to audit").
  → ★ Pattern catalog audit (if project has pattern-recognition-prep skill).
    Invoke it in WRITE direction on the work just done:
       - Did the implementation touch an existing Established / Watching
         pattern? → add this task as a new "Uses" entry (user approve)
       - Did a novel architectural pattern emerge? → draft a Watching entry
         (three-question check: generic / architectural-level / abstraction-
         level reasonable), surface for user approval
       - Did a Watching pattern hit its 3rd use this task? → propose promotion
         to Established with a full entry draft
     Record findings in result.md "Pattern Catalog Update" section. DO NOT
     auto-write to the catalog — propose drafts only, user decides.
     If skill absent or no updates, say so explicitly.
  → write result.md with conclusion, all changes, commits, test results,
    known limitations, recommended next steps, AND skill candidates
  → DAILY LOG + OPEN-ITEMS SYNC: per `guidelines/workflow/daily-and-open-items.md`:
       - Append entry to today's `<agent-state-root>/daily/YYYY-MM-DD.md` under the
         relevant project section, with reference to `handoffs/<task-slug>/result.md`
       - Sync task status to `<agent-state-root>/projects/<project>/open-items.md`:
         - task fully done → remove or close the in-flight item; record under
           daily's "Open Items Δ → Closed"
         - task escalated / incomplete → ensure an in-flight item exists with
           "paused at X" reference; record under daily's "Open Items Δ → Added"
           if newly added
       - daily.md is append-only; open-items.md can be freely edited
  → notify user: "task complete, result at <path>; daily logged"
  → DO NOT auto-archive the handoff dir. Let it stay at `handoffs/<task-slug>/`
    until the user explicitly decides to archive (see "Completion and Archival" below).
```

## Document Locations

Per `guidelines/collaboration/private-docs-policy.md`: agent artifacts (everything tied to a single task — design plans, impl plans, kickoff prompts, session logs, handoffs, research scratch, etc.) are agent-to-agent / agent-to-future-user communication, **NOT** project deliverables. They must never be committed to project git.

### Agent Artifact Layout

Agent artifacts live under `<agent-state-root>/projects/<project>/`, organized into 5 sibling subdirectories:

| Subdirectory | Holds | Used by |
|--------------|-------|---------|
| `sessions/` | Session execution logs (per-session summaries) | All workflows |
| `handoffs/<task-slug>/` | Autonomous workflow four files (brief / context / worklog / result), and cross-session handoff docs | Autonomous workflow; cross-session/agent handoff |
| `plans/` | Task-level design + impl-plan (the per-task ones, NOT the project-deliverable ones) | Supervised workflow, ad-hoc discussion |
| `research/` | Pre-implementation research, scratch analysis, third-party comparison | Any workflow that needs investigation |
| `prompts/` | Kickoff prompts for next session, starter-kit material, collaboration prompts for teammates | Cross-session continuation |

Each subdirectory has its own `Archive/` for completed / superseded artifacts. Archival is **user-driven** — the agent does not auto-archive.

The `memory/` subdirectory at the same level is the auto-memory system. It is orthogonal to these 5 — it holds long-term user / feedback / project / reference memories, not single-task artifacts.

Distinction from project deliverables: a `design.md` or `impl-plan.md` that the user has explicitly committed to project git (e.g. inside `Plugins/<Plugin>/Docs/Plans/`) is a project deliverable, not an agent artifact. Promotion / demotion between the two categories is always user-decided; the agent does not propose moves.

### `<handoff-root>` Resolution

For autonomous workflow specifically, `<handoff-root>` = `<agent-state-root>/projects/<project>/handoffs/` (the `handoffs/` row in the table above).

Resolution order (in priority):
1. If project AGENTS.md specifies a handoff directory → use it (project override)
2. Default: `<agent-state-root>/projects/<project>/handoffs/` (matches the Agent Artifact Layout)
3. Fallback when no `<project>` directory mapping is available: create `_agent_private/<project-name>/handoffs/` at workspace level and use it (notify user of the choice)

**Never** put handoff docs inside the project tree where they would be committed.

### Task Slug Convention

Format: `YYYY-MM-DD-<short-kebab-case>/`

Examples:
- `2026-05-11-fix-session-expiry/`
- `2026-05-11-add-patrol-callback/`
- `2026-05-11-refactor-dialogue-cache/`

Date prefix is **mandatory**. Reasons:
- Keeps the directory tree sorted chronologically — recent tasks are at the bottom
- Aligns with the existing `sessions/` and `plans/` naming conventions in this layout
- When the same task is redone or revised, a new date prefix makes the relationship to prior runs visible without overwriting

### Autonomous Task Artifact Convergence

An autonomous workflow run produces **all** its task artifacts inside the single directory `handoffs/<task-slug>/`. Do NOT scatter to sibling subdirectories (`plans/` / `research/` / `prompts/`).

Specifically:
- `brief.md` / `context.md` / `worklog.md` / `result.md` — the four standard files
- Task-internal research notes → inline section in `context.md`, not a separate file in `research/`
- Task-internal design / impl-plan → covered by `brief.md`'s "Milestone Plan" section, not a separate file in `plans/`

Other workflows (supervised, ad-hoc discussion) may use `plans/` / `research/` / `prompts/` directly — that is fine. The convergence rule applies only to artifacts produced inside an autonomous workflow run.

### Completion and Archival

After Phase 4 completes (result.md written, user notified):
- The `handoffs/<task-slug>/` directory **stays in place** by default. Do not delete, do not move automatically.
- Archival is user-decided. The user may either:
  - Manually move `handoffs/<task-slug>/` to `handoffs/Archive/<task-slug>/`
  - Explicitly tell the agent: "archive task X" / "归档 task X" → agent moves it
- Do NOT auto-archive even when the user says the task is "done" or "ship 了". The artifact stays accessible for ad-hoc audit until the user actively decides it is no longer needed.

The same rule applies to artifacts in the other 4 subdirectories: archival is always user-driven.

## Document Discipline

### brief.md

```markdown
# Task: <title>

## Statement
<one paragraph: what is being done and why>

## In Scope
- <bullet>
- ...

## Out of Scope
- <bullet>
- ...

## Acceptance Criteria
- <observable, verifiable conditions>

## Milestone Plan
(filled in at end of Phase 2)
1. <Milestone 1 name> — <one-line goal>
2. <Milestone 2 name> — <one-line goal>
...
```

### context.md

```markdown
# Context

## Relevant Files
- <path>: <one-line why relevant>

## Constraints
- <e.g., must not break existing X; must complete before Y>

## Known Risks
- <e.g., shared with team A; depends on Y branch>

## Framework / Engine References
- <engine source paths, prior project decisions, related guidelines>

## Manual Test Cases (accumulated during Phase 3)
- TC-1: ... (created by tdd-with-fixtures Rule 3)
- ...
```

### worklog.md (append-only)

One entry per Milestone. Append-only — **never edit prior entries**.

```markdown
## Milestone <N>: <name>

**Started**: <timestamp>
**Completed**: <timestamp or "in progress">
**Files changed**: <list>
**Commit**: <hash>
**Tests**:
  - Auto: <N pass / M fail>
  - Manual cases verified: <TC-id list>
**Deviations from plan**: <none / description with reason>
**Audit Findings**: <"no audit skills present" / "no findings" / bullet list per audit skill (e.g. "size: 2 findings; clarity: 1 finding") with optional severity>
**Notes**: <anything notable>
```

### result.md (written at end of Phase 4)

```markdown
# Result: <task title>

## Conclusion
<one paragraph: was the task achieved against acceptance criteria>

## Files Changed
<full list across all Milestones>

## Commits
- <hash> <subject>
- ...

## Test Results
- Auto-tests: <summary>
- Manual cases: <TC-id list, all verified>
- Fixtures added: <list>

## Known Limitations
- <anything the user should know that wasn't in scope>

## Skill Candidates
<from Phase 4 audit; classify each as project / global>
- **Project skill candidate**: <name + one-line rule>. Rationale: <why this should fire automatically for future work in this project>.
- **Global skill candidate**: <name + one-line rule>. Rationale: <evidence of cross-project applicability or hidden contract>.
- (or "None — nothing skill-worthy emerged in this task" if audit found nothing)

## Recommended Next Steps
- <follow-up items, if any>
```

## Commit Permission Pre-Flight

Task authorization and host enforcement are separate. Per `commits.md`, approved
implementation includes local commits of verified task results; it does not
include push, history rewriting, or permission-setting changes. A host allow rule
does not grant those actions, and a task instruction does not override host policy.

### Detection (Phase 0)

- **Claude Code:** inspect the active permission mode and applicable rules, using
  the available permission view or settings files. A matching `ask` rule is a
  possible interruption; do not infer the outcome from one setting alone.
- **Codex:** inspect the approval and sandbox policy exposed to this session.
  Do not infer it from Claude settings or change `.codex/config.toml` to bypass it.

If an actual restriction may prevent unattended commits, explain it at the plan
gate. The user can handle prompts through the host or choose to adjust their
configuration separately. Do not require a permission lift to start every task.

### When the Host Intervenes

Follow the host's approval or denial mechanism. Do not edit permission settings,
switch tools, or disable checks to avoid it. Report what is blocked and continue
independent authorized work when possible; do not claim a required commit exists
when it did not run. Do not create empty or otherwise unnecessary commits merely
to test permission behavior; use the next real, validated task commit.

No permission changes or restoration steps are part of this workflow. A separate
user request to configure the host is a separate task with its own scope.

### Reference

See `techniques/claude-code-autonomous-permissions.md` for the distinction between
task authorization and Claude Code permission configuration.

## TDD Is Mandatory Here

The plan gate catches strategic bias; it does NOT catch missing tests during execution. Once the plan is approved and Phase 3 starts, there is **no user gate during implementation** — `tdd-with-fixtures` is the only safety net for per-Milestone correctness.

- Every Milestone must pass its tests before being marked complete in worklog.md
- A Milestone with `Tests: N fail > 0` is **not done** — do not advance to next Milestone
- Auto-test can't cover a behavior → `tdd-with-fixtures` Rule 3 (fixture + manual case in context.md)
- Manual case with `Last verified: never` does not count — must run it before marking the Milestone done

## Escalation Discipline

Per `guidelines/workflow/agent-lifecycle.md` (Failure Escalation):

| Attempt | Action |
|---|---|
| 1st failure of a Milestone | Retry once with a focused fix based on the error |
| 2nd failure | Change approach entirely |
| 3rd failure | **Stop**, write current state to worklog.md, notify user with summary |

Never let a failing approach loop more than three times. Autonomous mode does not mean "keep trying alone forever" — it means "do the work the user delegated, escalate when blocked."

Other escalation triggers (immediate, no retry):
- Scope ambiguity that brief.md cannot resolve
- A decision that touches architecture not anticipated in Phase 1
- A necessary next step requires an action or target outside existing authorization
  (for example an unapproved
  destructive operation, push, or shared-infrastructure change)
- **The approved approach turns out infeasible** — not an execution failure, but the plan
  itself cannot reach the acceptance criteria (structural convergence problem, unreachable
  oracle). Gather the evidence, then stop and return with root cause + alternatives for a
  re-decision. Do **not** spend the 3-strike budget on it, and do not silently switch
  approach: plan approval covers the approved plan, so replacing it needs the user again.

When escalating: write current state to worklog.md, then notify user with: which Milestone, what failed, what was tried, what's needed.

## Status Queries Mid-Work

If user returns mid-work and asks "how's it going" / "什么进度":
- Read current state from worklog.md
- Respond concisely: which Milestone is active, what's done, any concerns
- Continue authorized work after the update unless the user pauses, redirects,
  or revokes it; a status question alone is not a request to stop.

This is not a gate (no waiting for confirm). It's a courtesy interrupt the user invokes by asking.

## Trivial-Task Exclusion

If during Phase 1 you discover the task is trivial (typo, single mechanical change, doc-only edit):
- Halt the workflow
- Notify user: "this is trivial, dropping out of autonomous workflow"
- Just do the work directly

Do not force the chain on trivial work. Same rule as supervised-workflow.

## Interaction with Other Skills

This skill is an **orchestrator**:

- `superpowers:brainstorming` — used mentally in Phase 1 (no user pause); output goes to brief.md and context.md
- `superpowers:writing-plans` — owns Phase 2; output goes into brief.md plan section
- `superpowers:executing-plans` — owns the per-Milestone execution structure in Phase 3
- `superpowers:test-driven-development` — invoked inside each Milestone in Phase 3 (red/green/refactor cycle)
- `tdd-with-fixtures` — invoked inside each Milestone in Phase 3 (milestone discipline + fixture/manual escape hatch). **Non-negotiable** — autonomous workflow cannot suspend its rules.
- Project-side audit skills (optional, plural) — typical names: `code-size-audit`, `code-clarity-audit`. If the project has any under `<project-skill-root>/`, invoke each at Phase 3 step c.5 (after build/tests pass, before commit) for each Milestone. Findings are **non-blocking** and recorded in worklog.md "Audit Findings". If no such skills exist, skip silently — do not warn the user. When multiple audit skills overlap on the same finding (e.g. size + clarity both flag a long function), one main report + cross-reference is enough — do not duplicate.
- Project-side `pattern-recognition-prep` skill (optional, design-time prep) — if `<project-skill-root>/pattern-recognition-prep/SKILL.md` exists, invoke it at Phase 1 (read direction: surface reusable Established / Watching patterns to inform plan) and Phase 4 (write direction: audit if novel pattern emerged for Watching addition / Watching → Established promotion). Findings are **non-blocking** but **architecturally important** (Phase 1 findings drive Milestone breakdown to favor reuse over re-implementation). User approve required before any catalog write.
- `superpowers:requesting-code-review` — owns Phase 4 (applied to own work adversarially)

When composing these, **follow each composed skill's discipline fully**. Autonomous does not authorize skipping; it just removes the user-review pauses.

Composed skills do not add default approval pauses for decisions already covered
by the approved scope and test strategy. Record their preparation and rationale
and proceed. Explicit user checkpoints, required manual verification, host
approvals, and scope-change escalation still apply.

The orchestration limits in this skill and `agent-lifecycle.md` take precedence
over an imported workflow's unbounded review wording. In particular,
`subagent-driven-development` phrases such as "repeat until approved" mean
"repeat within the shared three-failure budget." They never authorize a fourth
attempt or a silent scope/architecture expansion.

The root coordinator owns this decision. Do not delegate scope authority to a
spec reviewer, quality reviewer, or implementer. Their findings are evidence to
triage against the approved plan, not amendments to it.

## Failure Modes

| Failure | Looks like | Correct action |
|---|---|---|
| Skipping the plan gate | Advancing from Phase 2 to Phase 3 without explicit user approval of plan | Hard stop after Phase 2. Output framing + milestones, wait for confirm. Vague replies do not count. |
| Treating plan approval as carte blanche | Major scope expansion or design changes mid-implementation | Approval covers the approved plan. Anything outside it = scope change = escalate. |
| Skipping documentation | "I implemented it, no need to write worklog" | All four files are mandatory artifacts, not optional. Write them. |
| Advancing past failing tests | Mark Milestone done with red tests | Milestone NOT done. Fix or escalate. |
| Looping on a failed approach | 5th attempt on same Milestone | Stop at attempt 3, escalate per agent-lifecycle.md |
| Resetting the counter because tests are green or a reviewer found a different issue | Fourth review/remediation pass on one Milestone | Review rejection is still a failed iteration; stop after the third and notify the user |
| Treating `repeat until approved` as unbounded | Continuing because a composed skill requests another re-review | The shared three-failure budget overrides it |
| Editing past worklog entries | Rewriting Milestone 1 entry after Milestone 3 found issues | worklog is append-only. Add a new entry noting the correction. |
| Treating autonomous as "no rules" | Skipping commits, skipping tests, skipping docs | Autonomous removes per-Milestone gates, not discipline. Discipline + plan gate are the substitutes. |
| Silent scope expansion | Realizing brief.md was too narrow, expanding without notifying user | Escalate. Scope changes require user input. |
| Severity becomes authorization | Reviewer labels an unplanned hardening idea `Important`, so it is implemented | Classify against the approved plan; record advisory work or escalate scope |
| Architecture called an implementation detail | Adding a process, transport, protocol, auth layer, schema, or lifecycle hook to finish a Milestone | Stop immediately and return to the user; naming it a detail does not keep it in scope |
| Threat-model drift | Trusted same-machine scope grows defenses against malicious local or remote actors | Preserve the approved threat model; propose the expansion to the user |
| Milestone identity drift | Private handoff says M5 while the user-visible plan says M4 | Stop, use the canonical user-approved Milestone ID, and reconcile records before continuing |
| Committing handoff docs | brief.md ends up in `git status` | Move to private location per `private-docs-policy.md` |
| Host blocks a required commit | A real task commit prompts or is denied | Use the host's approval path, report the restriction, and continue independent authorized work; do not edit settings to bypass it. |
| Missing pre-flight | Host limitations were not checked | Check them now and report any unresolved restriction; do not repeat completed planning merely to replay Phase 0. |

## Related

- `guidelines/workflow/agent-lifecycle.md` — escalation discipline (3-strike rule)
- `guidelines/workflow/handoffs.md` — document template inspiration (different topology: that one is multi-chat, this is single-chat with future-user as reader)
- `guidelines/collaboration/private-docs-policy.md` — handoff docs must NOT be committed
- `guidelines/code/validation.md` — verification at each Milestone
- `guidelines/workflow/commits.md` — commit format
- `techniques/claude-code-autonomous-permissions.md` — task authorization versus host enforcement; diagnosis of commit prompts
- `guidelines/claude-code/autonomous-loop-scheduling.md` — Claude Code only: driving the gateless Phase 3 across turns / compaction / disconnects with `/loop` dynamic + `ScheduleWakeup`, plus when `/goal` is the better driver instead
- `skills/tdd-with-fixtures/SKILL.md` — mandatory test discipline, the safety net
- `skills/workflow/supervised-workflow/SKILL.md` — sibling workflow with gates; switch to this if user wants in-the-loop review
