# UE Settings 持久化的隐式约束

任何带 Project Settings / UDeveloperSettings / 自定义 config UObject 的 UE 代码都吃这条 trap：`SaveConfig()` 看起来"会持久化"，但**写到哪个 ini 文件**完全取决于 (1) UPROPERTY 有没有 `config` flag (2) 调的是哪个 SaveConfig 重载。错配的后果是字段关掉 editor 重开就消失，但只在重开后才暴露 → ship 之后才发现。

## 核心规则三件套

要让 setting 字段**入项目仓库**（git / P4 跟踪的 `Config/Default*.ini`）：

1. **字段必须带 `UPROPERTY(config)`**（或宿主类整体 `Config = Game` + 字段无 `Transient`）。缺了 `config` flag，所有 SaveConfig 调用都白搭——值只活在内存里
2. **写盘必须用 `Object->TryUpdateDefaultConfigFile()`**，不能用 `Object->SaveConfig()` 无参版
3. **AssetRegistrySearchable UPROPERTY 让 AR rename/move 自动跟随**，无需另维护 mirror 表

## 为什么 `SaveConfig()` 无参版是陷阱

`UObject::SaveConfig()` 默认参数是 `(CPF_Config, *GetConfigFilename(this))`，写到 **GetConfigFilename 返回的 ini**。这个返回值对 `Config = Game` 的类是：

| 调用环境 | 实际写到的文件 |
|---|---|
| Editor 跑时（开发机）| `<Project>/Saved/Config/<Platform>/Game.ini` —— **user-level，每个 dev 自己的本地文件，不入 git/P4** |
| 命令行 commandlet 跑 | 同上 |
| Packaged build 跑 | platform-specific 的 user save dir 下的 Game.ini |

也就是说 `SaveConfig()` 无参版**几乎不会**写到项目仓库入版本控制的 `Config/DefaultGame.ini` / `Config/DefaultEditor.ini`。Dev 在 Editor 里点完按钮，本机看起来"已保存"，提交 PR 时 git status 干净——但其实啥都没改。换台机器 / CI 跑就缺这份配置。

## 正确写盘 API：`TryUpdateDefaultConfigFile`

```cpp
// ❌ 错：写到 user-level Game.ini，不入 git
Settings->LineDatabase = NewDatabasePath;
Settings->SaveConfig();

// ✅ 对：强制写到 Config/DefaultGame.ini（或 DefaultEditor.ini 视 Config 类别）
Settings->LineDatabase = NewDatabasePath;
Settings->TryUpdateDefaultConfigFile();
```

`TryUpdateDefaultConfigFile()`：
- 走 `FConfigCacheIni::SetXxx` 直接写 `Config/Default<Category>.ini`
- 自动调 SourceControl checkout（编辑器交互模式下；commandlet 模式可能需要手动 checkout）
- 写完文件 mtime 改变 → git / P4 status 会显示改动 → dev commit 进仓库

**何时用 `SaveConfig()` 无参**：仅当你**明确想要 user-level 配置**（个人偏好 / 本机调试开关 / 路径配置且不想入仓库）。生产代码中绝大多数 plugin / project settings 都该走 `TryUpdateDefaultConfigFile()`。

## `UPROPERTY(config)` 验证 checklist

接手陌生 codebase 想"为什么这个 setting 改了不持久化"时，按顺序排查：

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
   `DefaultConfig` flag 让 SaveConfig 默认走 `Default<Category>.ini` 而不是 user-level
3. 字段类型是不是 UPROPERTY 反射支持的？
   - `TArray<UObject*>` / `TMap` 等容器要 each element 也是 UPROPERTY-reachable
   - 嵌套 UObject 不会自动深序列化——其内部字段如果是 config 也要看那 UObject 自身的 Config category
4. 真正的 ini 文件路径是不是按预期？
   - `Config = Engine` → `Config/DefaultEngine.ini`
   - `Config = Editor` → `Config/DefaultEditor.ini`
   - `Config = Game` → `Config/DefaultGame.ini`
   - 自定义 Category → `Config/Default<Category>.ini`

## AssetRegistrySearchable：rename / move 自动跟

需要持久化"`UObject` 内嵌的 `FName` / `FString` / 标量 metadata"，且想让 Asset Registry rename / move 时自动跟随时：

```cpp
UPROPERTY(VisibleAnywhere, AssetRegistrySearchable, Category = "Foo")
FName MyAssetId;
```

`AssetRegistrySearchable` meta 让该 UPROPERTY 进 AR tag。AR 重命名 / 移动 asset 时 tag 自动更新，runtime / editor 直接读 `FAssetData::GetTagValueRef<FName>` 就是当前最新值。**不需要另维护一份 mirror 表 / 文件**。

典型应用：
- DA 上的"业务 ID"字段（如 DialogueId / RecipeId / QuestId）
- "审核状态" bool 标记（如 `bReviewed`）—— Overview Panel 可以直接 query AR tag，不 force-load asset

**特别注意**：`AssetRegistrySearchable` 跟 `config` 是正交的两个机制。
- `config` 让字段持久化到 ini 文件（per-class，不 per-instance）
- `AssetRegistrySearchable` 让字段进 AR tag（per-instance，跟 asset 走）

混用两个 flag 在同一字段是合法的但通常没意义——`config` 的 per-class 跟 `AssetRegistrySearchable` 的 per-instance 语义不同。

## 特殊路径：嵌套 UObject 集合

如果 setting 字段是 `TArray<UObject*>` / `TMap<FName, UObject*>` 且每个元素自己有 config 字段，UE 不会自动序列化。常见 workaround pattern：

- 外层 UObject 暴露一个**导出函数**（如 `RebuildIndexFromObjects()`）把每个元素的关键字段抽到一个**平铺的** `UPROPERTY(config)` 容器（例：`TArray<FStructWithConfigFields>`）
- 修改时同步更新两份
- 用 `PostEditChangeProperty(空 event)` 触发外层的 sync 逻辑

这是 UE engine 内部对 `ULocalizationSettings` 的 `GameTargetSet` ↔ `GameTargetsSettings` 双轨设计的原因——前者 runtime 操作的对象层，后者是 `UPROPERTY(config)` 的扁平镜像，靠 `PostEditChangeProperty` 同步。具体见 `guidelines/ue/localization-pitfalls.md` Trap 4。

## Failure Symptoms

按"症状 → 怀疑 trap"排查：

| 症状 | 怀疑 |
|---|---|
| Editor 里改 setting 看起来生效，关掉重开值丢失 | UPROPERTY 缺 `config` flag / 或宿主类缺 `Config = ...` / 或调的 `SaveConfig()` 写到 user-level |
| Dev A 本机配的 setting，Dev B / CI 没看到 | `SaveConfig()` 无参写到 user-level，没入 `DefaultXxx.ini` |
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
