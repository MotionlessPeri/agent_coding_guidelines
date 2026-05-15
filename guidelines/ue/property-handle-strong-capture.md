# UE IDetailCustomization：`IPropertyHandle` 必须 strong-ref capture 进 lambda

## 核心规则

`IDetailCustomization::CustomizeDetails` 里通过 `DetailBuilder.GetProperty(TEXT("X"))` 拿到的 `TSharedRef<IPropertyHandle>` 是**函数 scope local**。该 handle capture 进**任何被 widget 持久持有的 lambda**（`Text_Lambda` / `ColorAndOpacity_Lambda` / `Visibility` attribute / button `OnClicked` 等）时，**必须显式拷一份 `TSharedPtr` strong ref 然后 by-value capture**，**不能用 `TWeakPtr` capture**。

```cpp
// ✅ 正确：strong ref by-value capture
TSharedRef<IPropertyHandle> Handle = DetailBuilder.GetProperty(TEXT("LineId"));
TSharedPtr<IPropertyHandle> StrongHandle = Handle;  // refcount +1

Category.AddCustomRow(...)
    .ValueContent()
    [
        SNew(STextBlock).Text_Lambda([StrongHandle]()
        {
            FName Cur;
            if (StrongHandle.IsValid()) StrongHandle->GetValue(Cur);
            return FText::FromName(Cur);
        })
    ];

// ❌ 错误：weak ref → CustomizeDetails 返回后立即失效
TWeakPtr<IPropertyHandle> WeakHandle = Handle;
Category.AddCustomRow(...)
    .ValueContent()
    [
        SNew(STextBlock).Text_Lambda([WeakHandle]()
        {
            FName Cur;
            if (auto H = WeakHandle.Pin()) H->GetValue(Cur);  // H 永远 null
            return FText::FromName(Cur);
        })
    ];
```

## 为什么

```
CustomizeDetails(IDetailLayoutBuilder& DetailBuilder)
{
    TSharedRef<IPropertyHandle> Handle = DetailBuilder.GetProperty(...);
    //                          ↑ refcount = 1 (本 scope local)

    TWeakPtr<IPropertyHandle> Weak = Handle;
    //                         ↑ 不增 refcount, 只观察

    SomeWidget.Text_Lambda([Weak](){ ... });
    // widget 持久持有 lambda by 值
    // lambda 内 Weak 跟着 widget 一样长寿

    // ← 函数返回, Handle (TSharedRef local) 析构 → refcount-1 → 0 → handle destruct
}

// 之后 widget tick:
Weak.Pin()  // → 返 null (refcount 早已归 0)
H->GetValue(Cur)  // 不跑
Cur 保持初始值 NAME_None / 0 / FString() / etc.
// → lambda 静默 return default value, UI 显示永远是"未设置"
```

**PropertyEditor 框架内部不持 strong ref** 兜底——`GetProperty()` 返回的 handle 生命周期完全交给 caller (customization) 管理。这是 UE 的 design 决策，**没在 API doc 明说**——只能从踩坑或读 engine source `PropertyEditor` module 内部推断。

## 失败症状

UI 显示永远是"property 默认值"，无视实际 UPROPERTY 值：

- `FName` UPROPERTY → 显示 `None` (或自定义 "Empty" / "Ad-hoc" 之类的 NAME_None 兜底分支)
- `int32` / `float` → 显示 0
- `FString` → 显示空字符串
- `bool` → 显示 false
- `FText` → 显示 empty

**特点**：
- Customize 函数体内立即跑 `Handle->GetValue()` **能拿到正确值**（refcount 还没归 0）
- 函数返回后 widget tick 跑 lambda **永远拿到 default**
- 调试时容易误判成"数据本身就是 default"——实际是 UI 拿不到数据
- **可能只对某些节点类型显现**：如果 customization 别处有显式 strong-ref capture（比如另一段 lambda 拷了一份 TSharedPtr），就**偶然**兜底；某些 code path（早 return / 分支跳过那段）的节点类型才暴露 bug

## 诊断技巧

加临时 UE_LOG 在 lambda 内 dump 三个信号：

```cpp
auto MyLambda = [WeakHandle]()
{
    FName Cur;
    bool bAlive = false;
    bool bGetOk = false;
    if (TSharedPtr<IPropertyHandle> H = WeakHandle.Pin())
    {
        bAlive = true;
        FPropertyAccess::Result R = H->GetValue(Cur);
        bGetOk = (R == FPropertyAccess::Success);
    }
    UE_LOG(LogTemp, Warning,
        TEXT("[diag] Alive=%d GetOk=%d Cur=%s"),
        (int32)bAlive, (int32)bGetOk, *Cur.ToString());
    // ...
};
```

跑一次 select 节点 → 看 widget tick log:

| Alive | GetOk | Cur | 诊断 |
|---|---|---|---|
| 0 | 0 | None | **handle 已 destruct → 本 guideline 的 bug** |
| 1 | 0 | None | handle 活但 GetValue 失败（property 不存在 / 多选不一致）|
| 1 | 1 | <expected value> | 正常 |

## 例外：单次 callback 不持久

如果 lambda **只在 customization 内同步跑一次**（比如 customization 函数体内立即 invoke 求初始 visibility），weak 也 OK——因为 lambda 跟 sharedref 同时 alive。但**别这么写**：维护成本高（reader 必须分清"这条 lambda 持久 vs 一次性"），统一 strong ref by value 更安全。

## 类似 hidden contract 在 IDetailCustomization 里的其它 corner

| 场景 | 必须 strong-ref capture | 不 strong 的后果 |
|---|---|---|
| `GetProperty().Text_Lambda([H](){ H->GetValue(...) })` | ✅ | 显示 default |
| `OnClicked` button lambda | ✅ | button 点了没反应 |
| `Visibility` attribute lambda | ✅ | widget 永远 collapsed / visible（default 状态）|
| `IsEnabled_Lambda` | ✅ | button 永远 disabled / enabled（default 状态）|
| Customization 函数内部立刻 invoke 的 lambda | weak 也 OK，但建议统一 strong | / |

## 项目实例参考

DialogueSystem 插件 `FDialogueNodeLineIdCustomization::CustomizeDetails` 用 TWeakPtr capture LineId handle 进 GetState lambda 半年没暴露，因为同 customization 处理 Speech / Choice 节点时跑到 Speaker section 末段**显式拷了一份 TSharedPtr** 进 Speaker section lambdas，间接保活同一个 LineId handle —— Speech / Choice 永远 OK。ChoiceItem 节点（M2 split 新加）路径在 Speaker section **之前**早 return，没拷 strong ref → ChoiceItem 上 LineId 显示永远 `None` (Status row 显黄色 "Ad-hoc")。

修复 commit: `1b2782e` (2026-05-15) —— weak ref 改 strong by-value capture，Speaker section 重复 declaration 删。同 customization 内统一 strong, 消除"两套 capture 写法"歧义。

## 相关 Guidelines

- [`guidelines/ue/details-customization-prefer-reflection.md`](details-customization-prefer-reflection.md) — 决定是否 write customization 之前先用反射；本条管 customization 内部 capture 写法
- [`guidelines/code/validation.md`](../code/validation.md) "Adversarial Mindset" — UI 显示问题不能只靠"代码看着对"，必须实测 widget runtime 状态（widget tick log）
- [`skills/ue-reference-engine-source/SKILL.md`](../../skills/ue-reference-engine-source/SKILL.md) — UE engine source `PropertyEditor` module 是本 hidden contract 的源头；UE doc 没说，必须读源码 + 实测
