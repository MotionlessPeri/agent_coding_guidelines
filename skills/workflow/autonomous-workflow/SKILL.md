---
name: autonomous-workflow
description: Use when the user requests autonomous work on a substantial task or wants only one implementation-plan approval. Skip trivial edits, unclear acceptance criteria, user-selected supervised work, and unresolved architecture or interface decisions.
---

# Autonomous Workflow

Orchestrator skill. Same composition chain as `supervised-workflow` but only **one user-review gate** — at the plan stage. After plan approval, execution runs without further gates. Three safety nets:

1. **Plan gate** — catches strategic bias (wrong scope / wrong approach / wrong milestone breakdown) BEFORE any code is written. Cheapest possible insurance, highest leverage of the three.
2. **Documentation** — durable handoff artifacts (brief + append-only worklog, with context and result sections) let the user audit afterward. Worklog is append-only and readable as a status check anytime.
3. **Verification** — apply TDD to new behavior and bugs, existing regression to covered refactors, and content checks to documentation. Required tests and manual cases block completion until verified.

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
| Final | requesting-code-review w/ user | self-review + <result-record> for user to read later |

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

## Reuse Existing Decisions and Evidence

Start at the first unfinished phase. Identify the user turn or durable record
that approved the design/plan and confirm it still covers the current task.
Reuse completed preparation and approvals; review only new or changed decisions.
Unresolved scope or architecture changes still need approval. An explicitly
requested new review remains a gate, even if an older approval exists.

For a resumed task, preserve its original task baseline and failure history;
record the current checkout status separately and resolve new ownership overlaps.
Do not reset the baseline to hide earlier task changes. Create a new baseline
only for a new task, not simply because the conversation resumed.

Use one review record for requirements coverage, scope attribution, correctness,
structure/comments, and integration findings. Reuse existing records rather than
creating a separate walkthrough tracking file. Each required review perspective
must still be covered; self-review does not substitute for required independent
review, user-requested walkthrough output, or human visual verification.

For reused verification, record the command/procedure, result, and tested source,
artifact and relevant environment state (commit plus any uncommitted changes).
Reuse evidence only while those inputs and its coverage remain applicable.
Changes affecting them require targeted re-verification; committing the same
tested content or an unrelated change alone does not invalidate evidence.
Existing full-suite/build evidence can satisfy a final check on that same state;
missing integration coverage still requires verification. Extra refactoring
remains subject to scope and user approval.

## The Chain

Five phases. **Exactly one hard gate** — after Phase 2 (plan). Phases 3 and 4 run without further approval gates. Reuse an existing applicable
plan approval rather than requesting it again; scope changes still escalate.
Each phase records its required information in the selected task layout.

