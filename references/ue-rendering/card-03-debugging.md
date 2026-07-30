# UE 5.8 渲染调试与诊断工具链 — 知识卡片

> **验证状态**：本文档的 CVar 表由 `scripts/ue-cvar-dump.py` 从 UE 5.8.0 源码
> （`H:/Epic Games/UE_5.8`）直接生成，名称与作用说明取自引擎自己的帮助文本，**逐条存在**。
> 外部工具（Nsight / RGP / PIX）一节讲的是第三方工具用法，不含引擎符号断言，未经工具校验。
> 重新生成：`python scripts/ue-cvar-dump.py r.DumpGPU --md`

## 目录

| 节 | 内容 |
|---|---|
| [1. 三种控制机制](#1-三种控制机制cvar--showflag--viewmode) | CVar / ShowFlag / viewmode 的区别——最常踩的坑 |
| [2. 帧捕获与 GPU Dump](#2-帧捕获与-gpu-dump) | `r.DumpGPU.*` 全 25 个 + 输出结构 |
| [3. GPU 性能剖析](#3-gpu-性能剖析) | `r.ProfileGPU.*` 全 13 个 |
| [4. GPU 崩溃取证](#4-gpu-崩溃取证) | `r.GPUCrashDebugging.*` 全 19 个（Breadcrumbs / Aftermath / Intel） |
| [5. 平台 Validation](#5-平台-validation) | D3D12 debug layer / Vulkan validation / RHI validation |
| [6. Shader 调试与符号](#6-shader-调试与符号) | 开发模式 / 调试信息导出 / 符号生成 |
| [7. 外部工具](#7-外部工具) | RenderDoc（`renderdoc.*` 全 16 个）/ Nsight / RGP / PIX |
| [8. 时序与 temporal 问题](#8-时序与-temporal-问题) | `r.Test.*` 冻结历史等 |
| [9. 诊断决策树](#9-诊断决策树) | 症状 → 该开哪个开关 |
| [10. 关键源码文件索引](#10-关键源码文件索引) | |
| [附录：不存在的 CVar 对照表](#附录不存在的-cvar-对照表) | 调研稿里出现过、5.8 中并不存在的名字及其真实对应物 |

---

## 1. 三种控制机制：CVar / ShowFlag / viewmode

这是最容易搞错的一点，也是调研稿里出错最多的地方——把 ShowFlag 和 viewmode 写成了
`r.*` 开头的 CVar。客户照着敲会直接得到 unknown command。

| 机制 | 语法 | 例子 | 特点 |
|---|---|---|---|
| **CVar** | `<名字> <值>` | `r.DumpGPU.FrameCount 3` | 有默认值、可写 ini、可 per-platform 覆盖 |
| **ShowFlag** | `ShowFlag.<名字> <0/1>` | `ShowFlag.VisualizeMotionBlur 1` | 布尔开关，挂在 `FEngineShowFlags` 上，per-view |
| **viewmode** | `viewmode <名字>` | `viewmode shadercomplexity` | 整体切换视图模式，互斥 |

判断某个名字属于哪一类：**能在 `scripts/ue-cvar-dump.py --check <名字>` 里查到的才是 CVar**，
查不到就去看它是不是 ShowFlag（`FEngineShowFlags` 里的成员）或 viewmode。

具体地说，下面这些**不是 CVar**（调研稿曾把它们写成 `r.` 开头的 CVar）：

<!-- verify:ignore-start -->

- 缓冲区可视化 → `ShowFlag.VisualizeBuffer` + 用 `r.BufferVisualizationOverviewTargets` 配置显示哪些通道
- 线框 → `viewmode wireframe` / `ShowFlag.Wireframe`
- Shader 复杂度 → `viewmode shadercomplexity`；`r.ShaderComplexity.Baseline.*`
  这组 CVar 只调可视化的**刻度基准**，不是开关
- Quad overdraw → `viewmode quadoverdraw`
- LOD 着色 → `viewmode lodcoloration`
<!-- verify:ignore-end -->

**可视化配置相关的真 CVar**（共 3 个）：

| CVar | 作用 |
|---|---|
| `r.BufferVisualizationDumpFrames` | When screenshots or movies dumps are requested, also save out dumps of the current buffer visualization materials 0:off (default) 1:on |
| `r.BufferVisualizationDumpFramesAsHDR` | When saving out buffer visualization materials in a HDR capable format 0: Do not override default save format. 1: Force HDR format for buffer visualization materials. |
| `r.BufferVisualizationOverviewTargets` | BaseColor,Specular,SubsurfaceColor,WorldNormal,SeparateTranslucencyRGB,,,WorldTangent,SeparateTranslucencyA,,,Opacity,SceneDepth,Roughness,Metallic,ShadingModel,,SceneDepthWorldUnits,SceneColor,PreTonemapHDRColor,PostTon… |

| CVar | 作用 |
|---|---|
| `r.VisualizeOccludedPrimitives` | Draw boxes for all occluded primitives. 0: Do not draw bounding boxes for occluded primitives (default). 1: Draw the primitive bounding boxes for all occluded primitives. 2: Draw the primitive bounding boxes for all… |
| `r.ShowMaterialDrawEvents` | Whether to emit a draw event around every mesh draw call with information about the assets used. Introduces severe CPU and GPU overhead when enabled, but useful for debugging. |

---

## 2. 帧捕获与 GPU Dump

控制台执行 `r.DumpGPU` 把一帧的 RDG pass、资源、参数导出到磁盘供离线分析。**对性能
影响极大**，只适合抓单帧。

下面这组 `r.DumpGPU.*` CVar（控制它的行为）逐条核实存在，声明在
`Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp`。**触发命令 `r.DumpGPU` 本身的
注册位置我没在源码里定位到**——它不以 `FAutoConsoleCommand` 的常见形式出现在 RenderCore
或 `DumpGPUServices` 插件里。命令可用（这是长期文档化的用法），但如果要精确引用注册处，
请自行再查一次。

### 2.1 全部 `r.DumpGPU.*`（25 个）

| CVar | 作用 | 声明位置 |
|---|---|---|
| `r.DumpGPU.Buffer` | Whether to dump buffer. 0: Ignores all buffers 1: Dump only buffers' descriptors 2: Dump buffers' descriptors and binaries (default) | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:75` |
| `r.DumpGPU.CameraCut` | Whether to issue a camera cut on the first frame of the dump. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:114` |
| `r.DumpGPU.ConsoleVariables` | Whether to dump rendering console variables (enabled by default). | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:148` |
| `r.DumpGPU.Delay` | Delay in seconds before dumping the frame. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:99` |
| `r.DumpGPU.Directory` | Directory to dump to. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:163` |
| `r.DumpGPU.Draws` | Whether to dump resource after each individual draw call (disabled by default). | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:133` |
| `r.DumpGPU.DumpOnScreenshotTest` | Allows to filter the tree when using r.DumpGPU command, the pattern match is case sensitive. | `Engine/Source/Developer/FunctionalTesting/Private/ScreenshotFunctionalTestBase.cpp:29` |
| `r.DumpGPU.EnableLogWrite` | Enables writing the log file to disk. 0: Does not write log file to disk 1: Logging writes are enabled (default) | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:187` |
| `r.DumpGPU.Explore` | Whether to open file explorer to where the GPU dump on completion (enabled by default). | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:143` |
| `r.DumpGPU.FixedTickRate` | Override the engine's tick rate to be fixed for every dumped frames (default=0). | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:119` |
| `r.DumpGPU.FrameCount` | Number of consecutive frames to dump (default=1). | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:109` |
| `r.DumpGPU.FrameDelay` | Delay in frames before dumping the frame. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:104` |
| `r.DumpGPU.Mask` | Whether to include GPU mask in the name of each Pass (has no effect unless system has multiple GPUs). | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:138` |
| `r.DumpGPU.MaxStagingSize` | Maximum size of stating resource in MB (default=64). | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:83` |
| `r.DumpGPU.PassParameters` | Whether to dump the pass parameters. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:88` |
| `r.DumpGPU.RedumpInputs` | Re-capture input resources at the point they are read, breaking linkage to any prior (stale) version. Useful when r.DumpGPU.Root excludes intermediate passes that modify a resource in-place. This would increase dumped… | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:93` |
| `r.DumpGPU.Root` | * Allows to filter the tree when using r.DumpGPU command, the pattern match is case sensitive. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:61` |
| `r.DumpGPU.Screenshot` | Whether to take a final screenshot. | `Engine/Source/Runtime/Engine/Private/UnrealEngine.cpp:286` |
| `r.DumpGPU.Stream` | Asynchronously readback from GPU to disk. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:124` |
| `r.DumpGPU.Test.EnableDiskWrite` | Main switch whether any files should be written to disk, used for r.DumpGPU automation tests to not fill up workers' hard drive. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:153` |
| `r.DumpGPU.Test.PrettifyResourceFileNames` | Whether the resource file names should include resource name. May increase the likelyness of running into Windows' filepath limit. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:158` |
| `r.DumpGPU.Texture` | Whether to dump textures. 0: Ignores all textures 1: Dump only textures' descriptors 2: Dump textures' descriptors and binaries (default) | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:67` |
| `r.DumpGPU.Upload` | Allows to upload the GPU dump automatically if set-up. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:168` |
| `r.DumpGPU.Upload.CompressResources` | Whether to compress resource binary. 0: Disabled (default) 1: Zlib 2: GZip | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:173` |
| `r.DumpGPU.Viewer.Visualize` | Name of RDG output resource to automatically open in the dump viewer. | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp:182` |

### 2.2 常用组合

```ini
; 抓当前帧，只导出描述不导出二进制（快得多，够看 pass 结构和资源尺寸）
r.DumpGPU.Texture 1
r.DumpGPU.Buffer 1
r.DumpGPU

; 抓连续 3 帧，延迟 5 帧后开始（等场景稳定）
r.DumpGPU.FrameCount 3
r.DumpGPU.FrameDelay 5
r.DumpGPU

; 逐 draw call 导出——量极大，只在定位"哪一次 draw 写坏了"时开
r.DumpGPU.Draws 1
r.DumpGPU
```

注意 `r.DumpGPU.FrameCount` 是**连续捕获的帧数**（引擎原文 "Number of consecutive
frames to dump"），不是"抓第 N 帧"。要延后开始用 `r.DumpGPU.FrameDelay` 或
`r.DumpGPU.Delay`（秒）。

输出目录由 `r.DumpGPU.Directory` 决定，过滤 pass 树用 `r.DumpGPU.Root`。

---

## 3. GPU 性能剖析

`ProfileGPU` 控制台命令出一份按 pass 的耗时树。下面这组 CVar 控制它的输出形态——
默认输出很长，调这几个能直接把注意力压到热点上。

| CVar | 作用 | 声明位置 |
|---|---|---|
| `r.ProfileGPU.Root` | * Allows to filter the tree when using ProfileGPU, the pattern match is case sensitive. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:45` |
| `r.ProfileGPU.ShowEmptyQueues` | When true, GPU queues without any registered work are still displayed in the report tables. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:81` |
| `r.ProfileGPU.ShowExclusive` | When true, exclusive GPU times are shown. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:105` |
| `r.ProfileGPU.ShowHeader` | When true, prints a summary of the profileGPU settings before the report table in the log. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:75` |
| `r.ProfileGPU.ShowInclusive` | When true, inclusive GPU times are shown. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:99` |
| `r.ProfileGPU.ShowLeafEvents` | Allows profileGPU to display event-only leaf nodes with no draws associated. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:69` |
| `r.ProfileGPU.ShowPercentColumn` | When true, a column showing the relative portion of time each stat takes as a percentage is displayed, including a visual unicode bar when unicode output is enabled. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:93` |
| `r.ProfileGPU.ShowStats` | When true, additional stat columns are shown in the report (numbers of draws, dispatches, vertices and primitives). | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:87` |
| `r.ProfileGPU.ShowUI` | Whether the user interface profiler should be displayed after profiling the GPU. The results will always go to the log/console. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:111` |
| `r.ProfileGPU.Sort` | Sorts the TTY Dump independently at each level of the tree in various modes. 0 : Chronological 1 : By time elapsed 2 : By number of prims 3 : By number of verts | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:35` |
| `r.ProfileGPU.TableFormatting` | When enabled, the output results will be formatted in a table with many secondary stats. When disabled, only inclusive times and event names are printed in an indented list for compactness. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:57` |
| `r.ProfileGPU.ThresholdPercent` | Percent of the total execution duration the event needs to be larger than to be printed. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:51` |
| `r.ProfileGPU.UnicodeOutput` | When enabled, the output results will be formatted in a unicode table. | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp:63` |

排查思路：先 `r.ProfileGPU.ThresholdPercent` 把小项过滤掉，再
`r.ProfileGPU.Sort` 按耗时排序，`r.ProfileGPU.ShowExclusive 1` 看自身耗时（排除子节点）
才能找出真正的热点 pass。

---

## 4. GPU 崩溃取证

GPU 崩溃（TDR / device removed）的取证分**厂商无关**和**厂商特定**两条路。厂商无关的
先开——它跨卡都能用，且开销低。

### 4.1 总开关与厂商无关的 Breadcrumbs

| CVar | 作用 |
|---|---|
| `r.GPUCrashDebugging` | Enable vendor specific GPU crash analysis tools |
| `r.GPUCrashDebugging.Breadcrumbs` | Enable RHI breadcrumbs, a vendor-agnostic method for determining which passes were active when a GPU crash occurs |

Breadcrumbs 是判断"崩在哪个 pass"的第一手段，不依赖厂商 SDK。

### 4.2 NVIDIA Aftermath（12 个）

| CVar | 作用 |
|---|---|
| `r.GPUCrashDebugging.Aftermath` | Enables or disables Nvidia Aftermath. |
| `r.GPUCrashDebugging.Aftermath.Callstack` | Enable callstack capture in Aftermath dumps |
| `r.GPUCrashDebugging.Aftermath.DumpProcessWaitTime` | Amount of time (in seconds) to wait for Aftermath to finish processing GPU crash dumps. |
| `r.GPUCrashDebugging.Aftermath.DumpShaderDebugInfo` | Dump shader debug info (.nvdbg) alongside the crash dump. |
| `r.GPUCrashDebugging.Aftermath.DumpStartWaitTime` | Amount of time (in seconds) to wait for Aftermath to start processing GPU crash dumps. |
| `r.GPUCrashDebugging.Aftermath.LateShaderAssociations.FrameLimit` | Max last since used number of frames to consider when collecting pipelines |
| `r.GPUCrashDebugging.Aftermath.LateShaderAssociations.TimeLimit` | Time limit (s) before the late associations are stopped |
| `r.GPUCrashDebugging.Aftermath.Markers` | Enable draw event markers in Aftermath dumps |
| `r.GPUCrashDebugging.Aftermath.ResourceTracking` | Enable resource tracking for Aftermath dumps |
| `r.GPUCrashDebugging.Aftermath.ShaderErrorReporting` | Enable shader error reporting for Aftermath dumps |
| `r.GPUCrashDebugging.Aftermath.ShaderRegistration` | Enable registration of shaders and pipelines in Aftermath. |
| `r.GPUCrashDebugging.Aftermath.TrackAll` | Enable maximum tracking for Aftermath dumps |

`r.GPUCrashDebugging.Aftermath.TrackAll` 是"全开"快捷方式，代价是明显的运行时开销；
定位阶段可以开，交付前要关。

### 4.3 Intel Crash Dumps（5 个）

| CVar | 作用 |
|---|---|
| `r.GPUCrashDebugging.IntelCrashDumps` | Enable/disable Intel GPU Crash Dumps. |
| `r.GPUCrashDebugging.IntelCrashDumps.Callstack` | Enable callstack capture in the GPU Crash Dumps. |
| `r.GPUCrashDebugging.IntelCrashDumps.DumpWaitTime` | Intel Breadcrumbs GPU crash dumps processing timeout. |
| `r.GPUCrashDebugging.IntelCrashDumps.Markers` | Enable event markers in the GPU Crash Dumps. |
| `r.GPUCrashDebugging.IntelCrashDumps.ResourceTracking` | Enable resource tracking in the GPU Crash Dumps. |

---

## 5. 平台 Validation

Validation 层抓的是"API 用法不合规"，跟渲染结果对不对是两件事。开着跑很慢，只在排查
诡异行为时开。

### 5.1 D3D12

| CVar | 作用 |
|---|---|
| `r.D3D12.EnableD3DDebug` | 0 to disable d3ddebug layer (default) 1 to enable error logging (-d3ddebug) 2 to enable error & warning logging (-d3dlogwarnings) 3 to enable breaking on errors & warnings (-d3dbreakonwarning) 4 to enable CONTINUING on… |
| `r.D3D12.DXR.RaytracingValidation` | Enables NVAPI Raytracing validation. |
| `r.D3D12.DXR.RaytracingValidation.IgnoreList` | List of warnings or errors to ignore to prevent spam from NVAPI Raytracing validation. For instance: warning1;warning2 etc |
| `r.D3D12.RayTracing.GPUValidation` | Whether to perform validation of ray tracing geometry and other structures on the GPU. Requires Shader Model 6. (default = 0) |

`r.D3D12.EnableD3DDebug` 也可以用命令行 `-d3ddebug` 打开（引擎帮助文本里写了）。

### 5.2 Vulkan

| CVar | 作用 |
|---|---|
| `r.Vulkan.EnableValidation` | 0 to disable validation layers 1 to enable errors 2 to enable errors & warnings 3 to enable errors, warnings & performance warnings 4 to enable errors, warnings, performance & information messages 5 to enable all… |
| `r.Vulkan.DebugMarkers` | 0 to disable all debug markers 1 to enable debug names for resources 2 to enable debug labels for commands 3 to enable debug resource names command labels 4 to automatically enable markers depending on tool detection… |
| `r.Vulkan.DebugBarrier` | Forces a full barrier for debugging. This is a mask/bitfield (so add up the values)! 0: Don't (default) 1: Enable heavy barriers after EndRenderPass() 2: Enable heavy barriers after every dispatch 4: Enable heavy… |
| `r.Vulkan.DebugVsync` | Whether to print vulkan vsync data |

真名是 `r.Vulkan.EnableValidation`。它是**分级**的（0 关 / 1 只报错 / 2 报错+警告），
不是布尔。调研稿里那个带 `Layers` 后缀的写法不存在。

`r.Vulkan.DebugBarrier` 强制全屏障，用来判断"是不是屏障漏了"——如果强制全屏障后症状
消失，问题就在屏障推导上。

### 5.3 RHI 层

| CVar | 作用 |
|---|---|
| `r.RHIValidation.DebugBreak.Transitions` | Controls whether the debugger should break when a validation error is encountered. 0: disabled; 1: break in the debugger if a validation error is encountered. |
| `r.RHICmdBypass` | Whether to bypass the rhi command list and send the rhi commands immediately. 0: Disable (required for the multithreaded renderer) 1: Enable (convenient for debugging low level graphics API calls, can suppress artifacts… |

`r.RHICmdBypass` 绕过 RHI 命令队列直接提交，用来排除"命令排序/并行录制"这一层的影响。

---

## 6. Shader 调试与符号

| CVar | 作用 |
|---|---|
| `r.ShaderDevelopmentMode` | 0: Default, 1: Enable various shader development utilities, such as the ability to retry on failed shader compile, and extra logging as shaders are compiled. |
| `r.DumpShaderDebugInfo` | Dumps debug info for compiled shaders to GameName/Saved/ShaderDebugInfo When set to 1, debug info is dumped for all compiled shader When set to 2, it is restricted to shaders with compilation errors When set to 3, it is… |
| `r.Shaders.Validation` | Enabled shader compiler validation warnings and errors. |

`r.ShaderDevelopmentMode` 的副作用要知道：编译变慢，日志量大增，编辑器里 shader 编译
错误会弹窗而不是静默回退。排查亚稳态渲染分支时正是要这个行为。

### 6.1 符号生成（图形调试器里看 shader 源码的前提）

| CVar | 作用 |
|---|---|
| `r.Shaders.SymbolFileNameOverride` | Override base file name for shader symbol related aggregate outputs (.zip, .info). '{Platform}' will be replaced with the shader platform string. '{DLC}' will be replaced with the DLC name if there is one. '{?DLC-}'… |
| `r.Shaders.SymbolPathOverride` | Override output location of shader symbols. If the path contains the text '{Platform}', that will be replaced with the shader platform string. Empty: use default location Saved/ShaderSymbols/{Platform} This setting can… |
| `r.Shaders.Symbols` | Enables debugging of shaders in platform specific graphics debuggers. This will generate and write shader symbols. This enables the behavior of both r.Shaders.GenerateSymbols and r.Shaders.WriteSymbols. Enables shader… |
| `r.Shaders.SymbolsInfo` | In lieu of a full set of platform shader PDBs, save out a slimmer ShaderSymbols.Info which contains shader platform hashes and shader debug info. An option for when it is not practical to save PDBs for shaders all the… |

| CVar | 作用 |
|---|---|
| `r.Shaders.GenerateSymbols` | Enables generation of data for shader debugging when compiling shaders. This explicitly does not write any shader symbols to disk. This setting can be overriden in any Engine.ini under the [ShaderCompiler] section. |
| `r.Shaders.WriteSymbols` | Enables writing shader symbols to disk for platforms that support that. This explicitly does not enable generation of shader symbols. This setting can be overriden in any Engine.ini under the [ShaderCompiler] section. |
| `r.Shaders.WriteSymbols.Zip` | 0: Export as loose files. 1: Export as an uncompressed archive. 2: Export as a compressed archive. |
| `r.Shaders.AllowUniqueSymbols` | When enabled, this tells supported shader compilers to generate symbols based on source files. Enabling this can cause a drastic increase in the number of symbol files, enable only if absolutely necessary. This setting… |

要在 RenderDoc / Nsight 里按源码单步 shader，得先让这些符号生成打开并重编 shader——
只开捕获工具是不够的。

---

## 7. 外部工具

### 7.1 RenderDoc

UE 自带 RenderDoc 插件，位置是 `Engine/Plugins/Developer/RenderDocPlugin`。

**触发捕获**：控制台命令 `renderdoc.CaptureFrame`（抓下一帧并启动 RenderDoc）或
`renderdoc.CapturePIE`（起一个 PIE 会话并从头抓若干帧）。这两个是插件注册的
`FAutoConsoleCommand`，声明在 `Engine/Plugins/Developer/RenderDocPlugin/Source/RenderDocPlugin/Private/RenderDocPluginModule.cpp`。

<!-- verify:ignore-start -->
**注意**：调研稿里写的那个 `r.CaptureNextFrame` CVar 在 5.8 中不存在，
`FViewDebugInfo::CaptureNextFrame()` 这个函数也不存在——两者都是生成的产物，仅作反面对照，勿引用。
<!-- verify:ignore-end -->

<!-- verify:ignore-start -->
（上面两个名字仅作反面对照，勿引用。）
<!-- verify:ignore-end -->

**全部 `renderdoc.*` CVar**（16 个，注意前缀没有 `r.`）：

| CVar | 作用 |
|---|---|
| `renderdoc.AutoAttach` | RenderDoc will attach on startup. |
| `renderdoc.BinaryPath` | Path to the main RenderDoc executable to use. |
| `renderdoc.CaptureAllActivity` | 0 - RenderDoc will only capture data from the current viewport. 1 - RenderDoc will capture all activity, in all viewports and editor windows for the entire frame. |
| `renderdoc.CaptureCallstacks` | 0 - Callstacks will not be captured by RenderDoc. 1 - Capture callstacks for each API call. |
| `renderdoc.CaptureDelay` | If > 0, RenderDoc will trigger the capture only after this amount of time (or frames, if CaptureDelayInSeconds is false) has passed. |
| `renderdoc.CaptureDelayInSeconds` | 0 - Capture delay's unit is in frames. 1 - Capture delay's unit is in seconds. |
| `renderdoc.CaptureFrame` | Captures the rendering commands of the next frame and launches RenderDoc |
| `renderdoc.CaptureFrameCount` | If > 0, the RenderDoc capture will encompass more than a single frame. Note: this implies that all activity in all viewports and editor windows will be captured (i.e. same as CaptureAllActivity) |
| `renderdoc.CapturePIE` | Starts a PIE session and captures the specified number of frames from the start. |
| `renderdoc.EnableCrashHandler` | 0 - Crash handling is completely delegated to the engine. 1 - The RenderDoc crash handler will be used (Only use this if you know the problem is with RenderDoc and you want to notify the RenderDoc developers!). |
| `renderdoc.ReferenceAllResources` | 0 - Only include resources that are actually used. 1 - Include all rendering resources in the capture, even those that have not been used during the frame. Please note that doing this will significantly increase capture… |
| `renderdoc.SaveAllInitials` | 0 - Disregard initial states of resources. 1 - Always capture the initial state of all rendering resources. Please note that doing this will significantly increase capture size. |
| `renderdoc.ShowHelpOnStartup` | 0 - Greeting has been shown and will not appear on startup. 1 - Greeting will be shown during next startup. |
| `renderdoc.TextureGraph_CaptureNextBatch` | Captures the next Job Batch and launches RenderDoc |
| `renderdoc.TextureGraph_CaptureNextBatchHistogram` | Captures the next Job Batch producing histogram and launches RenderDoc |
| `renderdoc.TextureGraph_CapturePrevBatch` | Captures the previous Job Batch and launches RenderDoc |

实用组合：`renderdoc.CaptureCallstacks 1` 让每个 API 调用带调用栈（找"谁发的这条命令"）；
`renderdoc.ReferenceAllResources 1` 连未使用的资源也纳入（排查"资源没绑上"）；
`renderdoc.CaptureFrameCount` > 1 抓跨帧，用于 temporal 相关问题。

配合 `r.ShowMaterialDrawEvents 1` 和 `r.Vulkan.DebugMarkers`（Vulkan）/
`r.D3D12.EnableD3DDebug`（D3D12），RenderDoc 的 Event Browser 里才能看到有意义的名字。

### 7.2 NVIDIA Nsight

**集成方式**：
- Nsight Graphics：独立安装，需与 UE 配合
- 在 Nsight 中启动 UE Editor 或 packaged game
- 支持 D3D12 和 Vulkan

**优势**：
- GPU 性能分析（时间线、occupancy、warp utilization）
- Shader 汇编级调试（SASS）
- 对 UE 5.8 的 Nanite Mesh Shader 有更好的调试支持
- 支持 GPU Trace（`r.GPUTrace 1` 配合 Nsight 使用）

**常用工作流**：
1. 在 Nsight 中设置启动 UE 项目的 Activity
2. 运行到目标场景，触发帧捕获
3. 使用 GPU Trace 分析 draw call 耗时
4. 使用 Shader Debugger 单步执行 shader

### 7.3 AMD Radeon GPU Profiler (RGP)

**集成方式**：
- 独立工具，需要 UE 以特定方式运行
- 通过 Radeon Developer Panel 启动 UE

**优势**：
- 详细的 GPU 流水线分析（Wave occupancy、Cache hit rate）
- Shader 指令级分析
- 对异步计算（Async Compute）有良好支持
- 支持 UE 5.8 的 RDG name tagging

**适用场景**：
- 性能瓶颈定位（ROPs、shader、bandwidth 三选一）
- 着色器优化（ALU 占用 vs 内存延迟）
- 异步计算队列分析

### 7.4 PIX (Windows)

**集成方式**：
- Microsoft PIX 独立工具，支持 D3D12
- 在 PIX 中启动 UE
- 或附加到运行中的 UE 进程

**优势**：
- D3D12 调试的最底层工具
- 资源状态追踪（Barrier validation）
- GPU 内存分配分析
- 对 UE 5.8 的 D3D12 RHI 有第一手支持

**常用功能**：
- GPU Capture：完整的 draw call 和资源状态记录
- Timing Capture：CPU vs GPU 时间线
- Memory Capture：资源分配分析
- Function Summary：按 shader/PSO 聚合的统计

---

---

## 8. 时序与 temporal 问题

TAA / TSR / Lumen 都带时间累积，"闪烁""拖影""收敛慢"这类问题必须能把时间维度冻住才好查。
`r.Test.*` 这组就是干这个的：

| CVar | 作用 |
|---|---|
| `r.Test.Aplha.OpaqueLerpWorldRange` | Sets the gradient length in world unit on which opaque pixel are lerped to translucent for testing purposes. |
| `r.Test.Aplha.OpaqueWorldDistance` | Sets the world distance beyond which the opaque pixel are lerped to translucent for testing purposes. |
| `r.Test.CameraCut` | Force enabling camera cut for testing purposes. |
| `r.Test.ConstrainedView` | Allows to test different viewport rectangle configuations (in game only) as they can happen when using cinematics/Editor. 0: off(default) 1..7: Various Configuations |
| `r.Test.DynamicResolutionHell` | Override the screen percentage interface for all view family with dynamic resolution hell. |
| `r.Test.EditorConstrainedView` | Allows to test different viewport rectangle configuations (in game only) as they can happen when using cinematics/Editor. 0: off(default) 1..7: Various Configuations |
| `r.Test.EditorViewGPUMirror` | Tests FSceneViewStateInterface system memory mirror functionality in the editor viewport for debugging. Mirroring is used for Movie Render Queue high resolution tiled rendering, but debugging it there can be difficult,… |
| `r.Test.ForceBlackVelocityBuffer` | Force the velocity buffer to have no motion vector for debugging purpose. |
| `r.Test.FreezeTemporalHistories` | Freezes all temporal histories as well as the temporal sequence. |
| `r.Test.FreezeTemporalHistories.Progress` | Progress the temporal histories by one frame when modified. |
| `r.Test.FreezeTemporalSequences` | Freezes all temporal sequences. |
| `r.Test.OverrideTimeMaterialExpressions` | Value to freeze time material expressions with. |
| `r.Test.PrimaryScreenPercentageMethodOverride` | Override the screen percentage method for all view family. 0: view family's screen percentage interface choose; (default) 1: old fashion upscaling pass at the very end right before before UI; 2: TemporalAA upsample. |
| `r.Test.SecondaryUpscaleOverride` | Override the secondary upscale. 0: disabled; (default) 1: use secondary view fraction = 0.5 with nearest secondary upscale. |
| `r.Test.ViewRectOffset` | Moves the view rect within the renderer's internal render target. |
| `r.Test.ViewRollAngle` | Roll the camera in degrees, for testing motion vector upscaling precision. (disabled by default) |

`r.Test.FreezeTemporalHistories 1` 冻结所有 temporal 历史：冻住之后如果画面就稳了，
问题在累积/重投影；如果依旧闪，问题在当帧生成。这是分离"当帧 vs 历史"最快的一刀。

`r.Test.ForceBlackVelocityBuffer 1` 把速度缓冲清零，用来判断拖影是不是速度矢量算错。

---

## 9. 诊断决策树

```mermaid
flowchart TD
    A["渲染异常"] --> B什么症状？

    B -->|"GPU 崩溃 / TDR"| C1["r.GPUCrashDebugging 1<br/>r.GPUCrashDebugging.Breadcrumbs 1"]
    C1 --> C2["拿到崩溃 pass 名"]
    C2 --> C3["NVIDIA 再开 Aftermath.TrackAll<br/>Intel 开 IntelCrashDumps"]

    B -->|"画面内容不对"| D1["先分清是哪一层"]
    D1 --> D2["ShowFlag.VisualizeBuffer<br/>看 GBuffer 各通道"]
    D2 --> D3GBuffer 就不对？
    D3 -->|"是"| D4["问题在 BasePass 之前<br/>查材质 / 顶点 / 剔除"]
    D3 -->|"否"| D5["问题在光照或后处理<br/>r.DumpGPU 抓帧看 pass"]

    B -->|"闪烁 / 拖影"| E1["r.Test.FreezeTemporalHistories 1"]
    E1 --> E2冻住就稳了？
    E2 -->|"是"| E3["累积 / 重投影问题<br/>再试 ForceBlackVelocityBuffer"]
    E2 -->|"否"| E4["当帧生成问题<br/>按内容不对那条走"]

    B -->|"API 用法可疑 / 间歇崩"| F1["r.D3D12.EnableD3DDebug 1<br/>或 r.Vulkan.EnableValidation 2"]
    F1 --> F2["r.RHIValidation.DebugBreak.Transitions 1<br/>在状态转换错误处断下"]
    F2 --> F3["仍不明确 → r.RHICmdBypass 1<br/>排除命令排序 / 并行录制"]

    B -->|"Shader 编译或结果可疑"| G1["r.ShaderDevelopmentMode 1<br/>错误弹窗不静默回退"]
    G1 --> G2["r.Shaders.Symbols 1 + 重编<br/>然后 renderdoc.CaptureFrame 单步"]

    classDef entry fill:#e3f2fd,stroke:#1565c0,color:#000
    classDef act fill:#fff3e0,stroke:#e65100,color:#000
    class A,B,D3,E2 entry
    class C1,C2,C3,D1,D2,D4,D5,E1,E3,E4,F1,F2,F3,G1,G2 act
```

主线是**先分层再深入**：崩溃走 breadcrumb 定 pass，画面走 GBuffer 定阶段，
闪烁走冻结历史分当帧/历史，可疑用法走 validation。四条都先用低开销手段定位到"哪一层
哪个 pass"，再开重开销的厂商工具。

---

## 10. 关键源码文件索引

| 文件 | 内容 |
|---|---|
| `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp` | `r.DumpGPU.*` 全部声明 + `FRDGResourceDumpContext` 实现 |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphPrivate.cpp` | `r.RDG.*` 调试与验证 CVar 声明 |
| `Engine/Source/Runtime/RHI/Private/RHIBreadcrumbs.cpp` | 厂商无关的 breadcrumb 实现 |
| `Engine/Source/Runtime/RHI/Private/RHIValidation.cpp` | RHI validation 层 |
| `Engine/Source/Runtime/D3D12RHI/Private/D3D12RayTracingDebug.cpp` | DXR 验证 |
| `Engine/Source/Runtime/VulkanRHI/Private/VulkanDevice.cpp` | Vulkan validation layer 启用逻辑 |
| `Engine/Plugins/Developer/RenderDocPlugin/Source/RenderDocPlugin/Private/RenderDocPluginModule.cpp` | `renderdoc.*` CVar 与捕获命令 |
| `Engine/Source/Runtime/Engine/Public/ShowFlags.h` | `FEngineShowFlags` —— 所有 ShowFlag 的定义处 |

RDG 专属的调试手段（验证层、`r.RDG.Debug.*`、资源 dump 上下文）见
[`card-08-rdg.md`](card-08-rdg.md) 的第 8 节。

---

## 附录：不存在的 CVar 对照表

这些名字在调研阶段的文档里出现过，但 5.8 源码里**不存在**。列出来是为了防止再被引用——
它们读起来都很合理，这正是危险之处。

<!-- verify:ignore-start -->

| 调研稿里的名字 | 5.8 里的真实对应物 |
|---|---|
| `r.VisualizeBuffer` | `ShowFlag.VisualizeBuffer` + `r.BufferVisualizationOverviewTargets` |
| `r.VisualizeHDR` / `r.VisualizeSSR` / `r.VisualizeDOF` | 对应的 `ShowFlag.*` / viewmode，不是 CVar |
| `r.ShaderComplexity` | `viewmode shadercomplexity`；`r.ShaderComplexity.Baseline.*` 只调刻度 |
| `r.ShaderComplexity.Accumulate` | 无对应物 |
| `r.QuadComplexity` | `viewmode quadoverdraw` |
| `r.Wireframe` | `viewmode wireframe` / `ShowFlag.Wireframe` |
| `r.LOD` | `viewmode lodcoloration` |
| `r.Vulkan.EnableValidationLayers` | `r.Vulkan.EnableValidation`（分级：0/1/2） |
| `r.Vulkan.DumpValidation` / `r.Vulkan.OptimalValidation` / `r.Vulkan.BreakOnError` / `r.Vulkan.EnableGPUBasedValidation` | 无对应物；用 `r.Vulkan.EnableValidation 2` + `r.RHIValidation.DebugBreak.Transitions` |
| `r.Nvidia.Aftermath` | `r.GPUCrashDebugging.Aftermath` |
| `r.FastVRAM.Dump` / `r.VRAM.Dump` | 无对应物 |
| `r.ScreenShot` / `r.ScreenShot.Mode` | 控制台命令 `Shot` / `HighResShot`，不是 CVar |
| `r.CaptureNextFrame` | 控制台命令 `renderdoc.CaptureFrame` |
| `r.RHISetDebugMarker` | `r.Vulkan.DebugMarkers`（Vulkan）/ `r.ShowMaterialDrawEvents`（通用 draw event） |
| `r.DumpShaderDebugInfo.CompileMode` / `.WorkingDirectory` | `r.DumpShaderDebugInfo` 单个开关；路径见 `r.Shaders.SymbolPathOverride` |
| `r.Tonemapper.GrainQuantization` | 无对应物（`r.Tonemapper.*` 家族里没有这个） |
| `r.PostProcessing.PropagateAlpha` | 5.8 已改为项目设置里的 Alpha Channel 支持；不是这个 CVar |
| `r.RHICmdBypass.NoDrawEvents` | 无对应物；`r.RHICmdBypass` 本身存在 |

<!-- verify:ignore-end -->
