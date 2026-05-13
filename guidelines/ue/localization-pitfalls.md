# UE Localization 工程 trap

UE 的本地化栈（StringTable / Localization Dashboard / `FText` / archive / `.locres`）有一组**没有官方文档**的硬约束，只能靠读 engine source 或踩坑发现。任何"让一段 DB / 配置驱动的文本走 UE 本地化"的工作开工前先看这一篇。

## Trap 1: `FText::FromStringTable(...).ToString()` 不是返回源串

`FText` 是变体类型，`ToString()` 行为取决于构造方式：

| 构造方式 | `ToString()` 返回 |
|---|---|
| `FText::FromString(s)` | 永远是 `s`，不受 culture 影响 |
| `FText::FromStringTable(TableId, Key)` | **当前 culture 的翻译**（命中 `.locres`）/ ST source 字段（未命中）|
| `LOCTEXT("Key", "Source")` 宏 | 同上 |

**陷阱**：如果把 `FromStringTable` 包出来的 `FText` 存进 cache 里，所有 `cache.Text.ToString()` caller 都跟着 editor / runtime culture 漂。后果会沿调用链向所有 `ToString()` 消费方扩散：

- **DB → xlsx 反向导出流程** 拿到当前 culture 翻译写回源 xlsx → silent data corruption
- **ST.uasset derive 流程** 用 `cache.Text.ToString()` dump 进 ST source 字段 → 自我污染（ST source 变成翻译值，archive 派生彻底乱）
- **文本搜索 / Picker** 按 cache.Text 匹配关键字 → 切了 culture 后搜不到

**正确做法**：
- cache 永远存源串（`FText::FromString`）
- culture-aware wrap 推到 query API 内部现包（`GetLineText` / `GetSpeakerDisplayName` 等公开 API 每次现 `FromStringTable`）
- 给"export / 字符串处理 / 任何不需要 culture-aware"的消费方专门暴露 `GetXxxSourceText(Id) -> FString` API，不让它们消费 `cache.Text.ToString()`

ST 本身有缓存，query API 现包性能影响小。

**Symmetric anti-pattern**：cache 里存 `FDateTime` 是 OK 的；存 "`FText` 已经按 locale format 过的日期字符串" 是 sin。同样的原则——渲染层变换不能进数据层。

## Trap 2: `ST.uasset` **不能**放 `Content/Localization/`

UE engine 在生成每个 Localization target 的 `GatherTextFromAssets` ini 时**硬编码**追加一条 exclude：

```ini
ExcludePathFilters=Content/Localization/*
```

源码锚点：`Engine/Source/Developer/Localization/Private/LocalizationConfigurationScript.cpp:375`（UE 5.5 / 5.6 稳定，跨 5.x 版本未变）。

UE 的硬约定：`Content/Localization/` 目录是给 archive / manifest / `.locres` **输出**用的，不应该往里塞 `.uasset`。如果把 ST 派生到这里：

1. Dashboard `Gather Text` 跑出来 Word Count = 0（ST.uasset 被 exclude 永远扫不到）
2. archive 派生为空
3. runtime 永远 fallback 到源串
4. dev 排查会非常困惑——`.uasset` 明明在那里，ini 里 IncludePath 也配了

**正确路径**：
- ST.uasset 派生到 `Content/StringTables/<Name>.uasset`（UE 标准 ST 位置）
- 你自己 plugin 的 ST 包路径用常量集中管理（`Public/Localization/LocalizationConstants.h` 等），Runtime + Editor 共享 SoT

archive JSON 仍然走 `Content/Localization/<TargetName>/<culture>/<TargetName>.archive` —— 这是 Dashboard `SourcePath/DestinationPath` 标准位置，**且** archive 不是 `.uasset` 不被上面的 ExcludePathFilters 排除。

**Setup wizard 的兼容点**：如果用户之前手动 / 旧版本 plugin 把 ST 放到 `Content/Localization/` 下，Setup wizard 重跑时应该清理掉旧 IncludePath（移除 `Content/Localization/*` wildcard），避免历史错配。

## Trap 3: `FEditorDelegates::PreBeginPIE` 不能 veto

老 PIE Gate 写法常见这种：

