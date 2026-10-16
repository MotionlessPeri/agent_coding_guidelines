---
class: procedure
scope: universal
---

# Code Review Guidelines

## Scope and Independent Review Evidence

- Establish the scope baseline from the original user request, subsequent explicit
  decisions, exclusions, and existing capabilities. Keep the author's inferences
  separate; neither their plan nor tests they added can turn an inference into a
  user requirement.
- Review the actual diff and affected execution paths against that baseline.
  Apply the [scope deletion test](../code/constraints.md#plan-scope-integrity) to
  added behavior, state, interfaces and lifecycle mechanisms. Evaluate deletion
  against the requested outcome, not an extra condition introduced by the proposal.
  Existing implementation and sunk effort do not prove the behavior is needed.
- When independent review is required, the reviewer forms a scope judgment from
  the source requirements and existing capabilities before evaluating the author's
  justification. Check both unnecessary additions and loss of required behavior;
  the reviewer cannot expand scope through a finding.
- Identify the baseline and candidate actually reviewed, using commits or file
  digests appropriate to the work. A later change needs review of the affected
  conclusions before that changed candidate is described as reviewed. A matching
  hash identifies content; it does not authenticate a reviewer's judgment.
- Keep author self-checks, independent findings, and execution checks distinct.
  Missing independent review, an author's `approved` field, or passing tests must
  not be reported as independent scope approval. Reuse valid review evidence for
  unchanged material rather than restarting unrelated checks.

These instructions do not install an enforcement mechanism or require independent
review for every edit. Where a project requires one, name the actual protected
action and executor; comparison and trial criteria are in the
[scope-control reference](../../references/agent-knowledge/scope-control.md).

## Merge Commit Review

When reviewing a feature branch that has merged the main branch (or any upstream branch)
back into itself, **always inspect the merge commit separately**.

### Why

A common failure mode:

1. Developer creates a feature branch from main and implements Feature X in File A.
2. Main undergoes a refactor that moves the logic from File A to File B.
3. Developer merges main into their feature branch.
4. Git auto-resolves or developer manually resolves conflicts — but only at the
   text level. The developer's Feature X code stays in File A (the old location),
   while File B (the new location) also exists with the refactored code.
5. Both code paths run. The old path masks bugs in the new path because it
   "happens to work."

The result: the feature appears functional during testing, but two redundant code
paths coexist. The old path is dead code that should have been removed, and the
new path may have bugs hidden by the old path's fallback behavior.

### What to Check

For every merge commit in a feature branch:

1. **List files touched by both sides.** If the feature branch and the upstream
   branch both modified the same file, check that the merge resolution makes sense
   architecturally — not just textually.

2. **Look for moved/renamed code.** If upstream moved logic from File A to File B,
   verify that the feature branch's changes to File A were also migrated to File B.
   A clean text merge does not guarantee a clean architectural merge.

3. **Search for duplicate handlers.** After the merge, grep for the feature's key
   function names or entry points. If they appear in two places (old location +
   new location), the merge was not fully reconciled.

4. **Check that deleted code stays deleted.** If upstream deleted a function or
   file, and the feature branch had modifications to it, the merge may resurrect
   the deleted code. Verify that upstream's deletions are respected unless there
   is an explicit reason to keep them.

### Shortcut

```bash
# Show which files were modified on both sides of a merge
git log --oneline --name-only <merge-base>..<feature-branch> -- <file>
git log --oneline --name-only <merge-base>..<upstream> -- <file>
# Files appearing in both lists need careful review
```

## General Review Principles

- Review the diff against the base branch, not just the latest commit.
  A clean latest commit can hide problems introduced in earlier commits
  or merge resolutions.
- If the branch has multiple commits, also review each commit individually —
  a squashed diff can hide that an intermediate commit broke the build.
- Test at system boundaries, not just the happy path the developer tested.
