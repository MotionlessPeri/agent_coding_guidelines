# C++ / 工程底座 Guidelines 索引

C++ / Windows DLL / cmake / MSVC 工程底座的 hidden contract——文档没明说、靠踩坑得到的
客观约束。**框架无关**：多 DLL 插件（含 UE `.dll` / Maya `.mll`）、任何 cmake + MSVC 项目
高频命中。

**非 C++ 项目可整段 skip 本目录。** 通用工程组织 / 验证规则在 `guidelines/code/` /
`guidelines/workflow/`。

## 按子领域分类

### 多 DLL / 符号导出 / 绑定可达面

| Guideline | 解决的问题 |
|---|---|
| [`multi-dll-plugin.md`](multi-dll-plugin.md) | 跨 DLL 共享单例 `getInstance()` 必须非内联在 `.cpp`（内联的 static 局部各 DLL 一份、状态隔离）/ `WINDOWS_EXPORT_ALL_SYMBOLS` 是偷懒方案、LNK4197 抑制前先确认不是真 ABI 问题 / DLL 加载顺序决定全局 init 顺序（base init 必须在 base 自己入口最早跑）+ 两阶段初始化 |
| [`native-binding-surface.md`](native-binding-surface.md) | 给 C++ 库做语言绑定（pybind / nanobind / SWIG / FFI）：消费方能调的 = 绑定模块**显式导出**的那一小面，不是 lib 里实现了什么；以运行期 introspect 产物为准（不读源码猜）；暴露一个功能 = 源进 lib + 显式绑定 + 重建三步；源提进 lib 后 test target 只链 lib 别再直接编（否则重复符号） |

### 构建系统 / 工具链版本差异

| Guideline | 解决的问题 |
|---|---|
| [`build-incremental-and-cmake.md`](build-incremental-and-cmake.md) | 改跨 DLL 公共头后增量编译漏重编 → ABI 布局不一致崩（容器/虚函数），`--clean-first` 全量重编;`git mv` / 改 CMakeLists 目录树后 VS IDE 用 stale `.vcxproj`（命令行能编、IDE 报 `cmake_pch.cxx not found`）→ 删**整个** build 目录重 cmake |
| [`make-format-args-lvalue.md`](make-format-args-lvalue.md) | 新版 MSVC STL（VS 2022 17.10+ / toolset 14.40+）的 `std::make_format_args` 只接受左值，`std::forward<Args>(args)...` 触发 `C2664`/`C2672`——传具名形参 `args...` 即可;**本地旧工具链编过、CI 新工具链 FAIL** 的高迷惑构建 bug |
| [`modern-cpp-by-standard.md`](modern-cpp-by-standard.md) | 用项目配置的标准（C++17/20/23）的现代特性，别停在更旧方言;但「配置写 C++20」≠「C++20 生效」——SDK/DevKit 钳制标准 + 本地 vs CI toolchain 版本差异都要确认;别为现代化 drive-by churn 旧代码（edit-scope） |
| [`cmake-multi-subdir-pitfalls.md`](cmake-multi-subdir-pitfalls.md) | 多子目录 CMake 三个顺序/作用域坑:子目录 `set` 的变量父作用域求值为空（显式传值、别依赖渗透）;`if(TARGET x)` 依 `add_subdirectory` 顺序为假（改用 `target_link_libraries` forward-reference）;可复用库测试 target 要 `PROJECT_IS_TOP_LEVEL`/`option` 门控别拖累消费方 |
| [`d3d12-agility-sdk-runtime-match.md`](d3d12-agility-sdk-runtime-match.md) | 链用新 D3D12 特性（enhanced barriers / DXR 新 flag）的框架（NVRHI/Donut/自研 RHI）:**编译期 Agility 特性版本必须匹配运行时 `D3D12Core`**——系统自带旧 runtime 不支持 → 一串「神秘」hang/segfault（`CreateCommittedResource3` 返 E_INVALIDARG → null 解引用）;修 = vendor + 显式部署 Agility SDK runtime;一根因多表象、别当多问题 |

### 热路径 / 性能测量

| Guideline | 解决的问题 |
|---|---|
| [`hot-path-cpp.md`](hot-path-cpp.md) | MB 级大对象在热路径传递用 move 别退回 `const&`+拷贝;逐帧循环别反复 `dynamic_cast`（循环外缓存指针）;逐帧并行别 per-call `std::thread` spawn（spawn 开销吊打收益、慢一个量级）用持久池;性能回退靠 profiler 不靠猜 |
| [`perf-measure-optimized-binary.md`](perf-measure-optimized-binary.md) | perf 必须在优化版（`/O2`）二进制上测、并先确认加载/跑的确实是它（`/Od` 下热循环慢 5–10×、结论全错）;「关优化」开关粘在 cmake cache;启动打印本模块全路径确认加载的是哪份;区分 core-lib（恒 `/O2`）vs 集成层计时 |

### Windows native 崩溃 / 卡死取证

| Guideline | 解决的问题 |
|---|---|
| [`windows-native-crash-hang-evidence.md`](windows-native-crash-hang-evidence.md) | 先分类（crash / hang / 主动退出 / 超时终止 / licensing 启动失败）再归因，不凭「窗口消失」断言崩溃;hang 先 Break All 抓全线程栈再 kill;默认 normal dump、按需升 full-heap;WinDbg 最小分析集 + 无 PDB 时 `module base + RVA` 映射 Ghidra;race/refcount 结论至少两类证据 |

## 相关目录

- **UE 项目**：UE 模块内并行（IntelTBB / OpenMP 装不了）+ GPU 数值库消费等框架相关面，见 UE 的 procedural-numerical skill（`skills/ue/ue-procedural-numerical/`）；UE hidden contracts 总索引 [`../ue/INDEX.md`](../ue/INDEX.md)
- **Maya 项目**：Maya `.mll` 是典型多 DLL + DevKit cmake 场景，上列底座坑高频命中；Maya 特有的 DevKit C++ 标准钳制 / `.mll` 覆盖 / 脚本契约见 [`../maya/plugin-build-and-scripting-contracts.md`](../maya/plugin-build-and-scripting-contracts.md)，Maya 总索引 [`../maya/INDEX.md`](../maya/INDEX.md)
- **验证纪律**：构建 / perf / 崩溃类结论都要实测证据（不靠「看代码对」），见 [`../code/validation.md`](../code/validation.md) / [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md)
