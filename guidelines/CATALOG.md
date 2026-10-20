# 页面目录（生成文件，勿手改）

由 `python scripts/kb/kb.py index` 从各页面的 frontmatter 生成。只列出已标 `class` 的页面；未标的页面仍按 [INDEX.md](INDEX.md) 按任务查。

## experience

| 页面 | 作用域 | 触发词 | 诞生 | 最近复测 | 事故数 |
|---|---|---|---|---|---|
| [guidelines/code/diagnose-before-fixing.md](code/diagnose-before-fixing.md) | universal | bug, 修复, 根因, 八成是, 直接改, 校验器告警, 框架报警, 打不开, 卡住, 复现不了, 诊断日志, 取证 | 2026-06，写下时的模型未记录 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：D1 pass、D2 pass、D3 fail；见 docs/evaluations/experience-retest-2026-10-15.md | 5 |
| [guidelines/code/generating-code-through-shell.md](code/generating-code-through-shell.md) | universal | heredoc, 反斜杠, 转义, sed, 生成代码, 生成文件, 落盘, py_compile, 代码块, 静默失败, 卡死 | 2026-08，写下时的模型未记录 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：G1 fail、G2 partial；见 docs/evaluations/experience-retest-2026-10-15.md | 4 |
| [guidelines/code/gui-visual-machine-gating.md](code/gui-visual-machine-gating.md) | gui-or-rendering-tools | GUI, 视口, 画面, 截图, 离屏, offscreen, 像素, 冒烟, 渲染层, Qt, pyqtgraph, ImGui, 画面对不对 | 2026-07，写下时的模型未记录 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：V1 pass、V2 pass；见 docs/evaluations/experience-retest-2026-10-15.md | 3 |
| [guidelines/code/premises-not-in-the-text.md](code/premises-not-in-the-text.md) | universal | 前提, HEAD, 当前树, 本仓的配置, 行号, 最近, 至今, 刚才, 唯一, 一律, 全部, 从不, 永久, 配方, 实测, 压缩, 改写, 宣发 | 2026-08，写下时的模型未记录 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：P1 pass、P2 pass；见 docs/evaluations/experience-retest-2026-10-15.md | 8 |
| [guidelines/code/reporting-limits-and-null-results.md](code/reporting-limits-and-null-results.md) | universal | 报结论, 做不到, 不支持, 能力边界, 框架不支持, 没变, 没接上, 不起作用, 零命中, 找不到, 不存在, 没发生, 搜了没有, ABSENT, 这个数, 搬数字, 聚合统计量, p95, 均值 | 2026-08，写下时的模型未记录 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：R1 pass、R2 partial、R3 pass、R4 pass、R5 pass；见 docs/evaluations/experience-retest-2026-10-15.md | 24 |
| [guidelines/code/reuse-before-implementing.md](code/reuse-before-implementing.md) | universal | 复用, 已有实现, 抽 helper, 重复代码, copy-paste, 新建文件, 新建类, 参考实现, samples, devkit, SDK, 过早抽象 | 2026-05，写下时的模型未记录；2026-10-13 按判断力改写 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：U1 pass、U2 pass；见 docs/evaluations/experience-retest-2026-10-15.md | 6 |
| [guidelines/collaboration/lane-topology-design.md](collaboration/lane-topology-design.md) | multi-lane-projects | lane, 拓扑, 切 lane, 重切, 开新 lane, 接缝, role description, 裁撤 lane, 并行派活, 多会话 | 2026-09，写下时的模型未记录 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：L1 pass、L2 partial；见 docs/evaluations/experience-retest-2026-10-15.md | 10 |
| [techniques/measurement-four-questions.md](../techniques/measurement-four-questions.md) | universal | 读数, 测量, 对照组, 分母, 样本, 探针, 阈值, 判据, 真值, A/B, 命中数, 扫描结论 | 2026-08，写下时的模型未记录 | 2026-10-15 claude-fable-5-1，claude -p 全新会话、无工具：Q1 fail、Q2 fail；见 docs/evaluations/experience-retest-2026-10-15.md | 9 |

## knowledge

