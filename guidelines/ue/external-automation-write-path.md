# 从外部脚本写入 UE 资产：必走 Editor 的"写入即同步"路径

## 核心规则

从外部脚本（**MCP 命令 / Python commandlet / Editor Utility Widget / automation script / 任何不走 Editor 原生 UI 的写入路径**）修改 UE 资产时，**默认走 Editor UI 自己用的"写入即同步"路径**（`PostEditChangeProperty` / `FBlueprintEditorUtils::*` / 各 framework 的 canonical API），除非已经核实过这个 property 没有任何 framework hook。

直接调底层 setter（`Object->SetXxx()` / 设 UPROPERTY 字段）会**只改最表面那一层数据**，跳过 framework 维护内部状态一致性的 hook，把资产留在"schema 看着对、运行时炸"的不一致状态。

## Hidden Contract

UE 的资产数据**不是单一字段集合**，而是「显式 UPROPERTY」+「framework 维护的隐式内部状态」的复合体：

| 类别 | 例子 | 谁维护 |
|---|---|---|
| 显式 UPROPERTY | `StateClass` / `Tags` / 任何 reflected field | 直接 setter 就改对了 |
| Template / Archetype subobject | `NodeInstanceTemplate`（LogicDriver state node 上挂的 instance）/ Blueprint CDO 间接 prop | 通常 `InitTemplate` / framework 自己内部维护 |
| Property graphs / 衍生 graph 数据 | 每个 state 的 exposed property graph 集合 / Animation Blueprint 的 anim graph 子图 / Niagara 的 emitter / | `CreateGraphPropertyGraphs` / framework reconstruct |
| Auto-generated nodes | LogicDriver state class 的 event entry 节点 / Blueprint construction script 输出 | framework PostEditChange / construction script |
| Caches | LogicDriver fastpath flag / Blueprint compile cache / property lookup table | `InvalidateCaches` / 框架自己 |
| Cross-object references | Pin 引用、Variable scope binding、Class default 间接引用 | framework reconstruct |

**Editor UI 改 property 时，`PostEditChangeProperty` 会触发框架把上面这一整套同步刷新**。bypass 它 = 只第 1 行对了，下面全部留旧 / 留空 / 留半完成态。

源码锚点（LogicDriver UE 5.5，作为通用模式范例）：

`Plugins/LogicDriver/Source/SMSystemEditor/Private/Graph/Nodes/SMGraphNode_Base.cpp:330`

```cpp
void USMGraphNode_Base::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
    Super::PostEditChangeProperty(PropertyChangedEvent);

    // ↓ 这一段：跑 construction scripts，让 framework reconstruct
    if (ConstructionProjectSetting == ESMEditorConstructionScriptProjectSetting::SM_Standard)
    {
        FSMConstructionConfiguration Config;
        Config.bFullRefreshNeeded = bPostEditChangeConstructionRequiresFullRefresh;
        ISMEditorConstructionManager::Get().RunAllConstructionScriptsForBlueprint(this, Config);
    }

    // ↓ 这一段：rebuild property graphs（按当前 class 重生成 + 清理旧 class 残留）
    if (bCreatePropertyGraphsOnPropertyChange && BoundGraph && !bJustPasted)
    {
        CreateGraphPropertyGraphs();
    }

    // ↓ 这一段：清 cache（fastpath / property template lookup 等）
    FSMBlueprintEditorUtils::InvalidateCaches(FSMBlueprintEditorUtils::FindBlueprintForNode(this));
}
```

bypass 这三段直接调 `StateNode->SetNodeClass(NewClass)` + `CompileBlueprint(BP)`，得到的 `.uasset` 会出现：
- StateClass 字段对了 ✅
- NodeInstanceTemplate 也换对了（`SetNodeClass` 内部调 `InitTemplate` 顺手做了）✅
- **但** property graphs 没刷 ❌、construction script 没跑 ❌、cache 没 invalidate ❌

编译能过，但运行时 SM 评估走到没刷的部分就死循环。

## 三个判断问题（开工前必答）

对每一个要改的 property，**写代码前问**：

### Q1: 这个 property 所在 class 有 `PostEditChangeProperty` 监听吗？

```bash
# 工具：用 ripgrep 验
rg "PostEditChangeProperty" path/to/owning/class.cpp
```

