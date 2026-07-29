# RDG 知识卡片 —— UE 5.8

## 概述

RDG（Render Dependency Graph / Render Graph）是 UE 5.0+ 引入的渲染 Pass 编排框架，核心思想是**声明式构建**：开发者通过 `FRDGBuilder` 声明 Pass 和资源依赖，框架自动推导资源生命周期、GPU 屏障（barrier）和执行顺序，并进行 Pass 裁剪（culling）。

```mermaid
graph TD
    A["FRDGBuilder 构造<br/>(栈上创建)"] --> B["声明资源<br/>CreateTexture / CreateBuffer<br/>RegisterExternalTexture"]
    B --> C["注册 Pass<br/>AddPass / AddDispatchPass"]
    C --> D["AddPass 内<br/>通过 RDG 参数宏<br/>声明读写依赖"]
    D --> E["Execute() 调用"]
    E --> F["编译阶段 Compile<br/>- 推导资源状态<br/>- 生成 Barrier<br/>- 裁剪无用 Pass"]
    F --> G["串行执行阶段 ExecuteSerial<br/>- Prologue Barrier<br/>- Pass Lambda 执行<br/>- Epilogue Barrier"]
    G --> H["提取资源<br/>QueueTextureExtraction<br/>等"]
```

---

## 1. FRDGBuilder 核心概念

### 1.1 构造与析构

`FRDGBuilder` 必须在栈上创建，`Execute()` 必须在析构前调用。构造时需要 `FRHICommandListImmediate&` 引用。

```cpp
FRDGBuilder GraphBuilder(
    FRHICommandListImmediate& RHICmdList,
    FRDGEventName Name = {},
    ERDGBuilderFlags Flags = ERDGBuilderFlags::None,
    EShaderPlatform ShaderPlatform = GMaxRHIShaderPlatform
);
```

`ERDGBuilderFlags` 控制并行化行为（`RenderGraphDefinitions.h:111`）：

- `None` —— 默认，全部串行
- `ParallelSetup` —— 允许并行执行 `AddSetupTask`
- `ParallelCompile` —— 允许并行编译
- `ParallelExecute` —— 允许并行执行 Pass
- `Parallel = ParallelSetup | ParallelCompile | ParallelExecute`

### 1.2 三阶段生命周期

| 阶段 | 方法 | 说明 |
|------|------|------|
| **Setup** | 构造后到 `Execute()` 前 | 声明资源、注册 Pass、分配参数 |
| **Compile** | `Execute()` 内部 | 裁剪、Barrier 推导、资源分配 |
| **Execute** | Compile 之后 | 逐 Pass 执行 Lambda |

### 1.3 执行流程

`Execute()` 内部核心调用链（`RenderGraphBuilder.h` 私有方法）：

```
Execute()
  └─ Compile()                          // 编译：裁剪 + 推导 Barrier
       ├─ CompilePassOps()              // 逐 Pass 编译操作
       └─ ...
  └─ ExecuteSerialPass()                // 逐 Pass 串行执行
       ├─ ExecutePassPrologue()         // 提交 Prologue Barrier
       ├─ ExecutePass()                 // 执行 Pass Lambda
       └─ ExecutePassEpilogue()         // 提交 Epilogue Barrier
```

### 1.4 并行执行

Pass 执行 Lambda 若使用 `FRHICommandList&`（非 Immediate），且 `ERDGBuilderFlags` 包含 `ParallelExecute`，则可能被调度到并行任务执行。默认行为：并行任务在 `Execute()` 末尾被 await。若 Lambda 首参数为 `FRDGAsyncTask`，则不被自动 await，须手动调用 `WaitForAsyncExecuteTasks()` 或插入到 `GetAsyncExecuteTask()` 的任务图。

---

## 2. 资源声明

所有资源声明都是 `FRDGBuilder` 的**成员函数**，不是宏。

### 2.1 Texture

```cpp
FRDGTextureRef CreateTexture(
    const FRDGTextureDesc& Desc,
    const TCHAR* Name,
    ERDGTextureFlags Flags = ERDGTextureFlags::None
);
```

`FRDGTextureDesc` 提供工厂方法（`RenderGraphDefinitions.h:628`）：

- `Create2D(Size, Format, ClearValue, Flags, NumMips, NumSamples)`
- `Create2DArray(Size, Format, ClearValue, Flags, ArraySize, NumMips, NumSamples)`
- `Create3D(Size, Format, ClearValue, Flags, NumMips)`
- `CreateCube(Size, Format, ClearValue, Flags, NumMips, NumSamples)`
- `CreateCubeArray(Size, Format, ClearValue, Flags, ArraySize, NumMips, NumSamples)`

`CreateTexture` 内部实现（`RenderGraphBuilder.inl:41`）会对 `Extent` 做 clamp 避免越界，并在 Debug 构建中运行 `UserValidation.ValidateCreateTexture()`。

### 2.2 Buffer

```cpp
FRDGBufferRef CreateBuffer(
    const FRDGBufferDesc& Desc,
    const TCHAR* Name,
    ERDGBufferFlags Flags = ERDGBufferFlags::None
);

// 带 NumElements 回调的变体（元素数在创建时未知）
FRDGBufferRef CreateBuffer(
    const FRDGBufferDesc& Desc,
    const TCHAR* Name,
    FRDGBufferNumElementsCallback&& NumElementsCallback,
    ERDGBufferFlags Flags = ERDGBufferFlags::None
);
```

`FRDGBufferDesc` 工厂方法（`RenderGraphResources.h:939`）：

