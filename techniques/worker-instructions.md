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

### Self-contained ≠ correct

A prompt can be **complete** (has everything the worker needs) yet **assert wrong facts**. Completeness is not correctness — separate what you *know* from what you *assume*:

- Tag each technical claim as **verified** (and ship the evidence — the oracle output / dump / test result) or **assumption** ("I think X — unverified, confirm before relying on it").
- **Ship the oracle/evidence with the task, not just your conclusion.** If you hold a ground-truth dump the worker must diagnose against, hand it over. A worker debugging against your (possibly wrong) second-hand conclusion costs a full round-trip every time you were wrong.

Learned from a multi-conversation cross-repo run (see skill `role-lane-coordination`): a coordinator twice baked confidently-wrong ground-truth into self-contained briefs; each error was a full round-trip, caught only by the dev lane's adversarial verification — not by the human.

## Anti-Patterns

| Bad | Why | Good |
|-----|-----|------|
| "Fix the bug we discussed" | Worker cannot see the discussion | "Fix the null pointer at `src/auth/validate.ts:42` — session's user field is undefined when..." |
| "Based on your findings, implement the fix" | Delegates understanding to the worker | Synthesize findings yourself, then give specific instructions |
| "Create a PR for the recent changes" | Which changes? Which branch? Draft? | "Push branch `fix/session-expiry` to origin, create a draft PR targeting `main`, add team-x as reviewer" |
| "Tests seem broken, take a look" | No error message, file path, or direction | "Test `validate.test.ts:58` fails — expects 'Invalid session' but gets 'Session expired'. Update the assertion." |
| Fix agent returns only a summary instead of the full content | When told "fix document X", many agents summarize what they changed instead of outputting the fixed document. The summary is useless for the coordinator — it has no file to write. | **Always include in the prompt: "Output the complete fixed document, do not omit any content."** When the worker's output is meant to be written back to a file, make the expectation explicit. |
| Coordinator writes a fan-out worker's output to the wrong file | With N workers each fixing a different document, nothing in the output itself says which file it belongs to — so a bad zip / off-by-one / resumed-cache mismatch silently sends worker i's output to file j. Text diffs won't reveal it: every line is still *a* line, just about the wrong topic. | **Make each worker echo its target path as the first line of its output, and assert that line matches the intended destination before writing.** Also assert an invariant the content itself must satisfy (title contains the expected topic). |
| Worker's raw reply gets written to disk verbatim | Agents wrap deliverables in prose ("here is the fixed document:") and fences, and append change summaries. Written as-is, the file gets a leading worklist, a stray outer ``` fence, and a trailing changelog. | Extract the deliverable from the reply before writing. Then verify structurally — for markdown, first line is a heading and fence count is even. |

## 反模式（中文摘要）

| 反模式 | 后果 | 修法 |
|--------|------|------|
| Fix agent 只输出摘要不输出完整内容 | 协调者拿不到完整的修复后文件，无法写入 | prompt 里显式强调："必须输出完整的 Markdown 文档内容，不要省略" |
| 协调者把 fan-out worker 的输出写进错误的文件 | 输出内容自身不带「我是给哪个文件的」，所以一次 zip 错位 / off-by-one / resume 缓存错配就会静默串行。**文本 diff 看不出来**——每一行都还在，只是讲错了主题 | 让每个 worker 把目标路径作为输出第一行回显，写盘前断言它等于预期目标；再断言一条内容自身必须满足的不变量（标题含预期主题） |
| worker 的原始回复被原样落盘 | agent 会把交付物包在散文（"以下是修复版文档："）和围栏里，末尾还附改动汇总。原样写盘就得到开头一段工单、中间一层多余围栏、结尾一张 changelog | 写盘前先从回复里抽出交付物；再做结构校验（markdown 就查首行是不是标题、围栏数是不是偶数） |

> 这两条来自一次真实损失：9 份文档的「源码验证修复」fan-out 跑完后，三份文档的内容被写进了
> 错误的文件，两个主题（渲染管线架构、RHI 架构）因此在仓库里丢失，且四份文档的正文被整段
> 包进 ```markdown 围栏（导致代码块边界从第一行起整体错位，散文渲染成代码）。这些都没有被
> 当次的 review 发现——因为逐行看每一行都是合理的。真正抓到它的是一条机械断言：**文件名与
> 文档 H1 标题是否对应**。教训是 [`adversarial-verification.md`](adversarial-verification.md)
> 「选可信 check」的直接应用：fan-out 写盘这件事需要一个 agent 无法糊弄的判官，而「文件名 ↔
> 内容主题一致」正是这样一个判官。

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
