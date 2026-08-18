# C++ 增量编译 ABI 陷阱 + CMake/VS 重构后 stale 缓存 + 工具集混链

三个"改了代码 / 装了依赖，但构建系统没跟上"导致的坑，都在 C++ + MSBuild/MSVC + CMake + Visual Studio
组合下高频。一个是增量编译漏重编导致 ABI 不一致崩溃，一个是 cmake 目录重构后 IDE 用 stale
工程文件编译失败，一个是依赖与消费方用了不同的 MSVC 工具集导致缺 STL 内部符号。

## 核心规则

1. **改了跨 DLL / 跨多 TU 共享的公共头（尤其加成员、改布局）后，执行全量重编，不要信增量编译**
2. **`git mv` / 改 CMakeLists 目录结构后，删除整个 build 目录重新 cmake，不要原地 reconfigure**
3. **依赖和消费方必须钉同一个 MSVC 工具集**——VS 的默认工具集版本文件会把你钉回一个旧版本

---

## 1. 增量编译漏重编 → ABI 布局不一致

**现象**：给一个被多处 include 的公共头（典型：跨 DLL 共享的全局单例头）加了成员后，
MSBuild 增量编译可能只重编"改过的 `.cpp`"，**漏掉依赖该头但本身没改的 `.cpp`**。结果：
部分 TU 用新的内存布局、部分用旧的，运行时成员 offset 不一致。

**典型崩溃信号**：
- 容器操作诡异崩溃（`unordered_map::count` / `size()` 返回垃圾值）
- 虚函数调用地址错乱
- 崩溃栈停在容器/STL 内部函数

**修法**：改公共头后全量重编。
```bash
cmake --build <build-dir> --config Release --clean-first
```
或在 CI 关键步骤禁用增量编译。**大量 `git mv` 文件后**报 unresolved external symbol / 链接错误
（即使内容没改）通常同根因，`--clean-first` 一次解决。

## 2. CMake 目录重构 → VS IDE 用 stale .vcxproj

**现象**：`git mv` 改了源文件目录 / 改了 CMakeLists 的目录树后：
- `cmake --build` 命令行**能成功**（它会自动 reconfigure）
- 但 **VS IDE 打开报错**：`cmake_pch.cxx not found` / `pch.h not found` 等找不到文件
- 即使删 `.sln` 重新生成仍报错

**原因**：VS 的 `.vcxproj` 里硬编码了源文件/中间产物路径（如 `CMakeFiles/<target>.dir/cmake_pch.cxx`）。
`cmake` reconfigure **不会删除旧的 `.vcxproj`**，stale 文件持续指向旧路径，VS IDE 用的就是它。

**修法**：删除**整个** build 目录，重新生成。
```bash
rm -rf <build-dir>
cmake -S <src> -B <build-dir> -G "Visual Studio 17 2022"
# 再用 VS 打开 + clean rebuild
```
只删 `.sln`、只 reconfigure、IDE 里 rebuild all 都**不够**——必须删整个 build 目录。

**触发场景**：任何 `git mv` 文件 / 改 CMakeLists 目录结构的重构之后。Ninja / Make 生成器通常没这个问题（不生成 `.vcxproj`），主要是 VS 生成器特有。

## 3. 依赖与消费方工具集不一致 → 缺 STL 内部符号（LNK2001）

**现象**：包管理器（vcpkg 等）装好的依赖链接不上，报一串**看起来不像你的代码**的未定义符号：

```
LNK2001: unresolved external symbol __std_find_last_trivial_1
LNK2001: unresolved external symbol __std_search_1
LNK2001: unresolved external symbol __std_min_8i
```

`__std_*` 前缀是 MSVC STL 的**向量化算法内部实现符号**，住在**某个具体工具集版本**的 lib 里。

**根因**：同一次构建里混了两个工具集。典型链条——包管理器用它自己探到的最新工具集（如 14.44）编依赖，
而你的工程走 VS 的默认解析：`Microsoft.VCToolsVersion.v143.default.txt` 把 `v143` 解析成一个**较旧的**
具体版本（实测 14.34）。新 STL 引入的那些 `__std_*` 实现只在新工具集的 lib 里，旧工具集链不到。

