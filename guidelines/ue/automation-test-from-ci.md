# UE 在 CI 跑 Automation Test 的两个 idiom

CI（GitLab / Jenkins / GitHub Actions Windows runner）跑 UE Automation Test
时绕不开的两个坑——选错 editor 二进制 / 测试跑完 editor 不 quit。两个坑都让 CI
job 表面上"开始跑"了实际**永远不会自然结束**，撞 job timeout 才发现。

跟 IDE 里手动跑 Automation（Tools → Test Automation → Run）行为不同，只在
CLI 模式才暴露。

---

## Idiom 1: 必须用 `UnrealEditor-Cmd.exe`，不能用 `UnrealEditor.exe`

### 现象

CI 脚本（PowerShell / bash）：

```powershell
& "$enginePath\Engine\Binaries\Win64\UnrealEditor.exe" `
    "$project.uproject" `
    -ExecCmds="Automation RunTests MyTests; Quit" `
    -unattended -nopause -nullrhi -log
$editorExitCode = $LASTEXITCODE       # ← 空字符串或立即 0
```

PowerShell 立即返回，`$LASTEXITCODE` 是空或 0。但**子进程 UnrealEditor.exe 仍在
后台跑**——直到 CI runner 把整个 step 1h timeout 强制 kill。

### Root cause

`UnrealEditor.exe` 是 **GUI subsystem** Windows app（PE header `Subsystem` 字段 = `IMAGE_SUBSYSTEM_WINDOWS_GUI`）。GUI subsystem app 的特点：

- 启动后**不阻塞** parent shell —— shell（PowerShell / cmd）立即返回
- 没有 attached console，stdout / stderr 不流到 parent

CI 脚本里 `& gui_app.exe` 调用立即返回 `$LASTEXITCODE` = 启动状态（通常 0），script 继续往下跑（"检测 report 文件" / "解析结果" / "exit 1"），但启动的 editor 子进程独立存活。

GitLab runner 等 step 启动的**所有子进程都退出**才认为 step 完成 —— 等到 timeout 强制 kill。

### 修法：用 `UnrealEditor-Cmd.exe`

UE 在 `Engine/Binaries/Win64/` 同目录下提供 **`UnrealEditor-Cmd.exe`**：

- 同一个 editor 二进制内核，PE Subsystem = `IMAGE_SUBSYSTEM_WINDOWS_CUI`（console）
- console subsystem 启动**会**阻塞 parent shell —— PowerShell `&` 等它退出
- stdout / stderr 流到 parent shell —— CI log 能看到 editor 实时输出（`LogInit:` / `LogAutomationController:` 等）
- `$LASTEXITCODE` 正确反映 editor exit code

```powershell
& "$enginePath\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
    "$project.uproject" `
    -ExecCmds="Automation RunTests MyTests; Quit" `
    -unattended -nopause -nullrhi -log
