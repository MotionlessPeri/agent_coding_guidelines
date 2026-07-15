# Claude Code 与 Codex Skill Compatibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让同一份仓库 skills 在 Windows 上可安装、发现并安全用于 Claude Code 与 Codex，同时支持个人级和项目级安装。

**Architecture:** `skills/` 保持唯一内容源；`scripts/sync-skills.ps1` 先校验所有 skill，再按平台和安装范围把目录扁平复制到目标。通用 skill 使用平台路径映射，确实依赖 Claude hooks 的 skill 明确标为 Claude-only。

**Tech Stack:** PowerShell 7、Markdown、YAML frontmatter、Git。

---

## 实施顺序

```mermaid
flowchart LR
    A["同步行为红测"] --> B["双端复制实现"]
    B --> C["校验行为红测"]
    C --> D["完整校验实现"]
    D --> E["文档与 skill 兼容调整"]
    E --> F["全量验证"]
    classDef gate fill:#fff3e0,stroke:#e65100,color:#000,stroke-width:2px
    class A,C,F gate
```

### Task 1: 建立同步脚本测试入口并写复制行为红测

**Files:**
- Create: `scripts/tests/test-sync-skills.ps1`
- Test: `scripts/sync-skills.ps1`

**Step 1: 写最小测试工具**

在测试脚本中提供：

```powershell
$ErrorActionPreference = "Stop"
$ScriptUnderTest = Resolve-Path (Join-Path $PSScriptRoot "..\sync-skills.ps1")
$Failures = [System.Collections.Generic.List[string]]::new()

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { $script:Failures.Add($Message) }
}

function New-TestSkill([string]$Root, [string]$Category, [string]$Name) {
    $dir = New-Item -ItemType Directory -Force (Join-Path $Root "$Category\$Name")
    @"
---
name: $Name
description: Test skill named $Name.
---

# $Name
"@ | Set-Content -Encoding utf8 (Join-Path $dir.FullName "SKILL.md")
    Set-Content -Encoding utf8 (Join-Path $dir.FullName "reference.txt") "current"
}
```

测试产生的 fixture 位于系统临时目录，并在 `finally` 中递归删除。测试脚本自身可以用 `Set-Content` 生成 fixture；production 文件仍只通过正常源码编辑维护。

**Step 2: 写四组失败测试**

覆盖以下调用和断言：

```powershell
& $ScriptUnderTest -SourcePath $source -UserHome $fakeHome
Assert-True ($LASTEXITCODE -eq 0) "default user sync should succeed"
Assert-True (Test-Path "$fakeHome\.claude\skills\alpha\SKILL.md") "Claude user target missing"
Assert-True (Test-Path "$fakeHome\.agents\skills\alpha\SKILL.md") "Codex user target missing"

& $ScriptUnderTest -SourcePath $source -UserHome $fakeHome -Targets Codex
& $ScriptUnderTest -SourcePath $source -ProjectPath $project -Targets Claude,Codex
```

另外断言分类目录没有复制到目标、无关 skill 得到保留、更新同名 skill 后旧附属文件被清除。

**Step 3: 运行测试并确认失败**

Run:

```powershell
pwsh -NoProfile -File ./scripts/tests/test-sync-skills.ps1
```

Expected: FAIL；现有脚本不认识 `SourcePath`、`UserHome`、`Targets` 或 `ProjectPath`。

**Step 4: 提交红测**

```powershell
git add scripts/tests/test-sync-skills.ps1
git commit -m "test: specify dual-platform skill sync behavior"
```

### Task 2: 实现个人级和项目级双端同步

**Files:**
- Modify: `scripts/sync-skills.ps1`
- Test: `scripts/tests/test-sync-skills.ps1`

**Step 1: 增加参数契约**

脚本顶部使用：

```powershell
[CmdletBinding()]
param(
    [ValidateSet("Claude", "Codex")]
    [string[]]$Targets = @("Claude", "Codex"),
    [string]$ProjectPath,
    [string]$SourcePath = (Join-Path $PSScriptRoot "..\skills"),
    [Parameter(DontShow)]
    [string]$UserHome = $env:USERPROFILE
)
```

`SourcePath` 保留为公开参数，方便验证其他 skill 集合；`UserHome` 只用于测试和高级调用。

**Step 2: 实现目标解析**

