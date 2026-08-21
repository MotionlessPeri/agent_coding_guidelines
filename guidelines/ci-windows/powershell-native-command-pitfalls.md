# PowerShell 5.1 调 native command 的五大 pitfall

GitLab Windows shell executor / 任何 PowerShell 写的 CI 脚本，调 `git` /
`p4` / `robocopy` / 别的 .exe 时都可能撞这五个坑。**单纯改 PowerShell encoding
变量都救不了**——必须用 `cmd /c` 包或换 .NET API。

⚠️ **第 4、5 条跟前三条差一层，值得先看一眼**：前三条失败时**会报错**（NCE / 参数被切错 / native 拒绝），
而这两条**让验证链自己给出假绿**——你写了、读回了、两边一致，而落盘的字节是错的。
（第 4 条另有一半是**响亮**的：`git apply` 会当场红，但两条错误信息都指向补丁内容 / 基线，
不指向写它的那支笔 ⇒ 标准处置会再走同一条通道。见该节「响亮不等于会被归对因」。）
⇒ 而第 5 条的暴露面最广：它跟 CI 无关，**任何用 PowerShell 写多行文字的场景**（commit message /
文档 / 注释）都命中，而技术散文里每个标识符都用反引号包。

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

## Pitfall 4: 用 PowerShell 写「会被程序解析的文件」——毁法有**三条独立轴**，而同一行命令换个 session 就换一种毁法

### 现象一：`-Encoding utf8` 写出来的文件带 BOM，而验证链会替它背书

```powershell
"docs: 记一条" | Out-File -FilePath msg.txt -Encoding utf8   # ❌ 文件开头是 EF BB BF
Set-Content msg.txt "docs: 记一条" -Encoding utf8            # ❌ 同样带 BOM
git commit -F msg.txt                                        # commit subject 首字符是 BOM
```

### ⚠️ 为什么它比前三条隐蔽：**"写了→读回→一致"全程通过**

`git log --pretty=%s` 读回来时**把 BOM 吞掉了**，于是：

| 你做的 | 你看到的 |
|---|---|
| 写文件 | 成功，无错 |
| `git commit -F` | 成功，无错 |
| `git log --pretty=%s` 读回核对 | **跟你写的一模一样** ✅ |
| 实际落库的 subject | 首字符是 `U+FEFF` ❌ |

⇒ **这是"缺席有两种成因"的一个实例**（见 [`reporting-limits-and-null-results.md`](../code/reporting-limits-and-null-results.md) 规则 3）：
读回工具对 BOM 是盲的，而"盲"和"没有"产生同一个观测。⇒ **验证 BOM 只能看字节，不能看某个工具的读回结果。**

```powershell
Format-Hex msg.txt | Select-Object -First 1        # 看头三字节是不是 EF BB BF
git log -1 --pretty=%s | Format-Hex                # 看落库的字节，不看它渲染出来的字
```

### ⚠️ 按建议做的人正是会踩的人

PowerShell 5.1 的 `Set-Content` / `Add-Content` **默认走系统 ANSI 代码页**，所以"给它传 `-Encoding utf8`"
是一条**正确且常见**的建议（也是本机 harness 说明里的建议）——它解决的是 ANSI 代码页问题。
**但 5.1 的 `utf8` 就是"UTF-8 with BOM"，没有 no-BOM 的写法**（PS 6+ 才有 `utf8NoBOM` 并把它设为默认）。

⇒ 于是形成一个恶性组合：**为了修一个真问题而采纳的建议，引入了另一个不报错的问题。**

### 现象二：**编码不是一个值，是一个未知量** —— 同一行命令在两个 session 里毁法不同

BOM 只是三条轴里的一条。实测同一行 `git diff > patch`（同一台机器、同一分钟、同一份 diff），
落盘结果**不同**：

| 写法 / 语境 | 落盘编码 | 行尾 | `git apply --check` |
|---|---|---|---|
| `git diff > f` 在裸 `powershell.exe -NoProfile` 子进程 | **UTF-16LE**（`FF FE`，137 个 16-bit 单元里 136 个高位是 `00`）| — | `error: No valid patches in input` （exit 128）|
| `git diff > f` 在一个 agent harness 的 PowerShell 里 | UTF-8 **with BOM**（`EF BB BF`）| **CRLF ×9** | `error: patch failed: a.txt:1` / `patch does not apply` （exit 1）|
| `[IO.File]::WriteAllText` + `UTF8Encoding($false)` | UTF-8 no BOM | LF | ✅ exit 0 |

