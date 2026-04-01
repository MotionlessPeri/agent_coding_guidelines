# Worker Instructions

## Core Principle

Workers cannot see the coordinator's conversation. Every prompt must be **self-contained** — include all information the worker needs to complete the task without asking questions.

## Required Elements

Every worker prompt should include:

1. **Specific file paths and line numbers** — not "that file" but `src/auth/validate.ts:42`
2. **Completion criteria** — what "done" looks like
3. **Purpose statement** — helps the worker calibrate depth and approach

### Purpose Statement Examples
- "This research is for writing a PR description — focus on user-visible changes."
- "I need this to plan implementation — report file paths, line numbers, and type signatures."
- "This is a pre-merge quick check — verify the happy path only."

## Anti-Patterns

| Bad | Why | Good |
|-----|-----|------|
| "Fix the bug we discussed" | Worker cannot see the discussion | "Fix the null pointer at `src/auth/validate.ts:42` — session's user field is undefined when..." |
| "Based on your findings, implement the fix" | Delegates understanding to the worker | Synthesize findings yourself, then give specific instructions |
| "Create a PR for the recent changes" | Which changes? Which branch? Draft? | "Push branch `fix/session-expiry` to origin, create a draft PR targeting `main`, add team-x as reviewer" |
| "Tests seem broken, take a look" | No error message, file path, or direction | "Test `validate.test.ts:58` fails — expects 'Invalid session' but gets 'Session expired'. Update the assertion." |

## Templates by Task Type

### Implementation
```
Fix [what] at [file:line].
[Describe the root cause in 1-2 sentences.]
[Describe the expected fix.]
Run related tests and type checks. Commit and report the hash.
```

### Research (read-only)
```
Investigate [area/module].
Find [what you're looking for — e.g., "where session handling and token validation
could produce null pointers"].
Report file paths, line numbers, and relevant type signatures.
Do not modify any files.
```

### Correction (continuing a failed worker)
```
[Reference what the worker did — not what you discussed with the user.]
Your [change] caused [specific problem — e.g., "test validate.test.ts:58 fails,
expects 'Invalid session' but gets 'Session expired'"].
Fix the [specific thing to fix]. Commit and report the hash.
```

### Git Operations
```
From [base branch], create branch '[branch-name]'.
[Cherry-pick / commit / merge instructions with specific hashes.]
Push and create a [draft/ready] PR targeting [target branch].
Add [reviewers].
Report the PR URL.
```

## Prompt Checklist

Before dispatching a worker, verify:
- [ ] File paths, line numbers, and error messages are included (not paraphrased)
- [ ] Completion criteria are stated
- [ ] For implementation: "run tests + type checks, commit, report hash"
- [ ] For research: "report findings, do not modify files"
- [ ] For git operations: branch name, target branch, draft/ready, reviewers are specified
- [ ] For corrections: references what the *worker* did, not what you discussed with the user
- [ ] Purpose statement is included to calibrate depth

## Related Techniques

- See `techniques/coordination-patterns.md` for the overall multi-agent workflow.
