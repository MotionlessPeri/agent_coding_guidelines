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

## 选可信 check：四要素 + oracle 判据（MFIC）

前面按改动类型给了验证策略，但还缺一个横切判断：**一个 check 本身可不可信？** 尤其当写代码和写 check 的是同一个 agent 时，用同一个错误假设写出来的 test 会跟着错代码一起变绿——静默通过。

**试金石（一句话判断）**：*如果同一个 agent 既写了 check 又写了被检对象，它能带着错误工作通过吗？* 能 → 这个 check 可被糊弄，不可信。

一个可信的 check 要同时满足四要素，缺一个就退化成常见近似失败：

| 要素 | 含义 | 缺了它 |
|---|---|---|
| **Mechanically** | 用例机器穷举 / 变异 / 生成，不手挑 | 手挑用例，漏掉没想到的分支 |
| **Falsifiable** | 用例真会咬——错了就红，且你无法预先安排让它绿 | 空洞绿测（"没崩就行"）|
| **Independent** | 判据在因果上独立于生产者（职责分离的软件版）| 合谋 check，跟代码共享盲点 |
| **Control** | 有权拦截（fail build / block commit），不只 log | 只告警不拦，坏结果照样进 |

### oracle 判据：什么时候才真的需要"换一个 agent"

Independence 不等于"永远要另找一个人 / agent review"。真正的分界是**有没有一个生产者之外的 oracle**：

| 情形 | 例子 | 谁写 check 重要吗 |
|---|---|---|
| **存在外部 oracle** | round-trip 逆运算 `decode(encode(x)) == x`、reference 实现差分、变换不变量、事先定死的 checksum | **不重要**——同一个 agent 写代码和 check 也糊弄不过去，因为判官是它控制不了的独立因果物 |
| **无 oracle** | 普通 example test，手写的期望值本身就是"真理标准" | **重要**——同一个 agent 会把同一个错误假设同时写进代码和期望值，一起错到底 |

推论：**只有在"无 oracle"这种情形，才真正需要一个独立的 checker**（且这个 checker 只从契约推导、绝不读实现——读了就被带进同一盲点=合谋）。有 oracle 时，优先花小成本上 oracle-based check，比拉一个独立 reviewer 更便宜也更稳。这跟 [`coordination-patterns.md`](coordination-patterns.md) 的"验证别人的实现用 fresh worker 防 anchoring"是一体两面：那条讲无 oracle 时怎么隔离 checker，这条讲有 oracle 时可以省掉隔离。

### 验证策略阶梯：优先选作者没写的判官

按"判官独立性"从强到弱，选**能上的最便宜那一档**：

1. **穷举有限域**——域有限就跑遍，不抽样。
2. **round-trip 逆运算**——操作有逆就 `f⁻¹(f(x)) == x`。谁写的 round-trip 不影响判据。
3. **差分 vs reference 实现**——有参照实现就两边都跑、diff 结果。
4. **metamorphic 不变量**——断言关系而非具体值（如复杂度门断言 `f(2N) ≈ 2·f(N)`，比值抵消掉机器速度、跨机可移植；无需期望值也无需 reference）。
5. **input-mutation 覆盖率**——把"我的 validator 覆盖了整个格式"这种不可证伪的空话变成一个数：拿一个合法输入，逐 bit / byte 翻转，断言 validator 现在**拒绝**它；被拒的比例就是覆盖率。两个防作弊前提：(a) 配一份全合法输入的 corpus 必须全过（否则"拒绝一切"的 checker 拿满分）；(b) 只统计"必须有意义"的字节（padding / checksum 排除区是合法 don't-care）。
6. **property-based + shrink**——都不满足才生成属性、把失败 shrink 到最小反例。

核心原则：**优先用作者没写的 oracle。** 手写的"期望值"本身可能就是 bug；round-trip / reference / 不变量不会，因为它们都不依赖"作者当初想对了"。

> 来源：pmarreck，[MFIC — Mechanically-Falsifiable Independent Control](https://gist.github.com/pmarreck/b30aa3ca69cb70a5526f8a63ab8c8d7e)。把企业内控（COSO / SOX：职责分离 / 预防-检测-纠正控制 / 控制测试）搬到"LLM 是不可信方"的语境。TDD 只提供四要素里的 Falsifiable（红相证明测试能咬），其余三个要另外补。

## 否定式约束是 LLM review 的结构性盲区 → 配确定性 check

LLM **系统性地弱于否定**：处理否定语句（"不要 X" / negated constraint）显著差于肯定语句。所以让 LLM 当审查员核"合不合规"时，**写成 `DO NOT ...` 的约束是它最容易 false-negative 的地方**——代码违反了否定约束，LLM review 读着读着把"不要"忽略了，照样判"通过"。

推论：**否定式约束不能只靠 LLM review 兜，必须配一个确定性检查**（grep / lint / 断言 / [`enumerate-then-adjudicate.md`](enumerate-then-adjudicate.md) 的机械枚举）。这跟上面的 oracle/mechanical-check 阶梯是一体的——否定约束正是"手写期望值不可靠、要上 mechanical oracle"的高发点；也跟 [`fact-forcing-gate.md`](fact-forcing-gate.md) 的 advisory vs hard 对齐：否定约束是"advisory review 兜不住、需要 hard gate"的典型。

- **既定事实**（可引）：LLM 弱于否定 —— Truong, Baldwin, Verspoor & Cohn (2023),《Language models are not naysayers: An analysis of language models on negation benchmarks》(\*SEM 2023, https://aclanthology.org/2023.starsem-1.10/)：直接对比肯定 vs 否定，记录否定 benchmark 上低于随机 + inverse scaling。
- **约束翻转机制**（可引）：Elkins & Chun (2026),《Auditing Negation Sensitivity in Moral Dilemmas》(https://arxiv.org/abs/2601.21433)：模型在同一提案被措辞成"禁止"时会翻转合规判断。
- **诚实边界**："LLM review 对 DO-NOT 约束 false-negative"这一步是**合理推论**——上述研究未直接 benchmark "LLM 审代码/spec 的 DO-NOT 合规"这个确切任务。正因为是推论而非实测，才更该上确定性检查兜底。

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
- [`techniques/enumerate-then-adjudicate.md`](enumerate-then-adjudicate.md) —— "选可信 check" 的一个具体落地：把"让 LLM 找全所有 X"这个静默失败换成"机械枚举候选 + LLM 逐条裁决"。
- [`techniques/coordination-patterns.md`](coordination-patterns.md) —— 无 oracle 时怎么隔离一个独立 checker（fresh worker / 从契约推导）。
