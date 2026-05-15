---
name: tdd-with-fixtures
description: Strengthened TDD discipline. Augments superpowers:test-driven-development with milestone-level test requirements, an escape hatch (fixture + manual test case) for behaviors that automated tests cannot cover, and an archive convention so manual cases stay reproducible. Use during the implementation phase of any non-trivial task. Especially critical inside autonomous-workflow where tests replace user review gates as the safety net. Does NOT replace superpowers:test-driven-development; invoke both — superpowers:TDD owns the red-green-refactor cycle, this skill owns milestone gating + fixture/manual accumulation.
when_to_use: Use during implementation of any non-trivial task — particularly inside supervised-workflow Phase 3 or autonomous-workflow Phase 3. Use whenever a milestone produces a behavior that needs verification. Skip only for trivial work (typo, doc edit, single-line mechanical change with no behavior delta).
---

# TDD with Fixtures

This skill **augments** `superpowers:test-driven-development`. Invoke both during implementation. superpowers owns the red-green-refactor cycle itself; this skill adds milestone-level discipline and the escape hatch for behaviors auto-tests can't reach.

## When This Fires

**Triggers (any one):**
- Inside `supervised-workflow` Phase 3 (per-milestone implementation)
- Inside `autonomous-workflow` Phase 3 (where this is the safety net replacing user gates)
- Standalone: any implementation phase of a non-trivial task

**Does NOT fire for:**
- Typo / doc-only edits
- Single-line mechanical changes with no behavior delta
- Pure refactors where existing tests already cover the changed code paths

## The Four Rules

### Rule 1: Every milestone ends with tests passing

A milestone is **not done** until:
- All new behavior has test coverage (auto OR manual+fixture, per the decision tree below)
- All existing tests still pass
- New tests demonstrate red-before-green (per `superpowers:test-driven-development`)

If you cannot satisfy this, the milestone is not done — escalate or replan, do not advance.

### Rule 2: Auto-test by default

For any behavior expressible as a deterministic function call with known input → known output:
- Write the test first, see it fail (red)
- Implement minimally to pass (green)
- Refactor if needed (refactor)
- This is the `superpowers:test-driven-development` cycle — follow it verbatim

### Rule 3: When auto-test can't cover, accumulate fixture + manual case

Some behaviors resist automated testing:
- UI / widget rendering / drag-drop / human visual judgment
- Editor-specific state (PIE, hot reload, asset reload from disk)
- External side effects with timing dependencies
- Behavior only observable through human inspection

For these, instead of skipping or "checking visually":
- Create a **fixture** that puts the system into the precondition state (see Fixture Library below)
- Write a **manual test case** describing setup, steps, expected outcome (see Manual Test Archive below)
- Both go into project's test archive. They are durable artifacts, not throwaway notes.

### Rule 4: Never silently bypass a failing test

Forbidden patterns:
- Commenting out a failing test to "fix later"
- Adding `[Skip]` / `@pytest.skip` / equivalent without justification
- Moving to the next milestone with red tests
- Marking a milestone done when manual case has never been verified

