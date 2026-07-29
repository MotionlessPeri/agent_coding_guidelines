```markdown
# UE 5.8 渲染调试与诊断工具链 — 知识卡片

---

## 1. 内置调试工具

### 1.1 帧捕获与截图

| 命令 | 作用 | 用法 |
|---|---|---|
| `r.DumpGPU` | 将当前帧的所有 GPU 指令、资源、PSO 导出为 JSON + 图像，供离线分析 | `r.DumpGPU -1`（当前帧）/ `r.DumpGPU <FrameNum>` |
| `r.DumpGPU.Frame` | 指定 DumpGPU 捕获的帧范围 | `r.DumpGPU.Frame 100` |
| `r.DumpGPU.Root` | 指定输出目录 | 默认 `ProjectSavedDir/DumpGPU/` |
| `r.ScreenShot` | 截取当前画面并保存 | `r.ScreenShot`（保存到 `Screenshots/`） |
| `r.ScreenShot.Mode` | 截图模式：0=标准, 1=HDR(exr), 2=立体 | `r.ScreenShot.Mode 1` |
| `r.CaptureNextFrame` | 触发 RenderDoc 外部捕获（需已安装 RenderDoc） | `r.CaptureNextFrame 1` |
| `r.CaptureFrameAfter` | 延迟 N 帧后捕获，绕过启动帧的噪声 | `r.CaptureFrameAfter 5` |

**`r.DumpGPU` 输出结构**（每个捕获帧生成一个子目录）：

```
DumpGPU/
  Frame_0001/
    frame.json          — 完整 draw call 列表、状态、资源绑定
    <PassName>_<RT>.png — 各 RT 的渲染结果
    resources/          — 所有 buffer / texture 的导出（可选）
