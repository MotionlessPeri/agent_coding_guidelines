---
name: autonomous-workflow
description: Low-touch workflow orchestrator for substantial tasks. Composes superpowers brainstorming, writing-plans, executing-plans, and requesting-code-review with EXACTLY ONE user-review gate — at the plan stage. After the user approves the plan, execution runs without further gates. Three safety nets: (1) plan gate catches strategic bias before any code is written, (2) handoff-style documentation (brief / context / worklog / result) lets the user audit afterward, (3) mandatory tdd-with-fixtures discipline blocks milestone advancement on failing tests. Use when the user explicitly requests autonomous workflow OR when the task is functional-only with a clear pre-defined pipeline and the user does not want to be in the loop for per-milestone reviews. Skip for trivial tasks and for tasks where architectural decisions need user involvement throughout.
when_to_use: User explicitly says "use autonomous / 自主 / agent-led / 你自己来" workflow, OR user asks agent to evaluate workflow choice and the task is functional-only with a clear pipeline AND the user does not want per-milestone review (one plan-review checkpoint is still required). Skip when supervised workflow is selected, when the task is trivial, or when architectural decisions need user input throughout.
---

# Autonomous Workflow

Orchestrator skill. Same composition chain as `supervised-workflow` but only **one user-review gate** — at the plan stage. After plan approval, execution runs without further gates. Three safety nets:

1. **Plan gate** — catches strategic bias (wrong scope / wrong approach / wrong milestone breakdown) BEFORE any code is written. Cheapest possible insurance, highest leverage of the three.
2. **Documentation** — durable handoff artifacts (brief / context / worklog / result) let the user audit afterward. Worklog is append-only and readable as a status check anytime.
3. **TDD discipline** — `tdd-with-fixtures` is mandatory; failing tests block milestone advancement. Acts as the safety net during the gateless execution phase.

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
  → PRE-FLIGHT: check commit permission state (see "Commit Permission Pre-Flight"
    section below). If commit is gated by `ask`, surface finding at plan gate so
    user picks a handling option before Phase 3 starts.

Phase 1: Self-Brainstorm
  → invoke superpowers:brainstorming mentally — do NOT pause for user
  → write brief.md: task statement, in scope, out of scope, acceptance criteria
  → write context.md: relevant files, constraints, known risks,
    framework references (engine source pointers, related guidelines)

Phase 2: Self-Plan
  → invoke superpowers:writing-plans
  → break into 3-7 Milestones (see supervised-workflow for granularity guidance)
  → append plan section to brief.md with Milestone list:
    each Milestone has goal, files touched, test approach, completion criteria

[GATE — the only gate in this workflow]
  → output to user: framing summary (from brief.md) + Milestone list,
    one-screen total. Concise, not the full file dump.
  → wait for explicit user response:
    - confirms → advance to Phase 3
    - redirects (scope wrong / milestones wrong / approach wrong)
      → restart at Phase 1 or 2 with adjustments
    - aborts → stop, leave the handoff dir intact for next attempt
  → DO NOT proceed on silence. DO NOT interpret vague replies as approval.
    Wait until you get a clear confirm.

