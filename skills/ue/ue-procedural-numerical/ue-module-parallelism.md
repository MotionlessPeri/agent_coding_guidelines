# UE 模块内并行:OpenMP 装不了,用 IntelTBB(引擎自带)/ ParallelFor;共享 core 走后端无关抽象

给 UE C++ 模块里的 CPU 热点(逐帧数值循环 / 稀疏矩阵乘 / 大数组处理)加**多线程并行**时,一组
「看着该 work 实际 work 不了」的 hidden contract + 一个跨框架共享库的可移植 pattern。**非 UE 项目
可 skip OpenMP/TBB 那两条**,但「per-call 线程 spawn 慢」「行分块并行 bit-identical」是通用的。

## 核心规则

1. **UE 模块里 OpenMP 基本用不了**——UBT 无 per-module `/openmp` 旋钮;target 级
   `AdditionalCompilerArguments="/openmp"` 在 **installed engine 上被拒**(报
   `modifies the values of properties: [AdditionalCompilerArguments] … build products in common
   with UnrealEditor`)。想并行用 **`IntelTBB`(引擎自带)或 `ParallelFor`(UE task system)**,不要 OpenMP。
2. **per-call `std::thread` spawn 别用**——逐帧调用的热路径里每次新建/join 线程,spawn 开销吊打
   收益(实测比串行慢一个量级)。用**持久池**(TBB / UE task system 都是池化)。详
   `guidelines/cpp/hot-path-cpp.md`。
3. **跨框架共享库**(同一份 core 被 UE + 别的 host 如 Maya 各自编译)做并行:用**编译期后端无关
   抽象**(`#if CA_USE_TBB / #elif CA_USE_OMP / #else 串行 fallback`)。core **不硬依赖任何并行库**;
   每个 host 编译期选自己的池 + 提供依赖(UE=IntelTBB;Maya/CMake=OpenMP `find_package(OpenMP)`;
   都不定义=串行、照样编过)。
4. **按输出行/元素分块的 data-parallel(每个输出独立、内部 reduction 顺序不变)是 bit-identical**
   ——跟串行逐位一致,零数值风险。有 scatter-add(多输入写同一输出)的段保持串行,或用 per-thread
   桶再合并(否则既有写竞争、又破坏 bit-identical)。

## 为什么 OpenMP 在 UE 用不了(带证据)

- **UBT 无 per-module 编译-flag 旋钮**:`ModuleRules` 没有 `AdditionalCompilerArguments` / `bEnableOpenMP`
  之类字段(只有 target 级 `TargetRules.AdditionalCompilerArguments` → 全局 `GlobalCompileEnvironment`)。
- **installed engine 拒全局 flag**:源码构建 / launcher 的 installed distribution,项目 target 跟预编译
  `UnrealEditor` **共享构建产物**,改任何全局编译属性(`/openmp`)→ UBT 报错拒编(同
  `guidelines/ue/ue58-upgrade-gotchas.md` 的 Target 属性一致性约束族)。
- **Epic 自己回避 OpenMP**:引擎带 OpenMP 的第三方库(如 FAISS)不开 `/openmp`,而是**提供一个 stub
  `omp.h`**(`omp_get_max_threads()` 恒返回 1、锁全 no-op)让它**编成串行**,注释原话
  *"All parallelism is managed by UE's task system instead, avoiding extra thread pools in the editor."*
  → 拿 stub 能让「假设 OpenMP 的代码编过」,但**是串行、拿不到并行**。
- **IntelTBB 是引擎一等公民**:`Engine/Source/ThirdParty/Intel/TBB`(oneTBB;`tbb12.dll` 已在进程),
  `IntelTBB.Build.cs` 走 `PublicSystemIncludePaths`(→ TBB 头**免 warnings-as-errors**)。模块加
  `PrivateDependencyModuleNames.Add("IntelTBB")` 即拿头 + 链库,`#include <tbb/parallel_for.h>` 直接可用。

## TBB vs OpenMP:线程行为(为什么 UE 选 TBB、OMP 消费者必须封顶)

同一份行分块 parallel-for,最优性能两者打平,但默认行为相反:

| | TBB | MSVC OpenMP(vcomp,OpenMP 2.0) |
|---|---|---|
| 默认线程数 | 硬件线程,work-stealing | 硬件线程 |
| 空闲等待 | passive-wait(让核) | **busy-spin-wait**(占核);`OMP_WAIT_POLICY` 关不掉 |
| 默认开箱 | 健壮(免调) | **多核机上过度订阅 → 比串行还慢**(实测 36 核默认 0.88×) |
| 要不要调 | 不用 | **必须 cap 线程**(如 `clamp(cores/4, 2, 8)` + 设 `OMP_NUM_THREADS`) |

→ **UE 用 TBB**(引擎自带 + 开箱健壮);用 OpenMP 的 host(如 Maya,避开跟自带 tbb.dll 版本冲突)
**必须 host 侧 cap 线程数**,别按核数默认开。core 的 OMP 分支应尊重 `OMP_NUM_THREADS`(由 host 设)。

