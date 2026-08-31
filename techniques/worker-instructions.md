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

### 记号歧义：完整且正确的 brief 仍会被读错

上一节管「brief 里的 claim 对不对」。但 claim 全对、oracle 也随任务给了，跨边界的**公式与作用域**
仍然会静默走样：对方拿到的信息足够开工，于是照着实现，歧义只在对拍时才暴露——一次一个往返。

同一轮跨 lane 工作里命中三次，三次走样的地方各不相同：

| 走样在哪 | 发出方写的 | 接收方合理地读成 | 后果 |
|---|---|---|---|
| **作用域** | 「只在重定向入口生效」 | 另一个入口档位 | 据此写进契约「该修正在这一档两边行为不一致」，并要求另一 lane 换实现路径。实测那个属性在这一档下是惰的（三个取值输出逐位相同），前提整个不成立 |
| **符号** | 「横移量 ≈ 两侧髋距之差的一半」（写成绝对值形式） | 幅度对了就行，方向按语义猜 | 4 个骨架的符号全反。发出方另给的一句自然语言解释，字面读**正好是反的** |
| **参照系** | 「Δ = 该骨本应承担的扭转**增量**」 | 该骨当前的**全部**扭转 | 把整根骨的扭转都拿去重分配（参照实现只分 IK 阶段新引入的那部分：恒 8.12°，对方的随注入量线性增长到 89°）。生产后果是把动画师做的扭转整根抹掉 |

四条修法：

1. **公式带符号，把正方向写进式子。** 不给 `|a − b|` 这种绝对值形式——写 `Δ = (b − a) / 2，外移为正`，
   「哪个减哪个」「正方向指哪」都钉死。自然语言解释只是辅助，冲突时以式子为准（这一点也要写明）。
2. **「增量」必须写清相对什么。** 相对求解前 / 相对静止姿势 / 相对源，是三个差一个数量级的量。
3. **作用域写标识符，不写自然语言。** 同一个词在两套命名里常指不同东西（例：「重定向入口」在被
   刻画的库里指含 IK 的那个入口，在契约里指不含 IK 的那一档）。写 `HIKSolveForCharacter` /
   `HIKSolveForCharacterRetarget`，歧义当场消失。
4. **随规格给一份 oracle 数值表，并预先点出哪些数不该拿来验。** 本轮给出的期望值表里手部精确吻合、
   脚部按设计必然不吻合——不预先说明，接收方拿脚部验会以为自己做错了。给表之前先确认量具自身
   可信，见 [`adversarial-verification.md`](adversarial-verification.md) 的「量具先自证」。
5. **双方都有的词，逐个问「这个词在他那边指什么」。** 词汇表错位比记号歧义更难自查：同一个词
   （「面板」/「视口」/「会话」/「角色」）在写方与读方的词汇表里各指一物，而写方重读自己的句子
   发现不了——在他自己的表里它是对的。实测：「面板自己 push」在写方语境为真（app 胶水层习称
   面板），在读方语境为假（读者拿到的 kit 面板根本不持撤销栈）⇒ 照抄会让读者以为这件事有人替他
   做了。这些**双方共有的词最不像术语，所以最不会被检查**。（单项目一击；修法与第 3 条同向——
   所指有歧义时，写读者语境里为真的那个名字。）

**诚实边界**：同一项目内 3 次独立命中、跨项目未验（不满足
[`knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md) 的两击规则）——apply-and-refine。
两点让它比一般单项目经验强些：第 3 次是**接收方**独立指认出的 pattern，不是发出方事后归纳；
三次的机制不同（作用域 / 符号 / 参照系），是同族的三个面，不是同一个坑踩三遍。

> **回报方向的对称面**：上面管"派出去的规格被读错"，反方向是"报回来的结论本身错了" ——
> 尤其把**自己这层的收窄**说成**下层 / 框架 / 对方的能力边界**，会让协调者放弃本来可行的路，
> 且错结论的污染面按转发次数放大（协调者转发一次就多一个 lane 中毒）。收到"做不到"时追一句
> **"哪一层做不到"**。见 [`../guidelines/code/reporting-limits-and-null-results.md`](../guidelines/code/reporting-limits-and-null-results.md) 规则 1。

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
