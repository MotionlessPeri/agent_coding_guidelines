# sync-skills.ps1
# One-way Windows sync from repository `skills/**` to Agent Skill discovery paths.
#
# Default user targets:
#   Claude Code: %USERPROFILE%\.claude\skills\<name>
#   Codex:       %USERPROFILE%\.agents\skills\<name>
#
# With -ProjectPath <repo>:
#   Claude Code: <repo>\.claude\skills\<name>
#   Codex:       <repo>\.agents\skills\<name>
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1 -Targets Codex
#   powershell -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1 -ProjectPath E:\some_project
#
# The script validates all source skills before writing. It replaces same-named target
# directories so removed source files do not remain stale, but leaves unrelated skills
# untouched. The categorized source layout is flattened by skill name at each target.

[CmdletBinding()]
param(
    [ValidateSet("Claude", "Codex")]
    [string[]]$Targets = @("Claude", "Codex"),

    [string]$ProjectPath,

    [string]$SourcePath,

    [Parameter(DontShow)]
    [string]$UserHome = $env:USERPROFILE
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = Join-Path $PSScriptRoot "..\skills"
}

function Get-YamlScalarField {
    param(
        [string]$Yaml,
        [string]$FieldName
    )

    $Pattern = '(?m)^' + [regex]::Escape($FieldName) + ':[ \t]*(?<value>[^\r\n]*)$'
    $Match = [regex]::Match($Yaml, $Pattern)
    if (-not $Match.Success) {
        return $null
    }

    $Value = $Match.Groups["value"].Value.Trim()
    if ($Value.Length -ge 2) {
        $First = $Value.Substring(0, 1)
        $Last = $Value.Substring($Value.Length - 1, 1)
        if (($First -eq '"' -and $Last -eq '"') -or ($First -eq "'" -and $Last -eq "'")) {
            $Value = $Value.Substring(1, $Value.Length - 2).Trim()
        }
    }

    return $Value
}

function Get-SkillMetadata {
    param([System.IO.DirectoryInfo]$SkillDirectory)

    $SkillFile = Join-Path $SkillDirectory.FullName "SKILL.md"
    $Content = Get-Content -Raw -LiteralPath $SkillFile
    $Frontmatter = [regex]::Match(
        $Content,
        '(?s)\A---[ \t]*\r?\n(?<yaml>.*?)\r?\n---[ \t]*(?:\r?\n|\z)'
    )

    if (-not $Frontmatter.Success) {
        return [pscustomobject]@{
            Directory = $SkillDirectory
            Name = $null
            Description = $null
            DescriptionRaw = $null
            DescriptionQuoted = $false
            Keys = @()
            Error = "$SkillFile`: missing valid YAML frontmatter boundaries"
        }
    }

    $Yaml = $Frontmatter.Groups["yaml"].Value
    $DescriptionLine = [regex]::Match($Yaml, '(?m)^description:[ \t]*(?<value>[^\r\n]*)$')
    $DescriptionRaw = if ($DescriptionLine.Success) {
        $DescriptionLine.Groups["value"].Value.Trim()
    }
    else {
        $null
    }
    $DescriptionQuoted = $false
    if ($DescriptionRaw -and $DescriptionRaw.Length -ge 2) {
        $First = $DescriptionRaw.Substring(0, 1)
        $Last = $DescriptionRaw.Substring($DescriptionRaw.Length - 1, 1)
        $DescriptionQuoted = ($First -eq '"' -and $Last -eq '"') -or ($First -eq "'" -and $Last -eq "'")
    }
    $Keys = @(
        [regex]::Matches($Yaml, '(?m)^(?<key>[A-Za-z][A-Za-z0-9_-]*):') |
            ForEach-Object { $_.Groups["key"].Value }
    )

    return [pscustomobject]@{
        Directory = $SkillDirectory
        Name = Get-YamlScalarField $Yaml "name"
        Description = Get-YamlScalarField $Yaml "description"
        DescriptionRaw = $DescriptionRaw
        DescriptionQuoted = $DescriptionQuoted
        Keys = $Keys
        Error = $null
    }
}

$ValidationErrors = [System.Collections.Generic.List[string]]::new()

if (-not (Test-Path -LiteralPath $SourcePath -PathType Container)) {
    $ValidationErrors.Add("Skill source does not exist or is not a directory: $SourcePath")
}

