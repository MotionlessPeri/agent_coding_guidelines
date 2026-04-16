# Code Review Guidelines

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