- `CreateByteAddressDesc(NumBytes)` —— ByteAddress buffer
- `CreateStructuredDesc(BytesPerElement, NumElements)` —— Structured buffer
- `CreateBufferDesc(BytesPerElement, NumElements)` —— 普通 typed buffer
- `CreateIndirectDesc(BytesPerElement, NumElements)` —— Indirect draw/dispatch args
- `CreateUploadDesc(...)` —— 纯上传用途（无 UAV）
- `CreateRawIndirectDesc(NumBytes)` —— ByteAddress + DrawIndirect

### 2.3 外部资源注册

```cpp
FRDGTextureRef RegisterExternalTexture(
    const TRefCountPtr<IPooledRenderTarget>& ExternalPooledTexture,
    ERDGTextureFlags Flags = ERDGTextureFlags::None
);

FRDGTextureRef RegisterExternalTexture(
    const TRefCountPtr<IPooledRenderTarget>& ExternalPooledTexture,
    const TCHAR* NameIfNotRegistered,
    ERDGTextureFlags Flags = ERDGTextureFlags::None
);

FRDGBufferRef RegisterExternalBuffer(
    const TRefCountPtr<FRDGPooledBuffer>& ExternalPooledBuffer,
    ERDGBufferFlags Flags = ERDGBufferFlags::None
);
```

外部资源（已有 `IPooledRenderTarget` 或 `FRDGPooledBuffer` 的 RHI 资源）注册到 RDG 后，RDG 会跟踪其状态并自动管理 Barrier。**去重机制**：`FRDGBuilder` 内部用 `ExternalTextures`（`RobinHoodHashMap<FRHITexture*, FRDGTexture*>`）和 `ExternalBuffers` 确保同一 RHI 资源不会重复注册。

### 2.4 查找外部资源

```cpp
FRDGTexture* FindExternalTexture(FRHITexture* Texture) const;
FRDGTexture* FindExternalTexture(IPooledRenderTarget* ExternalPooledTexture) const;
FRDGBuffer*  FindExternalBuffer(FRHIBuffer* Buffer) const;
FRDGBuffer*  FindExternalBuffer(FRDGPooledBuffer* ExternalPooledBuffer) const;
```

### 2.5 SRV / UAV 创建

```cpp
FRDGTextureSRVRef CreateSRV(const FRDGTextureSRVDesc& Desc);
FRDGBufferSRVRef  CreateSRV(const FRDGBufferSRVDesc& Desc);
FRDGTextureUAVRef CreateUAV(const FRDGTextureUAVDesc& Desc, ERDGUnorderedAccessViewFlags Flags = ERDGUnorderedAccessViewFlags::None);
FRDGBufferUAVRef  CreateUAV(const FRDGBufferUAVDesc& Desc, ERDGUnorderedAccessViewFlags Flags = ERDGUnorderedAccessViewFlags::None);
```

`ERDGUnorderedAccessViewFlags`：

- `None` —— 默认
- `SkipBarrier` —— 连续使用时不触发 UAV barrier

### 2.6 Uniform Buffer

```cpp
template <typename ParameterStructType>
TRDGUniformBufferRef<ParameterStructType> CreateUniformBuffer(const ParameterStructType* ParameterStruct);
```

### 2.7 资源提取

```cpp
void QueueTextureExtraction(FRDGTextureRef Texture, TRefCountPtr<IPooledRenderTarget>* OutPooledTexturePtr,
    ERDGResourceExtractionFlags Flags = ERDGResourceExtractionFlags::None);
void QueueTextureExtraction(FRDGTextureRef Texture, TRefCountPtr<IPooledRenderTarget>* OutPooledTexturePtr,
    ERHIAccess AccessFinal, ERDGResourceExtractionFlags Flags = ERDGResourceExtractionFlags::None);
void QueueBufferExtraction(FRDGBufferRef Buffer, TRefCountPtr<FRDGPooledBuffer>* OutPooledBufferPtr);
void QueueBufferExtraction(FRDGBufferRef Buffer, TRefCountPtr<FRDGPooledBuffer>* OutPooledBufferPtr, ERHIAccess AccessFinal);
```

`ERDGResourceExtractionFlags`：

- `None` —— 默认
- `AllowTransient` —— 允许资源维持 transient 状态（仅用于重新注册到下一个图）

### 2.8 转换到外部资源

```cpp
const TRefCountPtr<IPooledRenderTarget>& ConvertToExternalTexture(FRDGTextureRef Texture);
const TRefCountPtr<FRDGPooledBuffer>&    ConvertToExternalBuffer(FRDGBufferRef Buffer);
FRHIUniformBuffer*                       ConvertToExternalUniformBuffer(FRDGUniformBufferRef UniformBuffer);
```

这些方法用于增量迁移代码到 RDG —— 强制立即分配底层资源，使资源可被 RDG 框架外访问。

---

## 3. Pass 类型

### 3.1 AddPass —— 带参数结构体的 Pass

```cpp
template <typename ParameterStructType, typename ExecuteLambdaType>
FRDGPassRef AddPass(
    FRDGEventName&& Name,
    const ParameterStructType* ParameterStruct,  // 通过 AllocParameters() 分配
    ERDGPassFlags Flags,
    ExecuteLambdaType&& ExecuteLambda
);
```

**参数结构体**：必须通过 `AllocParameters()` 分配，生命周期绑定到 Graph。参数结构体中的 `_RDG` 宏声明的资源引用会被 RDG 自动跟踪，用于推导 Barrier 和裁剪。

**Lambda 签名**由 `ExecuteLambdaType` 推导：

