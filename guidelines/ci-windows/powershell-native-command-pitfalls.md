# PowerShell 5.1 调 native command 的三大 pitfall

GitLab Windows shell executor / 任何 PowerShell 写的 CI 脚本，调 `git` /
`p4` / `robocopy` / 别的 .exe 时都可能撞这三个坑。**单纯改 PowerShell encoding
变量都救不了**——必须用 `cmd /c` 包或换 .NET API。

跨项目通用，CI runner 上踩过一次后无差别复发。

---

## Pitfall 1: `$ErrorActionPreference = "Stop"` + native stderr = NativeCommandError

### 现象

```powershell
$ErrorActionPreference = "Stop"
p4 sync //...           # depot 全 up-to-date 时 p4 写 stderr "file(s) up-to-date."
                        # → PS 5.1 立即抛 NativeCommandError，script 终止
```

错误堆栈：

```
p4 : //... - file(s) up-to-date.
+ FullyQualifiedErrorId : NativeCommandError
```

任何写 stderr 的 native command 都触发：

| 命令 | 触发 stderr 的"非错误"场景 |
|---|---|
| `p4 sync` | 全 up-to-date |
| `p4 reopen` | 没匹配 opened 文件 |
| `p4 reconcile` | 没改动 |
| `p4 revert` | 没文件可 revert |
| `p4 submit` | "No files to submit" |
| `p4 opened` | 没 opened files |
| `git pull` | "Already up to date." 在某些 git 版本走 stderr |
| `robocopy` | exit code 1（正常状态"有文件复制"）—— 但 robocopy 不写 stderr，靠 exit code，不撞这条 |

**这些都是 native 命令的"无操作"语义**——它们写 stderr 不是真错误，是把"没事可做"的 hint 走 stderr。但 PS 5.1 把所有 stderr 当作 error candidate，`EAP=Stop` 看到 error stream 有内容就抛 NCE。

### 为什么 `2>&1 | Out-Host` 救不了

直觉以为 `... 2>&1 | Out-Host` 把 stderr merge 到 stdout 就没事了：

```powershell
p4 sync //... 2>&1 | Out-Host       # ❌ 仍然抛 NCE
```

实际不行。PS 5.1 的 NCE 在 native command **写 stderr 的瞬间**触发，**早于** `2>&1` redirect 处理。pipe 后面的 `| Out-Host` 在 NCE 抛出之后才有机会执行。

### 为什么改 `$ErrorActionPreference` / `$OutputEncoding` 救不了

`$ErrorActionPreference` 是**作用于整段 script**的全局变量，不是 per-call。设成 Continue 全段 cmdlet 都不 strict，副作用大。

`$OutputEncoding` 控制的是 PowerShell pipe **stdin 写给 native** 的 encoding，跟 stderr 处理无关。

### 修法：`cmd /c "exe args 2>&1"` 包

```powershell
$ErrorActionPreference = "Stop"   # 保留 strict 给 cmdlet
cmd /c "p4 sync //... 2>&1"       # cmd 子进程内 merge stderr→stdout，PS 只看到 stdout
$global:LASTEXITCODE = 0          # 接受 native exit non-zero（看具体语义决定要不要 check）
```

机制：
- `cmd /c "..."` 启动 cmd.exe 子进程跑命令
- cmd 内的 `2>&1` 在 cmd 进程内合并 stderr→stdout
- PowerShell 接收的是 cmd 进程的 stdout 流（合并后的内容），**完全看不到原 native stderr**
- PowerShell error stream 不被触发 → 不抛 NCE
- cmd 进程 exit code 仍然传递给 `$LASTEXITCODE`

### 不推荐的"修法"

| 方法 | 为什么不推荐 |
|---|---|
| `... 2>&1 \| Out-Null` | 错——NCE 在 redirect 之前抛 |
| `... 2>$null` | 同上 |
| `$ErrorActionPreference = "Continue"` 全局改 | cmdlet 错误也只 warn 不抛，关键 IO 失败会被静默 |
| `try { native } catch { }` | NCE 不是普通 exception，PS 5.1 上 catch 不到 |

---

## Pitfall 2: `Start-Process -ArgumentList @(...)` 含特殊字符的引号 bug

### 现象