```
Phase 0: Setup
  → generate task slug: YYYY-MM-DD-<short-kebab-case>
    e.g. "2026-05-11-fix-session-expiry", "2026-05-11-add-patrol-callback"
    (date prefix is mandatory — see "Task Slug Convention" below)
  → use the existing task directory when resuming; otherwise create
    <handoff-root>/<task-slug>/
  → initialize brief.md and append-only worklog.md using Document Discipline below;
    retain an existing four-file layout or required cross-conversation handoff contract
  → for a new task, record `TASK_BASELINE = git rev-parse HEAD` and the output of
    `git status --short` verbatim in <context-record>. If a planned Milestone overlaps a
    pre-existing dirty path, surface the overlap at the plan gate and do not start
    implementation until the user resolves it or explicitly defines ownership.
  → PRE-FLIGHT: check host constraints on local commits (see "Commit Permission
    Pre-Flight" below). If the active policy may interrupt unattended work,
    explain that limitation at the plan gate; do not change permission settings.

Phase 1: Self-Brainstorm
  → invoke superpowers:brainstorming mentally — do NOT pause for user
  → write brief.md: task statement, in scope, out of scope, acceptance criteria
  → write <context-record>: relevant files, constraints, known risks,
    framework references (engine source pointers, related guidelines)
  → ★ Pattern recognition (if project has it). Check whether the project has
    `<project-skill-root>/pattern-recognition-prep/SKILL.md`. If yes,
    invoke it on the task statement. Capture findings in <context-record> under
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
  → choose Milestones by coherent, verifiable delivery units; one is valid.
    Do not split merely to reach a target count. Each ends at a stable reviewable state.
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
  → use an existing applicable explicit approval, or wait for user response:
    - confirms → advance to Phase 3
    - redirects (scope wrong / milestones wrong / approach wrong)
      → restart at Phase 1 or 2 with adjustments
    - aborts → stop, leave the handoff dir intact for next attempt
  → DO NOT proceed on silence. DO NOT interpret vague replies as approval.
    Wait until you get a clear confirm.

Phase 3: Per-Milestone Implementation (verified, no gates)
  For each Milestone in order:
    0. Use the exact canonical Milestone ID and name from the approved brief in
       plans, commentary, worklog entries, reviewer prompts, and status reports.
       Never renumber from a private checklist. If two representations disagree,
       stop and reconcile them with the user-visible approved plan.
    a. Apply test skills within their own scope: new behavior and bug fixes
       require red-before-green; fixture/manual verification remains required
       where automation cannot cover behavior. For a pure refactor, run existing
       tests that cover the changed paths and retain their results. For doc-only
       or mechanical non-behavior changes, run applicable content/link checks
       rather than inventing a failing test. Missing coverage is not an exemption.
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
      - Record gaps in <result-record> with severity (CRITICAL / HIGH / MEDIUM / LOW). A CRITICAL
        coverage gap means the task is NOT done — fix or escalate, do not write <result-record> as complete.
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
      must trace to a Milestone goal. Flag silent scope creep in <result-record> and fix it
      before completion.
  → CHAIN VALIDATION (if the task had 2+ Milestones that touched shared files):
      The Milestone-level validation (build / tests / smoke) only checks current-Milestone
      correctness. When multiple Milestones touch the same checkout sequentially, cumulative
      damage — cross-Milestone interference, stale artifacts, unnoticed side effects — can
      escape per-Milestone checks. Validate:
        1. Run the full test suite, or reuse applicable full-suite evidence under
           "Reuse Existing Decisions and Evidence" above (not just the last
           Milestone's tests). All tests that
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
      this step can be skipped (document why briefly in <result-record>).
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
      policy route, and disposition in <result-record>. A rule cannot become confirmed merely
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
     Surface candidates in <result-record> "Skill Candidates" section.
     DO NOT auto-create skill files — propose only. User decides whether/how
     to create.
     If nothing skill-worthy emerged, explicitly say so in <result-record> (avoids
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
     Record findings in <result-record> "Pattern Catalog Update" section. DO NOT
     auto-write to the catalog — propose drafts only, user decides.
     If skill absent or no updates, say so explicitly.
  → write <result-record> with conclusion, all changes, commits, test results,
    known limitations, recommended next steps, AND skill candidates
  → DAILY LOG + OPEN-ITEMS SYNC: per `guidelines/workflow/daily-and-open-items.md`:
       - Append entry to today's `<agent-state-root>/daily/YYYY-MM-DD.md` under the
         relevant project section, with reference to the selected result record (file and section)
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
| `handoffs/<task-slug>/` | Autonomous task records and optional split context/result files, and cross-session handoff docs | Autonomous workflow; cross-session/agent handoff |
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
- `brief.md` and `worklog.md` by default; split context/result only when needed
  for readability or an existing handoff contract
- Task-internal research notes → inline section in `<context-record>`, not a separate file in `research/`
- Task-internal design / impl-plan → covered by `brief.md`'s "Milestone Plan" section, not a separate file in `plans/`

Other workflows (supervised, ad-hoc discussion) may use `plans/` / `research/` / `prompts/` directly — that is fine. The convergence rule applies only to artifacts produced inside an autonomous workflow run.

### Completion and Archival

After Phase 4 completes (<result-record> written, user notified):
- The `handoffs/<task-slug>/` directory **stays in place** by default. Do not delete, do not move automatically.
- Archival is user-decided. The user may either:
  - Manually move `handoffs/<task-slug>/` to `handoffs/Archive/<task-slug>/`
  - Explicitly tell the agent: "archive task X" / "归档 task X" → agent moves it
- Do NOT auto-archive even when the user says the task is "done" or "ship 了". The artifact stays accessible for ad-hoc audit until the user actively decides it is no longer needed.

The same rule applies to artifacts in the other 4 subdirectories: archival is always user-driven.

## Document Discipline

For new single-conversation tasks, use two files:
- `brief.md`: scope, acceptance criteria, plan, and the Context sections below.
- `worklog.md`: append-only progress/failure history; append the Result sections
  as a final entry at completion. Corrections are new entries, never rewrites.

Resolve `<context-record>` to the Context sections in brief.md and
`<result-record>` to the final Result entry in worklog.md. All fields below remain
required when relevant; merging files does not remove evidence or acceptance data.
Keep an existing four-file task or cross-conversation contract unchanged:
there, these placeholders resolve to `context.md` and `result.md` respectively.
For a new task, split those sections into files when their size or a handoff
consumer needs it, record the mapping once, and use it consistently. Do not
migrate or overwrite ongoing task records merely to adopt this default.


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

### Context sections (in brief.md by default)

```markdown
## Context

