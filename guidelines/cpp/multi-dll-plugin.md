# 多 DLL C++ 插件：单例 / 符号导出 / 初始化顺序

一个由多个 DLL（Windows `.dll` / Maya `.mll` / 任意 host plugin）组成、其中一个是"共享
base 层"被其他 DLL 依赖的 C++ 系统，有三组反复踩的坑。框架无关——只要是"多 DLL 共享 C++
状态"就适用。

## 核心规则

1. **跨 DLL 共享的单例 `getInstance()` 实现必须在 .cpp（非内联），不能内联在头文件**
2. **`WINDOWS_EXPORT_ALL_SYMBOLS` 是偷懒方案；LNK4197 抑制前先确认不是真 ABI 问题**
3. **DLL 加载顺序决定全局初始化顺序：base 层的 init 必须在 base 自己的入口最早跑**

---

## 1. 跨 DLL 单例的内联陷阱

```cpp
// ❌ 内联在头文件 —— 每个 include 该头的 DLL 各自编译出一份 static instance
// （存在各自数据段），WINDOWS_EXPORT_ALL_SYMBOLS 对内联函数的静态局部变量无效
// → 多个 DLL 看到不同的"单例"，状态完全隔离
struct EXPORT Global {
    static Global& instance() { static Global g; return g; }  // ⚠️ 内联
};

// ✅ 头文件只声明，.cpp 非内联实现 —— 非内联函数被自动导出，
// 所有 DLL 通过导入表调用同一份函数 → 真正全局唯一
// Global.h
struct EXPORT Global { static Global& instance(); };
// Global.cpp
Global& Global::instance() { static Global g; return g; }
```

**机制**：`__declspec(dllexport)` / `WINDOWS_EXPORT_ALL_SYMBOLS` 导出的是**函数符号**，
但**内联函数的静态局部变量不被导出**——这是 PE/COFF 链接器约定，跟 DLL 导出机制正交。
内联函数会在每个 TU 各自实例化，其 `static` 局部各一份。

**症状**：调试器里两个 DLL 看到同一单例的容器 `size()` 不同 / 一个 DLL 注册的东西另一个查不到。

## 2. 符号导出的一致性

`WINDOWS_EXPORT_ALL_SYMBOLS TRUE`（CMake）对新项目方便，但大型重构后容易漏导出某些符号
（尤其内联函数静态变量，见第 1 条）。

**LNK4197（重复导出）**：常来自第三方库（如 Torch 的 c10）的模板 vtable 在多个 `.cpp`
各自实例化。**多数无害**，可 `/ignore:4197` 抑制——**但抑制前先确认**它不是指向真的 ABI 问题
（模板多处实例化 / 库版本冲突 / 导出列表冲突）。理想是修根因（显式模板实例化 / 链接顺序 / 精确
导出列表），确认无害再 suppress。长期 suppress 列表在 major 升级时复查一次。

诊断实际导出：`dumpbin /exports your.dll`。

## 3. 加载顺序决定初始化顺序

多 DLL 系统里，host 按某个顺序（host 配置文件 / 用户脚本指定）依次调各 DLL 的入口。
**base 层的全局 init 必须在 base 自己的入口里最早跑**，不能延迟到某个 feature DLL 的入口：

```
// ❌ base init 写在某 feature DLL 的入口
FeatureA::startup() { BaseGlobal::instance().init(); }
// 如果 FeatureB 先于 FeatureA 加载，FeatureB 启动时 base 还没 init，
// 读到空配置 → 静默失败（如某个路径列表为空，for 循环不执行）

// ✅ base init 写在 base 自己的入口
Base::startup() { BaseGlobal::instance().init(); }   // base 必须最先加载
FeatureA::startup() { /* 此时 base 已 ready */ }
```

**两阶段初始化**：base 无法预知 feature 会注册什么 → (1) base init 设基础框架 + 共用数据；
(2) 各 feature init 注册自己的东西；(3) 若 feature A 依赖 feature B 已注册的东西，用 host 的
"插件是否已加载"查询（如 Maya `pluginInfo -q -loaded`）做先决检查，否则返回 warning。
关键操作前可提供一个"初始化完成"检查函数让脚本调用。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| `getInstance()` 内联在头 | 每个 DLL 一份单例，状态隔离 | 实现移 .cpp（非内联） |
| 靠 `WINDOWS_EXPORT_ALL_SYMBOLS` 不管导出细节 | 漏导出 / 内联静态不共享 | 关键符号确认导出，必要时 .def |
| 盲目 `/ignore:4197` | 可能掩盖真 ABI 问题 | 抑制前确认无害 |
| base init 延迟到 feature DLL | 加载顺序一变就空配置 | base init 在 base 入口最早跑 |

## 项目实例参考

某 Maya C++ 插件套件（多 `.mll`：一个 `RDMayaBase` 共享层 + 三个功能插件）：
- 共享单例 `getInstance()` 内联在头 → 两个插件看到各自的 registry（`instances_` size 不同），调试器显示数据段是各自的；实现移到 `.cpp` 后修复（仅跨 DLL 单例需要，纯插件内单例不跨 DLL 无需改）
- base 的 `init()` 原写在某功能插件入口，另一功能插件先加载时读到空的模型路径列表，运行时报 "model not loaded"；移到 base 自己的 `initializePlugin` 后修复
- Torch 头导致 LNK4197，确认是 c10 vtable 多处实例化、无害，`/ignore:4197` 抑制

## 相关 Guidelines

- [`build-incremental-and-cmake.md`](build-incremental-and-cmake.md) — 改跨 DLL 公共头后的增量编译 ABI 陷阱（配套）
- [`../../skills/architecture/multi-plugin-shared-core/SKILL.md`](../../skills/architecture/multi-plugin-shared-core/SKILL.md) — 多插件共享 core 的架构（非拥有 Registry / 两阶段初始化在此展开）