⇒ 🛑 **「`>` 会写成什么」不是一条可以学一次就依赖的知识** —— 它取决于那个 session 的
`$PSDefaultParameterValues` / `$OutputEncoding` / profile，而这些**不是你设的**。
⇒ 所以规矩只能写成**别用这条通道**，不能写成"记得配对编码"。

### ⚠️ 这两次都是**响亮**的失败 —— 而报错指向的方向是错的

跟 BOM 那半（静默、验证链背书）相反，这两次 `git apply` 都当场红了。但两条错误信息
**都在说补丁内容 / 目标文件**，没有一条提到写它的那支笔：

| 你看到的 | 你会去查 | 真因 |
|---|---|---|
| `No valid patches in input` | 「diff 是不是空的 / 我导出错了」 | 整份文件是 UTF-16LE，解析器一个 hunk 都认不出来 |
| `patch does not apply` | 「基线漂了 / 分支不对 / 该 `-3` 合」 | 目标与基线都对，是补丁的行尾被换成了 CRLF |

⇒ ⭐ **响亮不等于会被归对因**。第二条尤其贵：`patch does not apply` 是一个人**每周都会正当地
遇到**的错误，它的标准处置（换基线、加 `-3`、重导一次）**全部都会再走同一条通道**。
⇒ 判据：**收到"补丁不适用"时，先看补丁的头三字节和行尾，再去怀疑基线。** 一条命令的事。

### 修法：绕开 PowerShell 的 encoder，直接写字节

```powershell
[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
```

跟 Pitfall 3 同一个 API、同一个 `$false`（关 BOM）。⇒ **PS 5.1 上凡是"文件内容会被别的工具按字节读"，
一律用 `WriteAllText` + `UTF8Encoding($false)`，不要用 `Out-File` / `Set-Content` 的 `-Encoding utf8`。**

它同时治掉三条轴：BOM 由 `$false` 关掉，编码由你指定（不再由 session 决定），**行尾由字符串
自己决定**（`WriteAllText` 不做任何行尾转换 —— 你给 `\n` 它就写 `\n`）。

（只给人看、不被工具解析的文件无所谓；判据是**下游有没有按字节解析它**。）

⚠️ **这条修法自己带一个坑：.NET API 不认 PowerShell 的当前目录。**
`WriteAllText` 收到**相对路径**时用的是**进程** cwd，`Push-Location` / `Set-Location` 对它无效
⇒ 文件静默落在别处，而后续 `git diff` 只会诚实地报「没有改动」。
实测形态：`Push-Location $repo; [IO.File]::WriteAllText("a.txt", …)` 把文件写进了**进程启动时**
那个目录（那次恰好是一棵用户明令不许动的树），而探针自己报的是「diff 为空」——
**指向的是被测对象，不是路径**。⇒ **给 .NET API 一律传绝对路径。**

### ⭐ 更省事的一档：**产物来自某个工具时，让那个工具自己写文件**

`WriteAllText` 要你手动拼内容。而很多产物本来就是某个 native 工具生成的 —— 那就别让它经过 shell：

| 别写 | 改写成 | 为什么 |
|---|---|---|
| `git diff > f` | `git diff --output=f` | **git 自己写字节**，整条 shell 重定向层被绕开 |
| `git format-patch … > f` | `git format-patch -o <dir>` | 同上 |
| `<exe> … > f` | 该 exe 自己的 `-o` / `--output` / `--out-file` | 同上 |

⇒ 判据：**先找那个工具有没有「自己写文件」的参数**；有就用它，不需要记任何编码参数。
⚠️ 只在产物由工具生成时适用。**内容是你自己拼的**（commit message / 文档 / `.py`）仍然要
`WriteAllText` + `UTF8Encoding($false)` + 绝对路径。

---

## Pitfall 5: **反引号是转义符**，而技术散文里到处都是反引号

### 现象（最小复现，实测）

同一段话，只差 here-string 的引号种类：

```powershell
$double = @"
改的是 `ast.walk`，不是 `asset_create`；`take_file` 与 `viewport` 也一样。
"@
$single = @'
改的是 `ast.walk`，不是 `asset_create`；`take_file` 与 `viewport` 也一样。
'@
```

落盘之后：

```
@"…"@   改的是 <BEL>st.walk，不是 <BEL>sset_create；<TAB>ake_file 与 <VT>iewport 也一样。   反引号 0 个
@'…'@   改的是 `ast.walk`，不是 `asset_create`；`take_file` 与 `viewport` 也一样。        反引号 8 个 ✅
```

**两份都"写成功"，零报错零警告。**

### 机制

