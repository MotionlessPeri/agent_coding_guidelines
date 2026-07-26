# 调试器脚本化：lldb Python / gdb batch / WinDbg cdb 自动化调试

## 目的

用调试器脚本代替人工交互，在 CI 或自动化流程中完成 crash dump 分析、backtrace 提取、变量值检查。核心流程：

1. 确定平台（Linux core dump / Windows .dmp / macOS .crash）
2. 选对应调试器（lldb Python / gdb batch / WinDbg cdb）
3. 跑脚本提取：线程栈、crash 原因、寄存器、关键变量
4. 交叉引用符号文件（addr2line / PDB / dsymutil）

## 与现有 corpus 的关系

本仓库已有 `guidelines/cpp/windows-native-crash-hang-evidence.md`（Windows crash/hang 的**取证分类**和**手动分析步骤**）。本 technique 补的是**自动化脚本化**这一面——用调试器脚本替代人工逐条输入命令。

---

## 一、选型指南

| 场景 | 推荐工具 | 理由 |
|------|---------|------|
| Linux crash dump 分析 | **lldb Python**（首选）/ gdb batch | lldb Python API 更丰富；gdb 通用性更高 |
| Windows crash dump 分析 | **WinDbg cdb** | 原生 Windows 工具，`!analyze -v` 不可替代 |
| macOS crash dump 分析 | **lldb** | 原生调试器，gdb 已废弃 |
| 跨平台 agent 脚本 | **lldb Python** | 同一 Python API 跨 Linux/macOS |
| 最小依赖快速分析 | **gdb batch** | 几乎每个 Linux 系统都有，零依赖 |

---

## 二、lldb Python 自动化

### 核心 API

| 类 | 用途 | 关键方法 |
|---|---|---|
| `SBTarget` | 被调试的程序 | `CreateTarget()`, `BreakpointCreateByName()`, `LoadCore()` |
| `SBProcess` | 进程 | `GetNumThreads()`, `GetThreadAtIndex()`, `ReadMemory()`, `WriteMemory()` |
| `SBThread` | 线程 | `GetNumFrames()`, `GetFrameAtIndex()`, `GetStopReason()`, `GetStopDescription()` |
| `SBFrame` | 栈帧 | `GetPC()`, `GetFunctionName()`, `GetLineEntry()`, `GetVariables()`, `EvaluateExpression()` |
| `SBValue` | 变量值 | `GetName()`, `GetValue()`, `GetTypeName()`, `GetNumChildren()`, `GetChildAtIndex()` |

### Crash dump 分析脚本（完整模板）

```python
#!/usr/bin/env python3
"""LLDB Python script for automated crash dump analysis.

Usage:
    lldb -b -o "script import sys; sys.path.insert(0, '.'); import analyze_crash"
         -o "analyze_core" -o "quit" ./binary core

Or in non-interactive mode:
    lldb -b -s analyze_crash.lldb ./binary core
"""
import lldb

def analyze_core(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    if not target:
        print("No target selected")
        return

    process = target.GetProcess()
    if not process or not process.IsValid():
        print("No process (core dump not loaded?)")
        return

    print(f"=== Crash Dump Analysis ===")
    print(f"Target: {target.GetExecutable().GetFilename()}")
    print(f"Num threads: {process.GetNumThreads()}")
    print()

    for t in range(process.GetNumThreads()):
        thread = process.GetThreadAtIndex(t)
        reason = thread.GetStopReason()
        print(f"--- Thread {t} (stop_reason={reason}) ---")

        # Identify crashing thread
        if reason == lldb.eStopReasonException or reason == lldb.eStopReasonSignal:
            print(f"  *** CRASHING THREAD ***")
            stop_desc = thread.GetStopDescription(256)
            if stop_desc:
                print(f"  Stop: {stop_desc}")

        for f in range(min(thread.GetNumFrames(), 32)):  # Limit to 32 frames
            frame = thread.GetFrameAtIndex(f)
            func = frame.GetFunctionName() or "???"
            pc = frame.GetPC()
            line = frame.GetLineEntry()
            if line.IsValid():
                file_spec = line.GetFileSpec()
                print(f"  #{f:2d}: {func} [{file_spec.GetFilename()}:{line.GetLine()}] pc=0x{pc:x}")
            else:
                print(f"  #{f:2d}: {func} [pc=0x{pc:x}]")
        print()

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f analyze_crash.analyze_core analyze_core')
    print('Loaded: analyze_core. Run "analyze_core" to analyze.')
```

### CI 调用方式

```bash
# 方式 1：通过 -o 执行脚本
lldb -b -o "script import sys; sys.path.insert(0,'.'); import analyze_crash" \
    -o "analyze_core" -o "quit" ./binary core

# 方式 2：LLDB 命令文件
echo "script import sys; sys.path.insert(0,'.'); import analyze_crash" > script.lldb
echo "analyze_core" >> script.lldb
echo "quit" >> script.lldb
lldb -b -s script.lldb ./binary core
```

