# Multi-Session Coordination — Install Guide

This skill needs **two pieces** installed: (1) the skill bundle itself synced to `~/.claude/skills/multi-session-coordination/`, and (2) the hook registrations in `~/.claude/settings.json` that point Claude Code at our scripts.

## Prerequisites

- **Python 3** on PATH (3.8+; we test on 3.12). Verify: `python --version`
- **Claude Code** installed and working
- **Git** on PATH (used by Layer 4 commit-awareness; not strictly required, hooks degrade gracefully if missing)
- **Windows**: PowerShell 5.1+ (ships with Win10/11)
- **Mac / Linux**: optional — hooks themselves are pure Python; only the auto-install helper is PowerShell. Manual install via the JSON snippet works on any OS.

## Step 1 — Sync skill bundle to `~/.claude/skills/`

From the `agent_coding_guidelines` repo root:

```powershell
pwsh ./scripts/sync-skills.ps1
```

This copies all skill subdirectories (including `multi-session-coordination/`) into `~/.claude/skills/`. Re-run any time you update skills in the repo.

Verify:
```
~/.claude/skills/multi-session-coordination/
├── SKILL.md
├── multi_session.py
├── install.ps1
├── install.md
├── settings-snippet.json
└── tests/
```

## Step 2 — Register hooks in `~/.claude/settings.json`

### Option A — auto-install (recommended on Windows)

```powershell
pwsh ~/.claude/skills/multi-session-coordination/install.ps1
```

> ⚠️ **Re-run install.ps1 every time you re-sync the skill** (i.e. after `scripts/sync-skills.ps1`). The snippet contains `%USERPROFILE%` placeholders for human readability, but Claude Code does NOT shell-expand env vars in hook commands — install.ps1 bakes the absolute path in at install time. If you only sync without re-installing, your settings.json keeps pointing at whatever paths were baked from the previous install. (If you renamed your user dir between syncs, re-install picks up the new path.)

What it does:
- Backs up your current `~/.claude/settings.json` to `~/.claude/settings.json.bak.<timestamp>`
- Removes any prior multi-session-coordination hook entries (idempotent — safe to re-run)
- Adds 6 hook registrations (SessionStart / UserPromptSubmit / PreToolUse Edit|Write|MultiEdit / PreToolUse Bash / PostToolUse Edit|Write|MultiEdit / Stop)
- Writes back

To **uninstall** (removes our hooks; leaves other settings alone):
```powershell
pwsh ~/.claude/skills/multi-session-coordination/install.ps1 -Uninstall
```

### Option B — manual merge (works on any OS)

Open `~/.claude/skills/multi-session-coordination/settings-snippet.json`. The file's `hooks` object contains 5 event keys (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop).

Open your `~/.claude/settings.json`. Find (or create) the top-level `"hooks"` key.

For **each event** in the snippet:
- If the event doesn't exist in your settings → copy the array verbatim
- If the event exists → **append** the snippet's array entries to your existing array (do NOT replace)

The snippet uses Windows-style paths (`%USERPROFILE%\.claude\skills\...`). On **Mac/Linux**, replace each `command` value with:

```
python "$HOME/.claude/skills/multi-session-coordination/multi_session.py" <hook-name>
```

(e.g. `<hook-name>` is `session-start` / `pre-tool-edit` / etc — see the snippet).

## Step 3 — Verify

Open a new Claude Code conversation in any project (or reload the current VSCode window so it picks up the new settings). The SessionStart hook should run automatically and create state files:

```
~/.claude/multi-session-coord/<encoded-cwd>/
├── registry.json
└── sessions/<your-session-id>.json
```

Check `registry.json` — should have your session listed. If empty / missing → hook didn't fire; see Troubleshooting.

## Step 4 — (Optional) Tune thresholds

The defaults are tuned for typical multi-session workflows:

| Setting | Default | Where |
|---|---|---|
| `STALE_THRESHOLD_MIN` | 30 minutes | `multi_session.py` top of file |

You can override per-project via env var:
```
MULTI_SESSION_STALE_MIN=10 (not yet implemented — patch multi_session.py directly for now)
```

For per-project state isolation (testing only):
```
MULTI_SESSION_BASE=/some/path
```

## Troubleshooting

### Hook didn't fire (no state files created)

1. Check Claude Code's output panel for hook errors (Ctrl+Shift+P → "Developer: Show Logs")
2. Try running the hook directly to verify it works:
   ```
   echo '{"cwd": "C:/your/project", "session_id": "test"}' | python "%USERPROFILE%\.claude\skills\multi-session-coordination\multi_session.py" session-start
   ```
   Expected output: `{"hookSpecificOutput": {...}}`
3. Verify Python is on PATH from Claude Code's context (sometimes shell PATH ≠ user PATH on Windows)
4. Check `settings.json` for syntax errors with `python -m json.tool ~/.claude/settings.json`

### "permissionDecision: deny" denied an Edit I expected to succeed

The hook saw an active lease on that file held by another session. Check:
```
cat ~/.claude/multi-session-coord/<your-encoded-cwd>/registry.json
```

If the holder is actually stale, run:
```
python "%USERPROFILE%\.claude\skills\multi-session-coordination\multi_session.py" session-start < echo '{"cwd":"YOUR-CWD","session_id":"manual"}'
```
which triggers cleanup. Or wait 30 min for auto-stale.

### State files keep accumulating

Cleanup only happens at SessionStart of a new conversation when the caller is solo. If you run many parallel conversations, ended sessions stay in `sessions/` until the next solo SessionStart. They're small (~1KB each) and get archived under `archive/<date>/` eventually.

### I want to completely reset state

```
rm -rf ~/.claude/multi-session-coord/
```

Safe — files will recreate on next SessionStart. Any active sessions will register themselves fresh on their next turn (UserPromptSubmit / PostToolUse auto-register).

## How to read the SKILL.md

The skill itself (`SKILL.md`) is what Claude Code auto-loads at runtime when hook output indicates coordination is relevant. You don't usually need to read it — but if you want to understand the decision heuristics, that's the source.

The design doc (`docs/plans/2026-05-14-multi-session-coordination-design.md` in the repo, local-only) has architecture rationale.
