# CI 自动 submit 到 P4 server 的标准流程

把 CI build artifact 通过 `p4 submit` 部署到 P4 depot 让接收方 sync 即用。
比起拷到网络共享 / FTP，P4 部署能让接收方走标准 sync 流程拿增量更新 + 历史 revision。

本 technique 假设：
- CI runner 是 Windows（PowerShell 5.1）
- 部署目标是 P4 unicode-enabled server
- 接收方 client 可能用任意 charset（cp936 / utf8 / 其他）
- 每个新版本是新 depot 子目录（不覆盖历史版本）
- rerun 同 tag 时覆盖同名子目录（幂等）

依赖的 guidelines：

- `guidelines/p4/charset-pitfalls.md` — 为什么要强制 binary
- `guidelines/ci-windows/powershell-native-command-pitfalls.md` — PS 5.1 调 p4 必须 `cmd /c` 包
- `guidelines/workflow/agent-lifecycle.md` — 失败处理

---

## Stage 流程总览

```
入口（CI yaml 的 deploy stage）
  ├── Step 1: 切 P4 env + login（凭据走 CI secret variable）
  ├── Step 2: ensure workspace 存在（p4 client -i 幂等 create-or-update）
  ├── Step 2.5: 防御性 revert（清上次 partial run 残留）
  ├── Step 3: sync 现有 depot 内容到 workspace
  ├── Step 4: 物理删本地目标版本目录（让 reconcile 后面能 detect delete）
  ├── Step 5: 拷新内容到 workspace
  ├── Step 6: p4 reconcile -ead 检测 add/edit/delete
  ├── Step 7: 强制 reopen 关键扩展名为 binary
  └── Step 8: p4 submit（"No files to submit" 视为 success）
```

每个 step 都有跨项目通用的 idiom，下面一个一个列。

---

## Step 1: 切 P4 env + login

CI runner 可能同时连**多个 P4 server**（如 dev server 跑 sync stage，deploy
server 跑 submit）。临时切环境变量到部署 server：

```powershell
$env:P4PORT = $env:P4_DEPLOY_PORT                # 部署 server 地址
$env:P4USER = $env:P4_DEPLOY_USER                # 通常专门的 CI bot 账号
$env:P4CHARSET = "utf8"                          # 强制 utf8，详 charset-pitfalls.md
$env:P4CLIENT = $env:P4_DEPLOY_CLIENT_NAME       # CI 用的 workspace 名

# login（密码走 CI secret variable）
cmd.exe /c "echo $env:P4_DEPLOY_PASSWD| p4 login" 2>&1 | Write-Host
if ($LASTEXITCODE -ne 0) {
    Write-Error "P4 login failed"; exit 1
}
```

⚠️ **关键点**：

1. **`P4CHARSET=utf8`** —— CI 端 sync 出来的本地字节是 UTF-8。submit 上去的也是 UTF-8（如果文件标 binary 就是原字节）
2. **`P4_DEPLOY_PORT` / `P4_DEPLOY_PASSWD` 走 GitLab CI Variable**（secret），不能写在 yaml 里。如果 Variable 勾了 `Protected`，**tag pattern 必须 protected**（GitLab Settings → Repository → Protected tags 加 `v*`）
3. `echo $passwd | p4 login` 必须 `cmd.exe /c` 包，否则 PowerShell pipe encoding 出问题（PS 把 `Write-Output` 默认加 newline，p4 把 newline 当密码一部分）

---

## Step 2: Ensure workspace 存在

不预先在 runner 上手动建 workspace。yaml 里**幂等 create-or-update**：

```powershell
$wsRoot = $env:P4_DEPLOY_WS_ROOT
New-Item -ItemType Directory -Force -Path $wsRoot | Out-Null

# 注意：P4 client spec 的 View 段每行必须以 TAB 开头（不能用空格）
$tab = [char]9
$clientSpecLines = @(
    "Client: $env:P4CLIENT",
    "Owner: $env:P4USER",
    "Host: $env:COMPUTERNAME",
    "Description:",
    "$($tab)CI auto-deploy. Managed by GitLab pipeline; do not edit manually.",
    "Root: $wsRoot",
    "Options: noallwrite noclobber nocompress unlocked nomodtime normdir",
    "SubmitOptions: submitunchanged",
    "LineEnd: local",
    "View:",
    "$($tab)//depot/path/to/deploy/root/... //$env:P4CLIENT/..."
)
$clientSpec = $clientSpecLines -join "`n"

