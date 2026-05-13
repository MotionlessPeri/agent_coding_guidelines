# Runtime Module 永远不依赖 Editor Module

## 核心规则

UE plugin / project 的 **Runtime 模块**任何情况下**不能依赖 Editor 模块**：

- `<Runtime>.Build.cs` 的 `PublicDependencyModuleNames` / `PrivateDependencyModuleNames` 里**禁止**出现 Editor 模块名
- **含 conditional**：`if (Target.bBuildEditor)` / `if (Target.Type == TargetType.Editor)` 也禁
- 看到一行 `"<Plugin>Editor"`（或 `UnrealEd` / `Kismet` / `AssetTools` / `ToolMenus` / 等 editor-only modules）出现在 Runtime build.cs → **必须**拒绝合并 / 立即移除

依赖方向只能是 **Runtime ← Editor**（Editor 可以依赖 Runtime；反向不行）。

## 为什么

UE framework 硬约束：

| build target | 含 Editor 模块？ |
|---|---|
| Editor (development / debug) | ✓ |
| Cooked Game (shipping) | ✗ |
| Server | ✗ |
| Standalone | ✗ |

Cooked shipping build 完全不打包 Editor 模块。如果 Runtime 模块的 `Build.cs` 声明了 Editor 模块依赖：

- **直接症状**：cook 失败 / package 失败 —— UnrealBuildTool / UAT 报"missing module"
- **隐藏症状**：开发期 Editor build 一切正常，dev 看不到问题；CI 跑 packaging 才暴露 → late discovery
- **更隐蔽**：用 `if (Target.bBuildEditor)` 包起来"看起来"安全 → cook 时该 dep 不进 build，**但** Runtime 模块的 cpp 里如果有 `#include "<Editor>/..."`（gated by `WITH_EDITOR`）→ shipping build 编译时找不到 header → 编译错

哪怕 Runtime 代码用 `#if WITH_EDITOR` 包住了 Editor 头的 include，UnrealBuildTool 仍然在 shipping 配置下扫不到 header 搜索路径就报错。**WITH_EDITOR 不能救你**。

## 常见诱因 + 正确解法

| 诱因 | 错的解法 | 正确解法 |
|---|---|---|
| Runtime 模块想 log 到 Editor 才有的 MessageLog | Runtime build.cs 加 `"MessageLog"` dep | Runtime 暴露 `FOnDiagnostic` delegate，Editor 端 subscribe 后再 push 到 MessageLog |
| Runtime UObject 想触发 Editor 通知 / refresh widget | Runtime 调 Editor API | Runtime broadcast event，Editor subscribe |
| Runtime test 想用 Editor-only fixture / helper | Runtime test build.cs 加 Editor dep | **把 test 文件搬到 Editor module**（test 本来就 gated by `WITH_EDITOR`，归属本来就在 Editor） |
| Runtime 想读 Editor-only setting（如 `bAutoDeriveOnXlsxImport`） | Runtime include Editor settings header | Editor 暴露 delegate / Runtime 自己有 mirror config，Editor → Runtime 同步 |
| Runtime asset 需要 PostEditChangeProperty / Slate UI hooks | Runtime build.cs 加 `"UnrealEd"` / `"Slate"` | 这些已经是 Engine module 提供的 `WITH_EDITOR` 包住的 UObject API；不需要额外 dep |
| Runtime 模块的 graph 类型 / asset 类型想做 Details Customization | Runtime build.cs 加 `"PropertyEditor"` | Details Customization 全部走 Editor module 注册（`FPropertyEditorModule::RegisterCustomClassLayout`） |
| Runtime 需要在 PIE 启动时做某事 | Runtime 调 `FEditorDelegates::PreBeginPIE` | Editor 模块订阅 PreBeginPIE，调 Runtime 的纯函数 API |

通用 pattern：**Runtime 暴露纯数据 API + delegate**，**Editor 负责 UI / 工具链 / 编辑期触发**。

## 怎么诊断

build / link 报这类错时**优先怀疑** Runtime → Editor 反依赖：

```
LNK2001: unresolved external symbol "struct FLogCategoryLog<EditorOnlyCategory> ..."
  → 多半是 Runtime cpp 用了 Editor 模块定义的 LogCategory
```

```
Could not find header "<Editor>/Path/Foo.h" included by Runtime/Bar.cpp
  → Runtime cpp 直接 #include 了 Editor 头
```

```
UnrealBuildTool: ERROR: Couldn't find module rules file for module '<PluginName>Editor'
  (during shipping cook)
  → Runtime build.cs 进了 Editor dep
```

