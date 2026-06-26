# Windows 自托管 gitlab-runner（服务环境）+ PowerShell 脚本的坑

Windows 自托管 gitlab-runner（shell executor，以**服务**形式运行）+ PowerShell 跑 CI 时，一组跟
**「服务进程的环境」**和**「PowerShell 退出码 / 类型语义」**相关的坑。跟
[`powershell-native-command-pitfalls.md`](powershell-native-command-pitfalls.md)（PS ↔ native exe 的抽象漏洞）
是兄弟篇——那篇管「调 native 命令」，本篇管「runner 服务看到的环境」+「PowerShell 脚本自身的退出码/拆包陷阱」。

共同特征：**交互式登录 shell 里一切正常，CI job（服务上下文）里挂**——因为 gitlab-runner 服务跑在某服务账号下、
启动时定死环境，看不到你登录会话的盘映射 / 实时 PATH。排查时**别只在自己的交互 shell 验，真实判据是 CI job**。

## 核心规则

1. **CI 里任何网络路径用 UNC（`\\server\share\...`）不用盘符**——服务看不到交互会话映射的盘。
2. **System PATH 改完必须 `Restart-Service`**——服务启动时才读环境；且当心 WindowsApps「应用执行别名」存根挡道。
3. **PowerShell `& script.ps1` + `if ($LASTEXITCODE)` 判成败：脚本成功路径若全是 cmdlet，须显式 `exit 0`**。
4. **单元素 `$x -split ... | Where-Object {...}` 会被拆包成标量字符串**——`$x[0]` 取的是首字符不是首元素，用 `@()` 包。

---

## 1. 服务看不到交互映射盘 → 用 UNC

### 现象
CI 脚本访问网络盘（`I:\...`）报 `Cannot find drive. A drive with the name 'I' does not exist.`
（`DriveNotFoundException`）——但你**登录到 runner 机器交互运行同样命令是好的**（你的会话里 `I:` 映射着）。

### Root cause
gitlab-runner 以**服务**形式跑（某服务账号），Windows **服务进程不继承交互登录会话的盘符映射**
（`net use` / 资源管理器映射是 per-logon-session 的）。所以服务上下文里 `I:` 不存在。

### 修法：UNC
把路径从盘符改成 UNC（服务账号有该 share 网络访问权即可，**不需要盘映射**）：
```powershell
# ❌ I:\proj\out          ——服务看不到 I:
# ✅ \\server\share\proj\out
```
查盘符对应的 UNC：`Get-PSDrive <Letter>`（看 `DisplayRoot`）或 `net use`。
yml 里写 UNC 用**单引号**：双引号里 `\t`/`\n` 会被 YAML 当转义毁掉路径。

> 同理：rez / 包仓库 / 任何 CI 依赖若在网络盘，服务也读不到——要么 UNC、要么把依赖放本地盘、要么前台
> `gitlab-runner run`（继承你交互会话的映射，但非长久服务方案）。

## 2. System PATH 改完要重启服务 + WindowsApps 别名挡道

### 现象 A：PATH 改了 CI 还报找不到命令
在 runner 上把 `python` / `cmake` 等加进 System PATH，CI job 仍 `not recognized` / 找不到。

**Root cause**：服务**启动时**快照环境变量。改 System PATH 后，正在跑的服务还是旧 env。
**修法**：`Restart-Service <runner-service>`（或重启机器）后服务才看到新 PATH。且必须加 **System(Machine)** PATH——
服务账号不读你交互用户的 User PATH。

### 现象 B：`python` 报 `The system cannot find the path specified`（不是 not recognized）
PATH 上**找到了** `python.exe` 但启动失败，报「找不到指定的路径」。

**Root cause**：Windows 的 **App Execution Alias** 存根（`%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`，
指向 Microsoft Store 的 0 字节 reparse point）。没装 Store python 时一跑就报这个错，且它常**排在真 python 前面**
（WindowsApps 在 PATH 里靠前）。多用户机器上**别的账号**（如 Administrator）的 WindowsApps 也可能在 PATH 最前。

**修法**：
- 关掉别名：设置 → 应用 → 高级应用设置 → 应用执行别名 → 关 `python.exe`/`python3.exe`；或删存根文件。
- **更稳**：把真 python 目录**前插**到 System PATH 最前（盖过任何靠后的坏 python / 别名），再重启服务。
- 验证：`where.exe python` **第一行**应是真 python（`where` 列全部匹配，第一个才是会被跑的）。

## 3. `& script.ps1` + `$LASTEXITCODE` 判成败 → 脚本须显式 `exit 0`

### 现象
yml 里 `& .\foo.ps1; if ($LASTEXITCODE -ne 0) { exit 1 }`——`foo.ps1` 明明成功跑完（打了成功日志），
job 却报失败。

