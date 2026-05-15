---
name: bugfix-tdd
description: Bug-fix TDD discipline — 红→绿 流程。修 bug 必须先写一条能复现 bug 的 failing test（红测），跑出来真的看到 FAIL，再改 production code 到 test PASS（绿测），跑全 regression，最后 test + fix 单 commit 落地。跟 superpowers:test-driven-development 的区别：那条是 feature TDD（写 spec test → 实现满足 spec），本 skill 是 bug-fix TDD（写 reproduction test → demonstrate bug → fix → demonstrate fix）。跟 superpowers:systematic-debugging 衔接：那条管"怎么定位 root cause"（debug 阶段），本 skill 管"root cause 定位完后怎么修"（fix 阶段）。防的是"看了一眼代码、自信改了一行"这种无证据修复——经常修了一个症状漏掉同类 N 个、或改错位置。
when_to_use: 任何 bug 修复场景——user 报 bug + agent 确认 root cause 之后进入修复阶段，写 fix 代码前。包括：项目代码 bug、工具/脚本 bug、CI/部署 bug、test 自身 bug。Skip 场景：纯 typo / 文档 / 注释修正（无行为变化）；明确是 cosmetic-only 改动（格式、命名）；user 显式说"先快速试一下不走完整流程"（但要在回复里点出跳过了，并标记后续需要补红测）。
---

# Bug-Fix TDD (红→绿 Discipline)

修 bug 跟开发 feature 的 TDD 不一样——bug-fix TDD 的核心是**先 demonstrate
bug 存在**（红测），再 **demonstrate fix 生效**（绿测）。两个 demonstrate 都
要真跑出来看输出，不能停在"看代码自信"。

## When This Fires

**Triggers (任一)**:
- user 报告 bug 后，agent 确认 root cause 进入修复阶段
- 跑 regression 时发现某个 test fail 暴露的 bug
- code review 发现 latent bug（已存在但未触发）
- `superpowers:systematic-debugging` 定位完 root cause 后衔接进入

**Does NOT fire**:
- 纯 typo / 文档 / 注释修正
- cosmetic-only 改动（格式、命名、import 顺序）
- feature 开发（用 `superpowers:test-driven-development` 而不是本 skill）

## 核心规则

1. **红测先行**：先写 failing test 复现 bug，跑出来确认是 FAIL
   - 不能只是 read code 自信 bug 会被复现——**必须真跑、看到失败输出**
   - test fixture / 断言尽量精准命中 root cause，不只测表面症状
2. **绿测**：改 production code 到 test PASS
3. **回归**：跑全套 regression test 确认没破其他
4. **单 commit**：test + fix + 必要的注释更新**一个 commit 落地**，不分开

## How to Apply

按顺序走，**不要跳步**：

### Step 1: 跟 user 校准红测案

agent 确认 root cause 后，**先 propose 红测案给 user 看**：
- fixture 输入是什么
- 期望断言（assertion）针对什么
- 期望从哪里失败（哪个 file:line / 哪种 error 类型）

让 user 校准方向。如果 fixture / 断言不精准，红测可能"通过"在错误的地方——等于
没抓到 bug。**user 校准比直接动手写更省时间。**

### Step 2: 写红测 + 跑确认 FAIL

写完测试 case 后**立刻跑一次**：
- 看到具体 fail message（不是只看 build pass / compile pass）
- fail 位置要跟 propose 的预期一致；不一致就停下查为什么

**绝对不能跳过这一步**。"我相信这个测试会失败"不是证据；跑出来的 fail
输出才是证据。

### Step 3: 改 production code

红测确认后才能动 production code。改动**最小化**：
- 只改让红测变绿测必需的代码
- 不顺手 refactor 邻近代码（refactor 走单独 commit）
- 不顺手修第二个 bug（每个 bug 各自一遍红→绿）

### Step 4: 跑绿测

确认从 FAIL → PASS。看输出，不只看 exit code——有时 test framework 配置错
会 silently pass 一个本该 fail 的测试。

### Step 5: 跑全 regression

确认没破其他 test。如果 break 了：
- 先判断是不是 test 本身假设错了（test 错就修 test，跟 fix 同 commit）
- 不能 silently skip / comment out 失败 test
- 不能"先 commit 再说，下个 commit 修 regression"

### Step 6: 单 commit 落地

stage 三类内容一并 commit：
- 新增的 test（红测变绿测的那条）
- production fix
- 必要的注释（解释 fix 为什么这样改，如果非自明）

commit message 描述**修了什么 bug** + **怎么发现的**（如果非自明），让未来
grep commit log 能找到这条 bug 的历史。

## Edge Cases

### Bug 没法写自动化测试

UI 视觉问题、editor-only 交互、外部服务依赖等——auto test 不可达。

按 `superpowers:tdd-with-fixtures` 的 escape hatch：写一份 **manual
reproduction case**（fixture + 操作步骤 + 期望表现 vs 实际表现）当锚点，
跟 fix 一起进 commit。原则不变："先 demonstrate bug 再 fix"，只是
demonstrate 从自动化变成人工。

### Bug 在修复过程中暴露新 bug

不要在同一 commit 顺手修第二个 bug。每个 bug 各自走一遍红→绿，各自一个
commit。bundle 多个 bug 进一个 commit 会：
- 让 commit log 失去"每条 commit = 一个 bug"的可读性
- 让以后 bisect 定位某个 bug 引入点更难
- 让 review 难以审查

