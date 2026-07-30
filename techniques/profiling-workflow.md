# Profiling 工作流：采样 → 插桩 → 分析

## 目的

系统化的性能分析流程：先用采样 profiler 找宏观热点，再用插桩 profiler 做精确分析，最后定位到具体函数和代码行。核心原则是**不要在优化前猜热点**——见 `guidelines/cpp/hot-path-cpp.md` 和 `guidelines/cpp/perf-measure-optimized-binary.md`，性能回退靠 profiler 不靠猜。

## 与现有 corpus 的关系

本仓库已有：
- `guidelines/cpp/hot-path-cpp.md` —— 热路径编码规则（move 语义、dynamic_cast 缓存、线程池等）
- `guidelines/cpp/perf-measure-optimized-binary.md` —— 必须在优化版二进制上测，`/Od` 下热循环慢 5-10x

本 technique 补的是 **"怎么跑 profiler、怎么读结果、怎么自动化"** 这一面。

---

## 一、选型指南

### 采样 vs 插桩

| 维度 | 采样（perf / VTune / gperftools CPU） | 插桩（Tracy / gperftools Heap） |
|------|--------------------------------------|--------------------------------|
| 开销 | 很低（1-5%） | 中到高（10-50%+，取决于插桩密度） |
| 设置 | 最小（`perf record ./binary`） | 需要代码注解（`ZoneScoped`） |
| 精度 | 统计性质（可能漏短函数） | 精确（每个函数调用都记录） |
| 调用图 | 从栈采样统计推导 | 从插桩精确捕获 |
| 内存分析 | 需要 `perf mem` 或 `perf c2c` | 直接支持（Tracy / gperftools heap） |
| 源码关联 | 需要调试符号 | 自动（宏捕获 file:line） |
| 最适合 | 快速定位热点、生产环境 | 定向优化、实时系统、深度分析 |

### 工具选型

| 场景 | 推荐工具 | 理由 |
|------|---------|------|
| Linux 快速热点定位 | **perf** | 零依赖，内核内置，低开销 |
| Linux 深度 CPU 分析 | **perf + FlameGraph** | 免费，信息丰富，可脚本化 |
| 跨平台 GUI 分析 | **Tracy** | 实时可视化，GPU 支持，游戏/实时系统首选 |
| 硬件级分析（cache miss / branch mispredict） | **Intel VTune** | 最深入的 PMU 分析 |
| 快速 CPU/Heap 分析 | **gperftools** | 简单，双功能（CPU + heap），最小配置 |
| 生产环境持续监测 | **perf** | 安全，低开销，可部署到生产 |

---

## 二、核心工作流：perf + FlameGraph（Linux）

### 1. 前置条件

```bash
# 检查 perf 权限
cat /proc/sys/kernel/perf_event_paranoid
#   2 = 默认（仅用户空间，无内核跟踪，无系统级分析）
#   1 = 允许内核分析和 CPU 事件
#   0 = 允许原始 tracepoint 访问
#  -1 = 无限制

# 调整（临时）
sudo sysctl -w kernel.perf_event_paranoid=1

# 或永久写入 /etc/sysctl.conf
echo "kernel.perf_event_paranoid=1" | sudo tee -a /etc/sysctl.conf
```

### 2. 编译要求

```cmake
# 所有参与 profiling 的 target 必须开启 frame pointer
target_compile_options(target PRIVATE -fno-omit-frame-pointer)
```

**为什么**：perf 的 `--call-graph fp` 模式依赖 frame pointer 做栈展开。没有 `-fno-omit-frame-pointer`，编译器（`-O2` 及以上）会省略 frame pointer，调用栈被截断。可以用 `--call-graph dwarf` 替代（走 `.eh_frame`，更慢 5-10x 但不需要 frame pointer）。

### 3. 采样

```bash
# 基本采样（99 Hz = 避免与周期性事件锁步）
perf record -g --call-graph fp -F 99 -o perf.data -- ./myprogram

# 按时间采样
perf record -g --call-graph fp -F 99 -o perf.data --duration 30 -- ./myprogram

# 采样已运行的进程（-p PID）
perf record -g --call-graph fp -F 99 -o perf.data -p $(pgrep myprogram)

# 系统级采样（-a）
perf record -g --call-graph fp -F 99 -a -o perf.data --duration 30
```

### 4. 生成报告

```bash
# 文本报告（top 函数）
perf report -i perf.data --stdio --no-children | head -50

# 更详细的报告（含子调用）
perf report -i perf.data --stdio --children | head -50

# 函数级注解（热点函数源码 + 指令）
perf annotate -i perf.data --stdio --symbol HotFunction
```

### 5. 生成火焰图

```bash
git clone --depth=1 https://github.com/brendangregg/FlameGraph

# 导出采样数据
perf script -i perf.data > perf.script

# 折叠调用栈
./FlameGraph/stackcollapse-perf.pl perf.script > out.folded

# 生成 SVG 火焰图
./FlameGraph/flamegraph.pl out.folded > flamegraph.svg

# 生成差分火焰图（对比两个版本）
# 先各跑一次基线 + 新版本，再 diff
./FlameGraph/difffolded.pl out.baseline.folded out.new.folded | \
    ./FlameGraph/flamegraph.pl > diff.svg
```