$editorExitCode = $LASTEXITCODE       # ← 真实 exit code，编辑器退出后
```

### 用 PowerShell `Start-Process` 还是 `&` 还是 .NET Process

`UnrealEditor-Cmd.exe` 是 console subsystem，三种方式都能 work：

| 方式 | 阻塞 | 拿 process 对象 | 用法 |
|---|---|---|---|
| `& exe args` | ✅ 阻塞 | ❌ | 简单同步等退出 |
| `Start-Process -Wait -PassThru` | ✅ 阻塞 + 可拿对象 | ✅ | 同步等 + 拿 exit code |
| `[Diagnostics.Process]::Start($psi)` | ❌ 不阻塞 | ✅ | 后台监控 + 超时控制（见 Idiom 2）|

Idiom 2 需要超时控制 + force kill，必须用 `[Diagnostics.Process]`。

⚠️ 不要用 `Start-Process -ArgumentList @(...)`——含特殊字符的 arg 引号会被切错。详 `guidelines/ci-windows/powershell-native-command-pitfalls.md` Pitfall 2。

---

## Idiom 2: Editor 跑完 Automation 不能 graceful quit，必须脚本主动 force kill

### 现象

```powershell
& UnrealEditor-Cmd.exe ... -ExecCmds="Automation RunTests MyTests; Automation Quit" ...
```

观察 log：

```
[time:1.0] LogAutomationCommandLine: ...Automation Test Queue Empty 96 tests performed.
[time:1.5] LogEOSSDK: SDK Config Platform Update Request Successful
[time:2.0] LogEOSSDK: ScheduleNextSDKConfigDataUpdate ...
...
[time:10.0] LogAudioMixer: Changing default audio render device ...
[time:11.0] LogEOSSDK: Updating Product SDK Config ...
[time:1200.0] ← runner timeout，强制 kill
```

测试 1 分钟跑完了，但 editor 进程**继续跑 10+ 分钟**直到 CI runner 撞 job
timeout。

### Root cause

`Automation Quit` console command 触发 `FPlatformMisc::RequestExitWithStatus(force=true, exit_code=0)`。这个调用**只是 set flag** 让 main loop 检测到该退出，**不是**强制 kill 进程。

但 editor shutdown 路径上有几个**后台线程**会阻塞 main loop 退出：

| 阻塞源 | 行为 |
|---|---|
| **EOSSDK telemetry** | Epic Online Services 后台线程定期 ping `api.epicgames.dev`，HTTP timeout 30s 不退；后台 SDK Config 更新循环每 5-10 分钟一次 |
| **AudioMixer cleanup** | XAudio2 device 切换 / shutdown 流程，几百 ms 到几秒 |
| **DerivedDataCache maintenance** | DDC 后台清理可能阻塞 |
| **PythonScriptPlugin** | 如果有 PipInstall venv 跑 pip 命令，子进程没完不让 main loop 退 |

跟 `-nullrhi` 模式无关——这些都是 framework 层后台 worker，不依赖 rendering。

UE 5.5 实测：Automation 测试 ~1 min 完成，editor 在 EOSSDK / AudioMixer 等卡 shutdown 10+ 分钟。Job 1h timeout 几乎必中。

### 修法：脚本主动监控 report 文件 + grace + force kill

不靠 editor 自己 quit。脚本主动监控：

1. **`Automation Quit` 仍然写**（万一某天 Epic 修了 shutdown 卡的问题）
2. **同时启 polling loop** 检测 `Saved\AutomationReports\index.json` 是否生成
3. **report 出现 → 给 ~30s grace 等 editor 自己干净退**
4. **grace 超时 → force kill editor 进程**（shutdown 阶段被 kill 不影响测试结果，report 已在 "Automation Test Queue Empty" 时就写盘）

完整模式（PowerShell）：

```powershell
# 用 .NET Process 启 editor（async，拿到 Process 对象做超时控制）
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $editorCmdExe
$psi.Arguments = "`"$projectFile`" `"-ExecCmds=Automation RunTests $filter; Automation Quit`" -unattended -nopause -nosplash -nullrhi `"-ReportExportPath=$reportDir`" -log `"-abslog=$logFile`""
$psi.UseShellExecute = $false
$process = [System.Diagnostics.Process]::Start($psi)

$reportPath = Join-Path $reportDir "index.json"
$pollIntervalSec = 5
$absoluteTimeoutSec = 20 * 60       # 兜底硬超时
$gracefulShutdownSec = 30            # report 出现后等 editor 自己退的 grace
$elapsedSec = 0
$testsComplete = $false
$graceStartSec = 0
$forceKilled = $false

while (-not $process.HasExited) {
    if ($elapsedSec -ge $absoluteTimeoutSec) {
        Write-Warning "Editor exceeded absolute timeout (${absoluteTimeoutSec}s) — force killing"
        $process.Kill()
        $process.WaitForExit(5000)
        $forceKilled = $true
        break
    }
    if (Test-Path $reportPath) {
        if (-not $testsComplete) {
            Write-Host "Report detected at ${elapsedSec}s; granting ${gracefulShutdownSec}s grace"
            $testsComplete = $true
            $graceStartSec = $elapsedSec
        }
        if (($elapsedSec - $graceStartSec) -ge $gracefulShutdownSec) {
            Write-Warning "Editor still running ${gracefulShutdownSec}s after report — force killing"
            $process.Kill()
            $process.WaitForExit(5000)
            $forceKilled = $true
            break
        }
    }
    Start-Sleep -Seconds $pollIntervalSec
    $elapsedSec += $pollIntervalSec
}

# 测试结果跟 editor 是否 graceful 退出无关
# - 真卡死（超时 + report 不存在）→ fail
# - 跑完了 editor 卡 shutdown（report 存在 + force kill）→ success
if ($forceKilled -and -not $testsComplete) {
    Write-Error "Editor hung without producing report — test init / framework hang"
    exit 1
}

# 解析 report 检查测试结果（独立逻辑，跟 editor exit code 无关）
$report = Get-Content $reportPath -Raw | ConvertFrom-Json
$failedTests = @($report.tests | Where-Object { $_.state -eq 'Fail' })
if ($failedTests.Count -gt 0) {
    foreach ($t in $failedTests) { Write-Host "FAIL: $($t.fullTestPath)" }
    exit 1
}
```

