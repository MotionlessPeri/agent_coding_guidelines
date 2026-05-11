# sync-skills.ps1
# One-way sync: repo `skills/` -> `~/.claude/skills/`
#
# Repo is the source of truth. This script propagates updates to the
# Claude Code discovery location (`~/.claude/skills/`).
#
# Behavior:
#   - For each subdirectory under `skills/`, replace the same-named dir
#     in `~/.claude/skills/` (delete-then-copy so removed files in the
#     repo do not leave stale files in the target).
#   - Skills in `~/.claude/skills/` that do not exist in the repo are
#     left untouched (do not destroy user's other skills).
#
# Usage (from repo root):
#   pwsh ./scripts/sync-skills.ps1
#   or
#   powershell -File ./scripts/sync-skills.ps1

$ErrorActionPreference = "Stop"

$RepoSkills = Resolve-Path (Join-Path $PSScriptRoot "..\skills")
$TargetDir  = Join-Path $env:USERPROFILE ".claude\skills"

if (-not (Test-Path $TargetDir)) {
    New-Item -Path $TargetDir -ItemType Directory -Force | Out-Null
    Write-Host "Created target: $TargetDir"
}

$SkillDirs = Get-ChildItem -Directory $RepoSkills

if ($SkillDirs.Count -eq 0) {
    Write-Host "No skills found under $RepoSkills"
    exit 0
}

$Installed = 0
$Updated   = 0

foreach ($Skill in $SkillDirs) {
    $name = $Skill.Name
    $src  = $Skill.FullName
    $dst  = Join-Path $TargetDir $name

    if (Test-Path $dst) {
        Remove-Item -Recurse -Force $dst
        Copy-Item -Recurse $src $dst
        Write-Host "Updated:   $name"
        $Updated++
    } else {
        Copy-Item -Recurse $src $dst
        Write-Host "Installed: $name"
        $Installed++
    }
}

Write-Host ""
Write-Host "Synced $($SkillDirs.Count) skill(s) to $TargetDir"
Write-Host "  Installed: $Installed"
Write-Host "  Updated:   $Updated"

# Report any skills in target that are not in the repo (informational only).
$TargetSkills = Get-ChildItem -Directory $TargetDir | Select-Object -ExpandProperty Name
$RepoNames    = $SkillDirs | Select-Object -ExpandProperty Name
$Extra        = $TargetSkills | Where-Object { $_ -notin $RepoNames }

if ($Extra.Count -gt 0) {
    Write-Host ""
    Write-Host "Note: target has these skills not in repo (left untouched):"
    foreach ($e in $Extra) {
        Write-Host "  - $e"
    }
}