### 陷阱

| 陷阱 | 说明 | 修法 |
|------|------|------|
| **lldb 模块只能在 LLDB 内用** | 不能 `python analyze_crash.py` 独立运行 | 必须通过 `lldb -b -s` 或 `-o` 调用 |
| **Python 版本不匹配** | llvdb 捆绑自己的 Python，系统 pip 安装的包可能找不到 | 用 `lldb -b -P` 确认 Python 路径，用它安装依赖 |
| **SBValue 生命周期短** | 进程继续执行后 SBValue 失效 | crash dump 分析不受影响（静态数据） |
| **`GetStopReason()` 在 crash dump 上** | 崩溃线程不一定是 thread 0 | 遍历所有线程，检查 `GetStopReason()` |
| **`EvaluateExpression()` 只读** | 在 crash dump 上不能调修改状态的函数 | 只用于读变量，不影响 |

---

## 三、gdb batch 自动化

### 核心用法

```bash
# 基本 crash dump 分析
gdb -batch \
    -ex "set pagination off" \
    -ex "bt" \
    -ex "thread apply all bt" \
    -ex "info registers" \
    -ex "quit" \
    ./binary core

# 输出到文件
gdb -batch \
    -ex "set pagination off" \
    -ex "bt" \
    -ex "thread apply all bt full" \
    -ex "info registers" \
    -logfile analysis.txt \
    ./binary core
```

### Python 脚本扩展

```python
import gdb

class AnalyzeCrash(gdb.Command):
    """Analyze crash dump: prints backtrace, registers, and crash reason"""
    def __init__(self):
        super().__init__("analyze-crash", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        # Print crash reason
        thread = gdb.selected_thread()
        if thread:
            print(f"Thread: {thread.num}, name: {thread.name}")

        # Print backtrace
        frame = gdb.selected_frame()
        print(f"Crash at: {frame.name()} (PC=0x{frame.pc():x})")
        i = 0
        while frame:
            name = frame.name() or "???"
            line = frame.find_sal()
            if line and line.symtab:
                print(f"  #{i}: {name} at {line.symtab.filename}:{line.line}")
            else:
                print(f"  #{i}: {name}")
            frame = frame.older()
            i += 1
            if i >= 32:
                break

AnalyzeCrash()
```

调用：
```bash
gdb -batch -ex "source analyze.py" -ex "analyze-crash" -ex "quit" ./binary core
```

### GDB/MI 接口（机器可解析）

```bash
gdb -batch -interpreter=mi2 \
    -ex "file ./binary" \
    -ex "core core" \
    -ex "-stack-list-frames 0 32" \
    -ex "-stack-info-depth" \
    -ex "quit"
```

输出是结构化格式，适合 CI 解析。

### 陷阱

| 陷阱 | 说明 | 修法 |
|------|------|------|
| **`-batch` 遇到第一个错误就退出** | 某条命令失败，剩余命令不执行 | `set batch on` 或 Python 脚本 try/except |
| **`set pagination off` 必须** | 否则 gdb 可能卡住等待输入 | 每条 batch 命令链第一条加 |
| **core 文件格式自动检测可能失败** | 需要显式 `-c core` | 用 `gdb -c core ./binary` 指定 |
| **Python 模块只在 gdb 内可用** | 不能独立运行 | 通过 `-ex "source script.py"` 调用 |
| **`-batch-silent` 抑制输出** | 只输出错误信息，适合 CI 只关心失败 | 确认需要什么输出级别 |

---

## 四、WinDbg cdb 自动化

### 核心用法

```batch
:: 基本 crash dump 分析
cdb -z crash.dmp -c ".logopen analysis.txt; .ecxr; !analyze -v; kv; .logclose; q"

:: 全线程栈
cdb -z crash.dmp -c ".logopen analysis.txt; .ecxr; !analyze -v; ~*kb; .logclose; q"

:: 只看简要分析（适合 CI 快速检查）
cdb -z crash.dmp -c ".ecxr; !analyze -v; q"
```

### 关键命令

| 命令 | 用途 | 必须在 `!analyze -v` 之前？ |
|------|------|---------------------------|
| `.ecxr` | 设置异常上下文到崩溃线程 | ✅ 是 |
| `!analyze -v` | 自动崩溃分析（异常类型、根因、调用栈） | — |
| `kv` | 显示崩溃线程栈帧（含 FPO 信息） | 否 |
| `~*kb` | 显示所有线程的 backtrace | 否 |
| `!thread` | 线程信息 | 否 |
| `.logopen` / `.logclose` | 日志输出到文件 | 否 |
| `lm` | 列出已加载的模块 | 否 |

### JavaScript 脚本（WinDbg 现代方式）