### `ReportExportPath` flag

UE 5.5 的 Automation report 用 `-ReportExportPath="..."`（旧 flag `-ReportOutputPath` 在 5.5 会 warn）。

报告默认生成 `<ReportExportPath>\index.json`（机器可解析）+ `index.html`（人可读）。CI 解析用 `index.json`：

```powershell
$report = Get-Content "$reportDir\index.json" -Raw | ConvertFrom-Json
$report.tests   # 数组，每个 test 对象有 state / fullTestPath / errors / warnings
$report.succeeded
$report.failed
$report.succeededWithWarnings
$report.notRun
$report.inProcess
```

注意 `index.json` 可能带 UTF-8 BOM。PowerShell `Get-Content -Raw | ConvertFrom-Json` 在 PS 5.1+ 默认 strip BOM，没问题。

### Filter 语法

`Automation RunTests <filter>` 的 filter 是 substring matching：

| 写法 | 含义 |
|---|---|
| `Automation RunTests Foo` | 跑所有 testpath 含 `Foo` 的测试 |
| `Automation RunTests Foo+Bar` | 跑 testpath 含 `Foo` **或** `Bar` 的（`+` 是 OR） |
| `Automation RunTests Foo+Bar+Baz` | 三个 substring 任意匹配 |

源码引用：`Engine/Source/Developer/AutomationController/Private/AutomationCommandline.cpp:134`：

```cpp
StringCommand.ParseIntoArray(ArgumentNames, TEXT("+"), true);
```

多个 Automation 子命令用 `;` 分隔（同文件 line 552）：

```cpp
FString(Cmd).ParseIntoArray(CommandList, TEXT(";"), true);
```

所以完整 ExecCmds：

```
-ExecCmds="Automation RunTests Foo+Bar; Automation Quit"
```

---

## 防御性：CI 跑测试前清残留 editor 进程

跨 pipeline 防御。上次 CI run 中途 fail 时，editor / CrashReportClient 子进程
可能 detach 后继续跑（特别是 GUI subsystem，runner kill job 不一定杀子进程）。
下一次 pipeline 跑时残留进程持有文件锁 / 抢资源。

CI script 启动 editor 之前先清残留：

```powershell
$leftovers = Get-Process | Where-Object {
    $_.Name -match "^(UnrealEditor|UnrealEditor-Cmd|CrashReportClient.*)$"
}
foreach ($p in $leftovers) {
    $runMin = [int]((Get-Date) - $p.StartTime).TotalMinutes
    Write-Host "Killing leftover: $($p.Name) (PID $($p.Id), running $runMin min)"
    try { $p | Stop-Process -Force -ErrorAction Stop }
    catch { Write-Warning "  Failed: $($_.Exception.Message)" }
}
Start-Sleep -Seconds 3   # 等文件句柄释放
```

`CrashReportClient.exe` 是 UE 启动时自动 spawn 的 watcher，每个 editor 进程一对。
**两对 process 意味着 editor 启了两次** —— 通常是历史残留。

---

## 项目实例参考

UE 5.5 dialogue plugin GitLab CI 调试期间踩穿两个 idiom：

- **Idiom 1**: 第一版 CI 用 `UnrealEditor.exe`，job 跑 1h timeout 撞死。测试实际几秒就跑完了（report 已生成）但 GUI editor 进程后台继续跑。换成 `UnrealEditor-Cmd.exe` 后 PowerShell 同步等退出
- **Idiom 2**: 换 Cmd 之后 editor 跑完测试不退出。observed log：`Automation Test Queue Empty` 之后还有 10+ 分钟 EOSSDK / AudioMixer 后台输出。加 PowerShell polling + 30s grace + force kill 解决，整个 stage < 3 min 完成

测试发现：
- Editor 启动 ~30s
- 96 个测试跑完 ~17s
- 30s grace
- force kill ~5s
- 总 ~90s

跟 Job 1h timeout 比 < 2%，CI 加这步 gate 完全无压力。

## 相关 Guidelines / Techniques

- `guidelines/ci-windows/powershell-native-command-pitfalls.md` —— Idiom 2 的 `[Diagnostics.Process]` 调用方式跟 Pitfall 2 关联（Start-Process 不要用）
- `guidelines/ue/build-plugin-limitations.md` —— CI 部署链路上跟 BuildPlugin 一起处理
- `techniques/ci-deploy-to-p4.md` —— CI 完整部署链路的 automation_test stage 标准设计
