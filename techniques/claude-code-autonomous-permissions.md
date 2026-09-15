# Claude Code: Task Authorization and Commit Permissions

## Purpose

How to distinguish authorization for local commits from the host settings that
control whether the command runs, prompts, or is denied.

Historical context: this guide came out of a failure mode: a kickoff doc said
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

Do not infer effective permission from a single configuration file. Rules and
managed restrictions combine across scopes; consult the current host permission
view and official [settings precedence](https://code.claude.com/docs/en/permissions#settings-precedence).
The table describes rule evaluation, not a promise that every mode prompts.

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

- Do not treat an `allow` entry as proof that history loss is impossible or as
  authorization for push. Check actual host protections and task authority
  separately; an optional guard cannot replace either.
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

## Task Authorization and Host Configuration

Approved implementation includes local commits under `guidelines/workflow/commits.md`.
Discussion or review alone does not. Push, history rewriting, and permission
configuration require their own applicable authorization. An allow rule grants
tool capability; it does not add any of those actions to the task.

This repository does not prescribe an `ask` entry for every commit, nor a cycle
of removing and restoring one for every autonomous task. A user may choose an
interactive configuration, for example:

```json
"permissions": {
  "ask": ["Bash(git commit:*)"]
}
```

The active host mode and policies determine enforcement. Task approval does not
change those settings. Diagnose the actual session rather than treating this
example or a past incident as the current machine's configuration.

## When an Authorized Commit Prompts

1. Check the applicable host mode, rules, and the source of the restriction.
2. Explain the blocked action and use the host's approval mechanism. A user can
   choose to manage configuration separately; unattended execution is not a
   reason for the agent to change it.
3. Continue independent authorized work if possible. Preserve the uncommitted
   task changes and report the limitation if the required commit cannot run.

Do not create a trivial or empty commit just to check permissions. Observe the
next real, verified task commit instead.

## Configuration Is a Separate Task

A request to implement or commit is not a request to edit permission settings.
Do not move rules from `ask` to `allow`, add broader patterns, switch execution
tools, or remove a denial to make a blocked operation run.

If the user separately requests host configuration, make only the requested
changes through supported controls, preserve unrelated settings, and verify
the resulting configuration. Restore temporary changes only when that was part
of the user's requested configuration; do not impose a universal default-deny
restoration policy. Managed restrictions remain binding.

## Diagnostic: "Why Is It Still Prompting?"

Use Claude Code's permission view and applicable settings to identify the actual
matching rule and mode. Do not broaden patterns merely because the match is
unclear. Current matching and mode behavior are documented in the official
[permission reference](https://code.claude.com/docs/en/permissions).

The historical incident above explains why task wording and host behavior can
differ; it is not a guarantee about every current permission mode.

## Related Guidelines

- See `guidelines/workflow/agent-lifecycle.md` for which actions are permitted
  autonomously vs. require user confirmation.
- See `guidelines/workflow/commits.md` for commit granularity and message
  conventions that apply regardless of whether `git commit` is gated.
