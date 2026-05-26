# UE Guidelines 索引

UE 是当前 meta-corpus 最重的子目录（约 950 行 / 6 份 guidelines + 1 份配套
technique，另有 4 份内容已 promote 到 skill：`skills/ue-module-architecture/` 2 份
+ `skills/ue-reference-engine-source/` + `skills/ue-settings-persistence/`），
集中存放 Unreal Engine framework 的 hidden contracts 和 idiom。

**非 UE 项目可以整段 skip 本目录** —— 通用编程 / 工程组织规则在
`guidelines/code/` / `guidelines/workflow/` / `guidelines/collaboration/`。

## 按使用场景分类

### Prep work（开工前必看）

> 已 promote 到 skill：[`skills/ue-reference-engine-source/SKILL.md`](../../skills/ue-reference-engine-source/SKILL.md)（lazy-load，不再 eager-import）

| Skill 内容 | 解决的问题 |
|---|---|
| [`reference-engine-source.md`](../../skills/ue-reference-engine-source/reference-engine-source.md) | UE 功能（特别是 UI / Editor）开工前先找最相近的 engine source / official sample / 第三方 plugin reference impl；按 22 个 UE 子系统给 reference 清单 |

> 配对的项目内 prep work：[`../code/reuse-before-implementing.md`](../code/reuse-before-implementing.md)（survey 项目内已有 similar code）。两条 prep work 都属于"动手前先 survey"的对称概念。

### Graph Editor 子领域

| Guideline | 解决的问题 |
|---|---|
| [`graph-editor-constraints.md`](graph-editor-constraints.md) | NodeGuid 初始化 / Pin SetOwner / Custom SGraphNode Factory 注册 / Pin 自动连线 / Dynamic Pin Reconstruction / Reroute (Knot) 节点 4 件套 / Cold Rebuild over Live Coding / `RF_Transactional` / Undo Refresh / Dual-Layer Data 模型 / Copy-Paste DuplicateObject |
| [`graph-data-ownership.md`](graph-data-ownership.md) | UEdGraph pin 是连接 SoT / runtime 数据是 derived / Compile Full Flush > incremental sync / Anti-Patterns（incremental sync / edge properties on runtime side） |

### Editor / Runtime 架构

> 已 promote 到 skill：[`skills/ue-module-architecture/SKILL.md`](../../skills/ue-module-architecture/SKILL.md)（lazy-load，不再 eager-import）

| Skill 内容 | 解决的问题 |
|---|---|
| [`editor-runtime-separation.md`](../../skills/ue-module-architecture/editor-runtime-separation.md) | 三层模型（Runtime Ops / Editor Actions / UI）/ Undo Support（基础 + 嵌套 transaction）/ Editor Actions 自动化生成（ExecEditorOp 模板 + 可选 Python codegen） |
| [`runtime-module-no-editor-dep.md`](../../skills/ue-module-architecture/runtime-module-no-editor-dep.md) | 跨模块依赖方向硬约束：Runtime `*.Build.cs` 永远不能依赖 Editor module（含 conditional `if (Target.bBuildEditor)`）/ `WITH_EDITOR` 不能救你 / 常见诱因 + 正确解法（delegate / 把 test 移到 Editor module）/ build.cs review checklist |

### Asset Lifecycle

| Guideline | 解决的问题 |
|---|---|
| [`asset-definition-can-duplicate-limit.md`](asset-definition-can-duplicate-limit.md) | `UAssetDefinition::CanDuplicate` 只拦 Content Browser 命令；Copy+Paste / Migrate / 程序化 DuplicateObject 全部绕过；必须双层防御（CanDuplicate + PostDuplicate 兜底） |
| [`blueprint-auto-override-api.md`](blueprint-auto-override-api.md) | 程序化创建 Blueprint Override 时 `AddFunctionGraph<UClass*>` vs `<UFunction*>` 模板参数选择；`bIsUserCreated` 跟模板参数的正交语义 |

### Localization / Settings 持久化

