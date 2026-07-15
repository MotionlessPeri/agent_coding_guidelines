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

function New-RawSkill {
    param(
        [string]$Root,
        [string]$Category,
        [string]$DirectoryName,
        [string]$Content
    )

    $SkillDir = New-Item -ItemType Directory -Force (Join-Path $Root "$Category\$DirectoryName")
    Set-Content -Encoding UTF8 (Join-Path $SkillDir.FullName "SKILL.md") $Content
}

function Invoke-Sync {
    param(
        [string]$UserHome,
        [object[]]$Arguments
    )

    $PreviousUserProfile = $env:USERPROFILE
    $PreviousErrorAction = $ErrorActionPreference
    try {
        $env:USERPROFILE = $UserHome
        $ErrorActionPreference = "Continue"
        $Output = & $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $ScriptUnderTest @Arguments 2>&1
        return [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output = ($Output -join [Environment]::NewLine)
        }
    }
    finally {
        $env:USERPROFILE = $PreviousUserProfile
        $ErrorActionPreference = $PreviousErrorAction
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

    Invoke-Test "default source path resolves relative to the sync script" {
        $FakeHome = Join-Path $TestRoot "default-source-home"
        New-Item -ItemType Directory -Force $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @("-UserHome", $FakeHome, "-Targets", "Codex")

        Assert-True ($Result.ExitCode -eq 0) "default source sync failed: $($Result.Output)"
        Assert-True (Test-Path "$FakeHome\.agents\skills\tdd-with-fixtures\SKILL.md") "default repository source was not resolved"
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

    Invoke-Test "invalid frontmatter is rejected before target writes" {
        $Cases = @(
            @{ Name = "missing-name"; Directory = "missing-name"; Body = "---`ndescription: Missing name.`n---" },
            @{ Name = "empty-name"; Directory = "empty-name"; Body = "---`nname:`ndescription: Empty name.`n---" },
            @{ Name = "missing-description"; Directory = "missing-description"; Body = "---`nname: missing-description`n---" },
            @{ Name = "empty-description"; Directory = "empty-description"; Body = "---`nname: empty-description`ndescription:`n---" },
            @{ Name = "missing-boundaries"; Directory = "missing-boundaries"; Body = "name: missing-boundaries`ndescription: No delimiters." },
            @{ Name = "unsupported-field"; Directory = "unsupported-field"; Body = "---`nname: unsupported-field`ndescription: Has an extra key.`nwhen_to_use: Never portable.`n---" },
            @{ Name = "long-description"; Directory = "long-description"; Body = "---`nname: long-description`ndescription: $(('x' * 1025))`n---" },
            @{ Name = "angle-description"; Directory = "angle-description"; Body = "---`nname: angle-description`ndescription: Use with <placeholder>.`n---" },
            @{ Name = "invalid-name"; Directory = "Bad_Name"; Body = "---`nname: Bad_Name`ndescription: Invalid portable name.`n---" },
            @{ Name = "invalid-plain-yaml"; Directory = "invalid-plain-yaml"; Body = "---`nname: invalid-plain-yaml`ndescription: Unquoted colon: invalid YAML.`n---" }
        )

        foreach ($Case in $Cases) {
            $Source = Join-Path $TestRoot "$($Case.Name)-source"
            $FakeHome = Join-Path $TestRoot "$($Case.Name)-home"
            New-RawSkill $Source "workflow" $Case.Directory $Case.Body
            New-Item -ItemType Directory -Force "$FakeHome\.agents\skills\unrelated" | Out-Null
            Set-Content -Encoding UTF8 "$FakeHome\.agents\skills\unrelated\sentinel.txt" "keep"

            $Result = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")

            Assert-True ($Result.ExitCode -ne 0) "$($Case.Name) should fail validation"
            Assert-True (Test-Path "$FakeHome\.agents\skills\unrelated\sentinel.txt") "$($Case.Name) changed an existing target"
            Assert-True (-not (Test-Path "$FakeHome\.agents\skills\$($Case.Directory)")) "$($Case.Name) was copied before validation completed"
        }
    }

    Invoke-Test "metadata name must match directory name" {
        $Source = Join-Path $TestRoot "mismatch-source"
        $FakeHome = Join-Path $TestRoot "mismatch-home"
        New-RawSkill $Source "workflow" "directory-name" "---`nname: metadata-name`ndescription: Names differ.`n---"
        New-Item -ItemType Directory -Force $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")

        Assert-True ($Result.ExitCode -ne 0) "name mismatch should fail validation"
        Assert-True (-not (Test-Path "$FakeHome\.agents\skills")) "target was created before validation completed"
    }

    Invoke-Test "duplicate metadata names are rejected before target writes" {
        $Source = Join-Path $TestRoot "duplicate-metadata-source"
        $FakeHome = Join-Path $TestRoot "duplicate-metadata-home"
        New-RawSkill $Source "workflow" "first" "---`nname: shared`ndescription: First duplicate.`n---"
        New-RawSkill $Source "ue" "second" "---`nname: shared`ndescription: Second duplicate.`n---"
        New-Item -ItemType Directory -Force $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")

        Assert-True ($Result.ExitCode -ne 0) "duplicate metadata names should fail validation"
        Assert-True (-not (Test-Path "$FakeHome\.agents\skills")) "target was created before validation completed"
    }

    Invoke-Test "duplicate directory names are rejected before target writes" {
        $Source = Join-Path $TestRoot "duplicate-directory-source"
        $FakeHome = Join-Path $TestRoot "duplicate-directory-home"
        New-TestSkill $Source "workflow" "same-name"
        New-TestSkill $Source "ue" "same-name"
        New-Item -ItemType Directory -Force $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")

        Assert-True ($Result.ExitCode -ne 0) "duplicate directory names should fail validation"
        Assert-True (-not (Test-Path "$FakeHome\.agents\skills")) "target was created before validation completed"
    }

    Invoke-Test "invalid project path is rejected before user target writes" {
        $Source = Join-Path $TestRoot "invalid-project-source"
        $FakeHome = Join-Path $TestRoot "invalid-project-home"
        $MissingProject = Join-Path $TestRoot "does-not-exist"
        New-TestSkill $Source "workflow" "epsilon"
        New-Item -ItemType Directory -Force $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @(
            "-SourcePath", $Source,
            "-UserHome", $FakeHome,
            "-Targets", "Codex",
            "-ProjectPath", $MissingProject
        )

        Assert-True ($Result.ExitCode -ne 0) "invalid project path should fail"
        Assert-True (-not (Test-Path "$FakeHome\.agents\skills")) "user target was written during failed project sync"
    }

    Invoke-Test "empty skill source is rejected" {
        $Source = Join-Path $TestRoot "empty-source"
        $FakeHome = Join-Path $TestRoot "empty-home"
        New-Item -ItemType Directory -Force $Source, $FakeHome | Out-Null

        $Result = Invoke-Sync $FakeHome @("-SourcePath", $Source, "-UserHome", $FakeHome, "-Targets", "Codex")

        Assert-True ($Result.ExitCode -ne 0) "empty source should fail validation"
        Assert-True (-not (Test-Path "$FakeHome\.agents\skills")) "target was created for empty source"
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
