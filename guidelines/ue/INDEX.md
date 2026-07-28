# UE Guidelines 索引

UE 是 meta-corpus 最重的框架子目录——Unreal Engine framework 的 hidden contracts + idiom。
分两层：

- **broad guidelines**（14 份）——常碰的核心契约，**懒加载**：接 UE 任务时读本 INDEX 导航到具体文件（2026-07-28 起不再 `@`-import 常驻；重度 UE 项目可在项目侧 `AGENTS.md` `@`-import 需要的子集拉回）。
- **懒加载 UE skills**（8 个）——ultra-niche / 按场景触发的簇，bundle 成 skill，只在匹配任务时加载。

**非 UE 项目可整段 skip 本目录。** 通用编程 / C++ / 工程组织规则在 `guidelines/code/` /
`guidelines/cpp/`（见 [`../cpp/INDEX.md`](../cpp/INDEX.md)）/ `guidelines/workflow/`。

## UE 专用 skills（懒加载，不 `@`-import）

| Skill | 何时触发 |
|---|---|
| `ue-reference-engine-source` | 写**任何** UE 功能（尤其 UI / Editor / Asset Editor / Slate / Localization / Validator / Factory）**动手前**——先找最相近的 engine source reference impl 读一遍 |
| `ue-module-architecture` | 设计 UE module / plugin 切分、写 / review 任何 `*.Build.cs`、决定新类 / test / setting 归哪个 module、诊断 cook / package 的 missing-module 错 |
| `ue-settings-persistence` | 加 / 改 UE Project Settings / `UDeveloperSettings` / config UObject / per-asset metadata；settings 重启后丢 / 开发机 vs CI 不一致 |
| `ue-custom-graph-editor` | 从零建一个自定义 `UEdGraph` 节点图编辑器（7 步流程 + graph 数据归属设计）|
| `ue-procedural-numerical` | 程序化建 RigVM / ControlRig / Deformer 图 + 模块内数值 / GPU 求解 / CPU 并行 |
| `ue-ml-animation` | 代码 / 神经网络直出 pose（自定义 `UAnimInstance` proxy + 离线评估）+ NNE ONNX 推理 |
| `unrealmcp-usage` | 用 UnrealMCP **fork**（TCP 命令）做编辑器自动化 |
| `official-mcp-usage` | 用 UE 5.8+ **官方** `ModelContextProtocol` MCP（HTTP）做编辑器自动化 |

> MCP「用 fork 还是官方」的平台选型见下 broad guideline `mcp-platform-choice.md`（跟上面两条 usage skill 互补：那两条讲「怎么用」，选型讲「用哪个」）。

## broad guidelines（按场景）

### Graph Editor 硬约束

| Guideline | 解决的问题 |
|---|---|
| [`graph-editor-constraints.md`](graph-editor-constraints.md) | NodeGuid 初始化 / Pin `SetOwner` 一次 / Custom SGraphNode Factory 注册 / Pin 拖创后自动连线 / Dynamic Pin Reconstruction / Reroute (Knot) 4 件套 / Cold Rebuild over Live Coding / `RF_Transactional` / Undo Refresh widget / Dual-Layer Data 模型 undo / Copy-Paste DuplicateObject |

> 建一个**新的**自定义图编辑器的完整 7 步流程 + graph 数据归属（哪层拥有 node 属性 / 连接拓扑 / edge 属性）走 skill `ue-custom-graph-editor`；本条是它处处引用的硬约束底座。

### Asset / Blueprint

| Guideline | 解决的问题 |
|---|---|
| [`blueprint-auto-override-api.md`](blueprint-auto-override-api.md) | 程序化创建 BP Override：`AddFunctionGraph<UClass*>` vs `<UFunction*>` 模板参数 + `bIsUserCreated` 正交语义 |
| [`asset-definition-can-duplicate-limit.md`](asset-definition-can-duplicate-limit.md) | `UAssetDefinition::CanDuplicate` 只拦 Content Browser Duplicate；Copy+Paste / Migrate / 程序化 DuplicateObject 全绕过 → 双层防御（+ `PostDuplicate` 兜底） |

