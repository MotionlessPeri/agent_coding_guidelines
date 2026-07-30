# UE 渲染知识地图

> **验证状态**：§3 源码索引与 §4 CVar 速查表由脚本从 UE 5.8.0 源码生成——路径逐条断言存在，
> 「关键符号」一列**从文件里自动抽取**而非人工填写，所以不会出现「文件真、符号假」的组合。
> §1 知识树 / §2 卡片索引 / §5 学习路径是结构性内容，不含源码断言。
> 重生成：见 §3 段首说明。
> 校验：`python scripts/verify-ue-rendering-refs.py`（机械核对全库路径 / CVar / 符号三类断言是否真的存在于引擎源码）

---

## 1. 知识树结构

- **1. 性能优化 (Performance Optimization) [🔴 最高频]**
  - **1.1 性能分析工具链**
    - Unreal Insights (GPU Profiling)
    - ProfileGPU / stat GPU [🔴]
    - GPU Visualizer (r.VisualizeGPU) [🔴]
    - RenderDoc 集成 [🔴]
    - 第三方计数器 (Nsight / RGP / PIX) [🟡]
  - **1.2 瓶颈定位方法论**
    - 三端确认 (Game/Render/GPU Thread) [🔴]
    - Pass 级热点定位 [🔴]
    - Shader 复杂度分析 [🔴]
    - Overdraw 与半透明排序 [🔴]
    - 带宽瓶颈分析 [🟡]
  - **1.3 渲染分辨率策略**
    - r.ScreenPercentage + TSR 上采样 [🔴]
    - 动态分辨率 (r.DynamicRes.*) [🟡]
    - 半分辨率 / 1/4 分辨率 Pass [🟡]
  - **1.4 Lumen 降级策略 [🔴]**
    - 三种追踪模式切换 [🔴]
    - 关键 CVar 组合 [🔴]
    - 降级路径 (Hardware RT → Screen Probe → SSAO) [🔴]
  - **1.5 Nanite 裁剪 [🟡]**
    - MaxPixelsPerEdge / ViewDistance [🟡]
    - Page Pool 管理 [🟡]
    - FilterOutSmallObjects [🟢]
  - **1.6 Shadow 优化 [🔴]**
    - CSM 级数与分辨率 [🔴]
    - Shadow Distance 裁剪 [🔴]
    - Contact Shadows 开关 [🔴]
    - Virtual Shadow Map [🟡]
  - **1.7 PostProcessing 裁剪 [🔴]**
    - Bloom / MotionBlur / DOF / LensFlare [🔴]
    - Tonemapper / Vignette / EyeAdaptation [🟡]
  - **1.8 异步计算优化 [🟡]**
    - r.AsyncCompute.* 系列 [🟡]
    - Lumen 异步计算 [🟡]
    - Console 异步计算最佳实践 [🟡]
  - **1.9 移动端性能优化 [🔴]**
    - Mobile HDR / Forward Shading [🔴]
    - Vulkan Mobile 优化 [🔴]
    - 发热与降频控制 [🔴]
    - 移动 GPU 架构差异 (Mali/Adreno/Apple) [🟡]

- **2. 效果定制 (Custom Rendering) [🔴 高频]**
  - **2.1 自定义后处理效果 [🔴]**
    - FGlobalShader + SHADER_PARAMETER_STRUCT [🔴]
    - RDG AddPass 注册 [🔴]
    - 后处理 Hook 点 (PostProcessing.cpp) [🔴]
    - HLSL 编写 (Common.ush / MaterialTemplate.ush) [🟡]
  - **2.2 自定义渲染 Pass 注入 [🟡]**
    - FSceneRenderer::Render 阶段顺序 [🟡]
    - FMeshPassProcessor 注册 [🟡]
    - RDG 资源管理 (RegisterExternal / QueueExtraction) [🟡]
    - NeverCull 与 Pass Culling [🟡]
  - **2.3 Lumen 定制 [🔴]**
    - 追踪模式选择 [🔴]
    - 反射与 SSR 混合策略 [🔴]
    - Lumen Scene 数据结构 [🟡]
    - 自定义 GI 替代路径 [🟢]
  - **2.4 自定义材质系统扩展 [🟡]**
    - Substrate 多层 BSDF [🟡]
    - 自定义 Shading Model [🟡]
    - GBuffer 扩展 [🟡]
    - UMaterialExpression 编写 [🟡]
    - Substrate vs Legacy 互操作 [🟡]
  - **2.5 Nanite 适配与定制 [🟡]**
    - 兼容性检查 (半透明/WPO/Decal) [🟡]
    - 自定义剔除回调 [🟢]
    - Nanite + 传统渲染混合 [🟡]
    - Cook 管线定制 [🟢]

- **3. 平台适配 (Platform Adaptation) [🔴 高频]**
  - **3.1 Feature Level 系统 [🔴]**
    - ES3_1 / SM5 / SM6 功能差异 [🔴]
    - IsFeatureLevelSupported() 判断链 [🔴]
    - 降级策略 [🔴]
  - **3.2 Desktop 渲染路径 [🔴]**
    - D3D12 (默认) [🔴]
    - Vulkan Desktop [🟡]
    - Deferred vs Forward [🔴]
  - **3.3 Mobile 渲染路径 [🔴]**
    - OpenGL ES 3.1 [🟡]
    - Vulkan Mobile [🔴]
    - Metal (iOS/tvOS) [🟡]
    - Mobile Forward / Deferred [🔴]
  - **3.4 Console 平台 [🟡]**
    - PS5 (Geometry Engine) [🟡]
    - Xbox Series X|S (Mesh Shader) [🟡]
    - ESRAM 管理 (Xbox One) [🟢]
  - **3.5 VR 渲染 [🟡]**
    - Instanced Stereo [🟡]
    - Fixed Foveated Rendering [🟡]
    - 多视口渲染 [🟡]
    - OpenXR 集成 [🟡]
    - 移动 VR (Quest) [🟡]
  - **3.6 渲染管线裁剪 [🔴]**
    - 按平台裁剪 Pass [🔴]
    - 按硬件能力裁剪 Shader Feature [🔴]
    - 按内存限制裁剪资源精度 [🔴]
    - ShouldCompilePermutation() 裁剪入口 [🔴]

