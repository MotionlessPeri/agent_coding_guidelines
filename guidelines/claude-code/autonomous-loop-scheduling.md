# Claude Code 自主 loop(ScheduleWakeup 动态 /loop)的机制 + 纪律

用户明确要求 agent **自主迭代 / 挂 loop 跑下去 / 断线也能续**时,用 Claude Code 的
`ScheduleWakeup`(动态 `/loop` 模式)。它把「一个 agent 回合内的连续多步工作」延伸成
**跨回合、可续跑、可无人值守**的自主循环。属 Claude-Code harness hidden contract + 一套
用户确认过的 workflow 纪律。**Codex 无等价物**——本条只适用 Claude Code。

## 核心结论

1. **arm 不结束回合**:`ScheduleWakeup` 排好下次唤醒后**当前回合仍继续**——你照常在本回合往下做,
   唤醒只是「回合结束 / 断线」时的**续跑/兜底**。别 arm 完就干等唤醒。
2. **loop `prompt` 会被原样重放** → 必须**自包含 + 指向 durable SoT**(committed 的 worklog / 进度文档),
   因为压缩(compaction)会丢对话细节;唤醒后靠读那几个文件恢复,而不是靠记住对话。
3. **`stop: true` 取消 loop**;决策做完 / 有新阶段再**重新 arm**。
4. **遇真正需要用户拍板的点:停 loop,别空转**——loop `prompt` 里就要写「遇需用户决策停下问、
   别 fabricate」。让唤醒在一个只能等用户的点上反复醒来是纯浪费。
5. **到边际递减 / 没有真价值的活了:停**——别 manufacture busywork 喂 loop。

## 什么时候用它 vs `/goal`

