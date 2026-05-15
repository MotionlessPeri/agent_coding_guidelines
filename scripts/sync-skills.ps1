# sync-skills.ps1
# One-way sync: repo `skills/**` -> `~/.claude/skills/<name>/` (flat target).
#
# Repo is the source of truth. This script propagates updates to the
# Claude Code discovery location (`~/.claude/skills/`).
#
# Repo layout:
#   skills/
#     ue/<name>/SKILL.md
#     workflow/<name>/SKILL.md
#     collaboration/<name>/SKILL.md
#     ...
# Target layout (flat, by Claude Code discovery requirement):
#   ~/.claude/skills/<name>/SKILL.md
#
# Behavior:
#   - Recursive scan repo `skills/` for any directory containing a `SKILL.md`.
#     Each such directory is one skill; its basename (NOT its parent category)
#     is the discovery name copied to `~/.claude/skills/<name>/`.
#   - If two skills have the same basename in different categories, abort with
#     a clear error (target collision; skill names must be globally unique).
#   - Replace same-named target dir (delete-then-copy so removed files don't
#     leave stale files behind).
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

# Recursive scan: any directory under skills/ that contains a SKILL.md is a skill.
$SkillDirs = Get-ChildItem -Recurse -Directory $RepoSkills | Where-Object {
    Test-Path (Join-Path $_.FullName "SKILL.md")
}

if ($SkillDirs.Count -eq 0) {
    Write-Host "No skills found under $RepoSkills"
    exit 0
}

# Name collision check: basename must be unique across all categories.
$NameGroups = $SkillDirs | Group-Object -Property Name | Where-Object { $_.Count -gt 1 }
if ($NameGroups) {
    Write-Host "ERROR: Skill basename collision (target dir would collide):" -ForegroundColor Red
    foreach ($g in $NameGroups) {
        Write-Host "  $($g.Name):" -ForegroundColor Red
        foreach ($d in $g.Group) {
            Write-Host "    $($d.FullName)" -ForegroundColor Red
        }
    }
    exit 1
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