- **4. 调试诊断 (Debug & Diagnosis) [🔴 高频]**
  - **4.1 帧捕获与截图 [🔴]**
    - r.DumpGPU [🔴]
    - RenderDoc 捕获 [🔴]
    - r.ScreenShot [🟡]
  - **4.2 可视化模式 [🔴]**
    - r.VisualizeBuffer (GBuffer) [🔴]
    - r.VisualizeLighting [🔴]
    - r.ShaderComplexity [🔴]
    - r.VisualizeHDR / SSR / DOF / MotionBlur [🟡]
    - r.Wireframe / LOD / QuadComplexity [🟡]
  - **4.3 Shader 开发模式 [🔴]**
    - r.ShaderDevelopmentMode [🔴]
    - r.DumpShaderDebugInfo [🔴]
    - 编译错误诊断 [🔴]
  - **4.4 GPU Crash 诊断 [🟡]**
    - TDR 机制 [🟡]
    - r.GPUCrashDebugging [🟡]
    - Crash 报告分析 [🟡]
  - **4.5 内存与显存诊断 [🟡]**
    - r.RHIResourceStats [🟡]
    - r.VRAM.Dump / r.FastVRAM.Dump [🟡]
    - r.RenderTargetPool [🟡]
    - r.DumpRHIResources [🟡]
  - **4.6 Validation 层 [🟡]**
    - D3D12 Debug Layer [🟡]
    - Vulkan Validation Layers [🟡]
    - r.RHI.EnableValidation [🟡]
    - r.RDG.Validate (UE 5.8) [🟡]

- **5. 工具链 (Toolchain) [🟡 中频]**
  - **5.1 渲染管线架构 [🔴]**
    - 三级流水线 (Main → Render → RHI) [🔴]
    - FSceneRenderer::Draw 流程 [🔴]
    - Deferred vs Mobile 分支 [🔴]
    - 渲染线程同步原语 [🔴]
  - **5.2 RHI 抽象层 [🔴]**
    - 三层命令体系 [🔴]
    - RHI 线程模型 [🔴]
    - 核心资源类型 (Buffer/Texture/View) [🔴]
    - 资源生命周期管理 [🔴]
    - GPU 同步 (Fence/Barrier) [🔴]
    - 平台差异 (D3D12 vs Vulkan) [🟡]
  - **5.3 RDG (Render Dependency Graph) [🔴]**
    - FRDGBuilder 三阶段模型 [🔴]
    - Pass 注册方式 (Lambda / 完整类) [🔴]
    - 资源声明与生命周期 [🔴]
    - Barrier 自动推导 [🔴]
    - Pass Culling 机制 [🟡]
    - 跨帧资源传递 [🟡]
  - **5.4 Shader 编译管线 [🔴]**
    - 材质系统链条 (Material → FShader) [🔴]
    - HLSL 生成机制 [🔴]
    - SCW 外部进程模型 [🔴]
    - Shader Permutation 系统 [🔴]
    - Substrate 材质系统 [🟡]
    - Shader 调试 [🔴]
  - **5.5 Lumen 系统 [🔴]**
    - 三种 GI 追踪模式 [🔴]
    - Screen Probe 模式 [🟡]
    - Mesh Card + Surface Cache [🟡]
    - Hardware RT 模式 [🟡]
    - Lumen Reflections [🔴]
    - 性能调优与降级 [🔴]
  - **5.6 Nanite 系统 [🟡]**
    - Cluster / Page / Group 层级 [🟡]
    - Persistent LOD 选择 [🟡]
    - Visibility Buffer [🟡]
    - 流式加载与 Page Pool [🟡]
    - Overdraw 消除 [🟡]
    - 性能调优 [🟡]

- **6. 前沿 (Frontier) [🟢 低频]**
  - 6.1 UE 5.8 渲染新特性
  - 6.2 Substrate 材质系统演进
  - 6.3 官方 MCP (Model Context Protocol)
  - 6.4 Nanite 未来发展
  - 6.5 异步计算与 GPU 编排

---

## 2. 知识卡片索引

### 2.1 性能优化领域