PowerShell 的反引号 `` ` `` 相当于 C 的反斜杠。**在双引号语境**（`"…"` 与 `@"…"@`）里它吞掉自己并转义下一个字符：

| 写的 | 落盘的 |
|---|---|
| `` `a ``bc | **BEL**(0x07) bc |
| `` `t ``ake | **TAB** ake |
| `` `v ``iew | **VT**(0x0B) iew |
| `` `n `` / `` `r `` / `` `f `` / `` `b `` / `` `e `` / `` `0 `` | LF / CR / FF / BS / ESC / NUL |
| `` `m ``odel | model —— **反引号直接消失**，字母留着 |

⚠️ **暴露面不是"偶尔"，是"一写就中"**：技术散文用反引号包每一个标识符（`` `ast.walk` `` /
`` `take_file` ``），而 commit message、设计文档、注释全是这种文字。

### ⚠️ 为什么它静默：三层各自都有正当理由不报

| 层 | 为什么不报 |
|---|---|
| PowerShell | 转义是**合法语法**，它以为你就想要一个制表符 |
| 写入 | 产物是**格式良好**的字符串，只是不是你写的那个 |
| 下游 | 落在注释 / docstring / commit message 里 ⇒ **语法有效** ⇒ 编译、测试、审计全绿 |

而丢的东西**在屏幕上看不见**：BEL / VT / FF 不显示，少掉的反引号读起来也很自然。

### 🛑 三种检测手段里只有一种可用（这一节比结论更重要）

拿到这条知识的人，第一反应就是去数反引号或去比对原稿。**那两条正是踩过的人各自试过的，而它们都错**：

| 检测手段 | 结果 | 为什么不可用 |
|---|---|---|
| 数反引号（"长文本零反引号 = 受损"） | **高报** | 它测的是**写作风格**。实测 120 条 commit message 里命中 35 条，而真受损 4 条 |
| 比对"我原本写的那份文件" | **低报** | 那份文件**也是同一条通道写出来的** ⇒ 参照物与被测物一起被压短 ⇒ 差为 0 |
| **扫控制字符** | ✅ | 无歧义、不依赖任何人的写作习惯、第三方可复核 |

```python
BAD = "\x00\x07\x08\x0b\x0c\x1b\x1a"     # NUL BEL BS VT FF ESC SUB
hits = [(p, [c for c in BAD if c in p.read_text(encoding="utf-8")]) for p in files]
```

⭐ 中间那条尤其值得记：**它的失败形态是"一切正常"** —— 你建了一个看起来独立的 oracle
（"我意图写入的原稿" vs "实际落盘的"），而它报 0 丢失。⇒ 这是
[`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)
"对照组自己也需要被验"在**通道**这一维上的形态：**对照组不存在时你会发现（拿不到数）；
对照组存在但走了同一条被怀疑的通道时，你得到一个干净的数字。**
⇒ ⇒ 判据：**建 oracle 要问的不只是"它独立于我的推理吗"，还有"它独立于那条正在被怀疑的通道吗"。**

### 修法

1. **首选：不要用 PowerShell 写内容。** 用专门的写文件工具落盘，PowerShell 只负责跑命令。
   （实测对照：同一晚、同一个人、同样的内容，走文件工具 + `git commit -F` 的 8 条**反引号一个没丢**
   （64 / 60 / 58 …），走 PowerShell 内联 here-string 的 5 条**全军覆没**。通道是唯一变量。）
2. 必须在 PowerShell 里写：用**单引号** here-string `@'…'@`（字面量，不转义）。
   ⚠️ 代价是它不能插变量 —— 而"想插变量"正是人选双引号那种的原因。
3. 写完**扫一遍控制字符**（上面那段），别信读回。

⚠️ **别把"用 `-c`/内联传脚本给 native exe"当退路**：PowerShell 传参给 native exe 时还会
**剥掉内嵌的双引号**（`("a", "b")` → `(a, b)`）⇒ 那次是**响亮的** SyntaxError。
⇒ ⭐ 于是同一条通道有**三种表现**：① 静默毁内容 ② 响亮 SyntaxError（转义把脚本弄坏）
③ 响亮 SyntaxError（剥引号）。**两种响法会让人给自己发合格证** ——
实测的时间线是：先撞了两次响的、改成写文件，**然后才发现静默那次早就发生了**。

### 证据分档（促升时按这个读，别把三档并成一个数）

| 档 | 内容 |
|---|---|
| **硬证据**（控制字符，第三方可复核） | 4 条 commit message + 一份 durable 文档 3 处 + 另一份源码文件 2 处（后者溯到更早的会话，**此前无人发现**） |
| **仅作者可证**（反引号丢失） | 另 5 条 commit message —— 真实但**不可独立核验**（唯一参照副本已被同一通道污染） |
| **无证据**（已撤回） | 曾按"零反引号"判定的另外 4 条，实为写作风格 |

