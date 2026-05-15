---
name: multi-session-coordination
description: Async coordination protocol for multiple Claude Code conversations sharing one repo working tree. Covers lease claim / release, inbox messaging for negotiation (release_request / preempt_request / piggyback_notice / release_notice), commit-then-release strong contract, and the decision heuristics for letting / grabbing / negotiating when leases conflict. The mechanism layer (hooks) runs automatically — this skill teaches the agent-side policy that hooks alone can't enforce. Bundled with multi_session.py which provides the state library + hook handlers.
when_to_use: Triggers automatically when hook output mentions (1) other active sessions surfaced at SessionStart, (2) pending inbox messages at UserPromptSubmit, (3) PreToolUse(Edit/Write) deny due to lease held by another session, (4) PreToolUse(Bash) deny due to catchall `git add`. Also use proactively when an agent transitions from discussion/exploration into a real implementation phase that's going to edit files — claim a lease at that moment. Skip for pure discussion conversations that never plan to write to disk.
---

# Multi-Session Coordination

This skill is the **agent-side policy layer** of the multi-session coordination system. The **mechanism layer** (hook scripts in `multi_session.py`) runs automatically via `settings.json` hooks and handles registry I/O, stale cleanup, lease checks on Edit/Write, touched-files tracking, and post-commit awareness. The mechanism cannot decide *what to do* when something goes wrong — that's this skill's job.

## Mental Model

### Four Layers

| Layer | Mechanism (hook) | This skill teaches |
|---|---|---|
| 1. Session registry (mailbox) | SessionStart auto-registers, lists active sessions | When to update intent / status |
| 2. Lease + release-request | PreToolUse(Edit/Write) auto-denies on conflict | How to claim / release / negotiate |
| 3. Touched-files + precise git add | PostToolUse auto-records; PreToolUse(Bash) blocks `git add .` | Commit-then-release strong contract |
| 4. Post-commit awareness | UserPromptSubmit injects commits-since-last-turn | Whether to re-read affected files |

### Form A constraint

All conversations in one VSCode window share the same working tree, staging area, and HEAD. **There is no per-conversation independent uncommitted state.** Coordination prevents simultaneous edits; per-session touched_files enables clean commit scope. Worktrees are out of scope (user explicitly rejected the multi-window form).

### Async coordination

Each agent runs only when the user types in *that* tab. **No real-time A↔B negotiation.** State machine progresses one turn at a time per tab, driven by user attention. "B sends release_request to A" only resolves when the user types into A's tab next.

## When to Claim a Lease

Update `sessions/<self>.json` and registry from `discussion` → `active` + add lease paths **the moment you transition from exploring/discussing into implementing**. Triggers:

| Workflow phase | Action |
|---|---|
| `supervised-workflow` GATE 1 passes (plan approved) | Claim lease for files in plan scope |
| `autonomous-workflow` Phase 2 plan written | Claim lease for files in plan scope |
| Standalone task: user says "go ahead and implement" | Claim lease for the obvious target files |
| Brainstorming / reading code / answering questions | **Do NOT claim** — stay status=discussion |
| About to start a milestone in Phase 3 | Update intent_summary + ensure relevant paths are claimed |

### How to claim

Two options:

**Option A** — call the helper from inside an agent action:
```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/multi-session-coordination"))
import multi_session as ms
ms.register_session(cwd, my_session_id, status="active")
ms.add_lease(cwd, my_session_id, "AGENTS.md")
ms.add_lease(cwd, my_session_id, "skills/multi-session-coordination/")
# Also set intent_summary so other sessions see your plan
s = ms.load_session(cwd, my_session_id)
s["intent_summary"] = "Adding pattern-recognition-prep skill"
ms.save_session(cwd, s)
```

**Option B** — invoke the script as a CLI (preferred from a shell context):
```bash
python ~/.claude/skills/multi-session-coordination/multi_session.py claim --paths "AGENTS.md,skills/foo/" --intent "..."
```
(M6 will add this CLI surface.)

### Path scope discipline

- **Be specific.** Claim `skills/multi-session-coordination/` not `skills/`.
- **Don't pre-claim broadly "just in case."** Claim only what you genuinely intend to touch in this milestone.
- **Re-claim if scope grows.** Discovered a cross-reference in a new file? Update lease before editing.
- **One lease at a time isn't required** — multiple narrow paths is fine.

## Hook Triggers and How to Respond

### Trigger 1: SessionStart surfaces other active sessions

```
Other active Claude Code sessions in this project:
  - sess-abc1 status=active holds [AGENTS.md] — adding daily-tracking guideline
```

**Response policy:**
- Note who's working on what. If your task plausibly overlaps → tell the user upfront ("another session is editing AGENTS.md; I'll work on something else or wait").
- Do NOT proactively grab a lease until you're past brainstorming.

### Trigger 2: PreToolUse Edit/Write deny