| 知识卡片 | 关联领域 | 关键源码文件 | 学习优先级 | 前置知识 |
|----------|----------|-------------|-----------|---------|
| 性能分析工具链 | 1.1 | `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp` | P0 | 无 |
| ProfileGPU / stat GPU | 1.1 | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp` | P0 | 无 |
| GPU Visualizer | 1.1 | `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp` | P0 | 无 |
| RenderDoc 集成 | 1.1 | `Engine/Plugins/Editor/RenderDocPlugin/` | P0 | 无 |
| 分辨率缩放策略 | 1.3 | `Engine/Source/Runtime/Engine/Private/SceneView.cpp` | P0 | TSR 原理 |
| Lumen 降级策略 | 1.4 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenSceneRendering.cpp` | P0 | Lumen 架构 |
| Shadow 优化 | 1.6 | `Engine/Source/Runtime/Renderer/Private/ShadowRendering.cpp` | P0 | 阴影原理 |
| PostProcessing 裁剪 | 1.7 | `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` | P0 | 后处理管线 |
| 移动端性能优化 | 1.9 | `Engine/Source/Runtime/Renderer/Private/MobileShadingRenderer.cpp` | P0 | Mobile 渲染路径 |
| Nanite 裁剪 | 1.5 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteCullRaster.cpp` | P1 | Nanite 架构 |
| 异步计算优化 | 1.8 | `Engine/Source/Runtime/RenderCore/Private/RenderGraphBuilder.cpp` | P1 | 渲染线程模型 |
| 各 GPU 架构差异 | 1.9 | 厂商 SDK 文档 | P1 | GPU 硬件知识 |

### 2.2 效果定制领域

| 知识卡片 | 关联领域 | 关键源码文件 | 学习优先级 | 前置知识 |
|----------|----------|-------------|-----------|---------|
| 自定义后处理效果 | 2.1 | `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` | P0 | RDG、Shader 编写 |
| FGlobalShader 编写 | 2.1 | `Engine/Source/Runtime/RenderCore/Public/GlobalShader.h` | P0 | HLSL、C++ |
| RDG Pass 注册 | 2.1 | `Engine/Source/Runtime/RenderCore/Public/RenderGraphBuilder.h` | P0 | RDG 架构 |
| 自定义渲染 Pass 注入 | 2.2 | `Engine/Source/Runtime/Renderer/Private/DeferredShadingRenderer.cpp` | P1 | 渲染管线调度 |
| FMeshPassProcessor 注册 | 2.2 | `Engine/Source/Runtime/Renderer/Private/MeshPassProcessor.cpp` | P1 | Mesh 绘制管线 |
| Lumen 定制 | 2.3 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenReflections.cpp` | P0 | Lumen 架构 |
| 自定义材质系统 | 2.4 | `Engine/Source/Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp` | P1 | 材质系统、HLSL |
| Substrate 材质 | 2.4 | `Engine/Shaders/Private/Substrate/Substrate.ush` | P1 | PBR 理论 |
| GBuffer 扩展 | 2.4 | `Engine/Source/Runtime/RenderCore/Public/GBufferInfo.h` | P1 | GBuffer 布局 |
| Nanite 适配 | 2.5 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteMaterials.cpp` | P1 | Nanite 架构 |

### 2.3 平台适配领域

| 知识卡片 | 关联领域 | 关键源码文件 | 学习优先级 | 前置知识 |
|----------|----------|-------------|-----------|---------|
| Feature Level 系统 | 3.1 | `Engine/Source/Runtime/RHI/Public/RHI.h` | P0 | 无 |
| Desktop D3D12 路径 | 3.2 | `Engine/Source/Runtime/D3D12RHI/Private/D3D12RHI.cpp` | P0 | D3D12 基础 |
| Desktop Vulkan 路径 | 3.2 | `Engine/Source/Runtime/VulkanRHI/Private/VulkanRHI.cpp` | P1 | Vulkan 基础 |
| Mobile 渲染路径 | 3.3 | `Engine/Source/Runtime/Renderer/Private/MobileShadingRenderer.cpp` | P0 | 移动 GPU 架构 |
| Vulkan Mobile | 3.3 | `Engine/Source/Runtime/VulkanRHI/Private/VulkanRHI.cpp` | P0 | Vulkan 基础 |
| Metal RHI | 3.3 | `Engine/Source/Runtime/Apple/MetalRHI/Private/MetalRHI.cpp` | P1 | Metal 基础 |
| PS5 优化 | 3.4 | GDK SDK (非公开) | P1 | Console 开发 |
| Xbox Series X|S 优化 | 3.4 | GDK SDK (非公开) | P1 | Console 开发 |
| VR Instanced Stereo | 3.5 | `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp` | P1 | VR 渲染基础 |
| VR Fixed Foveated Rendering | 3.5 | `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` | P1 | VRS 机制 |
| 渲染管线裁剪 | 3.6 | `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` | P0 | 渲染管线架构 |

### 2.4 调试诊断领域

| 知识卡片 | 关联领域 | 关键源码文件 | 学习优先级 | 前置知识 |
|----------|----------|-------------|-----------|---------|
| r.DumpGPU | 4.1 | `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp` | P0 | 无 |
| RenderDoc 捕获 | 4.1 | RenderDoc 文档 | P0 | 无 |
| GBuffer 可视化 | 4.2 | `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessBufferInspector.cpp` | P0 | GBuffer 布局 |
| ShaderComplexity | 4.2 | `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessVisualizeComplexity.cpp` | P0 | 无 |
| Shader 开发模式 | 4.3 | `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` | P0 | Shader 编译 |
| GPU Crash 诊断 | 4.4 | `Engine/Source/Runtime/RHI/Private/RHIBreadcrumbs.cpp` | P1 | GPU 调试经验 |
| 显存诊断 | 4.5 | `Engine/Source/Runtime/RHI/Private/RHIStats.cpp` | P1 | GPU 内存管理 |
| D3D12 Debug Layer | 4.6 | `Engine/Source/Runtime/D3D12RHI/Private/D3D12RayTracingDebug.cpp` | P1 | D3D12 基础 |
| Vulkan Validation | 4.6 | `Engine/Source/Runtime/RHI/Private/RHIValidation.cpp` | P1 | Vulkan 基础 |
| RDG Validation | 4.6 | `Engine/Source/Runtime/RenderCore/Private/RenderGraphValidation.cpp` | P1 | RDG 架构 |

### 2.5 工具链领域

| 知识卡片 | 关联领域 | 关键源码文件 | 学习优先级 | 前置知识 |
|----------|----------|-------------|-----------|---------|
| 三级渲染流水线 | 5.1 | `Engine/Source/Runtime/RenderCore/Private/RenderingThread.cpp` | P0 | 多线程基础 |
| FSceneRenderer::Draw | 5.1 | `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp` | P0 | 渲染管线基础 |
| RHI 命令体系 | 5.2 | `Engine/Source/Runtime/RHI/Public/RHICommandList.h` | P0 | 无 |
| RHI 资源类型 | 5.2 | `Engine/Source/Runtime/RHI/Public/RHIResources.h` | P0 | 无 |
| GPU 同步 (Fence/Barrier) | 5.2 | `Engine/Source/Runtime/RHI/Public/RHIAccess.h` | P0 | GPU 管线基础 |
| RDG 核心 | 5.3 | `Engine/Source/Runtime/RenderCore/Public/RenderGraphBuilder.h` | P0 | 渲染管线基础 |
| RDG 资源管理 | 5.3 | `Engine/Source/Runtime/RenderCore/Public/RenderGraphResources.h` | P0 | 无 |
| 材质系统链条 | 5.4 | `Engine/Source/Runtime/Engine/Public/MaterialShared.h` | P0 | 材质编辑器使用 |
| HLSL 生成 | 5.4 | `Engine/Source/Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp` | P0 | HLSL |
| Shader 编译管线 | 5.4 | `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` | P0 | 编译原理 |
| Shader Permutation | 5.4 | `Engine/Source/Runtime/RenderCore/Public/ShaderPermutation.h` | P0 | 无 |
| Lumen 三种追踪模式 | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenSceneRendering.cpp` | P0 | 全局光照基础 |
| Lumen Screen Probe | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenScreenProbeGather.cpp` | P1 | 无 |
| Lumen Mesh Card | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenMeshCards.cpp` | P1 | 无 |
| Lumen Hardware RT | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenHardwareRayTracingCommon.cpp` | P1 | DXR 基础 |
| Lumen Reflections | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenReflections.cpp` | P0 | 反射原理 |
| Nanite 核心架构 | 5.6 | `Engine/Shaders/Shared/NaniteDefinitions.h` | P1 | 几何处理基础 |
| Nanite Visibility Buffer | 5.6 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteCullRaster.cpp` | P1 | 延迟渲染 |
| Nanite 流式加载 | 5.6 | `Engine/Source/Runtime/Engine/Private/Rendering/NaniteStreamingManager.cpp` | P1 | 内存管理 |
| Nanite 性能调优 | 5.6 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteCullRaster.cpp` | P1 | GPU 架构 |

---

## 3. 关键源码文件速查表

路径相对**引擎根目录**（含 `Engine/` 的那一层）。全部逐条断言在 UE 5.8 中存在——
生成脚本遇到不存在的路径会直接报错。「关键符号」一列由脚本从文件里自动抽取，
不是人工填写，所以不会出现「文件真、符号假」的组合。