# 必须用临时文件 + cmd < redirect 喂 p4 client -i 的 stdin，不能用 PS pipe
# 详 guidelines/ci-windows/powershell-native-command-pitfalls.md Pitfall 3
$tmpSpec = Join-Path $env:TEMP "p4_client_spec_$env:CI_PIPELINE_ID.txt"
[System.IO.File]::WriteAllText($tmpSpec, $clientSpec, (New-Object System.Text.UTF8Encoding $false))
try {
    cmd /c "p4 client -i < `"$tmpSpec`"" 2>&1
    $exitCode = $LASTEXITCODE
} finally {
    Remove-Item $tmpSpec -ErrorAction SilentlyContinue
}
if ($exitCode -ne 0) {
    Write-Error "p4 client -i failed (exit $exitCode)"; exit 1
}
```

⚠️ **关键点**：

1. **`Options: noallwrite noclobber ...` + `LineEnd: local`** 是 P4 标准 client options，可以直接抄
2. **`SubmitOptions: submitunchanged`** —— submit 所有 opened files 即使没改（防 reopen -t binary 这类"只改 type"操作被自动 revert）
3. **View 段每行必须 TAB 开头**——空格 P4 拒收
4. **PS 5.1 数组 + `-join "\`n"`**——不要用 here-string `@"..."@`，跟 yaml block scalar 缩进打架
5. **临时文件 + cmd `<` redirect 喂 stdin**——不能 `$spec | p4 client -i`（会插 BOM）
6. **`CI_PIPELINE_ID` 后缀**避免并发 pipeline 冲突

---

## Step 2.5: 防御性 revert

上次 partial run 失败时，workspace 可能留一堆 opened pending changes。下次跑
reconcile 会撞历史残留。开局先无脑 revert：

```powershell
cmd /c "p4 revert `"//$env:P4CLIENT/...`" 2>NUL"
$global:LASTEXITCODE = 0   # 没文件可 revert 时 exit 1，可接受
```

⚠️ **关键点**：

1. **`2>NUL` 吞 stderr**——`p4 revert` 没文件可 revert 时写 stderr `"File(s) not opened on this client."`，这是预期的"无操作"warning 不是错误
2. `$global:LASTEXITCODE = 0` 接受 non-zero exit code

revert 是无副作用的——有 pending 就清，没有就 no-op。每次 deploy 开局都做，幂等。

---

## Step 3: Sync 现有 depot 内容

```powershell
cmd /c "p4 sync `"//$env:P4CLIENT/...`" 2>&1"
$global:LASTEXITCODE = 0   # "file(s) up-to-date" 时 exit 1，可接受
```

⚠️ **关键点**：

1. **`cmd /c "... 2>&1"`** 而不是 `p4 sync ... 2>&1 | Out-Host`——后者 NCE 拦不住
2. sync 行为：rerun 同 tag 时拉旧版本目录的内容到 workspace，让 reconcile 后面能比较 diff
3. 第一次 deploy 时这个 sync 可能拉几 GB 数据（如果 depot 已有别人上传的历史版本），time 比较长

如果想避免 sync 整个 view 浪费时间，可以缩到当前版本目录：

```powershell
cmd /c "p4 sync `"//$env:P4CLIENT/MyProject_$version/...`" 2>&1"
cmd /c "p4 sync `"//$env:P4CLIENT/MyProject_${version}_Sample/...`" 2>&1"
```

但是这样如果**当前版本目录在 depot 不存在**（首次部署 / rerun），sync 报"no
files in path"。需要再 cmd /c 包吞 stderr。trade-off。

---

## Step 4: 物理删本地目标版本目录

让 `p4 reconcile -d` 后面能 detect "depot 有但本地没有"的文件 = mark delete：

```powershell
$pluginDeployDir = Join-Path $wsRoot "MyProject_$version"
$sampleDeployDir = Join-Path $wsRoot "MyProject_${version}_Sample"

foreach ($dir in @($pluginDeployDir, $sampleDeployDir)) {
    if (Test-Path $dir) {
        # P4 sync 出来 read-only，先清属性才能删
        Get-ChildItem -Recurse $dir -File -ErrorAction SilentlyContinue |
            ForEach-Object { $_.IsReadOnly = $false }
        Remove-Item -Recurse -Force $dir
    }
}
```

⚠️ **关键点**：

- **P4 sync 出来文件默认 read-only**（client option `noallwrite`），`Remove-Item` 默认拒删——必须先 clear read-only
- 只删**当前版本子目录**，不动其他版本（如 `MyProject_0.5.4/` / `MyProject_0.5.4_Sample/`）

---

## Step 5: 拷新内容到 workspace

```powershell
# Plugin / artifact 直接 Copy-Item
Copy-Item -Recurse -Force $artifactDir $pluginDeployDir

# Sample 项目用 robocopy 排除 build 产物
$robocopyArgs = @(
    $stagingDir, $sampleDeployDir, "*",
    "/E", "/XD", "Saved", "Intermediate", ".git",
    "/NFL", "/NDL", "/NP",
    "/R:2", "/W:5"
)
& robocopy @robocopyArgs
if ($LASTEXITCODE -ge 8) {
    Write-Error "robocopy failed with exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
}
$global:LASTEXITCODE = 0   # robocopy exit 0-7 都是成功

# 清新拷文件的 read-only 属性（reconcile 不要 read-only 文件）
Get-ChildItem -Recurse $pluginDeployDir -File | ForEach-Object { $_.IsReadOnly = $false }
Get-ChildItem -Recurse $sampleDeployDir -File | ForEach-Object { $_.IsReadOnly = $false }
```

⚠️ **关键点**：

1. **robocopy exit code 语义**：0 = 无文件复制（success），1-7 = 正常成功（有不同程度的变化），≥ 8 = 错误。**0-7 都 reset `$LASTEXITCODE = 0`**
2. `/XD Saved Intermediate .git` 排除 build 脏目录
3. 拷完**必须 clear read-only**——CI runner 上源文件可能本身 read-only（如 P4 sync 来的），保留属性会让 `p4 reconcile -e` 不 detect edit

---

## Step 6: `p4 reconcile -ead` 检测 add/edit/delete

```powershell
$pluginDepotPath = "//$env:P4CLIENT/MyProject_$version/..."
$sampleDepotPath = "//$env:P4CLIENT/MyProject_${version}_Sample/..."

cmd /c "p4 reconcile -ead `"$pluginDepotPath`" 2>&1"
$global:LASTEXITCODE = 0   # "no file(s) to reconcile" 时 exit 1，可接受

cmd /c "p4 reconcile -ead `"$sampleDepotPath`" 2>&1"
$global:LASTEXITCODE = 0
```

⚠️ **关键点**：

1. **`-ead` 是 `-e -a -d` 合一**：edit + add + delete 三种 reconcile 同时检测
2. **限定到当前版本子目录**——`//$P4CLIENT/MyProject_$version/...` 而不是 `//$P4CLIENT/...`。不然会误把别的版本子目录"depot 有但本地没"的文件 mark delete
3. `cmd /c "... 2>&1"` 包——reconcile 在 rerun 内容字节级未变场景写 stderr `"no file(s) to reconcile"`

---

## Step 7: 强制 reopen 关键扩展名为 binary

详 `guidelines/p4/charset-pitfalls.md`——避开 unicode/text 类型 charset transcode。

```powershell
$binaryExts = @(
    "py", "pyd",                              # Python
    "db", "sqlite",                           # SQLite
    "xlsx", "xls",                            # Excel
    "uasset", "umap",                         # UE assets
    "png", "tga", "jpg", "jpeg", "bmp",       # Images
    "fbx", "obj",                             # 3D models
    "wav", "mp3", "ogg",                      # Audio
    "ini", "cfg", "json", "md", "txt", "csv"  # Text-like with charset risk
)

# 先列 opened files，提取实际出现的 ext，跟白名单交集
# 这样保证 reopen 永远有匹配文件，不会撞 "not opened on this client." stderr
$openedRaw = cmd /c "p4 opened 2>NUL"
$openedExts = @{}
foreach ($line in $openedRaw) {
    if ($line -match '\.([a-zA-Z0-9]+)#\d+ - (?:add|edit)') {
        $openedExts[$matches[1].ToLower()] = $true
    }
}

$binaryExtsLower = $binaryExts | ForEach-Object { $_.ToLower() }
$extsToReopen = @($binaryExtsLower | Where-Object { $openedExts.ContainsKey($_) })

foreach ($ext in $extsToReopen) {
    $depotPath = "//$env:P4CLIENT/....$ext"
    p4 reopen -t binary $depotPath | Write-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Error "reopen failed for .$ext"
        exit 1
    }
}
```

⚠️ **关键点**：

1. **不要无差别对白名单所有 ext 跑 reopen**——白名单里没匹配文件的 ext 会写 stderr → NCE。先 `p4 opened` filter 出实际存在的 ext
2. 过滤后的 reopen **保证有匹配**——任何 reopen 真出 stderr 就是真 error（权限不够 / type 冲突），exit 1
3. `....EXT` 是 P4 递归通配 `.../.EXT`

---

## Step 8: Submit

```powershell
$msg = "[CI bot] MyProject v$version auto-deploy from tag $env:CI_COMMIT_TAG (pipeline #$env:CI_PIPELINE_IID)"

# 用 cmd /c：submit "No files to submit" 写 stderr
$submitOutput = cmd /c "p4 submit -d `"$msg`" 2>&1"
$submitExitCode = $LASTEXITCODE
$submitOutput | Write-Host

if ($submitExitCode -ne 0) {
    # "No files to submit." 视为 success（rerun tag 内容字节级未变是合法场景）
    $submitText = $submitOutput | Out-String
    if ($submitText -match "No files to submit") {
        Write-Host "Nothing to submit — depot already up to date. Treating as success."
        $global:LASTEXITCODE = 0
    } else {
        Write-Error "p4 submit failed (exit $submitExitCode)"
        exit $submitExitCode
    }
}
```

⚠️ **关键点**：

1. **`cmd /c "p4 submit -d \"$msg\" 2>&1"`** 引号 escape——message 含空格 / 方括号 / 括号都通过 cmd quoting 保留
2. **"No files to submit" 视 success**——rerun 同 tag 内容字节级未变是预期场景，部署目标已是"最新版"，视作幂等成功
3. **其他失败 fail-fast**——权限 / 网络 / lock 冲突等
4. **不区分新增 vs rerun**——deploy 语义是"depot 上有这个版本"，CI 不需要知道实际改了什么

---

## 完整 yaml 示例（GitLab CI deploy stage）

```yaml
deploy:
  stage: deploy
  tags:
    - windows
    - powershell
  rules:
    - if: $CI_COMMIT_TAG
    - when: never
  variables:
    P4_DEPLOY_PORT: "p4-deploy.company.com:1666"
    P4_DEPLOY_USER: "ci_bot"
    P4_DEPLOY_CLIENT_NAME: "MyProject_Deploy_CI"
    P4_DEPLOY_WS_ROOT: "D:\\p4_deploy_ws_CI"
    # P4_DEPLOY_PASSWD 走 GitLab CI Variable (Protected + Masked)
  script:
    - |
      $ErrorActionPreference = "Stop"

      # ... (上面 step 1-8 完整代码) ...
```

---

## 怎么 debug

跑挂时按 step 切入：

| 失败 step | 看哪里 |
|---|---|
| Step 1 login | server URL / Variable 是否注入 / 密码错 |
| Step 2 client -i | spec 格式（tab vs space）/ BOM（详 ci-windows pitfall 3）|
| Step 3 sync | "up-to-date" 撞 NCE → cmd /c 包没生效 |
| Step 6 reconcile | "no file(s) to reconcile" 撞 NCE → 同上 |
| Step 7 reopen | 撞 NCE → 没先 filter ext |
| Step 8 submit | 看 stderr 具体内容（权限 / lock / 内容冲突）|

跑挂之后 runner 上 workspace 会留**一堆 opened pending changes**。下一次 pipeline 跑会撞这些残留——Step 2.5 的防御性 revert 就是为这个设计的。手动 cleanup 也可以：

```cmd
p4 -p <server> -u <user> -c <client> revert //<client>/...
```

---

## 跟"拷到网络共享 / FTP"对比

| 维度 | 网络共享 / FTP | P4 部署（本文方案） |
|---|---|---|
| 接收方拿法 | 资源管理器拖 / FTP client | `p4 sync` 标准流程 |
| 增量更新 | 全量重传 | 只传变化的文件 |
| 历史 revision | 自己存 zip 备份 | 自动保留所有 revision |
| 权限管理 | 文件系统 / FTP user | P4 protection table |
| 接收方学习成本 | 0 | 需要 P4 client + workspace 配置 |
| Charset transcoding 坑 | 无 | 有（详 charset-pitfalls.md） |
| 同时 multi-version 分发 | 简单 | 需要 depot 目录约定 |

**适合 P4 部署的场景**：

- 接收方已经在用 P4 做日常开发（如游戏团队美术 / 策划）
- 项目跨多版本并行维护（需要历史 revision 快速回退）
- 团队规模大（增量同步节省带宽 + 时间）

**不适合**：

- 接收方都是非技术用户，没有 P4 client
- 一次性 throwaway 部署

## 项目实例参考

UE 5.5 dialogue plugin 部署到游戏团队 P4 server (策划方 commit-server)，
本 technique 整个流程在该项目 CI 上 ship verified。

完整 yaml 实现:
- workspace 名: `DialogueSystem_Deploy_CI`
- depot 根: `//ga-depot/pj2026yx018/syncData/To/DialogueSystem/`
- 每个 tag 部署到 `<root>/DialogueSystem_<version>/` + `<root>/DialogueSystem_<version>_Sample/`
- `binaryExts` 包含 16 种扩展名（py / db / xlsx / uasset / png / ini / md 等）
- "rerun 同 tag 视为内容覆盖"，"内容字节级未变 → No files to submit 视 success"

调试历程（按 cidev tag 顺序撞过的坑）：

| Tag | 撞的坑 | 修法对应本文哪一节 |
|---|---|---|
| cidev1 | `automation_test` Editor 不退 | 不在本流程内 |
| cidev5 | yaml here-string 跟 yaml block 缩进打架 | Step 2 注意点 4 |
| cidev6 | `P4_DEPLOY_PORT` Variable 未注入 (Protected vs unprotected tag) | Step 1 注意点 2 |
| cidev7 | `p4 client -i` stdin BOM | Step 2 注意点 5 |
| cidev8 | `p4 reopen` 不存在 ext → NCE | Step 7 注意点 1 |
| cidev9 | `p4 sync` up-to-date → NCE | Step 3 注意点 1 |
| cidev10 | ✅ ship | — |

10 次 tag 验证才打通——主要时间花在 PS 5.1 quirks 上。本流程提炼了所有踩过
的坑的修法，新项目按本文直接走能避开。

## 相关 Guidelines

- `guidelines/ci-windows/powershell-native-command-pitfalls.md` —— 每个 cmd /c 包决策的底层 mechanism
- `guidelines/p4/charset-pitfalls.md` —— Step 7 binary type 的底层 mechanism
- `guidelines/ue/build-plugin-limitations.md` —— UE 项目 deploy 前的 package 阶段 patch
- `guidelines/ue/automation-test-from-ci.md` —— deploy 之前的 automation gate stage
