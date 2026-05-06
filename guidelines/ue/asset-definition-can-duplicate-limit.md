# `UAssetDefinition::CanDuplicate` 拦不住所有复制路径

## 核心规则

`UAssetDefinition::CanDuplicate`（UE 5.0+）/ `FAssetTypeActions::CanDuplicate`（旧 API）**只在 Content Browser 通过 Duplicate 命令时被调**。如果你需要"禁止某种 asset 被复制 / 复制时强制改写状态"，**必须双层防御**：

- **第 1 层：`CanDuplicate` override** —— 拦 Content Browser Duplicate 命令路径（Ctrl+W / 右键 Duplicate / 拖拽复制）
- **第 2 层：`UObject::PostDuplicate` override** —— 兜底所有绕过 CanDuplicate 的路径（Copy+Paste / Migrate / 程序化 `DuplicateObject`）

两层缺一不可。

## 为什么

`UAssetDefinition::CanDuplicate` 只接入 Content Browser 的 Duplicate 命令分发——UE Asset Editor framework 在你点 Duplicate / Ctrl+W / 拖拽复制时调它做 pre-flight check。

但 **以下复制路径 100% 绕过 CanDuplicate**：

| 路径 | 触发方式 | 走不走 CanDuplicate |
|------|---------|---------------------|
| Content Browser Duplicate 命令 | 右键 → Duplicate / Ctrl+W / 拖拽时按 Alt | ✅ 走 |
| **Copy + Paste** | Ctrl+C → Ctrl+V | ❌ **绕过** |
| **Migrate Asset...** | 右键 → Asset Actions → Migrate... | ❌ **绕过** |
| **程序化 `DuplicateObject<T>(...)`** | C++ / Blueprint 代码直接调 | ❌ **绕过** |
| **Save As** | File menu → Save As | ❌ **绕过**（虽然不算严格 duplicate，但产生新 asset） |

CanDuplicate 单层防御 → Copy+Paste 复制出来的 asset 跳过你的 pre-flight check → 状态就错了。这是 UE framework 的 hidden contract，引擎自己的 docs 没明说。

## 双层防御 Code Template

### 第 1 层：CanDuplicate override

```cpp
// In your UAssetDefinition_<YourAsset>.cpp
FAssetSupportResponse UAssetDefinition_MyAsset::CanDuplicate(const FAssetData& InAsset) const
{
    // Fast path: AR tag（性能 critical —— Content Browser context menu / hover 频繁调 polling）
    const FString StateTag = InAsset.GetTagValueRef<FString>(GET_MEMBER_NAME_CHECKED(UMyAsset, StateField));
    if (!StateTag.IsEmpty() && /* StateTag 表明拒绝复制 */)
    {
        return FAssetSupportResponse::Error(LOCTEXT("CannotDuplicate", "...理由..."));
    }

    // Slow path: AR tag 空（dirty / 未 save 的 asset）→ load 出来看 UPROPERTY 兜底
    if (UMyAsset* Asset = Cast<UMyAsset>(InAsset.GetAsset()))
    {
        if (Asset->ShouldRejectDuplicate())
        {
            return FAssetSupportResponse::Error(LOCTEXT("CannotDuplicate", "...理由..."));
        }
    }
    return FAssetSupportResponse::Supported();
}
```

**Fast path / Slow path 双段必须**：Content Browser context menu / hover 时 CanDuplicate 被频繁 polling，纯 slow path（每次 GetAsset() force load）会卡 UI；纯 fast path 又 cover 不到刚 save 但 AR tag 还没 publish 的场景。

### 第 2 层：PostDuplicate override