| 文件（相对引擎根） | 子系统 | 一句话功能 | 关键符号（自动抽取） |
|---|---|---|---|
| `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp` | 渲染管线调度 | 渲染入口，FSceneRenderer 调度所有 Pass | `FScreenPercentageHellDriver`, `FCrossGPUTransfersDeferred`, `FScenePrimitiveRenderingContext` |
| `Engine/Source/Runtime/Renderer/Private/DeferredShadingRenderer.cpp` | 延迟渲染 | 延迟着色主流程：BasePass → Lights → PostProcessing | `Lumen`, `Nanite`, `RayTracingDebug` |
| `Engine/Source/Runtime/Renderer/Private/MobileShadingRenderer.cpp` | 移动端渲染 | 移动端渲染主流程 | `FMobileDirLightShaderParamsRenderResource`, `FMobileDeferredCopyPLSPS`, `FMobileDeferredCopyDepthPS` |
| `Engine/Source/Runtime/Renderer/Private/SceneVisibility.cpp` | 可见性计算 | InitViews 核心：可见性裁剪、阴影分配 | `FFrustumCullingFlags`, `FViewAllocationInfo`, `DoOcclusionQueries` |
| `Engine/Source/Runtime/Renderer/Private/BasePassRendering.cpp` | GBuffer 写入 | BasePass，把不透明 Mesh 渲进 GBuffer | `IMPLEMENT_BASEPASS_MESHSHADER_TYPE`, `IMPLEMENT_BASEPASS_VERTEXSHADER_TYPE`, `IMPLEMENT_BASEPASS_PIXELSHADER_TYPE` |
| `Engine/Source/Runtime/Renderer/Private/LightRendering.cpp` | 光照计算 | 延迟光照 Pass | `FStencilConeIndexBuffer`, `FStencilConeVertexBuffer`, `FDeferredLightHairVS` |
| `Engine/Source/Runtime/Renderer/Private/ShadowRendering.cpp` | 阴影渲染 | 阴影投射与 Shadow Map 渲染 | `FDummyWholeSceneDirectionalShadowStencilVertexBuffer`, `TOnePassPointShadowProjectionPS`, `FFrustumVertexBuffer` |
| `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` | 后处理 | 后处理管线编排，含 AddPostProcessingPasses | `FGBufferPickingCS`, `EPass`, `IsMobileEyeAdaptationEnabled` |
| `Engine/Source/Runtime/Renderer/Private/TranslucentRendering.cpp` | 半透明渲染 | 半透明物体渲染 | `FCopySceneColorPS`, `FEncodeSceneColorCopy`, `FCopyBackgroundVisibilityPS` |
| `Engine/Source/Runtime/Renderer/Private/DecalRenderingShared.cpp` | Decal 渲染 | Decal 写入 GBuffer 的共享逻辑 | `FDeferredDecalVS`, `FDeferredDecalPS`, `FDeferredDecalEmissivePS` |
| `Engine/Source/Runtime/RenderCore/Public/RenderGraphBuilder.h` | RDG 核心 API | FRDGBuilder 全部公开 API | `FRDGBuilder`, `FRDGAsyncComputeBudgetScopeGuard`, `FRHITransientBuffer` |
| `Engine/Source/Runtime/RenderCore/Public/RenderGraphResources.h` | RDG 资源 | RDG 资源抽象与描述符 | `FRDGBarrierBatchBegin`, `FRDGBarrierValidation`, `FRDGBuffer` |
| `Engine/Source/Runtime/RenderCore/Public/RenderGraphPass.h` | RDG Pass | Pass 类型体系与 Barrier 批处理 | `FRDGDispatchPassBuilder`, `FRDGBarrierBatchBegin`, `FRDGBarrierBatchEnd` |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphBuilder.cpp` | RDG 执行 | Execute / Compile / Culling 实现 | `FParallelPassSet`, `FTaskContext`, `ERDGTextureAccessFlags` |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphAllocator.cpp` | RDG 内存管理 | RDG 分配器 | — |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphValidation.cpp` | RDG 验证 | RDG 用法验证层 | — |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphPrivate.cpp` | RDG 调试 CVar | r.RDG.* 全部 CVar 声明处 | `IsDebugAllowedForGraph`, `IsDebugAllowedForPass`, `IsDebugAllowedForResource` |
| `Engine/Source/Runtime/RHI/Public/RHICommandList.h` | RHI 命令列表 | RHI 命令列表核心定义 | `FApp`, `FBlendStateInitializerRHI`, `FGraphicsPipelineStateInitializer` |
| `Engine/Source/Runtime/RHI/Public/DynamicRHI.h` | RHI 抽象接口 | 平台无关 RHI 抽象基类 | `FBlendStateInitializerRHI`, `FGraphicsPipelineStateInitializer`, `FReadSurfaceDataFlags` |
| `Engine/Source/Runtime/RHI/Public/RHIResources.h` | RHI 资源类型 | Texture / Buffer / View / Fence 等资源类型 | `FHazardPointerCollection`, `FRHIComputeCommandList`, `FRHICommandListImmediate` |
| `Engine/Source/Runtime/RHI/Public/RHIAccess.h` | RHI 屏障 | ERHIAccess 状态定义 | `FString`, `ERHIAccess` |
| `Engine/Source/Runtime/RHI/Private/RHIValidation.cpp` | RHI 验证层 | RHI 用法验证 | `FRHIValidationQueueScope`, `FInit`, `FResourceBinder` |
| `Engine/Source/Runtime/RHI/Private/RHIBreadcrumbs.cpp` | RHI 面包屑 | 厂商无关的 GPU 崩溃定位 | — |
| `Engine/Source/Runtime/RenderCore/Private/RenderingThread.cpp` | 渲染线程 | 渲染线程启动与同步 | `FRHIThread`, `FRenderingThread`, `FRenderingThreadTickHeartbeat` |
| `Engine/Source/Runtime/D3D12RHI/Private/D3D12RHI.cpp` | D3D12 RHI | D3D12 平台实现入口 | `D3D12_PLATFORM_NEEDS_DISPLAY_MODE_ENUMERATION` |
| `Engine/Source/Runtime/D3D12RHI/Private/D3D12CommandContext.cpp` | D3D12 命令 | D3D12 命令上下文 | — |
| `Engine/Source/Runtime/D3D12RHI/Private/D3D12Resources.cpp` | D3D12 资源 | D3D12 资源管理（注意是复数 Resources） | `FD3D12UpdateTileMappingsParams` |
| `Engine/Source/Runtime/VulkanRHI/Private/VulkanRHI.cpp` | Vulkan RHI | Vulkan 平台实现入口 | `FPhysicalDeviceInfo`, `FHashKey`, `FNonStateHashKey` |
| `Engine/Source/Runtime/VulkanRHI/Private/VulkanCommands.cpp` | Vulkan 命令 | Vulkan 命令录制 | `FVulkanResourceBinder`, `BindUniformBuffer`, `SetShaderParametersOnBinder` |
| `Engine/Source/Runtime/VulkanRHI/Private/VulkanPipelineState.cpp` | Vulkan PSO | Vulkan 管线状态 | `ShouldAlwaysWriteDescriptors`, `SetDefaultDescriptorsForMissingBuffers` |
| `Engine/Source/Runtime/Engine/Public/MaterialShared.h` | 材质系统 | FMaterial / FMaterialResource / ShaderMap | `FCbFieldView`, `FCbWriter`, `FMaterial` |
| `Engine/Source/Runtime/Engine/Public/Materials/Material.h` | 材质资产 | UMaterial 资产定义 | `ITargetPlatform`, `UMaterialExpressionComment`, `UPhysicalMaterial` |
| `Engine/Source/Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp` | HLSL 生成 | 材质表达式 → HLSL | `FCsvLogFile`, `FHLSLMaterialTranslator`, `FSubstrateTranslatorDataInterface` |
| `Engine/Source/Runtime/Engine/Public/ShaderCompiler.h` | Shader 编译 | 编译任务与队列 | `FAsyncCompilationNotification`, `FCbObjectView`, `FCbWriter` |
| `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` | Shader 编译调度 | 主进程编译调度 | `FRecompileShadersTimer`, `FGlobalComputePSOPrecacheData`, `ShaderCompiler` |
| `Engine/Source/Runtime/RenderCore/Public/ShaderPermutation.h` | Permutation | Permutation 域与裁剪 | `TShaderPermutationDomainSpetialization`, `FShaderCompilerEnvironment`, `FShaderPermutationParameters` |
| `Engine/Source/Runtime/RenderCore/Public/GlobalShader.h` | Global Shader | FGlobalShader 基类与注册宏 | `FArchive`, `FShaderCommonCompileJob`, `FShaderCompileJob` |
| `Engine/Source/Runtime/RenderCore/Public/ShaderParameterMacros.h` | Shader 参数宏 | SHADER_PARAMETER / RDG 参数宏 | `FRDGTexture`, `FRDGTextureSRV`, `FRDGTextureUAV` |
| `Engine/Source/Runtime/RenderCore/Public/Shader.h` | Shader 核心 | FShader 基类与序列化 | `ITargetPlatform`, `FCbFieldView`, `FCbWriter` |
| `Engine/Shaders/Private/MaterialTemplate.ush` | 材质模板 | 材质 HLSL 模板 | `FSubstrateData`, `FMaterialParticleParameters`, `FPixelMaterialInputs` |
| `Engine/Source/Runtime/Engine/Public/SceneView.h` | 场景视图 | FSceneView 定义 | `FSceneView`, `FSceneInterface`, `FSceneViewFamily` |
| `Engine/Source/Runtime/Engine/Public/StereoRendering.h` | 立体渲染 | EStereoscopicPass 定义处 | `FSceneView`, `IStereoLayers`, `IStereoRenderTargetManager` |
| `Engine/Source/Runtime/RHI/Public/RHIFeatureLevel.h` | Feature Level | ERHIFeatureLevel 枚举 | `FGenericStaticFeatureLevel`, `ERHIFeatureLevel`, `USE_STATIC_FEATURE_LEVEL_ENUMS` |
| `Engine/Source/Runtime/RHI/Public/RHIShaderPlatform.h` | Shader Platform | EShaderPlatform 枚举 | `FStaticShaderPlatform`, `DDPI_NUM_STATIC_SHADER_PLATFORMS` |
| `Engine/Source/Runtime/Engine/Public/ShowFlags.h` | ShowFlag | FEngineShowFlags —— 所有 ShowFlag 定义处 | `FEngineShowFlags`, `TCustomShowFlag`, `ECustomShowFlag` |
| `Engine/Shaders/Shared/NaniteDefinitions.h` | Nanite 定义 | Nanite 共享数据结构 | `FNaniteMaterialFlags`, `FNaniteStats`, `FNanitePickingFeedback` |
| `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteCullRaster.cpp` | Nanite 剔除光栅 | Nanite 剔除与光栅化主流程 | `FNaniteCurveClusterParameters`, `FRasterClearCS`, `FClearDepthDim` |
| `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteMaterials.cpp` | Nanite 材质 | Visibility Buffer → 材质着色 | — |
| `Engine/Source/Runtime/Engine/Private/Rendering/NaniteStreamingManager.cpp` | Nanite 流送 | Page 加载卸载与流送管理 | `FMemcpy_CS`, `FHierarchyDepthManager`, `FRingBufferAllocator` |
| `Engine/Source/Runtime/Engine/Public/Rendering/NaniteResources.h` | Nanite 资源 | Nanite 资源与 Page 结构 | `FNaniteVertexFactory`, `FStaticMeshSectionArray`, `FSkelMeshSectionArray` |
| `Engine/Source/Developer/NaniteBuilder/Private/NaniteBuilder.cpp` | Nanite 构建 | 离线构建（Cluster 生成） | `FTimeLogScope`, `FBuilderModule`, `FMeshData` |
| `Engine/Shaders/Private/Nanite/NaniteClusterCulling.usf` | Nanite 剔除 shader | Cluster 剔除 compute shader | `FNaniteTraversalClusterCullCallback`, `CULLING_PASS`, `VIRTUAL_TEXTURE_TARGET` |
| `Engine/Shaders/Private/Nanite/NaniteRasterizer.usf` | Nanite 光栅 shader | 软光栅写 Visibility Buffer | `FTriRange`, `FClusterRef`, `FCachedVertex` |
| `Engine/Shaders/Private/Nanite/NaniteShadeBinning.usf` | Nanite 着色分箱 | 材质 shade binning | `FCountPixelsTask`, `FScatterPixelsTask`, `FCountQuadsTask` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenSceneRendering.cpp` | Lumen 场景 | Lumen 场景数据与渲染调度 | `FResampleLightingHistoryToCardCaptureAtlasCS`, `FIndirectLighting`, `FWaveOpWaveSize` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenReflections.cpp` | Lumen 反射 | Lumen 反射 | `FInitReflectionIndirectArgsCS`, `FReflectionTileClassificationBuildListsCS`, `FWaveOps` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenScreenProbeGather.cpp` | Lumen Screen Probe | Screen Probe 生成与聚集 | `FScreenProbeDownsampleDepthUniformCS`, `FScreenProbeAdaptivePlacementMarkCS`, `FNumSamplesPerUniformProbe` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenMeshCards.cpp` | Lumen Mesh Card | Mesh Card 生成与管理 | `FLumenCardGPUData`, `FLumenMergedMeshCards`, `FLumenMeshCardsGPUData` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenHardwareRayTracingCommon.cpp` | Lumen 硬件光追 | 硬件光追公共层 | `Lumen`, `SetLumenHardwareRayTracingSharedParameters` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenTracingUtils.cpp` | Lumen 追踪工具 | 追踪相关工具 | `GetLumenCardTracingParameters` |
| `Engine/Source/Runtime/Renderer/Private/MegaLights/MegaLights.cpp` | MegaLights | 5.8 多光源渲染子系统 | `FMegaLightsTileClassificationBuildListsCS`, `FDownsampleFactorX`, `FDownsampleFactorY` |
| `Engine/Source/Runtime/Renderer/Private/VirtualShadowMaps/VirtualShadowMapCacheManager.cpp` | 虚拟阴影图 | VSM 页缓存与失效管理 | `FVirtualSmCopyStatsCS`, `FInvalidateInstancePagesLoadBalancerCS`, `FUseHzbDim` |
| `Engine/Source/Runtime/Renderer/Private/VirtualShadowMaps/VirtualShadowMapProjection.cpp` | 虚拟阴影图裁剪 | VSM 投影与采样 | `FVirtualShadowMapProjectionCS`, `FDirectionalLightDim`, `FOnePassProjectionDim` |
| `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp` | GPU 帧捕获 | r.DumpGPU.* 与资源导出 | `FDumpTextureCS`, `FTextureTypeDim`, `FRDGResourceDumpContext` |
| `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp` | GPU 剖析 | GPU Profiler 实现 | `FTimestampStream`, `TUnicodeHorizontalBar`, `FNode` |
| `Engine/Plugins/Developer/RenderDocPlugin/Source/RenderDocPlugin/Private/RenderDocPluginModule.cpp` | RenderDoc 插件 | renderdoc.* CVar 与捕获命令 | `FRenderDocFrameCapturer`, `FRenderDocDummyInputDevice`, `FRenderDocAsyncGraphTask` |
| `Engine/Shaders/Private/Substrate/Substrate.ush` | Substrate 核心 | Substrate 材质核心 | `FSubstrateBSDF`, `FHaziness`, `FSubstrateIrradianceAndOcclusion` |
| `Engine/Shaders/Private/Substrate/SubstrateEvaluation.ush` | Substrate 评估 | BSDF 评估 | `FSubstrateBSDFContext`, `FSubstrateToonData`, `FSubstrateEvaluateResult` |
| `Engine/Shaders/Private/Substrate/SubstrateDeferredLighting.ush` | Substrate 延迟光照 | Substrate 延迟路径 | `FSubstrateShadowTermInputParameters`, `SUBSTRATE_ENABLED`, `SUBSTRATE_LOAD_FROM_MATERIALCONTAINER` |

