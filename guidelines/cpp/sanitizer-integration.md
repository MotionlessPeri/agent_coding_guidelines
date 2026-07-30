# Sanitizer 集成：CMake 配置、运行时选项与组合规则

## 核心规则

Sanitizer 是 C++ 项目**性价比最高的运行时检查**——编译器插桩，自动捕获内存错误和未定义行为。但每个 sanitizer 有自己的隐藏契约，配置错了会假阳性泛滥或静默不工作。

本文件覆盖：ASan / UBSan / TSan / MSan 的 CMake 集成方式、组合规则、运行时选项和平台限制。

---

## 一、Sanitizer 速查表

| Sanitizer | Flag | 检测内容 | 性能开销 | 平台 | 组合兼容性 |
|-----------|------|---------|---------|------|-----------|
| **ASan** | `-fsanitize=address` | use-after-free、buffer overflow、double-free、memory leak | ~2x 慢，~2x 内存 | Linux / macOS / Windows（Clang+MSVC） | 与 UBSan ✅，与 TSan ❌，与 MSan ❌ |
| **UBSan** | `-fsanitize=undefined` | 整数溢出、越界移位、空指针解引用、未对齐访问 | ~1.1x 慢，忽略不计 | Linux / macOS / Windows（Clang） | 与 ASan/TSan/MSan ✅ |
| **TSan** | `-fsanitize=thread` | 数据竞争、锁顺序违规 | ~5-15x 慢，~5x 内存 | Linux（Clang），macOS 部分 | 仅与 UBSan ✅ |
| **MSan** | `-fsanitize=memory` | 未初始化内存读取 | ~2-3x 慢，~2x 内存 | Linux only（Clang） | 仅与 UBSan ✅ |

---

## 二、CMake 集成模式

### 推荐方式：CMake Option + 条件编译

```cmake
# 在 CMakeLists.txt 中定义 option
option(PROJECT_ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(PROJECT_ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)
option(PROJECT_ENABLE_TSAN "Enable ThreadSanitizer" OFF)

# 在库/目标级别添加（不要全局 set，避免影响第三方依赖）
function(target_enable_sanitizers TARGET)
    set(SANITIZERS "")

    if(PROJECT_ENABLE_ASAN)
        list(APPEND SANITIZERS "address")
    endif()
    if(PROJECT_ENABLE_UBSAN)
        list(APPEND SANITIZERS "undefined")
    endif()
    if(PROJECT_ENABLE_TSAN)
        list(APPEND SANITIZERS "thread")
    endif()

    if(SANITIZERS)
        string(JOIN "," SAN_FLAGS ${SANITIZERS})
        target_compile_options(${TARGET} PRIVATE -fsanitize=${SAN_FLAGS} -fno-omit-frame-pointer)
        target_link_options(${TARGET} PRIVATE -fsanitize=${SAN_FLAGS})
    endif()
endfunction()
```

### CMakePresets.json 调用

```json
{
  "configurePresets": [
    {
      "name": "asan",
      "inherits": "default",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "PROJECT_ENABLE_ASAN": "ON",
        "PROJECT_ENABLE_UBSAN": "ON"
      }
    },
    {
      "name": "tsan",
      "inherits": "default",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "PROJECT_ENABLE_TSAN": "ON"
      }
    }
  ]
}
```

### 为什么不全局 `set(CMAKE_CXX_FLAGS ...)`

```cmake
# ❌ 不推荐：全局设置影响所有目标（包括第三方库）
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address")
```

第三方库如果没带 sanitizer 编译，链接时可能 ODR 冲突。**应该只在项目自己的 target 上开启**，或者用 `target_compile_options` 加白名单。

---

## 三、组合规则

### ✅ 兼容的组合

| 组合 | Flag | 使用场景 |
|------|------|---------|
| **ASan + UBSan** | `-fsanitize=address,undefined` | **最推荐**——覆盖内存错误 + 未定义行为，一个 CI 配置 |
| **TSan + UBSan** | `-fsanitize=thread,undefined` | 并发 + 未定义行为 |
| **MSan + UBSan** | `-fsanitize=memory,undefined` | 内存初始化 + 未定义行为 |

### ❌ 不兼容的组合

| 组合 | 原因 |
|------|------|
| **ASan + TSan** | 都做内存拦截（shadow memory），编码冲突 |
| **ASan + MSan** | 同上 |
| **TSan + MSan** | 同上 |

---

## 四、运行时选项

每个 sanitizer 通过环境变量配置运行时行为。在 CI 中统一设置：

```bash
# ASan：检测泄漏 + 遇到错误中止 + 打印调用栈
export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1:print_stacktrace=1

# UBSan：遇到 UB 中止 + 打印调用栈
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1

# TSan：遇到数据竞争中止 + 扩展历史记录深度
export TSAN_OPTIONS=halt_on_error=1:history_size=7

# MSan：遇到未初始化读取中止 + 追踪来源
export MSAN_OPTIONS=halt_on_error=1:track_origins=2
```

### 常用选项速查

