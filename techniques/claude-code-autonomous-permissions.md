# Claude Code: Enabling Autonomous Commits for a Session

## Purpose

How to configure Claude Code permissions so that a session kickoff document can
**actually** grant autonomous commit authority — bypassing the default
interactive approval prompt on `git commit`.

This pattern came out of a real failure mode: a kickoff doc said
"本 session 无需再问 / autonomous commits authorized" but the user still got
prompted on every commit because a global `ask` rule overrode the project-level
`bypassPermissions`.

## Claude Code Permission Model Recap

Claude Code checks three lists (per tool invocation):

| List  | Effect             |
|-------|--------------------|
| `deny`| Always blocks      |
| `ask` | Always prompts     |
| `allow`| Runs silently     |

**Precedence across the lists**: `deny` > `ask` > `allow`.
This holds **regardless of scope** — a global `ask` will override a project
`allow`, not the other way around.

**Scope precedence** (for equal-priority matches): enterprise managed settings
> user settings (`~/.claude/settings.json`) > project shared settings
(`.claude/settings.json`) > project local settings (`.claude/settings.local.json`).

Patterns use either prefix match (`Bash(git commit*)`) or colon-delimited
command match (`Bash(git commit:*)`). Both forms are valid; prefer the colon
form when matching a command with arguments.

## Default Posture — Safety Net

Recommended baseline in `~/.claude/settings.json`:

```json
"permissions": {
  "ask": [
    "Bash(git commit:*)"
  ]
}
```

This means: **by default, every `git commit` prompts for approval**, even in
projects with `"defaultMode": "bypassPermissions"`. That is intentional — commits
are side-effecting and the interactive prompt is a cheap safety net that catches
hallucinated commits.

## When a Session Authorizes Autonomous Commits

Kickoff documents sometimes say things like:

> 授权(本 session 无需再问):
> - git add / git commit(前缀 `m-...`, 两个 repo 分别 commit)

This is the user **explicitly lifting the safety net for this session**. To
actually work autonomously you must modify the permission configuration —
the kickoff text alone does not disable the `ask` rule.

### How to Lift (temporarily)

Edit `~/.claude/settings.json`:

1. Remove `"Bash(git commit:*)"` from `ask`
2. Add `"Bash(git commit:*)"` to `allow`
3. Also add the same pattern to the project's `.claude/settings.local.json`
   `allow` list (belt-and-braces; matches both wildcard forms)

Verification step (non-negotiable): make one trivial commit and confirm **no
prompt appears**. If a prompt still appears, the lift did not take effect —
investigate before continuing (cache, typo, scope mismatch).

### How to Restore (when session ends or user asks)

Reverse the above:

1. Remove `"Bash(git commit:*)"` from `allow` in both scopes
2. Add `"Bash(git commit:*)"` back to `ask` in `~/.claude/settings.json`

Do this as part of the end-of-session wrap-up, or as soon as the user asks.
Default-deny posture is the correct steady state.

## Generalizing to Other Commands

The same procedure applies to any command the user has guarded with `ask`:
- `Bash(git push:*)` — push to origin
- `Bash(rm:*)` — destructive file ops
- `Bash(git reset --hard:*)` — history rewrite
- `Bash(git rebase:*)` — history rewrite

For any of these, the session kickoff must explicitly authorize the specific
command; otherwise default-deny (via `ask`) stays in effect.

## Diagnostic: "Why Is It Still Prompting?"

When a command keeps prompting despite what you think is an allow rule:

1. Read `~/.claude/settings.json` end-to-end — a global `ask` is the most
   common culprit.
2. Check project `.claude/settings.json` and `.claude/settings.local.json`
   for any `deny` or `ask` entries that match.
3. Remember that `"Bash(git commit*)"` (prefix) and `"Bash(git commit:*)"`
   (colon) are different patterns — Claude Code may normalize the command to
   the colon form for matching. Add both if unsure.
4. Compound commands (`cd X && git commit ...`) may or may not match depending
   on how Claude Code parses the prefix. Run the command as a single
   non-compounded form to test, or add allow entries for both forms.

## Agent Behavior

- **Never silently lift a user's safety rule.** Only lift when a session's
  kickoff doc explicitly authorizes the specific action, and always log the
  lift to the user in the session so they can see it.
- **Restore on request.** When the user asks you to add the ask rule back,
  do it immediately and verify by reading the resulting file.
- **Document the lift.** In the session log or the kickoff response, mention
  which rules were lifted, in which files, and for how long.

## Related Guidelines

- See `guidelines/workflow/agent-lifecycle.md` for which actions are permitted
  autonomously vs. require user confirmation.
- See `guidelines/workflow/commits.md` for commit granularity and message
  conventions that apply regardless of whether `git commit` is gated.