⚠️ **三个独立命中分属不同会话 / 不同 agent，没有一次是被人读出来的** ——
两次靠扫控制字符，一次靠有人恰好去清理。⇒ 它是**通道的性质，不是谁的疏忽**。

### ⭐ 附带的一条(给促升本身的)

上面那张"三种检测手段"表是在**为这一条促升凑证据**的过程中打出来的：三个量具错，方向各不相同
（判据过宽 → 高报 / 扫描范围过窄 → 低报 / 参照物同源污染 → 低报且最可信）。
⇒ 📌 **给促升凑证据时，量具本身要先自证** —— 这是"量具先自证"在**语料层**的应用。
⇒ ⇒ 而**最可信的那个错得最深**：范围过窄那次一看就知道要补，参照物同源污染那次
**看起来是一份原稿**。

---

## 五个 pitfall 的统一形态

五个坑底层是同一个 PowerShell 5.1 quirk：**native command 的 stdin/stderr/文件字节 跟 PowerShell 自己的 encoder 与 parser 之间有抽象漏洞**。

⚠️ 而**第 4、5 条跟前三条差一层**：前三条失败时会报错（NCE / 参数被切错 / native 拒绝），
后两条**让验证链自己给出假绿** —— 你写了、读回了、两边一致，而落盘的字节是错的。

修法都是**绕过 PowerShell 这一层**：

| Pitfall | 绕过点 |
|---|---|
| 1. stderr → NCE | 用 `cmd /c "exe 2>&1"` 让 cmd 在子进程合并 stderr→stdout |
| 2. ArgumentList 引号 bug | 用 `[Diagnostics.Process]` + 单 string Arguments 自己控引号 |
| 3. stdin BOM | 用临时文件 + `cmd /c "exe < file"` 绕过 PS pipe encoder |
| 4. 写文件的 BOM / 编码 / 行尾（三条独立轴，且随 session 变）| 用 `[IO.File]::WriteAllText` + `UTF8Encoding($false)` + **绝对路径** 绕过 PS 文件 encoder |
| 5. 反引号被当转义符 | **别用 PowerShell 写内容**（用专门的写文件工具）；退而求其次用 `@'…'@` |

**没有"PowerShell 配置一行就根治"的方案**。每个具体场景都要选对应绕过方式。

⚠️ **但第 4 条多一层教训**：前三条你会被报错逼着去修，第 4 条**要靠你事先知道**——因为它的失败
形态是"验证通过而结果是错的"。⇒ 凡是 PowerShell 写出来、由别的工具按字节解析的文件，
**不要用它的读回结果当验证**，看字节（`Format-Hex`）。

## 防御性约定（适合写进项目 AGENTS.md）

PowerShell CI 脚本里调 native command 时遵守：

1. **任何会在"无操作"/"已完成"状态写 stderr 的 native command，必须 `cmd /c "... 2>&1"` 包**（p4 / git 等多数 VCS 工具都属于）
2. **子进程需要监控 / 超时 / kill 时，用 `[Diagnostics.Process]` 不要用 `Start-Process`**
3. **通过 stdin 给 native exe 喂 multi-line text 时，用临时文件 + `cmd /c "exe < file"` 不要用 PowerShell `|` pipe**
4. **简单调用阻塞执行可以用 `& exe arg1 arg2`**，PS native parser 正确处理空格
5. **写"会被别的工具按字节解析"的文件时，用 `[IO.File]::WriteAllText` + `UTF8Encoding($false)` + 绝对路径**，
   不要用 `>` / `>>` / `Out-File` / `Set-Content -Encoding utf8`（5.1 上 `utf8` 就是带 BOM；
   `>` 写成什么**由 session 决定**，实测同一行命令一处给 UTF-16LE、一处给 UTF-8+BOM+CRLF）。
   **验证看字节，不看读回**；收到"补丁不适用 / 解析不出"先看头三字节和行尾，再怀疑基线
6. **写"人要读的多行文字"（commit message / 文档 / 注释）时，不要用 PowerShell 写** ——
   用专门的写文件工具落盘，PowerShell 只负责跑命令。必须在 PS 里写就用 `@'…'@`，
   写完**扫一遍控制字符**。理由:反引号是转义符,而技术散文里每个标识符都用反引号包

加新 native command 调用时先想清楚走哪条路径，不要等 CI 跑挂了再来改。

## 项目实例参考

UE 5.5 plugin 的 GitLab CI 调试期间踩穿三个坑：

