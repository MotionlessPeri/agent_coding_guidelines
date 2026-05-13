# Daily Activity Tracking and Open Items

Two complementary mechanisms for cross-conversation continuity:

- **`~/.claude/daily/YYYY-MM-DD.md`** — substantive cross-project record of the day's work. Format is suitable for direct copy into daily reports / 日报. Cross-project because work flows along the time axis, not along project boundaries.
- **`~/.claude/projects/<project>/open-items.md`** — per-project rolling list of pending items. Per-project because items carry project context (specific file paths, task slugs, PR numbers).

## File Locations

```
~/.claude/
├── daily/
│   ├── 2026-05-13.md         ← one file per active day
│   └── ...
└── projects/<project>/
    └── open-items.md         ← one persistent file per project
```

Both are agent artifacts per `guidelines/collaboration/private-docs-policy.md` — **never** commit to project git.

## `daily/YYYY-MM-DD.md` Template

```markdown
# YYYY-MM-DD

## Today's Themes
- <project>: <one-line theme>
- ...

## Conversations by Project

### <project>
- [HH:MM, ~Nmin] <topic / what was discussed or done>
  → (optional) artifact path: handoffs/<slug>/ etc.

## Commits Today
- [<project>] <hash> <subject>

## Decisions / Conclusions
- <decision and brief why>

## Open Items Δ
### Added
- [<project>] <item>
### Closed
- [<project>] <item> ✓
```

Append throughout the day. Never rewrite past time slots. If you need to correct a past entry, add a new entry that notes the correction.

## `open-items.md` Template

```markdown
# Open Items — <project>

## In-Flight (active, pick up next)
- <item, with reference: handoff dir / PR / file, and "paused at X" if applicable>

## Pending (will do, not started)
- <item>

## Watching (monitoring, not acting)
- <item>
```

Items can be reclassified / reprioritized / closed freely (unlike daily.md, which is append-only).

## Trigger Guidance: When to Write

| Event | What to write |
|---|---|
| `autonomous-workflow` Phase 4 completes | Append to today's daily.md (under project section, referencing handoffs/<task-slug>/); sync status to project's open-items.md |
| `supervised-workflow` Phase 4 completes | Same |
| Ad-hoc conversation produces a meaningful decision / artifact / discovery | Append daily.md entry; new pending items → open-items.md |
| User wraps up: "今天就到这" / "明天再聊" / equivalent | Agent proposes: "log 一下今天？" |
| Trivial Q&A / one-line lookups / short clarifying questions | **Do NOT write to daily** — avoid noise that buries real entries |

The threshold for writing is **substantive output**: a decision, an artifact, a meaningful discovery, a commit, a status change on existing work. Casual chat does not qualify.

## Query Patterns (No Extra Storage)

These views are computed at query time by reading the existing files:

- **Daily report / 日报**: read `~/.claude/daily/<today>.md` — copy Themes + Decisions + key Conversations entries
- **Weekly summary / 周报**: scan `~/.claude/daily/` last 7 days
- **All open items across projects**: scan `~/.claude/projects/*/open-items.md` and aggregate
- **What did I do on day X**: read `~/.claude/daily/X.md`
- **What conversations touched project P this week**: filter daily files by `### P` section

No aggregation files needed — the daily/ folder is already cross-project; the per-project open-items.md files are easy to scan.

## Cross-Project Open Items

Some items don't fit any specific project (e.g., "set up new IDE plugin", "evaluate tool X"). Current policy: **add to today's daily.md "Open Items Δ → Added"** with no project prefix, then carry forward to subsequent daily files as needed.

When this becomes painful (3+ recurring cross-project items), revisit and consider adding a top-level `~/.claude/open-items.md` layer.

## Composition Notes

- `guidelines/collaboration/private-docs-policy.md` — these files are agent artifacts, not project deliverables; never committed to project git
- `skills/autonomous-workflow/SKILL.md` Phase 4 — the workflow's natural trigger to write daily + sync open-items
- `skills/supervised-workflow/SKILL.md` Phase 4 — same
- `guidelines/workflow/handoffs.md` — handoff documents are per-task artifacts; daily.md and open-items.md are cross-task / cross-project layers above that

## Agent Behavior Summary

- Write daily.md and open-items.md on substantive events; skip trivial chat
- daily.md is append-only; open-items.md is freely editable
- Both are agent artifacts at `~/.claude/`; do not commit to project git
- At end of substantive conversation, proactively ask user "要不要 log 今天？" if no automatic workflow trigger has fired
- When user asks "what did I do today / yesterday / this week", read the corresponding daily files rather than reconstructing from memory