## 后端无关抽象(可移植 pattern)

```cpp
// 共享 core 里:一个 parallel-for over [0,n),各段行不相交;编译期选后端,串行兜底。
template <class Fn>
void caParallelFor(int n, int grain, Fn&& fn) {
    if (n <= 0) return;
#if defined(CA_USE_TBB)
    tbb::parallel_for(tbb::blocked_range<int>(0, n, grain),
        [&fn](const auto& r){ fn((int)r.begin(), (int)r.end()); });
#elif defined(CA_USE_OMP)
    int nT = omp_get_max_threads();                        // 尊重 host 设的 OMP_NUM_THREADS
    int nChunks = std::min(nT, std::max(1, n / std::max(1, grain)));
    int chunk = (n + nChunks - 1) / nChunks;
    #pragma omp parallel for schedule(static)
    for (int c = 0; c < nChunks; ++c) { int s=c*chunk, e=std::min(n, s+chunk); if (s<e) fn(s, e); }
#else
    fn(0, n);                                              // 串行 fallback(哪个 host 都编得过)
#endif
}
```
消费方:UE `Build.cs` → `PrivateDefinitions.Add("CA_USE_TBB=1")` + `PrivateDependencyModuleNames.Add("IntelTBB")`;
Maya `CMakeLists.txt` → `find_package(OpenMP)` + `target_link_libraries(<lib> PUBLIC OpenMP::OpenMP_CXX)` +
`target_compile_definitions(<lib> PUBLIC CA_USE_OMP)`。

**thread_local 陷阱**:并行 lambda 里若直接访问 `static thread_local` 缓冲,worker 线程会解析到
**自己的空实例**(崩)。取**局部引用别名**(automatic 引用被 `[&]` 捕获)→ worker 经引用访问主线程实例。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 想在 UE 模块开 `/openmp` | installed engine 拒编 / 无 per-module 旋钮 | 用 IntelTBB 或 ParallelFor |
| 见 FAISS 有 omp.h 以为 UE 支持 OpenMP | 那是 stub 成串行,不是真并行 | 同上 |
| per-call `std::thread` spawn 逐帧并行 | spawn 开销 >> 收益,慢一个量级 | 池化(TBB/task system) |
| 共享 core 硬 `#include <tbb/*>` 无门控 | 非 UE host(Maya)编不了 | `#if CA_USE_TBB` 门控 + 串行 fallback |
| OpenMP 默认按核数开(不 cap) | vcomp busy-spin 过度订阅,比串行慢 | host 设 `OMP_NUM_THREADS` / cap 线程 |
| 并行有 scatter-add 的段不管写竞争 | 数据竞争 + 破坏 bit-identical | 该段串行,或 per-thread 桶合并 |

## 项目实例参考

UE 5.8 curvenet 形变插件 + 配套 Maya 插件(共享 `ca_core` 求解 core):per-frame solve 的稀疏×稠密乘 +
per-halfedge 循环内部并行。

- **UE=TBB**:`IntelTBB` per-module 依赖,每帧 40→29.5ms;OpenMP 试过——installed engine(OF_UE_58)
  target 级 `/openmp` 直接拒编,坐实规则 1。
- **naive `std::thread`** 版(每帧 ~6 段各 spawn ~15 线程)实测慢一个量级 → 回退换池化(spawn 主导的完整数字 + 通用机制见 `guidelines/cpp/hot-path-cpp.md` 项目实例)。
- **Maya=OpenMP**(方案:只在 Maya CMake 给 core lib 加 `CA_USE_OMP` + 链 OpenMP,core 一行没改):
  每帧 42→34.7ms(OMP=8);OMP 默认 36 核 0.88×(过度订阅),cap 到 8 才 1.22×。TBB 默认 36 线程开箱 ~1.19×。
- **行分块并行 bit-identical**:serial / OMP / TBB / 任意线程数,输出 `max|Δ|=0.000e+00`(唯一 scatter-add 的
  fsum 段保持串行)——parity 门对纯 CPU 后端可按 0 卡(叠 GPU 后端如 cuDSS 才有 ~1e-11 求和顺序差)。

## 相关 Guidelines

- `guidelines/cpp/hot-path-cpp.md` —— per-call `std::thread` spawn 慢(规则 2 的通用面)。
- `guidelines/ue/ue58-upgrade-gotchas.md` —— installed engine 的 Target 属性一致性约束(拒
  `/openmp` 同源);那条管 5.8 升级,本条管并行后端。
- [`gpu-numerical-lib-consumption.md`](gpu-numerical-lib-consumption.md) —— 同项目另一条:UE 没有官方 GPU
  数值求解器、bring-your-own 运行时库的消费 pattern。
- skill `ue-reference-engine-source` —— FAISS omp_stub / IntelTBB.Build.cs / UBT ModuleRules 都是读 engine
  source 确认的;UE doc 没写这些。