### 6. 结果解读

火焰图读法：
- **X 轴**：采样占比（宽度 = 该函数在采样中的占比）
- **Y 轴**：调用栈深度（从下到上 = 从主函数到叶子函数）
- **颜色**：通常随机（红色 = 热点，但不同工具着色不同）

**agent 读图建议**：agent 不直接读 SVG XML，而是读 `perf report --stdio` 的文本输出，或 `perf script` 的原始采样数据。文本输出比 SVG 更适合自动化分析。

### 7. 回归检测

```bash
# 对比两个 profile 的热点差异
perf diff perf.baseline.data perf.new.data
```

输出显示函数热度的变化量（+/- 百分比），适合 CI 中做性能回归检测。

---

## 三、gperftools（Google Performance Tools）

### 特点

- **CPU Profiler**：基于 `SIGPROF` 信号采样，跟 perf 类似
- **Heap Profiler**：跟踪所有 `malloc`/`free`，生成堆快照
- **最小配置**：链接库 + 设环境变量即可

### CPU Profiler

```bash
# 方法 1：环境变量
CPUPROFILE=/tmp/prof.out ./myprogram
pprof --text ./myprogram /tmp/prof.out
pprof --svg ./myprogram /tmp/prof.out > flame.svg
pprof --top ./myprogram /tmp/prof.out

# 方法 2：程序化控制
# 在代码中：
#   #include <gperftools/profiler.h>
#   ProfilerStart("/tmp/prof.out");
#   // ... 热路径 ...
#   ProfilerStop();
```

### Heap Profiler

```bash
# 需要链接 -ltcmalloc
HEAPPROFILE=/tmp/heap ./myprogram

# 生成报告（对比两个快照）
pprof --text ./myprogram --base=/tmp/heap.0001.heap /tmp/heap.0002.heap

# 查看泄漏
pprof --objects ./myprogram /tmp/heap.0001.heap
```

### 陷阱

| 陷阱 | 说明 | 修法 |
|------|------|------|
| **`-fno-omit-frame-pointer` 必须** | gperftools 依赖 frame pointer 做栈展开 | CMake 里设置 |
| **SIGPROF 冲突** | 如果程序已用 `SIGPROF`，gperftools 的 CPU profiler 会冲突 | 换用 perf 或 Tracy |
| **`-lprofiler` vs `-ltcmalloc`** | CPU profiler 和 heap profiler 是独立的库 | CPU profiler 不需要 tcmalloc |
| **线程采样不均匀** | 多线程下各线程可能不被均匀采样 | 对多线程场景用 `perf` 或 Tracy |
| **社区维护状态** | 原始 google-perftools 已不活跃 | 用社区 fork：`gperftools/gperftools` |

---

## 四、Tracy（实时插桩 Profiler）

### 特点

- **低开销插桩**：每个 `ZoneScoped` 约 10-50ns
- **实时可视化**：GUI 连接正在运行的程序
- **GPU 支持**：OpenGL / Vulkan / DirectX
- **内存分析**：`TracyAlloc` / `TracyFree`
- **锁分析**：`ZoneScopedLock` 检测互斥竞争

### 代码插桩

```cpp
#include <tracy/Tracy.hpp>

void MyFunction() {
    ZoneScoped;  // 自动捕获函数名、文件、行号、耗时

    // ... 函数体 ...

    {   // 命名区间
        ZoneScopedN("Parsing");
        // ...
    }
}

void MyNamedFunction() {
    ZoneScopedN("Custom Name");
    // ...
}

// 内存跟踪
void* ptr = malloc(1024);
TracyAlloc(ptr, 1024);
// ...
TracyFree(ptr);
```

### 编译要求

```cmake
# CMake 集成
# Tracy 的 ZoneScoped 在 Release 下默认是空操作（零开销）
# 需要 profiling 时必须定义 TRACY_ENABLE
target_compile_options(target PRIVATE
    $<$<CONFIG:RelWithDebInfo>: -DTRACY_ENABLE>)
target_link_libraries(target TracyClient)
```

### 捕获方式

```bash
# 实时捕获（启动 GUI 后连接正在运行的进程）
# 运行程序，然后启动 tracy-profiler 连接

# 命令行捕获到文件（headless capture）
tracy-capture -o trace.tracy -a 127.0.0.1

# 查看捕获文件
tracy-profiler trace.tracy
```

### 陷阱

| 陷阱 | 说明 | 修法 |
|------|------|------|
| **Release 下默认是空操作** | `ZoneScoped` 在没有 `TRACY_ENABLE` 时是空宏 | 需要 profiling 的配置显式定义 |
| **需要手动注解** | 不像 perf 自动捕获所有函数 | 先用 perf 找热点，再对热点函数加 Tracy 插桩 |
| **网络端口 8086** | 默认 UDP 端口，防火墙/容器可能拦截 | 确保端口开放 |
| **DLL 边界问题** | 跨 DLL 的 Tracy 插桩需要每个 DLL 有自己的 client context | 项目中统一 Tracy 初始化 |