```cpp
// ❌ 不能这么写
FEditorDelegates::PreBeginPIE.AddLambda([](bool) {
    if (HasValidationErrors())
    {
        if (AskUserModal("Continue PIE?") == EAppReturnType::No)
        {
            GEditor->RequestEndPlayMap();
            return;  // ⚠️ 这条 delegate 不接受 veto
        }
    }
});
```

`FEditorDelegates::PreBeginPIE` 是**通知性**的，不是**可拦截**的。lambda 返回不能阻止 PIE 启动。`RequestEndPlayMap()` 在 PIE 还没真正启动时调用会走 `CancelRequestPlaySession()` 链，`TOptional` 空 deref → crash。

**正确做法**：UE 5.5+ 用 `IPIEAuthorizer` modular feature：

```cpp
class FDialoguePIEAuthorizer : public IPIEAuthorizer
{
public:
    virtual bool RequestPIEPermission(bool bIsSimulateInEditor, FString& OutReason) const override
    {
        if (HasValidationErrors())
        {
            if (AskUserModal("Continue PIE?") == EAppReturnType::No)
            {
                OutReason = TEXT("User chose abort due to validation errors");
                return false;  // ✅ 真 veto
            }
        }
        return true;
    }
};

// 注册到 modular feature manager
IModularFeatures::Get().RegisterModularFeature(
    IPIEAuthorizer::GetModularFeatureName(), &Authorizer);
```

UE 5.5 之前用 `FEditorDelegates::PreBeginPIE` + workaround（标志位 + 下一帧才拦）会更脆弱，建议升级到 5.5+ 或避开 PIE veto 需求。

## Trap 4: `ULocalizationTargetSet::TargetObjects` **不是** `UPROPERTY(config)`

程序化创建 / 维护 Localization target（如 plugin 提供"Setup Localization"一键 wizard）时常见错法：

```cpp
// ❌ 不持久化
ULocalizationTarget* Target = NewObject<ULocalizationTarget>(...);
Target->Settings.Name = TEXT("MyTarget");
TargetSet->TargetObjects.Add(Target);
Target->SaveConfig();         // 不写盘
TargetSet->SaveConfig();      // 也不写盘
```

`ULocalizationTargetSet::TargetObjects` 字段不是 `UPROPERTY(config)`，所以 `SaveConfig()` 写不出。关闭 editor 重开后 target 列表全丢。

UE 内部的 target 持久化走另一条路径：

- `ULocalizationSettings` 有 `GameTargetSet`（也是 `ULocalizationTargetSet`）
- 但 `ULocalizationSettings` 的 `UPROPERTY(config)` 是 `GameTargetsSettings`（**注意复数 s**，类型不同）
- 两者之间靠 `ULocalizationSettings::PostEditChangeProperty` 内部触发同步：把 `GameTargetSet->TargetObjects` 各 target 的 `Settings` 字段复制到 `GameTargetsSettings`，后者带 `config` flag → 写 `DefaultEditor.ini`

**正确做法**：

```cpp
// ✅ 触发 UE 内部同步路径
ULocalizationSettings* LocSettings = GetMutableDefault<ULocalizationSettings>();
ULocalizationTargetSet* TargetSet = LocSettings->GetGameTargetSet();

ULocalizationTarget* Target = NewObject<ULocalizationTarget>(TargetSet);
Target->Settings.Name = TEXT("MyTarget");
// ... 配 Gather sources / cultures / etc.
TargetSet->TargetObjects.Add(Target);

// 触发 PostEditChangeProperty 走内部同步逻辑
FPropertyChangedEvent EmptyEvent(nullptr);
LocSettings->PostEditChangeProperty(EmptyEvent);
// 现在 GameTargetsSettings 已经 sync 完，会写 DefaultEditor.ini
```

具体引用的字段名跨 5.x 版本相对稳定，但每次接触新版本先 `grep "TargetObjects\|GameTargetsSettings"` 在 `Engine/Source/Runtime/Localization/` 确认。

## Trap 5: GatherText commandlet 在 P4 / git ignore 项目下日志噪音

UE `GatherText` commandlet 默认调 `MarkForAdd` 把生成的 manifest / archive / csv / Conflicts.txt 加进 SourceControl changelist。如果项目 `.p4ignore` / `.gitignore` 把 `Content/Localization/` 排除（典型做法——这些是派生物），commandlet 会刷大段：

