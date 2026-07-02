# 自定义 AnimInstance/Proxy 的更新契约 + SkeletalMeshComponent 离线评估配方

写"代码直出 pose"的自定义 `UAnimInstance` + `FAnimInstanceProxy`（神经网络 / 程序化动画注入，不走 AnimBP 资产），以及在**无引擎主循环**的环境（automation test / 编辑器工具脚本 / 离线烘焙）驱动 `USkeletalMeshComponent` 评估动画时，一组 UE 文档没写、靠实测 + 读源码得到的契约。UE 5.8 实测，锚点为 5.8 行号（跨版本行号会漂，函数名稳定）。

## 核心规则

1. **纯 C++ `UAnimInstance` 子类可以零 AnimBP 资产直出 pose**：重写 `CreateAnimInstanceProxy()` 返回自定义 proxy，proxy 重写 `Evaluate(FPoseContext&)` 直接写 `FCompactPose`（父骨骼局部空间）并 `return true`。组件侧 `SetAnimInstanceClass(原生类)` 即生效——它自动把 `AnimationMode` 切到 AnimationBlueprint 并初始化实例（`SkeletalMeshComponent.cpp:3683`）；编辑器 Details 的 Anim Class 下拉也能直接选原生类。
2. **proxy 的 `Update(float)` 每引擎帧至多跑一次**：被 `FrameCounterForUpdate != GFrameCounter` 门控（`AnimInstanceProxy.cpp` 的 native update 段，5.8 约 :1335）。同一引擎帧内多次 `TickAnimation`（测试 / 离线逐帧评估的常态）只有第一次进 `Update`——逐 update 的状态累计（时间推进等）放 **`PreUpdate`**（game thread、每次 `UpdateAnimation` 都跑、无门控）。
3. **`PreUpdateAnimation` 先于 `NativeUpdateAnimation`**（`AnimInstance.cpp:764` vs `:792`）：proxy 在 `PreUpdate` 拷到的 instance 成员是**上一次** `NativeUpdateAnimation` 写的，晚一拍（AnimBP 属性访问本来就是这个语义）。要么接受一帧延迟，要么像时间推进这类状态直接在 `PreUpdate` 里用它收到的 `DeltaSeconds` 算。
4. **离线驱动组件评估的完整配方**（引擎 `FbxAnimationExport.cpp:614-620`）：

   ```cpp
   Comp->TickAnimation(Dt, false);       // 只跑 Update 相
   Comp->RefreshBoneTransforms(nullptr); // 评估（TickFunction = nullptr → 立即执行）
   Comp->FinalizeBoneTransform();        // ★ 翻转 component space transforms 双缓冲
   ```

   `GetComponentSpaceTransforms()` 读的是双缓冲的读侧——漏掉 `FinalizeBoneTransform` 永远读到旧值，且多次评估读到的值相同，极像"动画没动"。

## 线程契约（proxy 模型）

| 回调 | 线程 | 用途 |
|---|---|---|
| `PreUpdate(UAnimInstance*, float)` | game thread | **唯一**安全的 instance → proxy 拷贝点；也是无门控的逐 update 累计点 |
| `Update(float)` | 可能 worker | 每引擎帧至多一次（规则 2） |
| `Evaluate(FPoseContext&)` | 可能 worker | 只能读 proxy 内已拷贝数据；`Output.ResetToRefPose()` 后改写；return true 表示接管 |

跨线程共享大数据（pose 序列等）用不可变对象 + `TSharedPtr<const T, ESPMode::ThreadSafe>`，`PreUpdate` 只拷指针。

## 症状 → 根因

| 症状 | 根因 |
|---|---|
| 多次 TickAnimation + 评估，骨骼变换两次读值完全相同 | 漏 `FinalizeBoneTransform`（规则 4）或 proxy 时间没走（规则 2） |
| proxy 里累计的时间恒为 0 / 只走第一步 | `Update` 帧门控（规则 2） |
| proxy 读 instance 状态总慢一拍 | `PreUpdate` 先于 `NativeUpdateAnimation`（规则 3） |
| 角色离屏 / 走出视野后动画冻结 | `VisibilityBasedAnimTickOption` 默认按可见性省 tick；离线评估 / 试验台设 `AlwaysTickPoseAndRefreshBones` |

**诊断技巧**：给 proxy 加 `EvaluateCount` 与"拷到的时间"两个观测点（instance 上加转发 accessor——`GetProxyOnGameThread<T>()` 是 protected，只能从实例方法取），一次运行即可区分"Evaluate 没跑 / 时间没走 / 读旧缓冲"三类故障。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 为程序化 pose 专门建 AnimBP 资产 + graph | 多余资产与样板 | 原生子类 + proxy `Evaluate` 直写 |
| proxy `Update(float)` 里累计时间 / 状态 | 同帧多次 tick 丢更新 | 累计放 `PreUpdate` |
| `Evaluate` 里直接读 `UAnimInstance` 成员 | worker 线程读 game thread 状态 | `PreUpdate` 拷进 proxy |
| 离线评估只 Tick + Refresh 就读变换 | 双缓冲读旧值，"看似没动" | 补 `FinalizeBoneTransform`（照抄 FbxAnimationExport 配方） |
| 断言失败先怀疑 pose 数学 | 查错方向 | 先加观测点区分三类故障，再读对应引擎源码 |

## 项目实例参考

UE 5.8 路径→动画生成预研插件（PathAnimGen）：自定义 proxy 直出正弦摆 pose 的 wiring 自动化测试两连败——第一败读旧双缓冲（`FinalizeBoneTransform` 补齐后 `EvaluateCount=4` 但时间仍为 0），第二败 proxy `Update` 帧门控（时间累计移到 instance 的 `NativeUpdateAnimation` 后又晚一拍），最终把时间累计放进 `PreUpdate` 后绿。全程靠观测点 + 读引擎源码对照取证，无盲改。

## 相关 Guidelines

- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 本条的诊断过程是范例：观测点设计成能区分竞争假设
- skill `ue-reference-engine-source` —— 离线评估配方来自 `FbxAnimationExport.cpp`；"离线驱动组件"这类需求先找引擎里谁在做同样的事
- [`nne-onnx-inference-contracts.md`](nne-onnx-inference-contracts.md) —— 同一预研的推理侧契约（姊妹篇）
