# `GLevelEditorModeTools()` 无效时不是返回空——会 ensure 失败 + 错误重建

## 核心规则

`GLevelEditorModeTools()` 在全局 mode-tools 单例**无效**时不是安全返回 / 返回 null,而是 **(1) `ensureMsgf` 失败(调试器里像崩)+ (2) 错误地 `MakeShared` 重建一个新的 `FEditorModeTools`**。所以**任何**在「模块 startup 早期」或「模块 shutdown / 引擎退出期」访问它的代码,都必须先用引擎自带的 **`GLevelEditorModeToolsIsValid()`** 守卫;无效就跳过。

- **Startup 端**:registration 不要放在 `StartupModule` / `OnPostEngineInit`(都早于 level editor 创建)。用 **`FLevelEditorModule::OnLevelEditorCreated`** gate(引擎那条 ensure 的报错信息自己就这么建议)。
- **Shutdown 端**:`ShutdownModule`(经 `UnloadModulesAtShutdown`)里**单例已销毁**,清理 delegate 前必须 `GLevelEditorModeToolsIsValid()` 守卫;无效则直接跳过——mode tools 连同你绑进去的回调已一起销毁,无需也无法显式移除。
- **Commandlet / headless**:`GLevelEditorModeTools()` 顶部有 `checkf(!IsRunningCommandlet(), ...)`——commandlet 环境直接 check 失败。这类全局编辑器单例**不要**在 commandlet 里碰。

## ⚠️ 版本兼容:UE 5.8 起 `GLevelEditorModeToolsIsValid()` 不可用

`GLevelEditorModeToolsIsValid()` **UE 5.5 起标 `UE_DEPRECATED`、5.8 删除了定义**——`Editor.h` 里只剩声明(带 `UE_DEPRECATED(5.5, ...)`),全引擎源码**无任何定义** → 调用它链接期 `LNK2019: unresolved external symbol`。Epic 在 deprecation 消息里给的指引:

> "Checking the validity of the global mode manager is unnecessary. Instead use `FLevelEditorModule::OnLevelEditorCreated` to gate the access on the global mode manager."

所以**跨 5.5–5.8+ 的代码不要用 `GLevelEditorModeToolsIsValid()` 守卫**,改用「level editor 是否存在」做代理(5.7 / 5.8 通用,本文后续所有 `GLevelEditorModeToolsIsValid()` 用法在 5.8+ 一律换成它):

```cpp
static bool AreLevelEditorModeToolsValid()
{
    if (!GIsEditor || IsRunningCommandlet()) { return false; }
    FLevelEditorModule* LE = FModuleManager::GetModulePtr<FLevelEditorModule>("LevelEditor");
    return LE != nullptr && LE->GetFirstLevelEditor().IsValid();
}
```

全局 mode-tools 单例的生命周期跟 LevelEditor 模块的 live level editor 一致:level editor 在 ⇒ 单例有效;引擎退出时两者同时消失 ⇒ 代理返回 false → 跳过访问,正好避免 shutdown 期 `GLevelEditorModeTools()` ensure-fail + 错误重建导致的退出崩溃(下节)。需依赖 `FModuleManager`(`Modules/ModuleManager.h`)+ `FLevelEditorModule`(`LevelEditor.h`,Build.cs 加 `LevelEditor` 依赖)。

> 下文「Hidden Contract」记的 `GLevelEditorModeToolsIsValid()` 是 ≤5.7 的守卫形态;其**机制**(单例无效时 `GLevelEditorModeTools()` ensure-fail + 重建)在 5.8 仍成立,只是**那个具名守卫函数没了** → 用上面的代理顶替。

## Hidden Contract(带 engine source 锚点)

`Engine/Source/Editor/UnrealEd/Public/Editor.h`:
```cpp
UNREALED_API class FEditorModeTools& GLevelEditorModeTools();   // :723
UNREALED_API bool GLevelEditorModeToolsIsValid();              // :729
```

`Engine/Source/Editor/UnrealEd/Private/UnrealEdGlobals.cpp`:
```cpp
static TSharedPtr<FEditorModeTools> EditorModeToolsSingleton;   // Internal::

bool GLevelEditorModeToolsIsValid()                            // :53
{
    return Internal::EditorModeToolsSingleton.IsValid();        // 守卫就是查这个
}

FEditorModeTools& GLevelEditorModeTools()                     // :116
{
    checkf(!IsRunningCommandlet(), TEXT("...should not be created or accessed in a commandlet..."));
    if (!ensureMsgf(Internal::EditorModeToolsSingleton.IsValid(),
        TEXT("The level editor is not started up yet. ... please use "
             "FLevelEditorModule::OnLevelEditorCreated to gate the access.")))
    {
        Internal::EditorModeToolsSingleton = MakeShared<FEditorModeTools>();   // ⚠️ 错误重建
    }
    return *Internal::EditorModeToolsSingleton.Get();
}
```

