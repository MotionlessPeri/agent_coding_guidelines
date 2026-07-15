# `FRBFSolver` / 任何用 `TMemStackAllocator` 的引擎设施,在 anim-eval 作用域外调用要自建 `FMemMark`

## 核心规则

从 **automation test / 编辑器工具 / ControlRig RigUnit / 任何不在 anim(或 render)评估管线里的地方**调用
`FRBFSolver::InitSolver` / `FRBFSolver::Solve`(以及**任何内部用 `TMemStackAllocator` / `FMemStack` 的引擎
设施**)时,**必须先自建一个活跃的 `FMemMark` 内存栈作用域**,否则 **access violation**(不是 check 断言,是
未处理异常):

```cpp
#include "Misc/MemStack.h"   // 注意:是 Misc/,不是 HAL/

void MyStandaloneRBFEval(...)
{
    // FRBFSolver 的 interpolative InitSolver 建 kernel 时走 TMemStackAllocator(RBFInterpolator.h
    // MakeUpperKernel);没有活跃 FMemMark → 从未准备好的 mem stack 分配 → AV。
    FMemMark Mark(FMemStack::Get());          // ★ 必须,且要活到 InitSolver + Solve 都跑完

    FRBFParams Params = /* ... */;
    TArray<FRBFTarget> Targets = /* ... */;
    TSharedPtr<const FRBFSolverData> Data = FRBFSolver::InitSolver(Params, Targets);   // 没 FMemMark 就崩这
    FRBFEntry Input = /* ... */;
    TArray<FRBFOutputWeight> Weights;
    FRBFSolver::Solve(*Data, Params, Targets, Input, Weights);
    // Mark 出作用域自动 unwind
}
```

**为什么 `FAnimNode_PoseDriver` 不崩**:它跑在 anim graph 评估里,外层 `FAnimInstanceProxy` 已经建好了
`FMemMark` 作用域。所以引擎自己的 RBF 用法从不显式建 mark —— 依赖调用栈上层已有。你**把它搬到 anim-eval
之外**(独立测试 / 编辑器 / RigUnit)就失去了这个隐式前提。

## 机制(带 engine source 锚点)

- `FRBFSolver::InitSolver`(`AnimGraphRuntime/Private/RBF/RBFSolver.cpp`)对 `Interpolative` solver 建
  `TRBFInterpolator`;其构造 → `MakeUpperKernel()`(`AnimGraphRuntime/Public/RBF/RBFInterpolator.h`)里
  `TArray<float, TMemStackAllocator<>> UpperKernel;` —— 从 `FMemStack` 分配。
- `TMemStackAllocator` 从 `FMemStack::Get()`(线程本地内存栈)拿内存,**假设调用栈上有活跃的 `FMemMark`**
  界定/回收这段分配。评估管线(anim / render)在顶层建 mark;脱离该管线独立调用时栈未处于预期状态 →
  分配崩(access violation)。
- 症状特征:**不是** `Assertion failed`(check),而是 `LogWindows: Error: [Callstack] ... AnimGraphRuntime.dll`
  + `ExceptionHandler` + 进程 exit code 3;栈顶几帧在 `AnimGraphRuntime`(RBF 内部),下面是你的调用点。

## 泛化

不止 RBF。**任何引擎 API 内部用 `TMemStackAllocator` / `FMemStack` / `FMemMark` 且原本设计在 anim/render
评估里调用的设施**,搬到下列语境时都要自问「上层还有没有 FMemMark」:

- automation test / headless commandlet 里直接调
- 编辑器工具 / Slate / details 回调里调
- **ControlRig 的 RigUnit `Execute` 里调**(RigUnit 是否运行在某个 mem-mark 作用域内不保证 —— 要么实测确认,
  要么自建一个,自建是无害的防御)

拿不准就**自建 `FMemMark`**:多建一个是廉价且无害的(嵌套 mark 合法),漏建则可能 AV 或内存栈污染。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 从 test / 编辑器 / RigUnit 直接调 `FRBFSolver::InitSolver` 不建 mark | access violation(非 check,难懂) | 调用前 `FMemMark Mark(FMemStack::Get())` |
| 撞 AV 去查自己的 RBF 数据(targets / params)对不对 | 查错方向(数据没问题,是缺 mem-mark 作用域) | 先看栈顶在不在 AnimGraphRuntime 内部 + 是否 anim-eval 外调用 |
| `#include "HAL/MemStack.h"` | 找不到头文件(编译失败) | 是 `#include "Misc/MemStack.h"` |
| 只在 InitSolver 前建 mark,Solve 时已出作用域 | Solve 也可能用 mem stack → 崩 | mark 活到 InitSolver + Solve 都完成 |

## 项目实例参考

UE 5.8 curvenet 形变插件(CurveArticulationUE)PSD B 层 M2:把 PoseWrangler 的 RBF 求解搬进 Core 模块的一个
纯函数(`CurveNetPSDSolve::SolveWeights`,给 headless automation test + 将来的 ControlRig RigUnit 用),
第一版直接调 `FRBFSolver::InitSolver` → automation test 里 access violation(exit 3,栈顶在
`AnimGraphRuntime.dll` 的 InitSolver 内)。逐层读 engine source(InitSolver → TRBFInterpolator →
MakeUpperKernel 的 `TMemStackAllocator`)定位到缺 `FMemMark`;`FMemMark Mark(FMemStack::Get())`(`Misc/MemStack.h`)
后测试转绿。对照 `AnimNode_PoseDriver.cpp` 确认引擎自己的 RBF 用法无此建 mark —— 因它依赖 anim eval 上层的 mark。

## 相关 Guidelines / Skills

- skill `ue-reference-engine-source` —— 本条全靠读 engine source(RBFSolver.cpp / RBFInterpolator.h /
  AnimNode_PoseDriver.cpp)定位;UE doc 完全没提这个 mem-mark 前提。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 本条的定位过程是范例:AV 后不猜「RBF 数据错」,
  逐层读崩溃栈涉及的 engine 实现,把「数据错 vs 缺执行上下文」两个竞争假设区分开。
- [`../code/validation.md`](../code/validation.md) —— 「headless / 独立调用」跟「引擎正常评估里调用」的执行上下文不同;
  一个能跑不代表另一个能跑,必须在目标语境实测(本条正是「PoseDriver 里能跑 ≠ 独立调用能跑」)。