```powershell
$args = @(
    "$projectFile",
    "-ExecCmds=Automation RunTests Filter1+Filter2; Automation Quit",   # 含空格 + 分号
    "-unattended"
)
Start-Process -FilePath $exe -ArgumentList $args -NoNewWindow -PassThru
```

子进程实际收到的命令行**被切错**：
- 期望：`Automation RunTests Filter1+Filter2; Automation Quit` 作为一个 arg
- 实际：被切成 `Automation`、`RunTests`、`Filter1+Filter2;`、`Automation`、`Quit` 五段

子进程（如 UnrealEditor-Cmd）只把第一段 `Automation` 当 console command 执行，后面全部丢失。

### Root cause

PowerShell 5.1 `Start-Process -ArgumentList @(...)` 把数组 join 成单字符串前**不会对单元素做精确的引号 escape**。含空格 / 分号 / 等号的 arg 边界丢失。

这是 PowerShell 5.1 的**长期 bug**，PS 7 部分场景修了但 5.1 上仍然存在。

### 修法：用 .NET `[Diagnostics.Process]` + `ProcessStartInfo.Arguments` 单字符串

```powershell
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
# Arguments 是单 string，按 Windows 原生命令行规则解析，自己控引号
$psi.Arguments = "`"$projectFile`" `"-ExecCmds=Automation RunTests $filter; Automation Quit`" -unattended"
$psi.UseShellExecute = $false
$psi.WorkingDirectory = $stagingDir
# stdout/stderr 默认继承父 console，CI log 能看到子进程输出

$process = [System.Diagnostics.Process]::Start($psi)
# $process 可以 .HasExited / .Kill() / .WaitForExit(timeout)
```

机制：
- `ProcessStartInfo.Arguments` 是单 string，**完全按 Windows 命令行 native escape 规则**（[官方文档](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw)）
- 手动加引号 escape：含空格 / 分号 / 等号的 arg 用 `"..."` 整体包起来
- 引号内的 `"` 自身需要 `""` 或 `\"` escape

### 适合用 .NET Process 的场景

- 需要监控子进程（HasExited / Kill）
- 子进程可能不退出（需要超时 force kill）
- stdin/stdout/stderr 需要精细控制
- arg 含特殊字符

简单调用直接用 `&` operator：

```powershell
& $exe $arg1 $arg2 $arg3        # PowerShell native parser 正确 escape
```

`&` operator 跟 `Start-Process` 不同——`&` 用 PowerShell native parser，正确处理含空格的 arg。**但 `&` 是阻塞的**，不能拿 process 对象做超时监控。

---

## Pitfall 3: `$string | native_exe` 通过 stdin 时插 UTF-8 BOM

### 现象

```powershell
$spec = "Client: myclient`nOwner: me`n..."
$spec | p4 client -i      # ❌ p4 报：Unknown field name '﻿Client'.
                          # （Client 前那个不可见字符是 UTF-8 BOM U+FEFF）
```

### Root cause

PowerShell 5.1 把字符串 pipe 给 native exe 时，stdin 编码用 `[Console]::OutputEncoding`。中文 Windows 上这个值的默认状态 / Windows Terminal 默认 / 某些环境配置后是 **UTF-8 with BOM**（preamble = `EF BB BF`）。

PS 5.1 写第一行 stdin 时把 BOM 写进去，p4 把这 3 字节当字段名首字符读 → 报"Unknown field name `[BOM]Client`"。

### 改 encoding 变量救不了

实测 5 种 PowerShell encoding 修法**全部仍有 BOM**：

| 修法 | 结果 |
|---|---|
| 默认（不改）| ❌ BOM |
| `[Console]::OutputEncoding = UTF-8 no BOM` | ❌ BOM |
| `$OutputEncoding = UTF-8 no BOM` | ❌ BOM |
| 两个都改 | ❌ BOM |
| `$OutputEncoding = ASCII` | ❌ BOM |
| **临时文件 + `cmd /c "exe < file"`** | ✅ no BOM |

PS 5.1 pipe 到 native 的 stdin encoding 行为 quirky——文档说用 `$OutputEncoding`，实际行为像是用 `[Console]::OutputEncoding`，但两个都改也救不了。

### 修法：临时文件 + `cmd /c "exe < tempfile"` 完全绕过 PS encoder

