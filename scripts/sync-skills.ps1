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
            Error = "$SkillFile`: missing valid YAML frontmatter boundaries"
        }
    }

    $Yaml = $Frontmatter.Groups["yaml"].Value
    return [pscustomobject]@{
        Directory = $SkillDirectory
        Name = Get-YamlScalarField $Yaml "name"
        Description = Get-YamlScalarField $Yaml "description"
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
    if ([string]::IsNullOrWhiteSpace($Metadata.Name)) {
        $ValidationErrors.Add("$SkillFile`: frontmatter field 'name' is missing or empty")
    }
    elseif ($Metadata.Name -ne $Metadata.Directory.Name) {
        $ValidationErrors.Add(
            "$SkillFile`: frontmatter name '$($Metadata.Name)' must match directory '$($Metadata.Directory.Name)'"
        )
    }

    if ([string]::IsNullOrWhiteSpace($Metadata.Description)) {
        $ValidationErrors.Add("$SkillFile`: frontmatter field 'description' is missing or empty")
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