```
File 'AGENTS.md' is leased by session abc1 (status=active, intent: adding daily-tracking guideline).
Coordinate via inbox (write a release_request to that session) or work on a non-overlapping path.
```

**Decision heuristics:**

| Lease holder situation | Your task | Recommended action |
|---|---|---|
| Their status=discussion / mode=discussion | Anything | Write `piggyback_notice` to their inbox; proceed (their claim is provisional) |
| Their scope is narrow (one file) and you also touch one file | Same file | Write `release_request` with reason; pick non-blocking work until released |
| Their scope is broad (a whole dir) but you only need one file | Single file inside their dir | Write `release_request` asking them to narrow scope; pick non-blocking work |
| Both touch same file, you're urgent | Same file | Write `preempt_request`; surface to user "I want to preempt, OK?" — don't preempt unilaterally |
| Holder is stale (heartbeat old) | Anything | Hook should have already auto-released; if you still see it, force release via `ms.remove_lease(cwd, holder_id, path)` after surfacing to user |
| Multiple holders block same target | — | Surface to user; do not resolve alone |

### Writing an inbox message

Append to the holder's session file:
```python
import multi_session as ms
holder_session = ms.load_session(cwd, holder_id)
holder_session.setdefault("inbox", []).append({
    "from": my_session_id,
    "ts": ms.now_iso(),
    "type": "release_request",   # or preempt_request / piggyback_notice
    "path": "AGENTS.md",
    "reason": "blocked on AGENTS.md to register a new skill; can wait ~15 min",
    "resolved": False,
})
ms.save_session(cwd, holder_session)

# Also log to your own outbox
my_session = ms.load_session(cwd, my_session_id)
my_session.setdefault("outbox_log", []).append({
    "to": holder_id, "ts": ms.now_iso(),
    "type": "release_request", "path": "AGENTS.md",
})
ms.save_session(cwd, my_session)
```

### Trigger 3: Your inbox has unresolved messages

UserPromptSubmit hook surfaces messages each turn until you mark them `resolved`.

**Handling each message type:**

| Message type | Action |
|---|---|
| `release_request` | If you're at a stable point (tests pass, no half-written edits) → commit + release lease + write `release_notice` to sender. If mid-flow → reply with "will release at ~T" (write a `release_notice` with `eta` field). If you genuinely cannot release → surface to user. |
| `preempt_request` | Always surface to user — agent should not unilaterally yield priority |
| `piggyback_notice` | Awareness only; mark resolved |
| `release_notice` | Lease holder released — if you wrote the original request, you can now claim that path |

**Always mark `resolved: true` after acting** so the hook stops re-surfacing:
```python
for m in session["inbox"]:
    if m.get("type") == "release_request" and m.get("path") == "AGENTS.md":
        m["resolved"] = True
ms.save_session(cwd, session)
```

### Trigger 4: PreToolUse Bash deny (catchall `git add`)

```
Catch-all `git add` ... is blocked ... Use `git add AGENTS.md skills/foo.md` instead.
```

The reason field already contains your touched_files. Just substitute the suggested command.

### Trigger 5: UserPromptSubmit surfaces commits since last turn

```
Commits since your last turn (2 from other sessions):
  - bf5609e feat(multi-session): M2 Edit/Write hooks (lease check + touched_files)
      files: skills/multi-session-coordination/multi_session.py, ...
  If your current work depends on any of these files, re-read them before proceeding.
```

**Decision:**
- Skim the file list. If any file you've cached / modified / depend on is listed → **re-read it** before continuing your work. Otherwise proceed.
- This is Layer 4 awareness, not a hard gate — agent uses judgment.

## Commit-Then-Release Strong Contract

Before releasing a lease, **commit OR stash your work**. Never release with uncommitted edits remaining in the touched-files clone — another session might claim the path, edit it, then your work either gets buried in someone else's commit (bad) or overlaps with theirs (worse).

### Standard commit flow

```python
import multi_session as ms

session = ms.load_session(cwd, my_session_id)
touched = session.get("touched_files", [])

# 1. Filter — exclude files agent explored but doesn't intend to commit
to_commit = [f for f in touched if want_to_commit(f)]

# 2. Use precise git add (hook blocks `git add .`)
subprocess.run(["git", "add", *to_commit], cwd=cwd, check=True)
subprocess.run(["git", "commit", "-m", "..."], cwd=cwd, check=True)

# 3. Get the resulting sha and record it
sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()
session.setdefault("commits", []).append({"sha": sha, "ts": ms.now_iso(), "files": to_commit})

# 4. Release lease for the paths we just committed
for path in committed_lease_paths:
    ms.remove_lease(cwd, my_session_id, path)
ms.save_session(cwd, session)

# 5. If there are still un-committed touched files (e.g. exploration leftovers),
#    EITHER commit them in a separate commit OR `git stash` them.
#    Do NOT just leave them — they'll bleed into the next session's commit.
```

### Stash variant

