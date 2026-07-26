# clang-tidy 策略：Check 分组、CI 集成与常见陷阱

## 核心规则

clang-tidy 不是"全开就好"的工具。Check 分组策略直接决定 CI 的**可信度 × 速度**的平衡点，也是 agent 最常踩的坑——默认全开会让 CI 变慢数倍，噪音淹没信号，最终被关掉不用。

本文件管"CI 常驻跑哪些 check、不跑哪些、怎么配置"。clang-tidy 各 check 的详细说明请直接参考 LLVM 官方文档。

---

## 一、Check 分组策略

clang-tidy 的 90+ 个 check 按 13 组分类。按 CI 常驻适用性分三档：

### 1. ✅ CI 常驻（低假阳性、高回报）

| 组 | 典型效果 | 备注 |
|---|---------|------|
| `bugprone-*` | 可疑的 bug 模式（suspicious `sizeof`、`strncpy` 用法、未使用的 RAII 等） | 假阳性少，真抓 bug |
| `performance-*` | 不必要拷贝、低效算法调用 | 同上 |
| `concurrency-*` | 线程安全相关 check | 同上 |
| `clang-analyzer-*` | **路径敏感**的深层分析（空指针、内存泄漏、use-after-return） | 耗时较长但更准，需设 timeout |

**CI 最小配置：**
```yaml
Checks: '-*,bugprone-*,performance-*,concurrency-*,clang-analyzer-*'
```

### 2. ⚠️ 按需或一次性迁移

| 组 | 建议 | 理由 |
|---|------|------|
| `modernize-*` | **一次性迁移**，跑完即关 | 常驻会不断建议新写法（`auto`、`override`、范围 for），噪音大 |
| `readability-*` | 按需手动跑，不常驻 CI | 假阳性多，跟项目风格相关 |
| `cppcoreguidelines-*` | 选择性启用 | 部分规则过于严格，不适合所有项目 |
| `cert-*` | 安全敏感项目启用 | CERT 安全编码标准映射 |

### 3. ❌ 默认不启用

| 组 | 原因 |
|---|------|
| `alpha.*` | 实验性 check，路径分析在复杂函数上可能跑几分钟 |
| `llvmlibc-*` | LLVM libc 项目专用 |
| `altera-*` | Altera/Intel FPGA OpenCL 专用 |
| `zircon-*` | Fuchsia Zircon 内核专用 |

---

## 二、CI 集成

### 1. CMake 集成方式

CMake 提供 `CMAKE_CXX_CLANG_TIDY` 变量（或 per-target `CXX_CLANG_TIDY` 属性），让 clang-tidy 在**每次编译时**作为 compiler wrapper 运行：

```cmake
# CMakeLists.txt 或 CMakePresets.json
set(CMAKE_CXX_CLANG_TIDY
    "clang-tidy"
    "--checks=-*,bugprone-*,performance-*,clang-analyzer-*"
    "--warnings-as-errors=*"
    "--timeout=60")
```

**注意**：这会乘 2-5x 编译时间（每个 TU 都跑一轮）。适合 CI 的 build job，不适合本地开发。

### 2. 独立 CI job（推荐）

```bash
# 独立在 CI 跑，不拖慢编译
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -B build
run-clang-tidy -p build -j 4 \
    -checks='-*,bugprone-*,performance-*,concurrency-*,clang-analyzer-*' \
    -header-filter='src/.*' \
    --timeout=60 \
    --warnings-as-errors='*'
```

`run-clang-tidy` 是 LLVM 自带的并行 runner，比 `CMAKE_CXX_CLANG_TIDY` 更灵活（可以单独设 timeout 和并行度）。

### 3. 关键配置项

| 配置 | 作用 | 推荐值 |
|------|------|--------|
| `--timeout=60` | 单文件超时跳过，不阻塞 CI | 60-120s |
| `--header-filter='src/.*'` | 只分析项目源码，不分析第三方库头文件 | 匹配项目路径 |
| `--warnings-as-errors='*'` | 所有 warning 都当 error | 视项目容忍度决定 |
| `-j N` | 并行度 | 跟 CI runner 核心数一致 |

---

## 三、常见陷阱

### 1. 性能问题

clang-tidy 的性能瓶颈主要在 `clang-analyzer-*` 组的路径敏感分析。复杂函数（含深层循环、大量分支）可能跑几分钟。

