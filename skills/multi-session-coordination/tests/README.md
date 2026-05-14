# Multi-Session Coordination — Tests

## Run all

From the skill root (`skills/multi-session-coordination/`):

```bash
python -m unittest discover -s tests -p '*.py'
```

Expected: `Ran 81 tests in ~1s — OK`

## Layout

```
tests/
├── test_state.py                       ← unit tests (78) — state lib + each hook handler
├── scenario_a_no_conflict.py           ← E2E: two sessions, non-overlapping work
├── scenario_b_lease_conflict.py        ← E2E: lease conflict resolved via inbox
└── scenario_c_crash_recovery.py        ← E2E: stale session auto-cleaned + archived
```

## Test isolation

All tests set `MULTI_SESSION_BASE` to a fresh temp directory in `setUp` and unset
it in `tearDown`. They never touch the real `~/.claude/multi-session-coord/`.

## Per-file run

```bash
# Unit tests only (fastest)
python -m unittest tests.test_state -v

# A specific scenario (good for debugging the negotiation flow)
python -m unittest tests.scenario_b_lease_conflict -v
```

## What the scenarios cover

| Scenario | Models design doc Appendix… | Verifies |
|---|---|---|
| A. No conflict | §A | Non-overlapping work passes through; PreToolUse correctly distinguishes own-lease (allow) from other-lease (deny); solo SessionStart archives ended sessions |
| B. Lease conflict + negotiation | §B | Full inbox negotiation: deny → release_request → UserPromptSubmit surfaces it → A resolves + writes release_notice → B's next turn sees notice → B claims and edits |
| C. Crash recovery | §C | Stale lease (heartbeat > 30 min) auto-released by next SessionStart cleanup; ended session archived under `archive/<date>/`; new session can claim freely |

## Adding new scenarios

When you discover a new failure mode in production:

1. Capture it as a manual fixture (file paths, registry state, hook calls in order)
2. Drop a `scenario_<short_name>.py` here that programmatically reproduces it
3. Assert the state at each interesting point — not just the end result
4. Commit alongside the fix

This matches the `tdd-with-fixtures` skill's escape-hatch convention for
behaviors that pure unit tests can't capture.
