# Clarify Before Implementing

## Purpose

Before touching code, surface what you've assumed and what is ambiguous.
Hidden assumptions and silent interpretation choices are a primary source of
rework — work spent implementing the wrong thing because the agent guessed
rather than asked.

This is the pre-implementation counterpart to the verification rules in
`guidelines/code/validation.md`: validation catches mistakes after the fact,
clarification prevents them from being made.

## When This Applies

- The user request has multiple plausible interpretations.
- The request is concrete but you would be filling in unstated parameters
  (scope, format, side effects, error semantics).
- You are about to make a non-trivial design choice the user did not specify.
- You notice the request contradicts existing code, docs, or earlier
  conversation context.

This rule does **not** apply to small, mechanical tasks where the
interpretation is unambiguous (rename a variable, add a missing import,
fix an obvious typo). Do not ask permission for the obvious.

## What to Do Before Editing

1. **State your assumptions explicitly.** One or two sentences: what you
   understand the task to be, what inputs/outputs you assume, what is in
   and out of scope.
2. **List alternative interpretations** when more than one is plausible.
   Let the user pick — do not silently choose for them.
3. **Stop and ask** when something is unclear, contradictory, or missing.
   The cost of one clarifying question is low; the cost of building the
   wrong thing is high.
4. **Push back when warranted.** If a simpler approach exists, or the
   request seems to fight existing structure, say so before implementing.

## What This Looks Like

| Situation | Bad | Good |
|-----------|-----|------|
| "Add user data export" | Implement JSON export of all fields | "I will export to JSON. Scope: all profile fields except password hash. Per-user file or single bundle? Include audit log entries?" |
| "Make search faster" | Add an index on the most obvious column | "Which queries are slow? I see three search paths: name autocomplete, full-text body, geo-radius. Which one are we tuning?" |
| Request conflicts with existing code | Pick one silently and proceed | "The request says X but `Foo.cs:42` already does the opposite for reason Y — which should win?" |

## Anti-Patterns

- "Based on my best guess, I will …" — if you need to guess, ask first.
- Listing assumptions in the **final report** instead of before
  implementation. By then it is too late to course-correct cheaply.
- Asking five questions at once. Pick the one or two that actually block
  progress. Fold the rest into your stated assumptions so the user can
  correct them in passing.

## Relationship to Other Guidelines

- `superpowers:brainstorming` (skill) handles open-ended creative work
  ("let's design X"). This guideline handles narrower task ambiguity
  ("implement X" where X has multiple valid readings).
- `guidelines/code/constraints.md` "Architecture First" requires reading
  docs first; this requires surfacing your interpretation first.
- `guidelines/workflow/agent-lifecycle.md` lists "Let me read the code
  first" as a procrastination pattern. Clarification is not procrastination
  — it is a single targeted question, not exploratory reading.
