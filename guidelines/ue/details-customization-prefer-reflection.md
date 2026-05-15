# UE Details Customization：能用反射不要写 Customization

## 核心规则

UE Details 面板的 widget 渲染**优先靠 UPROPERTY 反射驱动**——UE 自带的 default widget 已经
从 `FProperty` / `FClassProperty` / `FObjectProperty` 等反射信息生成正确的 widget（含下拉
过滤 / 类型校验 / 读写路径 / undo / 持久化）。**能用反射约束的事情不要在 `IDetailCustomization`
里手写实现**。

## Hidden Contract: `FClassProperty::MetaClass` UHT 编译期固化

`TSubclassOf<T> Field;` 字段，UHT 在编译期把 `T` 写到 `FClassProperty::MetaClass`。
Details default widget (`SPropertyEditorClass.cpp`) **直接读这个 C++ struct 字段**
决定 ClassViewer 下拉的根类，**不读 runtime instance metadata**。

源码锚点（UE 5.5）: `Engine/Source/Editor/PropertyEditor/Private/UserInterface/PropertyEditor/SPropertyEditorClass.cpp`

```cpp
if (FClassProperty* ClassProp = CastField<FClassProperty>(Property))
{
    MetaClass = ClassProp->MetaClass;   // ← 编译期写死，runtime 改不动
    bAllowAbstract = Property->GetOwnerProperty()->HasMetaData(TEXT("AllowAbstract"));
    ...
}
```

含义：

| 设想做法 | 实际行为 |
|---|---|
| `CondHandle->SetInstanceMetaData(TEXT("MetaClass"), ...)` | default widget 不读此 key，**不生效** |
| `CondHandle->SetValue(const UClass*)` 写 TSubclassOf 字段 | overload resolution 不稳，写入可能静默失败 |
| 想让基类 `TSubclassOf<UBase>` 的下拉按上下文动态收窄 | 撞 UE PropertyEditor 内部 API 边界 case，读写均不稳 |

## 决策表

| 需求 | 是否需要 Customization |
|---|---|
| 下拉只列某基类的派生 | ❌ 不需要 —— UPROPERTY 声明为 `TSubclassOf<那个基类>`，UHT 自动生成正确 MetaClass |
| 下拉过滤实例（不是类） | ❌ 不需要 —— `UPROPERTY(meta=(AllowedClasses="..."))` 或 `MustImplement` |
| 隐藏某些字段 | ❌ 不需要 —— `UPROPERTY(meta=(EditCondition="..."))` |
| 字段值改变联动改别的 | ⚠️ 可能需要 —— 优先 `PostEditChangeProperty` |
| 加自定义按钮 / 诊断信息 / 非反射可表达的复杂 widget | ✅ 需要 Customization |
| 同一字段在不同 owner instance 上要不同根类 | ⚠️ **数据层问题**：拆派生类让每个派生类各自 typed field，比 Customization 稳得多 |

## Anti-Pattern：基类承载 union 类型 + Customization 动态收窄

```cpp
// 反 pattern：基类承载所有派生 union，Customization 在 UI 层挑根类
UCLASS()
class UMyWrapper : public UEdGraphNode {
public:
    UPROPERTY(EditAnywhere)
    TSubclassOf<UBaseEvaluator> ConditionClass;   // 顶层基类，下拉混所有派生
};

// + IDetailCustomization 拿 owner 上下文动态过滤下拉根类
// → 撞 UE 内部 API 边界 case（写入路径 / 读路径 / 持久化 / undo 各踩一遍）
```

**正解：数据层分流**

```cpp
UCLASS(Abstract)
class UMyWrapper : public UEdGraphNode {
public:
    virtual TSubclassOf<UBaseEvaluator> GetConditionClass() const { return nullptr; }
    virtual bool HasCondition() const { return GetConditionClass() != nullptr; }
};

UCLASS()
class UMyVisibilityWrapper : public UMyWrapper {
public:
    UPROPERTY(EditAnywhere)
    TSubclassOf<UVisibilityBase> ConditionClass;  // typed，UHT 自动把 MetaClass 写成 UVisibilityBase
    virtual TSubclassOf<UBaseEvaluator> GetConditionClass() const override { return ConditionClass; }
};

UCLASS()
class UMyFlowWrapper : public UMyWrapper {
public:
    UPROPERTY(EditAnywhere)
    TSubclassOf<UFlowBase> ConditionClass;
    virtual TSubclassOf<UBaseEvaluator> GetConditionClass() const override { return ConditionClass; }
};
```