| Lambda 签名 | 执行方式 | 说明 |
|---|---|---|
| `(FRHIComputeCommandList&)` | 可能并行（Await） | Compute / AsyncCompute |
| `(FRHICommandList&)` | 可能并行（Await） | Raster |
| `(FRHICommandListImmediate&)` | 强制串行（Inline） | 需要 Immediate 的调用 |
| `(FRDGAsyncTask, FRHICommandList&)` | 异步（Async） | 需手动 await |
| `(const FRDGPass*, FRHICommandList&)` | （UE 5.5 废弃） | 不再支持 |

### 3.2 AddPass —— 无参数 Pass

```cpp
template <typename ExecuteLambdaType>
FRDGPassRef AddPass(FRDGEventName&& Name, ERDGPassFlags Flags, ExecuteLambdaType&& ExecuteLambda);
```

内部使用 `FEmptyShaderParameters`。自动添加 `NeverCull` 和（如果 `Raster`）`SkipRenderPass` 标志。

### 3.3 AddPass —— 运行时参数结构体

```cpp
template <typename ExecuteLambdaType>
FRDGPassRef AddPass(
    FRDGEventName&& Name,
    const FShaderParametersMetadata* ParametersMetadata,
    const void* ParameterStruct,
    ERDGPassFlags Flags,
    ExecuteLambdaType&& ExecuteLambda
);
```

用于数据驱动的参数结构体（非编译期模板化）。

### 3.4 AddDispatchPass —— 5.8 新增

```cpp
template <typename ParameterStructType, typename LaunchLambdaType>
FRDGPassRef AddDispatchPass(
    FRDGEventName&& Name,
    const ParameterStructType* ParameterStruct,
    ERDGPassFlags Flags,
    LaunchLambdaType&& LaunchLambda
);
```

**核心区别**：Lambda 不接收 `RHICommandList&`，而是接收 `FRDGDispatchPassBuilder&`。Lambda 负责创建命令列表并启动任务来记录命令。每条命令列表需调用 `EndRenderPass()`（如果是 Raster）和 `FinishRecording()` 来完成。

**Lambda 签名**：`void(FRDGDispatchPassBuilder& DispatchPassBuilder)`

内部实现（`RenderGraphBuilder.inl:326`）：

- 如果 `Flags` 包含 `Raster`，自动添加 `SkipRenderPass`
- 创建 `TRDGDispatchPass<ParameterStructType, LaunchLambdaType>` 实例
- 注册到 `DispatchPasses` 数组

**FRDGDispatchPass**（`RenderGraphPass.h:715`）：

- 继承自 `FRDGPass`，`TaskMode` 强制为 `Async`
- 持有 `TArray<FRHICommandListImmediate::FQueuedCommandList>` 命令列表
- 持有 `UE::Tasks::FTaskEvent CommandListsEvent` 用于同步
- `Execute()` 调用 `RHICmdList.GetAsImmediate().QueueAsyncCommandListSubmit(MoveTemp(CommandLists))`

**FRDGDispatchPassBuilder**（`RenderGraphPass.h:738`）：

```cpp
class FRDGDispatchPassBuilder {
public:
    // 创建新命令列表并插入，完成时调用 FinishRecording()
    RENDERCORE_API FRHICommandList* CreateCommandList();

    // 添加 Graph 在执行时等待的任务
    RENDERCORE_API void AddPrerequisite(const UE::Tasks::FTask& Task);
};
```

### 3.5 ERDGPassFlags

定义在 `RenderGraphDefinitions.h:129`：

| Flag | 值 | 说明 |
|------|-----|------|
| `None` | 0 | 无输入/输出，仅用于无参数 Pass |
| `Raster` | 1<<0 | 图形管线光栅化 |
| `Compute` | 1<<1 | 图形管线计算 |
| `AsyncCompute` | 1<<2 | 异步计算管线 |
| `Copy` | 1<<3 | 复制命令 |
| `NeverCull` | 1<<4 | 永不裁剪（输出不可被跟踪时必需） |
| `SkipRenderPass` | 1<<5 | 跳过 RenderPass Begin/End（仅与 Raster 组合） |
| `NeverMerge` | 1<<6 | 不与其他 Pass 合并 RenderPass |
| `NeverParallel` | 1<<7 | 永不在渲染线程外执行 |
| `Readback` | Copy \| NeverCull | 复制到 staging 资源的读取回传 |

---

## 4. 资源生命周期与 Transient 资源

### 4.1 生命周期管理

RDG 资源的生命周期绑定到 Graph 的执行：

- **CPU 内存**：通过 `FRDGAllocator` 分配，保证在 Graph 执行期间有效，执行完释放
- **GPU 资源**：只对引用该资源的 Pass 保证有效；未引用的 Pass 中访问是未定义行为

### 4.2 Transient 资源

RDG 5.8 通过 `IRHITransientResourceAllocator` 支持 Transient 资源分配。`FRDGBuilder` 内部成员：

```cpp
IRHITransientResourceAllocator* TransientResourceAllocator = nullptr;
bool bSupportsTransientTextures = false;
bool bSupportsTransientBuffers = false;
```

Transient 资源在 Pass 之间即时分配和回收，可显著降低峰值内存。

`FRDGViewableResource` 中有 `bTransient` / `bForceNonTransient` 标志控制是否启用 Transient 分配。

### 4.3 外部资源生命周期

- **外部注册**（`RegisterExternalTexture`/`RegisterExternalBuffer`）：外部持有引用，RDG 只跟踪状态
- **提取**（`QueueTextureExtraction`/`QueueBufferExtraction`）：Graph 创建的资源在 `Execute()` 结束时将引用传给外部
- **转换**（`ConvertToExternalTexture`/`ConvertToExternalBuffer`）：强制立即分配底层资源

### 4.4 资源访问模式