- **有**——必须走 PostEditChange 路径
- **无**——直接 setter 可以

### Q2: 改动会跨多个 framework 子系统吗？

跨子系统的信号：
- 改 **Class 引用类型** field（`TSubclassOf<T>` / `UClass*` UPROPERTY）—— 几乎必跨 template / property graph / 多处
- 改 **Graph / Schema 类**的结构（加删节点 / 改 pin 类型 / 改 Blueprint parent）
- 改 **会影响其他对象的 cached lookup** 的标识（GUID / Name / TypePath）

- **跨**——必须走 framework canonical API（`FBlueprintEditorUtils::*` / `FSMBlueprintEditorUtils::*` / `FAnimBlueprintCompiler::*` / etc.）甚至 framework 没给 API 的话**自己显式触发 PostEditChangeProperty**
- **不跨**——单 property 直接 setter 可以

### Q3: 是不是 batch 操作？

- **是**——开 `FScopedTransaction` 包整批，单个改动用 setter，**末尾一次性**触发 PostEditChange / Compile / MarkPackageDirty。不要每条改动都跑完整 hook 链（会 N 倍时间 + N 倍编译）
- **不是**——单次 PostEditChange 直接做

## 正确的 PostEditChange 触发模板

framework 没暴露 canonical helper 时（如 LogicDriver `SetNodeClass`），自己显式触发：

```cpp
StateNode->Modify();                                  // ① undo 支持
StateNode->SetNodeClass(NewClass);                    // ② 改底层字段

FProperty* PropertyRef = USMGraphNode_StateNode::StaticClass()->FindPropertyByName(
    GET_MEMBER_NAME_CHECKED(USMGraphNode_StateNode, StateClass));
FPropertyChangedEvent Evt(PropertyRef, EPropertyChangeType::ValueSet);
StateNode->PostEditChangeProperty(Evt);               // ③ ★ 关键：触发 framework 同步路径

// CompileBlueprint 留给上层调度（如果 PostEditChange 自己已经触发了 ConditionallyCompile 就别再 force compile）
```

`EPropertyChangeType` 的选项：
- `ValueSet` —— 普通的"换值"语义（最常用）
- `Interactive` —— 拖 slider 这种连续过程（**不**触发完整 reconstruction）
- `ArrayAdd` / `ArrayRemove` / `ArrayClear` —— 数组操作语义
- `Duplicate` —— 拷贝场景

选错 ChangeType 也会让 framework 跳过部分同步（比如 `Interactive` 会被很多 framework 当 "skip heavy work"）。

## UE 已知有 PostEditChangeProperty 重型 hook 的 framework

写到 / 跨这些 framework 的资产时，外部脚本默认必须走 PostEditChange 路径：

| Framework | UPROPERTY → PostEditChange 重型动作 |
|---|---|
| **LogicDriver SM** (`USMGraphNode_StateNode`) | `RunAllConstructionScriptsForBlueprint` + `CreateGraphPropertyGraphs` + `InvalidateCaches` |
| **Blueprint** (`UBlueprint`) | `FBlueprintEditorUtils::PostEditChangeBlueprint` → 标 dirty + refresh nodes + reinstance |
| **Animation Blueprint** (`UAnimBlueprint`) | Anim graph 子图同步 / 参数 binding 重建 |
| **Material** (`UMaterial`) / **Material Function** | shader recompile + parameter cache refresh |
| **Niagara** (`UNiagaraSystem` / `UNiagaraEmitter`) | emitter 重 compile + dependency graph 重建 |
| **DataTable** (`UDataTable`) | RowMap 重建 + RowStructure 一致性校验 |
| **GameplayAbility** (`UGameplayAbility` 子类) | AbilityTags / Cost / Cooldown effect 关联 cache |
| **AssetUserData** | 通常自己写 PostEditChange 维护派生数据 |
| 任何你自己的 plugin 里 **重写过 `PostEditChangeProperty`** 的 class | 同上 |

未列出的 framework / 自己定义的简单 UPROPERTY（`FString` `FName` `int` 之类）通常不需要——但开工前还是先 grep `PostEditChangeProperty` 验一遍。

## Anti-Patterns

### 1. 直接 setter + 立即 CompileBlueprint

