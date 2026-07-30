# UE 渲染知识地图

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
| GPU Visualizer | 1.1 | `Engine/Source/Runtime/Renderer/Private/VisualizeGPU.cpp` | P0 | 无 |
| RenderDoc 集成 | 1.1 | `Engine/Plugins/Editor/RenderDocPlugin/` | P0 | 无 |
| 分辨率缩放策略 | 1.3 | `Engine/Source/Runtime/Engine/Private/SceneView.cpp` | P0 | TSR 原理 |
| Lumen 降级策略 | 1.4 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenSceneRendering.cpp` | P0 | Lumen 架构 |
| Shadow 优化 | 1.6 | `Engine/Source/Runtime/Renderer/Private/ShadowRendering.cpp` | P0 | 阴影原理 |
| PostProcessing 裁剪 | 1.7 | `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` | P0 | 后处理管线 |
| 移动端性能优化 | 1.9 | `Engine/Source/Runtime/Renderer/Private/MobileShadingRenderer.cpp` | P0 | Mobile 渲染路径 |
| Nanite 裁剪 | 1.5 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteRendering.cpp` | P1 | Nanite 架构 |
| 异步计算优化 | 1.8 | `Engine/Source/Runtime/RenderCore/Private/RenderGraph.cpp` | P1 | 渲染线程模型 |
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
| Substrate 材质 | 2.4 | `Engine/Shaders/Private/Substrate/SubstrateBSDF.ush` | P1 | PBR 理论 |
| GBuffer 扩展 | 2.4 | `Engine/Source/Runtime/RenderCore/Public/GBufferInfo.h` | P1 | GBuffer 布局 |
| Nanite 适配 | 2.5 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteMaterialResolve.cpp` | P1 | Nanite 架构 |

### 2.3 平台适配领域

| 知识卡片 | 关联领域 | 关键源码文件 | 学习优先级 | 前置知识 |
|----------|----------|-------------|-----------|---------|
| Feature Level 系统 | 3.1 | `Engine/Source/Runtime/RHI/Public/RHI.h` | P0 | 无 |
| Desktop D3D12 路径 | 3.2 | `Engine/Source/Runtime/D3D12RHI/Private/D3D12RHI.cpp` | P0 | D3D12 基础 |
| Desktop Vulkan 路径 | 3.2 | `Engine/Source/Runtime/VulkanRHI/Private/VulkanRHI.cpp` | P1 | Vulkan 基础 |
| Mobile 渲染路径 | 3.3 | `Engine/Source/Runtime/Renderer/Private/MobileShadingRenderer.cpp` | P0 | 移动 GPU 架构 |
| Vulkan Mobile | 3.3 | `Engine/Source/Runtime/VulkanRHI/Private/VulkanRHIMobile.cpp` | P0 | Vulkan 基础 |
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
| GBuffer 可视化 | 4.2 | `Engine/Source/Runtime/Renderer/Private/VisualizeBuffer.cpp` | P0 | GBuffer 布局 |
| ShaderComplexity | 4.2 | `Engine/Source/Runtime/Renderer/Private/ShaderComplexity.cpp` | P0 | 无 |
| Shader 开发模式 | 4.3 | `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` | P0 | Shader 编译 |
| GPU Crash 诊断 | 4.4 | `Engine/Source/Runtime/RenderCore/Private/GPUCrashDebugging.cpp` | P1 | GPU 调试经验 |
| 显存诊断 | 4.5 | `Engine/Source/Runtime/RHI/Private/RHIResourceStats.cpp` | P1 | GPU 内存管理 |
| D3D12 Debug Layer | 4.6 | `Engine/Source/Runtime/D3D12RHI/Private/D3D12Debug.cpp` | P1 | D3D12 基础 |
| Vulkan Validation | 4.6 | `Engine/Source/Runtime/VulkanRHI/Private/VulkanValidation.cpp` | P1 | Vulkan 基础 |
| RDG Validation | 4.6 | `Engine/Source/Runtime/RenderCore/Private/RenderGraphValidation.cpp` | P1 | RDG 架构 |

### 2.5 工具链领域

| 知识卡片 | 关联领域 | 关键源码文件 | 学习优先级 | 前置知识 |
|----------|----------|-------------|-----------|---------|
| 三级渲染流水线 | 5.1 | `Engine/Source/Runtime/RenderCore/Private/RenderingThread.cpp` | P0 | 多线程基础 |
| FSceneRenderer::Draw | 5.1 | `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp` | P0 | 渲染管线基础 |
| RHI 命令体系 | 5.2 | `Engine/Source/Runtime/RHI/Public/RHICommandList.h` | P0 | 无 |
| RHI 资源类型 | 5.2 | `Engine/Source/Runtime/RHI/Public/RHIBuffer.h` | P0 | 无 |
| GPU 同步 (Fence/Barrier) | 5.2 | `Engine/Source/Runtime/RHI/Public/RHIAccess.h` | P0 | GPU 管线基础 |
| RDG 核心 | 5.3 | `Engine/Source/Runtime/RenderCore/Public/RenderGraphBuilder.h` | P0 | 渲染管线基础 |
| RDG 资源管理 | 5.3 | `Engine/Source/Runtime/RenderCore/Public/RenderGraphResources.h` | P0 | 无 |
| 材质系统链条 | 5.4 | `Engine/Source/Runtime/Engine/Public/MaterialShared.h` | P0 | 材质编辑器使用 |
| HLSL 生成 | 5.4 | `Engine/Source/Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp` | P0 | HLSL |
| Shader 编译管线 | 5.4 | `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` | P0 | 编译原理 |
| Shader Permutation | 5.4 | `Engine/Source/Runtime/RenderCore/Public/ShaderPermutation.h` | P0 | 无 |
| Lumen 三种追踪模式 | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenSceneRendering.cpp` | P0 | 全局光照基础 |
| Lumen Screen Probe | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenScreenProbe.cpp` | P1 | 无 |
| Lumen Mesh Card | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenMeshCards.cpp` | P1 | 无 |
| Lumen Hardware RT | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenHardwareRayTracing.cpp` | P1 | DXR 基础 |
| Lumen Reflections | 5.5 | `Engine/Source/Runtime/Renderer/Private/Lumen/LumenReflections.cpp` | P0 | 反射原理 |
| Nanite 核心架构 | 5.6 | `Engine/Shaders/Shared/NaniteDefinitions.h` | P1 | 几何处理基础 |
| Nanite Visibility Buffer | 5.6 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteRendering.cpp` | P1 | 延迟渲染 |
| Nanite 流式加载 | 5.6 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteStreaming.cpp` | P1 | 内存管理 |
| Nanite 性能调优 | 5.6 | `Engine/Source/Runtime/Renderer/Private/Nanite/NaniteCull.cpp` | P1 | GPU 架构 |

---

## 3. 关键源码文件速查表

| 文件名 (相对路径 Engine/Source/...) | 所属子系统 | 一句话功能 | 关键类/函数 |
|--------------------------------------|-----------|-----------|-------------|
| `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp` | 渲染管线调度 | 渲染入口，FSceneRenderer::Draw 调度所有 Pass | `FSceneRenderer::Draw`, `PreRender`, `PostRender`, `InitViews` |
| `Engine/Source/Runtime/Renderer/Private/DeferredShadingRenderer.cpp` | 延迟渲染 | 延迟着色主流程，RenderBasePass → RenderLights → PostProcessing | `FDeferredShadingSceneRenderer::Render` |
| `Engine/Source/Runtime/Renderer/Private/MobileShadingRenderer.cpp` | 移动端渲染 | 移动端渲染主流程 | `FMobileSceneRenderer::Render` |
| `Engine/Source/Runtime/Renderer/Private/SceneVisibility.cpp` | 可见性计算 | InitViews 核心实现，可见性裁剪/阴影分配/Lumen 场景更新 | `InitViews`, `FRelevancePacket`, `ComputeAndMarkRelevanceForViewParallel` |
| `Engine/Source/Runtime/Renderer/Private/BasePassRendering.cpp` | GBuffer 写入 | BasePass 实现，渲染不透明 Mesh 到 GBuffer | `RenderBasePass`, `FBasePassMeshProcessor` |
| `Engine/Source/Runtime/Renderer/Private/LightRendering.cpp` | 光照计算 | Lighting Pass 实现，逐像素光照计算 | `RenderLights`, `FDeferredLightSceneInfo` |
| `Engine/Source/Runtime/Renderer/Private/ShadowRendering.cpp` | 阴影渲染 | Shadow Map 渲染 | `RenderShadowDepthMaps`, `FProjectedShadowInfo` |
| `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` | 后处理 | 后处理管线，Bloom/Tonemapping/TSR/DOF/MotionBlur | `FPostProcessing::Process`, `AddPostProcessingPasses` |
| `Runtime/Renderer/Private/TranslucencyRendering.cpp` | 半透明渲染 | 半透明物体渲染 | `FRenderTranslucency`, `FTranslucencyDrawingPolicyFactory` |
| `Runtime/Renderer/Private/DecalRendering.cpp` | Decal 渲染 | Decal 写入 GBuffer | `RenderDeferredDecals` |
| `Engine/Source/Runtime/RenderCore/Public/RenderGraphBuilder.h` | RDG 核心 | RDG 核心 API，Pass 注册/资源创建/执行 | `FRDGBuilder`, `AddPass`, `CreateTexture`, `Execute` |
| `Engine/Source/Runtime/RenderCore/Public/RenderGraphResources.h` | RDG 资源 | RDG 资源抽象，Texture/Buffer 描述符 | `FRDGTexture`, `FRDGBuffer`, `FRDGResource` |
| `Engine/Source/Runtime/RenderCore/Public/RenderGraphPass.h` | RDG Pass | Pass 类型体系 | `FRDGPipelineStatePass`, `ERDGPassFlags` |
| `Runtime/RenderCore/Private/RenderGraph.cpp` | RDG 执行 | RDG Compile/Execute 实现 | `FRDGBuilder::Execute`, Compile, Culling |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphAllocator.cpp` | RDG 内存管理 | Transient 资源分配与别名优化 | `FRDGTransientResourceAllocator` |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphValidation.cpp` | RDG 调试 | RDG 调试验证 | RDG Validation |
| `Engine/Source/Runtime/RHI/Public/RHICommandList.h` | RHI 命令 | RHI 命令列表核心定义 | `FRHICommandList`, `FRHICommandListImmediate` |
| `Engine/Source/Runtime/RHI/Public/DynamicRHI.h` | RHI 抽象接口 | 平台无关 RHI 抽象基类 | `FDynamicRHI` (数百个纯虚函数) |
| `Engine/Source/Runtime/RHI/Public/RHIAccess.h` | RHI 屏障 | Barrier/Transition API | `ERHIAccess`, `FRHITransitionInfo`, `FRHIBarrier` |
| `Runtime/RHI/Public/RHIBuffer.h` | RHI Buffer | Buffer 资源类型定义 | `FRHIBuffer`, `FRHIVertexBuffer`, `FRHIIndexBuffer` |
| `Runtime/RHI/Public/RHITexture.h` | RHI Texture | Texture 资源类型定义 | `FRHITexture`, `FRHITexture2D`, `FRHITextureCube` |
| `Runtime/RHI/Public/RHIView.h` | RHI View | SRV/UAV 定义 | `FRHIShaderResourceView`, `FRHIUnorderedAccessView` |
| `Runtime/RHI/Public/GPUFence.h` | GPU 同步 | GPU Fence 定义 | `FGPUFence` |
| `Engine/Source/Runtime/RenderCore/Private/RenderingThread.cpp` | 渲染线程 | 渲染线程启动与控制 | `StartRenderingThread`, `FRenderCommandFence` |
| `Engine/Source/Runtime/D3D12RHI/Private/D3D12RHI.cpp` | D3D12 RHI | D3D12 平台 RHI 实现 | `FD3D12DynamicRHI::Init` |
| `Engine/Source/Runtime/D3D12RHI/Private/D3D12CommandContext.cpp` | D3D12 命令 | D3D12 命令上下文与 Barrier | `FD3D12CommandContext::RHITransitionResources` |
| `Runtime/D3D12RHI/Private/D3D12Resource.cpp` | D3D12 资源 | D3D12 资源管理 | `FD3D12Resource`, DeferredDelete |
| `Engine/Source/Runtime/VulkanRHI/Private/VulkanRHI.cpp` | Vulkan RHI | Vulkan 平台 RHI 实现 | `FVulkanDynamicRHI::Init` |
| `Runtime/VulkanRHI/Private/VulkanCommandList.cpp` | Vulkan 命令 | Vulkan 命令列表 | `FVulkanCommandListContext` |
| `Engine/Source/Runtime/VulkanRHI/Private/VulkanPipelineState.cpp` | Vulkan PSO | Vulkan PSO 缓存 | `FVulkanPipelineStateCache` |
| `Engine/Source/Runtime/Engine/Public/MaterialShared.h` | 材质系统 | FMaterial/FMaterialResource/FMaterialShaderMap | `FMaterial`, `FMaterialResource`, `FMaterialShaderMap` |
| `Runtime/Engine/Public/Material.h` | 材质资产 | UMaterial UObject 定义 | `UMaterial`, `UMaterialInstance` |
| `Engine/Source/Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp` | HLSL 生成 | 材质表达式 → HLSL 代码生成 | `FMaterialCompiler` |
| `Engine/Source/Runtime/Engine/Public/ShaderCompiler.h` | Shader 编译 | Shader 编译任务与队列 | `FShaderCompileJob`, `FShaderCompilingThreadManager` |
| `Engine/Source/Runtime/Engine/Private/ShaderCompiler/ShaderCompiler.cpp` | Shader 编译调度 | 主进程编译调度 | `FShaderCompilingThreadManager` |
| `Runtime/Programs/ShaderCompileWorker/ShaderCompileWorker.cpp` | SCW 进程 | Shader 编译外部进程入口 | `main` |
| `Engine/Source/Runtime/RenderCore/Public/ShaderPermutation.h` | Permutation 系统 | Shader Permutation 定义与裁剪 | `FShaderPermutationBool`, `TShaderPermutationDomain` |
| `Engine/Source/Runtime/RenderCore/Public/GlobalShader.h` | Global Shader | FGlobalShader 基类与注册宏 | `FGlobalShader`, `IMPLEMENT_GLOBAL_SHADER` |
| `Engine/Source/Runtime/RenderCore/Public/ShaderCore.h` | Shader 核心 | Shader 参数反射系统 | `SHADER_PARAMETER_STRUCT`, `FShader` 基类 |
| `Engine/Source/Runtime/RenderCore/Public/ShaderParameters.h` | Shader 参数 | SHADER_PARAMETER_STRUCT 宏定义 | `BEGIN_SHADER_PARAMETER_STRUCT` |
| `Engine/Source/Runtime/RHI/Public/RHI.h` | RHI 枚举 | ERHIFeatureLevel/ERHIShaderPlatform 等枚举 | `ERHIFeatureLevel`, `IsFeatureLevelSupported()` |
| `Engine/Source/Runtime/Engine/Public/SceneView.h` | 场景视图 | FSceneView/FViewInfo 定义 | `FSceneView`, `FViewInfo`, `EStereoscopicPass` |
| `Engine/Source/Runtime/Engine/Private/SceneView.cpp` | 视图计算 | 视图矩阵/投影矩阵计算 | `FSceneView::SetupViewRect` |
| `Engine/Shaders/Shared/NaniteDefinitions.h` | Nanite 定义 | Nanite 数据结构定义 | `Cluster`, `Page`, `Group` 结构体 |
| `Runtime/Renderer/Private/Nanite/NaniteRendering.cpp` | Nanite 渲染 | Nanite 渲染主入口 | `RenderNanite()`, `FNaniteVS`, `FNanitePS` |
| `Runtime/Renderer/Private/Nanite/NaniteStreaming.cpp` | Nanite 流式加载 | Page 加载/卸载/LOD 选择 | `FNaniteStreamingManager::UpdateLODs`, `UpdateStreaming` |
| `Runtime/Renderer/Private/Nanite/NaniteCull.cpp` | Nanite 剔除 | GPU 剔除 Kernel | `CullKernel` |
| `Runtime/Renderer/Private/Nanite/NaniteMaterialResolve.cpp` | Nanite 材质解析 | Visibility Buffer → G-Buffer | Material Resolve |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenSceneRendering.cpp` | Lumen 场景 | Lumen 场景数据管理、体素化、主渲染调度 | `RenderLumenScene()`, `VoxelizeLumenScene()`, `ShouldRenderLumen()` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenReflections.cpp` | Lumen 反射 | Lumen 反射合成与降噪 | `CompositeLumenReflections()`, `RenderLumenReflections()` |
| `Runtime/Renderer/Private/Lumen/LumenScreenProbe.cpp` | Lumen Screen Probe | Screen Probe 生成/采样/插值 | `LumenScreenProbeGather()`, `ScreenProbePlacement()` |
| `Engine/Source/Runtime/Renderer/Private/Lumen/LumenMeshCards.cpp` | Lumen Mesh Card | Mesh Card 生成与管理 | `LumenSceneCardBuild()`, `CardRasterize()` |
| `Runtime/Renderer/Private/Lumen/LumenHardwareRayTracing.cpp` | Lumen Hardware RT | DXR 加速结构 + RayGen | `BuildLumenHardwareRayTracingScene()`, `LumenRayGen()` |
| `Runtime/Renderer/Private/Lumen/LumenTracing.cpp` | Lumen 追踪 | 统一追踪接口，抽象三种后端 | `TraceLumenRadiance()` |
| `Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp` | GPU 性能分析 | GPU Profiler 实现 | `FGPUProfiler` |
| `Runtime/RenderCore/Private/GPUCrashDebugging.cpp` | GPU Crash 诊断 | GPU Crash 调试 | `FGPUCrashDebugging` |
| `Engine/Source/Runtime/RenderCore/Private/DumpGPU.cpp` | GPU 帧捕获 | DumpGPU 实现 | `DumpGPU` |
| `Runtime/Renderer/Private/VisualizeBuffer.cpp` | 可视化 | GBuffer 可视化 | `FVisualizeBuffer` |
| `Runtime/Renderer/Private/ShaderComplexity.cpp` | Shader 复杂度 | Shader 复杂度可视化 | `FShaderComplexityAccumulator` |
| `Runtime/RHI/Private/RHIResourceStats.cpp` | RHI 资源统计 | RHI 资源统计 | `FRHIResourceStats` |
| `Engine/Source/Runtime/RenderCore/Private/RenderGraphValidation.cpp` | RDG 验证 | RDG 验证实现 | RDG Validation |
| `Engine/Source/Runtime/RenderCore/Private/Shader.cpp` | Shader 核心 | Shader 序列化/缓存/Permutation 调度 | `FShader`, `GET_SHADER_CONDITIONAL` |
| `Runtime/Engine/Private/MaterialShaderMap.cpp` | ShaderMap 编译 | ShaderMap 编译调度 | `FMaterialShaderMap::Compile` |
| `Engine/Shaders/Private/MaterialTemplate.ush` | 材质模板 | 材质 HLSL 模板 | `GetMaterialPixelParameters()`, `GetMaterialVertexParameters()` |
| `Shaders/Private/Substrate/SubstrateBSDF.ush` | Substrate BSDF | Substrate BSDF 计算 | BSDF 函数 |
| `Shaders/Private/Substrate/SubstrateDeferredShading.ush` | Substrate 延迟 | Substrate Deferred 路径 | Shading 函数 |
| `Shaders/Nanite/NaniteCull.usf` | Nanite 剔除 | GPU 剔除 Compute Shader | CullKernel |
| `Shaders/Nanite/NaniteMaterialResolve.ush` | Nanite 材质解析 | Material Resolve Shader 入口 | Material Resolve |
| `Shaders/Nanite/NaniteVS.usf` | Nanite VS | Nanite Vertex Shader | VS 实现 |
| `Shaders/Nanite/NanitePS.usf` | Nanite PS | Nanite Pixel Shader (Visibility Buffer 写入) | PS 实现 |
| `Shaders/RayTracing/Lumen/LumenHardwareRayTracing.usf` | Lumen RT | Lumen 光线追踪 Shader | RayGen |
| `Runtime/Programs/NaniteCook/NaniteCook.cpp` | Nanite Cook | 离线 Cook 工具 | Cluster 生成/压缩 |

---

## 4. 常见 CVar 速查表

### 4.1 渲染分辨率与质量

| CVar | 默认值 | 优化值 | 功能 | 场景 |
|------|--------|--------|------|------|
| `r.ScreenPercentage` | 100 | 50-80 | 渲染分辨率百分比 | 性能瓶颈时降低 |
| `r.TSR.OverrideScreenPercentage` | 100 | 100 | TSR 输出分辨率 | 配合 ScreenPercentage 使用 |
| `r.MaterialQualityLevel` | 1 | 0 | 材质质量 (0=低,1=中,2=高) | 低端设备 |
| `r.PostProcessAAQuality` | 6 | 3-4 | 抗锯齿质量 | 性能敏感时降低 |
| `r.DefaultFeature.AntiAliasing` | 2 (TAA) | 0/1/2 | AA 方法 (0=关,1=FXAA,2=TAA) | 移动端用 FXAA |
| `r.FeatureLevel` | 5 (SM6) | 4 (SM5) | Feature Level 降级 | 低端 PC |

### 4.2 阴影

| CVar | 默认值 | 优化值 | 功能 | 场景 |
|------|--------|--------|------|------|
| `r.Shadow.MaxResolution` | 2048 | 512-1024 | 阴影贴图最大分辨率 | 性能瓶颈 |
| `r.Shadow.CSM.MaxCascades` | 4 | 2-3 | CSM 级数 | 性能瓶颈 |
| `r.Shadow.RadiusThreshold` | 0.01 | 0.03-0.05 | 阴影剔除半径 | 远处阴影无关紧要 |
| `r.Shadow.DistanceScale` | 1.0 | 0.3-0.7 | 阴影距离缩放 | 缩小阴影距离 |
| `r.ContactShadows` | 1 | 0 | 接触阴影 | 移动端必关 |
| `r.Shadow.Virtual.Enable` | 1 | 0 | Virtual Shadow Map | 退回到传统阴影 |

### 4.3 Lumen

| CVar | 默认值 | 优化值 | 功能 | 场景 |
|------|--------|--------|------|------|
| `r.Lumen.DiffuseIndirect.Allow` | 1 | 0 | 关闭 Lumen GI | 性能瓶颈 |
| `r.Lumen.Reflections.Allow` | 1 | 0 | 关闭 Lumen 反射 | 性能瓶颈 |
| `r.Lumen.DiffuseIndirect.Method` | 1 | 0/1/2 | 追踪模式 (0=ScreenProbe,1=MeshCard,2=HardwareRT) | 无 RT 硬件时降级 |
| `r.Lumen.Reflections.Method` | 1 | 0/1 | 反射模式 (0=Probe,1=Trace) | 性能敏感用 0 |
| `r.Lumen.ScreenProbe.NumRays` | 64 | 32 | 每 Probe Ray 数 | 性能瓶颈 |
| `r.Lumen.Scene.RayIterations` | 4 | 2 | 追踪步进次数 | 性能瓶颈 |
| `r.LumenScene.SurfaceCacheResolution` | 512 | 256 | Surface Cache 分辨率 | 低端设备 |
| `r.Lumen.DiffuseIndirect.NumMeshCards` | 256 | 64-128 | Mesh Card 数量 | 性能瓶颈 |
| `r.Lumen.TemporalFilter` | 1 | 0/1 | 时间降噪开关 | 调试闪烁 |
| `r.Lumen.TemporalFilter.NumFrames` | 8 | 4-8 | 时间积累帧数 | 减少 Ghosting |
| `r.Lumen.AsyncCompute` | 1 | 1 | 异步计算 | 保持开启 |
| `r.Lumen.FarField` | 1 | 0 | 远场 GI | 室外大世界关闭 |

### 4.4 Nanite

| CVar | 默认值 | 优化值 | 功能 | 场景 |
|------|--------|--------|------|------|
| `r.Nanite.VisibilityBuffer` | 1 | 1 | 启用 Visibility Buffer | 保持开启 |
| `r.Nanite.MaterialResolve` | 1 | 1 | Material Resolve 策略 | 保持开启 |
| `r.Nanite.MaxPixelsPerEdge` | 4 | 8-16 | 裁剪阈值 | 性能瓶颈 |
| `r.Nanite.FilterOutSmallObjects` | 0 | 1 | 剔除小物体 | 性能瓶颈 |
| `r.Nanite.ViewDistance` | 1.0 | 0.3-0.7 | Nanite 渲染距离 | 性能瓶颈 |
| `r.Nanite.PagePoolSize` | 2048 | 1024-4096 | GPU Page Pool (MB) | 显存不足时调整 |
| `r.Nanite.Streaming.PageSize` | 128 | 128 | Page 目标大小 (KB) | 保持默认 |
| `r.Nanite.AllowMovingNanite` | 1 | 0/1 | 动态物体走 Nanite | 调试 |
| `r.Nanite.HiZB` | 1 | 1 | Hierarchical Z-Buffer | 保持开启 |
| `r.Nanite.ShowStats` | 0 | 1 | 显示 Nanite 性能统计 | 调试 |

### 4.5 PostProcessing

| CVar | 默认值 | 优化值 | 功能 | 场景 |
|------|--------|--------|------|------|
| `r.BloomQuality` | 5 | 0-3 | Bloom 质量 | 性能瓶颈 |
| `r.MotionBlurQuality` | 4 | 0 | 运动模糊 | 性能瓶颈 |
| `r.DepthOfFieldQuality` | 2 | 0 | 景深 | 性能瓶颈 |
| `r.LensFlareQuality` | 2 | 0 | 镜头光晕 | 性能瓶颈 |
| `r.Tonemapper.GrainQuantization` | 1 | 0 | 颗粒噪声 | 移动端关 |
| `r.SceneColorFringeQuality` | 1 | 0 | 色差 | 性能瓶颈 |
| `r.EyeAdaptation` | 1 | 0 | 人眼适应 | 性能瓶颈 |
| `r.Vignette` | 1 | 0 | 暗角 | 性能瓶颈 |
| `r.TemporalAASamples` | 8 | 4 | TAA 采样数 | 性能瓶颈 |
| `r.PostProcessing.Enable` | 1 | 0 | 全部后处理 | 调试 (禁用后输出 HDR LogLuv) |
| `r.PostProcessing.PropagateAlpha` | 0 | 1 | 后处理保留 Alpha | 特定渲染需求 |

### 4.6 移动端

| CVar | 默认值 | 优化值 | 功能 | 场景 |
|------|--------|--------|------|------|
| `r.MobileHDR` | 1 | 0 | 移动端 HDR | 性能瓶颈 |
| `r.Mobile.DisableVertexFog` | 0 | 1 | 关闭顶点雾 | 性能瓶颈 |
| `r.Mobile.SkyLightPermutation` | 0 | 0 | 天光计算简化 | 保持默认 |
| `r.Mobile.UsePreprocessedShaders` | 1 | 1 | 预编译 Shader | 保持开启 |
| `r.ForwardShading` | 0 | 1 | Forward Shading | 移动端 |
| `r.ForwardLighting.MaxDynamicPointLights` | 4 | 2 | 动态点光源上限 | 移动端 |
| `r.FrameRateLimit` | 0 | 30/60 | 帧率限制 | 移动端/VR |
| `r.ThermalThrottling.Enabled` | 1 | 1 | 热降频 | 保持开启 |
| `r.ThermalThrottling.TargetFPS` | 30 | 30 | 降频目标帧率 | 移动端 |

### 4.7 异步计算

| CVar | 默认值 | 优化值 | 功能 | 场景 |
|------|--------|--------|------|------|
| `r.AsyncCompute.Enabled` | 1 | 1 | 启用异步计算 | 保持开启 |
| `r.AsyncCompute.MaxConcurrency` | 2 | 2 | 最大并发队列 | Console 可调大 |
| `r.Lumen.AsyncCompute` | 1 | 1 | Lumen 异步计算 | 保持开启 |
| `r.PostProcessing.AsyncCompute` | 0 | 1 | 后处理异步计算 | Console 开启 |

### 4.8 调试与诊断

| CVar / 命令 | 功能 | 使用场景 |
|-------------|------|----------|
| `ProfileGPU` | 捕获单帧 GPU Pass 树 | 性能瓶颈定位 |
| `stat GPU` | 实时 GPU 各 Pass 耗时 | 持续监测 |
| `stat unit` | 三端耗时 (Game/Render/GPU) | 瓶颈端确认 |
| `r.VisualizeGPU 1` | 实时 GPU Pass 时间条 | 快速定位 |
| `r.VisualizeBuffer 0-16` | GBuffer 各通道可视化 | 调试渲染错误 |
| `r.VisualizeLighting 1` | 光照可视化 | 调试光照 |
| `r.ShaderComplexity 1` | Shader 复杂度热力图 | 定位昂贵材质 |
| `r.DumpGPU -1` | 捕获当前帧 GPU 状态 | Crash 分析 |
| `r.DumpShaderDebugInfo 1` | 导出 Shader 中间表示 | Shader 编译错误 |
| `r.ShaderDevelopmentMode 1` | Shader 开发模式 | Shader 调试 |
| `r.GPUCrashDebugging 1` | GPU Crash 调试 | Crash 取证 |
| `r.RHIResourceStats` | RHI 资源统计 | 内存泄漏排查 |
| `r.RenderTargetPool` | RT 池状态 | 显存优化 |
| `r.VRAM.Dump` | VRAM 分配报告 | 显存优化 |
| `r.RHI.EnableValidation 1` | RHI Validation | 开发期验证 |
| `r.RDG.Validate 1` | RDG 验证 (5.8) | RDG 调试 |
| `r.D3D12.EnableDebugLayer 1` | D3D12 Debug Layer | 底层调试 |
| `r.Vulkan.EnableValidation 1` | Vulkan Validation | 底层调试 |
| `r.RHICmdBypass 0` | 关闭 RHI 命令旁路 | 调试 PSO 排序 |
| `r.RenderThread.Suspend 1` | 冻结渲染线程 | 调试渲染线程 Crash |
| `r.RHIThread.Enable 0` | 关闭 RHI 线程 | 简化同步调试 |
| `r.ShowMaterialDrawEvents 1` | 在 Draw Event 显示材质名 | RenderDoc 捕获 |

### 4.9 平台特定

| CVar | 默认值 | 功能 | 平台 |
|------|--------|------|------|
| `r.Vulkan.EnableValidation` | 0 | Vulkan Validation | Vulkan |
| `r.Vulkan.PrefillPools` | 1 | 预填充命令池 | Vulkan Mobile |
| `r.Vulkan.SubmitOnRenderThread` | 0 | 渲染线程异步提交 | Vulkan Mobile |
| `r.InstancedStereo` | 0 | Instanced Stereo Rendering | VR |
| `r.VR.VRS` | 0 | VR VRS 配置 | VR |
| `r.VR.FoveatedShafts` | 0 | FFR 轴辐式密度 | VR |
| `r.Mobile.FoveatedRendering` | 0 | 移动端 FFR | Mobile VR |
| `r.ESRAM.Enable` | 1 | ESRAM 分配 | Xbox One |
| `r.DynamicRes.OperationMode` | 0 | 动态分辨率模式 | Console |
| `r.DynamicRes.TargetFrameTime` | 33.33 | 动态分辨率目标帧时间 | Console |

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
- `Engine/Source/Runtime/RHI/Public/RHIAccess.h` — `ERHIAccess` / `FRHIBarrier` / `FRHITransitionInfo`
- `Engine/Source/Runtime/Renderer/Private/PostProcess/PostProcessing.cpp` — 后处理链的 RDG 编排参考

**要实操的内容**：
1. 写一个简单的全屏后处理 Pass（如灰度/反色/自定义色调映射），挂接到 `FPostProcessing::Process` 链中
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
- `Runtime/Renderer/Private/Nanite/NaniteRendering.cpp` — `RenderNanite()`
- `Runtime/Renderer/Private/Nanite/NaniteStreaming.cpp` — `FNaniteStreamingManager`
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
- `Runtime/RenderCore/Private/GPUCrashDebugging.cpp` — GPU Crash 检测
- `Runtime/D3D12RHI/Private/D3D12Debug.cpp` — D3D12 Debug Layer
- `Runtime/VulkanRHI/Private/VulkanValidation.cpp` — Vulkan Validation

**要实操的内容**：
1. 搭建多平台测试场景（PC D3D12 + Vulkan + Mobile），对比渲染效果差异
2. 用 `r.MobileHDR 0` + `r.ForwardShading 1` 模拟移动端渲染，优化至 30fps
3. 用 `r.ShaderCompiler.Stats` 观察 Shader 编译队列，定位 Permutation 爆炸源
4. 用 `bUsedWith*` 开关裁剪不必要的 Shader 变体，对比编译时间变化
5. 模拟 GPU Crash（用非法 Shader 参数），用 `r.GPUCrashDebugging` 取证
6. 用 D3D12 Debug Layer 捕获资源泄漏，用 `r.RHIResourceStats` 验证

**里程碑**：能独立处理跨平台渲染适配咨询，能给出 Shader 编译优化方案，能诊断 GPU Crash 根因

---

### 第 3 个月：综合实战与知识体系完善

**目标**：能应对客户技术咨询中的 90% 场景，能独立完成复杂渲染定制

**要读的源码**：
- `Engine/Source/Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp` — 材质表达式 → HLSL 完整流程
- `Engine/Source/Runtime/Engine/Public/MaterialShared.h` — `FMaterialShaderMap` 序列化
- `Runtime/Renderer/Private/Nanite/NaniteMaterialResolve.cpp` — Visibility Buffer → G-Buffer
- `Runtime/Renderer/Private/Lumen/LumenTracing.cpp` — 统一追踪接口
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