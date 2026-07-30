# CMakePresets 编排：构建 / 测试 / 工作流三层设计

## 核心规则

CMakePresets.json（CMake 3.19+，扩展至 3.27）替代了旧式的 `-D` 参数链 + `CMAKE_TOOLCHAIN_FILE` 模式。它把构建配置、测试配置和工作流编排统一到一个 JSON 文件中，**可提交到 git、可被 CI 解析、可被 IDE 自动发现**。

本文件管"怎么用 Presets 组织 C++ 项目的构建/测试矩阵"。详细的 Presets 字段说明请直接参考 CMake 官方文档。

---

## 一、三层 Preset 模型

| 层级 | CMake 版本 | 用途 | 类比 |
|------|-----------|------|------|
| **`configurePresets`** | 3.19+ | 配置 CMake 的 cache variables、generator、toolchain | 替代 `-D` 参数链 |
| **`buildPresets`** | 3.19+ | 构建参数（target、并行度、配置） | `cmake --build` 参数包装 |
| **`testPresets`** | 3.20+ | CTest 参数（filter、output、timeout、环境变量） | `ctest` 参数包装 |
| **`workflowPresets`** | 3.27+ | 编排 configure → build → test → package 步骤序列 | 本地 CI 管道 |

### 文件位置

```
project/
├── CMakePresets.json       ← 提交到 git，项目共享
├── CMakeUserPresets.json   ← gitignore，本地覆盖
└── CMakeLists.txt
```

---

## 二、基础模板：Ninja Multi-Config 模式

### 为什么用 `Ninja Multi-Config`

**Ninja Multi-Config**（CMake 3.17+）支持一个 build tree 容纳所有配置（Debug / Release / RelWithDebInfo / Sanitized）。这是最重要的设计决策——**不需要为每个配置创建单独的 build 目录**。

```json
{
  "version": 6,
  "configurePresets": [
    {
      "name": "default",
      "hidden": true,
      "generator": "Ninja Multi-Config",
      "binaryDir": "${sourceDir}/build",
      "cacheVariables": {
        "CMAKE_CXX_STANDARD": "20",
        "CMAKE_CXX_STANDARD_REQUIRED": "ON",
        "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"
      }
    }
  ]
}
```

`hidden: true` 使该 preset 不直接出现在 `--list-presets` 输出中，但可作为继承基类。

### 配置继承

```json
{
  "configurePresets": [
    {
      "name": "debug",
      "inherits": "default",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "PROJECT_ENABLE_ASAN": "OFF",
        "PROJECT_ENABLE_UBSAN": "OFF"
      }
    },
    {
      "name": "release",
      "inherits": "default",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release"
      }
    },
    {
      "name": "asan",
      "inherits": "default",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "PROJECT_ENABLE_ASAN": "ON",
        "PROJECT_ENABLE_UBSAN": "ON"
      }
    }
  ]
}
```

---

## 三、各 Preset 类型详解

### 1. configurePresets

```json
{
  "configurePresets": [
    {
      "name": "linux-clang",
      "hidden": true,
      "generator": "Ninja",
      "architecture": { "value": "x64", "strategy": "set" },
      "cacheVariables": {
        "CMAKE_C_COMPILER": "clang-18",
        "CMAKE_CXX_COMPILER": "clang++-18"
      },
      "condition": {
        "type": "equals",
        "lhs": "${hostSystemName}",
        "rhs": "Linux"
      }
    }
  ]
}
```

**关键字段**：

| 字段 | 作用 | 说明 |
|------|------|------|
| `generator` | 构建系统生成器 | Ninja / Ninja Multi-Config / Visual Studio 17 2022 |
| `architecture` | 目标架构 | VS generator 专用，`"strategy": "set"` 显式设 |
| `toolset` | 工具集 | VS generator 专用，如 `ClangCL` |
| `cacheVariables` | CMake cache 变量 | 值类型：string / bool / array |
| `environment` | 环境变量 | **只在 configure 阶段设置，不传递到 build/test** |
| `condition` | 条件启用 | CMake 3.22+，`${hostSystemName}` 等变量 |
| `inherits` | 继承 | 字符串或数组，多继承 |
| `hidden` | 隐藏 | 不出现在 `--list-presets`，只做基类 |

### 2. buildPresets

```json
{
  "buildPresets": [
    {
      "name": "debug",
      "configurePreset": "debug",
      "configuration": "Debug",
      "jobs": 8
    },
    {
      "name": "release",
      "configurePreset": "release",
      "configuration": "Release",
      "jobs": 8
    },
    {
      "name": "asan",
      "configurePreset": "asan",
      "configuration": "Debug",
      "jobs": 4
    }
  ]
}
```

使用：
```bash
cmake --build --preset debug
cmake --build --preset release
cmake --build --preset asan
```

### 3. testPresets