Phase 3: Per-Milestone Implementation (TDD-strict, no gates)
  For each Milestone in order:
    a. Invoke superpowers:test-driven-development AND tdd-with-fixtures
       — tests come BEFORE implementation, milestone NOT done if tests fail
    b. Implement to pass tests
    c. Validate (build / tests / smoke as appropriate). Reading code is NOT
       validation — run commands and observe output. If failure, fix or escalate;
       do not advance to next Milestone with red state.
    c.5. Audit (if project-side audit skills exist). After build/tests pass
       and BEFORE commit, check whether the project has audit skills under
       `<project>/.claude/skills/` (typical: `code-size-audit`,
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
    e. Append entry to worklog.md (format below)

  Escalation conditions (stop and notify user):
    - Same milestone fails verification 3 times in a row → escalate per agent-lifecycle.md
    - Build broken and can't be fixed within one fix attempt → escalate
    - Scope ambiguity discovered (acceptance criteria insufficient) → escalate
    - User explicitly interrupts asking for status → respond with current worklog state

Phase 4: Self-Review and Result
  → invoke superpowers:requesting-code-review adversarially against your own work
    (focus: cross-Milestone consistency, integration risks not visible per Milestone)
  → IF Option B was chosen at plan gate (agent lifted commit gate at Phase 0):
       restore the `ask` rule by reverse-editing the same settings file(s).
       Verify by reading the setting back. Record restoration in result.md.
       Restoration is NON-NEGOTIABLE — workflow is not complete without it.
  → SKILL-WORTHY LESSON AUDIT: self-question against the worklog —
       "Did anything emerge during this task that should fire automatically
        for FUTURE work (a pattern, contract, anti-pattern, or convention)?"
     For each candidate, classify:
       - **Project skill candidate**: the rule only makes sense in THIS project
         (uses project helpers / business invariants / data conventions).
         Target location: `<project>/.claude/skills/<name>/SKILL.md`. Low bar.
       - **Global skill candidate**: rule applies across projects / framework
         level. Target location: `agent_coding_guidelines/skills/`. Higher bar:
         needs evidence per knowledge-promotion.md (two-strike rule, hidden
         contract, validated workflow pattern, etc.)
     Surface candidates in result.md "Skill Candidates" section.
     DO NOT auto-create skill files — propose only. User decides whether/how
     to create.
     If nothing skill-worthy emerged, explicitly say so in result.md (avoids
     ambiguity between "nothing emerged" and "agent forgot to audit").
  → write result.md with conclusion, all changes, commits, test results,
    known limitations, recommended next steps, AND skill candidates
  → DAILY LOG + OPEN-ITEMS SYNC: per `guidelines/workflow/daily-and-open-items.md`:
       - Append entry to today's `~/.claude/daily/YYYY-MM-DD.md` under the
         relevant project section, with reference to `handoffs/<task-slug>/result.md`
       - Sync task status to `~/.claude/projects/<project>/open-items.md`:
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

Agent artifacts live under `~/.claude/projects/<project>/`, organized into 5 sibling subdirectories:

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

For autonomous workflow specifically, `<handoff-root>` = `~/.claude/projects/<project>/handoffs/` (the `handoffs/` row in the table above).

Resolution order (in priority):
1. If project AGENTS.md specifies a handoff directory → use it (project override)
2. Default: `~/.claude/projects/<project>/handoffs/` (matches the Agent Artifact Layout)
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

Autonomous Phase 3 commits per Milestone. If `git commit` is gated by a `permissions.ask` rule in user or project settings, every commit prompts — user is offline (that's the point of autonomous) → workflow stalls indefinitely.

### Detection (Phase 0)

Read `~/.claude/settings.json` and (if present) the project's `.claude/settings.json` / `.claude/settings.local.json`. Look for `Bash(git commit:*)` or `Bash(git commit*)` in the `permissions.ask` list.

If found in ANY of these files → commit is gated. Surface at plan gate.

### If Gated: Surface at Plan Gate

Plan gate output must include a "Pre-flight notice" section listing the gated location(s) and presenting three options to the user:

**A. User lifts before approving the plan.**
- User opens the relevant settings file(s)
- Moves the `Bash(git commit:*)` entry from `permissions.ask` to `permissions.allow`
- Verifies by running one trivial commit — should NOT prompt
- Tells agent to proceed
- User restores `ask` rule at task end (or opens a follow-up reminder)

**B. User authorizes agent to lift, agent restores at Phase 4 end.**
- Agent edits the same settings file(s): moves entry `ask` → `allow`
- Verifies (read setting back; or attempt trivial commit if safe)
- Records the lift in worklog.md including which file(s) were modified
- At Phase 4 end: reverse-edits the same files, verifies restoration, records in result.md
- Restoration is non-negotiable; result.md is NOT complete without it

**C. Proceed unlifted (will stall).**
- Phase 3 runs until first commit, halts on prompt, escalates to user
- Effectively switches to supervised behavior at commit time
- Useful only if user is briefly available at commit moments

### Discipline (Option B specifics)

- Authorization is **scoped to this task only**. Do not extend the lift to other operations or future tasks.
- If agent picks B but later fails to restore at Phase 4 end: escalate immediately, do not close result.md, do not declare the workflow complete.
- If user revokes authorization mid-task: stop, restore immediately, then continue under Option C or pause for redirection.

### Reference

Full rationale (safety net principles, scope precedence, diagnostic patterns for "why is it still prompting"): see `techniques/claude-code-autonomous-permissions.md` in the agent_coding_guidelines repo. The operational core above is sufficient for runtime; the technique doc is the deeper read.

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
- A safety boundary (would need destructive action, would push, would touch shared infra)

When escalating: write current state to worklog.md, then notify user with: which Milestone, what failed, what was tried, what's needed.

## Status Queries Mid-Work

If user returns mid-work and asks "how's it going" / "什么进度":
- Read current state from worklog.md
- Respond concisely: which Milestone is active, what's done, any concerns
- Continue or pause based on user response

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
- Project-side audit skills (optional, plural) — typical names: `code-size-audit`, `code-clarity-audit`. If the project has any under `<project>/.claude/skills/`, invoke each at Phase 3 step c.5 (after build/tests pass, before commit) for each Milestone. Findings are **non-blocking** and recorded in worklog.md "Audit Findings". If no such skills exist, skip silently — do not warn the user. When multiple audit skills overlap on the same finding (e.g. size + clarity both flag a long function), one main report + cross-reference is enough — do not duplicate.
- `superpowers:requesting-code-review` — owns Phase 4 (applied to own work adversarially)

When composing these, **follow each composed skill's discipline fully**. Autonomous does not authorize skipping; it just removes the user-review pauses.

## Failure Modes

| Failure | Looks like | Correct action |
|---|---|---|
| Skipping the plan gate | Advancing from Phase 2 to Phase 3 without explicit user approval of plan | Hard stop after Phase 2. Output framing + milestones, wait for confirm. Vague replies do not count. |
| Treating plan approval as carte blanche | Major scope expansion or design changes mid-implementation | Approval covers the approved plan. Anything outside it = scope change = escalate. |
| Skipping documentation | "I implemented it, no need to write worklog" | All four files are mandatory artifacts, not optional. Write them. |
| Advancing past failing tests | Mark Milestone done with red tests | Milestone NOT done. Fix or escalate. |
| Looping on a failed approach | 5th attempt on same Milestone | Stop at attempt 3, escalate per agent-lifecycle.md |
| Editing past worklog entries | Rewriting Milestone 1 entry after Milestone 3 found issues | worklog is append-only. Add a new entry noting the correction. |
| Treating autonomous as "no rules" | Skipping commits, skipping tests, skipping docs | Autonomous removes per-Milestone gates, not discipline. Discipline + plan gate are the substitutes. |
| Silent scope expansion | Realizing brief.md was too narrow, expanding without notifying user | Escalate. Scope changes require user input. |
| Committing handoff docs | brief.md ends up in `git status` | Move to private location per `private-docs-policy.md` |
| Stalling on commit prompt | Phase 3 halts at first Milestone commit because `Bash(git commit:*)` is in `ask` list | Pre-flight should have caught this. Escalate; workflow cannot continue without commit gate lifted. See Commit Permission Pre-Flight section. |
| Skipping pre-flight | Started Phase 1 / 2 without checking commit settings | Restart Phase 0 to do the check. Better caught early than at first commit. |
| Failing to restore after Option B | Phase 4 completed without restoring `ask` rule | Restoration is non-negotiable. Restore immediately, verify, append note to result.md. Workflow is not complete until restoration is confirmed. |

## Related

- `guidelines/workflow/agent-lifecycle.md` — escalation discipline (3-strike rule)
- `guidelines/workflow/handoffs.md` — document template inspiration (different topology: that one is multi-chat, this is single-chat with future-user as reader)
- `guidelines/collaboration/private-docs-policy.md` — handoff docs must NOT be committed
- `guidelines/code/validation.md` — verification at each Milestone
- `guidelines/workflow/commits.md` — commit format
- `techniques/claude-code-autonomous-permissions.md` — full rationale for commit permission lift; operational core is inlined above in Commit Permission Pre-Flight
- `skills/tdd-with-fixtures/SKILL.md` — mandatory test discipline, the safety net
- `skills/supervised-workflow/SKILL.md` — sibling workflow with gates; switch to this if user wants in-the-loop review