### Details Customization / Property Editor

| Guideline | 解决的问题 |
|---|---|
| [`details-customization-prefer-reflection.md`](details-customization-prefer-reflection.md) | 能用 UPROPERTY 反射就别写 Customization；`FClassProperty::MetaClass` UHT 编译期固化、runtime 改不动 → 数据层分派生类而非 UI 层动态收窄 |
| [`property-handle-strong-capture.md`](property-handle-strong-capture.md) | `IDetailCustomization` 里 `IPropertyHandle` 必须 strong-ref by-value capture 进持久 lambda（weak 会在 CustomizeDetails 返回后失效 → widget 永远显默认值） |

### Editor 生命周期 / 数学类型

| Guideline | 解决的问题 |
|---|---|
| [`leveleditor-modetools-lifetime.md`](leveleditor-modetools-lifetime.md) | `GLevelEditorModeTools()` 单例无效时 ensure 失败 + **错误重建**（非返回空）；startup gate 到 `FLevelEditorModule::OnLevelEditorCreated`、shutdown 守卫；5.8 起 `GLevelEditorModeToolsIsValid()` 删除、用 live-level-editor 代理 |
| [`fvector4-vector-equals-silent-fail.md`](fvector4-vector-equals-silent-fail.md) | `FMatrix::TransformVector`/`TransformPosition` 返 `FVector4`(W=0)，直接跟 `FVector` 比 `.Equals` 因 W 静默失败（XYZ 对、断言恒 false）；用 `FVector(...)` 包裹丢 W |

### 版本升级 / 构建 / 打包 / CI

| Guideline | 解决的问题 |
|---|---|
| [`ue58-upgrade-gotchas.md`](ue58-upgrade-gotchas.md) | 升 UE 5.8 三硬契约：Target `BuildSettingsVersion.V7` + `IncludeOrderVersion.Unreal5_8` / `.uproject` RapidJSON 读裸控制字符报误导性 `Invalid encoding` / 运行 editor 需 VC++ redist `14.50.35719+` |
| [`build-plugin-limitations.md`](build-plugin-limitations.md) | `RunUAT BuildPlugin` 四个 limitation：`Config/`+`Scripts/` 默认不进包（`FilterPlugin.ini`）/ UBT 剥 `PythonRequirements` / 交付包含非交付物（`Intermediate`/`.pdb`/RuntimeDependencies dll）/ installed distribution 只开放 Editor target（`-NoTargetPlatforms`） |
| [`automation-test-from-ci.md`](automation-test-from-ci.md) | UE 在 CI 跑 Automation：必须 `UnrealEditor-Cmd.exe`（不是 GUI 版）/ 跑完不 graceful quit → 脚本监控 report + grace + force kill |

### 外部自动化 / MCP 写入 / LogicDriver / 本地化

| Guideline | 解决的问题 |
|---|---|
| [`external-automation-write-path.md`](external-automation-write-path.md) | 外部脚本（MCP / commandlet / Editor Utility Widget）写 UE 资产**必走** Editor 的 `PostEditChangeProperty` 同步路径，别只调底层 setter（否则只改表层、framework 隐式状态不刷 → 运行时炸；schema 编译 success ≠ asset OK） |
| [`mcp-platform-choice.md`](mcp-platform-choice.md) | UE 5.8 官方 `ModelContextProtocol` vs 社区 fork UnrealMCP 的选型决策表 + 不要 backport / 不要抄重构；官方 `UToolsetDefinition` 扩展机制 |
| [`logicdriver-state-class-rewires-boundgraph.md`](logicdriver-state-class-rewires-boundgraph.md) | LogicDriver state node 切自定义 `StateClass` 会自动**撕 BoundGraph wire**（注入节点 + 重定向 lifecycle 输出），切回 default 不撤销 → 只能 file-revert；设计上 self class 别 override BlueprintNativeEvent |
| [`localization-pitfalls.md`](localization-pitfalls.md) | UE Localization 6 trap：`FromStringTable.ToString` culture 漂 / `Content/Localization` 硬编码 exclude / `PreBeginPIE` 不能 veto / `LocalizationTargetSet` 非 `UPROPERTY(config)` / GatherText SCC noise / Culture BCP-47 validate |

