# NNE 消费契约：ONNX 模型接入推理的 hidden contracts

用 UE 内置 NNE（Neural Network Engine）在 runtime 模块跑 ONNX 推理（神经网络动画 / 形变 / 任意 ML 推理）时的一组实测契约。UE 5.8 实测（vendored ONNX Runtime 1.24.1），锚点为 5.8 行号。

## 核心规则

1. **NNE 只吃 ONNX**（导入为 `UNNEModelData` 资产）；PC 上走 `NNERuntimeORT` 插件——**一个插件注册两个 runtime**：`"NNERuntimeORTCpu"`（`INNERuntimeCPU`）与 `"NNERuntimeORTDml"`（DirectML，`INNERuntimeGPU`/`INNERuntimeRDG`）。该插件 **`EnabledByDefault: false` 且标 Beta**——消费插件必须在自己 `.uplugin` 的 `Plugins` 里显式引用启用，宿主项目才会连带带起它。
2. **坏模型的报错点在 `CreateModelInstanceCPU`**：`CanCreateModelCPU` / `CreateModelCPU` 只查文件类型与数据存在性、**不解析 ONNX**——垃圾字节照样返回 Ok / 非空。ORT 真正 parse 在创建实例（session 创建）时（`LogNNERuntimeORT: ... protobuf parsing failed`）。排障先看这一步的日志。
3. **动态输出 shape 要第一次 `RunSync` 后才可查**：`SetInputTensorShapes` 只在模型**所有输出 shape 都是 concrete** 时预填 `OutputTensorShapes`（`NNERuntimeORTModel.cpp:340`）；动态输出（如 `[N]`）在第一次 `RunSync` 后才填（`:456`），且**输出 binding 容量不足时 ORT 只记录 shape、不拷数据、不报错**（静默）。应对：两跑协议（先按启发容量跑 → 查实际 shape → 不够按实际大小重跑），或跟模型作者约定"输出尺寸 = f(输入尺寸)"的公式提前算好。
4. **内存态 `UNNEModelData` 可直接推理**：`NewObject<UNNEModelData>()` + `Init(TEXT("onnx"), bytes)`（`Init` 是 `NNE_API` 导出）与 `UNNEModelDataFactory` 资产导入等价——Factory 内部就是 `Init(<扩展名>, <文件字节>)`；编辑器环境模型数据按需 cook（走 DDC）。测试 / 快速实验不必先落 Content 资产；打包运行时用 cook 好的资产。

## CPU 同步调用链

```cpp
TWeakInterfacePtr<INNERuntimeCPU> Runtime = UE::NNE::GetRuntime<INNERuntimeCPU>(TEXT("NNERuntimeORTCpu"));
Runtime->CanCreateModelCPU(ModelData);                                     // 只查类型，不解析
TSharedPtr<UE::NNE::IModelCPU> Model = Runtime->CreateModelCPU(ModelData);
TSharedPtr<UE::NNE::IModelInstanceCPU> Instance = Model->CreateModelInstanceCPU();  // ← ONNX 真正解析点
Instance->SetInputTensorShapes(Shapes);                                    // 动态输出此时还查不到 shape
Instance->RunSync(InBindings, OutBindings);   // FTensorBindingCPU{ void*, uint64 }，内存由调用方持有
```

- **runtime 注册与 RHI 无关**：`-nullrhi` headless 下 Cpu 和 Dml 都注册（headless 测试可覆盖推理链路）。
- **实例创建（ORT session）是重操作**——Create 一次、Run 多次，别每次推理重建。
- 引擎内参考实现：CPU 同步一条龙 `NNEDenoiser/Private/NNEDenoiserModelInstanceCPU.cpp`；GPU/RDG（神经网络驱动形变，最贴动画场景）`MLDeformer/VertexDeltaModel/Private/VertexDeltaModelInstance.cpp`。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 只启用消费插件、不引用 `NNERuntimeORT` | `GetRuntime` 返回无效（runtime 没注册） | 消费插件 `.uplugin` 的 `Plugins` 显式引用 |
| 拿 `CanCreateModelCPU` 当"模型合法"校验 | 垃圾模型照样过，炸在后面 | 以 `CreateModelInstanceCPU` 成败为准 |
| `SetInputTensorShapes` 后立刻按输出 shape 分配 buffer | 动态输出模型查到空列表 | 两跑协议 / 输出尺寸公式 |
| 输出 buffer 给小了，以为会报错 | 静默不拷数据（结果全是旧值） | `RunSync` 后核对 `GetOutputTensorShapes` 的实际 volume |
| 每次推理都 Create 模型实例 | 每次重建 ORT session | 缓存 runner / instance |

## 项目实例参考

UE 5.8 路径→动画生成预研插件（PathAnimGen）：先用 identity/echo ONNX（`onnx.helper` 建单个 Identity 节点、opset 17，几十行 Python 即可生成）打通"内存态 ModelData → CPU RunSync → 输出==输入"最小闭环——红测里垃圾字节在 `CreateModelInstanceCPU` 被 ORT protobuf 报错拦下，实锤规则 2；后续生成器封装撞上规则 3（`GetOutputTensorShapes` 返回 0 个），读 `NNERuntimeORTModel.cpp` 后落成两跑协议。echo 模型同时是推理链路的 round-trip oracle：输出必须逐元素等于输入，测试不依赖真模型。

## 相关 Guidelines

- skill `ue-reference-engine-source` —— 本条全部锚点来自读 `NNERuntimeORT` / `NNEDenoiser` / `MLDeformer` 源码；接 NNE 前先读它们
- [`animinstance-proxy-and-offline-eval.md`](animinstance-proxy-and-offline-eval.md) —— 同一预研的动画注入侧契约（姊妹篇）
- [`../code/validation.md`](../code/validation.md) —— echo/identity 占位模型是 round-trip oracle 的实例（`techniques/adversarial-verification.md` 的"选可信 check"）