```cpp
void UseExternalAccessMode(FRDGViewableResource* Resource, ERHIAccess ReadOnlyAccess, ERHIPipeline Pipelines = ERHIPipeline::Graphics);
void UseInternalAccessMode(FRDGViewableResource* Resource);
```

- `UseExternalAccessMode`：从某点开始，RDG 不再跟踪资源状态，允许外部代码直接访问 RHI 资源（只读）
- `UseInternalAccessMode`：恢复 RDG 跟踪

### 4.5 资源 Flags

**ERDGTextureFlags**（`RenderGraphDefinitions.h:186`）：

| Flag | 说明 |
|------|------|
| `None` | 默认 |
| `MultiFrame` | 跨帧存活（多 GPU AFR） |
| `SkipTracking` | 跳过全部 Barrier 跟踪 |
| `ForceImmediateFirstBarrier` | 首次 Barrier 不 split |
| `MaintainCompression` | 阻止元数据解压缩 |

**ERDGBufferFlags**（`RenderGraphDefinitions.h:164`）：同上三项（无 `MaintainCompression`）。

### 4.6 资源描述符

```cpp
struct FRDGTextureDesc : public FRHITextureDesc
{
    static FRDGTextureDesc Create2D(...);
    static FRDGTextureDesc Create2DArray(...);
    static FRDGTextureDesc Create3D(...);
    static FRDGTextureDesc CreateCube(...);
    static FRDGTextureDesc CreateCubeArray(...);
    static FRDGTextureDesc CreateRenderTargetTextureDesc(...);
};

struct FRDGBufferDesc
{
    uint32 BytesPerElement = 1;
    uint32 NumElements = 1;
    EBufferUsageFlags Usage = EBufferUsageFlags::None;
    const FShaderParametersMetadata* Metadata = nullptr;

    static FRDGBufferDesc CreateByteAddressDesc(...);
    static FRDGBufferDesc CreateStructuredDesc(...);
    static FRDGBufferDesc CreateBufferDesc(...);
    static FRDGBufferDesc CreateIndirectDesc(...);
    static FRDGBufferDesc CreateUploadDesc(...);
    // ...
};
```

---

## 5. Barrier 管理

### 5.1 核心架构

RDG 的 Barrier 系统基于三个核心概念：

- **FRDGBarrierBatchBegin** —— 管理一组 Barrier 的 Begin 端，创建 `FRHITransition`
- **FRDGBarrierBatchEnd** —— 管理 Barrier 的 End 端，依赖对应的 Begin batch
- **FRDGTransitionInfo** —— 紧凑的单个子资源 transition 信息

```mermaid
graph LR
    subgraph "Pass N"
        A["PrologueBarriersToBegin<br/>(资源状态变换 前)"] --> B["Pass Lambda 执行"]
        B --> C["EpilogueBarriersToBegin<br/>(资源状态变换 后)"]
    end

    D["FRDGBarrierBatchBegin<br/>创建 FRHITransition"] --> E["FRDGBarrierBatchEnd<br/>提交 Transition"]
    E --> F["RHI 执行实际 Barrier"]
```

### 5.2 FRDGTransitionInfo

紧凑的 64-bit transition 信息结构（`RenderGraphPass.h:58`）：

```cpp
struct FRDGTransitionInfo
{
    uint64 AccessBefore            : 21;
    uint64 AccessAfter             : 21;
    uint64 ResourceHandle          : 16;
    uint64 ResourceType            : 3;   // Texture / Buffer
    uint64 ResourceTransitionFlags : 3;

    union {
        struct { uint16 ArraySlice; uint8 MipIndex; uint8 PlaneSlice; } Texture;
        struct { uint64 CommitSize; } Buffer;
    };
};
```

### 5.3 FRDGBarrierBatchBegin

```cpp
class FRDGBarrierBatchBegin
{
public:
    void AddTransition(FRDGViewableResource* Resource, FRDGTransitionInfo Info);
    void AddAlias(FRDGViewableResource* Resource, const FRHITransientAliasingInfo& Info);
    void CreateTransition(TConstArrayView<FRHITransitionInfo> TransitionsRHI);
    void Submit(FRHIComputeCommandList& RHICmdList, ERHIPipeline Pipeline);
    bool IsTransitionNeeded() const;
};
```

- `PipelinesToBegin`/`PipelinesToEnd` —— 跨管线 barrier 控制
- `TransitionFlags` —— 默认 `NoFence | AllowDecayPipelines`
- `bSeparateFenceTransitionNeeded` —— 跨管线 fence 控制

### 5.4 FRDGBarrierBatchEnd

```cpp
class FRDGBarrierBatchEnd
{
public:
    void AddDependency(FRDGBarrierBatchBegin* BeginBatch);
    void Submit(FRHIComputeCommandList& RHICmdList, ERHIPipeline Pipeline);
};
```

### 5.5 每个 Pass 的 Barrier 结构

`FRDGPass` 中维护的 Barrier 相关成员（`RenderGraphPass.h`）：

- `PrologueBarriersToBegin` —— Pass 执行前的 Barrier
- `PrologueBarriersToEnd` —— 对应 End
- `EpilogueBarriersToBeginForGraphics` —— 执行后 Graphics 管线的 Barrier
- `EpilogueBarriersToBeginForAsyncCompute` —— 执行后 AsyncCompute 管线的 Barrier
- `EpilogueBarriersToBeginForAll` —— 执行后跨管线 Barrier
- `EpilogueBarriersToEnd` —— 对应 End

### 5.6 Barrier 位置

```cpp
enum class ERDGBarrierLocation : uint8
{
    Prologue,   // 在 Pass 执行前
    Epilogue    // 在 Pass 执行后
};
```

