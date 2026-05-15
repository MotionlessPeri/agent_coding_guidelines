# Bug-Fix TDD (红→绿 Discipline)

修 bug 跟开发 feature 用 TDD 不一样——bug fix 的 TDD 是**红→绿 discipline**：
先写一条能复现 bug 的 failing test（红测），跑出来**真的看到失败**，再改
production code 到 test pass（绿测），最后单 commit 落地。

防的是"看了一眼代码、自信改了一行"这种**无证据**修复。

## 核心规则

1. **红测先行**：先写 failing test 复现 bug，跑出来确认是 FAIL
   - 不能只是 read code 自信 bug 会被复现 —— 必须真跑、看到失败输出
   - test fixture / 断言尽量精准命中 root cause，不只测表面症状
2. **绿测**：改 production code 到 test PASS
3. **回归**：跑全套 regression test 确认没破其他
4. **单 commit**：test + fix + 必要的注释更新**一个 commit 落地**，不分开

## Why

- **红测先确认 bug 可复现**：避免修了一个不存在的 bug，或修错了地方
- **绿测是证据进 commit log**：未来 grep 这条 commit 能看到"曾经存在这种失败模式"
- **同 commit 让 regression 立刻触发**：以后再有人改这块碰回这个 bug，test 会先失败
- **不走红测直接改的 fix 常见失败模式**：修了 1 个症状漏掉同类 N 个、改到错误位置、
  改完跑没跑都不知道；红测把这些 failure mode 全堵掉

## How to Apply

任何 bug 修复对话起手到落 commit 的具体顺序：

1. user 描述症状 + agent 确认 root cause 之后，**先 propose 红测案给 user**
   （fixture 输入 + 期望断言 + 期望失败位置），让 user 校准方向
2. 写完红测，**先跑一次确认 FAIL**（看到具体 fail message，不是只看 build pass）
3. **才能动 production code**——红测确认前不写任何 fix 代码
4. 改完跑绿测，确认从 FAIL → PASS
5. 跑全 regression 套确认没破其他 test
6. **单 commit**：test 文件 + production fix + 必要注释一并 stage 一次 commit

## Edge Cases

- **bug 没法写自动化测试**（UI 视觉问题、editor-only 交互、外部服务依赖等）：
  写一份 **manual reproduction case**（fixture + 操作步骤 + 期望表现 vs 实际表现）
  当锚点，跟 fix 一起进 commit。原则仍是"先 demonstrate bug 再 fix"，只是
  demonstrate 从自动化变成人工。
- **bug 在跑的过程中暴露新 bug**：不要在同一 commit 顺手修第二个 bug。每个 bug
  各自走一遍红→绿，各自一个 commit。
- **修 bug 同时需要 refactor**：refactor 跟 fix 分开 commit。refactor 不得改变
  test 通过状态，fix commit 必须只含 test + 最小修复。

## 跟其他 Guideline / Skill 的关系

- **`superpowers:test-driven-development`** (skill) —— 那是 **feature 开发 TDD**
  （增量 feature 先写 spec test 再实现），本条专管 **bug fix TDD**（红测必须先
  demonstrate bug 存在，绿测必须 demonstrate fix 生效）。两条**互补不重叠**。
- **`superpowers:systematic-debugging`** (skill) —— 那是 debug 阶段的方法论
  （怎么定位 root cause），本条接在它之后：root cause 定位完，进入修复阶段的
  discipline。
- **`guidelines/code/validation.md`** —— 那条强调 "evidence before assertions"
  （跑命令看实际输出），本条把这个通则具体化到**测试形式的 evidence**：红测
  是"bug 存在"的证据，绿测是"fix 生效"的证据。
- **`guidelines/workflow/agent-lifecycle.md`** —— 那条的 "Validation Before
  Completion" 通则要求 "never claim done without verification"，本条是 bug fix
  场景的具体落地：verification = 红测变绿测 + 回归全过。

## Examples

### Anti-pattern：无证据修复

```
user: 报 bug X
agent: 读 code、推测原因、改一行 → commit
```

失败模式：
- 修的可能不是 X 的真正 root cause
- 修了一个症状漏掉同类 N 个
- 以后这块代码再改可能 regress，没人察觉

### 正例：红→绿 流程

```
user: 报 bug X
agent: 读 code 推测 root cause → propose 红测案给 user 校准
       → 写红测 → 跑确认 FAIL → 改 production → 跑确认 PASS
       → 跑全 regression → 单 commit (test + fix)
```

证据链完整：
- 红测 FAIL 输出 = bug 真实存在的证据
- 绿测 PASS 输出 = fix 真实生效的证据
- commit log 同时保留两个证据，未来 regress 时立刻触发

## Promotion Trigger

本条 guideline 来自**多个项目的 bug fix 实践**，规则跨项目通用。promote 成
guideline（而非 skill）的理由：

- 适用范围是 "agent 修任何 bug 都该走"，是常态 discipline，不是按特定 phase /
  domain 触发的 skill
- 内容是声明式 ("always do red-then-green")，符合 `guidelines/` 的 declarative
  rule 定位
- 跟现有 `superpowers:test-driven-development` skill 互补：那条是 feature TDD
  domain skill，按特定开发阶段 lazy load；本条是**通则**，每次 bug fix 都该入眼