```cpp
// In your UMyAsset.cpp
void UMyAsset::PostDuplicate(EDuplicateMode::Type DuplicateMode)
{
    Super::PostDuplicate(DuplicateMode);

    // PostDuplicate 是 Copy+Paste / Migrate / 程序化 DuplicateObject 的唯一兜底。
    // 策略选一：
    //   (a) 拒绝 + crash / log + 把 asset 删掉（暴力）
    //   (b) **降级 + 内容保留**（推荐）—— 把"不能复制"的状态字段清空，但保留所有数据
    //       让 dev 复制完得到一个"干净"asset，可以自由编辑作为变种

    if (/* 这是要拒绝复制的状态 */)
    {
        // 推荐策略 (b) 示例：
        // 1. 把"身份字段"清空（如本对象指向某个外部 ID）
        // 2. 把外部 ID 引用的内容快照到本对象本地字段（保留 runtime 可读）
        // 3. 状态降级为 "free" / "ad-hoc"
        SnapshotExternalContentToLocal();
        ClearIdentityField();
    }
}
```

策略 (b) 优于 (a)：dev 复制 asset 当模板的需求合理，强行拒绝（删了 / crash）UX 太差。降级 + 保留数据让 dev 拿到可用结果。

## 何时应用

判断你需要双层防御：

- 你的 asset 有"独占某种身份 / 状态"的不变式（`DialogueId` 必须唯一、`ConfigSlot` 必须只有一份等）
- 你不希望 dev 复制后产出"两份独占身份"的 asset
- 你需要保证 **任何复制路径**（不只 Duplicate 命令）都符合不变式

不需要双层防御的场景：

- Asset 没有独占身份不变式（普通 DataAsset，复制几份没问题）
- 复制时只需要给 dev 弹 confirm 提示（CanDuplicate 单层够，弹了 dialog 用户 cancel 就行；Copy+Paste 跳过弹窗 dev 也是有意为之）

## Failure Symptom（怎么发现没做对）

**症状 1**：dev 在 Content Browser 试 Duplicate 你的 asset → 弹错正确拒绝。但**改用 Ctrl+C / Ctrl+V**复制 → 没拦住，复制出来的 asset 跟原版有相同身份字段 → 运行时冲突 / 数据污染。

**症状 2**：dev Migrate 你的 asset 到另一个项目 → CanDuplicate 不被调 → asset 在新项目里身份冲突。

**症状 3**：你或同事写程序化创建 asset 模板的工具，调了 `DuplicateObject<UMyAsset>(...)` → 没人警告 → 产出来的 asset 状态错。

**症状 4**：dev 在 Asset Editor 里点 Save As → 新 asset 跟旧 asset 共享身份字段。

任何一种发现，**第 2 层 PostDuplicate 没实施 / 没正确处理状态**。

## 项目实例参考

DialogueSystemSample 插件的 `UDialogueAsset` 是典型案例：

- **不变式**：generated DA 持有 `DialogueId` UPROPERTY，必须 1:1 对应 DB lines 表的 DialogueID 集合。复制出 generated DA = 两个 DA 共享同一 DialogueId = 整套 import / drift gate / overview 系统全部错乱。
- **第 1 层 CanDuplicate**：`UAssetDefinition_DialogueAsset::CanDuplicate` 在 Content Browser Duplicate 路径拒绝 generated DA（fast path AR tag + slow path GetAsset 双段）。
- **第 2 层 PostDuplicate**：`UDialogueAsset::PostDuplicate` 走"降级 + 内容保留"策略——遍历每个 Node 用 `LineId` 查 DB 把 Text / SpeakerID 快照到 Adhoc UPROPERTY，然后清 Node 的 LineId + DA 的 DialogueId → 复制结果是干净 ad-hoc DA + 完整内容。

详见 `DialogueSystem/Public/Core/DialogueAsset.h` + `Private/Core/DialogueAsset.cpp` 的 PostDuplicate 注释 + `DialogueSystemEditor/Private/AssetDefinitions/AssetDefinition_DialogueAsset.cpp` 的 CanDuplicate 实施。

## 相关 Guidelines

- `guidelines/ue/graph-editor-constraints.md` — 含 `Copy/Paste Must DuplicateObject the RuntimeNode`，是**graph 节点层面**的 Copy/Paste 处理（PostPasteNode hook），跟本文档 **asset 层面** 的复制路径覆盖是不同 layer 的 hidden contract，不要混淆。