### Root cause
`$LASTEXITCODE` **只被 native 程序（exe）设置，cmdlet（Copy-Item / Test-Path / New-Item …）不设**。
若 `foo.ps1` 成功路径**全是 cmdlet、且结尾没 `exit`**，调用后 `$LASTEXITCODE` 停在**之前的陈旧值或 `$null`**。
而 PowerShell 里 **`$null -ne 0` 求值为 `True`** → `if ($LASTEXITCODE -ne 0)` 误判失败。

### 修法
被 `&` 调用、且调用方用 `$LASTEXITCODE` 判成败的 `.ps1`，**成功路径结尾显式 `exit 0`**（失败路径 `exit 1`）：
```powershell
# foo.ps1 末尾
Write-Host "done"
exit 0     # 没有它，调用方 $LASTEXITCODE 可能是 $null → $null -ne 0 = True → 假失败
```
（脚本里若有 native 命令如 `cmd /c "...";` 成功后 `$LASTEXITCODE`=0，碰巧不挂——但别依赖这种巧合，统一 `exit 0`。）

## 4. 单元素 `-split | Where-Object` 拆包成标量 → `[0]` 取首字符

### 现象
```powershell
$versions = $env:VERS -split '\s+' | Where-Object { $_ }   # VERS="2024"
$dir = "build_$($versions[0])"                              # 期望 build_2024，实得 build_2
```

### Root cause
`"2024" -split '\s+'` 返回单元素数组 `@("2024")`，但**经 `| Where-Object` 管道后，单元素结果被 PowerShell
拆包成标量字符串** `"2024"`。对字符串索引 `[0]` → **首字符 `"2"`**。

### 修法
用 `@(...)` 强制成数组：
```powershell
$versions = @($env:VERS -split '\s+' | Where-Object { $_ })  # 永远是数组
$versions[0]                                                  # "2024" ✓
```
（`foreach ($x in $scalar)` 对标量只迭代一次、拿到整串，所以 foreach 场景通常不挂；挂的是 `[index]` 取元素。
为一致+安全，凡是要按元素用的，统一 `@()`。）

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| CI 用盘符路径访问网络盘 | 服务 `DriveNotFound` | 改 UNC |
| 改 System PATH 不重启 runner 服务 | 服务用旧 env，CI 还找不到命令 | `Restart-Service` |
| 把命令缺失当「没装」反复装 | 其实是 WindowsApps 别名挡道 / PATH 顺序 | `where.exe` 看第一个解析到谁；前插真路径 + 关别名 |
| `& ps1` 成功路径全 cmdlet 不 `exit 0` | `$LASTEXITCODE`=$null → 假失败 | 脚本显式 `exit 0` |
| `($x -split .. \| Where ..)[0]` | 单元素拆包成标量，取首字符 | `@(...)` 包 |
| 只在交互 shell 验「好了」就以为 CI 也好 | 服务上下文环境不同 | 真实判据是 CI job |

## 项目实例参考

某 Maya C++ 插件在 Windows 自托管 gitlab-runner（shell executor，服务形式，复用自另一项目的 runner）
首次 bring-up 时一条 tag 跑通前**四条全踩**：

- deploy 写网络盘 `I:\...` 报 `DriveNotFound`——服务看不到交互映射的 `I:`；改 `\\<server>\<share>\...` UNC 后通。
- `python` 先报 `not recognized`（PATH 没加），加 System PATH 后**重启服务前**仍挂；重启后又报
  `cannot find the path specified`——WindowsApps 别名 + 别的账号的 WindowsApps 排 PATH 最前；前插真 python 目录 + 删存根后通。
- deploy 脚本（全 cmdlet：Copy-Item / New-Item / Test-Path）**实际成功**（文件已落盘）但 job 假失败——
  `$LASTEXITCODE` 停在 `$null`，`$null -ne 0`=True；脚本末尾补 `exit 0` 后通。
- 多版本 build 脚本 `$versions[0]` 在单版本（`"2024"`）下取成 `"2"`（`build_2`）——`-split | Where` 拆包成标量；`@()` 包后通。

兄弟篇 `powershell-native-command-pitfalls.md` 的 PS↔native 三坑则来自另一项目（UE 插件）的 Windows runner CI——
同一类「Windows 自托管 runner + PowerShell CI」环境，两个项目分别踩到不同子集。

## 相关 Guidelines / Techniques

- [`powershell-native-command-pitfalls.md`](powershell-native-command-pitfalls.md) —— 兄弟篇：PS ↔ native exe（NCE / stdin BOM / ArgumentList 引号）。本篇是「服务环境 + PS 脚本退出码/类型」维度。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 「服务上下文 ≠ 交互 shell」正是「别在错的环境取证」的实例：真实判据是 CI job，不是登录 shell。
- [`../code/validation.md`](../code/validation.md) —— 「看着对 ≠ 验证」；交互 shell 验通不代表服务上下文通，必须 CI 实跑。
