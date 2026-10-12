# Review the whole result — Phase 4

Workflow material. Read when the accepted delivery units are ready for final
coverage and integration review.

## Inputs

The accepted design/plan; original task baseline; every task-owned change;
verification records, user decisions and unresolved findings.

## Actions

1. Check acceptance coverage and scope in both directions. Every required outcome
   needs supporting implementation/evidence; every change must serve the authorized
   task. Identify missing behavior, placeholders and silent additions.
2. Review changes from the original baseline through HEAD and include staged,
   unstaged and untracked task-owned content. Preserve prior ownership decisions;
   do not overlook resumed work or claim unrelated edits in a shared file.
3. Examine cross-unit integration, stale paths and relevant test-state pollution.
   Run or reuse required integration/full-suite/build evidence covering the final
   inputs. An unrelated commit does not invalidate sound evidence; changed covered
   inputs or a missing integration case require targeted verification.
4. Reuse one review record for coverage, correctness, structure/comments and
   integration. Fulfil user-requested independent review or human observation.
   Additional review skills are selected for an actual uncovered need.
5. Triage remaining findings with `guidelines/workflow/agent-lifecycle.md`.
   Necessary corrections remain within accepted scope and selected checkpoints;
   optional refactoring and new architecture do not become mandatory because
   a reviewer suggested them.
6. If a transferable lesson actually emerged, assess it under
   `guidelines/workflow/knowledge-promotion.md`. Evidence and user authorization
   govern persistent rule/catalog changes. Do not create new skills or require
   an empty "no candidates" entry as a routine completion step.

## Output

A concise result describing achieved behavior, scope, relevant commits, verification,
accepted deviations and remaining limitations. Required acceptance gaps or failed
verification prevent claiming completion. Preserve project deliverables and private
handoff records under their respective ownership policies.

## Completion condition

The accepted outcome has applicable evidence and all user-selected reviews are
satisfied. No fourth default approval round is created here. If the user explicitly
requested final acceptance, respect that checkpoint and its scope.
