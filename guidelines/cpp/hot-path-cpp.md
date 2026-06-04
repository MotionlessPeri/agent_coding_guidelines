# C++ 热路径：大对象传递 + dynamic_cast

两个"看着没问题、实际在性能关键路径上拖慢"的 C++ 坑。重构改 API 签名时尤其容易引入。

## 核心规则

1. **MB 级大对象（逐帧/逐元素数据结构）在热路径上传递必须用 move 语义，别随手把 `&&`/`std::move` 改成 `const&` + 拷贝**
2. **逐帧循环里别反复 `dynamic_cast`（如每帧 `getExtensionAs<T>()`）→ 循环外缓存指针/引用**

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

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 重构把 `&&`/`std::move` 改 `const&`+拷贝 | 热路径深拷贝回退 | 拿所有权用 `&&`，只读用 `const&` |
| 凭直觉判断"哪里慢" | 改错地方 | profiler 看 `memcpy` 调用栈 |
| 逐帧循环里 `dynamic_cast` | 累积可测开销 | 循环外缓存指针/引用 |
| 扩展 API 鼓励处处 `getExtensionAs<>` | 调用方在热路径反复 RTTI | 提供 `requireX()` 取一次返回引用 |

## 项目实例参考

某 Maya 角色动画插帧插件（逐帧骨骼数据）：
- `CharacterSnapshot`（逐帧逐骨骼，MB 级）的传递从 `&&` 误改 `const&` 导致拖拽路径明显变慢；profiler 确认 `memcpy` 后改回 move 语义
- type-keyed 扩展容器 `getExtensionAs<T>()` 在逐帧循环里反复调，profiler 见 `dynamic_cast` 开销；改为循环外 `requireBezierExtra()` 取一次引用

## 相关 Guidelines

- [`../../skills/architecture/multi-plugin-shared-core/SKILL.md`](../../skills/architecture/multi-plugin-shared-core/SKILL.md) — type-keyed 扩展容器的设计（`requireX()` 缓存接口在此展开）
- [`../code/validation.md`](../code/validation.md) — 性能结论要 profiler 证据，不靠推断
