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

## LLM-as-judge 评测（评 agent / 研究类输出）

当要评的是 **agent 生成的输出 / 研究报告 / 难以写确定性断言**的产物（不像代码可跑测试）时，Anthropic 实测**最稳、最贴合人工判断**的方式是：**单次 LLM 调用 + 单个 prompt**，按 rubric 输出 **0.0–1.0 分 + pass/fail**。比多次调用 / 多 judge 投票更一致。

rubric 五维（可裁剪）：

- **事实准确**（claim 与来源一致）
- **引用准确**（引用的源确实支持该 claim）
- **完整性**（要求的方面都覆盖）
- **源质量**（优先一手源 over 二手）
- **工具效率**（用了对的工具、次数合理）

适用：评 research / digest 输出、评一段 agent 自动改动是否达标、给「难以单测」的产物一个可复现评分。**不适用**：能写确定性断言的代码——那走前面的「运行命令 + 对抗探针」。

> 来源：Anthropic [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)。

## Diagnostic Log Discipline

When debugging a bug that requires adding diagnostic logs:

- **Do not remove diagnostic logs until the user confirms the fix works.** A premature
  cleanup forces re-adding the same logs if the fix turns out to be wrong.
- Add logs, build, let the user reproduce, read the logs, propose a fix, build again —
  but keep the logs in place.
- Only remove logs in a separate cleanup step after the user explicitly confirms the
  issue is resolved.

## Completion Checklist

Before reporting verification complete:

- [ ] At least one command was run with actual output shown
- [ ] At least one adversarial probe was attempted
- [ ] At least one non-happy-path scenario was tested
- [ ] No "the code looks correct" reasoning was used as a substitute for running commands

## Related Guidelines

- See `guidelines/code/validation.md` for the declarative principles behind this technique.
