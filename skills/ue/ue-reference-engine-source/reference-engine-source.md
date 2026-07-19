# 写 UE 功能前先找 reference implementation

## 核心规则

实现任何 UE 功能（特别是 UI / Editor / Asset Editor / Slate / Localization / SourceControl / Validator 等 framework 相关），**动手前必须先找最相近的 reference implementation**：

1. 优先读 **UE engine source**（`Engine/Source/Editor/` / `Engine/Source/Developer/` / `Engine/Source/Runtime/`）里同 framework 的 native 实现
2. 找不到 native 实现时读 **UE official sample**（Lyra / ContentExamples / VariantManager 等）
3. 仍找不到查 **第三方 plugin 源码** / 官方文档 / 论坛
4. 网络搜索（UE forums / Stack Overflow / Reddit r/unrealengine）作为辅助

**不要凭猜测实施**。UE framework 有大量 implicit contracts（NodeGuid 初始化 / Pin SetOwner / RF_Transactional / 各种 PostXxx hook 调用顺序 / 模块依赖方向 等），都**只在 reference impl 里能看到**，引擎自己的 docs 几乎不写。

跟 `guidelines/code/reuse-before-implementing.md` 关系：那条讲"先 survey 项目内现有代码"；本条讲"先 survey UE engine / 生态现有实现"。两条都属于 prep work。

## 为什么

UE 的 framework 设计普遍**靠 example 学**，不靠文档学：

- `UEdGraphSchema` 有 30+ virtual method，doc comment 只写"override this if you want to..."，**调用顺序 / 副作用 / 不可绕过的约束** 都没说
- `SGraphNode` 子类怎么注册 / `PinWidget->SetOwner()` 调几次 / `CreatePinWidgets` vs `AddPin` 各自时机 —— 都得从 `SGraphNodeK2Default` / `SGraphNodeKnot` 反向读出来
- `UAssetDefinition` 的 `CanDuplicate` 只在哪些 path 被调 —— 引擎 doc 完全不提
- `ULocalizationSettings::PostEditChangeProperty` 触发的内部 sync 逻辑 —— 只有读 `GameTargetSet ↔ GameTargetsSettings` 双轨同步的 engine cpp 才能看到
- `IPIEAuthorizer` modular feature 用法 —— UE 5.5 新引入，唯一 reference 在 engine source 自己注册的 sample 里

凭猜测实施的代价：
- 编译过但 runtime crash（典型：`PinWidget->SetOwner()` 调两次 → `check(!OwnerNodePtr.IsValid())` fatal）
- 看起来工作但行为有 corner case（典型：`CanDuplicate` 拦不住 Ctrl+C/V）
- 静默失效（典型：ST.uasset 放 `Content/Localization/` 下，`Gather Text` 扫不到）

读 reference impl 的成本是 30 分钟到 2 小时；踩坑 + 排查 + 重写的代价通常是几天到一周。

## 怎么找最相近的 reference implementation

### 1. 按 UE 子系统分类的 reference 清单