---

## 4. 常见 CVar 速查表

全部取自 UE 5.8 源码，作用说明是引擎自己的帮助文本。按类别列常用项，完整家族用 `python scripts/ue-cvar-dump.py <前缀> --md` 现查。

### 4.1 渲染分辨率与上采样

| CVar | 作用 |
|---|---|
| `r.ScreenPercentage` | To render in lower resolution and upscale for better performance (combined up with the blenable post process setting). 70 is a good value for low alia… |
| `r.ScreenPercentage.Default` | — |
| `r.DynamicRes.OperationMode` | Select the operation mode for dynamic resolution. |
| `r.TSR.History.ScreenPercentage` | Resolution multiplier of the history of TSR based of output resolution. While increasing the resolution adds runtime cost to TSR, it allows to maintai… |
| `r.TemporalAA.HistoryScreenPercentage` | Size of temporal AA's history. |
| `r.AntiAliasingMethod` | Engine default (project setting) for AntiAliasingMethod is (postprocess volume/camera/game setting still can override) 0: off (no anti-aliasing) 1: Fa… |
| `r.SecondaryScreenPercentage.GameViewport` | Override secondary screen percentage for game viewport. |

### 4.2 阴影

| CVar | 作用 |
|---|---|
| `r.Shadow.Virtual.Cache` | Turn on to enable caching |
| `r.Shadow.Virtual.Cache.AllocateViaLRU` | Prioritizes keeping more recently requested cached physical pages when allocating for new requests. |
| `r.Shadow.Virtual.Cache.CPUCullInvalidationsOutsideLightRadius` | CPU culls invalidations that are outside a local light's radius. |
| `r.Shadow.Virtual.Cache.DebugSkipDynamicPageInvalidation` | Skip invalidation of cached pages when geometry moves for debugging purposes. This will create obvious visual artifacts when disabled. |
| `r.Shadow.Virtual.Cache.DebugSkipRevealedPrimitivesInvalidation` | Debug skip invalidation of revealed Non-Nanite primitives, i.e. they go from being culled on the CPU to unculled. |
| `r.Shadow.Virtual.Cache.DeformableMeshesInvalidate` | If enabled, Primitive Proxies that are marked as having deformable meshes (HasDeformableMesh() == true) cause invalidations regardless of whether thei… |
| `r.Shadow.Virtual.Cache.ForceInvalidateDirectional` | Forces the clipmap to always invalidate, useful to emulate a moving sun to avoid misrepresenting cache performance. |
| `r.Shadow.Virtual.Cache.ForceInvalidateLocal` | Controls local light VSM invalidation behavior: 0: No forced invalidation (default) 1: Force invalidate all non-distant lights 2: Force invalidate all… |
| `r.Shadow.Virtual.Cache.FramesStaticThreshold` | Number of frames without an invalidation before an object will transition to static caching. |
| `r.Shadow.Virtual.Cache.InvalidateUseHZB` | When enabled, instances invalidations are tested against the HZB. Instances that are fully occluded will not cause page invalidations. |
| `r.Shadow.Virtual.Cache.MaxLightAgeSinceLastRequest` | The maximum number of frames to allow lights (and their associated pages) that aren't present in the current frame to live in the cache. Larger values… |
| `r.Shadow.Virtual.Cache.MaxPageAgeSinceLastRequest` | The maximum number of frames to allow cached pages that aren't requested in the current frame to live. 0=disabled. |

