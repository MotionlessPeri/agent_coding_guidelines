# 核对 UE 框架契约与参考实现

## 查证范围与已有证据

本文件是 UE 框架查证方法的主来源。实现、审查或排查涉及**不熟悉、发生变化或有疑点的契约**时，在依赖该契约作决定前查证；纯文字修改或已有有效证据覆盖的用法，无须重新查整套参考。

1. 明确当前项目的目标引擎版本、相关调用路径和待确认的问题，例如调用顺序、对象归属、线程或生命周期前提。
2. 复用覆盖同一版本、配置和调用路径且未被新证据推翻的源码记录、官方说明或验证结果。版本升级、路径变化或行为与记录冲突时，只补查受影响部分。
3. 按下方导航定位有关定义、调用者或参考实现，不要求每个 feature 重读一遍，也不要求把每个已知 API 全部 grep 一遍。
4. 保留支撑关键结论的版本、源码位置或验证结果；未确认部分说明限制。现有项目记录或交付说明足够时，不另建查证清单。

UE framework 的隐式契约包括 NodeGuid 初始化、Pin SetOwner、RF_Transactional、各类 PostXxx hook 调用顺序和模块依赖方向等。参考实现有助于发现这些前提；确认适用于当前调用路径的前提后，仍须遵守，不能因按需查证而把它降为可选建议。

项目内的复用调查见 `guidelines/code/reuse-before-implementing.md`；本文件处理 UE 框架证据。针对同一个问题找到的有效证据可共用，不重复做两轮调查。

## 为什么

参考实现能补充 API 说明未覆盖的调用上下文。既有项目中需要查清的问题包括：

- `UEdGraphSchema` 有 30+ virtual method，doc comment 只写"override this if you want to..."，**调用顺序 / 副作用 / 不可绕过的约束** 都没说
- `SGraphNode` 子类怎么注册 / `PinWidget->SetOwner()` 调几次 / `CreatePinWidgets` vs `AddPin` 各自时机 —— 都得从 `SGraphNodeK2Default` / `SGraphNodeKnot` 反向读出来
- `UAssetDefinition` 的 `CanDuplicate` 只在哪些 path 被调 —— 引擎 doc 完全不提
- `ULocalizationSettings::PostEditChangeProperty` 触发的内部 sync 逻辑 —— 只有读 `GameTargetSet ↔ GameTargetsSettings` 双轨同步的 engine cpp 才能看到
- `IPIEAuthorizer` modular feature 用法 —— UE 5.5 新引入，唯一 reference 在 engine source 自己注册的 sample 里

凭猜测实施的代价：
- 编译过但 runtime crash（典型：`PinWidget->SetOwner()` 调两次 → `check(!OwnerNodePtr.IsValid())` fatal）
- 看起来工作但行为有 corner case（典型：`CanDuplicate` 拦不住 Ctrl+C/V）
- 静默失效（典型：ST.uasset 放 `Content/Localization/` 下，`Gather Text` 扫不到）

查证以解决当前不确定性为准，不按固定阅读时长验收。

## 怎么找最相近的 reference implementation

### 1. 按 UE 子系统分类的 reference 清单

| 你要做什么 | 可定位的 engine source |
|---|---|
| 自定义 Graph Editor (节点 / Schema / Toolkit) | `BlueprintGraph/` / `AnimGraph/` / `BehaviorTreeEditor/` / `MaterialEditor/` / `SoundCueEditor/` |
| 自定义 Schema 重载（`TryCreateConnection` / `OnPinConnectionDoubleCicked` / `GetGraphContextActions` 等）| `EdGraphSchema_K2.cpp` / `AnimationStateMachineSchema.cpp` / `MaterialGraphSchema.cpp` |
| 自定义 SGraphNode 子类 + 工厂注册 | `SGraphNodeK2Default` / `SGraphNodeKnot` / `SAnimationGraphNode` |
| Pin Widget / Drag Drop / Knot | `SGraphPin.cpp` / `SGraphPinKnot.cpp` / `FDragConnection` / `FAmbivalentDirectionDragConnection` |
| ConnectionDrawingPolicy | `FKismetConnectionDrawingPolicy` / `FAnimGraphConnectionDrawingPolicy` |
| Asset Editor Toolkit（多 tab / undo client / details panel）| `FBlueprintEditor` / `FAnimationBlueprintEditor` / `FMaterialEditor` / `FBehaviorTreeEditor` |
| Asset Type Actions / AssetDefinition | `UAssetDefinition_Blueprint` / `UAssetDefinition_AnimBlueprint` / `UAssetDefinition_Material` |
| Details Customization | 在 `Engine/Source/Editor/DetailCustomizations/` 中定位相近的 customization |
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

- "UE 怎么 X" → 用中文问题和英文 API / 子系统名交叉搜索，例如 `Unreal Engine X`
- 错误信息直接贴去 search：UE engine 的 assertion / `check()` / `LogXxx Error:` 文本通常有人遇过
- `site:forums.unrealengine.com` / `site:stackoverflow.com` 可帮助定位讨论；帖子仍需核对版本和证据
- 找 hidden contract 的关键字：`Unreal Engine X hidden / gotcha / not documented`