```
SourceControl: Error: CommandMessage Command: MarkForAdd, Error: ... - ignored file can't be added.
LogLocalizationSourceControl: Error: Failed to check out file '...'.
```

**这是 noise 不影响功能**——看最后 `GatherText completed with exit code 0` 即可。

抑制方法（如需要）：避免传 `-EnableSCC` switch（默认 commandlet 不开 SCC）。但 Localization Dashboard UI 调 commandlet 时**硬编码**加这个 switch（`LocalizationCommandletExecution.cpp:758`），无法从 ini 关。**接受 noise 是当前最现实的做法**。

## Trap 6: Translation 文件 culture 标识不验 BCP-47 格式

写 xlsx → DB / xlsx → archive 的翻译 import pipeline 时，culture 标识通常从列名 / 文件名后缀 / 行字段抽出来（如 `Text_en`、`Text_zh-Hans`）。**如果不验格式**，错的 culture 会静默入库：

| 策划列头 | DB 落进的 culture | UE Dashboard 标准 culture | 后果 |
|---|---|---|---|
| `Text_en_US` | `en_US` | `en-US` | runtime 切到 `en-US` 查不到 → fallback 源串 |
| `Text_EN` | `EN` | `en` | 同上 |
| `Text_zh-cn` | `zh-cn` | `zh-Hans` | 同上 |
| `Text_pirate` | `pirate` | （非标但合法可配）| OK，但 dev 可能想验是不是 typo |

**建议**：translator 解析列头时跑一次 simplified BCP-47 regex：

```python
import re
BCP47_RE = re.compile(r'^[a-z]{2,3}(-[A-Z][a-z]{3})?(-[A-Z]{2})?$')

def _validate_culture(culture: str) -> None:
    if not BCP47_RE.match(culture):
        warnings.append(make_warning(
            severity='warning',
            code='TRANSLATION_CULTURE_NONSTANDARD',
            message=f"culture '{culture}' 不是标准 BCP-47 格式；"
                     "runtime 切 culture 时可能查不到。常见标准: en-US / zh-Hans / ja"
        ))
```

**不阻断入库**（用户可能配了非标 culture 如 `pirate`），但要给 warning 让用户自查 typo。

## 项目实例参考

DialogueSystemSample 插件 Phase 3 本地化 ship 期间踩出 Trap 1-4 + 6，集中在 v0.5.0 → v0.5.4 修复：

- Trap 1: `UDialogueAsset` 缓存 `FDialogueLineRow.Text` 烧成 `FromStringTable` → DB→xlsx 反向导出写回英文翻译。修法 A：cache 退回 `FromString` 源串，`ULineRegistry::GetLineText` 内部 wrap。`Plugins/DialogueSystem/Source/DialogueSystem/Private/Lines/LineRegistry.cpp` cache 段
- Trap 2: `ST_DialogueLines.uasset` 派生到 `/Game/Localization/` 下 → Dashboard Word Count = 0。修法：迁到 `/Game/StringTables/`；新增 `Public/Localization/LocalizationConstants.h` 集中 8 个路径常量
- Trap 3: 老 PIE Gate 走 `FEditorDelegates::PreBeginPIE` + `RequestEndPlayMap` 链 crash。修法：UE 5.5 `IPIEAuthorizer` modular feature
- Trap 4: `SetupDialogueLocalization::EnsureDialogueTarget` 调 `Target->SaveConfig()` + `TargetSet->SaveConfig()` 不持久化。修法：触发 `ULocalizationSettings::PostEditChangeProperty(空 event)` 走内部 `GameTargetSet → GameTargetsSettings` 同步
- Trap 6: Gisei translator 的 culture 列头抽取没 validate。修法：`Scripts/Translators/Default/translate.py::_validate_culture` helper

## 相关 Guidelines

- skill `ue-settings-persistence` （`skills/ue-settings-persistence/settings-persistence.md`）—— Trap 4 是 settings 持久化的特例；通用 UPROPERTY(config) 持久化 pattern 在那篇
- `skills/ue-module-architecture/editor-runtime-separation.md` —— Trap 1 修法（query API 暴露 culture-aware wrap）也是 Editor / Runtime API 边界设计（已 promote 到 skill `ue-module-architecture`）
- `guidelines/code/validation.md` —— Trap 6 的 input validation 原则