### 4.3 Lumen 总开关与降级

| CVar | 作用 |
|---|---|
| `r.Lumen.DiffuseIndirect.Allow` | Whether to allow Lumen Global Illumination. Lumen GI is enabled in the project settings, this cvar can only disable it. |
| `r.Lumen.DiffuseIndirect.AsyncCompute` | Whether to run Lumen diffuse indirect passes on the compute pipe if possible. |
| `r.Lumen.Reflections.Allow` | Whether to allow Lumen Reflections. Lumen Reflections is enabled in the project settings, this cvar can only disable it. |
| `r.Lumen.HardwareRayTracing` | Uses Hardware Ray Tracing for Lumen features, when available. Lumen will fall back to Software Ray Tracing otherwise. Note: Hardware ray tracing has s… |
| `r.Lumen.ScreenProbeGather.DownsampleFactor` | Pixel size of the screen tile that a screen probe will be placed on. |
| `r.Lumen.AsyncCompute` | Whether Lumen should use async compute if supported. |

### 4.4 Nanite

| CVar | 作用 |
|---|---|
| `r.Nanite` | Render static meshes using Nanite. |
| `r.Nanite.MaxPixelsPerEdge` | The triangle edge length that the Nanite runtime targets, measured in pixels. |
| `r.Nanite.FilterPrimitives` | Whether per-view filtering of primitive is enabled. |
| `r.Nanite.Culling.DrawDistance` | Set to 0 to test disabling Nanite culling due to instance draw distance. |
| `r.Nanite.Culling.Frustum` | Set to 0 to test disabling Nanite culling due to being outside of the view frustum. |
| `r.Nanite.Culling.HZB` | Set to 0 to test disabling Nanite culling due to occlusion by the hierarchical depth buffer. |
| `r.Nanite.Streaming.Async` | Perform most of the Nanite streaming on an asynchronous worker thread instead of the rendering thread. |
| `r.Nanite.Streaming.BandwidthLimit` | Streaming bandwidth limit in megabytes per second. Negatives values are interpreted as unlimited. |