if ($ProjectPath -and -not (Test-Path -LiteralPath $ProjectPath -PathType Container)) {
    $ValidationErrors.Add("ProjectPath does not exist or is not a directory: $ProjectPath")
}

if ($ValidationErrors.Count -gt 0) {
    Write-Host "ERROR: Skill sync validation failed:" -ForegroundColor Red
    foreach ($ValidationError in $ValidationErrors) {
        Write-Host "  - $ValidationError" -ForegroundColor Red
    }
    exit 1
}

$RepoSkills = (Resolve-Path -LiteralPath $SourcePath).Path
$SkillDirs = @(Get-ChildItem -Recurse -Directory $RepoSkills | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md")
})

if ($SkillDirs.Count -eq 0) {
    $ValidationErrors.Add("No skills found under $RepoSkills")
}

$NameGroups = @($SkillDirs | Group-Object -Property Name | Where-Object { $_.Count -gt 1 })
foreach ($Group in $NameGroups) {
    $Paths = ($Group.Group | Select-Object -ExpandProperty FullName) -join ", "
    $ValidationErrors.Add("Skill directory name '$($Group.Name)' is duplicated: $Paths")
}

$SkillMetadata = @($SkillDirs | ForEach-Object { Get-SkillMetadata $_ })
foreach ($Metadata in $SkillMetadata) {
    if ($Metadata.Error) {
        $ValidationErrors.Add($Metadata.Error)
        continue
    }

    $SkillFile = Join-Path $Metadata.Directory.FullName "SKILL.md"
    $UnsupportedKeys = @($Metadata.Keys | Where-Object { $_ -notin @("name", "description") })
    foreach ($UnsupportedKey in $UnsupportedKeys) {
        $ValidationErrors.Add("$SkillFile`: unsupported frontmatter field '$UnsupportedKey'; use only name and description")
    }

    $DuplicateKeys = @($Metadata.Keys | Group-Object | Where-Object { $_.Count -gt 1 })
    foreach ($DuplicateKey in $DuplicateKeys) {
        $ValidationErrors.Add("$SkillFile`: frontmatter field '$($DuplicateKey.Name)' appears more than once")
    }

    if ([string]::IsNullOrWhiteSpace($Metadata.Name)) {
        $ValidationErrors.Add("$SkillFile`: frontmatter field 'name' is missing or empty")
    }
    elseif ($Metadata.Name -ne $Metadata.Directory.Name) {
        $ValidationErrors.Add(
            "$SkillFile`: frontmatter name '$($Metadata.Name)' must match directory '$($Metadata.Directory.Name)'"
        )
    }
    elseif ($Metadata.Name.Length -gt 64 -or $Metadata.Name -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
        $ValidationErrors.Add("$SkillFile`: name must be at most 64 lowercase letters, digits, or hyphen-separated words")
    }

    if ([string]::IsNullOrWhiteSpace($Metadata.Description)) {
        $ValidationErrors.Add("$SkillFile`: frontmatter field 'description' is missing or empty")
    }
    else {
        if ($Metadata.Description.Length -gt 1024) {
            $ValidationErrors.Add("$SkillFile`: description exceeds the 1024-character portable limit")
        }
        if ($Metadata.Description -match '[<>]') {
            $ValidationErrors.Add("$SkillFile`: description cannot contain angle brackets")
        }
        if (-not $Metadata.DescriptionQuoted -and $Metadata.DescriptionRaw -match ':\s') {
            $ValidationErrors.Add("$SkillFile`: quote a description containing colon followed by whitespace")
        }
    }
}

$MetadataNameGroups = @(
    $SkillMetadata |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_.Name) } |
        Group-Object -Property Name |
        Where-Object { $_.Count -gt 1 }
)
foreach ($Group in $MetadataNameGroups) {
    $Paths = ($Group.Group | ForEach-Object { Join-Path $_.Directory.FullName "SKILL.md" }) -join ", "
    $ValidationErrors.Add("Skill metadata name '$($Group.Name)' is duplicated: $Paths")
}

if ($ValidationErrors.Count -gt 0) {
    Write-Host "ERROR: Skill sync validation failed:" -ForegroundColor Red
    foreach ($ValidationError in $ValidationErrors) {
        Write-Host "  - $ValidationError" -ForegroundColor Red
    }
    exit 1
}

$ScopeRoot = if ($ProjectPath) {
    (Resolve-Path -LiteralPath $ProjectPath).Path
}
else {
    $UserHome
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