---

## 五、Intel VTune（硬件级分析）

### 特点

- **最深入的硬件分析**：cache miss、branch mispredict、front-end stall、TLB miss
- **CLI 可脚本化**：`vtune -collect hotspots -r result -- ./app`
- **分析类型丰富**：hotspots、performance-snapshot、memory-access、threading、hpc-performance

### CLI 用法

```bash
# 收集热点数据
vtune -collect hotspots -result-dir vtune_result -- ./myprogram

# 收集性能快照（快速概览）
vtune -collect performance-snapshot -result-dir vtune_result -- ./myprogram

# 收集内存访问分析
vtune -collect memory-access -result-dir vtune_result -- ./myprogram

# 生成报告
vtune -report summary -result-dir vtune_result
vtune -report hotspots -result-dir vtune_result
```

### 陷阱

| 陷阱 | 说明 | 修法 |
|------|------|------|
| **Driver 安装** | 需要 `sepdk` 驱动访问硬件 PMU | CI 环境可能无法安装，用 perf 替代 |
| **事件列表 CPU 特定** | Skylake 上收集的数据不能比较 Ice Lake | 不同 CPU 的报告分开比较 |
| **CLI vs GUI 差距** | 部分分析类型只在 GUI 可用 | 多数场景 CLI 够用 |
| **License** | 商业产品，部分功能需要付费 | 免费版覆盖大部分场景 |

---

## 六、Profililng 自动化 CI 管道

### 性能回归检测

```yaml
# GitHub Actions 示例：perf 性能回归
- name: Profile with perf
  run: |
    perf record -g --call-graph fp -F 99 -o perf.data -- ./myprogram
    perf report -i perf.data --stdio --no-children > report.txt

- name: Compare with baseline
  run: |
    # 从 artifact 下载基线
    perf diff perf.baseline.data perf.data > diff.txt
    # 如果某函数热度增加超过 10%，标记为失败
    if grep -qE '[+][0-9]+\.[0-9]+%' diff.txt; then
      echo "Performance regression detected"
      exit 1
    fi
```

### 火焰图作为 CI artifact

```yaml
- name: Generate flamegraph
  run: |
    perf script -i perf.data > perf.script
    ./stackcollapse-perf.pl perf.script > out.folded
    ./flamegraph.pl out.folded > flamegraph.svg

- name: Upload flamegraph
  uses: actions/upload-artifact@v4
  with:
    name: flamegraph
    path: flamegraph.svg
```

### 分层策略

| 管道 | 频率 | 工具 | 目标 |
|------|------|------|------|
| **Per-commit** | 每次 push | 不跑 profiling | 保持 CI 快速 |
| **Nightly** | 每日 | perf + FlameGraph | 检测性能回归 |
| **Release** | 打 tag | perf + VTune（可选） | 完整性能基线 |
| **Ad-hoc** | 按需 | Tracy 或 VTune | 定向优化 |

---

## 七、Agent 适用性

| 任务 | agent 能做吗 | 注意事项 |
|------|------------|---------|
| 运行 perf 采样 | ✅ | 检查 `perf_event_paranoid` 权限 |
| 生成火焰图 | ✅ | 管道化脚本，clone FlameGraph 仓库 |
| 读 `perf report --stdio` 输出 | ✅ | 文本格式，容易解析热点函数 |
| 配置 Tracy 插桩 | ✅ | 注意 `TRACY_ENABLE` 宏 |
| 运行 gperftools | ✅ | 注意 `-fno-omit-frame-pointer` 和 SIGPROF 冲突 |
| 运行 VTune CLI | ⚠️ | 需要 driver 安装，CI 环境可能不行 |
| 读 SVG 火焰图 | ❌ | 直接读 SVG XML 不实用，用文本报告替代 |
| 判断性能回归 | ⚠️ | 需要基线数据，统计显著性判断 |

## 相关 Guidelines / Techniques

- [`guidelines/cpp/hot-path-cpp.md`](../guidelines/cpp/hot-path-cpp.md) —— 热路径编码规则（发现问题后的修法）
- [`guidelines/cpp/perf-measure-optimized-binary.md`](../guidelines/cpp/perf-measure-optimized-binary.md) —— 必须在优化版上测
- [`guidelines/cpp/INDEX.md`](../guidelines/cpp/INDEX.md) —— C++ 工程底座总索引
- [`techniques/debugger-scripting.md`](debugger-scripting.md) —— 配套的调试器脚本化（crash 取证后需要优化性能时衔接本 technique）
- [`guidelines/code/diagnose-before-fixing.md`](../guidelines/code/diagnose-before-fixing.md) —— 先取证再修（profiling 是性能取证手段）
- [`guidelines/code/validation.md`](../guidelines/code/validation.md) —— 验证纪律
- Brendan Gregg's FlameGraph：`https://github.com/brendangregg/FlameGraph`