两个失败窗口、同一根因(单例无效):

| 窗口 | 为什么单例无效 | 后果 |
|---|---|---|
| `StartupModule` / `OnPostEngineInit` | level editor 还没创建,单例未建 | ensure 失败 + 重建一个**早产**的 mode tools(后续真 level editor 起来时状态错乱) |
| `ShutdownModule` / `UnloadModulesAtShutdown` | 引擎退出已销毁单例 | ensure 失败 + 在退出期**重建**一个永远不会清理的 `FEditorModeTools` → shutdown 崩溃 |

## 正确写法

```cpp
// 注册:gate 在 level editor 创建后(不要 StartupModule / OnPostEngineInit 直接调)
FCoreDelegates::OnPostEngineInit.AddLambda([this]()
{
    FLevelEditorModule& LE = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
    if (LE.GetFirstLevelEditor().IsValid())                 // 已经起来(mid-session 加载)
    {
        RegisterModeToolsConsumer();                        // 内部仍 GLevelEditorModeToolsIsValid() 守卫
    }
    else
    {
        LE.OnLevelEditorCreated().AddLambda([this](TSharedPtr<ILevelEditor>){ RegisterModeToolsConsumer(); });
    }
});

// 任何访问 GLevelEditorModeTools() 的函数(注册 / 注销 / bind / unbind)统一守卫:
void Foo::Unregister()
{
    if (GLevelEditorModeToolsIsValid())                     // shutdown 时为 false → 跳过
    {
        GLevelEditorModeTools().OnEditorModeIDChanged().Remove(Handle);
    }
    Handle.Reset();                                         // 本地状态照样清
}
```

需要订阅 edit mode 选择 / 切控件状态的参考消费方:`AnimDetailsProxyManager`
(`...ControlRigEditor/Private/AnimDetails/AnimDetailsProxyManager.cpp` 的
`SetupBingings` / `ReleaseBindings`)——Animation Mode 语境下经
`GLevelEditorModeTools().GetActiveMode(...)` 拿 edit mode + 订阅其 delegate 的官方范例。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| `StartupModule` 里直接 `GLevelEditorModeTools()` | ensure 失败 + 早产重建 | gate 到 `OnLevelEditorCreated` |
| `OnPostEngineInit` 里直接调(以为够晚) | 仍早于 level editor 创建 | 同上 |
| `ShutdownModule` 里无守卫 `GLevelEditorModeTools().Remove(...)` | 退出期错误重建 → 崩溃 | 先 `GLevelEditorModeToolsIsValid()` |
| 以为它无效会返回 null / 抛异常 | 它**静默重建**,看似工作实则状态错 | 永远先 IsValid 守卫 |
| 在 commandlet / headless 访问 | `checkf(!IsRunningCommandlet())` 直接挂 | 编辑器单例不进 commandlet |

## 项目实例参考

某 UE 5.7 插件(curvenet)做"选中端点控件→显隐其切线手柄"功能,模块级 manager 订阅
`FControlRigEditMode` 选择事件——一个 session 内**两次**命中同一根因:

1. registration 初版放 `OnPostEngineInit` → 启动时 `GLevelEditorModeTools()` ensure 失败(早于 level editor)。改 gate 到 `FLevelEditorModule::OnLevelEditorCreated`。
2. `Unregister()`(`ShutdownModule` 调)无守卫调 `GLevelEditorModeTools()` → 退出期错误重建 → **退出崩溃**。给所有访问加 `GLevelEditorModeToolsIsValid()` 守卫修复。

同一 hidden contract 的两端(太早 / 太晚)各踩一次,符合 two-strike 提炼条件。

## 相关 Guidelines

- [`property-handle-strong-capture.md`](property-handle-strong-capture.md) / [`details-customization-prefer-reflection.md`](details-customization-prefer-reflection.md) —— 同属"UE 编辑器框架 hidden contract,doc 没写、读 engine source + 实测才知道"族
- skill `ue-reference-engine-source` —— 本条的 `GLevelEditorModeToolsIsValid()` / `OnLevelEditorCreated` 都是读 engine source 找到的;遇到全局编辑器单例的访问时机问题,先翻 source 看引擎自己怎么 gate
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 本案根因从崩溃 stack(`GLevelEditorModeTools` 内部 lambda)+ 读 `UnrealEdGlobals.cpp` 实现取证得到,不是凭猜
