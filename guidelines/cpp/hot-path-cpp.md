# C++ 热路径：大对象传递 + dynamic_cast

两个"看着没问题、实际在性能关键路径上拖慢"的 C++ 坑。重构改 API 签名时尤其容易引入。

## 核心规则

1. **MB 级大对象（逐帧/逐元素数据结构）在热路径上传递必须用 move 语义，别随手把 `&&`/`std::move` 改成 `const&` + 拷贝**
2. **逐帧循环里别反复 `dynamic_cast`（如每帧 `getExtensionAs<T>()`）→ 循环外缓存指针/引用**
3. **逐帧/热路径的并行别用 per-call `std::thread` spawn**——每次调用新建 + `join` 线程，spawn 开销吊打收益（实测比串行慢一个量级）；用**持久线程池**（TBB / OpenMP runtime / 框架 task system）

---

## 1. 大对象传递的 move vs copy

包含大量逐帧逐元素数据的结构（数百个 vector / MB 级），**拷贝代价极高**。重构/改签名时一个
常见回退：

```cpp
// 原本：调用方 std::move 进来，零拷贝
void process(BigSnapshot&& snap);
caller: process(std::move(snap));

// ❌ 重构时"顺手"改成 const& —— 看着安全，但若实现里要保留一份就触发深拷贝；
//    或调用方原本 move 的语义被破坏
void process(const BigSnapshot& snap);   // 实现内 auto copy = snap; → 深拷贝回退
```

原则：
- 热路径大对象**必须拿到所有权**的地方用右值引用 `&&` + `std::move`，明确表意零拷贝
- 只读不留存用 `const&`
- 改 API 签名前确认调用方原本的传递语义，别无意中把 move 变 copy

**性能回退别靠猜**：怀疑时用 CPU profiler（VTune / perf）确认 `memcpy` 调用栈，而不是读代码推断。

## 2. 热路径上的 dynamic_cast

type-keyed 扩展容器（`getExtensionAs<T>()` 这类）内部通常一次 `dynamic_cast` + null 检查。
单次便宜，但**放进逐帧/逐元素循环反复调**就成了 profiler 里"不起眼但频繁"的耗时项。

```cpp
// ❌ 循环内每次 dynamic_cast
for (auto& frame : frames) {
    auto* ext = obj->getExtensionAs<FooExtra>("foo");  // 每帧一次 RTTI
    ext->doStuff(frame);
}

// ✅ 循环外缓存一次
auto* ext = obj->getExtensionAs<FooExtra>("foo");
for (auto& frame : frames) ext->doStuff(frame);
```

设计扩展 API 时就该**引导调用方缓存**：提供 `requireFoo() -> FooExtra&`（取一次）而非鼓励处处
走 `getExtensionAs<>`；或在性能敏感的内部实现里直接接收已解析的指针/引用参数，不重复查询。

---

## 3. 逐帧并行：用持久池，别 per-call spawn `std::thread`

给逐帧热路径（逐元素循环 / 稀疏矩阵乘）加并行时，**别每次调用都新建 `std::thread` + `join`**：

```cpp
// ❌ 每帧调用都 spawn N 个线程 —— 线程创建是 OS 级重操作（Windows 上每线程 ~百 µs + ~1MB 栈）
void parFor(int n, Fn fn) {
    std::vector<std::thread> pool;
    for (int t=0;t<nThreads;++t) pool.emplace_back([&]{ /* 处理一段 */ });
    for (auto& th:pool) th.join();
}
// 每帧调 ~几段 × 每段 ~十几线程 = 每帧上百次线程创建 → 实测比串行慢一个量级
```

逐帧热路径里单次并行段的工作量（几 ms）**远小于** spawn N 个 OS 线程的代价。**用持久线程池**（创建一次、
复用）：`tbb::parallel_for` / OpenMP runtime（`#pragma omp parallel for`，池化）/ 框架自带 task system
（如 UE `ParallelFor`）——它们摊薄 spawn，重复调用近乎零开销。

性能回退别靠猜：怀疑「并行反而更慢」时先 profiler 看是不是 spawn 主导（对比串行 vs 并行的单段耗时），
别加了并行看没提速就以为「并行没用」——很可能是没用池。

框架相关的后端选择（UE 里 OpenMP 装不了、用 IntelTBB；跨框架共享库做后端无关抽象）见
[`../ue/ue-module-parallelism.md`](../ue/ue-module-parallelism.md)。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 重构把 `&&`/`std::move` 改 `const&`+拷贝 | 热路径深拷贝回退 | 拿所有权用 `&&`，只读用 `const&` |
| 凭直觉判断"哪里慢" | 改错地方 | profiler 看 `memcpy` 调用栈 |
| 逐帧循环里 `dynamic_cast` | 累积可测开销 | 循环外缓存指针/引用 |
| 扩展 API 鼓励处处 `getExtensionAs<>` | 调用方在热路径反复 RTTI | 提供 `requireX()` 取一次返回引用 |
| 逐帧并行 per-call `std::thread` spawn | 线程创建开销吊打收益，慢一个量级 | 持久线程池（TBB/OpenMP/task system） |
| 加了并行没提速就以为并行没用 | 可能是 spawn 主导，不是并行没用 | profiler 对比单段耗时，换池化 |

## 项目实例参考

某 Maya 角色动画插帧插件（逐帧骨骼数据）：
- `CharacterSnapshot`（逐帧逐骨骼，MB 级）的传递从 `&&` 误改 `const&` 导致拖拽路径明显变慢；profiler 确认 `memcpy` 后改回 move 语义
- type-keyed 扩展容器 `getExtensionAs<T>()` 在逐帧循环里反复调，profiler 见 `dynamic_cast` 开销；改为循环外 `requireBezierExtra()` 取一次引用

UE 5.8 curvenet 形变插件（逐帧 solve 的稀疏×稠密乘并行）：初版用 per-call `std::thread` spawn（每帧 ~6 段 × 每段 ~15 线程），每帧 40ms → **423ms（慢 10×）**，单段光 spawn ~73ms；换持久池（UE 用 TBB / Maya 用 OpenMP，见 `../ue/ue-module-parallelism.md`）后每帧 40→~30ms。

## 相关 Guidelines

- [`../../skills/architecture/multi-plugin-shared-core/SKILL.md`](../../skills/architecture/multi-plugin-shared-core/SKILL.md) — type-keyed 扩展容器的设计（`requireX()` 缓存接口在此展开）
- [`../code/validation.md`](../code/validation.md) — 性能结论要 profiler 证据，不靠推断
- [`../ue/ue-module-parallelism.md`](../ue/ue-module-parallelism.md) — 规则 3 的框架相关面（UE 用 IntelTBB、OpenMP 装不了；跨框架共享库的后端无关抽象 + 行分块 bit-identical）