### 5.7 FRHITransitionInfo（RHI 层）

RDG Barrier 最终翻译为 RHI 的 `FRHITransitionInfo` 结构：

```cpp
struct FRHITransitionInfo
{
    FRHITransitionInfo(FRHITexture* InTexture, ERHIAccess InAccessBefore, ERHIAccess InAccessAfter, ...);
    FRHITransitionInfo(FRHIBuffer* InBuffer, ERHIAccess InAccessBefore, ERHIAccess InAccessAfter, ...);

    FRHITexture* Texture = nullptr;
    FRHIBuffer*  Buffer = nullptr;
    ERHIAccess AccessBefore = ERHIAccess::Unknown;
    ERHIAccess AccessAfter = ERHIAccess::Unknown;
    EResourceTransitionFlags TransitionFlags = EResourceTransitionFlags::None;
    // ...
};
```

`FRHITransitionCreateInfo` 控制 Barrier 创建行为（`NoFence`、`AllowDecayPipelines` 等）。

---

## 6. 裁剪与执行

### 6.1 Pass Culling

RDG 的裁剪（Culling）机制基于**资源消费方**：

- 只有被 `EpiloguePass`（根节点）可达的 Pass 才会被执行
- 不被任何提取/外部资源引用的 Graph 内资源 → 生产它的 Pass 被裁剪
- 裁剪在 `Compile()` 阶段完成，由 `FRDGPass::bCulled` 标志控制

**裁剪根（Cull Root）**：外部资源（`bExternal`）或提取资源（`bExtracted`）是裁剪根，不会被裁剪。

### 6.2 NeverCull

当 Pass 输出无法被 RDG 跟踪（如写入外部资源、通过非 RDG 参数方式输出）时，必须设置 `NeverCull` 标志，否则 Pass 会被错误裁剪。

### 6.3 NeverParallel

`ERDGPassFlags::NeverParallel` 强制 Pass 在渲染线程串行执行，不调度到并行任务。

### 6.4 Readback Flag

`ERDGPassFlags::Readback = Copy | NeverCull`，用于 GPU → CPU 读取回传场景。

### 6.5 SkipRenderPass

当 `Raster` Pass 需要自己管理 `BeginRenderPass`/`EndRenderPass` 时，设置 `SkipRenderPass`。

### 6.6 NeverMerge

阻止 RDG 将相邻 Raster Pass 合并到同一个 RenderPass 中。

### 6.7 资源裁剪检测

```cpp
// FRDGTexture
bool IsCulled() const { return ReferenceCount == 0; }

// FRDGBuffer
bool IsCulled() const { return ReferenceCount == 0 && PendingCommitSize == 0; }
```

### 6.8 资源是否已被生产

```cpp
inline bool HasBeenProduced(FRDGViewableResource* Resource);
inline FRDGTextureRef GetIfProduced(FRDGTextureRef Texture, FRDGTextureRef FallbackTexture = nullptr);
inline FRDGBufferRef  GetIfProduced(FRDGBufferRef Buffer, FRDGBufferRef FallbackBuffer = nullptr);
inline ERenderTargetLoadAction GetLoadActionIfProduced(FRDGTextureRef Texture, ERenderTargetLoadAction ActionIfNotProduced);
```

---

## 7. 自定义 Pass 注入实践

### 7.1 标准模板

```cpp
FRDGBuilder GraphBuilder(RHICmdList, RDG_EVENT_NAME("MyBuilder"));

// 1. 声明资源
FRDGTextureRef MyTexture = GraphBuilder.CreateTexture(
    FRDGTextureDesc::Create2D(Size, PF_R8G8B8A8, FClearValueBinding::Black, TexCreate_RenderTargetable | TexCreate_UAV),
    TEXT("MyTexture")
);

// 2. 分配参数
FMyPassParameters* PassParams = GraphBuilder.AllocParameters<FMyPassParameters>();
PassParams->Input = PreviousTexture;
PassParams->Output = MyTexture;
PassParams->SomeUniform = GraphBuilder.CreateUniformBuffer(&UniformData);

// 3. 注册 Pass
GraphBuilder.AddPass(
    RDG_EVENT_NAME("MyPass"),
    PassParams,
    ERDGPassFlags::Compute,
    [PassParams](FRHIComputeCommandList& RHICmdList)
    {
        // 实际渲染命令
        FMyShader::Dispatch(RHICmdList, PassParams, DispatchGroup);
    }
);

// 4. 提取结果
GraphBuilder.QueueTextureExtraction(MyTexture, &OutPooledTexture);

// 5. 执行
GraphBuilder.Execute();
```

### 7.2 外部资源注入

```cpp
// 从 PooledRenderTarget 注册
TRefCountPtr<IPooledRenderTarget> ExternalRT = ...;
FRDGTextureRef RDGTexture = GraphBuilder.RegisterExternalTexture(ExternalRT);

// 从 FRHITexture 查找已注册的
FRDGTexture* Existing = GraphBuilder.FindExternalTexture(SomeRHITexture);
```

### 7.3 外部资源在生产后的使用

```cpp
// 在不同的 Graph 或 Pass 之间传递资源
if (HasBeenProduced(SomeTexture))
{
    // 使用 Load 动作而非 Clear
    FRenderTargetBinding Binding(SomeTexture, ERenderTargetLoadAction::ELoad);
}
```

### 7.4 参数分配