### Task Baseline and Ownership
- Original TASK_BASELINE and verbatim initial git status
- Resumption status and ownership decisions (preserve original baseline)

## Relevant Files
- <path>: <one-line why relevant>

## Constraints
- <e.g., must not break existing X; must complete before Y>

## Known Risks
- <e.g., shared with team A; depends on Y branch>

## Framework / Engine References
- <engine source paths, prior project decisions, related guidelines>

## Manual Test Cases (accumulated during Phase 3)
- TC-1: link to the durable project test archive and fixture (tdd-with-fixtures Rule 3)
- ...
```

### worklog.md (append-only)

Append a completion entry per Milestone; record interim progress, failures and
corrections as additional entries. Append-only — **never edit prior entries**.

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

### Result sections (append to worklog.md at end of Phase 4)

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

At Phase 0, inspect host constraints: Claude Code's active permission mode and
applicable rules, or Codex's exposed approval/sandbox policy. Do not infer one
host's behavior from another's settings or from a single allow rule.
Report restrictions that could interrupt unattended work at the plan gate.
Approved implementation includes verified local commits per `commits.md`, not
push, history rewriting or permission changes. Host capability is not authority.
Follow actual host approval/denial; do not switch tools, disable checks or edit
settings to bypass it. Report blocked actions and continue independent authorized
work; never claim a commit that did not run. Use a real task commit, not an empty
permission probe. Configuration changes are a separate user-authorized task;
this workflow has no permission-lift or restoration steps.
See `techniques/claude-code-autonomous-permissions.md` for host-specific details.

## Verification Discipline

Apply `superpowers:test-driven-development` and `tdd-with-fixtures` to the
behavior changes they cover, following Phase 3's change-type rules. A milestone
with failing required tests or an unverified required manual case is not done.
Fixtures and manual cases stay in the project's test archive; `<context-record>`
links to them rather than replacing that durable archive.

## Escalation Discipline

Apply the shared three-failure budget, finding triage and failure ledger in
`guidelines/workflow/agent-lifecycle.md`; Phase 3 lists workflow stop conditions.

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

## Trivial-Task Exclusion

If during Phase 1 you discover the task is trivial (typo, single mechanical change, doc-only edit):
- Halt the workflow
- Notify user: "this is trivial, dropping out of autonomous workflow"
- Just do the work directly

Do not force the chain on trivial work. Same rule as supervised-workflow.

## Interaction with Other Skills

This skill is an **orchestrator**:

- `superpowers:brainstorming` — used mentally in Phase 1 (no user pause); output goes to brief.md and <context-record>
- `superpowers:writing-plans` — owns Phase 2; output goes into brief.md plan section
- `superpowers:executing-plans` — owns the per-Milestone execution structure in Phase 3
- `superpowers:test-driven-development` — Phase 3 red/green/refactor for applicable behavior changes
- `tdd-with-fixtures` — applicable milestone verification and fixture/manual cases; respect its trigger and skip conditions, never bypass required tests.
- Project-side audit skills — invoke at Phase 3 c.5; keep one report per finding.
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

| Failure | Correct action |
|---|---|
| Rewriting old progress to match a changed plan | Append a correction to worklog.md; preserve prior entries. |
| Treating merged files as permission to omit evidence | Preserve all required task information in the chosen layout. |
| Private Milestone numbering diverges from the approved plan | Reconcile with the canonical user-approved IDs before continuing. |
| Handoff records appear in git status | Move them to the private location; never commit handoff records. |
| Pre-flight was missed | Check current restrictions and report them; do not repeat completed planning just to replay setup. |

## Related

- `guidelines/workflow/agent-lifecycle.md` — escalation discipline (3-strike rule)
- `guidelines/workflow/handoffs.md` — document template inspiration (different topology: that one is multi-chat, this is single-chat with future-user as reader)
- `guidelines/collaboration/private-docs-policy.md` — handoff docs must NOT be committed
- `guidelines/code/validation.md` — verification at each Milestone
- `guidelines/workflow/commits.md` — commit format
- `techniques/claude-code-autonomous-permissions.md` — task authorization versus host enforcement; diagnosis of commit prompts
- `guidelines/claude-code/autonomous-loop-scheduling.md` — Claude Code only: driving the gateless Phase 3 across turns / compaction / disconnects with `/loop` dynamic + `ScheduleWakeup`, plus when `/goal` is the better driver instead
- `skills/tdd-with-fixtures/SKILL.md` — verification discipline within its own scope
- `skills/workflow/supervised-workflow/SKILL.md` — sibling workflow with gates; switch to this if user wants in-the-loop review
