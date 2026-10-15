# Skill 目录：按内容与任务选择

Skill 是包装；下表的“主要内容”描述它提供什么，不决定其权限，也不要求把同组技能一起加载。知识用于解答当前问题，流程用于当前阶段，规范只在其来源和范围内生效。分类方法见 [内容边界](../guidelines/workflow/instruction-content.md)，只在维护或审查指令时读取。

## 知识为主

| 入口 | 提供什么 | 混合内容的边界 |
|---|---|---|
| [multi-plugin-shared-core](architecture/multi-plugin-shared-core/SKILL.md) | 多插件共享实体的架构模式与权衡 | 模式是候选解法，不强制采用全部模式 |
| [maya-tool-interaction](maya/maya-tool-interaction/SKILL.md) | 拖拽、缓存、反馈与撤销机制 | 只应用当前工具需要的模式与契约 |
| [ue-settings-persistence](ue/ue-settings-persistence/SKILL.md) | UE 配置持久化的条件与陷阱 | 写入目标不同，适用的调用与验证也不同 |
| [ue-module-architecture](ue/ue-module-architecture/SKILL.md) | 模块依赖与职责划分 | 框架约束与项目分层选择分别判断 |
| [ue-ml-animation](ue/ue-ml-animation/SKILL.md) | 自定义动画求值与 NNE 契约 | 只读取正在使用的动画或推理路径 |
| [ue-procedural-numerical](ue/ue-procedural-numerical/SKILL.md) | 程序化动画图、批处理与数值计算 | 不把不同子系统的做法合成必跑流程 |

## 流程为主

| 入口 | 何时使用 | 不自动扩大为 |
|---|---|---|
| [autonomous-workflow](workflow/autonomous-workflow/SKILL.md) | 已选择自主推进的长任务 | 每次修改都重新规划、审批和建记录 |
| [supervised-workflow](workflow/supervised-workflow/SKILL.md) | 用户选择逐阶段审阅 | 普通复杂任务默认强制逐阶段审批 |
| [bugfix-tdd](workflow/bugfix-tdd/SKILL.md) | 已授权缺陷修复的复现与验证 | 一般查询、文档更正或额外功能实现 |
| [conversation-walkthrough](workflow/conversation-walkthrough/SKILL.md) | 非平凡改动或明确要求的代码走查 | 全仓重构、重复审批和机械注释清理 |
| [auditing-plan-scope](workflow/auditing-plan-scope/SKILL.md) | 计划增加接口、状态、边界等时审查范围 | 用户已经批准的同一决定再次审批 |
| [context-budget-audit](workflow/context-budget-audit/SKILL.md) | 指令加载成本、触发或约束审计 | 审计材料决定审计者必须遵守它自己 |
| [reverse-maya-closed-nodes](maya/reverse-maya-closed-nodes/SKILL.md) | 闭源节点刻画、诊断或复刻 | 每个窄问题都重跑整个静态到真实资产链 |
| [ue-custom-graph-editor](ue/ue-custom-graph-editor/SKILL.md) | 新建或维护自定义 UE 图编辑器 | 维护单一行为也从第一步重新建设 |
| [official-mcp-usage](ue/official-mcp-usage/SKILL.md) | UE 官方 MCP 的配置、操作和诊断 | 自动切换工具后端或修改共享服务 |
| [unrealmcp-usage](ue/unrealmcp-usage/SKILL.md) | UnrealMCP fork 的操作与接入 | 未授权扩展工具或迁移后端 |
| [multi-session-coordination](collaboration/multi-session-coordination/SKILL.md) | 带协调 hooks 的 Claude Code 同仓会话 | Codex 会话、无 hooks 的环境或擅自收走他人改动 |
| [role-lane-coordination](collaboration/role-lane-coordination/SKILL.md) | 多个持久 lane 的分工与交接 | 每个临时子任务都新增持久 lane |

## 规范应用为主

| 入口 | 提供什么 | 生效范围 |
|---|---|---|
| [doc-writing-style](workflow/doc-writing-style/SKILL.md) | 项目文体的应用与图示参考 | 交付文档；形式服务内容，不强制统一仪式 |
| [tdd-with-fixtures](workflow/tdd-with-fixtures/SKILL.md) | 行为验证与可复现人工用例 | 新行为或缺陷验证；文档、机械修改和已有覆盖的重构采用相应验证 |
| [ue-reference-engine-source](ue/ue-reference-engine-source/SKILL.md) | 源码查证要求与参考索引 | 不熟悉、变化或有争议的 UE 契约；有效既有证据可复用 |

## 维护与安装

本次分层、测量口径、待审项与 Techne-Loom 适用边界见 [2026-10-13 审计记录](../docs/audits/2026-10-13-skill-content-separation.md)，仅复查本次治理时读取。

`skills/<category>/<name>/` 是本仓源码，`SKILL.md` 保留名称、触发范围、必要边界和最短阅读路线；大段知识、模板或阶段细节放同目录附件。附件只按当前需要读取，不能在入口要求全部读完。

保留可移植的 `name`、`description` frontmatter，不为三分类新增自造的自动触发字段。新增技能在此注册，根 `AGENTS.md` 只保留目录入口。外部插件和 Superpowers 由各自来源维护，不属于本目录。

[`scripts/sync-skills.ps1`](../scripts/sync-skills.ps1) 将整个技能目录扁平同步到 Claude 的 `~/.claude/skills/<name>/` 和 Codex 的 `~/.agents/skills/<name>/`。同目录附件随包复制；规范库路径仍从消费项目接入指针解析，不把安装目录当作规范库根。
