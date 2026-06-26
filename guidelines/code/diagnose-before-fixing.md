# 先取证再修:调试不靠猜

## 核心规则

遇到 bug / 测试失败 / 非预期行为时,**不要凭假设直接改代码**。先用**证据确认根因**,再动手修。

"我觉得是 X → 直接改 X" 是反 pattern。改一个未经证实的假设,常常:**修错地方** / **掩盖症状**(症状偶然消失但根因还在)/ **引入新问题** / **烧光 failure budget**(见 [`../workflow/agent-lifecycle.md`](../workflow/agent-lifecycle.md) 失败升级)。

这条是 [`validation.md`](validation.md) 的**前置对称面**:validation 管"改完怎么验证",本条管"**改之前怎么确认根因**"。

## 取证手段(动手修之前)

- **加诊断日志**:在关键决策点 dump 状态——变量值、分支走向、**是否进入某代码路径**、对象/容器计数、指针有效性。
- **dump 数据结构**:打印 size、关键字段、id 映射。
- **断点 / 调试器**:单步、看调用栈、看实际值。
- **最小复现**:隔离到最小场景,排除干扰变量。
- **bisect**:二分(git bisect / 逐段注释)定位引入点。
- **读框架源码**:行为诡异且涉及外部框架时,读那一层源码确认 hidden contract(配合 reference-engine-source 类 skill)。

**关键判据**:你加的 log/dump 应该能**区分相互竞争的假设**——让"是 A 还是 B"有明确答案,而不只是"看起来对"。设计取证手段时先问:"这条证据出现/不出现,分别证明了什么?"

## 确认后再修

- 证据收敛到**单一确认根因**后才写 fix。
- fix 后**再取证**,确认确实是那个根因被解决(不是症状被偶然掩盖)。
- 诊断日志在确认 fix 生效**之前不要删**(见 [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) "Diagnostic Log Discipline")。

## Agent 自己观察不到时,让 user 协助取证

很多证据 agent 直接拿不到(GUI / 编辑器交互、运行期画面、硬件、远程环境)。这时**仍然不要猜**,而是把取证**外包给 user**:

1. 给 user **精准的 instrumentation**:具体加哪几条 log / dump 什么 / 跑哪几步操作。
2. 给一张 **"观察 → 含义" 解读表**,让 user 回报的证据能直接定位到环节。
3. user 回报证据后**再下结论 + 修**。

解读表示例(把"可能的观察"预先映射到"问题在哪一环"):

| 观察(log/现象) | 说明 | 下一步 |
|---|---|---|
| `X = NULL`(初始化处) | 初始化时序问题 | 改时序 / 延迟初始化 |
| 回调日志从不出现 | 回调没注册 / 没触发 | 查注册路径 |
| `count = 0` | 数据没填进来 | 查数据来源 |
| `count = N` 但无可见效果 | 下游(应用/绘制)问题 | 查下游 |

这比"你再试试 / 再看看"高效得多——一次往返就能定位,不浪费 user 时间。

## Anti-Patterns

| 反 pattern | 为什么错 |
|---|---|
| "八成是 X,直接改 X" | 假设未证实;根因可能在别处,改了白改还可能引入新问题 |
| 连续试多个 speculative fix | 每个都没取证;改对了不知为何,改错了 budget 烧光(对应 agent-lifecycle 失败升级"换 layer 不是换 API"——但换之前要先取证知道卡在哪层) |
| 过早删诊断日志 | fix 没确认就删,错了要重加 |
| 让 user 反复"再试试"却不给精准 instrumentation | 浪费 user 时间;拿不到能定位的证据 |
| 把"代码看着对"当证据 | reading ≠ evidence(见 validation.md "Adversarial Mindset") |

## 跟其它条目的关系

- [`validation.md`](validation.md) "Adversarial Mindset" —— 改完怎么验证(本条的对称后置面)。
- [`../workflow/agent-lifecycle.md`](../workflow/agent-lifecycle.md) "Common Failure Modes" / "Failure Escalation" —— "probably fine" / "code looks correct" 是同源自欺;换 approach/layer 的前提是先取证知道卡在哪层。
- [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) "Diagnostic Log Discipline" —— 诊断日志保留到确认 fix。
- skill `superpowers:systematic-debugging` —— debug 方法论(本条是其 declarative、始终在线的精炼版);skill `bugfix-tdd` —— 取证定位**之后**的红→绿修复流程(写复现测试 → 改 → 验)。

## 项目实例

UE curvenet 插件 M3:viewport 控制点手柄不显示。Agent 第一反应是"八成是 `GUnrealEd` 在 `StartupModule` 时为 null 导致 component visualizer 没注册",准备直接改成 `OnPostEngineInit` 延迟注册。user 叫停:**先加 log 取证**——StartupModule 时 GUnrealEd 是否 valid / 注册是否跑 / `DrawVisualization` 是否被调 / 控制点数——确认到底卡在**注册、调用、数据、还是绘制**哪一环,再修。避免了对未证实假设的盲改(那个假设只是 4 个候选环节之一)。
