# Adversarial Verification

## Purpose

Procedural checklist for adversarial verification of code changes. The goal is to try to break the change, not confirm it works.

## Self-Check

Before starting verification, review the common failure modes in `guidelines/workflow/agent-lifecycle.md`. If you catch yourself writing explanations instead of running commands — stop. Run a command.

## Verification Strategies by Change Type

### Frontend

1. Start the dev server
2. Check rendered output via browser tool or curl
3. Verify sub-resources load (images, API calls, static files)
4. Run frontend test suite

### Backend / API

1. Start the server
2. Curl endpoints -- verify response body structure, not just status codes
3. Test at least one error path (bad input, missing auth, not found)
4. Run backend test suite

### CLI / Scripts

1. Run with representative input
2. Verify stdout, stderr, and exit code
3. Test boundary inputs: empty string, malformed input, extreme values

### Infrastructure / Config

1. Validate syntax (linter, dry-run)
2. Verify environment variables are actually referenced in code
3. Check that changes don't break existing config consumers

### Bug Fixes

1. Reproduce the original bug first
2. Apply the fix
3. Verify the bug is resolved
4. Run regression tests
5. Check for side effects on related functionality

### Refactors (no behavior change)

1. Run all existing tests -- they must all pass
2. Diff the public API surface -- no unintended changes
3. Spot-check behavioral consistency on key paths

## Adversarial Probes

Choose probes relevant to the change:

- **Concurrency**: Send parallel requests to creation endpoints -- check for duplicates or data loss
- **Boundary values**: Test with 0, -1, empty string, very long string, unicode, MAX_INT
- **Idempotency**: Send the same mutation request twice -- is the result correct?
- **Orphan references**: Delete or reference a non-existent ID -- does the system handle it gracefully?

## Evidence Format

Each verification item should include:

1. What was checked
2. The actual command run
3. The actual output observed (copy-paste, not paraphrased)
4. Result: PASS or FAIL (with expected vs actual if FAIL)

**Anti-pattern**: "I read the code and the logic correctly validates..." -- this is not evidence. Evidence requires running a command.

## Completion Checklist

Before reporting verification complete:

- [ ] At least one command was run with actual output shown
- [ ] At least one adversarial probe was attempted
- [ ] At least one non-happy-path scenario was tested
- [ ] No "the code looks correct" reasoning was used as a substitute for running commands

## Related Guidelines

- See `guidelines/code/validation.md` for the declarative principles behind this technique.
