# UE Settings 持久化的隐式约束

先确定保存目标：项目共享配置要进入版本控制中的 `Config/Default*.ini`；个人偏好等用户配置则按项目要求保存在用户位置。下文的共享配置配方不能泛化成所有持久化场景都必须写 `Default*.ini`。每资产 metadata 与 ini 配置是另一类需求，见 `AssetRegistrySearchable` 节。

## 适用范围与证据

- 主要案例是 DialogueSystemSample v0.5.4 的共享配置修复，原项目 commit 为 `afc1771`；本仓促升提交 `d54ea71`（2026-05-11）还记录了原项目回顾 `DialogueSystem plugin Docs/Reports/2026-05-11-line-and-localization-retrospective.md`。这些是证据定位，不代表本仓包含该项目或已经重跑它。
- 原记录未明确注明这组持久化结论对应的 UE 版本。调用目标、类标志、checkout 行为和嵌套对象配方须对照当前版本与项目；不能从邻近本地化案例的版本推定本节也已验证。
- 核验时记录引擎版本、配置类及标志、实际调用和写入文件，重启后读回；共享配置还要确认所需改动确实进入版本控制。本文“验证 checklist”用于定位这些条件；本次只整理范围和来源，未运行 UE 或逐条核对引擎实现。

## 项目共享配置的写入检查

原项目为将字段写入共享的 `Config/Default*.ini` 采用以下做法；这份配方不替代对当前类实际写入结果的检查：

1. **字段检查 `UPROPERTY(config)`**；宿主类的 `Config` / `DefaultConfig` 与字段条件分别按下方 checklist 检查。
2. **原案例用 `Object->TryUpdateDefaultConfigFile()` 修正写入目标**；不能反推所有无参 `SaveConfig()` 调用都写错。

`AssetRegistrySearchable` 用于下文的每资产 metadata 场景，与 `config` 正交，不是写入项目 ini 的第三个必要条件。

## 原共享配置案例中的无参 `SaveConfig()` 误用

原项目记录中的 `Config = Game` 配置类调用无参 `SaveConfig()` 后写到了用户配置位置。下表保留该记录的路径说明；类标志也影响目标（见下方 checklist 中的 `DefaultConfig`），不能把该表当成所有配置类和引擎版本的固定结果：

| 调用环境 | 原记录所述路径（采用前按当前类核对） |
|---|---|
| Editor 跑时（开发机）| `<Project>/Saved/Config/<Platform>/Game.ini` —— **user-level，每个 dev 自己的本地文件，不入 git/P4** |
| 命令行 commandlet 跑 | 同上 |
| Packaged build 跑 | platform-specific 的 user save dir 下的 Game.ini |

原案例的问题是：目标本来是项目共享配置，实际文件却没有进入版本控制。本机看起来“已保存”，换台机器或到 CI 就缺少这份配置。判断是否修复应检查实际写入文件，而不是仅凭调用名判断。

## 项目共享配置的写盘配方：`TryUpdateDefaultConfigFile`

```cpp
// 原项目目标是共享配置；该类此次调用后实际写到了用户 Game.ini，未进入版本控制
Settings->LineDatabase = NewDatabasePath;
Settings->SaveConfig();

// 原项目改用此调用写入共享默认配置；采用时仍需检查当前类的实际目标文件
Settings->LineDatabase = NewDatabasePath;
Settings->TryUpdateDefaultConfigFile();
```

原资料对 `TryUpdateDefaultConfigFile()` 的实现路径与项目结果作了以下记录；本次未逐条核对，采用前应检查目标版本、配置类与 SourceControl 环境：
- 走 `FConfigCacheIni::SetXxx` 直接写 `Config/Default<Category>.ini`
- 自动调 SourceControl checkout（编辑器交互模式下；commandlet 模式可能需要手动 checkout）
- 写完文件 mtime 改变 → git / P4 status 会显示改动 → dev commit 进仓库

**用户配置场景**：个人偏好、本机调试开关或不想入仓库的路径配置，不应为了套用上述配方而改写项目默认配置。选择调用前确认当前类的实际写入目标；不要仅因使用了无参 `SaveConfig()` 就判定为缺陷。

## `UPROPERTY(config)` 验证 checklist

接手陌生 codebase 想“为什么这个 setting 改了不持久化”时，先明确共享配置还是用户配置，再检查：

1. UPROPERTY 上有没有 `config` flag？
   ```cpp
   UPROPERTY(EditAnywhere, Config, Category = "Foo")
   FString MySettingPath;
   ```
   缺了 `Config` → SaveConfig 不写
2. 宿主类的 `UCLASS` 有没有 `Config = <Category>` ？
   ```cpp
   UCLASS(Config = Editor, DefaultConfig)
   class UMyPluginSettings : public UDeveloperSettings
   ```
   缺 `Config = ...` → UE 不知道写哪个 ini
   核对 `DefaultConfig` 对当前类保存目标的影响，不凭这段声明示例认定无参调用必然写用户目录。
3. 字段类型是不是 UPROPERTY 反射支持的？
   - `TArray<UObject*>` / `TMap` 等容器要 each element 也是 UPROPERTY-reachable
   - 嵌套 UObject 不会自动深序列化——其内部字段如果是 config 也要看那 UObject 自身的 Config category