### 4. AI agent / IDE 工具

- 从相关模块或符号开始，用 `rg` 找定义和调用者；需要时再扩大到 `Engine/Source/`
- IDE（Rider / Visual Studio）"Find Usages" 看 native engine 怎么 call 某个 API

## 选择证据

- 框架内部行为优先查**目标版本**的声明、实现与调用者；公开契约可先查对应版本的官方文档。官方 sample / plugin 可补充完整用法，不要求按固定顺序读完所有来源。
- 选择与当前对象类型、配置和生命周期相近的实例。引擎内部实现可能依赖公共扩展接口没有的条件，不能因为它来自引擎就照搬。
- 第三方源码、论坛和博客可提供线索；检查其版本与适用条件。AI 生成的解释或代码是待核对的提议，本身不是框架契约的证据。
- 没找到参考，只能说明当前搜索未提供证据；可能是名称、搜索范围、版本或来源可见性的问题。继续查声明、调用者、官方说明或做最小行为验证。调整设计应有接口限制、行为结果或项目权衡等具体理由，不能只因没搜到参考；关键不确定性无法消除时，如实报告其对任务的影响。

## 读参考实现与验证

1. **理解前提**：看调用顺序、断言、对象归属和副作用，分清框架要求与示例自身选择。`CreateNewGuid()` / `PostPlacedNewNode()` 等既有案例可作查找入口。
2. **选相近且容易理解的实例**：例如从 `SGraphNodeKnot` 入手，再按需对照 `SGraphNodeK2Default`；简短不意味着适用条件相同。
3. **解释差异**：例如 `K2Node_Switch::PostEditChangeProperty` 直接 `ReconstructNode`，而 `AnimGraphNode_Base` 走 `GetSchema()->ReconstructNode(*this)`。先核对对象类型、schema、版本和调用路径，再追踪差异的实际效果；写法不同不能直接证明约束弱或只是风格。
4. **在当前路径验证行为**：参考代码按项目的数据模型与需求适配。编译可验证部分接口兼容性，不能证明生命周期、持久化、撤销或运行行为正确；对本次依赖的关键契约选择针对性的测试或可复现操作，已有有效结果可以复用。

## Anti-Patterns

### 1. 凭"我以为 UE 是这样工作的"动手

最常见的 bug 来源。典型：

- "我以为 `UEdGraphNode` 构造完就能用" → 忘记 `CreateNewGuid()` + `PostPlacedNewNode()` → GUID 全 0 → 拖线静默失败
- DialogueSystemSample 的共享配置案例曾假定 `SaveConfig()` 会写进版本控制中的 ini，实际写入本地 `Game.ini`，跨机未带走；这不是无参 `SaveConfig()` 的通用结论。原引擎版本未记录，配置类标志与调用对象等条件见[持久化案例的适用范围与证据](../ue-settings-persistence/settings-persistence.md#适用范围与证据)。
- "我以为 `CanDuplicate` 拦所有复制" → 实际只拦 Content Browser Duplicate 命令

**修法**：把猜测转成明确的待确认问题，按上方方法核对目标版本及调用路径。

### 2. 用 AI 生成 UE 代码不验证

生成代码可能使用不适合目标版本的 API，或遗漏调用前提；不能仅凭代码看起来合理就接受。

**修法**：针对不熟悉、变化或可疑的接口与行为补足证据，按“读参考实现与验证”区分接口检查和行为检查。

### 3. 复制论坛贴的 workaround 不核对条件

论坛贴解决的可能是另一版本、另一调用路径的问题；绕过症状的代码也未必解释了根因。

**修法**：核对帖子依据和当前路径，必要时查相关实现并复现行为，不把他人的成功报告当作当前项目的验证。

### 4. 把搜索无结果当作支持或不支持的结论

搜索不到示例既不能授权凭猜测实现，也不能直接证明框架不支持。

**修法**：按“选择证据”继续查证。既有案例中，`PreBeginPIE` 不支持 veto、UE 5.5 可走 `IPIEAuthorizer` modular feature；这个判断依赖接口与行为证据，不能由“没搜到示例”推出。

## 项目实例参考

以下保留 DialogueSystemSample 插件开发期间的参考与失败经验，用于定位线索，不代表跨版本保证；应用时按目标版本与调用路径查证：

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

- `guidelines/code/reuse-before-implementing.md` —— 项目内复用调查的范围与语义判断
- `guidelines/ue/graph-editor-constraints.md` —— Graph Editor 子领域的具体 hidden contracts（NodeGuid / Pin Ownership / Reroute / 等）
- `guidelines/ue/localization-pitfalls.md` —— Localization 子领域的 hidden contracts
- `guidelines/ue/asset-definition-can-duplicate-limit.md` —— AssetDefinition 子领域的 hidden contracts
- skill `ue-custom-graph-editor` —— 新建自定义 Graph Editor 时的流程；仅在任务匹配时使用