> Settings 持久化已 promote 到 skill：[`skills/ue-settings-persistence/SKILL.md`](../../skills/ue-settings-persistence/SKILL.md)（lazy-load，不再 eager-import）

| Guideline / Skill 内容 | 解决的问题 |
|---|---|
| [`localization-pitfalls.md`](localization-pitfalls.md) | UE Localization API 6 条 trap：FromStringTable.ToString culture 漂 / Content/Localization 硬编码 exclude / PreBeginPIE 不能 veto / LocalizationTargetSet 非 UPROPERTY(config) / GatherText SCC noise / Culture BCP-47 validate |
| [`settings-persistence.md`](../../skills/ue-settings-persistence/settings-persistence.md) | UPROPERTY(config) flag + `TryUpdateDefaultConfigFile()` + AssetRegistrySearchable 三件套；SaveConfig 无参陷阱 + 排查 checklist + 嵌套 UObject 集合的 PostEditChangeProperty 双轨同步 pattern |

### Tooling / Agent Integration（MCP 平台选择）

| Guideline | 解决的问题 |
|---|---|
| [`mcp-platform-choice.md`](mcp-platform-choice.md) | UE 5.8 官方 ModelContextProtocol plugin vs 社区 fork UnrealMCP 的选型决策表；不要 backport / 不要抄重构的两个 anti-pattern；官方 `UToolsetDefinition` 扩展机制（Python Path A + C++ Path B + AICallable UFUNCTION 约束）；演进路径（短中长期） |

> 配对的 fork 使用指南（"fork 怎么用"，跟"用哪个"互补不重叠）：[`skills/ue/unrealmcp-usage/SKILL.md`](../../skills/ue/unrealmcp-usage/SKILL.md)

## 相关 Techniques

[`../../techniques/ue-custom-graph-editor.md`](../../techniques/ue-custom-graph-editor.md) ——
建一个 custom UE Graph Editor 的 step-by-step procedural guide。Prerequisites
段强调"读最相近的 UE reference implementation"——是 skill
[`ue-reference-engine-source`](../../skills/ue-reference-engine-source/SKILL.md)
在 Graph Editor 子领域的具体应用。

## 看哪几篇取决于你在做什么

- **第一次接 UE custom graph editor** → 先 skill [`ue-reference-engine-source`](../../skills/ue-reference-engine-source/SKILL.md) + [`../../techniques/ue-custom-graph-editor.md`](../../techniques/ue-custom-graph-editor.md)，按 procedural 步骤推进 + 每步翻 graph-editor-constraints.md / graph-data-ownership.md 对应章节
- **写新 Asset Editor + UPROPERTY 持久化设置** → skill [`ue-settings-persistence`](../../skills/ue-settings-persistence/SKILL.md) + [`asset-definition-can-duplicate-limit.md`](asset-definition-can-duplicate-limit.md)
- **本地化 / 翻译 pipeline** → [`localization-pitfalls.md`](localization-pitfalls.md) + skill [`ue-settings-persistence`](../../skills/ue-settings-persistence/SKILL.md)
- **Runtime 跟 Editor 模块边界设计** → skill [`ue-module-architecture`](../../skills/ue-module-architecture/SKILL.md)（含同 module 内三层模型 + 跨 module 依赖方向硬约束）
- **接到一个 UE bug / weird behavior** → skill [`ue-reference-engine-source`](../../skills/ue-reference-engine-source/SKILL.md) 的"按子系统分类的 reference 清单"找最相近 engine source 看怎么实现的

## 增长状态

UE 子目录从 5 份扩到 8 份发生在 2026-04 → 2026-05 期间，主要来自
DialogueSystemSample 插件 Phase 1-3 ship（Line ID + 本地化）的 retrospective
promotion。后续候选（two-strike rule 等第二次复发）：

- UE Factory 共存不替换（`UDataAssetFactory` 跟自定义 Factory 同 SupportedClass 共存）
- Validation Gate 三道闸（Save / PIE / Cook + `UEditorValidatorBase`）
- 双源 schema parity test（C++ + Python / SQL + ORM 等）
