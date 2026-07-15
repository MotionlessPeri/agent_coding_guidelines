$ErrorActionPreference = "Stop"

$ScriptUnderTest = (Resolve-Path (Join-Path $PSScriptRoot "..\sync-skills.ps1")).Path
$PowerShellExe = Join-Path $PSHOME "powershell.exe"
$Failures = [System.Collections.Generic.List[string]]::new()
$Passed = 0

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function New-TestSkill {
    param(
        [string]$Root,
        [string]$Category,
        [string]$Name
    )

    $SkillDir = New-Item -ItemType Directory -Force (Join-Path $Root "$Category\$Name")
    $SkillBody = @"
---
name: $Name
description: Test skill named $Name.
---

# $Name
"@
    Set-Content -Encoding UTF8 (Join-Path $SkillDir.FullName "SKILL.md") $SkillBody
    Set-Content -Encoding UTF8 (Join-Path $SkillDir.FullName "reference.txt") "current"
}

function Invoke-Sync {
    param(
        [string]$UserHome,
        [object[]]$Arguments
    )

    $PreviousUserProfile = $env:USERPROFILE
    try {
        $env:USERPROFILE = $UserHome
        $Output = & $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $ScriptUnderTest @Arguments 2>&1
        return [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output = ($Output -join [Environment]::NewLine)
        }
    }
    finally {
        $env:USERPROFILE = $PreviousUserProfile
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

$TestRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("skill-sync-tests-" + [guid]::NewGuid())
New-Item -ItemType Directory -Force $TestRoot | Out-Null

try {
    Invoke-Test "default user sync installs Claude and Codex targets" {
        $Source = Join-Path $TestRoot "default-source"
        $FakeHome = Join-Path $TestRoot "default-home"
        New-TestSkill $Source "workflow" "alpha"
        New-Item -ItemType Directory -Force $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome)

        Assert-True ($Result.ExitCode -eq 0) "sync failed: $($Result.Output)"
        Assert-True (Test-Path "$FakeHome\.claude\skills\alpha\SKILL.md") "Claude user target is missing"
        Assert-True (Test-Path "$FakeHome\.agents\skills\alpha\SKILL.md") "Codex user target is missing"
    }

    Invoke-Test "single target sync installs only Codex" {
        $Source = Join-Path $TestRoot "single-source"
        $FakeHome = Join-Path $TestRoot "single-home"
        New-TestSkill $Source "ue" "beta"
        New-Item -ItemType Directory -Force $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")

        Assert-True ($Result.ExitCode -eq 0) "sync failed: $($Result.Output)"
        Assert-True (Test-Path "$FakeHome\.agents\skills\beta\SKILL.md") "Codex user target is missing"
        Assert-True (-not (Test-Path "$FakeHome\.claude\skills")) "Claude target should not be created"
    }

    Invoke-Test "project sync installs flat Claude and Codex targets" {
        $Source = Join-Path $TestRoot "project-source"
        $FakeHome = Join-Path $TestRoot "project-home"
        $Project = Join-Path $TestRoot "target-project"
        New-TestSkill $Source "architecture" "gamma"
        New-Item -ItemType Directory -Force $FakeHome, $Project | Out-Null

        $Result = Invoke-Sync $FakeHome @(
            "-SourcePath", $Source,
            "-UserHome", $FakeHome,
            "-Targets", "Claude,Codex",
            "-ProjectPath", $Project
        )

        Assert-True ($Result.ExitCode -eq 0) "sync failed: $($Result.Output)"
        Assert-True (Test-Path "$Project\.claude\skills\gamma\SKILL.md") "Claude project target is missing"
        Assert-True (Test-Path "$Project\.agents\skills\gamma\SKILL.md") "Codex project target is missing"
        Assert-True (-not (Test-Path "$Project\.agents\skills\architecture")) "source category should not appear in target"
    }

    Invoke-Test "update removes stale files and preserves unrelated skills" {
        $Source = Join-Path $TestRoot "update-source"
        $FakeHome = Join-Path $TestRoot "update-home"
        New-TestSkill $Source "workflow" "delta"
        New-Item -ItemType Directory -Force "$FakeHome\.agents\skills\unrelated" | Out-Null
        Set-Content -Encoding UTF8 "$FakeHome\.agents\skills\unrelated\SKILL.md" "unrelated"

        $First = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")
        Assert-True ($First.ExitCode -eq 0) "first sync failed: $($First.Output)"
        Assert-True (Test-Path "$FakeHome\.agents\skills\delta\SKILL.md") "managed skill was not installed"
        Set-Content -Encoding UTF8 "$FakeHome\.agents\skills\delta\stale.txt" "stale"
        Set-Content -Encoding UTF8 "$Source\workflow\delta\reference.txt" "updated"

        $Second = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")

        Assert-True ($Second.ExitCode -eq 0) "second sync failed: $($Second.Output)"
        Assert-True (-not (Test-Path "$FakeHome\.agents\skills\delta\stale.txt")) "stale managed file was not removed"
        Assert-True (Test-Path "$FakeHome\.agents\skills\unrelated\SKILL.md") "unrelated skill was removed"
        Assert-True ((Get-Content -Raw "$FakeHome\.agents\skills\delta\reference.txt").Trim() -eq "updated") "updated source was not copied"
    }
}
finally {
    Remove-Item -Recurse -Force -LiteralPath $TestRoot
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