### 4.5 MegaLights（5.8）

| CVar | 作用 |
|---|---|
| `r.MegaLights.Allowed` | Whether the MegaLights feature is allowed by scalability and device profiles. |
| `r.MegaLights.AsyncCompute.GenerateSamples` | Whether to run light sample generation passes on async compute. |
| `r.MegaLights.AsyncCompute.Volume` | Whether to run volume and TLV passes on async compute. |
| `r.MegaLights.Debug` | Whether to enabled debug mode, which prints various extra debug information from shaders. 0 - Disable 1 - Opaque 2 - Volume 3 - Translucency Volume 4 … |
| `r.MegaLights.Debug.CursorX` | Override default debug visualization cursor position. |
| `r.MegaLights.Debug.CursorY` | Override default debug visualization cursor position. |
| `r.MegaLights.Debug.LightId` | Which light to show debug info for. When set to -1, uses the currently selected light in editor. |
| `r.MegaLights.Debug.TraceStats` | Whether to print ray tracing stats on screen. |
| `r.MegaLights.Debug.VisualizeLight` | Whether to visualize selected light. Useful to find in in the level. |
| `r.MegaLights.Debug.VisualizeTraces` | How to draw traces for the selected pixel. 0 - Disabled 1 - Draw traced rays 2 - Draw samples |
| `r.MegaLights.Debug.VolumeSliceIndex` | Which volume slice to debug. |
| `r.MegaLights.DefaultShadowMethod` | The default shadowing method for MegaLights, unless over-ridden on the light component. 0 - Ray Tracing. Preferred method, which guarantees fixed Mega… |
| `r.MegaLights.Denoiser` | Whether to use denoiser. Useful in case of using joint denoising and upsampling at the end of the frame. |
| `r.MegaLights.Directional.LightSampleFraction` | Max fraction of samples which should be used to sample directional lights. Higher values make directional lights higher quality, but reduce quality of… |

### 4.6 异步计算

| CVar | 作用 |
|---|---|
| `r.RDG.AsyncCompute` | Controls the async compute policy. 0:disabled, no async compute is used; |
| `r.RDG.ParallelExecute` | Whether to enable parallel execution of passes when supported. 0: off 1: parallel with all tasks awaited 2: parallel with async tasks (default) |
| `r.RDG.ParallelSetup` | RDG will launch setup tasks from AddSetupTask. 0: setup tasks are executed inline; |
| `r.RDG.ParallelCompile` | RDG will launch tasks to compile the RDG graph. 0: compile tasks are executed inline; |
| `r.Nanite.Streaming.AsyncCompute` | Schedule GPU work in async compute queue. |

### 4.7 调试与诊断

| CVar | 作用 |
|---|---|
| `r.RDG.Validation` | Enables validation of correctness in API calls and pass parameter dependencies. 0: disabled; |
| `r.RDG.ImmediateMode` | Executes passes as they get created. Useful to have a callstack of the wiring code when crashing in the pass' lambda. |
| `r.RDG.ClobberResources` | Clears all render targets and texture / buffer UAVs with the requested clear color at allocation time. Useful for debugging. |
| `r.GPUCrashDebugging` | Enable vendor specific GPU crash analysis tools |
| `r.GPUCrashDebugging.Breadcrumbs` | Enable RHI breadcrumbs, a vendor-agnostic method for determining which passes were active when a GPU crash occurs |
| `r.ShaderDevelopmentMode` | 0: Default, 1: Enable various shader development utilities, such as the ability to retry on failed shader compile, and extra logging as shaders are co… |
| `r.Shaders.Symbols` | Enables debugging of shaders in platform specific graphics debuggers. This will generate and write shader symbols. This enables the behavior of both r… |
| `r.Test.FreezeTemporalHistories` | Freezes all temporal histories as well as the temporal sequence. |
| `r.ShowMaterialDrawEvents` | Whether to emit a draw event around every mesh draw call with information about the assets used. Introduces severe CPU and GPU overhead when enabled, … |

---

## 5. 学习路径图

### 第 1 周：建立渲染管线全局认知

**目标**：能画出 UE 渲染管线全貌图，理解三线程架构和核心 Pass 顺序

**要读的源码**：
- `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp` — `FSceneRenderer::Draw` 入口函数
- `Engine/Source/Runtime/Renderer/Private/DeferredShadingRenderer.cpp` — `Render` 主流程
- `Engine/Source/Runtime/RenderCore/Private/RenderingThread.cpp` — 三级流水线启动
- `Engine/Source/Runtime/RHI/Public/RHICommandList.h` — `FRHICommandList` 定义

**要实操的内容**：
1. 在 SceneRendering.cpp 的 `FSceneRenderer::Draw` 开头和结尾加断点，单步跟踪一帧渲染
2. 运行 `ProfileGPU` 输出，对照源码找到每个 Pass 的对应文件
3. 运行 `r.VisualizeGPU 1` 观察 Pass 时间分布
4. 用 RenderDoc 抓一帧，观察 Event Browser 中的 Pass 命名

**里程碑**：能用 `ProfileGPU` 输出解释"哪几个 Pass 最贵，它们分别在哪个文件里实现"

---

### 第 2 周：掌握 RDG 编程模型与 RHI 资源管理

**目标**：能写一个简单的 RDG Pass（自定义后处理），理解 RHI 资源生命周期和 Barrier

**要读的源码**：
- `Engine/Source/Runtime/RenderCore/Public/RenderGraphBuilder.h` — `FRDGBuilder` 核心 API
- `Engine/Source/Runtime/RenderCore/Public/RenderGraphResources.h` — `FRDGTexture` / `FRDGBuffer`
- `Engine/Source/Runtime/RenderCore/Public/RenderGraphPass.h` — `ERDGPassFlags` / Pass 类型
- `Engine/Source/Runtime/RHI/Public/RHIAccess.h` — `ERHIAccess`；transition 结构在 `RHIResources.h` 的 `FRHITransitionInfo`
- `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` — 后处理链的 RDG 编排参考