| 你要做什么 | 先读哪些 engine source |
|---|---|
| 自定义 Graph Editor (节点 / Schema / Toolkit) | `BlueprintGraph/` / `AnimGraph/` / `BehaviorTreeEditor/` / `MaterialEditor/` / `SoundCueEditor/` |
| 自定义 Schema 重载（`TryCreateConnection` / `OnPinConnectionDoubleCicked` / `GetGraphContextActions` 等）| `EdGraphSchema_K2.cpp` / `AnimationStateMachineSchema.cpp` / `MaterialGraphSchema.cpp` |
| 自定义 SGraphNode 子类 + 工厂注册 | `SGraphNodeK2Default` / `SGraphNodeKnot` / `SAnimationGraphNode` |
| Pin Widget / Drag Drop / Knot | `SGraphPin.cpp` / `SGraphPinKnot.cpp` / `FDragConnection` / `FAmbivalentDirectionDragConnection` |
| ConnectionDrawingPolicy | `FKismetConnectionDrawingPolicy` / `FAnimGraphConnectionDrawingPolicy` |
| Asset Editor Toolkit（多 tab / undo client / details panel）| `FBlueprintEditor` / `FAnimationBlueprintEditor` / `FMaterialEditor` / `FBehaviorTreeEditor` |
| Asset Type Actions / AssetDefinition | `UAssetDefinition_Blueprint` / `UAssetDefinition_AnimBlueprint` / `UAssetDefinition_Material` |
| Details Customization | `Engine/Source/Editor/DetailCustomizations/` 整个目录 |
| Slate Widget（list / tree / picker / panel） | `SListView` / `STreeView` / `SAssetView` / `SContentBrowser` / `SAssetPicker` |
| Path / Class Picker | `SObjectPropertyEntryBox` / `SPathPicker` / `SClassPicker` / `FOpenAssetDialogConfig` |
| Toolkit / NomadTab / WorkflowCentric | `FAssetEditorToolkit` / `FWorkflowCentricApplication` / `FGlobalTabmanager` |
| Editor Validator (Save / PIE / Cook 校验) | `UEditorValidatorBase` / `UEditorValidator_LoadPackage` 等子类 |
| PIE Gate / Authorize | `IPIEAuthorizer` (UE 5.5+ modular feature) / `FEditorDelegates::PreBeginPIE` 各 caller |
| MessageLog 注册 + Jump-to-Asset | `FMessageLog` / `FUObjectToken` / `IMessageLogListing` |
| Localization Target / Gather / archive | `ULocalizationSettings` / `LocalizationConfigurationScript.cpp` / `GatherTextFromAssetsCommandlet` |
| StringTable | `FStringTable` / `FStringTableRegistry` / `UStringTable` |
| Source Control | `USourceControlHelpers` / `ISourceControlProvider` / `ISourceControlOperation` 各子类 |
| Commandlet (CI / 批处理) | `UCommandlet` / `UGatherTextCommandlet` / `UDataValidationCommandlet` |
| Subsystem (Engine / Editor / GameInstance) | `UEngineSubsystem` / `UEditorSubsystem` / `UWorldSubsystem` 各 native subclass |
| Asset Registry tags / `AssetRegistrySearchable` | `UBlueprintGeneratedClass::GetAssetRegistryTags` / `UStaticMesh::GetAssetRegistryTags` |
| `PostEditChangeProperty` / dynamic pin rebuild | `K2Node_Switch::PostEditChangeProperty` / `AnimGraphNode_Base::PostEditChangeProperty` |
| `PostDuplicate` / `PostLoad` / `PostInitProperties` 各 hook 用法 | grep 自带 UObject 子类的同名 override 看典型 idiom |
| Factory (Content Browser "Create X") | `UFactory` / `UBlueprintFactory` / `UDataAssetFactory` |
| Property Customization (Combo / 三态 / 自定义 row) | `Engine/Source/Editor/DetailCustomizations/Private/*Customization.cpp` |

### 2. UE official sample 项目

| 项目 | 用途 |
|---|---|
| **Lyra** (UE 5.x sample game) | gameplay framework / `CommonConversation` / input remap / Asset Manager 用法 |
| **ContentExamples** (官方 demo project) | Blueprint / Material / Animation / 各种 native asset 怎么用的最小例子 |
| **VariantManager** plugin | 自定义 detail customization + asset editor + 工具栏 多面综合 |
| **Niagara** | 自研 graph editor 大型实例 |

UE Marketplace / Fab 上的官方 + 第三方插件源码（如果开源）也可参考——但官方实例优先。

### 3. 网络搜索关键字

按"症状 → 关键字"找：