**修法**：
- CI 设 `--timeout=60`，超时的 check **跳过而非失败**
- 独立 CI job 而非 `CMAKE_CXX_CLANG_TIDY`，避免编译被拖慢
- 大型项目可以先只跑 `bugprone-*` + `performance-*`，`clang-analyzer-*` 放 nightly

### 2. `HeaderFilterRegex` 默认不检查头文件

clang-tidy 分析 `.cpp` 时默认**不检查头文件中的问题**。`HeaderFilterRegex` 控制哪些头文件被分析，但**默认值为空**（不检查头文件）。

```yaml
# .clang-tidy
HeaderFilterRegex: 'src/.*\.h$'
```

没有这一行，写在头文件里的 bug 被静默放过。

### 3. `NOLINTBEGIN` / `NOLINTEND` 需要 LLVM 14+

LLVM 14+ 支持批量抑制一段代码：
```cpp
// NOLINTBEGIN(bugprone-suspicious-sizof)
...  // 这段代码的 bugprone 检查被抑制
// NOLINTEND(bugprone-suspicious-sizof)
```

之前版本只有 `// NOLINT`（单行抑制）和 `// NOLINTNEXTLINE`（下一行抑制）。

**修法**：确保 CI 的 clang-tidy 版本 >= 14，否则 `NOLINTBEGIN` 编译报错。

### 4. clang-tidy 与 clang-format 的 `FormatStyle` 冲突

clang-tidy 内部也读 `.clang-format` 做某些检查的格式化上下文。两边配置不一致会导致 clang-tidy 误报格式相关 warning。

**修法**：一个项目只维护一个 `.clang-format`，clang-tidy 的 `FormatStyle` 设成 `file`：
```yaml
# .clang-tidy
FormatStyle: file
```

### 5. 与 `system_header` 的交互

clang-tidy 默认不检查 `-isystem` 目录的头文件（第三方库）。但某些 `.clang-tidy` 配置可能意外覆盖。

**修法**：
```yaml
# .clang-tidy
HeaderFilterRegex: 'src/.*'  # 明确只匹配项目源码路径
```

### 6. 不同 clang-tidy 版本输出不同

同一 `.clang-tidy` 在不同 LLVM 版本下可能产生不同结果。新版本会新增 check、修改老 check 的行为。

**修法**：CI 固定 clang-tidy 版本（Docker 镜像或特定 LLVM 包），避免版本不一致导致的非确定性。

---

## 四、示例 `.clang-tidy` 配置

```yaml
# 项目根目录的 .clang-tidy
Checks: '-*,bugprone-*,performance-*,concurrency-*,clang-analyzer-*'
WarningsAsErrors: '*'
HeaderFilterRegex: 'src/.*'
FormatStyle: file
CheckOptions:
  - key: performance-unnecessary-value-param.Threshold
    value: 32
  - key: bugprone-suspicious-sizof.EnableSuspiciousSizeof
    value: 1
```

---

## 五、Agent 适用性

| 任务 | agent 能做吗 | 注意事项 |
|------|------------|---------|
| 生成 `.clang-tidy` 配置 | ✅ | 按项目类型选 check 组，别全开 |
| 独立 CI job 配置 | ✅ | 记得设 `--timeout` 和 `--header-filter` |
| 解析 clang-tidy 输出 | ✅ | 理解各 check 的假阳性率，不盲目修 |
| 应用 `--fix` 建议 | ⚠️ | **不要自动应用 `modernize-*` 的 fix**（可能改变 API 语义） |
| 跨版本迁移配置 | ⚠️ | 版本差异需要手动核对 |

## 相关 Guidelines

- [`guidelines/cpp/INDEX.md`](INDEX.md) —— C++ 工程底座总索引
- [`guidelines/code/validation.md`](../code/validation.md) —— 验证纪律（"看代码对 ≠ 验证"）
- [`guidelines/code/complexity-coverage-metrics.md`](../code/complexity-coverage-metrics.md) —— CRAP 指标与 clang-tidy 的互补关系
- `techniques/cpp-coverage-and-crap-measurement.md` —— 覆盖率测量（本仓库已有）
- LLVM 官方 clang-tidy check 列表：`https://clang.llvm.org/extra/clang-tidy/checks/list.html`