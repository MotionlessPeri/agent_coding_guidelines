# Review the whole result — Phase 4

Workflow material. Read when the delivery units are ready for the final scope and
integration check, or when resuming an incomplete final review.

## Inputs

The acceptance criteria and decisions; original task baseline; all task-owned
changes and artifacts; verification evidence, failure history and review findings.

## Actions

1. Check coverage in both directions: each acceptance criterion has a demonstrated
   result, and each change serves the authorized scope. Identify missing behavior,
   placeholders and unexplained additions. Fix necessary in-scope gaps; do not turn
   optional cleanup into a new requirement.
2. Inspect committed changes from the original task baseline through HEAD, plus
   staged, unstaged and untracked task-owned content. A HEAD-only diff or the latest
   milestone is insufficient. Preserve attribution of pre-existing changes; do not
   silently exclude an entire dirty file or claim its unrelated edits.
3. Check interactions between delivery units, stale paths and relevant test-state
   pollution. Run or reuse applicable integration/full-suite/build evidence required
   by the project. Earlier evidence is reusable only for unchanged covered inputs;
   a commit alone does not invalidate it, and unrelated tests do not cover a new risk.
4. Reuse one review record for scope, correctness, structure/comments and integration.
   Honor requested independent review and human visual verification. Choose any
   further review skill for a concrete uncovered need, not an unconditional chain.
5. Address remaining findings under `guidelines/workflow/agent-lifecycle.md`.
   Serious acceptance gaps or failed required verification prevent a completion
   claim. Report what is incomplete, why, and which decision or evidence is missing.
6. If a reusable lesson actually emerged, evaluate it under
   `guidelines/workflow/knowledge-promotion.md`. Separate reproduced evidence,
   provisional observations and suggestions. Propose persistent rules or catalog
   changes only within that policy and the user's authorization. Routine completion
   does not require inventing a skill candidate or a "no candidates" record.

## Output

A concise user-facing result: achieved behavior, affected scope, actual commits
when applicable, verification and relevant limitations. Link existing durable
records when useful; avoid copying the whole worklog into the response.

Task logs and handoffs remain private. Implementation/design plans and test
fixtures follow the project's ownership policy; they are not automatically private
merely because an agent created them. Keep retained records in place unless their
archival/removal was authorized.

## Completion condition

The authorized outcome is supported by applicable evidence and required reviews.
No additional approval is introduced by this phase. A specifically requested final
review or a newly needed out-of-scope action retains its own authorization boundary.