- "UE 怎么 X" → 优先**英文** search `Unreal Engine X` 比中文准
- 错误信息直接贴去 search：UE engine 的 assertion / `check()` / `LogXxx Error:` 文本通常有人遇过
- `site:forums.unrealengine.com` / `site:stackoverflow.com` 限定优质来源
- 找 hidden contract 的关键字：`Unreal Engine X hidden / gotcha / not documented`

### 4. AI agent / IDE 工具

- 用 Agent 调度（如 Explore / Grep）批量在 `Engine/Source/` 下 grep 找 reference
- IDE（Rider / Visual Studio）"Find Usages" 看 native engine 怎么 call 某个 API

## 选 reference 的优先级

```
1. UE engine native 实现（最权威，跟你写的会跑在同一引擎上）
   ↓ 找不到
2. UE official sample / plugin
   ↓ 找不到
3. 知名第三方 plugin 源码（生产验证过）
   ↓ 找不到
4. 官方文档 / 论坛 / blog
   ↓ 找不到
5. AI 生成的代码（最不可靠，UE 接口在不同版本变化大）
```

**优先级不能跳级**：找到 engine native 实现就用它，不要因为"看起来麻烦"退回到论坛贴。论坛贴里的代码常常带过时 API / 错误模式。

## 读 reference impl 的方法

找到一份 reference impl 后**不是简单 copy**，应该：

1. **先理解约束**：reference 里那些"看起来多余"的代码通常对应 framework 的隐式约束（如 `CreateNewGuid()` + `PostPlacedNewNode()` 必须成对）。理解它在防什么。
2. **找最简洁的实例**：通常 native engine 实现会有"完整版"和"极简版"。极简版（如 `SGraphNodeKnot` 比 `SGraphNodeK2Default` 简单很多）作为起步参考更合适。
3. **跨多个 reference 对比**：如果两个 reference impl 都做同一类事但写法不一样（例：`K2Node_Switch::PostEditChangeProperty` 直接 `ReconstructNode`，但 `AnimGraphNode_Base` 走 `GetSchema()->ReconstructNode(*this)`），通常说明约束很弱 / 风格选择；选更符合自己上下文的。
4. **抄前理解：abstract over 别 copy 死**：你的 use case 跟 reference 通常不完全一样。理解 reference 在做什么后，用自己的命名 / 数据模型重写，不要硬抄 native 类名。

## Anti-Patterns

### 1. 凭"我以为 UE 是这样工作的"动手

最常见的 bug 来源。典型：

- "我以为 `UEdGraphNode` 构造完就能用" → 忘记 `CreateNewGuid()` + `PostPlacedNewNode()` → GUID 全 0 → 拖线静默失败
- "我以为 SaveConfig 会写到项目仓库 ini" → 实际写到 user-level Game.ini → 跨机配置丢
- "我以为 `CanDuplicate` 拦所有复制" → 实际只拦 Content Browser Duplicate 命令

**修法**：动手前**强制**找一份 reference impl 读 30 分钟。

### 2. 用 AI 生成 UE 代码不验证

UE 接口跨版本变化大（5.0 → 5.5 之间很多 API 改名 / 拆分）。AI 训练数据可能停在 4.x 或 5.0；生成的代码用过时 API 编译失败 / 编译过但 runtime crash。

**修法**：AI 生成 UE 代码后，每个用到的 UE 类型 / 函数都**在当前版本 engine source 里 grep 确认存在**。

### 3. 复制论坛贴的"work-around"不读 engine source

论坛贴常见模式："I tried X and got Y crash, here's my workaround"——workaround 通常是 hack，没真理解 root cause。直接复制进项目后维护极痛苦。

**修法**：论坛贴只作为"找 engine source 入口"的提示，最终实施必须基于 engine source 自己看明白。

### 4. 找不到 reference 就硬上

如果一个 UE 功能你**完全找不到 reference**（既不在 engine source / 也不在 sample / 也没人在论坛贴过）——通常说明你正在做**框架不打算支持**的事情，或者**用错了路径**。

