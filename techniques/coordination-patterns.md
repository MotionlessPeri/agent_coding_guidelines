# Coordination Patterns

## Four-Phase Workflow

| Phase | Who | Purpose |
|-------|-----|---------|
| Research | Workers (parallel) | Investigate codebase, understand the problem |
| Synthesize | **Coordinator** | Read worker findings, understand the problem, formulate a plan |
| Implement | Workers | Execute the plan |
| Verify | Workers | Prove the changes work |

## Core Principle: Never Delegate Understanding

The coordinator's most important job is **synthesis**. After workers report research findings, the coordinator must understand them before directing implementation.

**Anti-patterns:**
- "Based on your findings, fix the bug" — delegates understanding to the worker
- "The researcher found an issue in the auth module, please fix it" — no synthesis

**Correct pattern:**
- "Fix the null pointer at `src/auth/validate.ts:42`. The session's `user` field is undefined when the session expires, but the token remains cached. Add a null check before accessing `user.id`; if null, return 401 with 'Session expired'."

**Rule: If your instruction contains "based on your findings" or "based on the research" — rewrite it. You have not synthesized.**

## Concurrency Rules

### Read-Write Separation
- Read-only tasks (research, search, analysis): freely parallel, no restrictions
- Write operations (implementation, editing): serialize within the same file region
- Verification: can run parallel to implementation on different file regions

### When to Parallelize
- Independent research across different modules — always parallel
- Multiple file edits in unrelated areas — can parallel
- Sequential dependencies (research → synthesize → implement → verify) — must be serial at phase boundaries

## Dependency Patterns

### Serial Chain
Research → Implement → Verify. Each step depends on the previous.

### Fan-Out (parallel research)
Multiple research workers investigate different modules simultaneously. Coordinator synthesizes all findings before proceeding.

### Fan-In (parallel implementation + unified verification)
Multiple implementation workers edit different modules. A single verification pass covers all changes after all workers complete.

## Continue vs. New Worker

| Situation | Decision | Reason |
|-----------|----------|--------|
| Research worker found the exact files to edit | Continue same worker | Already has file context |
| Research was broad but implementation is narrow | New worker | Avoid context noise |
| Correcting a failed attempt | Continue same worker | Already has error context |
| Verifying someone else's implementation | New worker | Fresh perspective, no anchoring |
| First approach was completely wrong | New worker | Avoid anchoring to failed strategy |

## Iterative Retrieval (when worker context cannot be predicted)

The default rule in `techniques/worker-instructions.md` is "make the prompt
self-contained" — list file paths, line numbers, completion criteria. This
works when the **coordinator already knows** which files / symbols the worker
needs.

For genuinely exploratory tasks — "find all places that handle X" / "review
every caller of Y for memory safety" / "is there an existing helper for Z?" —
the coordinator does not yet know the file set. Three naive options all fail:

- **Send everything**: exceeds worker context
- **Send nothing**: worker lacks critical context, makes wrong calls
- **Guess what's needed**: usually wrong; wastes a dispatch

### The 4-phase loop

```
  Dispatch ──▶ Evaluate ──▶ Refine ──▶ Loop (max 3 cycles)
  (broad      (what was    (worker     (then return findings
   initial     found vs     fetches     even if partial — do
   query)      what's       follow-up   not extend the budget)
               missing)     itself)
```

The defining move is **Phase 3 (Refine)**: the worker fetches its own follow-up
context (Grep / Read more files) instead of returning to the coordinator and
asking for permission. Each round-trip to the coordinator costs latency and
context — the worker should be empowered to dig deeper within its own session.

### When to use this pattern

- Worker task is **exploratory** (research, audit, "find all X")
- Coordinator can articulate the **goal** but not the **file set**
- Worker has Glob / Grep / Read tools available
- Sending whole repo would exceed worker context

### When NOT to use

- Coordinator already knows the file set → use standard self-contained prompt
- Task is **implementation** with clear target file (file paths are in the plan)
- Worker has only narrow read tools without search capability

### Worker prompt template

```
Task: [investigation goal in one sentence].

Phase 1 — Dispatch: start with [initial search query / glob pattern].

Phase 2 — Evaluate: after the initial sweep, report (to yourself):
  - what you found
  - what is still unclear / missing
  - what additional context you need

Phase 3 — Refine: based on Phase 2, fetch the additional context yourself
  (Grep / Read more files). DO NOT come back to ask permission for
  follow-up reads.

Phase 4 — Loop: max 2 more cycles, then return findings even if incomplete.

Report:
  - files investigated
  - what was found vs what was missed
  - confidence level
```

### Cap the loop

**Max 3 cycles total.** After that:

- Either the worker has enough → report findings
- Or the task is too broad → return partial findings + flag "needs scope reduction"

Do **not** extend the loop budget. If 3 cycles isn't enough, the coordinator
should reformulate the task — splitting it, narrowing the scope, or providing
a better initial dispatch query — rather than letting the worker spin.

## Failure Escalation

This applies the general failure escalation from `guidelines/workflow/agent-lifecycle.md` to the coordinator-worker context:

1. Worker fails → continue the same worker (already has error context)
2. Correction fails → change approach, still continue the same worker
3. Third failure → report to the user with a list of approaches tried and why each failed

**Never let a failing approach loop more than three times.**

## Stopping Misdirected Work

If the direction changes mid-task (user redirects, new information emerges):
- Stop the current worker immediately
- Do not let a wrong-direction worker run to completion
- Continue the same worker with corrected instructions (it has the existing context)

## Related Guidelines

- See `guidelines/collaboration/multi-agent.md` for declarative multi-agent rules.
- See `guidelines/workflow/agent-lifecycle.md` for general failure modes and escalation rules.
- See `techniques/worker-instructions.md` for how to write effective worker prompts.
