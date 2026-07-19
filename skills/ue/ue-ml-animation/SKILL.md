---
name: ue-ml-animation
description: Use when writing UE C++ that drives skeletal animation from code or a neural network instead of an AnimBP state machine — a custom `UAnimInstance` + `FAnimInstanceProxy` that writes pose directly, or running ONNX inference in-engine via NNE (Neural Network Engine). Covers the AnimInstance/proxy update contract (Update() is frame-gated by GFrameCounter, PreUpdate ordering, the offline-eval recipe TickAnimation to RefreshBoneTransforms to FinalizeBoneTransform), and NNE ONNX consumption contracts (NNERuntimeORT must be enabled by the consumer plugin, errors surface at CreateModelInstanceCPU, dynamic output shape only queryable after the first RunSync with a silent no-copy on undersized buffers). Skip for non-UE projects, or animation that uses standard AnimBP graphs with no code-driven pose or ML inference.
---

# UE ML / 程序化驱动动画

UE 里「代码或神经网络直出 pose、不走 AnimBP 状态机」的两组 framework hidden contract。
来自 PathAnimGen 预研（路径→动画生成插件）M1–M3。两侧配套：动画注入侧 + 模型推理侧。

| 侧面 | 解决的问题 | 内容 |
|---|---|---|
| **动画注入** | 纯 C++ `UAnimInstance` 子类 + 自定义 `FAnimInstanceProxy` 零 AnimBP 资产直出 pose；proxy `Update(float)` 被 `GFrameCounter` 门控成每帧一次（累计放 `PreUpdate`）；`PreUpdate` 先于 `NativeUpdateAnimation`（instance 状态晚一拍）；离线评估配方 `TickAnimation → RefreshBoneTransforms → FinalizeBoneTransform`（漏最后一步永远读旧双缓冲） | [`animinstance-proxy-and-offline-eval.md`](animinstance-proxy-and-offline-eval.md) |
| **模型推理** | NNE 只吃 ONNX；`NNERuntimeORT` 默认关闭需消费插件 `.uplugin` 显式引用；坏模型报错点在 `CreateModelInstanceCPU`（CanCreate 不解析）；动态输出 shape 第一次 `RunSync` 后才可查、buffer 不足时**静默不拷数据**（两跑协议）；内存态 `UNNEModelData::Init` 与资产导入等价（测试不依赖 Content） | [`nne-onnx-inference-contracts.md`](nne-onnx-inference-contracts.md) |

两侧常一起命中：一个 tick 里 NNE 推理出骨骼变换 → 经自定义 proxy 写进 pose。

## When This Fires

- 写「代码直出 pose」的自定义 `UAnimInstance` / `FAnimInstanceProxy`（神经网络 / 程序化动画注入，不走 AnimBP 资产）
- 在无引擎主循环的环境（automation test / 编辑器工具 / 离线烘焙）驱动 `USkeletalMeshComponent` 评估动画
- 用 UE 内置 NNE 在 runtime 模块跑 ONNX 推理（动画 / 形变 / 任意 ML 推理）
- 症状：多次 tick 后骨骼变换读到相同值 / proxy 时间不走 / NNE 输出 0 个 shape / 坏模型不报错

## How to Apply

1. **动画注入**：读 `animinstance-proxy-and-offline-eval.md` 的线程契约表（`PreUpdate` 唯一安全拷贝点）+ 离线评估配方，累计状态放 `PreUpdate` 不放 `Update`。
2. **模型推理**：读 `nne-onnx-inference-contracts.md` 的 CPU 同步调用链，以 `CreateModelInstanceCPU` 成败判模型合法，动态输出走两跑协议。
3. **验证**：两条都靠观测点 / round-trip oracle 取证（不靠「看代码对」），遇故障先加观测点区分竞争假设再读引擎源码。

## Related

- skill `ue-reference-engine-source` —— 两侧全部锚点来自读 engine source（`FbxAnimationExport.cpp` 离线配方 / `NNERuntimeORT` / `NNEDenoiser` / `MLDeformer`）；接这类活先找引擎里谁在做同样的事
- `guidelines/code/diagnose-before-fixing.md` —— 观测点设计成能区分竞争假设，是本 skill 诊断纪律的通用面
- `guidelines/code/validation.md` —— echo/identity 占位模型作 round-trip oracle