- **Pitfall 1**: `automation_test` stage 里 `p4 sync //...` 在 client 已 up-to-date 时撞 NCE。修法走 `cmd /c "p4 sync //... 2>&1"`
- **Pitfall 2**: `automation_test` 跑 UnrealEditor-Cmd 时用 `Start-Process -ArgumentList @(...)`，`-ExecCmds="Automation RunTests Filter1+Filter2; Automation Quit"` 被切错，UE Editor 只收到 `Automation` 一个 token。修法换 .NET ProcessStartInfo + 单 string Arguments
- **Pitfall 3**: `deploy` stage 里 `$clientSpec | p4 client -i` 撞 BOM，p4 报 `Unknown field name '﻿Client'`。修法走临时文件 + cmd `<` redirect

三个坑实测验证脚本：`Scripts/CI/test-p4-stdin-bom.ps1` / `test-p4-client-i-bom.ps1` / `test-p4-stderr-nce.ps1`（本地复现 + 验证修法）。

**第二个项目（Windows 上的 Python + 原生扩展桌面应用，多条 agent 对话并发同一仓）——
Pitfall 4 在这里跟 CI 完全无关地复发了**，而且暴露面比 CI 大：它命中的是**日常开发动作**。

| 命中 | 落点 |
|---|---|
| BOM ×4 | 一个 `.py` 源文件、两条 commit message、另一条 lane 在 `tools/` 下的产物（**溯到更早的会话，此前无人发现**）|
| 行尾 ×1 | 递给另一条 lane 的补丁带 62 个 CRLF ⇒ 对方 `git apply` 失败 |
| UTF-16LE ×1 | 复现实验里 `git diff > f` 在裸 `powershell.exe` 子进程整份写成 UTF-16LE |
| **编码+行尾 ×1（另一条 lane，独立命中）** | 另一条 lane 用 `>` 写一份 patch ⇒ `git apply --check --reverse` **当场失败**（`patch does not apply`）；换成 `git diff --output=<file>`（git 自己写、不经 shell）后通过 |

⚠️ **这里有一个促升本身的边界，值得写下来**：这条规矩的"错误建议源头"是
**agent harness 自己的 PowerShell 工具说明**（它正当地建议 `-Encoding utf8` 来治 ANSI 代码页），
**而那份说明不在本语料仓里** ⇒ 改语料改不到源头。
⇒ 所以这条只能以**反制规则**的形态存在（"别走这条通道"），不能指望上游那句建议被改掉；
也因此它必须写得足够显眼，让读到语料的人在读到那句建议时能想起来。

**诚实边界**：BOM 那一轴已**跨 2 项目**命中（UE/P4 的 CI + 上面这个），满足两击；
行尾与 UTF-16LE 两轴仍是**单项目**（表里第 2、3、4 行同属上面那个项目，只是分属不同 lane
⇒ **不满足跨项目两击**），但都有当场实测的字节与 `git apply` 退出码，
且"编码随 session 变"这一条是**对照实验**（同分钟、同 diff、只换 session）得出的，不是推断。
apply-and-refine。

⭐ **而第 4 行那次复发带来一条比"又中一次"更有用的东西：坏的形态跟前一次不一样。**
第 2 行是纯行尾（62 个 CRLF），第 4 行是编码与行尾一起坏。⇒ 这正好否掉一个看起来更省事的
写法：**反制不能写成"记得同时管 BOM 和行尾"** —— 那种写法只覆盖你**见过的**那几样，
而这条通道每换一个 session 就可能给一种没见过的坏法。⇒ **只能写成"别走这条通道"。**
（⚠️ 那次复发的经过也值得记：写规则的那条 lane 把"两条轴要分别记得"这个**理由**转述给了第三方，
第三方照抄；后来是对照实验推翻了理由、而**动作**一直是对的。⇒ 与
[`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)
"断言正确、解释错误的 check 比没有解释更糟"同形：**理由错的规则只有跨到第二个场景才暴露，
在第一个场景里永远看起来是对的。**）

ℓ **第 4 行是被机械自检抓住的，不是人看出来的** —— `git apply --check --reverse` 当场红。
⇒ 这条通道的产物若要递给别人，**递之前先让接收侧的工具 dry-run 一次**（`git apply --check`
之类），比任何字节自查都便宜。

## 相关 Guidelines / Techniques

- `guidelines/code/validation.md` —— 强调"verify before claim done"，本文是 CI 验证的具体 pitfall 索引
- `guidelines/workflow/agent-lifecycle.md` —— 列了 "Probably fine" 类自欺欺人；CI 出错时容易凭推测改，应该走"本地复现 → 实测 → 改"的严格流程
