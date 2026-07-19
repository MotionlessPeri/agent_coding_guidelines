---
name: ue-procedural-numerical
description: Use when programmatically authoring UE RigVM / Control Rig graphs, batch-baking animation into Control Rig via Sequencer, building Optimus deformer graphs, running numerical solvers (RBF, sparse-linear, GPU) in a UE module, or parallelizing a UE C++ hot path. Six hidden contracts from procedural rigging / deformation / solver work — bulk per-element data goes in URigHierarchy metadata not pin defaults (else the graph editor hangs); batch-bake keys via section float channels not per-key SetLocalControlRig; Optimus ComputeNormalsTangents drops authored normals so use the KeepImported/KeepInput variants; FRBFSolver and TMemStackAllocator users need an active FMemMark outside anim evaluation; UE has no GPU sparse solver so bring-your-own runtime lib with CPU fallback; OpenMP will not build in a UE module so use IntelTBB or ParallelFor. Skip for non-UE work or standard UE anim/rendering without programmatic graph authoring, in-engine solving, or hot-path parallelism.
---

# UE 程序化 RigVM / 数值 / GPU / 并行

UE 里「程序化建 RigVM/ControlRig/Deformer 图 + 在模块内跑数值 / GPU 求解 / 加并行」的六组
framework hidden contract。多数踩自 curvenet 形变插件（程序化绑定 + 变形 + 数值求解）。
都属 UE 内 ultra-niche——只在做这几类活时命中，UE doc 基本没写，靠读 engine source + 踩坑得到。

| 子领域 | 解决的问题 | 内容 |
|---|---|---|
| **RigVM 建图数据投递** | 程序化建 RigVM/CR 图时逐元素大批量数据（几百+ 项）走 `URigHierarchy` element metadata，别烤成节点 pin 默认值（每 sub-pin 一个 Slate widget → 打开图卡死 + 资产膨胀）；metadata 序列化且复制到运行时实例 | [`rigvm-bulk-data-as-metadata-not-pins.md`](rigvm-bulk-data-as-metadata-not-pins.md) |
| **Sequencer 批量烤 key** | 批量烤 key 到 Control Rig 别用逐 key 的 `SetLocalControlRig*` / `SetControlValue(bNotify=true)`（~35ms/key）；直接批量写 `UMovieSceneControlRigParameterSection` 浮点通道 + 一次 `RefreshCurrentLevelSequence` + 一个 `FScopedTransaction`（含通道顺序表） | [`controlrig-sequencer-bulk-key-bake.md`](controlrig-sequencer-bulk-key-bake.md) |
| **Deformer graph 法线** | Optimus 纯 `ComputeNormalsTangents` 全重算丢 authored 法线（接缝/硬边/边界着色不连续）→ 换引擎 `Keep{Imported,Input}Normals` 变体；Wireframe/Unlit 分离「几何 vs 着色」 | [`deformer-graph-keep-authored-normals.md`](deformer-graph-keep-authored-normals.md) |
| **RBF / TMemStack 内存栈** | `FRBFSolver` / 任何 `TMemStackAllocator` 使用者，在 anim-eval 作用域外调用（test / RigUnit / 编辑器工具）必须自建活跃 `FMemMark`，否则 access violation（`AnimNode_PoseDriver` 不崩是因为 anim graph 已建 mark） | [`rbf-and-tmemstack-need-memmark.md`](rbf-and-tmemstack-need-memmark.md) |
| **GPU 数值库消费** | UE 无官方 GPU 稀疏直接求解器 → bring-your-own（cuDSS / cuSOLVER）用运行时动态加载 + 安全回退（激活即 opt-in、已知解 sanity 自证、失败退 CPU）；先 profile 确认求解真是瓶颈 | [`gpu-numerical-lib-consumption.md`](gpu-numerical-lib-consumption.md) |
| **模块内并行** | UE 模块里 OpenMP 装不了（UBT 无 per-module `/openmp`、installed engine 拒全局 flag）→ 用 `IntelTBB`（引擎自带）/ `ParallelFor`；跨框架共享 core 走编译期后端无关抽象（`#if CA_USE_TBB / CA_USE_OMP / 串行`）；行分块 data-parallel 是 bit-identical | [`ue-module-parallelism.md`](ue-module-parallelism.md) |

## When This Fires

- 程序化生成 Control Rig / 加 RigUnit / 建 RigVM 图（尤其逐元素大批量数据要投递给 RigUnit）
- 从脚本 / Sequencer 批量烤动画到 Control Rig 控件
- 给 SkeletalMesh 挂 Optimus Deformer Graph，法线在接缝 / 硬边 / 开放边界发虚或塌陷
- 在 UE 模块（automation test / RigUnit / 编辑器工具）里跑 `FRBFSolver` 或别的用 `TMemStack` 的引擎设施
- 想给 UE C++ 逐帧热点加 GPU 数值求解 / CPU 并行
- 症状：打开 CR 图卡死 / 烤 key 分钟级 / access violation 栈顶在 `AnimGraphRuntime` / 加了并行反而更慢

## How to Apply

1. 按上表定位子领域，读对应 bundled 文档的「核心规则」+「症状 → 根因」。
2. **数值 / GPU / 并行**共通纪律：性能结论靠 profiler / 分段计时（不靠猜），先确认瓶颈落在哪层；bit-identical 的并行往往比降精度 / 换后端更值。
3. **GUI 相关**（RigVM 图卡死 / deformer 法线）只在编辑器内实开验证——headless 编译过 ≠ 图能开、法线对。

## Related

- skill `ue-reference-engine-source` —— 六条锚点全靠读 engine source（`RigHierarchy.h` / `ControlRigSequencerHelpers` / DeformerFunctions / `RBFSolver.cpp` / `NNERuntimeORT` / `IntelTBB.Build.cs`）；接这类活先找引擎里谁在做同样的事
- `guidelines/cpp/hot-path-cpp.md` —— per-call `std::thread` spawn 慢是本 skill「模块内并行」规则 2 的通用面（canonical 数字在那）
- `guidelines/code/diagnose-before-fixing.md` / `guidelines/code/validation.md` —— 「先取证 / 看代码 ≠ 验证」是数值 / GPU / GUI 全部子领域的验证底座
- `guidelines/ue/external-automation-write-path.md` —— 程序化写 UE 资产走正规同步路径（RigVM 数据投递、Sequencer key 批量写都是其特例）
