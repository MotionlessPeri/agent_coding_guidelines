---
class: experience
scope: universal
triggers: [bug, 修复, 根因, 八成是, 直接改, 校验器告警, 框架报警, 打不开, 卡住, 复现不了, 诊断日志, 取证]
born: "2026-06，写下时的模型未记录"
retested:
  - "2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：D1 pass、D2 pass、D3 fail；见 docs/evaluations/experience-retest-2026-10-15.md"
incidents:
  - 2026-06-visualizer-fix-before-evidence
  - 2026-08-validator-warning-pointed-at-local-code
  - 2026-08-stream-died-after-unlogged-user-action
  - 2026-08-host-hang-blamed-on-user-file
---

# 先取证再修：调试不靠猜

遇到 bug、测试失败、非预期行为，不凭假设直接改代码；先让证据把根因收敛到一个，再动手。改一个未证实的假设，常见后果是修错地方、掩盖症状、引入新问题、烧光失败预算。本条管改之前，[`validation.md`](validation.md) 管改之后，[`reporting-limits-and-null-results.md`](reporting-limits-and-null-results.md) 管报出去那句话。

## 取证手段

诊断日志（变量值、分支走向、是否进入某路径、容器计数、指针有效性）、dump 数据结构、断点、最小复现、bisect、读框架源码。判据只有一条：这条证据出现或不出现，分别证明了什么？能区分相互竞争的假设才算证据，「看起来对」不算。

## 四条判据

1. **框架的校验器只看它面前的局部，告警指向你的本地代码，根因可能在上游数据。** 收到告警先分清它报的是症状所在层还是根因所在层，校验器几乎总是前者。画面分不出的两个假设，用方向性 oracle 打破平局：在源端推一个已知符号的位移，量目标端的符号。任何一条变换链（重定向、坐标转换、单位换算、编解码）都先问「它的方向性验过没有」。
2. **交互式工具的 bug，复现条件常在用户的操作史里，日志里没有。** 日志记结果，不记「这个人五分钟前点了什么」。直接问用户做过什么操作，把它当一等取证手段。
3. **宿主打不开一份文件，而你的插件跑在加载流程里：你是嫌疑人，不是旁观者。** 插件的启用状态会被文档序列化，重开时启动逻辑在加载中途跑起来，表现就是卡住。修法是加载期守卫；取证用格式自己的 SDK 直读那份文件，绕开宿主，读通了同时证明文件没坏、问题在你这层。
4. **agent 自己观察不到时，把取证外包给用户，仍然不要猜。** 给精准的 instrumentation（加哪几条日志、跑哪几步），再给一张「观察 → 含义 → 下一步」的解读表，让回报的证据一次定位到环节。

## 确认后再修

证据收敛到单一根因后才写 fix；fix 后再取证，确认是那个根因被解决而不是症状被掩盖；诊断日志在确认生效之前不删。

## 反模式

| 反模式 | 为什么错 |
|---|---|
| 「八成是 X，直接改 X」 | 假设未证实；根因可能在别处 |
| 连续试多个 speculative fix | 每个都没取证；改对了不知为何，改错了预算烧光。换层之前先取证知道卡在哪层 |
| 过早删诊断日志 | fix 没确认就删，错了要重加 |
| 让用户反复「再试试」却不给精准 instrumentation | 拿不到能定位的证据 |
| 把「代码看着对」当证据 | 读代码不是验证 |
| 把框架校验器的告警当定位结论 | 它只看局部，上游的错伪装成局部几何不对 |
| 只在日志里找交互式 bug 的复现条件 | 操作史不落日志 |
| 宿主打不开文件就先怀疑文件 | 你的插件可能就跑在加载器里；先自查，再用 SDK 直读作独立判据 |
| 用画面判一条变换链的方向性 | 镜像后的结果看起来仍然正常；要用符号断言 |

## 证据

事故记录在 [`evidence/incidents/`](../../evidence/README.md)，清单在本页 frontmatter 的 `incidents`，统计见生成的 [`evidence/INDEX.md`](../../evidence/INDEX.md)。四条判据各来自一次命中，其中「打不开先查自己」那次与报结论规则 1 共用同一条记录。单项目各一次，机制清楚可复述；apply-and-refine。

## 相关

- [`../workflow/agent-lifecycle.md`](../workflow/agent-lifecycle.md)：「probably fine」「code looks correct」是同源自欺；换 approach 或换层的前提是先取证。
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)：oracle 阶梯（方向性断言属 metamorphic 不变量档）、Diagnostic Log Discipline。
- skill `superpowers:systematic-debugging`：debug 方法论的完整版；skill `bugfix-tdd`：取证定位之后的红→绿修复流程。
