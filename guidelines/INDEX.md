# 按任务查找规范与领域知识

只读取当前行为涉及的条目。这里是导航，不是需要依次执行的清单；历史案例和领域契约保留在原文件中。

页面的类别（知识 / 规范 / 经验 / 流程）标在各自 frontmatter 的 `class` 里，按类别的目录由 `python scripts/kb/kb.py index` 生成到 [CATALOG.md](CATALOG.md)；经验类页面的事故记录在 [evidence/](../evidence/README.md)，执行任务时不必读。

## 通用规范

| 当前工作 | 资料 |
|---|---|
| 维护指令库、区分知识/流程/规范、更新证据与旧结论 | [内容边界](workflow/instruction-content.md)、[知识促升与维护](workflow/knowledge-promotion.md)、[参考资料](../references/README.md) |
| 写或改 skill、`AGENTS.md`、索引条目等给 agent 读的文档 | [给 agent 写文档](workflow/writing-for-agents.md) |
| 本地提交、推送或版本操作 | [提交约定](workflow/commits.md)、[授权与生命周期](workflow/agent-lifecycle.md) |
| 继续长任务、协调优先级、处理信息不足、重复失败或范围变化 | [授权与生命周期](workflow/agent-lifecycle.md)、[协调者的工作优先级](workflow/agent-lifecycle.md#协调者的工作优先级)、[交接](workflow/handoffs.md) |
| 新增或修改文档 | [文档归属与同步](workflow/documentation.md)、[行文](writing/prose-and-register.md)、[私人记录](collaboration/private-docs-policy.md) |
| 代码审查与修正 | [审查规范](workflow/code-review.md)、[任务范围](code/constraints.md) |
| 需求有影响结果的歧义 | [澄清边界](code/clarify-before-implementing.md)、[未写出的前提](code/premises-not-in-the-text.md) |
| 设计或实现代码 | [改动约束](code/constraints.md)、[先找复用](code/reuse-before-implementing.md)、[函数与注释](code/function-clarity.md) |
| 排查缺陷 | [诊断后再修复](code/diagnose-before-fixing.md)、[报告限制与空结果](code/reporting-limits-and-null-results.md) |
| 验证实现或设计测试 | [验证](code/validation.md)、[测试目的](code/test-purpose.md)、[GUI 验证边界](code/gui-visual-machine-gating.md) |
| 分析复杂度和覆盖率 | [指标的适用条件](code/complexity-coverage-metrics.md) |
| 同一数据同时有编辑与运行时表示 | [双层数据归属](code/dual-layer-data-ownership.md) |
| 通过 shell 生成代码或文档 | [生成文件](code/generating-code-through-shell.md)、下方 Windows 写入条目 |
| 跨 agent 或跨会话工作 | [规范库接入](collaboration/multi-agent.md)、[私人记录](collaboration/private-docs-policy.md) |
| 新建或重切持久 lane | [lane 拓扑](collaboration/lane-topology-design.md)、[Lane Router](../techniques/lane-router.md) |

## 领域知识与条件约束

| 触发范围 | 资料入口 |
|---|---|
| C++、DLL、编译链、ABI、性能或 native crash | [C++ 索引](cpp/INDEX.md) |
| UE 开发与编辑器自动化 | [UE 索引](ue/INDEX.md) |
| Maya 插件、操作工具与绘制 | [Maya 索引](maya/INDEX.md) |
| 向既有 rig 写 FBX 动画 | [FBX 写入](fbx/write-animation-to-existing-rig.md) |
| 采样读取 FBX 动画 | [FBX 读取](fbx/read-animation-from-fbx.md) |
| P4 编码与文件类型 | [P4 字符集](p4/charset-pitfalls.md) |
| Windows 上用 PowerShell 跑 native 命令或写文件 | [PowerShell 契约](ci-windows/powershell-native-command-pitfalls.md)；写文件重点看 Pitfall 4/5 |
| Windows 上用 Python 修改既有文件 | [行尾保留](ci-windows/python-write-text-line-endings.md) |
| Windows 上使用 POSIX 编辑工具 | [文件替换语义](ci-windows/posix-tools-on-windows.md) |
| Windows GitLab runner | [服务与 shell](ci-windows/gitlab-runner-service-and-powershell-pitfalls.md) |
| Claude Code hook、subagent 或自动循环 | [hooks](claude-code/hook-conventions.md)、[subagent](claude-code/subagent-contracts.md)、[循环](claude-code/autonomous-loop-scheduling.md)；Codex 不自动套用 |

领域文件中的 API 前提仍在相应调用路径上生效；按需加载不等于把必要前提降为可选建议。