### 修 bug 同时需要 refactor

refactor 跟 fix 分开 commit。refactor commit 不得改变 test 通过状态；
fix commit 必须只含 test + 最小修复。

### Bug 是"行为正确但性能不达标"

红测可以是 perf benchmark + 上限断言（如 "must complete in <500ms"）。
fixture 要稳定（同一 input 在 CI 上跑同样耗时分布）。如果 perf 测试不稳，
fall back 到 manual reproduction case + 跑前后对比数据。

### 红测真的写不出来怎么办

如果尝试 30 分钟仍写不出 demonstrate bug 的 test：
1. 先怀疑 root cause 定位错了——回 `superpowers:systematic-debugging`
2. 再怀疑 bug 实际不在 codebase 内（可能是依赖 / 环境问题）
3. 最后才考虑跳过红测——但必须在 commit message / PR 描述里**显式说明**
   为什么跳过，并标记"红测 TODO"

跳过红测不是默认选项，是 last resort。

## Anti-Patterns

| Anti-pattern | 失败模式 | 正例 |
|---|---|---|
| 读 code → 自信改一行 → commit | 修的可能不是 root cause；漏掉同类症状；以后 regress 没人察觉 | 读 code → 写红测 → 跑 FAIL → 改 → 跑 PASS → commit |
| 写完红测不跑、直接动 production | 红测可能本身写错（fixture 错 / 断言错），动 production 后才发现等于白干 | 红测写完**立刻**跑一次确认 FAIL message 跟预期一致 |
| 红测放 commit A、fix 放 commit B | bisect / cherry-pick 困难；commit A 单独 check out 时 test 红 | test + fix 同一 commit |
| 顺手修第二个 bug | commit 信息糊；review 难审；以后定位"哪个 commit 引入修复"变难 | 每个 bug 各自一个 commit |
| `@skip` / 注释掉失败 test "回头修" | "回头"通常不来；regression 失去 coverage | 当场修；test 真错就跟 fix 同 commit 一起改 |
| 跑绿测只看 exit code 不看输出 | 某些 framework 配错会 silently pass；fix 没生效但显示绿 | 看实际 fail/pass message + 看测试断言确实命中 |
| "这个 bug 太小不值得写 test" | 小 bug 复发概率更高（没人记得）；红测成本很低 | 任何 bug fix 都写红测，除非红测真写不出（last resort） |

## Composition

- **`superpowers:test-driven-development`** —— feature TDD skill。base cycle
  是 red-green-refactor，本 skill 复用同样的 red-green 节奏但 trigger 时机
  不同（bug fix vs feature）。两者**互补不重叠**：feature 开发用 superpowers；
  bug 修用本 skill。
- **`superpowers:systematic-debugging`** —— debug 方法论 skill，管"怎么定位
  root cause"。本 skill 在它之后衔接：root cause 定位完进入修复阶段。
- **`superpowers:tdd-with-fixtures`** —— TDD discipline + escape hatch skill。
  本 skill 的 "Bug 没法写自动化测试" edge case 走它的 fixture + manual case
  pattern。
- **`guidelines/code/validation.md`** —— "evidence before assertions" 通则。
  本 skill 把这条通则具体化到**测试形式的 evidence**：红测 = bug 存在的证据，
  绿测 = fix 生效的证据。
- **`guidelines/workflow/agent-lifecycle.md`** —— "Validation Before
  Completion" 通则的具体落地。verification 形式 = 红测变绿测 + 回归全过。
- **`guidelines/workflow/commits.md`** —— "one commit = one theme" 规则。
  本 skill 强化为"一个 bug fix = test + fix 一个 commit"。

## Failure Modes

| Failure | Looks like | Correct action |
|---|---|---|
| 跳过红测 | "我看了代码，bug 应该在 X 行，改一下" | 停下，先写红测跑确认 FAIL |
| 红测不跑就动 production | "test 写好了，开始改 fix" | 红测先跑确认 FAIL，再动 production |
| 红测断言不精准 | test 通过但 bug 仍在某些 case 触发 | 让红测断言命中 root cause，不只测表面症状 |
| Fix 涉及多文件、红测只覆盖一部分 | 部分 case 修了部分没修 | 红测要覆盖所有 manifest case，或拆多个红测 |
| Regression 失败 silently skip | `@skip` / 注释掉 | 当场查、当场修；test 错就改 test 跟 fix 同 commit |
| Test + fix 分开 commit | "test 先 commit，fix 下个 commit" | merge 成一个 commit |
| Commit message 没说修了什么 bug | `fix: bug fix` | 写清楚 bug 症状 + root cause + 怎么发现 |

## Related

- `superpowers:test-driven-development` — feature TDD（基础 red-green-refactor cycle）
- `superpowers:systematic-debugging` — debug 阶段方法论，本 skill 衔接其后
- `superpowers:tdd-with-fixtures` — TDD + escape hatch，处理 auto-test 不可达的 bug
- `guidelines/code/validation.md` — "evidence before assertions" 通则
- `guidelines/workflow/commits.md` — commit 粒度 + 单 theme 规则
- `guidelines/workflow/agent-lifecycle.md` — Validation Before Completion 通则