```cpp
// 分配参数结构体（零初始化）
FMyPassParameters* Params = GraphBuilder.AllocParameters<FMyPassParameters>();

// 分配内存
void* Mem = GraphBuilder.Alloc(SizeInBytes, AlignInBytes);
template<typename T> T*     Ptr = GraphBuilder.AllocPOD<T>();
template<typename T> T*     Arr = GraphBuilder.AllocPODArray<T>(Count);
template<typename T> T*     Obj = GraphBuilder.AllocObject<T>(Args...);
template<typename T> TArray<T, SceneRenderingAllocator>& Arr = GraphBuilder.AllocArray<T>();
```

### 7.5 Buffer 上传

```cpp
// 上传数据到 buffer（在 Execute 前）
GraphBuilder.QueueBufferUpload(MyBuffer, InitialData, InitialDataSize);

// 带回调的变体
GraphBuilder.QueueBufferUpload(MyBuffer,
    FRDGBufferInitialDataCallback([&]() { return GetData(); }),
    FRDGBufferInitialDataSizeCallback([&]() { return GetDataSize(); })
);
```

---

## 8. 关键源码文件索引

| 文件 | 路径（相对于 `Engine/Source/Runtime/RenderCore/Public/`） | 核心内容 |
|------|------|----------|
| `RenderGraphBuilder.h` | `RenderGraphBuilder.h` | `FRDGBuilder` 主类声明（AddPass / Execute / 资源创建等） |
| `RenderGraphBuilder.inl` | `RenderGraphBuilder.inl` | `FRDGBuilder` 内联实现（资源创建、AddPass 模板、AddDispatchPass） |
| `RenderGraphPass.h` | `RenderGraphPass.h` | `FRDGPass` / `TRDGLambdaPass` / `FRDGDispatchPass` / `FRDGDispatchPassBuilder` / Barrier 批处理 |
| `RenderGraphDefinitions.h` | `RenderGraphDefinitions.h` | 枚举定义（`ERDGPassFlags` / `ERDGBufferFlags` / `ERDGTextureFlags` / `ERDGSetupTaskWaitPoint`）、Handle 类型、`FRDGTextureDesc` |
| `RenderGraphResources.h` | `RenderGraphResources.h` | `FRDGResource` / `FRDGViewableResource` / `FRDGTexture` / `FRDGBuffer` / `FRDGUniformBuffer` / View 类型、`FRDGBufferDesc` |
| `RenderGraphFwd.h` | `RenderGraphFwd.h` | 前向声明和类型别名（`FRDGTextureRef` 等） |
| `RenderGraphBlackboard.h` | `RenderGraphBlackboard.h` | `FRDGBlackboard` 黑板数据结构 |
| `RenderGraphAllocator.h` | `RenderGraphAllocator.h` | `FRDGAllocator` 分配器 |
| `RenderGraphEvent.h` | `RenderGraphEvent.h` | `FRDGEventName` 事件名 |
| `RenderGraphUtils.h` | `RenderGraphUtils.h` | 工具函数（`HasBeenProduced` / `GetIfProduced` / `GetLoadActionIfProduced` / `TryGetRHI` 等） |
| `RenderGraphValidation.h` | `RenderGraphValidation.h` | `FRDGUserValidation` 用户验证类 |
| `RenderGraphTrace.h` | `RenderGraphTrace.h` | RDG Insight 追踪 |
| `RenderGraphTextureSubresource.h` | `RenderGraphTextureSubresource.h` | 子资源布局/范围类型 |
| `DumpGPU.h` | `DumpGPU.h` | GPU 资源转储框架 |
| `GlobalShader.h` | `GlobalShader.h` | 全局 Shader 管理 |
| `ShaderParameterStruct.h` | `ShaderParameterStruct.h` | Shader 参数结构体宏（`_RDG` 宏） |

**实现文件**（`Private/` 目录下）：

| 文件 | 路径 | 核心内容 |
|------|------|----------|
| `RenderGraph.cpp` | `Private/RenderGraph.cpp` | `FRDGBuilder::Execute()` / `Compile()` 等核心实现 |
| `DumpGPU.cpp` | `Private/DumpGPU.cpp` | `FRDGResourceDumpContext` 完整实现 |
| `RenderGraphValidation.cpp` | `Private/RenderGraphValidation.cpp` | `FRDGUserValidation` 实现 |
| `RenderGraphBlackboard.cpp` | `Private/RenderGraphBlackboard.cpp` | `FRDGBlackboard::AllocateIndex` 等 |

---

## 9. UE 5.8 新增特性

### 9.1 AddDispatchPass + FRDGDispatchPass

**5.8 新增**。允许 Pass 创建多条命令列表并异步提交，突破单条命令列表的限制。

`AddDispatchPass` 的 Lambda 接收 `FRDGDispatchPassBuilder&` 而非 `FRHICommandList&`，通过 `CreateCommandList()` 创建独立命令列表，每条命令列表需 `FinishRecording()` 完成录制。

**执行流程**：

```
AddDispatchPass 注册
  → FRDGDispatchPass 创建（TaskMode = Async, bDispatchPass = 1）
  → Execute() 阶段：QueueAsyncCommandListSubmit 提交所有命令列表
  → FRDGDispatchPassBuilder::CreateCommandList() 创建 FRHICommandList
  → Lambda 中用户调用 EndRenderPass() + FinishRecording()
  → FRDGDispatchPass::Execute() 提交所有命令列表
```

**关键源码**（`RenderGraphPass.h:715-768`）：

```cpp
class FRDGDispatchPass : public FRDGPass
{
    // bDispatchPass = 1
    // TaskMode = ERDGPassTaskMode::Async
    void Execute(FRHIComputeCommandList& RHICmdList) override
    {
        RHICmdList.GetAsImmediate().QueueAsyncCommandListSubmit(MoveTemp(CommandLists));
    }
    TArray<FRHICommandListImmediate::FQueuedCommandList, FRDGArrayAllocator> CommandLists;
    UE::Tasks::FTaskEvent CommandListsEvent{ UE_SOURCE_LOCATION };
};

class FRDGDispatchPassBuilder
{
    FRHICommandList* CreateCommandList();
    void AddPrerequisite(const UE::Tasks::FTask& Task);
};
```

