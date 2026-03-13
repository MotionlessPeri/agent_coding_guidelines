# Documentation Guidelines

## Sync Rules

- When you gain new code understanding or design details during a session, update the
  corresponding doc immediately. Do not wait for the user to prompt you.
- When you modify code, update the doc that describes that flow in the same change.
- When you find a doc is wrong, correct it immediately — do not preserve errors.
- When a new important file, class, or interface is added, update the project index.

## Writing Style

- Put conclusions before details.
- Convert conversation output into structured knowledge. Avoid transcript-style notes.
- Prefer sections: `Conclusion`, `Why`, `Typical Approaches`, `Open Questions`.
- Separate general principles from project-specific choices.

## Document Splitting

- If a document covers 3 or more independent topics, split it.
- If a document exceeds roughly 200-300 lines, evaluate splitting before extending further.
- If one section needs substantial background to stay readable, move it to its own file.

## Index Maintenance

- Every new document must be registered in the project's index file in the same work step.
- When a new term may be ambiguous, add it to the project glossary (if one exists).

## Deferred Topics

- Maintain a visible queue of deferred topics in the documentation.
- Phrase deferred topics as discussable questions, not vague reminders.
- When a deferred topic is later resolved, integrate the result into formal documents.

## In-Progress Docs

- Refactoring plans and progress records should be committed during active work so
  reviewers can track progress.
- Remove or archive them in a separate cleanup commit when the work is complete.