When you can't commit (e.g., the work isn't ready, or you're mid-experiment):
```python
subprocess.run(["git", "stash", "push", "-m", f"sess-{my_session_id[:8]} mid-flow"], cwd=cwd)
# now release lease, surface to user "I stashed and released — pop stash@{0} when resuming"
```

## Workflow Integration

### supervised-workflow

| Phase | This skill's action |
|---|---|
| Phase 1 (brainstorm) | Stay status=discussion; don't claim anything |
| GATE 1 passes | Transition status=active + claim plan scope + set intent_summary |
| Phase 3 milestone start | Verify claim still matches scope; widen/narrow as needed |
| Phase 3 milestone end (commit) | Use precise-add commit flow; touched_files for that milestone |
| Phase 4 (review) | Release all leases + mark status=ended + sync daily.md / open-items |

### autonomous-workflow

| Phase | Action |
|---|---|
| Phase 1 (brainstorm) | status=discussion |
| Phase 2 (plan ready) | status=active + claim plan scope |
| Phase 3 (per-milestone) | Same as supervised Phase 3 — precise-add per milestone |
| Phase 4 (handoff result.md + commits) | Release leases + status=ended |

### Solo conversation (no workflow skill)

If user just says "do X" without invoking a workflow:
- Stay discussion until you've actually decided to write a file
- Claim narrowly at the moment of first Edit
- Release + ended when conversation winds down (Stop hook also auto-handles this)

## Limitations (v1)

| Limitation | Reason | Workaround |
|---|---|---|
| Intra-conversation parallel sub-agents share session_id | Hooks see one session; can't tell sub-agent A from B | When dispatching parallel sub-agents (via `superpowers:dispatching-parallel-agents`), parent partitions file scope explicitly — each sub-agent prompt says "you only touch path X" |
| Cross-session semantic dependency (A renames Foo→Bar, B keeps calling Foo) | Lease is path-level, not symbol-level | Layer 4 surfaces commits since last turn → agent should re-read affected files. CI / type-check / build catches the rest |
| Lease scope is path-prefix, not line-range | Intended-diff (line-level) was rejected as v2 candidate due to scope drift / coordination overhead | If lease误伤太多场景再考虑 v2 |
| Pure-discussion conversation that suddenly edits a file | If you never claimed, your Edit goes through but doesn't appear in registry until PostToolUse | PostToolUse hook auto-registers (defensive); recommend explicitly claiming when transitioning out of discussion |
| Multi-user (different physical users on same repo) | Single-user-multi-session design | Out of scope for v1 |
| Cross-machine coordination | State files are local | Out of scope |

## Anti-Patterns

| Anti-pattern | Why bad | Right way |
|---|---|---|
| Claim broad lease at SessionStart "just in case" | Blocks others unnecessarily | Stay discussion; claim narrow when you know what you'll touch |
| `git add .` to "save time" | Hook blocks; defeats Layer 3 commit scoping | Use touched_files; hook gives you the list |
| Release lease without committing first | Other session may claim + edit; your work either lost or commingled | Commit-then-release; or stash-then-release |
| Forget to mark inbox messages resolved after acting | Hook keeps re-surfacing same message every turn | After action, set `resolved: true` in session file |
| Preempt another session's lease unilaterally | High-priority signal needs human authorization | Surface `preempt_request` to user for approval |
| Cache `find_lease_holder` result across turns | State changes between turns | Always read fresh from registry |

## Common Helpers (one-liners)

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/multi-session-coordination"))
import multi_session as ms

# Read current state
ms.load_registry(cwd)                            # global registry
ms.load_session(cwd, my_id)                      # my session blob
ms.active_sessions(cwd, exclude=my_id)           # others, freshness-filtered
ms.find_lease_holder(cwd, "AGENTS.md")           # who holds (or None)

# Mutate
ms.register_session(cwd, my_id, status="active")
ms.add_lease(cwd, my_id, "skills/foo/")
ms.remove_lease(cwd, my_id, "skills/foo/")
ms.add_touched_file(cwd, my_id, "AGENTS.md")     # PostToolUse does this automatically
ms.update_heartbeat(cwd, my_id)                  # PostToolUse does this automatically
```

## Related Skills

- `superpowers:dispatching-parallel-agents` — when dispatching parallel sub-agents, partition file scope explicitly (see Limitations §1)
- `superpowers:test-driven-development` + `tdd-with-fixtures` — per-milestone test discipline (orthogonal — TDD owns red-green-refactor, this skill owns lease + commit scope)
- `autonomous-workflow` / `supervised-workflow` — natural triggers for status transitions (see Workflow Integration above)
- `guidelines/workflow/commits.md` — "one commit one theme" is the rationale behind precise-add via touched_files
- `guidelines/workflow/daily-and-open-items.md` — Phase 4 daily log + open-items sync references session activity from this system's archive

## Design Doc

For architecture rationale, rejected approaches, and full state schema, see `docs/plans/2026-05-14-multi-session-coordination-design.md` (local artifact, not in git).