**修法**：换思路 / 找替代实现路径，**别硬上**。例：要 veto `PreBeginPIE`——找不到 reference 是因为这 delegate 设计上就不支持 veto；正确路径是 UE 5.5 的 `IPIEAuthorizer` modular feature。

## 项目实例参考

DialogueSystemSample 插件 3 个月开发期间，几乎所有 UE 功能都从 engine source 借了 reference impl：

| 功能 | reference impl |
|---|---|
| Custom Graph Editor 整套（Schema / SGraphNode / Toolkit / Factory）| `BlueprintGraph` / `AnimationStateMachineEditor` / `BehaviorTreeEditor` |
| Reroute / Knot 节点（widget + drag + connection drawing） | `SGraphNodeKnot` / `SGraphPinKnot` / `FAmbivalentDirectionDragConnection` / `FKismetConnectionDrawingPolicy::ShouldChangeTangentForKnot` |
| Dynamic Pin Reconstruction | `K2Node_Switch::PostEditChangeProperty` + `AnimGraphNode_Base::PostEditChangeProperty` |
| `UAssetDefinition` + CanDuplicate 双层防御 | UE 5.0+ 新 framework；`SMyBlueprint::ImplementFunction` 抄 override 实现路径 |
| Blueprint Override 程序化创建（`AddFunctionGraph<UClass*>` 模板参数选）| `SMyBlueprint::ImplementFunction:2814`（UE 5.5）|
| `IDetailsView::OnFinishedChangingProperties()` 作为 Editor 端拦截 PropertyChanged | engine 蓝图编辑器内部用法 |
| `IPIEAuthorizer` modular feature（PIE Gate veto）| UE 5.5 引擎自带 framework |
| Localization Setup `GameTargetSet → GameTargetsSettings` 同步 | `ULocalizationSettings` + `LocalizationConfigurationScript.cpp` |
| `SComboButton + SPathPicker popup`（path 输入 UX）| `Engine/Source/Editor/ContentBrowser` |
| `UEditorValidatorBase` 子类（Save / Cook gate） | `UEditorValidator_LoadPackage` 等 native 子类 |
| Asset Registry tags + `AssetRegistrySearchable` UPROPERTY meta | `UBlueprintGeneratedClass::GetAssetRegistryTags` |

反例（凭猜测踩的坑）：
- 最早版本 `PinWidget->SetOwner()` 在 `CreatePinWidgets` 里又调一次 → crash。读 `SGraphNodeK2Default` 后才知道 SetOwner 只能在 `AddPin` 里调一次
- 最早版本节点 `NewObject<UEdGraphNode>()` 后没调 `CreateNewGuid()` + `PostPlacedNewNode()` → 拖线失败。读任何 native schema 的 NewNode 路径都能发现
- 最早版本 PIE Gate 走 `FEditorDelegates::PreBeginPIE` + `RequestEndPlayMap` → TOptional 空 deref crash。如果开工前 grep 找过"PIE veto"会发现 UE 5.5 引入了专门的 `IPIEAuthorizer`

## 相关 Guidelines

> 链接相对路径已在 promote 到 skill 时去除；下列路径是相对 `agent_coding_guidelines` repo root 的引用。

- `guidelines/code/reuse-before-implementing.md` —— 对称的另一条 prep work（survey 项目内 vs survey UE 生态）
- `guidelines/ue/graph-editor-constraints.md` —— Graph Editor 子领域的具体 hidden contracts（NodeGuid / Pin Ownership / Reroute / 等）
- `guidelines/ue/localization-pitfalls.md` —— Localization 子领域的 hidden contracts
- `guidelines/ue/asset-definition-can-duplicate-limit.md` —— AssetDefinition 子领域的 hidden contracts
- skill `ue-custom-graph-editor` —— Graph Editor 的 step-by-step procedural guide，"Prerequisites" 节是本条 guideline 的具体应用