```javascript
"use strict";

function initializeScript() {
    return [new host.apiVersion(1, 0)];
}

function invokeScript() {
    var control = host.namespace.Debugger.Sessions[0].Control;
    var output = control.ExecuteCommand("!analyze -v");
    for (var i = 0; i < output.length; i++) {
        host.diagnostics.debugLog(output[i] + "\n");
    }
}
```

运行：
```batch
cdb -z crash.dmp -c ".scriptrun analyze.js; q"
```

### 陷阱

| 陷阱 | 说明 | 修法 |
|------|------|------|
| **`.ecxr` 必须在 `!analyze -v` 之前** | 否则分析的是错误上下文 | 命令链顺序：`.ecxr` → `!analyze -v` |
| **`!analyze -v` 不是 100% 准确** | 启发式分析，堆栈损坏或嵌套异常时可能误判 | 交叉检查 `kv` 和寄存器值 |
| **符号文件是必需的** | 没有 PDB 时函数名变成地址 | 设置 `_NT_SYMBOL_PATH` 环境变量 |
| **exit code 0 不代表成功** | cdb 即使分析失败也返回 0 | 检查 log 文件中是否有预期输出 |
| **语法与 gdb/lldb 不兼容** | WinDbg 的 `MASM` 表达式语法与 gdb 不同 | Windows 上优先用 lldb 的 Windows 端口（`lldb -c dump.dmp`） |

---

## 五、跨平台策略

### 场景：agent 需要通用 crash dump 分析

如果 agent 需要跨平台处理 crash dump，推荐顺序：

1. **平台检测**：文件扩展名（`.dmp` = Windows，`core` = Linux，`.crash` = macOS）
2. **工具选择**：
   - Linux → lldb Python（首选，API 最丰富）
   - Windows → cdb batch（`!analyze -v` 不可替代）
   - macOS → lldb Python（原生调试器）
3. **符号解析**：
   - Linux → `addr2line -e binary -f address`
   - Windows → `!sympath` + `.reload` / `dbghelp`
   - macOS → `atos` / `lldb` 自动符号化

### 最小依赖方案

如果 agent 所在环境限制多（无 Python、无 LLDB、只有最小系统工具）：

```bash
# Linux 最小依赖：gdb + addr2line
gdb -batch -ex "bt" -ex "thread apply all bt" -ex "quit" binary core 2>&1

# 配合 addr2line 符号化
addr2line -e binary -f <pc_address>
```

---

## 六、自动化验证的 CI 集成

### GitHub Actions 示例

```yaml
- name: Analyze crash dump
  run: |
    # Linux: lldb Python
    lldb -b -o "script import sys; sys.path.insert(0,'.'); import analyze_crash" \
         -o "analyze_core" -o "quit" ./binary core

    # Windows: cdb
    cdb -z crash.dmp -c ".ecxr; !analyze -v; q"
```

### 失败判据

调试器脚本输出的结果不属于本技术范围。但有两个通用原则：

1. **崩溃类型**：如果 crash 是 `SIGSEGV` / `ACCESS_VIOLATION` / `assert` 之一，且调用栈指向项目代码而非第三方库 → 需要人工 review
2. **符号完整性**：如果 backtrace 中超过 50% 的帧是 `??`（无符号）→ 需要检查符号文件配置

---

## 七、Agent 适用性

| 任务 | agent 能做吗 | 注意事项 |
|------|------------|---------|
| 编写 lldb Python 脚本 | ✅ | 模板化代码，注意 Python 版本匹配 |
| 编写 gdb batch 命令链 | ✅ | 记得 `set pagination off` |
| 编写 cdb 命令链 | ✅ | 命令顺序 `.ecxr` → `!analyze -v` |
| 解析 backtrace 输出 | ✅ | 识别崩溃线程、关键函数 |
| 设置 CI 中的调试器脚本 | ✅ | 确认调试器已安装，符号路径已配置 |
| 读寄存器值 / 变量值 | ⚠️ | 需要知道目标架构的寄存器约定 |
| 反编译 crash 地址附近的指令 | ⚠️ | 配合 `objdump` / `llvm-objdump` |

## 相关 Guidelines / Techniques

- [`guidelines/cpp/windows-native-crash-hang-evidence.md`](../guidelines/cpp/windows-native-crash-hang-evidence.md) —— Windows crash/hang 取证分类（本 technique 的自动化脚本与之互补：那条管"取什么证"，本条管"怎么用脚本取"）
- [`guidelines/cpp/INDEX.md`](../guidelines/cpp/INDEX.md) —— C++ 工程底座总索引
- [`guidelines/code/diagnose-before-fixing.md`](../guidelines/code/diagnose-before-fixing.md) —— 先取证再修（调试器脚本是取证手段之一）
- [`guidelines/code/validation.md`](../guidelines/code/validation.md) —— 验证纪律
- `techniques/cpp-coverage-and-crap-measurement.md` —— 配套的 C++ 覆盖率测量技术