```cpp
// ❌ bypass framework hooks
StateNode->SetNodeClass(NewClass);
FKismetEditorUtilities::CompileBlueprint(Blueprint);
```

编译时 BP 数据已经处于"半新半旧"状态，bytecode 把不一致烙进去，运行时炸。

### 2. 多个改动各自触发 PostEditChange

```cpp
// ❌ N 次 PostEditChange = N 次 construction script + N 次 reconstruct
for (auto& Node : Nodes)
{
    Node->StateClass = NewClass;
    Node->PostEditChangeProperty(Evt);   // N 次
}
```

Batch 场景应该批量改字段 + 末尾**一次** PostEditChange（或者末尾触发 framework 的批量 refresh API）。

### 3. 假设 "schema 没错就 OK"

外部脚本写完，跑 BP Compile 报 success / 无 warning → 以为 OK。但 PostEditChange 同步的是**编译能看到但不报错**的隐式内部状态，没跑的话编译"成功"是假象。

**唯一验证**：editor 内 reload + PIE 实跑流程。schema-only 检查（编译 success / 无 warning）**不算验证**。

### 4. 撞坑后只 in-memory revert

发现 bug 想"撤销"，又用同样 bypass-PostEditChange 的方式把 property 改回去。结果：又跑一遍同样的损伤循环，新一轮 schema 改 + framework 状态又没刷，**累积更多脏数据**。

正确处置：**file-level revert（git checkout / p4 revert）**回到资产已知好的版本，然后修脚本走 PostEditChange 后重做。

## 验证 Discipline

外部脚本写完资产后**强制下列验证**才能 claim done：

1. **关闭并重新打开 asset editor**——加载磁盘版本，排除"in-memory 状态对但磁盘错"
2. **跑一次会触发完整 PostEditChange 路径的 UI 操作**（比如手 toggle 一个无关 UPROPERTY 再 toggle 回来）——看 framework 有没有报 warning / 强制 reconstruct
3. **PIE 实跑相关流程**——schema 编译 success ≠ 资产 OK

省略上面任何一步，bug 都可能藏到 commit 之后。

## 项目实例参考

BattleDemo 项目 R2 (2026-05-20) 自定义 MCP 命令 `set_logicdriver_state_node_class`：

- 实施只调了 `StateNode->SetNodeClass(NewClass)` + `FKismetEditorUtilities::CompileBlueprint(Blueprint)`，**跳过 `PostEditChangeProperty`**
- 18 个 state 的 `StateClass` 全部成功改为 `UCombatSkillState`（schema 层面正确）
- 编译 success 无 warning
- PIE 装 Sword 按左键 → "Infinite loop detected" 多个 BP 死循环错误
- 即使用同 MCP 命令 in-memory revert StateClass 回 default `SMStateInstance`，bug 仍在（property graphs / construction script / cache 全部残留)
- **唯一恢复路径**：`p4 revert SwordActionSM.uasset` 拿回 pre-M4 版本
- 根因：bypass `PostEditChangeProperty` → LogicDriver framework 维护的 property graphs / construction script 输出 / cache 没刷 → 运行时跑到不一致部分死循环 → BP detector 兜底

详 BattleDemo 项目 `Docs/sessions/2026-05-21-mcp-write-path-postmortem.md`（若存在）/ R2 result.md Known Limitations。

## 相关 Guidelines / Skills

- [`skills/ue/unrealmcp-usage/SKILL.md`](../../skills/ue/unrealmcp-usage/SKILL.md) "Extending UnrealMCP" —— MCP 命令扩展场景的具体工艺（含本规则的 LogicDriver 实例 + 模板）
- [`guidelines/code/validation.md`](../code/validation.md) "Adversarial Mindset" —— "tests passing ≠ behavior correct"，这里"compile success ≠ asset OK"是同类原则的 UE 版本
- [`guidelines/ue/details-customization-prefer-reflection.md`](details-customization-prefer-reflection.md) —— 同向 hidden contract：UE PropertyEditor 内部很多状态绑定在 PostEditChangeProperty 走过的路径上
- [`skills/ue/ue-settings-persistence/SKILL.md`](../../skills/ue/ue-settings-persistence/SKILL.md) "嵌套 UObject 集合 PostEditChangeProperty 同步 pattern" —— 项目内 UPROPERTY 也用类似双轨同步，跟本条是同形态在不同 layer 的应用
