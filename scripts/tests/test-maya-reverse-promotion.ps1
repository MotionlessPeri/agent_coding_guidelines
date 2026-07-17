$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Failures = [System.Collections.Generic.List[string]]::new()
$Passed = 0

function Read-RepoFile {
    param([string]$Path)
    return Get-Content -Raw -LiteralPath (Join-Path $RepoRoot $Path)
}

function Assert-Matches {
    param([string]$Text, [string]$Pattern, [string]$Message)
    if ($Text -notmatch $Pattern) { throw $Message }
}

function Assert-Excludes {
    param([string]$Text, [string]$Pattern, [string]$Message)
    if ($Text -match $Pattern) { throw $Message }
}

function Invoke-Test {
    param([string]$Name, [scriptblock]$Body)
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

Invoke-Test "reverse skill keeps the full evidence gate" {
    $Text = Read-RepoFile "skills/maya/reverse-maya-closed-nodes/SKILL.md"
    Assert-Matches $Text '(?m)^description: Use when' "skill description lacks a portable trigger"
    foreach ($Pattern in @('XMM3|ABI', '激发守卫', '非共面 quad', '真实资产', 'confirmed', 'strong inference')) {
        Assert-Matches $Text $Pattern "skill lacks required evidence concept: $Pattern"
    }
    Assert-Excludes $Text '0x180[0-9a-f]+|H:\\xd_projects|proximityWrap' "skill leaked project-specific evidence"
}

Invoke-Test "GPU guideline requires real GUI execution evidence" {
    $Text = Read-RepoFile "guidelines/maya/gpu-deformer-gui-validation.md"
    foreach ($Pattern in @('GPU Active', 'success marker', '非零形变', 'CPU 输出', 'bootstrap\.mel', 'licensing')) {
        Assert-Matches $Text $Pattern "GPU guideline lacks gate: $Pattern"
    }
}

Invoke-Test "mesh guideline preserves Maya triangulation" {
    $Text = Read-RepoFile "guidelines/maya/mesh-topology-fidelity.md"
    Assert-Matches $Text 'MFnMesh::getTriangles' "mesh guideline does not require Maya triangles"
    Assert-Matches $Text 'triangle.*polygon' "mesh guideline lacks triangle-to-polygon mapping"
    Assert-Matches $Text '非共面 quad' "mesh guideline lacks the adversarial topology case"
}

Invoke-Test "native dump guideline distinguishes hang and crash" {
    $Text = Read-RepoFile "guidelines/cpp/windows-native-crash-hang-evidence.md"
    foreach ($Pattern in @('Break All', '不带 heap', 'full-memory', '~\* k', 'RVA =', 'licensing')) {
        Assert-Matches $Text $Pattern "native dump guideline lacks: $Pattern"
    }
}

Invoke-Test "new documents are imported and indexed" {
    $Agents = Read-RepoFile "AGENTS.md"
    $Index = Read-RepoFile "guidelines/maya/INDEX.md"
    foreach ($Path in @(
        'guidelines/cpp/windows-native-crash-hang-evidence.md',
        'guidelines/maya/gpu-deformer-gui-validation.md',
        'guidelines/maya/mesh-topology-fidelity.md'
    )) {
        Assert-Matches $Agents ([regex]::Escape("@$Path")) "AGENTS does not import $Path"
    }
    Assert-Matches $Index 'reverse-maya-closed-nodes' "Maya index lacks the reverse skill"
}

Write-Host ""
Write-Host "Passed: $Passed"
Write-Host "Failed: $($Failures.Count)"
if ($Failures.Count -gt 0) {
    foreach ($Failure in $Failures) { Write-Host "  - $Failure" -ForegroundColor Red }
    exit 1
}
exit 0
