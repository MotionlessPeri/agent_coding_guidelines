# Knowledge Promotion Guidelines

Rules for deciding when a lesson learned in a specific project should be
promoted to this shared guidelines repository, and how to do it.

## Why This Exists

This repository is a **meta-corpus** — rules that apply across projects. The
pull direction (guidelines → project) is covered by
`collaboration/multi-agent.md`. This file covers the push direction
(project → guidelines).

Without an explicit promotion discipline:

- **Under-promotion** — every new project re-discovers the same framework
  constraints. The lesson stays trapped in one project's docs.
- **Over-promotion** — project-specific details pollute the shared repo
  and make it noisy for other projects.

Both failure modes are real. This file draws the line.

## What to Promote

A lesson is promotion-worthy if it meets **at least one** of these:

- **Two-strike rule** — the same class of issue hit in two different
  projects. One incident is an anecdote; two is a pattern.
- **Hidden contract in an external framework or tool** — behavior not
  documented by the tool itself but learned from its source, crashes, or
  bug reports. Examples: UE `PinWidget->SetOwner()` must be called exactly
  once; `git rebase --no-edit` is invalid.
- **Editor / IDE / CLI gotcha** an agent would otherwise re-encounter —
  e.g., Live Coding vs. cold rebuild, MCP protocol quirks, shell
  portability pitfalls.
- **Workflow discipline the user has confirmed works** — validated patterns
  for commits, reviews, verification, coordination.

## What NOT to Promote

Keep out of the shared repo:

- **Project-specific names, paths, or identifiers** (commit prefixes,
  P4 workspaces, port numbers, repo URLs, engine install locations).
- **One-off bug fixes** whose solution does not generalize — the fix
  belongs in the project commit, not the meta-corpus.
- **Rules already in the framework's own docs** — if it's in the UE engine
  source comments or the tool's official guide, cite the source from the
  project instead of duplicating here.
- **Organization-specific policies** (a specific company's code-review
  norms, compliance frameworks) — they belong in that organization's own
  AGENTS.md.
- **Exploratory or unverified patterns** — if it has only been tried once
  and it worked, it is not yet a guideline. Wait until it proves itself
  in a second use.

## Promotion Workflow

1. **Draft in the project first.** Write the lesson into the project's own
   docs (`Docs/`, `AGENTS.md`, or a plan file). Use it there for at least
   one real task cycle to validate it is actionable.

2. **Strip project-specific details.** When extracting, replace concrete
   names with category examples. "In DialogueSystemSample we saw X" becomes
   "UE graph editor plugins must do X".

3. **Pick the right subdirectory** under `guidelines/`:
   - `workflow/` — commits, docs, agent lifecycle, code review
   - `code/` — correctness and validation constraints
   - `collaboration/` — multi-agent setup, artifact placement
   - `ue/` — Unreal Engine specific
   - Create a new subdirectory only if the lesson does not fit any existing
     category and at least one more lesson is expected in that category.

4. **Create the file** with a focused scope (one topic per file). Use
   existing files as style reference — declarative rules, concise bullets,
   tables where comparisons help. Keep under ~200 lines; split if longer.

5. **Register it in `AGENTS.md`** by adding `@guidelines/<subdir>/<name>.md`
   in the appropriate section. Without the `@` import, the file is
   invisible to agents even after commit.

6. **Commit separately** with a `governance:` or `docs:` message. Do not
   bundle the promotion commit with unrelated project work.

## Agent Behavior

- When you notice a signal that **clearly** matches "What to Promote"
  during project work, flag it to the user — do not silently promote.
- When unsure whether a lesson generalizes, leave it in the project docs.
  The promotion step is a conscious decision, not a default action.
- Never leave the same content in both places — either the canonical
  version lives in guidelines and the project `@`-imports it, or it moves
  fully into the project if it turned out to be project-specific.
- Do not promote at every session end. The trigger is "I spotted a
  generalizable lesson," not a periodic sweep.