```

**关键限制**：`r.DumpGPU` 对性能影响极大，只适合捕获单个帧做离线分析。UE 5.8 中其 JSON 输出结构略有调整（RenderGraph 节点命名更规范），但基本机制不变。

### 1.2 可视化模式

| CVar | 作用 | 典型值 |
|---|---|---|
| `r.VisualizeBuffer` | 可视化 GBuffer 各通道 | 0=关, 1=BaseColor, 2=Specular, 3=Normal, 4=Metallic, 5=Roughness, 6=SubsurfaceColor, ... |
| `r.VisualizeLighting` | 光照可视化 | 0=关, 1=Diffuse, 2=Specular, 3=Light Complexity |
| `r.VisualizeHDR` | HDR 亮度可视化 | 0=关, 1=亮度分布, 2=区域直方图 |
| `r.VisualizeMotionBlur` | 运动模糊可视化 | 0=关, 1=速度矢量 |
| `r.VisualizeSSR` | 屏幕空间反射的可视化 | 0=关, 1=粗糙度, 2=光线数, 3=命中率 |
| `r.VisualizeDOF` | 景深可视化 | 0=关, 1=CoC 圆 |
| `r.ShaderComplexity` | 着色器复杂度（像素着色时间） | 1=开启（色彩映射到复杂度） |
| `r.ShaderComplexity.Accumulate` | 是否累计多重采样 | 0=关, 1=开 |
| `r.QuadComplexity` | 瓦片着色复杂度 | 1=开启 |
| `r.LOD` | LOD 可视化 | 0=全细节, 其他值=强制LOD级别 |
| `r.Wireframe` | 线框模式 | 1=开启 |
| `r.ShowMaterialDrawEvents` | 在 draw event 中显示材质名 | 1=开启（对 RenderDoc 捕获有用） |

### 1.3 Shader 开发模式

| CVar | 作用 |
|---|---|
| `r.ShaderDevelopmentMode=1` | 开启 Shader 开发模式。启用后：DoFD（Detail of Failure Diagnostics）默认开启，Shader 编译错误在 Editor 中即时弹窗，不静默回退 |
| `r.ShaderDevelopmentMode.SkipConsole` | 跳过控制台 Shader 编译（仅 Editor 中测试用） |
| `r.ShaderDevelopmentMode.MaterialSource` | 指定材质源路径 |
| `r.ShaderDevelopmentMode.RenderDocIntegration` | 自动启用 RenderDoc API hook |
| `r.DumpShaderDebugInfo` | 导出 shader 中间表示（HLSL → DXIL/SPIR-V）到 Saved 目录 |
| `r.DumpShaderDebugInfoShort` | 同上，但只输出编译后的 shader |
| `r.DumpShaderDebugInfo.CompileMode` | 0=仅失败时, 1=总是 |
| `r.DumpShaderDebugInfo.WorkingDirectory` | 指定输出目录 |

**`r.ShaderDevelopmentMode` 的副作用**：
- 编译速度变慢（DoFD 增加编译时间）
- 日志中 shader 信息量大幅增加
- Editor 中 shader 编译错误会弹窗而非静默回退（在亚稳态渲染分支上排查时有用）

### 1.4 其他调试 CVar

| CVar | 作用 |
|---|---|
| `r.ScreenPercentage` | 分辨率缩放，可用于调试 LOD / 纹理分辨率问题 |
| `r.ScreenPercentage.Force` | 强制覆盖渲染分辨率 |
| `r.Tonemapper.GrainQuantization` | 禁用颗粒噪声以调试后处理 |
| `r.PostProcessing.PropagateAlpha` | 后处理中保留 alpha 通道 |
| `r.FastVRAM.Dump` | 导出 VRAM 分配报告 |
| `r.RHICmdBypass` | 跳过 RHI 命令队列，直接执行（调试 draw call 排序） |
| `r.RHICmdBypass.NoDrawEvents` | 跳过 draw events 以减少开销 |

---

## 2. 外部调试工具

### 2.1 RenderDoc

**集成方式**：
- UE 5.x 内置 RenderDoc 插件（`Editor/Plugins/RenderDoc`），默认启用
- 快捷键：`Ctrl+Alt+F12` 触发捕获（Editor 中）
- `r.CaptureNextFrame 1` 通过命令行触发
- 支持 Vulkan 和 D3D12

**实用技巧**：
- 在 RenderDoc 中查看 UE 的 Event 标记（需 `r.ShowMaterialDrawEvents 1` 和 `r.RHISetDebugMarker 1`）
- 使用 RenderDoc 的 Pipeline State Viewer 查看 PSO 状态
- 原生支持 UE 5.8 RDG（Render Graph）的 Pass 命名，pass 名称在 Event Browser 中可见
- 对 Nanite 和 Lumen 的 draw call 有独立标记，但内部细节因 Mesh shader 而部分不透明

**限制**：
- UE 5.8 的 Nanite 使用 Mesh Shader 路径，RenderDoc 对 Mesh Shader 的顶点数据查看支持有限（需 2024+ 版本）
- Lumen 的 indirect dispatch 和 compute shader 链在 RenderDoc 中较难追踪

### 2.2 NVIDIA Nsight

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

### 2.3 AMD Radeon GPU Profiler (RGP)

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

### 2.4 PIX (Windows)

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

## 3. 常见渲染问题诊断

### 3.1 闪烁（Temporal 抖动、Z-Fighting）

| 症状 | 可能原因 | 排查方法 |
|---|---|---|
| 画面高频闪烁 | Temporal 累积（TAA / TSR）历史帧匹配失败 | `r.TemporalAASamples 1` 关闭 TAA；`r.TSR 0` 关闭 Temporal Super Resolution |
| 几何面闪烁/交替 | Z-Fighting | 调整摄像机近远平面；`r.DepthOfField.MaxDepth 0`（排除 DOF 影响）；`r.Shadow.CSM.ZFightingMethod` |
| 阴影闪烁 | Shadow map 精度不足 | `r.ShadowQuality 5` 最高；`r.Shadow.MaxCSMResolution` 增加 |
| 间接光照闪烁 | Lumen 逐帧收敛不一致 | `r.Lumen.DiffuseIndirect.Allow 0` 关闭 Lumen 隔离；`r.Lumen.ProbeGrid.SpatialFilter` 调整 |
| SSR 闪烁 | 屏幕空间反射历史帧匹配 | `r.SSR.Quality 0` 关闭 SSR 隔离 |

**Temporal 抖动排查流程**：
1. 关闭所有 temporal 效果：`r.TemporalAASamples 1` + `r.TSR 0` + `r.Lumen.DiffuseIndirect.Allow 0` + `r.SSR.Quality 0`
2. 逐项开启，观察哪项引入闪烁
3. 对定位到的功能，进一步调整其 temporal 参数

### 3.2 GPU Crash（TDR、Timeout）

**TDR（Timeout Detection and Recovery）**：
- Windows 默认：2 秒 GPU 无响应 → TDR 触发 → UE 崩溃
- 调整 TDR 超时以允许调试（注册表）：

```reg
[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers]
"TdrDelay"=dword:00000008    ; 8 秒
"TdrDdiDelay"=dword:00000008
```

**UE 端 TDR 相关设置**：

| CVar / 设置 | 作用 |
|---|---|
| `r.GPUCrashDebugging` | 启用 GPU crash 调试（5.8 默认开启） |
| `r.GPUCrashDebugging.Dump` | Crash 后自动导出当前 GPU 状态 |
| `r.GPUCrashDebugging.Enable` | 手动开关 |
| `r.GPUTimeout` | GPU 超时检测（ms），0=无限 |
| `r.FastVRAM.CrashDump` | VRAM 错误时触发导出 |

**GPU Crash 分析步骤**：
1. 检查 `Saved/Crashes/` 下的 crash 报告
2. 查看 GPU 相关行：`GPU Crash: ...`、`Last draw: ...`、`Last RHI command: ...`
3. `r.DumpGPU` 在 crash 前触发可捕获导致崩溃的帧
4. 检查 `Log.txt` 中的 `LogRHI` 和 `LogD3D12` 条目
5. 使用 `r.GPUCrashDebugging.Dump` 导出 crash 时 GPU 的最后状态

**常见原因**：
- Shader 编译错误导致非法 PSO → 检查 `r.DumpShaderDebugInfo`
- VRAM 耗尽 → 检查 `r.FastVRAM.Dump` 输出
- 无效 RHI 资源（已释放的 buffer/texture）→ D3D12 Debug Layer 捕获
- 驱动未适配 UE 5.8 新特性 → 更新驱动

### 3.3 内存泄漏（RHI 资源）

**监控工具**：

| CVar / 命令 | 作用 |
|---|---|
| `r.RHIResourceStats` | 显示 RHI 资源（buffer/texture）总数和内存占用 |
| `r.RHIResourceStats.Show` | 分类显示各资源类型 |
| `r.RHIResourceStats.Dump` | 导出 JSON 报告 |
| `r.TexturePool` | 纹理池状态 |
| `r.RenderTargetPool` | RT 池状态 |
| `r.RenderTargetPool.Evict` | 手动清理 RT 池 |
| `r.VRAM.Dump` | VRAM 分配报告 |
| `r.FastVRAM.Dump` | Fast VRAM 分配报告 |
| `r.DumpRHIResources` | 导出所有 RHI 资源列表 |
| `r.DumpRHIResources.Detailed` | 详细版（含分配栈） |
| `r.DumpRDGResources` | 导出 RDG 资源分配情况（UE 5.8 新增） |

**排查流程**：
1. `r.RHIResourceStats` 观测基线
2. 执行目标操作后再次查看，确认增长
3. `r.DumpRHIResources.Detailed 1` 导出带分配栈的列表
4. 对比两帧间的资源增量，找出未释放的分配
5. 对 RDG 资源：`r.DumpRDGResources` 检查 RDG 生命周期管理

### 3.4 Shader 编译问题

| 工具 | 作用 |
|---|---|
| `r.ShaderDevelopmentMode 1` | 开启后 shader 编译错误即时上报 |
| `r.DumpShaderDebugInfo 1` | 导出编译失败的 shader 源码和中间表示 |
| `r.ShaderCompiler.Stats` | 显示 shader 编译统计 |
| `r.ShaderCompiler.Cache` | Shader 缓存状态 |
| `r.ShaderPipelineCache` | PSO 缓存状态 |
| `r.ShaderPipelineCache.Log` | 导出 PSO 缓存日志 |
| `r.ShaderPipelineCache.ToggleDebug` | 切换 PSO 缓存调试模式 |

**常见问题**：
- Shader 编译失败 → 查 `r.DumpShaderDebugInfo` 输出的 HLSL 源码
- Shader 编译卡顿 → `r.ShaderCompiler.Stats` 看编译队列
- 材质编译错误 → Editor 中打开材质编辑器，查看编译日志面板
- PSO 缓存缺失 → `r.ShaderPipelineCache.Log` 导出缺失的 PSO 列表

---

## 4. Validation 层

### 4.1 D3D12 Debug Layer

**启用方式**：

```cmd
UE 启动参数：-d3d12debug
// 或通过环境变量
set D3D12_DEBUG=1
// 或代码中
ID3D12Debug5* DebugInterface;
D3D12GetDebugInterface(IID_PPV_ARGS(&DebugInterface));
DebugInterface->EnableDebugLayer();
```

**UE 5.8 相关 CVar**：

| CVar | 作用 |
|---|---|
| `r.D3D12.EnableDebugLayer` | 运行时启用 D3D12 Debug Layer |
| `r.D3D12.EnableGPUBasedValidation` | 启用 GPU-based validation |
| `r.D3D12.EnableAutoSerialization` | 自动序列化调试 |
| `r.D3D12.ValidationLevel` | 0=Minimal, 1=Basic, 2=Full |
| `r.D3D12.BreakOnError` | 在 D3D12 错误时中断（调试器 attach） |
| `r.D3D12.BreakOnWarning` | 在 D3D12 警告时中断 |

**性能影响**：D3D12 Debug Layer 性能开销极大（帧率可能掉到 1-5 FPS），只用于诊断阶段。

**启用 GPU-Based Validation**：
```
r.D3D12.EnableGPUBasedValidation 1
r.D3D12.ValidationLevel 2
```
这会在 GPU 侧验证资源状态、屏障正确性等，但需要 Debug Layer 已启用。

### 4.2 Vulkan Validation Layers

**启用方式**：

```cmd
UE 启动参数：-vulkan -vulkanvalidation
// 或通过环境变量
set VK_LAYER_PATH=<path-to-layers>
```

**UE 5.8 相关设置**：

| CVar / 配置 | 作用 |
|---|---|
| `r.Vulkan.EnableValidation` | 运行时启用 Vulkan Validation |
| `r.Vulkan.EnableValidationLayers` | 启用 Standard Validation |
| `r.Vulkan.EnableGPUBasedValidation` | GPU-based validation |
| `r.Vulkan.BreakOnError` | 错误时 debug break |
| `r.Vulkan.DumpValidation` | 导出 validation 输出到文件 |
| `r.Vulkan.OptimalValidation` | 启用所有推荐的 validation 功能 |

**要求**：
- Vulkan SDK 安装（`VK_LAYER_KHRONOS_validation`）
- 或系统已安装 Vulkan validation layers

### 4.3 UE 内置 RHI Validation

| CVar | 作用 |
|---|---|
| `r.RHI.EnableValidation` | 全局 RHI Validation 开关（UE 5.8 新增改进） |
| `r.RHI.ValidationLevel` | 0=Off, 1=Basic, 2=Detailed, 3=Full |
| `r.RHI.BreakOnRHIError` | RHI 错误时调用 `DebugBreak` |
| `r.RHI.BreakOnRHIWarning` | RHI 警告时调用 `DebugBreak` |
| `r.RHI.LogResourceLeaks` | 在 shutdown 时报告未释放的 RHI 资源 |
| `r.RHI.ValidateResourceStates` | 验证资源状态转换 |
| `r.RHI.ValidateBindings` | 验证资源绑定合法性 |
| `r.RHI.ValidatePipeline` | 验证 PSO 状态 |
| `r.RHI.DumpValidation` | 导出 validation 结果到日志文件 |

**UE 5.8 新增的 RDG Validation**：

| CVar | 作用 |
|---|---|
| `r.RDG.Validate` | RDG 资源生命周期验证 |
| `r.RDG.ValidateBindings` | RDG 绑定验证 |
| `r.RDG.ValidateAsyncCompute` | 异步计算 pass 验证 |
| `r.RDG.ValidateBarriers` | 屏障验证 |
| `r.RDG.Debug` | RDG Debug 模式（额外日志和检查） |
| `r.RDG.BreakOnError` | RDG 错误时中断 |

**层级说明**：

| Level | 内容 | 性能影响 |
|---|---|---|
| 0 (Off) | 无验证 | 无 |
| 1 (Basic) | 资源空检查、类型匹配、边界检查 | 轻微 |
| 2 (Detailed) | 状态跟踪、屏障验证、绑定一致性 | 中等 |
| 3 (Full) | 所有检查 + 资源生命周期的完整跟踪 | 显著 |

---

## 5. 关键 CVar 与命令汇总

### 帧捕获与截图

| CVar / 命令 | 描述 |
|---|---|
| `r.DumpGPU <n>` | 捕获第 n 帧的 GPU 状态 |
| `r.DumpGPU.Frame <start>-<end>` | 范围捕获 |
| `r.DumpGPU.Root <path>` | 输出目录 |
| `r.DumpGPU.DumpResources` | 同时导出所有资源 |
| `r.ScreenShot` | 截图 |
| `r.ScreenShot.Mode <0/1/2>` | 截图模式 |
| `r.CaptureNextFrame <0/1>` | 触发 RenderDoc 捕获 |
| `r.CaptureFrameAfter <n>` | 延迟捕获 |

### 可视化模式

| CVar | 描述 |
|---|---|
| `r.VisualizeBuffer <0-16>` | GBuffer 通道可视化 |
| `r.VisualizeLighting <0-3>` | 光照可视化 |
| `r.VisualizeHDR <0-2>` | HDR 可视化 |
| `r.VisualizeMotionBlur <0/1>` | 运动模糊速度场 |
| `r.VisualizeSSR <0-3>` | SSR 可视化 |
| `r.VisualizeDOF <0/1>` | 景深 CoC 可视化 |
| `r.VisualizeBloom <0-3>` | Bloom 各层可视化 |
| `r.ShaderComplexity <0/1>` | 着色复杂度 |
| `r.QuadComplexity <0/1>` | 瓦片复杂度 |
| `r.Wireframe <0/1>` | 线框模式 |

### Shader 调试

| CVar | 描述 |
|---|---|
| `r.ShaderDevelopmentMode <0/1>` | Shader 开发模式 |
| `r.DumpShaderDebugInfo <0/1>` | 导出 shader 调试信息 |
| `r.DumpShaderDebugInfoShort <0/1>` | 精简导出 |
| `r.ShaderCompiler.Stats` | 编译统计 |
| `r.ShaderPipelineCache.Log` | PSO 缓存日志 |
| `r.ShaderPipelineCache.ToggleDebug` | 缓存调试模式 |

### GPU 诊断

| CVar | 描述 |
|---|---|
| `r.GPUCrashDebugging <0/1>` | GPU crash 调试 |
| `r.GPUCrashDebugging.Dump` | Crash 时导出 GPU 状态 |
| `r.GPUTimeout <ms>` | GPU 超时阈值 |
| `r.RHIResourceStats` | RHI 资源统计 |
| `r.RHIResourceStats.Dump` | 导出资源统计报告 |
| `r.RenderTargetPool` | RT 池状态 |
| `r.RenderTargetPool.Evict` | 清理 RT 池 |
| `r.VRAM.Dump` | VRAM 报告 |
| `r.FastVRAM.Dump` | Fast VRAM 报告 |
| `r.DumpRHIResources` | 导出所有 RHI 资源 |
| `r.DumpRDGResources` | 导出 RDG 资源 (5.8) |

### Validation

| CVar | 描述 |
|---|---|
| `r.RHI.EnableValidation <0/1>` | RHI Validation 开关 |
| `r.RHI.ValidationLevel <0-3>` | Validation 级别 |
| `r.RHI.BreakOnRHIError <0/1>` | 错误时中断 |
| `r.RHI.LogResourceLeaks <0/1>` | 资源泄漏检测 |
| `r.RHI.ValidateResourceStates` | 资源状态验证 |
| `r.RDG.Validate <0/1>` | RDG 验证 (5.8) |
| `r.D3D12.EnableDebugLayer <0/1>` | D3D12 Debug Layer |
| `r.D3D12.EnableGPUBasedValidation` | GPU-based validation |
| `r.Vulkan.EnableValidation <0/1>` | Vulkan Validation |

### 性能分析

| CVar | 描述 |
|---|---|
| `r.GPUTrace <0/1>` | GPU Time trace |
| `r.GPUTrace.SampleCount <n>` | 采样帧数 |
| `r.GPUTrace.Output` | 输出路径 |
| `r.ProfileGPU <0/1>` | GPU 性能分析 |
| `r.ProfileGPU.ShowEventHistory` | 事件历史 |
| `r.ProfileGPU.ShowEvents` | 显示 GPU 事件 |
| `r.ProfileGPU.Trimmed` | 精简输出 |
| `stat gpu` | 实时 GPU 统计 |
| `stat rdg` | RDG 统计 (5.8) |
| `stat rhi` | RHI 统计 |
| `stat memory` | 内存统计 |

---

## 6. 调试工作流速查

### 帧率/性能问题 → GPU 瓶颈定位

```
stat gpu            → 查看每个 pass 耗时
r.GPUTrace 1        → 捕获详细 GPU trace
r.ProfileGPU 1      → 看 CPU 端 submit 耗时
r.ProfileGPU.Trimmed 1 → 精简输出
```

### 渲染错误/画面异常 → 逐层隔离

```
r.VisualizeBuffer 0 → 看 GBuffer 各层
r.ShaderComplexity 1 → 看哪个像素最贵
r.TemporalAASamples 1 → 关闭 TAA
r.TSR 0            → 关闭 TSR
r.Lumen.DiffuseIndirect.Allow 0 → 关闭 Lumen
```

### GPU Crash → 取证

```
r.GPUCrashDebugging 1
r.DumpGPU -1        → 捕获 crash 帧
r.D3D12.EnableDebugLayer 1 → 用 validation 复现
r.RHI.LogResourceLeaks 1
```

### Shader 问题 → 编译诊断

```
r.ShaderDevelopmentMode 1
r.DumpShaderDebugInfo 1
r.DumpShaderDebugInfo.CompileMode 1
```

### 内存泄漏 → 资源追踪

```
r.RHIResourceStats
r.DumpRHIResources.Detailed 1
启动参数 -d3d12debug → D3D12 Debug Layer 报告泄漏
r.RHI.LogResourceLeaks 1
```

---

**Sources**：本卡片基于 UE 5.8 引擎源码（`Engine/Source/Runtime/RenderCore/`, `Engine/Source/Runtime/D3D12RHI/`, `Engine/Source/Runtime/VulkanRHI/`, `Engine/Source/Runtime/RenderGraph/`）中 ConsoleVariables 和 Debug 功能的实现，以及 UE 官方文档（`docs.unrealengine.com`）中关于渲染调试工具链的内容综合整理。
```

---

**审校说明**（未在改写中体现，供你参考）：

1. **文体**：原文整体质量较高，主要改动了三处——"静默 fallback" → "静默回退"（半通用 CS 词本地化）、"自动 dump" → "自动导出"（动词 dump 本地化）、"极其昂贵" → "性能开销极大"（更正式的技术文档用语）。"时间线"保留，"timeline"出现在括号内给 GPU 性能分析术语时保留原文与中文混排。

2. **图示**：原文无 ASCII art 框图（第 1.1 节的目录树使用代码块格式，符合"树形结构 → 缩进列表即可，不要画图"的原则，无需改为 Mermaid）。第 3.1 节排查流程是 3 步编号列表，第 6 节是命令序列代码块，均不适用 Mermaid。

3. **结构**：原文已采用"结论先于细节"的组织方式——表格先列出 CVar 再给说明，排查流程先给症状表再给步骤。未做结构性重组。