### 9.2 FRDGBlackboard

**5.8 新增**。一种映射结构，生命周期绑定到 Render Graph Allocator，用于跨 Pass 传递不可变数据，避免显式 marshalling。

**关键 API**（`RenderGraphBlackboard.h:56`）：

```cpp
class FRDGBlackboard
{
    template <typename StructType, typename... ArgsType>
    StructType& Create(ArgsType&&... Args);           // 创建实例（断言唯一）

    template <typename StructType>
    StructType* GetMutable() const;                   // 获取可变指针（可能 null）

    template <typename StructType>
    const StructType* Get() const;                    // 获取不可变指针（可能 null）

    template <typename StructType, typename... ArgsType>
    StructType& GetOrCreate(ArgsType&&... Args);      // 获取或创建

    template <typename StructType>
    StructType& GetMutableChecked() const;            // 获取（断言存在）

    template <typename StructType>
    const StructType& GetChecked() const;             // 获取（断言存在）
};
```

**使用步骤**：

1. 用 `RDG_REGISTER_BLACKBOARD_STRUCT(StructType)` 宏注册结构体
2. 在初始化阶段调用 `GraphBuilder.Blackboard.Create<FMyStruct>(...)` 创建
3. 在后续 Pass 中调用 `GraphBuilder.Blackboard.GetChecked<FMyStruct>()` 读取

### 9.3 FRDGResourceDumpContext

**5.8 新增**。GPU 资源转储的核心上下文，用于调试和故障排查。

**关键成员**（`Private/DumpGPU.cpp:253`）：

```cpp
class FRDGResourceDumpContext
{
    static constexpr const TCHAR* kBaseDir = TEXT("Base/");
    static constexpr const TCHAR* kPassesDir = TEXT("Passes/");
    static constexpr const TCHAR* kResourcesDir = TEXT("Resources/");
    static constexpr const TCHAR* kStructuresDir = TEXT("Structures/");
    static constexpr const TCHAR* kStructuresMetadataDir = TEXT("StructuresMetadata/");

    bool bEnableDiskWrite = false;
    bool bUpload = false;
    bool bStream = false;
    float DeltaTime = 0.0f;
    int32 DumpedFrameId = 0;
    int32 FrameCount = 1;

    void Start();   // 创建目录结构 + 初始化转储文件
    void Finish();  // 完成转储 + 计时统计

    // 输出文件：Passes.json / ResourceDescs.json / PassDrawCounts.json / Infos.json / Status.txt
};
```

`FRDGBuilder` 中的入口：

```cpp
// RenderGraphBuilder.h:436
#if RDG_DUMP_RESOURCES
static RENDERCORE_API FString BeginResourceDump(const TCHAR* Cmd = TEXT(""), const TCHAR* Context = TEXT(""));
static RENDERCORE_API bool IsDumpingFrame();
#endif
```

### 9.4 AddSetupTask

**5.8 新增**。在 Graph 执行前启动并行任务，用于准备数据。

```cpp
template <typename TaskLambda>
UE::Tasks::FTask AddSetupTask(
    TaskLambda&& Task,
    bool bCondition = true,
    ERDGSetupTaskWaitPoint WaitPoint = ERDGSetupTaskWaitPoint::Compile
);

template <typename TaskLambda>
UE::Tasks::FTask AddSetupTask(
    TaskLambda&& Task,
    UE::Tasks::ETaskPriority Priority,
    bool bCondition = true,
    ERDGSetupTaskWaitPoint WaitPoint = ERDGSetupTaskWaitPoint::Compile
);

// 带 Pipe 的变体
template <typename TaskLambda>
UE::Tasks::FTask AddSetupTask(
    TaskLambda&& Task,
    UE::Tasks::FPipe* Pipe,
    UE::Tasks::ETaskPriority Priority = UE::Tasks::ETaskPriority::Normal,
    bool bCondition = true,
    ERDGSetupTaskWaitPoint WaitPoint = ERDGSetupTaskWaitPoint::Compile
);

// 带 Prerequisites 的变体
template <typename TaskLambda, typename PrerequisitesCollectionType>
UE::Tasks::FTask AddSetupTask(
    TaskLambda&& Task,
    PrerequisitesCollectionType&& Prerequisites,
    UE::Tasks::ETaskPriority Priority = UE::Tasks::ETaskPriority::Normal,
    bool bCondition = true,
    ERDGSetupTaskWaitPoint WaitPoint = ERDGSetupTaskWaitPoint::Compile
);
```

`ERDGSetupTaskWaitPoint`（`RenderGraphDefinitions.h:210`）：

| 值 | 说明 |
|-----|------|
| `Compile` | （默认）在编译前同步。任务会修改 RDG 资源（如 buffer 上传内容、size callback）时使用 |
| `Execute` | 在执行前同步。任务不影响 RDG 编译时使用 |

还有 `AddCommandListSetupTask` 系列，用于需要在命令列表上下文中执行的 setup 任务。

### 9.5 AddPassDependency

**5.8 新增**。在 Pass 之间添加用户定义的依赖，用于微调异步计算的重叠。

```cpp
RENDERCORE_API void AddPassDependency(FRDGPass* Producer, FRDGPass* Consumer);
```

### 9.6 SetPassWorkload