```
COOK-FAIL: missing module '<PluginName>Editor' in target '<Project>Server'
  → 同上
```

## review checklist（给 PR / 自我 review）

变更包含 `*.Build.cs` 时**强制**走一遍：

- [ ] 改的是哪个 module 的 build.cs？（看路径 `Source/<ModuleName>/`）
- [ ] 该 module 是 Runtime 还是 Editor？（看 `<Plugin>.uplugin` 的 `Modules[].Type`，`Runtime` / `RuntimeNoCommandlet` / `RuntimeAndProgram` 都算 runtime）
- [ ] 如果是 Runtime —— `PublicDependencyModuleNames` / `PrivateDependencyModuleNames` 里**有没有任何 Editor module 名**？
  - 项目自己的 Editor module（如 `<Plugin>Editor` / `<Plugin>RuntimeEditor` 等）→ 禁
  - UE engine 的 Editor-only module（`UnrealEd` / `Kismet` / `KismetCompiler` / `KismetWidgets` / `AssetTools` / `AssetDefinition` / `ToolMenus` / `PropertyEditor` / `EditorStyle` / `EditorWidgets` / `EditorFramework` / `EditorSubsystem` / `LevelEditor` / `Sequencer` / `MaterialEditor` / `BlueprintGraph` / `GraphEditor` / `SourceControl` 等）→ 禁
- [ ] 如果新增了 conditional `if (Target.bBuildEditor)` / `if (Target.Type == ...)` 包 Editor dep → **禁**（理由见上"WITH_EDITOR 不能救你"）

如果该改动确实需要 Editor API → 走"诱因 + 解法"表的对称重设计。

## Anti-pattern: 用 `WITH_EDITOR` 自欺欺人

```csharp
// ❌ 看起来"只在 editor build 才依赖" —— 实际不安全
if (Target.bBuildEditor)
{
    PrivateDependencyModuleNames.Add("UnrealEd");
}
```

```cpp
// 同时 Runtime/Public/Foo.h 里
#if WITH_EDITOR
#include "Editor.h"   // ← UnrealEd 头
#endif

class MYRUNTIME_API UFoo : public UObject
{
    UFUNCTION()
    void DoEditorThing();    // impl 在 cpp 里 #if WITH_EDITOR
};
```

Shipping 配置下 build 系统：
1. 不进 `if (Target.bBuildEditor)` 分支 → 不加 UnrealEd dep
2. 但 `#include "Editor.h"` 还在 Header 里 → 找不到该 header → 编译 fail

需要 `WITH_EDITOR` 包住的功能，**该功能本身就应该在 Editor module**，不是把 Runtime 类型挖洞。

## 项目实例参考

UE 5.5 dialogue plugin 历史踩过 2 次，commit 锚点 + 修法分别：

- **I-016 / DepClean-A**：Runtime `USidecarRegistry` 想往 MessageLog 写错误 → Runtime build.cs 加了 `"MessageLog"` dep。Cook fail 后修法：runtime 暴露 `FOnSidecarRegistryDiagnostic` delegate，`DialogueSystemEditor` 提供 `FSidecarRegistryDiagnosticBridge` 订阅后 push 到 MessageLog。详 `DialogueSystem.Build.cs` 头注释 + `SidecarRegistry.h` 的 `OnDiagnostic` 字段
- **I-017 / DepClean-B**：Runtime `UDialogueChoiceNode::PostEditChangeProperty` 想触发 `FStateGraphAssetEditorBase::ReconstructNode` → 加了 `OFStateGraphCoreEditor` dep。修法：删冗余的 `PostEditChangeProperty`（`FStateGraphAssetEditorBase` 已经监听 `DetailsView::OnFinishedChangingProperties` 做同样工作）
- **2026-05-13 test-isolation 场景预防**：`SidecarRegistryFilterTest.cpp` 在 Runtime tests 目录想用 Editor module 的 `FScopedTestLineDatabase` fixture → **解法不是加 dep，是把 test 移到 Editor module**（test 已经 gated by `WITH_EDITOR`，归属 Editor module 更合理）

## 相关 Guidelines

- [`editor-runtime-separation.md`](editor-runtime-separation.md) —— 同 module 内的"Runtime Ops / Editor Actions / UI" 三层模型（本 skill 的 sibling 文件）；本文档是**跨 module** 的依赖方向规则
- skill `ue-reference-engine-source` —— UE engine module 哪些是 editor-only 不能进 runtime build.cs，最权威参考是 engine source 本身（grep `<ModuleName>.Build.cs` 的 `Type` 字段）
