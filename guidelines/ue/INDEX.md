# UE Guidelines 索引

UE 是当前 meta-corpus 最重的子目录（约 1400 行 / 8 份 guidelines + 1 份配套
technique），集中存放 Unreal Engine framework 的 hidden contracts 和 idiom。

**非 UE 项目可以整段 skip 本目录** —— 通用编程 / 工程组织规则在
`guidelines/code/` / `guidelines/workflow/` / `guidelines/collaboration/`。

## 按使用场景分类

### Prep work（开工前必看）

| Guideline | 解决的问题 |
|---|---|
| [`reference-engine-source.md`](reference-engine-source.md) | UE 功能（特别是 UI / Editor）开工前先找最相近的 engine source / official sample / 第三方 plugin reference impl；按 22 个 UE 子系统给 reference 清单 |

> 配对的项目内 prep work：[`../code/reuse-before-implementing.md`](../code/reuse-before-implementing.md)（survey 项目内已有 similar code）。两条 prep work 都属于"动手前先 survey"的对称概念。

### Graph Editor 子领域

| Guideline | 解决的问题 |
|---|---|
| [`graph-editor-constraints.md`](graph-editor-constraints.md) | NodeGuid 初始化 / Pin SetOwner / Custom SGraphNode Factory 注册 / Pin 自动连线 / Dynamic Pin Reconstruction / Reroute (Knot) 节点 4 件套 / Cold Rebuild over Live Coding / `RF_Transactional` / Undo Refresh / Dual-Layer Data 模型 / Copy-Paste DuplicateObject |
| [`graph-data-ownership.md`](graph-data-ownership.md) | UEdGraph pin 是连接 SoT / runtime 数据是 derived / Compile Full Flush > incremental sync / Anti-Patterns（incremental sync / edge properties on runtime side） |

### Editor / Runtime 架构

| Guideline | 解决的问题 |
|---|---|
| [`editor-runtime-separation.md`](editor-runtime-separation.md) | 三层模型（Runtime Ops / Editor Actions / UI）/ Undo Support（基础 + 嵌套 transaction）/ Editor Actions 自动化生成（ExecEditorOp 模板 + 可选 Python codegen） |

### Asset Lifecycle

| Guideline | 解决的问题 |
|---|---|
| [`asset-definition-can-duplicate-limit.md`](asset-definition-can-duplicate-limit.md) | `UAssetDefinition::CanDuplicate` 只拦 Content Browser 命令；Copy+Paste / Migrate / 程序化 DuplicateObject 全部绕过；必须双层防御（CanDuplicate + PostDuplicate 兜底） |
| [`blueprint-auto-override-api.md`](blueprint-auto-override-api.md) | 程序化创建 Blueprint Override 时 `AddFunctionGraph<UClass*>` vs `<UFunction*>` 模板参数选择；`bIsUserCreated` 跟模板参数的正交语义 |

### Localization / Settings 持久化

| Guideline | 解决的问题 |
|---|---|
| [`localization-pitfalls.md`](localization-pitfalls.md) | UE Localization API 6 条 trap：FromStringTable.ToString culture 漂 / Content/Localization 硬编码 exclude / PreBeginPIE 不能 veto / LocalizationTargetSet 非 UPROPERTY(config) / GatherText SCC noise / Culture BCP-47 validate |
| [`settings-persistence.md`](settings-persistence.md) | UPROPERTY(config) flag + `TryUpdateDefaultConfigFile()` + AssetRegistrySearchable 三件套；SaveConfig 无参陷阱 + 排查 checklist + 嵌套 UObject 集合的 PostEditChangeProperty 双轨同步 pattern |

## 相关 Techniques

[`../../techniques/ue-custom-graph-editor.md`](../../techniques/ue-custom-graph-editor.md) ——
建一个 custom UE Graph Editor 的 step-by-step procedural guide。Prerequisites
段强调"读最相近的 UE reference implementation"——是 `reference-engine-source.md`
guideline 在 Graph Editor 子领域的具体应用。

## 看哪几篇取决于你在做什么

- **第一次接 UE custom graph editor** → 先 [`reference-engine-source.md`](reference-engine-source.md) + [`../../techniques/ue-custom-graph-editor.md`](../../techniques/ue-custom-graph-editor.md)，按 procedural 步骤推进 + 每步翻 graph-editor-constraints.md / graph-data-ownership.md 对应章节
- **写新 Asset Editor + UPROPERTY 持久化设置** → [`settings-persistence.md`](settings-persistence.md) + [`asset-definition-can-duplicate-limit.md`](asset-definition-can-duplicate-limit.md)
- **本地化 / 翻译 pipeline** → [`localization-pitfalls.md`](localization-pitfalls.md) + [`settings-persistence.md`](settings-persistence.md)
- **Runtime 跟 Editor 模块边界设计** → [`editor-runtime-separation.md`](editor-runtime-separation.md)
- **接到一个 UE bug / weird behavior** → [`reference-engine-source.md`](reference-engine-source.md) 的"按子系统分类的 reference 清单"找最相近 engine source 看怎么实现的

## 增长状态

UE 子目录从 5 份扩到 8 份发生在 2026-04 → 2026-05 期间，主要来自
DialogueSystemSample 插件 Phase 1-3 ship（Line ID + 本地化）的 retrospective
promotion。后续候选（two-strike rule 等第二次复发）：

- UE Factory 共存不替换（`UDataAssetFactory` 跟自定义 Factory 同 SupportedClass 共存）
- Validation Gate 三道闸（Save / PIE / Cook + `UEditorValidatorBase`）
- 双源 schema parity test（C++ + Python / SQL + ORM 等）
