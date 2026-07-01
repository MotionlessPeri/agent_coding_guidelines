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

## Auto Mode: Engine-Side Destructive-Command Guardrails

Since ~2.1.183 (June 2026), Claude Code's **auto mode** adds a second, *independent*
enforcement layer on top of the `allow` / `ask` / `deny` lists. The two layers answer
different questions:

- **Permission lists** (above) decide — by pattern match — whether a tool call is
  auto-approved, prompted, or blocked.
- **Auto mode classifier** inspects the *content / intent* of a shell command and can
  block destructive actions the user never asked for — **even if the permission lists
  would have allowed them**.

This is the engine-side enforcement of the "do not use destructive actions as shortcuts"
rule that `guidelines/workflow/agent-lifecycle.md` previously left to agent
self-discipline. It matters directly here: lifting `git commit` into `allow` for an
autonomous session does **not** also open the door to `git reset --hard` or history
rewrites — auto mode still guards those separately.

### What auto mode blocks (2.1.183+)

> Destructive git commands (`git reset --hard`, `git checkout -- .`, `git clean -fd`,
> `git stash drop`) are blocked when you didn't ask to discard local work;
> `git commit --amend` is blocked when the commit wasn't made by the agent this session;
> `terraform destroy` / `pulumi destroy` / `cdk destroy` are blocked unless you asked for
> the specific stack.

Two related settings extend the surface:

| Setting (`settings.json`) | Since | Effect |
|---|---|---|
| `autoMode.classifyAllShell` | 2.1.193 | Routes **all** Bash/PowerShell commands through the auto-mode classifier, not just arbitrary-code-execution patterns. |
| `sandbox.credentials` | 2.1.187 | Blocks sandboxed commands from reading credential files and secret environment variables — a CI / agent credential-isolation knob. |

### Implications for this technique

- Lifting `git commit` / `git push` into `allow` for an autonomous session is **still
  safe against accidental history loss** — auto mode's destructive-command guard is a
  separate net that a permission lift does not disable.
- If you *intend* an autonomous session to run a specific destructive command (e.g. a
  scripted `git reset --hard` in a throwaway worktree), you must **ask for it explicitly**
  — auto mode blocks *unrequested* destructive actions regardless of the allow list.
- Consider `sandbox.credentials` for CI / agent flows that run sandboxed and should never
  read secrets directly (secrets belong in the CI secret store — see
  `techniques/ci-deploy-to-p4.md`).

### Caveats before relying on this

- The changelog does **not** state default on/off values for `autoMode.classifyAllShell`
  or `sandbox.credentials`, nor does it formally define "auto mode." Confirm current
  behavior against the official changelog / docs before treating any of these as
  always-on.
- Requires Claude Code ≥ 2.1.193 (June 2026); older versions have narrower auto-mode
  behavior or none.
- Source: Claude Code changelog (https://code.claude.com/docs/en/changelog), entries
  2.1.183 / 2.1.187 / 2.1.193.

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