```json
{
  "testPresets": [
    {
      "name": "unit",
      "configurePreset": "debug",
      "configuration": "Debug",
      "execution": {
        "noTestsAction": "error",
        "stopOnFailure": false,
        "jobs": 4,
        "timeout": 120
      },
      "output": {
        "outputOnFailure": true,
        "shortProgress": true,
        "verbosity": "default"
      },
      "filter": {
        "include": { "name": "UnitTest*" },
        "exclude": { "name": "*Integration*" }
      },
      "environment": {
        "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
        "ASAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"
      }
    },
    {
      "name": "integration",
      "configurePreset": "release",
      "configuration": "Release",
      "execution": {
        "noTestsAction": "error",
        "timeout": 300
      },
      "filter": {
        "include": { "name": "*Integration*" }
      }
    }
  ]
}
```

**关键字段**：

| 字段 | 作用 | 说明 |
|------|------|------|
| `filter.include/exclude` | 按名称/标签/夹具过滤 | 分离 unit vs integration 测试 |
| `execution.timeout` | 单测试超时 | Sanitizer 构建需要更大的值 |
| `execution.jobs` | 并行度 | 默认用 CPU 核心数 |
| `environment` | **测试环境变量** | 在 test 阶段设置，不影响 build |
| `output.outputOnFailure` | 失败时输出完整日志 | CI 必备 |
| `output.junit` | JUnit XML 输出 | CI 解析用 |

使用：
```bash
ctest --preset unit
ctest --preset integration
```

### 4. workflowPresets（CMake 3.27+）

```json
{
  "workflowPresets": [
    {
      "name": "ci-pipeline",
      "steps": [
        { "type": "configure", "name": "debug" },
        { "type": "build", "name": "debug" },
        { "type": "test", "name": "unit" },
        { "type": "configure", "name": "asan" },
        { "type": "build", "name": "asan" },
        { "type": "test", "name": "unit" }
      ]
    }
  ]
}
```

使用：
```bash
cmake --workflow --preset ci-pipeline
```

**限制**：
- 无条件分支（不能跳过 macOS 不支持的 sanitizer）
- 无并行步骤
- 无错误恢复策略（任何步骤失败中止整个 pipeline）
- CI 系统通常在自己的 YAML 中复制此逻辑，workflowPresets 主要用于本地开发

---

## 四、环境变量跨 Preset 的传递规则

一个容易混淆的点：`environment` 字段在不同 Preset 类型中的作用域不同。

```json
{
  "configurePresets": [
    {
      "name": "debug",
      "environment": {
        "MY_VAR": "hello"
      }
    }
  ],
  "testPresets": [
    {
      "name": "unit",
      "configurePreset": "debug",
      "environment": {
        "ASAN_OPTIONS": "halt_on_error=1"
      }
    }
  ]
}
```

| Preset 类型 | 环境变量何时生效 | 传递性 |
|-------------|----------------|--------|
| `configurePreset` | 只在 `cmake -S . --preset <name>` 时 | **不传递**到 build 或 test 阶段 |
| `buildPreset` | 只在 `cmake --build --preset <name>` 时 | 不传递到 test 阶段 |
| `testPreset` | 只在 `ctest --preset <name>` 时 | 不传递回 build 或 configure |

**陷阱**：`testPreset` 的 `environment` 字段是设置 sanitizer 运行时选项的正确位置（build 阶段不需要 ASAN_OPTIONS）。

---

## 五、条件 Preset（CMake 3.22+）

```json
{
  "configurePresets": [
    {
      "name": "win-msvc",
      "condition": {
        "type": "equals",
        "lhs": "${hostSystemName}",
        "rhs": "Windows"
      }
    },
    {
      "name": "linux-clang",
      "condition": {
        "type": "equals",
        "lhs": "${hostSystemName}",
        "rhs": "Linux"
      }
    }
  ]
}
```

**可用变量**：
- `${hostSystemName}` — `CMAKE_HOST_SYSTEM_NAME`（运行 cmake 的机器）
- `${hostSystemVersion}`
- `${sourceDir}` — 项目源码目录
- `${sourceParentDir}`
- `${presetName}` — 当前 preset 的名称
- `${generator}` — 生成器名称（解析后）

**运算符**：`equals`、`notEquals`、`inList`、`notInList`、`matches`、`notMatches`、`and`、`or`、`not`

**陷阱**：`${hostSystemName}` 在 configure 时评估，**不是 test 时**。一个在 Linux 上 configure 的 preset，它的 test preset 条件看不到 Windows 测试机器的 OS。

---

## 六、测试矩阵设计

### 分层策略

| 管道 | 频率 | 配置 | 目标 |
|------|------|------|------|
| **Per-commit** | 每次 push/PR | 1 编译器（最快）+ Debug + Release + unit test | <10 分钟 |
| **Nightly** | 每日 | 全矩阵（MSVC + Clang + GCC）×（Debug + Release + ASan + UBSan） | <1 小时 |
| **Release** | 打 tag | 同 nightly + 打包 + install test + ABI 合规 | 完整验证 |