If a test is genuinely wrong (not the impl that's wrong):
- Fix or remove the test in the same commit, with reason in commit message
- Do not silently neuter it

## Fixture Library

A **fixture** is a reproducible "known starting state" for testing. Properties: content is predetermined; reloading yields the same state.

**Where they live** (default; project AGENTS.md may override):
- `tests/fixtures/<area>/<name>.<ext>` for test data files (.xlsx, .json, .uasset, .sql, etc.)
- `tests/fixtures/<area>/setup_<name>.py` for programmatic state setup
- Project-specific layout: defer to the project's AGENTS.md or test conventions

**Naming**:
- Name after the behavior or bug being tested: `fixture-reroute-pin-double-direction.uasset`, not `test1.uasset`
- Include a short README or top-of-file comment explaining what state it represents

**Size discipline**:
- Distill to minimum reproducer. A 100 MB asset is rarely a real fixture — it's project state that drifted in.
- If a fixture must be large, document why; otherwise reduce it.

**Lifecycle**:
- Fixture stays as long as the manual case referencing it stays
- When the manual case is retired, retire the fixture too — don't leave orphans

## Manual Test Case Archive

A **manual test case** is a procedure a human can re-run to verify behavior. It is a contract: future you / future agent / future teammate must be able to follow it without asking questions.

**Format** (default; project may override):

```markdown
### TC-<id>: <short title>

**Goal**: what behavior this verifies
**Fixture**: path to fixture(s) used (or "none" if setup is in steps)
**Setup**: prerequisites not in fixture (env vars, build mode, etc.)
**Steps**:
1. Concrete action
2. Concrete action
3. ...
**Expected**: specific, observable outcome — no "looks right" / "works"
**Last verified**: <date> on <commit hash>
**Notes**: known caveats, related bugs, etc.
```

**Where they live** (default; project AGENTS.md may override):
- `docs/manual-tests.md` for a short flat list
- `docs/manual-tests/<area>.md` when split by area (e.g., `graph-editor.md`, `localization.md`)
- Project-specific: defer to project conventions

**Discipline**:
- "Expected" must be unambiguous — observable, not subjective
- "Last verified" gets updated only when you actually run the case end-to-end
- A case with `Last verified` older than ~6 months: re-verify or retire
- A case that fails: fix it (or the underlying behavior) before declaring the milestone done

## Decision Tree: Auto vs Fixture+Manual

```
Behavior to test
  │
  ├── Can it be expressed as: input → deterministic output?
  │     ├── YES → auto-test (superpowers:TDD cycle)
  │     └── NO ↓
  │
  ├── Can a programmatic setup put the system into the test state,
  │   and can a programmatic assertion verify the outcome?
  │     ├── YES → auto-test using a fixture for setup
  │     └── NO ↓
  │
  ├── Does verification require human judgment (UI/visual/usability)?
  │     ├── YES → fixture + manual case in archive
  │     └── NO  → suspect false negative; try to decompose the behavior
  │                into testable pieces before giving up on auto
```

When you arrive at "fixture + manual case", **do not skip the decomposition check**. Many "untestable" behaviors are testable after you separate the deterministic core from the human-judgment shell.

## Project-Level Customization

This skill gives **principles**. Concrete paths (`tests/fixtures/`, `docs/manual-tests.md`) and naming conventions live in each project's own AGENTS.md or project-specific TDD skill.

When working in a project:
1. Check the project's AGENTS.md for test conventions
2. If found, use those paths and naming
3. If not found, use this skill's defaults — and consider adding a project-level convention if the project will accumulate many fixtures

## Failure Modes

| Failure | Looks like | Correct action |
|---|---|---|
| Skipping tests | "I'll add tests later" | Don't. Tests now or milestone not done. |
| Silencing failures | `// TODO: fix test` / `@skip` | Fix or remove with reason in commit |
| Vague manual case | "should work correctly" | Replace with observable outcome |
| Oversize fixture | 100MB asset | Reduce to minimum reproducer |
| Stale manual case | `Last verified` > 6 months | Re-verify or retire |
| Auto-testable handled manually | "Let me just visually check" | Decompose; auto if input/output is deterministic |
| Fixture orphans | Fixture files with no referencing manual case | Delete in cleanup commit |
| Manual case as TODO | Case written but never `Last verified` | A case that's never been run is not yet a case — run it once before claiming the milestone done |

## Composition

- `superpowers:test-driven-development` — base cycle (red-green-refactor). Invoke alongside this skill, not instead of.
- `supervised-workflow` Phase 3 — this skill fires inside each Milestone
- `autonomous-workflow` Phase 3 — this skill is the **mandatory** safety net (replacing user gates)

When multiple workflow skills are active, this skill's rules are **non-negotiable** — workflow skills cannot suspend them. A workflow that wants to skip tests is not a workflow this skill participates in.

## Related

- `guidelines/code/validation.md` — verification baseline; this skill specializes that baseline for the test layer
- `techniques/adversarial-verification.md` — related but different: that one is "how to try to break the change", this is "what test artifacts to leave behind"
- `superpowers:test-driven-development` — composed inside this skill's Rule 2
