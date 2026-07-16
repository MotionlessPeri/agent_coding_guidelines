# 按项目 C++ 标准选用现代特性（别写比目标标准更旧的方言）

写 C++ 时，用**项目配置的语言标准**（C++17/20/23…）所提供的现代特性——不要停在比目标标准更旧的写法。
但有两条 counterweight 必须一起守，否则"用新特性"会翻车：

1. **「配置写 C++20」≠「C++20 真的在生效」**——SDK / 框架 / DevKit 会**钳制**标准，CI toolchain 又可能跟本地不同。
2. **别为"现代化"去 churn 已有旧代码**——新代码 + 已经 touch 到的地方用现代形式即可（edit-scope）。

跨框架通用。任何有明确 `CMAKE_CXX_STANDARD` / `-std=` 的 C++ 项目都适用。

## 核心规则

1. **用目标标准的特性**：C++20 项目里 `std::sort(v.begin(), v.end())` 是旧方言，应 `std::ranges::sort(v)`；
   手写下标循环能用 ranges / 算法就别手写；`NULL`→`nullptr`、`typedef`→`using`、裸 `new/delete`→智能指针，等等。
2. **先确认标准真在生效，不假设**：读 build 配置（CMake `set(CMAKE_CXX_STANDARD 20)` / `target_compile_options(.. /std:c++20)`），
   并确认没被 SDK 钳制（见下）。
3. **scope discipline**（[`../code/constraints.md`](../code/constraints.md) "Edit Scope Discipline"）：现代特性进**新代码**
   + **你正在改的那处**；**不 drive-by** 把一片能跑的旧代码翻新纯为风格——那会 inflate diff、混淆 review。
4. **可读性优先**：现代 ≠ 晦涩。ranges / concepts 用在能**变清楚**的地方；别为炫技压成看不懂的一行（见
   [`../code/function-clarity.md`](../code/function-clarity.md)）。

## 「配置 C++20」≠「C++20 生效」——两个真实的坑

- **SDK / 框架钳制标准**：如 Maya DevKit 的 `devkit.cmake` 在未设 `MAYA_WANT_CPP_17` 时把 `CMAKE_CXX_STANDARD`
  **强制回 14**——顶层设了 `CMAKE_CXX_STANDARD 20` 也被盖掉。必须 **target 级**显式 `set_target_properties(t PROPERTIES CXX_STANDARD 20)`
  + MSVC 再补 `/std:c++20`（取最后一个 `/std:` 生效）才真的是 C++20。所以「项目意图 C++20」要靠**显式覆盖 + 验证生效**
  （grep 有效 flag / 看编译行 / 试编一个 C++20-only 语法），不能想当然。
- **本地 vs CI toolchain 版本差异**：标准 **LEVEL**（C++20）和 toolchain **VERSION** 是两回事。一个特性要同时满足
  (a) 标准开启 + (b) 编译器 / STL 版本够新才可用。本地旧 toolchain 编过 ≠ CI 新 toolchain 编过（反向也成立：新 STL
  收紧 API 让旧写法 FAIL，见 [`make-format-args-lvalue.md`](make-format-args-lvalue.md)）。

→ **用一个新特性前**：确认 (1) 标准在目标 target 上真生效 (2) 目标 toolchain（尤其 **CI**）支持它。

## 特性对照（按标准，常见替代）

| 标准 | 现代特性（替代的旧写法） |
|---|---|
| C++17 | 结构化绑定；`if constexpr`；`std::optional` / `variant` / `string_view`；`[[nodiscard]]`；fold expression；inline 变量 |
| C++20 | ranges（`std::ranges::sort(v)` 替 `sort(v.begin(),v.end())`；views 替手写过滤/变换循环）；`std::span`；concepts 替 SFINAE；designated initializer；`<=>`；`std::format`（**注意左值契约**，见 [`make-format-args-lvalue.md`](make-format-args-lvalue.md)） |
| C++23 | `std::print`；`std::expected`；`std::mdspan`；`std::ranges::to`（视 toolchain 支持度，尤其 CI）|

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| C++20 项目写 `std::sort(v.begin(), v.end())` / 手写下标循环 | 停在旧方言，读者以为不是新标准项目 | `std::ranges::sort(v)` / ranges 算法 |
| 假设标准生效、不验证（SDK 钳制） | 「以为 C++20」实际 C++14 编译 → 新特性编不过、或静默降级 | grep 有效 `/std:` / `CXX_STANDARD`；target 级覆盖 |
| 为现代化 drive-by churn 一大片旧代码 | diff 膨胀、混淆 review（哪行是语义改哪行是翻新） | 只在新代码 + 顺手处用；旧代码不动 |
| 用 CI toolchain 不支持的特性（本地绿、CI 红） | 发版链断在 CI build | 确认目标 toolchain 版本（见 make-format-args-lvalue）|
| 现代化成晦涩一行 | 可读性倒退 | 可读性优先，现代化服务清晰 |

## 怎么查项目当前标准

读 build 配置：CMake `CMAKE_CXX_STANDARD` / `target_compile_options(.. /std:c++NN | -std=c++NN)`；确认目标 target
没被 SDK/框架钳制（必要时 target 级覆盖）。拿不准就试编一段目标标准独有的语法验证。

## 项目实例参考

Maya C++ 插件（curve_articulation_maya）是 C++20——`maya/CMakeLists.txt` 用 target 级 `CXX_STANDARD 20` +
`/std:c++20` **显式盖过 Maya DevKit 的 C++14 钳制**（DevKit 的 `devkit.cmake` 未设 `MAYA_WANT_CPP_17` 时把
`CMAKE_CXX_STANDARD` 强制回 14）。即便如此，deformer 的 `buildWeightCSR` 仍写着 `std::sort(row.begin(), row.end())`——
C++20 下应 `std::ranges::sort(row)`。review 中被发现，提醒：**新标准项目要真的用上新特性，而不是配置写了 C++20、代码却停在旧方言**。

## 相关 Guidelines

- [`make-format-args-lvalue.md`](make-format-args-lvalue.md) — 标准 / STL 版本间 API 契约收紧（本地旧 toolset 编过、CI 新 toolset FAIL）；本条「验证目标 toolchain 支持」与之同源
- [`build-incremental-and-cmake.md`](build-incremental-and-cmake.md) — toolchain / 构建差异族
- [`../code/constraints.md`](../code/constraints.md) "Edit Scope Discipline" — 别 drive-by 现代化 churn
- [`../code/function-clarity.md`](../code/function-clarity.md) — 可读性优先，现代化不等于晦涩