| 页面 | 作用域 | 触发词 | 诞生 | 最近复测 | 事故数 |
|---|---|---|---|---|---|
| [guidelines/code/complexity-coverage-metrics.md](code/complexity-coverage-metrics.md) | universal |  |  | 未复测 | 0 |
| [guidelines/code/dual-layer-data-ownership.md](code/dual-layer-data-ownership.md) | universal |  |  | 未复测 | 0 |
| [guidelines/workflow/writing-for-agents.md](workflow/writing-for-agents.md) | universal |  |  | 未复测 | 0 |
| [references/software-engineering/business-command-reliability.md](../references/software-engineering/business-command-reliability.md) | business-software |  |  | 未复测 | 0 |

## norm

| 页面 | 作用域 | 触发词 | 诞生 | 最近复测 | 事故数 |
|---|---|---|---|---|---|
| [guidelines/code/clarify-before-implementing.md](code/clarify-before-implementing.md) | universal |  |  | 未复测 | 0 |
| [guidelines/code/constraints.md](code/constraints.md) | universal |  |  | 未复测 | 0 |
| [guidelines/code/function-clarity.md](code/function-clarity.md) | universal |  |  | 未复测 | 0 |
| [guidelines/code/test-purpose.md](code/test-purpose.md) | universal |  |  | 未复测 | 0 |
| [guidelines/code/validation.md](code/validation.md) | universal |  |  | 未复测 | 0 |
| [guidelines/collaboration/multi-agent.md](collaboration/multi-agent.md) | universal |  |  | 未复测 | 0 |
| [guidelines/collaboration/private-docs-policy.md](collaboration/private-docs-policy.md) | universal |  |  | 未复测 | 0 |
| [guidelines/workflow/agent-lifecycle.md](workflow/agent-lifecycle.md) | universal |  |  | 未复测 | 0 |
| [guidelines/workflow/commits.md](workflow/commits.md) | universal |  |  | 未复测 | 0 |
| [guidelines/workflow/documentation.md](workflow/documentation.md) | universal |  |  | 未复测 | 0 |
| [guidelines/workflow/handoffs.md](workflow/handoffs.md) | universal |  |  | 未复测 | 0 |
| [guidelines/workflow/instruction-content.md](workflow/instruction-content.md) | universal |  |  | 未复测 | 0 |
| [guidelines/workflow/knowledge-promotion.md](workflow/knowledge-promotion.md) | universal |  |  | 未复测 | 0 |
| [guidelines/writing/prose-and-register.md](writing/prose-and-register.md) | universal |  |  | 未复测 | 0 |

## procedure

| 页面 | 作用域 | 触发词 | 诞生 | 最近复测 | 事故数 |
|---|---|---|---|---|---|
| [guidelines/workflow/code-review.md](workflow/code-review.md) | universal |  |  | 未复测 | 0 |
| [techniques/adversarial-verification.md](../techniques/adversarial-verification.md) | universal |  |  | 未复测 | 0 |
| [techniques/blackbox-api-characterization.md](../techniques/blackbox-api-characterization.md) | closed-source-apis |  |  | 未复测 | 0 |
| [techniques/ci-deploy-to-p4.md](../techniques/ci-deploy-to-p4.md) | p4-windows-ci |  |  | 未复测 | 0 |
| [techniques/claude-code-autonomous-permissions.md](../techniques/claude-code-autonomous-permissions.md) | claude-code |  |  | 未复测 | 0 |
| [techniques/coordination-patterns.md](../techniques/coordination-patterns.md) | universal |  |  | 未复测 | 0 |
| [techniques/cpp-coverage-and-crap-measurement.md](../techniques/cpp-coverage-and-crap-measurement.md) | cpp |  |  | 未复测 | 0 |
| [techniques/debugger-scripting.md](../techniques/debugger-scripting.md) | universal |  |  | 未复测 | 0 |
| [techniques/enumerate-then-adjudicate.md](../techniques/enumerate-then-adjudicate.md) | universal |  |  | 未复测 | 0 |
| [techniques/fact-forcing-gate.md](../techniques/fact-forcing-gate.md) | universal |  |  | 未复测 | 0 |
| [techniques/lane-router.md](../techniques/lane-router.md) | lane-router |  |  | 未复测 | 0 |
| [techniques/model-worker-mcp.md](../techniques/model-worker-mcp.md) | model-worker-mcp |  |  | 未复测 | 0 |
| [techniques/profiling-workflow.md](../techniques/profiling-workflow.md) | universal |  |  | 未复测 | 0 |
| [techniques/worker-instructions.md](../techniques/worker-instructions.md) | universal |  |  | 未复测 | 0 |
