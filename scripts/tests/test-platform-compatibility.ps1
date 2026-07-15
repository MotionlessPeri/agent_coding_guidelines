$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Failures = [System.Collections.Generic.List[string]]::new()
$Passed = 0

function Assert-TextContains {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Message
    )

    $Content = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot $Path)
    if ($Content -notmatch $Pattern) {
        throw $Message
    }
}

function Assert-TextExcludes {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Message
    )

    $Content = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot $Path)
    if ($Content -match $Pattern) {
        throw $Message
    }
}

function Invoke-Test {
    param(
        [string]$Name,
        [scriptblock]$Body
    )

    try {
        & $Body
        $script:Passed++
        Write-Host "PASS: $Name" -ForegroundColor Green
    }
    catch {
        $script:Failures.Add("$Name`: $($_.Exception.Message)")
        Write-Host "FAIL: $Name" -ForegroundColor Red
        Write-Host "  $($_.Exception.Message)"
    }
}

Invoke-Test "entry docs describe Agent Skills for both platforms" {
    Assert-TextContains "README.md" '\.agents[\\/]skills' "README lacks the Codex skill target"
    Assert-TextContains "README.md" '\.claude[\\/]skills' "README lacks the Claude Code skill target"
    Assert-TextExcludes "AGENTS.md" 'Codex 无(?:对应机制| skill 发现机制)' "AGENTS still says Codex cannot discover skills"
}

Invoke-Test "sync script help documents user and project targets" {
    Assert-TextContains "scripts/sync-skills.ps1" 'ProjectPath' "script help does not mention ProjectPath"
    Assert-TextContains "scripts/sync-skills.ps1" '\.agents[\\/]skills' "script help does not mention the Codex target"
    Assert-TextContains "scripts/sync-skills.ps1" '\.claude[\\/]skills' "script help does not mention the Claude target"
}

Invoke-Test "UE MCP skills do not claim generic use is Claude-only" {
    Assert-TextExcludes "skills/ue/unrealmcp-usage/SKILL.md" 'from a Claude Code session' "unrealmcp description is still Claude-only"
    Assert-TextContains "skills/ue/unrealmcp-usage/SKILL.md" '\.agents/skills/unrealmcp-usage' "unrealmcp lacks the Codex-installed client path"
    Assert-TextContains "skills/ue/unrealmcp-usage/SKILL.md" '<skill-dir>' "unrealmcp commands lack a platform-neutral skill path"
    Assert-TextExcludes "skills/ue/official-mcp-usage/SKILL.md" 'from a Claude Code session' "official MCP description is still Claude-only"
    Assert-TextContains "skills/ue/official-mcp-usage/SKILL.md" '\.codex/config\.toml' "official MCP lacks Codex project configuration"
}

Invoke-Test "workflow skills define platform-neutral roots" {
    foreach ($Path in @(
        "skills/workflow/autonomous-workflow/SKILL.md",
        "skills/workflow/supervised-workflow/SKILL.md"
    )) {
        Assert-TextContains $Path '<project-skill-root>' "$Path lacks project skill root mapping"
        Assert-TextContains $Path '<agent-state-root>' "$Path lacks agent state root mapping"
    }
}

Invoke-Test "Claude hook coordination skill declares its platform limit" {
    Assert-TextContains "skills/collaboration/multi-session-coordination/SKILL.md" 'Claude Code[- ]only' "multi-session skill does not declare its Claude-only limit"
}

Invoke-Test "skill frontmatter uses the shared portable fields" {
    $SkillFiles = Get-ChildItem -Recurse -Filter SKILL.md (Join-Path $RepoRoot "skills")
    foreach ($SkillFile in $SkillFiles) {
        $Content = Get-Content -Raw -LiteralPath $SkillFile.FullName
        if ($Content -match '(?m)^when_to_use:') {
            throw "$($SkillFile.FullName) contains unsupported when_to_use frontmatter"
        }
    }
}

Write-Host ""
Write-Host "Passed: $Passed"
Write-Host "Failed: $($Failures.Count)"

if ($Failures.Count -gt 0) {
    foreach ($Failure in $Failures) {
        Write-Host "  - $Failure" -ForegroundColor Red
    }
    exit 1
}

exit 0
