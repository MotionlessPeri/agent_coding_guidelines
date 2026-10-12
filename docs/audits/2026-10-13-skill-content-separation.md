# 2026-10-13：Skill 内容分层与阶段加载

本次工作承接 [启动上下文与约束审计](2026-10-13-context-and-instruction-audit.md)。目标是区分知识、流程和规范，减少无关加载与重复审批，同时保留真实验证、授权和领域前提。审查期间把 skill 文本作为数据，不让被审查规则决定审计方法。

## 已落实

- [内容边界](../../guidelines/workflow/instruction-content.md)定义三类内容，Skill 作为包装；不强制所有文件套三个标题。
- 根 AGENTS 改成简短边界与导航，原 28 个直接导入改为任务索引。Claude 不再经本入口自动展开这些文件；Codex 仍须显式读取匹配条目。领域文件没有整体迁移。
- [技能索引](../../skills/INDEX.md)覆盖本仓 21 包：6 个以知识为主、12 个以流程为主、3 个以规范应用为主。分类不提高权限，也不证明所有领域事实已重新核验。
- 六个通用技能分离入口、当前阶段流程和参考附件：autonomous-workflow、supervised-workflow、bugfix-tdd、conversation-walkthrough、doc-writing-style、tdd-with-fixtures。
- 删除自动串联其他技能、重复审批、固定文档图示、固定收尾表格及不按影响面选择的构建要求。同步调整 canonical 验证、函数可读性和复用规则，避免入口与正文冲突。
- 缺陷修复仍须修复前失败与修复后通过的可追溯证据；可复用有效记录。用户明确选择的监督检查点、独立评审、人工判断和项目必需检查均保留。
- 文字检查点与机械门禁分开；字段值等于 `approved` 不足以证明真实用户批准。

## 静态成本

以下采用 UTF-8 字节数、LF 归一化，基准为本次开始的 `bb6f088`，不是对实际 token 或模型表现的估算。

| 对象 | 修改前 | 修改后 | 说明 |
|---|---:|---:|---|
| 根 AGENTS | 22,467 | 5,292 | 修改后工作树另保留原有未提交的两段工具导航 |
| 六个 SKILL 入口合计 | 99,352 | 16,925 | 减少约 83%；实际任务通常只会选择其中部分 |
| 根入口直接 `@path` | 28 | 0 | 详细约束仍由任务索引发现 |

阶段附件仍消耗上下文，故入口缩短不等于同幅度减少任务总成本。其他插件的发现目录仍由宿主注入；这次没有禁用插件、删除 Superpowers 或移除 Orca 的重复发现入口。文件更新不会从正在进行的对话里撤回旧内容。

本地 `codex debug prompt-input audit` 确认新根入口完整出现；这是本地 CLI 渲染结果，不代表当前宿主已经更新其缓存。先前测到的宿主 70 项 skill 目录与正文加载不是同一个成本口径。

## 尚未裁定或修改的候选

下面是后续按实际任务验证的审查发现，不是已证实某领域技术事实过时：

| 包 | 待审边界 |
|---|---|
| ue-reference-engine-source | 每个 API 都 grep、找不到参考就重新设计过宽；应按陌生、变化或可疑契约定位 |
| ue-custom-graph-editor | 新建七步流程与维护单一行为应区别 |
| official-mcp-usage | 区分可自行恢复的错误与确实需要用户刷新连接的情况 |
| unrealmcp-usage | 当前任务的工具缺口不必直接扩展工具仓库 |
| reverse-maya-closed-nodes | 窄问题不一定需要从反汇编到真实资产的完整证据链 |
| multi-session-coordination | commit/stash 残留前必须确认归属；不能处置其他会话工作 |
| context-budget-audit | 历史计数与当前宿主加载机制应分开；本次保留既有未提交修改 |

## Techne-Loom 的适用范围

[文章](https://github.com/waynebaby/Techne-Loom/blob/main/docs/zh-cn/articles/skill-unchanged-rules-gated.md)说明按节点提供输入并由运行时检查部分继续条件，没有提供模型效果或 token 成本的对照测量。三分类是本仓组织决定，不归功于文章。

该项目采用 [MIT 许可](https://github.com/waynebaby/Techne-Loom/blob/main/LICENSE)，提供 Windows 自包含包，CLI 可独立于 MCP 使用。适合已明确阶段、需要等待及中断恢复的重复流程；不会自动整理本仓内容，也不是现成的 Codex 或 Lane Router 替代品。[包索引](https://github.com/waynebaby/Techne-Loom/blob/main/packages.released.md)

SO 在模型、工具、子代理或用户步骤处等待外部调用者处理再 resume；真实工具结果、批准来源和业务判断仍由外层负责。原生 collaboration 与它组合的路径需要试验；本次没有部署。[职责边界](https://github.com/waynebaby/Techne-Loom/blob/main/docs/en/guides/so-guide-reference-behavior.md)

建议如需试点，只取一个只读流程的副本，验证正常完成、缺证据阻断、中断恢复和重复结果。先用独立目录与 CLI，确认收益后再决定接入。官方整套治理另有模板、谓词、合同、审计产物与汇报要求，不宜直接导入。[治理说明](https://github.com/waynebaby/Techne-Loom/blob/main/docs/en/guides/so-guide-reference-governance.md)

## 验证边界

静态场景审查覆盖文档小改、已授权任务恢复、缺陷修复和用户选择监督模式；发现并修复了实施入口对缺陷红测要求弱化的问题。附件链接、元数据、安装清单和内容 hash 用机械检查验证。没有运行模型 A/B 实验，不能把这些检查说成行为效果已证明。

现有同步测试 11/11、平台契约测试 11/11 通过，最终暂存的 31 份 Markdown 中 140 个本地链接无缺失，暂存差异格式检查通过。六个包已定向安装到本机 Codex 与 Claude；12 个目标包与源包清单及 SHA-256 一致，未选中包未变化。旧版备份在仓库外的 `D:\my_projects\_agent_private\agent_coding_guidelines\skill-layering-20261013-9c5301ab\backup`。没有同步仓库内原有未提交的其他技能修改，也没有安装 Techne-Loom。
