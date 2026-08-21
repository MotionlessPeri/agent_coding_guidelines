# 代码复杂度 / 覆盖率指标：作 review triage，别当 KPI

## 核心规则

两条：

1. 圈复杂度（CC）/ CRAP 这类指标只能当**发现线索**——机械选出"最该深读 / 最该拆 / 最该补测"的少数函数，把有限的人工 review 定向到高风险处。**不能当考核目标（KPI）**：一旦变成要优化的数字，就会被 gaming，而复杂度只是搬家、不会消失。
2. CRAP（`= CC²·(1−cov)³ + CC`）作 review triage 时，**它相对纯 CC 的全部增量价值都在覆盖率那一项，且这项必须是真实测量出来的**。拿不到真覆盖率的层（假设 `cov=0`、或设计上就不做单测），CRAP 立即退化成一个穿着 CRAP 外衣的 CC 排序——谁复杂谁靠前——并且会误导。

这条管"指标怎么理解、怎么用来定向 review"；[`test-purpose.md`](test-purpose.md) 管"选出补测目标后，到底该测哪条行为"；[`validation.md`](validation.md) / [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) 管"给定要测 X，怎么测得可信"。四条正交互补。

## 一、CC 的三个盲区（为什么不能当 KPI）

CC 数的是一个函数里**独立执行路径（判定点）的条数**——只看代码结构，跟测没测无关。三个盲区，都可实测复现：

| 盲区 | 现象 | 含义 |
|---|---|---|
| **CC 与语法无关** | 把嵌套 `if` 链改成等价 `switch-case`，CC **不变**（N 路 switch = N 路 if）。实测两个等价函数 CC 相同 | CC 数路径数，不数你用什么写法 |
| **复杂度守恒，可搬不可消** | 把分支改成 dispatch table / 拆多个函数，主函数 CC 骤降，但各 handler 各自带走 CC，**总量守恒甚至略增**（多了间接层） | CC 是 per-function 局部指标；降的是"某函数的局部 CC"，不是系统总复杂度 |
| **CC 不惩罚嵌套深度** | 3 层深嵌套 `if` 和 3 个扁平并列 `if`，判定点数相同 → CC 相同，但前者认知负担明显更重 | 管嵌套认知负担的是 cognitive complexity / max nesting depth，不是 CC |

**推论（Goodhart 定律）**：指标一旦变成目标就不再是好指标。为了把某函数 CC 数字做低，可以用 switch / 硬拆 / 查表——数字降了，复杂度只是搬进了指标照不到的地方（数据表、别的函数、更深的调用链）。

> **外部佐证**（deepseek-harness 0.1.0-rc.5，2026-08-17 源码核实）：连把 per-file 100% 覆盖当 CI 硬 gate 的项目，官方立场也与本条同向——"Line coverage is necessary, never sufficient — it proves lines ran, not that the feature works as shipped"，未覆盖行首先当「该删的死代码」而非「该补的测试」；且自认 "100%-coverage pressure can produce assertion-free tests — mutation testing is the planned counterweight"（其 mutation 长期停在 proposed，缺口只靠 review 兜）。硬 gate 的真实形态 =「100% 减一张带理由的豁免表」，行为判官放在 snapshot / e2e / smoke 层。

**什么时候降 CC 是真收益**：判据不是"数字降了没"，而是**拆出来的每一块能不能独立理解、独立测试**。真解耦（各块是自洽语义单元、可单测）→ 真收益；机械换语法 / 硬拆但各块仍紧耦合、必须凑一起读 → 数字降了是自欺。

## 二、CRAP 作 review triage 的正确用法

CRAP 想挑出"**又复杂、又没测**"的函数（最容易改出事：复杂=易改错，没测=改错没人拦）。公式拆解：`CC²` 平方惩罚复杂度；`(1−cov)³` 立方放大"未覆盖比例"，起闸门作用——`cov=100%` → 第一项归零、CRAP=CC（复杂但全测，压到只剩基础复杂度）；`cov=0%` → 第一项满额（复杂又没测，拉满）。