```powershell
$scopeRoot = if ($ProjectPath) {
    (Resolve-Path -LiteralPath $ProjectPath).Path
} else {
    $UserHome
}

$TargetDirs = foreach ($target in $Targets) {
    switch ($target) {
        "Claude" { Join-Path $scopeRoot ".claude\skills" }
        "Codex"  { Join-Path $scopeRoot ".agents\skills" }
    }
}
```

**Step 3: 把现有复制循环应用到每个目标**

保留“同名目录存在则删除后完整复制”的行为。每个平台分别统计 `Installed`、`Updated` 和未受管理的额外 skills，并在输出中带平台名和绝对目标路径。

**Step 4: 运行测试并确认复制行为通过**

Run:

```powershell
pwsh -NoProfile -File ./scripts/tests/test-sync-skills.ps1
```

Expected: Task 1 的复制与保留测试 PASS。

**Step 5: 提交实现**

```powershell
git add scripts/sync-skills.ps1 scripts/tests/test-sync-skills.ps1
git commit -m "feat: sync skills to Claude Code and Codex"
```

### Task 3: 先写源数据校验红测，再实现完整校验

**Files:**
- Modify: `scripts/tests/test-sync-skills.ps1`
- Modify: `scripts/sync-skills.ps1`

**Step 1: 写校验失败测试**

分别创建以下 fixture，并通过启动独立 `pwsh` 进程取得可靠退出码：

- 两个分类中存在相同目录 basename。
- 两份不同目录的 frontmatter 使用相同 `name`。
- `name` 缺失、为空或与目录名不一致。
- `description` 缺失或为空。
- frontmatter 缺少起止 `---`。
- `ProjectPath` 不存在。

每次调用前在目标放置 sentinel 文件，失败后断言 sentinel 仍在且没有新 skill 被复制，证明校验先于写入。

**Step 2: 运行测试并确认失败**

Run: `pwsh -NoProfile -File ./scripts/tests/test-sync-skills.ps1`

Expected: FAIL；错误 fixture 尚未被完整拒绝。

**Step 3: 实现 frontmatter 读取**

新增 `Get-SkillMetadata`，只解析本仓库需要的单行 `name` 和 `description`：

```powershell
$match = [regex]::Match($content, '(?ms)\A---\s*\r?\n(?<yaml>.*?)\r?\n---(?:\s*\r?\n|\s*\z)')
$name = [regex]::Match($match.Groups['yaml'].Value, '(?m)^name:\s*["'']?(?<value>[^\r\n"'']+)["'']?\s*$')
$description = [regex]::Match($match.Groups['yaml'].Value, '(?m)^description:\s*["'']?(?<value>[^\r\n"'']+)["'']?\s*$')
```

函数返回规范化后的 `Name`、`Description` 和错误列表。不要引入 YAML 模块依赖。

**Step 4: 聚合全部源错误后统一退出**

发现阶段收集所有 skill 后再检查目录 basename 冲突、metadata `name` 冲突和名称一致性。若 `$ValidationErrors.Count -gt 0`，逐条输出并 `exit 1`；此分支必须发生在任何 `New-Item`、`Remove-Item` 或 `Copy-Item` 之前。

**Step 5: 运行全套测试**

Run: `pwsh -NoProfile -File ./scripts/tests/test-sync-skills.ps1`

Expected: PASS，末尾输出测试数量且退出码为 0。

**Step 6: 提交校验功能**

```powershell
git add scripts/sync-skills.ps1 scripts/tests/test-sync-skills.ps1
git commit -m "feat: validate skill metadata before syncing"
```

