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

- The request has multiple plausible interpretations that materially change
  the result, scope, side effects, or acceptance criteria.
- A necessary decision cannot be resolved from the conversation, applicable
  project conventions, or judgment within the user's delegated scope.
- The request conflicts with a constraint and it is unclear whether the user
  intends to replace that constraint. A clear instruction to change an existing
  behavior is not itself a reason to ask the user to repeat the decision.

This rule does **not** apply to small, mechanical tasks where the
interpretation is unambiguous (rename a variable, add a missing import,
fix an obvious typo). Do not ask permission for the obvious.

## What to Do Before Editing

1. **State your assumptions explicitly.** One or two sentences: what you
   understand the task to be, what inputs/outputs you assume, what is in
   and out of scope.
2. **List unresolved alternatives** when they materially change the result or
   exceed delegated judgment. Let the user decide those choices.
3. **Use existing decisions first.** Do not re-ask questions already answered
   or seek approval for routine implementation choices within delegated scope.
   If a material ambiguity remains, ask one focused question and pause only the
   dependent work; continue other authorized work.
4. **Push back when warranted.** If a simpler approach exists, or the
   request seems to fight existing structure, say so before implementing.

## What This Looks Like

| Situation | Bad | Good |
|-----------|-----|------|
| "Add user data export" | Implement JSON export of all fields | "I will export to JSON. Scope: all profile fields except password hash. Per-user file or single bundle? Include audit log entries?" |
| "Make search faster" | Add an index on the most obvious column | "Which queries are slow? I see three search paths: name autocomplete, full-text body, geo-radius. Which one are we tuning?" |
| Request conflicts with an unresolved constraint | Ignore the conflict | "The request says X, but the documented compatibility requirement needs Y. Should that requirement change?" |

## How to Ask (User Preference)

When you do ask — whether clarifying a task, choosing between approaches, or
confirming a decision — **ask in plain conversational text in your reply**.
Do **not** route questions through a structured multiple-choice question
tool/UI (e.g. Claude Code's `AskUserQuestion`). State the question directly and
let the user answer in their own words.

This applies to **all** questions, not only pre-implementation clarification —
the intent is a direct back-and-forth, not a form to fill in.

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
- `guidelines/workflow/agent-lifecycle.md` requires purposeful preparation
  followed by action. Resolve concrete uncertainties, then continue; do not
  turn reading or clarification into repeated pauses.