**分层用 + 一个硬前提：**

| 用途 | 该用什么 |
|---|---|
| 选**深读 / 拆**目标 | 用 **CC / 文件大小**即可（CRAP 在此 ≈ CC，因为大函数往往覆盖乘子不做功） |
| 选**补测**目标 | 用 **CRAP**，前提是该层有可量测的真实覆盖率 |
| **不可替代的贡献** | 在"已经测得不错的复杂代码"里，机械揪出那几个"真没测"的——这是 CC 单独做不到的 |

**硬前提：覆盖率必须真测。** 覆盖率若是"假设值"或该层设计上就不做单测（如 GUI / 渲染层，见 [`gui-visual-machine-gating.md`](gui-visual-machine-gating.md)），CRAP = CC 排序 + 误导，别在这种层上用它。实际怎么测 per-function 覆盖率、怎么算 CRAP，见 technique [`cpp-coverage-and-crap-measurement`](../../techniques/cpp-coverage-and-crap-measurement.md)（C++ 场景）。

## Anti-Patterns

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| 把 CC / CRAP 当团队 KPI | 会被 switch / 硬拆 / 查表刷低，复杂度只是搬家 | 只当发现线索，定向 review |
| 为降 CC 机械换 switch / 硬拆函数 | 数字降了、各块仍紧耦合 → 认知负担没减 | 拆到每块可独立理解+独立测试才算数 |
| 用 CC 衡量"读起来多累" | CC 不惩罚嵌套深度 | 深嵌套用 cognitive complexity / nesting depth |
| 在没有真覆盖率的层跑 CRAP | 退化成 CC 排序且误导（复杂但已测的会被误报） | 无真覆盖率的层不上 CRAP；只用 CC 选深读目标 |
| 拿 CRAP 单一排名当权威清单 | 渲染层等"故意不单测"的高分会淹没真缺陷 | 按 population 分层看，真覆盖率层才信覆盖项 |

## 相关 Guidelines / Techniques

- [`test-purpose.md`](test-purpose.md) —— CRAP 选出补测目标后，测哪条行为（钉行为不测结构）
- [`validation.md`](validation.md) / [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) —— 覆盖率是必要非充分；check 的可信性（MFIC 四要素）
- [`function-clarity.md`](function-clarity.md) —— CC 高 → 拆 sub-function 的行数阈值（本条的"拆"落到具体阈值）
- [`gui-visual-machine-gating.md`](gui-visual-machine-gating.md) —— 渲染 / GUI 层机器 gate 压纯函数、画面交人工；那层 `cov=0` 是设计选择，CRAP 在那层不适用
- [`../../techniques/cpp-coverage-and-crap-measurement.md`](../../techniques/cpp-coverage-and-crap-measurement.md) —— 实际怎么测 C++ per-function 覆盖率 / 算 CRAP（含工具链坑）

## 项目实例参考

某跨图形 API 光追渲染器（C++，三层 RenderCore/Material/GUI，各有 oracle 测试）上一轮评测（**validated once**）：

- **排序反转（覆盖项做功的铁证）**：Material 层 `evalSubgraph`（CC31）在"假设 cov=0"下 CRAP=992（全项目头号），实测 91% 覆盖后真实 CRAP 只有 **31.6**；与此同时真没测的 `removeNode`（CC11，**0%**，CRAP 132）从被淹没升到该层榜首。排序从"evalSubgraph 992 > removeNode 132"（纯 CC）反转成"removeNode 132 > evalSubgraph 31.6"（真风险）——证明不实测覆盖率，CRAP 就是 CC 排序。
- **补测让高 CRAP 塌陷**：`intersectTriangle`（CC8，0%，CRAP72，纯结构阅读会漏的标准算法盲区）补测跑红→绿后覆盖 100%、CRAP→8。
- **CC 盲区实测**：等价的 `if`-链版本与 `switch`-版本 CC 都是 14；改 dispatch table 后主函数 CC 14→3，但 5 个 handler 总量 16（守恒略增）。
