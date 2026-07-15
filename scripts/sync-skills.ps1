# sync-skills.ps1
# One-way sync from the repository skill source to Claude Code and Codex.

[CmdletBinding()]
param(
    [ValidateSet("Claude", "Codex")]
    [string[]]$Targets = @("Claude", "Codex"),

    [string]$ProjectPath,

    [string]$SourcePath = (Join-Path $PSScriptRoot "..\skills"),

    [Parameter(DontShow)]
    [string]$UserHome = $env:USERPROFILE
)

$ErrorActionPreference = "Stop"

$RepoSkills = (Resolve-Path -LiteralPath $SourcePath).Path
$ScopeRoot = if ($ProjectPath) {
    (Resolve-Path -LiteralPath $ProjectPath).Path
}
else {
    $UserHome
}

$SkillDirs = @(Get-ChildItem -Recurse -Directory $RepoSkills | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md")
})

if ($SkillDirs.Count -eq 0) {
    Write-Host "No skills found under $RepoSkills"
    exit 0
}

$NameGroups = @($SkillDirs | Group-Object -Property Name | Where-Object { $_.Count -gt 1 })
if ($NameGroups.Count -gt 0) {
    Write-Host "ERROR: Skill basename collision (target directory would collide):" -ForegroundColor Red
    foreach ($Group in $NameGroups) {
        Write-Host "  $($Group.Name):" -ForegroundColor Red
        foreach ($Directory in $Group.Group) {
            Write-Host "    $($Directory.FullName)" -ForegroundColor Red
        }
    }
    exit 1
}

$TargetSpecs = foreach ($TargetName in ($Targets | Select-Object -Unique)) {
    $RelativePath = switch ($TargetName) {
        "Claude" { ".claude\skills" }
        "Codex" { ".agents\skills" }
    }

    [pscustomobject]@{
        Name = $TargetName
        Path = Join-Path $ScopeRoot $RelativePath
    }
}

foreach ($TargetSpec in $TargetSpecs) {
    $TargetDir = $TargetSpec.Path
    if (-not (Test-Path -LiteralPath $TargetDir)) {
        New-Item -Path $TargetDir -ItemType Directory -Force | Out-Null
        Write-Host "Created $($TargetSpec.Name) target: $TargetDir"
    }

    $Installed = 0
    $Updated = 0

    foreach ($Skill in $SkillDirs) {
        $Name = $Skill.Name
        $Source = $Skill.FullName
        $Destination = Join-Path $TargetDir $Name

        if (Test-Path -LiteralPath $Destination) {
            Remove-Item -Recurse -Force -LiteralPath $Destination
            Copy-Item -Recurse -LiteralPath $Source -Destination $Destination
            Write-Host "[$($TargetSpec.Name)] Updated:   $Name"
            $Updated++
        }
        else {
            Copy-Item -Recurse -LiteralPath $Source -Destination $Destination
            Write-Host "[$($TargetSpec.Name)] Installed: $Name"
            $Installed++
        }
    }

    Write-Host ""
    Write-Host "Synced $($SkillDirs.Count) skill(s) to $($TargetSpec.Name): $TargetDir"
    Write-Host "  Installed: $Installed"
    Write-Host "  Updated:   $Updated"

    $TargetSkills = @(Get-ChildItem -Directory $TargetDir | Select-Object -ExpandProperty Name)
    $RepoNames = @($SkillDirs | Select-Object -ExpandProperty Name)
    $Extra = @($TargetSkills | Where-Object { $_ -notin $RepoNames })

    if ($Extra.Count -gt 0) {
        Write-Host ""
        Write-Host "Note: $($TargetSpec.Name) target has skills not managed by this repo (left untouched):"
        foreach ($Name in $Extra) {
            Write-Host "  - $Name"
        }
    }
}