## 看哪几篇取决于你在做什么

- **写任何 UE 功能动手前** → skill `ue-reference-engine-source`（按 22 子系统找 engine reference）
- **第一次建 UE custom graph editor** → skill `ue-custom-graph-editor`（7 步流程 + 数据归属）+ 每步翻 [`graph-editor-constraints.md`](graph-editor-constraints.md)
- **写新 Asset Editor + 持久化设置** → skill `ue-settings-persistence` + [`asset-definition-can-duplicate-limit.md`](asset-definition-can-duplicate-limit.md)
- **Details 面板定制** → 先 [`details-customization-prefer-reflection.md`](details-customization-prefer-reflection.md)（能反射别写 customization），要写就守 [`property-handle-strong-capture.md`](property-handle-strong-capture.md)
- **Runtime / Editor 模块边界** → skill `ue-module-architecture`
- **程序化建 RigVM / ControlRig / Deformer 图、模块内数值 / GPU / 并行** → skill `ue-procedural-numerical`
- **代码 / 神经网络驱动动画（不走 AnimBP）** → skill `ue-ml-animation`
- **外部脚本 / MCP 写 UE 资产** → [`external-automation-write-path.md`](external-automation-write-path.md)（必走 PostEditChangeProperty）+ 平台选型 [`mcp-platform-choice.md`](mcp-platform-choice.md) + usage skill `unrealmcp-usage` / `official-mcp-usage`
- **本地化 / 翻译 pipeline** → [`localization-pitfalls.md`](localization-pitfalls.md) + skill `ue-settings-persistence`
- **升级到 UE 5.8 / BuildPlugin 打包 / CI 跑 automation** → [`ue58-upgrade-gotchas.md`](ue58-upgrade-gotchas.md) / [`build-plugin-limitations.md`](build-plugin-limitations.md) / [`automation-test-from-ci.md`](automation-test-from-ci.md)
- **接到一个 UE bug / weird behavior** → skill `ue-reference-engine-source` 的按子系统 reference 清单，找最相近 engine source 看怎么实现的

## 增长状态

UE 子目录 2026-04 → 2026-07 从 5 份扩到 20+ 份，来自 DialogueSystemSample（Line ID + 本地化）、
BattleDemo（LogicDriver / MCP 写入）、PathAnimGen（AnimInstance proxy + NNE）、curvenet 形变插件
（RigVM / Deformer / RBF / GPU / 并行）等项目 ship 的 retrospective promotion。

2026-07-19 context-budget audit S2 Tier D：ultra-niche 簇（procedural-numerical / ML-anim /
custom-graph）bundle 成懒加载 skill；`graph-data-ownership` 的框架无关内核提升到常驻
[`../code/dual-layer-data-ownership.md`](../code/dual-layer-data-ownership.md)；broad guidelines 当轮保留常驻。

2026-07-28 context-budget audit：broad-UE 14 份也从常驻转懒加载，本 INDEX 承接导航，省 ~2500 行常驻（非 UE session 不再吃这块）；重度 UE 项目在项目侧 `AGENTS.md` `@`-import 需要的子集拉回（`../collaboration/multi-agent.md` Option 2）。触发本条的判据来自 `skills/workflow/context-budget-audit` 新增的「约束必要性」第二轴 + Claude 5-gen 博文的渐进披露原则。

后续候选（two-strike rule 第二次复发时补）：UE Factory 共存不替换 / Validation Gate 三道闸（Save / PIE / Cook）/ 双源 schema parity test。
