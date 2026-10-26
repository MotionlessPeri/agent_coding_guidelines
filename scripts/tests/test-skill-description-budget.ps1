$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Failures = [System.Collections.Generic.List[string]]::new()
$Passed = 0

function Get-SkillDescription {
    param([string]$Path)

    $Content = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot $Path)
    $Match = [regex]::Match($Content, '(?ms)\A---\s*\r?\n(.*?)\r?\n---')
    if (-not $Match.Success) {
        throw "$Path has no YAML frontmatter"
    }

    $Description = [regex]::Match(
        $Match.Groups[1].Value,
        '(?m)^description:\s*(.+?)\s*$'
    )
    if (-not $Description.Success) {
        throw "$Path has no single-line description"
    }

    return $Description.Groups[1].Value.Trim().Trim('"').Trim("'")
}

function Assert-Matches {
    param(
        [string]$Value,
        [string]$Pattern,
        [string]$Message
    )

    if ($Value -notmatch $Pattern) {
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

$Contracts = @(
    @{
        Name = "context-budget-audit"
        Path = "skills/workflow/context-budget-audit/SKILL.md"
        Required = @('context|always-loaded', 'AGENTS|CLAUDE|skill descriptions|injected', 'Skip')
    },
    @{
        Name = "ue-custom-graph-editor"
        Path = "skills/ue/ue-custom-graph-editor/SKILL.md"
        Required = @('UEdGraph', 'runtime', 'built-in', 'Skip')
    },
    @{
        Name = "ue-procedural-numerical"
        Path = "skills/ue/ue-procedural-numerical/SKILL.md"
        Required = @('RigVM|Control Rig', 'Optimus', 'FRBFSolver|TMemStack', 'GPU', 'parallel', 'Skip')
    },
    @{
        Name = "ue-ml-animation"
        Path = "skills/ue/ue-ml-animation/SKILL.md"
        Required = @('UAnimInstance|FAnimInstanceProxy', 'NNE|ONNX', 'AnimBP', 'Skip')
    }
)

foreach ($Contract in $Contracts) {
    Invoke-Test "$($Contract.Name) keeps a concise routing contract" {
        $Description = Get-SkillDescription $Contract.Path

        if ($Description.Length -gt 400) {
            throw "description is $($Description.Length) chars; expected at most 400"
        }
        if (-not $Description.StartsWith("Use when ")) {
            throw "description must start with 'Use when '"
        }
        if ($Description -match 'Bundles the|Covers the|Provides a \d+-step|hidden contracts? from') {
            throw "description leaks body workflow or content summary"
        }
        foreach ($Pattern in $Contract.Required) {
            Assert-Matches $Description $Pattern "description misses routing signal: $Pattern"
        }
    }
}

Invoke-Test "trimmed skills publish reproducible trigger contracts" {
    $ContractPath = Join-Path $RepoRoot "skills/workflow/context-budget-audit/trigger-contracts.md"
    if (-not (Test-Path -LiteralPath $ContractPath)) {
        throw "trigger-contracts.md is missing"
    }

    $Content = Get-Content -Raw -LiteralPath $ContractPath
    foreach ($Contract in $Contracts) {
        Assert-Matches $Content ([regex]::Escape($Contract.Name)) "trigger contract misses $($Contract.Name)"
    }
    foreach ($Pattern in @('应触发', '不应触发', 'codex debug prompt-input', '新建.*(?:conversation|对话)')) {
        Assert-Matches $Content $Pattern "trigger contract misses validation requirement: $Pattern"
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