| 选项 | 适用 | 默认值 | 说明 |
|------|------|--------|------|
| `halt_on_error=1` | 所有 | 0 | 遇到错误立即中止（不继续执行） |
| `print_stacktrace=1` | 所有 | 1 | 打印错误时的调用栈 |
| `detect_leaks=1` | ASan | Linux=1, macOS=0, Windows=❌ | 内存泄漏检测 |
| `suppressions=file.txt` | 所有 | 空 | 抑制已知假阳性 |
| `log_path=/path/to/log` | 所有 | 输出到 stderr | 错误日志输出到文件 |
| `track_origins=2` | MSan | 0 | 追踪未初始化值的来源（2=full） |
| `history_size=7` | TSan | 2 | 历史记录深度（越大越准但内存越多） |

### `suppressions` 文件示例

```text
# supp.txt — 抑制已知假阳性
# 第三方库的已知泄漏
leak:libfoo.so
# 特定函数的已知 UB
vptr:my_known_false_positive_function
```

---

## 五、平台限制与陷阱

### 1. UBSan trap 模式 vs runtime 模式

UBSan 有两种模式：

| 模式 | Flag | 行为 | 适用场景 |
|------|------|------|---------|
| **runtime** | `-fsanitize=undefined` | 打印诊断信息后继续执行 | CI 调试（配合 `halt_on_error=1`） |
| **trap** | `-fsanitize=undefined-trap` | 遇到 UB 直接 `__builtin_trap()` | 生产环境（无运行时依赖） |

**陷阱**：trap 模式**不区分 UB 类型**，所有 UB 都走同一个 trap handler，无法知道触发了哪类 UB。

**修法**：CI 用 runtime 模式 + `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`，既打印诊断信息又中止。

### 2. ASan 的 LeakSanitizer 平台差异

| 平台 | LeakSanitizer |
|------|--------------|
| Linux | 默认启用（`detect_leaks=1`） |
| macOS | 需要显式 `ASAN_OPTIONS=detect_leaks=1`，且不如 Linux 可靠 |
| Windows | **不支持** |

**修法**：CMake 里根据平台条件式设置 leak detection：
```cmake
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(ASAN_OPTIONS "detect_leaks=1:halt_on_error=1:print_stacktrace=1")
elseif(APPLE)
    set(ASAN_OPTIONS "detect_leaks=1:halt_on_error=1:print_stacktrace=1")
else()
    set(ASAN_OPTIONS "halt_on_error=1:print_stacktrace=1")
endif()
```

### 3. MSan 的"全量插桩"要求

MSan 要求**所有**链接的库（包括系统 libc、libstdc++）都被 MSan 插桩，否则读取未 MSan 插桩的库写入的内存会假阳性。

**这是 MSan 在实践中最难用的原因**。两个应对策略：

- **策略 A**（推荐）：只用 ASan + UBSan 组合，覆盖大部分内存错误
- **策略 B**（需要时）：构建一个定制的 instrumented libc++，从源码全量编译所有依赖

### 4. ASan + UBSan 可以同时使用

```cmake
target_compile_options(target PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
target_link_options(target PRIVATE -fsanitize=address,undefined)
```

这是最推荐的一对组合——覆盖内存错误 + 未定义行为，一个 CI 配置。

### 5. Windows 上 ASan 的限制

- `detect_leaks` 不支持
- 调用栈可靠性不如 Linux（依赖 PDB 和 frame pointer 约定）
- MSVC 的 ASan 实现与 Clang 略有不同，假阳性率略高

### 6. 测试在 sanitizer 构建下慢 2-10x

Sanitizer 构建的测试运行时间显著增加，CTest 默认 timeout 可能触发假失败。

**修法**：在 test preset 中单独设置 timeout：
```json
{
  "testPresets": [
    {
      "name": "asan",
      "configurePreset": "asan",
      "execution": { "timeout": 300 }
    }
  ]
}
```

---

## 六、CI 推荐配置

### Per-commit（~10min）

```
1. Debug 编译 + unit test
2. Release 编译 + unit test
```

### Nightly 全量（~1h）

```
1. Debug + ASan + UBSan → unit test
2. Release + ASan + UBSan → unit test
3. Debug + TSan → integration test（并发相关）
4. Debug + coverage → coverage report
```

### 每 commit 跑 sanitizer 的策略

如果 CI 资源充足（或项目对内存安全要求高），每 commit 跑 ASan + UBSan 的 Debug 配置。**Release 下跑 ASan 虽然可以，但调试信息少**（优化导致调用栈不准）。

---

## 七、Agent 适用性

| 任务 | agent 能做吗 | 注意事项 |
|------|------------|---------|
| 配置 CMake sanitizer option | ✅ | 用 target-level 而非全局 flag |
| 设置 CI 的 sanitizer 构建 | ✅ | 注意组合规则和平台限制 |
| 解析 sanitizer 错误输出 | ✅ | 区分 ASan/UBSan/TSan 的不同错误类型 |
| 维护 suppression 文件 | ⚠️ | 需要判断是真假阳性，agent 不应单方面做判断 |
| 跨平台 sanitizer 配置 | ⚠️ | 需要了解各平台的 LSan/ASan 差异 |

## 相关 Guidelines

- [`guidelines/cpp/static-analysis-clang-tidy.md`](static-analysis-clang-tidy.md) —— clang-tidy 静态分析（与 sanitizer 互补）
- [`guidelines/cpp/INDEX.md`](INDEX.md) —— C++ 工程底座总索引
- [`guidelines/code/validation.md`](../code/validation.md) —— 验证纪律
- LLVM 官方文档：`https://clang.llvm.org/docs/AddressSanitizer.html`