**要实操的内容**：
1. 写一个简单的全屏后处理 Pass（如灰度/反色/自定义色调映射），挂接到后处理链（走后处理材质或 `ISceneViewExtension::SubscribeToPostProcessingPass`，见 card-12）
2. 使用 `FRDGTexture` 创建临时 RT，在 Pass 之间传递
3. 使用 `FGlobalShader` + `SHADER_PARAMETER_STRUCT` 声明 Shader 参数
4. 用 `r.DumpShaderDebugInfo` 验证生成的 HLSL 正确性
5. 用 `r.RDG.Validate 1` 验证 RDG 资源生命周期正确

**里程碑**：能独立完成一个自定义后处理效果（从 HLSL 编写到 C++ Pass 注册到引擎渲染管线）

---

### 第 1 个月：深入 Lumen / Nanite 与性能调优

**目标**：能诊断 Lumen 性能问题并给出降级方案，能使用完整性能分析工具链定位瓶颈

**要读的源码**：
- `Engine/Source/Runtime/Renderer/Private/Lumen/LumenSceneRendering.cpp` — `ShouldRenderLumen()`、`RenderLumenScene()`
- `Engine/Source/Runtime/Renderer/Private/Lumen/LumenReflections.cpp` — `CompositeLumenReflections()`
- `Runtime/Renderer/Private/Nanite/NaniteCullRaster.cpp` — `RenderNanite()`
<!-- verify:ignore-start -->
- `Engine/Source/Runtime/Engine/Private/Rendering/NaniteStreamingManager.cpp` — Nanite Page 流送管理（类名在 `Nanite` 命名空间下，不是全局的 `FNaniteStreamingManager`）
<!-- verify:ignore-end -->
- `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp` — GPU Profiler 内部机制

**要实操的内容**：
1. 搭建一个渲染压力大的场景（大量光源 + 复杂几何 + Lumen 开启），用 ProfileGPU 定位瓶颈
2. 逐项应用 Lumen 降级策略，记录每项对帧时间的影响
3. 用 `r.Nanite.ShowStats 1` 观察 Nanite 各阶段耗时，调整 `r.Nanite.MaxPixelsPerEdge`
4. 用 Unreal Insights 捕获 3 秒数据，分析 Timing Wheel 中的 GPU Stall
5. 用 RenderDoc 抓帧，定位最贵的 Draw Call，反查其 Shader 和 PSO
6. 用 Nsight/RGP 对同一帧做硬件级分析，验证 ProfileGPU 结论

**里程碑**：能对一个性能不达标的场景做完整诊断（瓶颈端 → 瓶颈 Pass → 瓶颈原因 → 优化方案），并能给出量化的优化前后对比

---

### 第 2 个月：平台适配与高级主题

**目标**：能处理跨平台渲染一致性、移动端优化、Shader 编译优化、GPU Crash 诊断

**要读的源码**：
- `Engine/Source/Runtime/RHI/Public/RHI.h` — `ERHIFeatureLevel` / `IsFeatureLevelSupported()`
- `Engine/Source/Runtime/Renderer/Private/MobileShadingRenderer.cpp` — Mobile 渲染路径
- `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` — `ShouldCompilePermutation()`
- `Engine/Source/Runtime/RenderCore/Public/ShaderPermutation.h` — `FShaderPermutationBool` 裁剪机制
- `Runtime/RHI/Private/RHIBreadcrumbs.cpp` — GPU Crash 检测
- `Runtime/D3D12RHI/Private/D3D12RayTracingDebug.cpp` — D3D12 Debug Layer
- `Runtime/RHI/Private/RHIValidation.cpp` — Vulkan Validation

**要实操的内容**：
1. 搭建多平台测试场景（PC D3D12 + Vulkan + Mobile），对比渲染效果差异
2. 用 `r.MobileHDR 0` + `r.ForwardShading 1` 模拟移动端渲染，优化至 30fps
3. 用 `stat ShaderCompiling` 观察 Shader 编译队列，定位 Permutation 爆炸源
4. 用 `bUsedWith*` 开关裁剪不必要的 Shader 变体，对比编译时间变化
5. 模拟 GPU Crash（用非法 Shader 参数），用 `r.GPUCrashDebugging` 取证
6. 用 `r.D3D12.EnableD3DDebug 1` 开 D3D12 debug layer 捕获资源泄漏，用 `stat RHI` 验证

**里程碑**：能独立处理跨平台渲染适配咨询，能给出 Shader 编译优化方案，能诊断 GPU Crash 根因

---

### 第 3 个月：综合实战与知识体系完善

**目标**：能应对客户技术咨询中的 90% 场景，能独立完成复杂渲染定制

**要读的源码**：
- `Engine/Source/Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp` — 材质表达式 → HLSL 完整流程
- `Engine/Source/Runtime/Engine/Public/MaterialShared.h` — `FMaterialShaderMap` 序列化
- `Runtime/Renderer/Private/Nanite/NaniteMaterials.cpp` — Visibility Buffer → G-Buffer
- `Runtime/Renderer/Private/Lumen/LumenTracingUtils.cpp` — 统一追踪接口
- `Engine/Source/Runtime/Renderer/Private/MeshPassProcessor.cpp` — `FMeshPassProcessor` 注册机制
- Shaders/Private/Substrate/ — Substrate 完整 Shader 链

**要实操的内容**：
1. 实现一个完整的自定义渲染功能（如自定义 GI 替代 Lumen、自定义 Shading Model）
2. 对真实项目做一次完整的性能审计（从 ProfileGPU 到硬件级分析），输出优化报告
3. 实现一个跨平台渲染方案，确保 D3D12/Vulkan/Console 效果一致
4. 写一篇关于所实现功能的内部技术文档（仿照本文档的知识卡片格式）
5. 模拟一次"客户咨询"场景，从问题描述到解决方案的完整响应

**里程碑**：能独立完成 UE 渲染技术咨询的全部环节（问题定位、方案设计、落地实施、效果验证）

---

### 持续学习资源

| 资源 | 类型 | 用途 |
|------|------|------|
| UE 源码 (Runtime/Renderer/, Runtime/RHI/, Runtime/RenderCore/) | 源码 | 权威参考，常量更新 |
| UE 官方文档 (docs.unrealengine.com) | 文档 | 基础概念，但可能滞后于源码 |
| RenderDoc 官方文档 | 工具文档 | GPU 调试 |
| Unreal Insights 文档 | 工具文档 | 性能分析 |
| GPU 厂商文档 (NVIDIA/AMD/Intel) | 技术文档 | 硬件级优化 |
| SIGGRAPH/ GDC UE 演讲 | 视频 + 幻灯片 | 深入了解设计决策 |
| UE 社区论坛 (dev.epicgames.com) | 社区 | 踩坑经验分享 |
| 《Real-Time Rendering》4th Edition | 书籍 | 渲染理论基础 |

---

**注**：本知识地图中的 [🔴] = 客户项目中常见程度高，[🟡] = 中等，[🟢] = 较低。所有源码路径基于 UE 5.8，版本差异可能导致路径变化，建议以实际引擎源码为准。