- 派生类各自 typed 字段 → UHT 编译期分别写 `FClassProperty::MetaClass` 为 `UVisibilityBase` / `UFlowBase`
- UE default widget 自动按各自 MetaClass 收窄下拉
- Schema / Factory 创建 wrapper 时按上下游 runtime 类型选具体派生类
- **Zero customization**。读写 / 持久化 / undo / transaction 全走 UE 标准实施

## Failure Symptoms（怎么发现走错方向）

写 Class property customization 撞下列任一即应停下，回到数据层评估：

- `SetValue(const UClass*)` 调用后 widget 不刷新 / 值不持久化
- `SetInstanceMetaData("MetaClass", ...)` 不影响下拉根类
- 自己写 `SClassPropertyEntryBox` 的 `OnSetClass` lambda 但读不到最新值
- 切 None / 切已选 BP / 切到另一 BP 都不响应
- 多选 / undo / redo 路径行为漂

**任一一次出现就停。** 不要换 UI 层 API 再试一次——见 [`workflow/agent-lifecycle.md` "What 'change approach' actually means"](../workflow/agent-lifecycle.md) "换 approach = 换 layer 不是换 API"。

## 同一原则适用其它反射字段

不止 ClassProperty。类似的"反射 vs customization"决策也适用：

| 字段类型 | UHT 反射自动给的功能 | 用 customization 重写的 anti-pattern |
|---|---|---|
| `TObjectPtr<T>` / `T*` | 资产选择器按 T 派生过滤；asset picker 路径 | 自己写 asset picker widget |
| `TSoftClassPtr<T>` / `TSoftObjectPtr<T>` | soft class viewer 按 T 派生过滤 | 自己包装 ClassViewer |
| `FName` + `AllowedClasses` meta | enum-like 下拉 | 自己写 ComboBox + 维护选项列表 |
| `FInstancedStruct` (UE 5.0+) | 多态 struct 编辑器（按 base type 派生过滤） | 自己写多态 struct 编辑器 |
| `TSet<TSubclassOf<T>>` | 多选 class picker | 自己写 multi-select |

发现自己在 customization 里手写"读 owner 类型 → 动态生成 widget"逻辑时，**先问**：能不能让数据类型分流，让 UE default widget 自动派？

## 项目实例参考

DialogueSystemSample 插件 2026-05-15 踩穿这条：试图给 `UStateGraphTransitionNode.ConditionClass`
（顶层 `TSubclassOf<UConditionEvaluator>`）加 Details Customization 按边语义动态收窄
visibility / flow 派生：

- v1: 自己 `CustomWidget` + `SClassPropertyEntryBox` + `OnSetClass` 调 `SetValue(UClass*)` → 写入静默失败
- v2: 换 `SetInstanceMetaData("MetaClass", ...)` → 下拉根类不变
- v3: 换 `HideProperty + AddCustomRow + SetValueFromFormattedString` → 切 None / 切已选 BP 都失效

3 版 customization 都撞 UE 内部 API 边界 case。回退到数据层拆 `UDialogueVisibilityTransitionNode`
/ `UDialogueFlowTransitionNode` 两个派生，各自 typed `ConditionClass` 字段，UHT 自动写 MetaClass
→ UE default widget **0 customization** 完成下拉分流。

详 plan 文档（agent-private）`plans/2026-05-15-wrapper-transition-split.md`。

## 相关 Guidelines / Techniques

- [`guidelines/workflow/agent-lifecycle.md`](../workflow/agent-lifecycle.md) "What 'change approach' actually means" —— 同 customization 反复失败时按 layer 换 approach 的判断
- [`guidelines/ue/graph-editor-constraints.md`](graph-editor-constraints.md) —— UE graph editor 其它 hidden contract
- [`guidelines/ue/blueprint-auto-override-api.md`](blueprint-auto-override-api.md) —— UE BP 程序化创建的另一个反射 hidden contract（`AddFunctionGraph` 模板参数）
- [`guidelines/code/reuse-before-implementing.md`](../code/reuse-before-implementing.md) —— 反射机制就是 framework 提供的"现成 helper"，写 customization 前应该确认是不是绕开了它