### CCache / SCCache 集成

```json
{
  "configurePresets": [
    {
      "name": "default",
      "cacheVariables": {
        "CMAKE_CXX_COMPILER_LAUNCHER": "ccache",
        "CMAKE_C_COMPILER_LAUNCHER": "ccache",
        "CCACHE_MAXSIZE": "50G"
      }
    }
  ]
}
```

**ccache 命中率**：80-95% 在增量编译下。**Windows 上注意**：ccache 对 MSVC 支持有限，用 sccache 替代。

### 完整的 Presets 文件示例

```json
{
  "version": 6,
  "configurePresets": [
    {
      "name": "default",
      "hidden": true,
      "generator": "Ninja Multi-Config",
      "binaryDir": "${sourceDir}/build",
      "cacheVariables": {
        "CMAKE_CXX_STANDARD": "20",
        "CMAKE_EXPORT_COMPILE_COMMANDS": "ON",
        "CMAKE_CXX_COMPILER_LAUNCHER": "ccache",
        "CMAKE_C_COMPILER_LAUNCHER": "ccache"
      }
    },
    {
      "name": "debug",
      "inherits": "default",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Debug" }
    },
    {
      "name": "release",
      "inherits": "default",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Release" }
    },
    {
      "name": "asan",
      "inherits": "default",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "PROJECT_ENABLE_ASAN": "ON",
        "PROJECT_ENABLE_UBSAN": "ON"
      }
    }
  ],
  "buildPresets": [
    { "name": "debug", "configurePreset": "debug", "configuration": "Debug" },
    { "name": "release", "configurePreset": "release", "configuration": "Release" },
    { "name": "asan", "configurePreset": "asan", "configuration": "Debug", "jobs": 4 }
  ],
  "testPresets": [
    {
      "name": "unit",
      "configurePreset": "debug",
      "configuration": "Debug",
      "execution": { "noTestsAction": "error", "timeout": 120 },
      "filter": { "exclude": { "name": "*Integration*" } },
      "output": { "outputOnFailure": true }
    },
    {
      "name": "unit-asan",
      "configurePreset": "asan",
      "configuration": "Debug",
      "execution": { "noTestsAction": "error", "timeout": 300 },
      "filter": { "exclude": { "name": "*Integration*" } },
      "output": { "outputOnFailure": true },
      "environment": {
        "ASAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
        "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"
      }
    }
  ]
}
```

---

## 七、常见陷阱

| 陷阱 | 说明 | 修法 |
|------|------|------|
| **Ninja 不支持多配置** | 普通 Ninja 需要每个配置一个 build 目录 | 用 `Ninja Multi-Config` |
| **`environment` 不继承** | configurePreset 的环境变量不传到 testPreset | 各层分别设自己的 environment |
| **`${env.PATH}` 只在 configurePresets 可用** | buildPresets 和 testPresets 不能展开环境变量 | 需要时在 CMakeLists.txt 中用 `find_program` 替代 |
| **`vendor` 字段不继承** | IDE 特定配置整个替换，不合并 | 只在顶层 preset 设 vendor |
| **CMakePresets.json vs CMakeUserPresets.json** | 项目文件提交 git，用户文件 gitignore | 机器特定路径只放 UserPresets |
| **Generator 在 configure 时固定** | 不能在不同 preset 间切换 generator | 不同 generator 需要不同的 configurePreset |
| **Workflow preset 无并行** | 步骤顺序执行 | CI 用原生 YAML 替代 workflow preset |

---

## 八、Agent 适用性

| 任务 | agent 能做吗 | 注意事项 |
|------|------------|---------|
| 生成初始 `CMakePresets.json` | ✅ | 按项目需求选 generator 和配置 |
| 添加新的 build/test preset | ✅ | 注意继承关系和 `version` 字段 |
| 配置 sanitizer 构建 | ✅ | 参考 `sanitizer-integration.md` 的组合规则 |
| 配置 ccache 集成 | ✅ | 透明，加两个 cacheVariables |
| 设计 CI 测试矩阵 | ⚠️ | 需要理解项目的性能/资源约束 |
| 迁移旧式 `-D` 参数链到 Presets | ✅ | 保持语义一致，逐个测试 |

## 相关 Guidelines

- [`guidelines/cpp/sanitizer-integration.md`](sanitizer-integration.md) —— Sanitizer 的 CMake 集成（与 CMakePresets 配合使用）
- [`guidelines/cpp/static-analysis-clang-tidy.md`](static-analysis-clang-tidy.md) —— clang-tidy 的 `CMAKE_CXX_CLANG_TIDY` 集成
- [`guidelines/cpp/build-incremental-and-cmake.md`](build-incremental-and-cmake.md) —— CMake 增量构建 + 跨 DLL 坑
- [`guidelines/cpp/INDEX.md`](INDEX.md) —— C++ 工程底座总索引
- CMake 官方文档：`https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html`