Claude Code 另有一个原生的「朝目标自主推进」命令 `/goal`,跟本条是**两个不同机制,按任务形态选**,不是二选一的优劣。对比如下(`/goal` 一栏据[官方文档](https://code.claude.com/docs/en/goal),**非本项目实测**):

| 维度 | `/goal` | ScheduleWakeup 动态 loop(本条) |
|---|---|---|
| 停止判定 | 独立小模型每轮判完成条件——**软**,且只看对话输出、不跑命令不读文件 | agent 自己按 backlog + 测试 + stop 纪律判 |
| 跨回合 / 扛 compaction / 断线续跑 | 弱:单 session;`--resume` 恢复条件但**轮次/计时/token 基线全重置** | **强**:prompt 重放 + 指向 durable SoT |
| 失败熔断 | **无原生熔断**——只能把上限写进条件(仍是软判)或另叠脚本 Stop hook | 靠 stop 纪律 + 账号 usage limit 兜底 |
| 适合 | **短、单 session 能收敛、完成条件能自证**(如「修到 `npm run lint` 退 0」) | **长、多里程碑、无人值守、怕中途断** |

**选择判据**:一晚跑不完 / 会触发 compaction / 怕断线 → ScheduleWakeup(本条);任务短、单回合能收敛、且有一个「Claude 自己输出就能自证」的完成条件 → `/goal` 更省事(不用搭 worklog SoT 脚手架)。二者也可叠加(`/goal` 本身就是 session 级 prompt Stop hook),但叠加行为**未实测**,按需再验。

## 机制细节(hidden contract)

- **arm 后继续工作**:实测 `ScheduleWakeup` 返回「nothing more to do this turn」只是**提示**(你可以停),
  不是硬结束;后续 tool call 照常执行。所以标准姿势是「arm 一个心跳 loop → 本回合持续推进 → 回合自然
  结束/断线时唤醒接手」。
- **delaySeconds 被 clamp 到 [60, 3600]**;按「在等什么」选:
  - 纯心跳 / 断线兜底(你本回合一直在做):1200–1800s。
  - 轮询 harness **追踪不到**的外部状态(CI / 远程队列):按那状态变化速度选。
  - **别**为轮询「harness 能追踪的后台工作」设短唤醒——那种完成会自动重新唤起你,轮询是浪费。
- **prompt 形态**:有用户任务驱动 → 传你自己的续跑 prompt(指向 SoT + backlog + 纪律);
  纯自主无 prompt → 传 `<<autonomous-loop-dynamic>>` sentinel。
- **journal / 续跑**:唤醒重放同一 prompt;conversation(含用户新回复)在 context 里,所以决策做完后
  唤醒能看到。但**别依赖对话记忆**,依赖 committed 文件。

## Workflow 纪律(用户确认过的)

- **勤 checkpoint durable 状态**:每个有意义的增量 → 一个 commit + append 进度到 worklog。这样 loop 中途
  掉线,损失只到上一个 commit,唤醒读 worklog 就能接上。
- **arm 的时机**:开始一段较长自主工作时 arm(兼续跑 + 断线韧性);短问答 / 一次性任务不需要。
- **stop 的时机**(两类,都要主动 stop 不要让它空转):
  1. **决策 gate**:碰到「只有用户能定」的岔口(要不要跨过某硬约束 / 某语义取舍 / 优先级),停下问。
  2. **边际递减**:backlog 做完、剩下的都是 speculative/busywork,停;诚实告诉用户「到此为止,再往下没真价值」。
- **re-arm**:用户拍板后,带更新过的 backlog prompt 重新 arm。
- **opt-in only**:只有用户**明确**要 autonomous/loop 才用(它烧 token、且是无人值守授权);别自作主张挂 loop。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| arm 完就结束回合干等唤醒 | 本可立刻做的活拖到下次唤醒 | arm 后本回合继续推进,唤醒作兜底 |
| loop prompt 只说「继续上面的工作」 | 压缩后「上面」没了,唤醒无从恢复 | prompt 自包含 + 指向 committed SoT 文件 |
| 卡在需用户决策的点还让 loop 醒着 | 反复空转 / 可能 fabricate 结果 | 到决策 gate `stop`,问用户,再 re-arm |
| backlog 做完继续找活喂 loop | manufacture busywork,烧 token 无价值 | 到边际递减主动 stop,诚实收尾 |
| loop 中途久不 commit | 掉线丢一大段工作 | 每增量 commit + append worklog |
| 未经用户要求就挂 loop | 擅自无人值守 + 烧 token | opt-in:仅用户明确要才 arm |
| 为轮询 harness 可追踪的后台任务设短唤醒 | 浪费(完成会自动唤起) | 心跳用长间隔;只对外部不可追踪状态短轮询 |

## 跟其它条目的关系

- [`skills/workflow/autonomous-workflow/SKILL.md`](../../skills/workflow/autonomous-workflow/SKILL.md) —— low-touch 工作流(plan gate + handoff 文档 + TDD 安全网)。那条是**工作怎么组织**;本条是**用 ScheduleWakeup 把它跨回合/无人值守跑起来**的 harness 机制 + stop 纪律。两者组合。
- [`techniques/coordination-patterns.md`](../../techniques/coordination-patterns.md) —— 单回合内的 multi-agent 编排 + 「值不值得上」。本条是**时间轴上**的自主续跑,不是并行 fan-out。
- [`guidelines/workflow/daily-and-open-items.md`](../workflow/daily-and-open-items.md) / [`guidelines/workflow/handoffs.md`](../workflow/handoffs.md) —— loop 的 checkpoint 落点(worklog / open-items / daily)。
- [`guidelines/claude-code/hook-conventions.md`](hook-conventions.md) —— 兄弟篇:同属 Claude-Code harness hidden contract。

## 项目实例参考

RetargetStudy(UE Retarget 移植的 GUI 测试工具)一次长 session:用户明确「goal/loop 自主做下去」。原 plan 提的是 `/goal`,最终改用 ScheduleWakeup,是用户要求**扛中途断线 / compaction**——正是上「vs `/goal`」表里 ScheduleWakeup 胜出的那一格。
- arm 一个 25 分钟心跳 loop,prompt 指向 `Docs/handoffs/.../worklog.md`(SoT)+ 显式 backlog(B1–B6)+ 纪律;
  **本回合持续推进不干等唤醒**,每个里程碑一个 commit + append worklog。中途发生过 compaction,靠 worklog
  + commit 无缝恢复(验证了「prompt 指向 durable SoT」的价值)。
- 碰到「要不要跨过『不改 RetargetCore』硬约束去暴露 PBIK」这个**决策 gate**:主动 `stop` loop、问用户;
  用户授权后 re-arm 继续。
- backlog 全做完 + 两条自找加固后判**边际递减**:主动 `stop`,诚实收尾「再往下是 busywork」,把真正待用户的
  (视觉眼校 / UE 数值对拍)列清。
全程无「空转唤醒」、无 fabricate。