4. 真正的 ini 文件路径是不是按预期？下列是**项目默认配置**目标；用户配置不能用这张清单判错：
   - `Config = Engine` → `Config/DefaultEngine.ini`
   - `Config = Editor` → `Config/DefaultEditor.ini`
   - `Config = Game` → `Config/DefaultGame.ini`
   - 自定义 Category → `Config/Default<Category>.ini`

## AssetRegistrySearchable：原项目的每资产 metadata 用法

需要持久化"`UObject` 内嵌的 `FName` / `FString` / 标量 metadata"，且想让 Asset Registry rename / move 时自动跟随时：

```cpp
UPROPERTY(VisibleAnywhere, AssetRegistrySearchable, Category = "Foo")
FName MyAssetId;
```

原项目用 `AssetRegistrySearchable` 将该 UPROPERTY 暴露为 AR tag，并通过 `FAssetData::GetTagValueRef<FName>` 读取；原记录称资产重命名 / 移动后无需另维护 mirror 表。采用这份经验时应检查目标版本与资产类型的 tag 更新结果，不能由该案例推定所有 metadata 都自动保持最新。

典型应用：
- DA 上的"业务 ID"字段（如 DialogueId / RecipeId / QuestId）
- "审核状态" bool 标记（如 `bReviewed`）—— Overview Panel 可以直接 query AR tag，不 force-load asset

**特别注意**：`AssetRegistrySearchable` 跟 `config` 是正交的两个机制。
- `config` 让字段持久化到 ini 文件（per-class，不 per-instance）
- `AssetRegistrySearchable` 让字段进 AR tag（per-instance，跟 asset 走）

混用两个 flag 在同一字段是合法的但通常没意义——`config` 的 per-class 跟 `AssetRegistrySearchable` 的 per-instance 语义不同。

## 特殊路径：嵌套 UObject 集合

原资料针对 `TArray<UObject*>` / `TMap<FName, UObject*>` 元素有 config 字段、但嵌套值未按期望保存的情形记录了以下配方。先复现当前类的保存问题，再判断是否需要它：

- 外层 UObject 暴露一个**导出函数**（如 `RebuildIndexFromObjects()`）把每个元素的关键字段抽到一个**平铺的** `UPROPERTY(config)` 容器（例：`TArray<FStructWithConfigFields>`）
- 修改时同步更新两份
- 用 `PostEditChangeProperty(空 event)` 触发外层的 sync 逻辑

这是 UE engine 内部对 `ULocalizationSettings` 的 `GameTargetSet` ↔ `GameTargetsSettings` 双轨设计的原因——前者 runtime 操作的对象层，后者是 `UPROPERTY(config)` 的扁平镜像，靠 `PostEditChangeProperty` 同步。具体见 `guidelines/ue/localization-pitfalls.md` Trap 4。

## Failure Symptoms

按"症状 → 怀疑 trap"排查：

| 症状 | 怀疑 |
|---|---|
| Editor 里改 setting 看起来生效，关掉重开值丢失 | 检查字段与类的配置标志，以及实际写入和读回目标；不能仅凭文件位于 user-level 判错 |
| Dev A 本机配的 setting，Dev B / CI 没看到 | 实际写到了 user-level，所需共享配置没入 `DefaultXxx.ini` |
| `Config/DefaultGame.ini` 改了但运行时没读到 | 字段类型不是 UE 反射支持的 / 配置覆盖被更高优先级 ini（`<Platform>Game.ini`）盖了 |
| Asset rename 后 AR 查不到 / mirror 表不一致 | 该字段没 `AssetRegistrySearchable` flag → 项目自己另维护一份 mirror，rename 没同步 |

## 项目实例参考

DialogueSystemSample 插件 v0.5.4 修这一组 trap：

- `UDialogueSettings::LineDatabase` UPROPERTY 字段持久化丢失。Root cause: `OnRebuildLocalizationClicked` 和 `DialogueDatabaseSetup::WriteSettings` 调 `Settings->SaveConfig()` 无参版，只写 user-level `Saved/Config/.../Game.ini`，不写项目入 P4 的 `Config/DefaultGame.ini`。Fix: 改 `Object->TryUpdateDefaultConfigFile()`，自动 P4 checkout
- `UDialogueAsset::DialogueId` / `bReviewed` 走 `UPROPERTY(VisibleAnywhere, AssetRegistrySearchable)`：DA Overview Panel 直接读 FAssetData tag，不 force-load asset，几百 DA 也 cheap。AR rename DA 时 DialogueId 自动跟。Phase 2 design §3.2.1

commit 锚点：`afc1771`（v0.5.3 → v0.5.4）。

## 相关 Guidelines

- `guidelines/ue/localization-pitfalls.md` Trap 4 —— `ULocalizationTargetSet::TargetObjects` 不是 `UPROPERTY(config)`，要走 PostEditChangeProperty trick 同步到 `GameTargetsSettings`（是本文 "嵌套 UObject 集合" 节的典型实例）
- `guidelines/ue/asset-definition-can-duplicate-limit.md` —— DA 复制时 UPROPERTY 值的处理跟 AssetRegistrySearchable 配合
- `guidelines/code/validation.md` —— 验证 setting 改动是否真持久化的方法