```powershell
$tmp = Join-Path $env:TEMP "p4_spec_$($PID).txt"
[System.IO.File]::WriteAllText($tmp, $spec, (New-Object System.Text.UTF8Encoding $false))
try {
    cmd /c "p4 client -i < `"$tmp`"" 2>&1
    $exitCode = $LASTEXITCODE
} finally {
    Remove-Item $tmp -ErrorAction SilentlyContinue
}
```

机制：
- `[System.IO.File]::WriteAllText` + `UTF8Encoding($false)` 写 **UTF-8 no BOM** 文件（`$false` 参数关 BOM）
- `cmd /c "... < file"` 用 cmd 的 stdin redirect，**完全绕过 PowerShell pipe encoder**
- cmd 把文件字节原样喂 native exe stdin

### 适合用这个 pattern 的场景

任何"PowerShell 通过 stdin 喂 multi-line text 给 native exe"——比如：

- `p4 client -i` / `p4 user -i` / `p4 change -i` / 任何 `p4 ... -i`
- `git commit-tree` 通过 stdin 喂 commit message
- 用 PowerShell 给 `psql -c` / `mysql -e` 喂多行 SQL
- 任何 native exe 用 `-` 参数表示"从 stdin 读"

---

## 三个 pitfall 的统一形态

三个坑底层是同一个 PowerShell 5.1 quirk：**native command 的 stdin/stderr 跟 PowerShell native parser 之间有抽象漏洞**。

修法都是**绕过 PowerShell 这一层**：

| Pitfall | 绕过点 |
|---|---|
| 1. stderr → NCE | 用 `cmd /c "exe 2>&1"` 让 cmd 在子进程合并 stderr→stdout |
| 2. ArgumentList 引号 bug | 用 `[Diagnostics.Process]` + 单 string Arguments 自己控引号 |
| 3. stdin BOM | 用临时文件 + `cmd /c "exe < file"` 绕过 PS pipe encoder |

**没有"PowerShell 配置一行就根治"的方案**。每个具体场景都要选对应绕过方式。

## 防御性约定（适合写进项目 AGENTS.md）

PowerShell CI 脚本里调 native command 时遵守：

1. **任何会在"无操作"/"已完成"状态写 stderr 的 native command，必须 `cmd /c "... 2>&1"` 包**（p4 / git 等多数 VCS 工具都属于）
2. **子进程需要监控 / 超时 / kill 时，用 `[Diagnostics.Process]` 不要用 `Start-Process`**
3. **通过 stdin 给 native exe 喂 multi-line text 时，用临时文件 + `cmd /c "exe < file"` 不要用 PowerShell `|` pipe**
4. **简单调用阻塞执行可以用 `& exe arg1 arg2`**，PS native parser 正确处理空格

加新 native command 调用时先想清楚走哪条路径，不要等 CI 跑挂了再来改。

## 项目实例参考

UE 5.5 plugin 的 GitLab CI 调试期间踩穿三个坑：

- **Pitfall 1**: `automation_test` stage 里 `p4 sync //...` 在 client 已 up-to-date 时撞 NCE。修法走 `cmd /c "p4 sync //... 2>&1"`
- **Pitfall 2**: `automation_test` 跑 UnrealEditor-Cmd 时用 `Start-Process -ArgumentList @(...)`，`-ExecCmds="Automation RunTests Filter1+Filter2; Automation Quit"` 被切错，UE Editor 只收到 `Automation` 一个 token。修法换 .NET ProcessStartInfo + 单 string Arguments
- **Pitfall 3**: `deploy` stage 里 `$clientSpec | p4 client -i` 撞 BOM，p4 报 `Unknown field name '﻿Client'`。修法走临时文件 + cmd `<` redirect

三个坑实测验证脚本：`Scripts/CI/test-p4-stdin-bom.ps1` / `test-p4-client-i-bom.ps1` / `test-p4-stderr-nce.ps1`（本地复现 + 验证修法）。

## 相关 Guidelines / Techniques

- `guidelines/workflow/validation.md` —— 强调"verify before claim done"，本文是 CI 验证的具体 pitfall 索引
- `guidelines/workflow/agent-lifecycle.md` —— 列了 "Probably fine" 类自欺欺人；CI 出错时容易凭推测改，应该走"本地复现 → 实测 → 改"的严格流程