### Task 4: 更新仓库入口文档

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/sync-skills.ps1`

**Step 1: 更新 README**

明确写出：skill 不是 Claude 专属格式；`skills/` 是唯一内容源；默认个人级双端安装；`-Targets` 和 `-ProjectPath` 的三个示例；Windows-only 限制；Codex 项目目录是 `.agents/skills/`。

**Step 2: 更新 AGENTS.md**

替换以下旧结论：

- “Codex 无对应机制，需手动读取”。
- “skills/ 下是 Claude Code skill 形态”。
- 只同步 `~/.claude/skills/` 的说明。

新的说明应区分通用 Agent Skill 格式、Claude Code 发现目录和 Codex 发现目录，并说明 `description` 是双端触发条件的共同来源。

**Step 3: 更新脚本帮助注释**

文件头列出默认行为、个人和项目目标、覆盖规则、不会删除无关 skill 的承诺，以及所有命令示例。

**Step 4: 检查旧表述**

Run:

```powershell
rg -n "Codex 无|Claude Code skills|只.*\.claude|Claude Code skill 形态" README.md AGENTS.md scripts/sync-skills.ps1
```

Expected: 无过时结论；平台名称只出现在需要区分路径或能力的地方。

**Step 5: 提交文档**

```powershell
git add README.md AGENTS.md scripts/sync-skills.ps1
git commit -m "docs: document dual-platform skill discovery"
```

### Task 5: 调整现有 skill 的平台边界

**Files:**
- Modify: `skills/ue/unrealmcp-usage/SKILL.md`
- Modify: `skills/ue/official-mcp-usage/SKILL.md`
- Modify: `skills/workflow/autonomous-workflow/SKILL.md`
- Modify: `skills/workflow/supervised-workflow/SKILL.md`
- Modify: `skills/collaboration/multi-session-coordination/SKILL.md`

**Step 1: 中性化 UE MCP skills**

把 description 中的 “from a Claude Code session” 改成 “from an agent session”。保留 `.claude/mcp.json` 作为 Claude Code 专属检测线索，同时补充 Codex 的项目 MCP 配置路径或明确说明 TCP 直连不依赖客户端配置。官方 MCP skill 中，按 Claude Code 与 Codex 分开列出客户端配置和 reconnect 操作；无法从现有资料确认的 Codex 操作不得猜测。

**Step 2: 给两个 workflow orchestrator 增加平台路径映射**

在正文首次使用路径前定义：

| 概念 | Claude Code | Codex |
|---|---|---|
| 项目 skill 根目录 | `<project>/.claude/skills` | `<project>/.agents/skills` |
| agent 私有状态根目录 | `~/.claude` | `~/.codex` |

后文用 `<project-skill-root>` 和 `<agent-state-root>`，不再把 `.claude` 写死。Claude `settings.json` 权限预检保留为 Claude-only 分支；Codex 使用当前会话暴露的 approval/sandbox policy，不读取或虚构 Claude 配置。

**Step 3: 明确 multi-session-coordination 的限制**

该 skill 依赖 Claude Code hooks 和 `settings.json`，首版不移植机制。把 Claude-only 限制前置到 `description` 和正文开头，并说明同步到 Codex 只是为了让 Codex 能识别“不适用”，不得尝试运行 Claude hook 安装流程。

**Step 4: 扫描残余的误导性平台绑定**

Run:

```powershell
rg -n "Claude Code session|<project>/\.claude/skills|~/.claude" skills -g "SKILL.md"
```

Expected: 只剩明确标注的平台分支或 Claude-only skill，不再有把通用流程误写成 Claude 专属的表述。

**Step 5: 提交 skill 兼容调整**

```powershell
git add skills/ue skills/workflow skills/collaboration/multi-session-coordination/SKILL.md
git commit -m "docs: make skill platform boundaries explicit"
```

### Task 6: 全量验证与可控安装检查

**Files:**
- Modify if needed: `scripts/tests/test-sync-skills.ps1`
- Modify if needed: `scripts/sync-skills.ps1`

**Step 1: 运行自动测试**

Run: `pwsh -NoProfile -File ./scripts/tests/test-sync-skills.ps1`

Expected: 所有测试 PASS，退出码 0。

**Step 2: 对真实 skills 源执行临时 Codex 安装**

```powershell
$tempProject = Join-Path ([System.IO.Path]::GetTempPath()) ("skill-sync-smoke-" + [guid]::NewGuid())
New-Item -ItemType Directory $tempProject | Out-Null
pwsh -NoProfile -File ./scripts/sync-skills.ps1 -Targets Codex -ProjectPath $tempProject
Get-ChildItem "$tempProject\.agents\skills" -Directory
Remove-Item -Recurse -Force -LiteralPath $tempProject
```

Expected: 脚本报告所有仓库 skills 已安装；目标下每个 skill 目录包含 `SKILL.md`。

**Step 3: 运行静态检查**

```powershell
git diff --check
rg -n "Codex 无 skill|Codex 无对应机制" README.md AGENTS.md
git status --short
```

Expected: `git diff --check` 无输出；旧结论无匹配；只出现本任务预期文件和用户原有的未跟踪文件。

**Step 4: 最终提交**

只有验证阶段产生修正时才提交：

```powershell
git add scripts/sync-skills.ps1 scripts/tests/test-sync-skills.ps1
git commit -m "fix: harden Windows skill sync verification"
```