**5.8 新增**。设置 Pass 执行 Lambda 的预期工作负载，用于指导并行调度。

```cpp
void SetPassWorkload(FRDGPass* Pass, uint32 Workload);
```

默认 `Workload = 1`。推荐设置为复杂 draw/dispatch 调用的数量，仅当某个 Pass 相对其他 Pass 非常昂贵时作为性能调优使用。

### 9.7 其他 5.8 变化

- `ParallelCompile` 和 `ParallelSetup` 分离为独立的 `ERDGBuilderFlags`（之前合并为 `ParallelSetup`）
- `FRDGPass::bDispatchPass` 标志用于区分 Dispatch Pass 和普通 Pass
- `FRDGDispatchPass` 的 `LaunchDispatchPassTasks` 虚方法被 `FRDGDispatchPassBuilder` 调用
- 5.5 废弃的 `FRDGPass*` lambda 参数在 5.8 中确认不再支持
- `GLevelEditorModeToolsIsValid()` 在 5.8 中已删除定义（注：此条为编辑器相关，非 RDG 核心）

---

## 附录：RDG 参数宏

Pass 参数结构体中使用 `_RDG` 后缀宏声明资源引用，使 RDG 可以自动跟踪依赖：

```cpp
BEGIN_SHADER_PARAMETER_STRUCT(FMyPassParameters, )
    RDG_TEXTURE_ACCESS(Input, ERHIAccess::SRV)       // 输入纹理
    RDG_TEXTURE_ACCESS(Output, ERHIAccess::UAV)       // 输出纹理 UAV
    RDG_BUFFER_ACCESS(IndirectArgs, ERHIAccess::IndirectArgs)
    SHADER_PARAMETER_RDG_TEXTURE(SceneColor)           // 纹理 SRV
    SHADER_PARAMETER_RDG_BUFFER(VertexBuffer)           // 缓冲区 SRV
    SHADER_PARAMETER_RDG_TEXTURE_UAV(OutputUAV)        // 纹理 UAV
    SHADER_PARAMETER_RDG_BUFFER_UAV(OutputBufferUAV)   // 缓冲区 UAV
    SHADER_PARAMETER_RDG_UNIFORM_BUFFER(ViewUB)        // Uniform Buffer
    RDG_RENDER_TARGET_BINDING_SLOTS()                  // RenderTarget 绑定
END_SHADER_PARAMETER_STRUCT()
```

这些宏展开为 RDG 能识别的成员字段，在 `AddPass` 时被 `FRDGParameterStruct` 解析，用于推导资源访问模式、Barrier 和裁剪。

---

## 附录：资源类继承关系

```mermaid
classDiagram
    class FRDGResource {
        +const TCHAR* Name
        +FRHIResource* ResourceRHI
        +GetRHI()
        +MarkResourceAsUsed()
    }

    class FRDGViewableResource {
        +ERDGViewableResourceType Type
        +IsExternal()
        +IsExtracted()
        +HasBeenProduced()
    }

    class FRDGTexture {
        +FRDGTextureDesc Desc
        +ERDGTextureFlags Flags
        +GetRHI() FRHITexture*
        +IsCulled()
    }

    class FRDGBuffer {
        +FRDGBufferDesc Desc
        +ERDGBufferFlags Flags
        +GetRHI() FRHIBuffer*
        +IsCulled()
    }

    class FRDGView {
        +ERDGViewType Type
        +GetParent() FRDGViewableResource*
    }

    class FRDGShaderResourceView {
        +GetRHI() FRHIShaderResourceView*
    }

    class FRDGUnorderedAccessView {
        +ERDGUnorderedAccessViewFlags Flags
        +GetRHI() FRHIUnorderedAccessView*
    }

    class FRDGUniformBuffer {
        +GetRHI() FRHIUniformBuffer*
        +GetParameters()
    }

    FRDGResource <|-- FRDGViewableResource
    FRDGViewableResource <|-- FRDGTexture
    FRDGViewableResource <|-- FRDGBuffer
    FRDGResource <|-- FRDGView
    FRDGView <|-- FRDGShaderResourceView
    FRDGView <|-- FRDGUnorderedAccessView
    FRDGResource <|-- FRDGUniformBuffer
    FRDGTextureSRV --|> FRDGShaderResourceView
    FRDGTextureUAV --|> FRDGUnorderedAccessView
    FRDGBufferSRV --|> FRDGShaderResourceView
    FRDGBufferUAV --|> FRDGUnorderedAccessView
```

---

## 附录：Pass 类继承关系

```mermaid
classDiagram
    class FRDGPass {
        +FRDGEventName Name
        +ERDGPassFlags Flags
        +ERHIPipeline Pipeline
        +FRDGParameterStruct ParameterStruct
        +GetWorkload()
        +IsCulled()
        +IsParallelExecuteAllowed()
    }

    class FRDGSentinelPass {
        +bSentinel = 1
    }

    class FRDGDispatchPass {
        +bDispatchPass = 1
        +CommandLists
        +Execute() 提交命令列表
    }

    class TRDGLambdaPass~ParameterStruct, ExecuteLambda~ {
        +Execute() 执行 Lambda
    }

    class TRDGDispatchPass~ParameterStruct, LaunchLambda~ {
        +LaunchDispatchPassTasks()
    }

    FRDGPass <|-- FRDGSentinelPass
    FRDGPass <|-- FRDGDispatchPass
    FRDGPass <|-- TRDGLambdaPass
    FRDGDispatchPass <|-- TRDGDispatchPass
    FRDGSentinelPass : Prologue / Epilogue 哨兵
    TRDGLambdaPass : 普通 AddPass
    TRDGDispatchPass : 5.8 AddDispatchPass
```