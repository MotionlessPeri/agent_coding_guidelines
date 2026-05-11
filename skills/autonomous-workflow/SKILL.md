---
name: autonomous-workflow
description: Low-touch workflow orchestrator for substantial tasks the user wants the agent to execute independently. Composes superpowers brainstorming, writing-plans, executing-plans, and requesting-code-review WITHOUT user review gates. Replaces gates with two safety nets — (1) handoff-style documentation (brief / context / worklog / result) so the user can audit the work afterward, and (2) mandatory tdd-with-fixtures discipline so failing tests block milestone advancement. Use when the user explicitly requests autonomous workflow OR when the task is functional-only with a clear pre-defined pipeline and the user signals unavailability. Skip for trivial tasks and for tasks where architectural decisions need user involvement.
when_to_use: User explicitly says "use autonomous / 自主 / agent-led / 你自己来" workflow, OR user asks agent to evaluate workflow choice and the task is functional-only with a clear pipeline AND the user signals unavailability for review. Skip when supervised workflow is selected, when the task is trivial, or when architectural decisions need user input.
---

# Autonomous Workflow

Orchestrator skill. Same composition chain as `supervised-workflow` but **no user-review gates**. Two replacement safety nets:

1. **Documentation** — durable handoff artifacts the user can audit after the fact
2. **TDD discipline** — `tdd-with-fixtures` is mandatory, not optional; failing tests block milestone advancement

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

Five phases. No gates between phases. Each phase has explicit doc artifacts.

```
Phase 0: Setup
  → generate task slug (short kebab-case from task description,
    e.g. "fix-session-expiry", "add-patrol-callback")
  → create handoff dir at <handoff-root>/<task-slug>/
  → initialize four files: brief.md, context.md, worklog.md, result.md (placeholder)

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

Phase 3: Per-Milestone Implementation (TDD-strict, no gates)
  For each Milestone in order:
    a. Invoke superpowers:test-driven-development AND tdd-with-fixtures
       — tests come BEFORE implementation, milestone NOT done if tests fail
    b. Implement to pass tests
    c. Run validation per guidelines/code/validation.md
    d. Commit per guidelines/workflow/commits.md
    e. Append entry to worklog.md (format below)

  Escalation conditions (stop and notify user):
    - Same milestone fails verification 3 times in a row → escalate per agent-lifecycle.md
    - Build broken and can't be fixed within one fix attempt → escalate
    - Scope ambiguity discovered (acceptance criteria insufficient) → escalate
    - User explicitly interrupts asking for status → respond with current worklog state

Phase 4: Self-Review and Result
  → invoke superpowers:requesting-code-review adversarially against your own work
    (focus: cross-Milestone consistency, integration risks not visible per Milestone)
  → write result.md with conclusion, all changes, commits, test results,
    known limitations, recommended next steps
  → notify user: "task complete, result at <path>"
```

## Document Locations

Per `guidelines/collaboration/private-docs-policy.md`: handoff documents are agent-to-agent / agent-to-future-user communication, **NOT** project deliverables. They must not be committed to project git.

**Default `<handoff-root>` resolution order:**

1. If project AGENTS.md specifies a handoff directory → use it
2. If `_agent_private/<project-name>/handoffs/` exists at workspace level → use it
3. If `~/.claude/projects/<project>/sessions/` exists → use it
4. Otherwise: create `_agent_private/<project-name>/handoffs/` at workspace level and use it (notify user of the choice)

**Never** put handoff docs inside the project tree where they would be committed.

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

## Recommended Next Steps
- <follow-up items, if any>
```

## TDD Is Mandatory Here

Inside autonomous workflow there is **no user gate** catching missing tests. `tdd-with-fixtures` is the only safety net.

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
- `superpowers:requesting-code-review` — owns Phase 4 (applied to own work adversarially)

When composing these, **follow each composed skill's discipline fully**. Autonomous does not authorize skipping; it just removes the user-review pauses.

## Failure Modes

| Failure | Looks like | Correct action |
|---|---|---|
| Skipping documentation | "I implemented it, no need to write worklog" | All four files are mandatory artifacts, not optional. Write them. |
| Advancing past failing tests | Mark Milestone done with red tests | Milestone NOT done. Fix or escalate. |
| Looping on a failed approach | 5th attempt on same Milestone | Stop at attempt 3, escalate per agent-lifecycle.md |
| Editing past worklog entries | Rewriting Milestone 1 entry after Milestone 3 found issues | worklog is append-only. Add a new entry noting the correction. |
| Treating autonomous as "no rules" | Skipping commits, skipping tests, skipping docs | Autonomous removes user gates, not discipline. Discipline is the substitute. |
| Silent scope expansion | Realizing brief.md was too narrow, expanding without notifying user | Escalate. Scope changes require user input. |
| Committing handoff docs | brief.md ends up in `git status` | Move to private location per `private-docs-policy.md` |

## Related

- `guidelines/workflow/agent-lifecycle.md` — escalation discipline (3-strike rule)
- `guidelines/workflow/handoffs.md` — document template inspiration (different topology: that one is multi-chat, this is single-chat with future-user as reader)
- `guidelines/collaboration/private-docs-policy.md` — handoff docs must NOT be committed
- `guidelines/code/validation.md` — verification at each Milestone
- `guidelines/workflow/commits.md` — commit format
- `skills/tdd-with-fixtures/SKILL.md` — mandatory test discipline, the safety net
- `skills/supervised-workflow/SKILL.md` — sibling workflow with gates; switch to this if user wants in-the-loop review