**修法**：在工程侧显式钉死具体版本 —— `Directory.Build.props`：

```xml
<Project>
  <PropertyGroup>
    <VCToolsVersion>14.44.35207</VCToolsVersion>
  </PropertyGroup>
</Project>
```

⚠️ **CMakePresets 的 `toolset` 字段吃不下版本号**（实测 CMake 3.27 拒 `version=14.44` 和
`version=14.44.35207` 两种写法）。这一层要在 **MSBuild** 解决，不是在 CMake 解决。

**验证**：构建日志里搜工具集路径，确认**只出现你钉的那一个版本**（`...\MSVC\14.44.35207\...`）。
两个版本同时出现就是还没钉住。

> **跟同族条目的区别**：[`make-format-args-lvalue.md`](make-format-args-lvalue.md) /
> [`modern-cpp-by-standard.md`](modern-cpp-by-standard.md) 管的是"**跨机**版本差异 + 新 STL 收紧 API 契约"
> （本地旧 toolset 编过、CI 新 toolset 编不过）。本条是**同一台机、同一次构建内部**两个工具集混链，
> 失败面是缺 STL 内部符号、修法在 MSBuild 层。三者同属"标准 LEVEL vs toolchain VERSION"家族。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 改公共头后只增量编译 | ABI 不一致 → 容器/虚函数崩溃 | `--clean-first` 全量重编 |
| 把容器崩溃当"代码 bug"反复查逻辑 | 浪费时间，根因是构建 | 先怀疑增量编译，全量重编排除 |
| 目录重构后只 reconfigure | VS IDE stale .vcxproj 报错 | 删整个 build 目录重新 cmake |
| 只删 .sln 想修 stale | 不够，.vcxproj 还在 | 删整个 build 目录 |
| 撞 `__std_*` 未定义符号去查自己的代码 / 依赖装没装全 | 查错方向，根因是工具集版本 | 比对依赖与工程各用哪个工具集 |
| 想在 CMakePresets 的 `toolset` 里写版本号 | CMake 直接拒（实测 3.27 两种写法都不认） | 用 `Directory.Build.props` 的 `VCToolsVersion` |
| 钉完不验证 | 可能仍在混链 | 构建日志里确认只出现钉的那个版本 |

## 项目实例参考

某 Maya C++ 多 `.mll` 插件项目重构期间：
- 给共享单例头 `RDMayaBaseGlobal.h` 加成员后，MSBuild 增量编译漏了对应 `.cpp`，运行时崩在 `unordered_map::count`、调试器显示 map size 是垃圾值；`--clean-first` 全量重编后正常
- `git mv` 大批文件做目录重构后，VS IDE 报 `cmake_pch.cxx not found`，删 `.sln` 重生成无效；删整个 `build_vs_2022/` 目录重新 `cmake -S -B` 后修复

某 MotionBuilder C++ 设备插件（vcpkg manifest mode + CMake + MSVC）首次配依赖时踩穿第 3 条：vcpkg 用
14.44 编 gRPC/protobuf，插件走 VS 默认解析拿到 14.34，link 报三个 `__std_*` 未定义。**先试错了两次**
——`CMakePresets.json` 里写 `"toolset": "version=14.44"` 和 `"version=14.44.35207"`，CMake 3.27 两种都拒；
最后靠 `Directory.Build.props` 的 `<VCToolsVersion>` 钉住，并在构建日志里确认只出现 `MSVC\14.44.35207`。

## 相关 Guidelines

- [`multi-dll-plugin.md`](multi-dll-plugin.md) — 跨 DLL 共享头/单例的导出契约（与本篇配套，公共头改动同时触发两类问题）
- [`make-format-args-lvalue.md`](make-format-args-lvalue.md) / [`modern-cpp-by-standard.md`](modern-cpp-by-standard.md) — 同族的**跨机**工具集差异（本地旧 toolset 编过、CI 新 toolset FAIL）；本篇第 3 条是同一次构建**内部**混链
- [`../code/validation.md`](../code/validation.md) — "看代码对" ≠ 验证；构建类崩溃必须全量重编后实测。另：**别在读之前过滤构建输出**——本篇三条的诊断全靠读完整日志
