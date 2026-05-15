# install.ps1
# Auto-merge multi-session-coordination hooks into ~/.claude/settings.json.
#
# Idempotent: running twice is safe — existing entries for our commands are
# replaced, not duplicated. Always creates a timestamped backup.
#
# Usage:
#   pwsh ~/.claude/skills/multi-session-coordination/install.ps1
#   or
#   powershell -File ~/.claude/skills/multi-session-coordination/install.ps1
#
# Uninstall:
#   pwsh ~/.claude/skills/multi-session-coordination/install.ps1 -Uninstall

[CmdletBinding()]
param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$SkillDir       = $PSScriptRoot
$SnippetPath    = Join-Path $SkillDir "settings-snippet.json"
$SettingsPath   = Join-Path $env:USERPROFILE ".claude\settings.json"
$BackupSuffix   = "bak.$([DateTimeOffset]::Now.ToUnixTimeSeconds())"
$BackupPath     = "$SettingsPath.$BackupSuffix"

# Match marker: any hook command containing this substring belongs to us.
$OurMarker      = "skills\multi-session-coordination\multi_session.py"

# --- read snippet --------------------------------------------------------

if (-not (Test-Path $SnippetPath)) {
    throw "settings-snippet.json not found at $SnippetPath"
}

# Claude Code does NOT shell-expand %USERPROFILE% (or $HOME) in hook command
# strings — it passes them verbatim to the OS process layer. So the snippet's
# placeholder paths must be baked into actual absolute paths at install time.
# JSON encodes backslashes as `\\`, so we double them in the replacement.
$snippetRaw = Get-Content $SnippetPath -Raw
$userProfileForJson = $env:USERPROFILE.Replace('\', '\\')
$snippetRaw = $snippetRaw.Replace('%USERPROFILE%', $userProfileForJson)
$snippet = $snippetRaw | ConvertFrom-Json
$snippetHooks = $snippet.hooks
if (-not $snippetHooks) {
    throw "snippet has no 'hooks' key"
}

# --- read existing settings ----------------------------------------------

if (Test-Path $SettingsPath) {
    Copy-Item $SettingsPath $BackupPath
    Write-Host "Backed up existing settings → $BackupPath"
    $settings = Get-Content $SettingsPath -Raw | ConvertFrom-Json
} else {
    Write-Host "No existing $SettingsPath — will create."
    $settings = [PSCustomObject]@{}
}

# Ensure .hooks exists as an ordered object
if (-not ($settings.PSObject.Properties.Name -contains "hooks")) {
    $settings | Add-Member -NotePropertyName "hooks" -NotePropertyValue ([PSCustomObject]@{})
}

# --- helpers -------------------------------------------------------------

function Remove-OurHooks {
    param([PSCustomObject]$Settings)
    if (-not $Settings.hooks) { return }
    # Filter out $null / empty names (happens when .Name is $null on empty obj)
    $eventNames = @($Settings.hooks.PSObject.Properties.Name | Where-Object { $_ })
    foreach ($eventName in $eventNames) {
        $existing = @($Settings.hooks.$eventName)
        $kept = @()
        foreach ($entry in $existing) {
            # Each $entry has its own .hooks array of {type, command, ...}
            $subKept = @()
            if ($entry.hooks) {
                foreach ($cmd in $entry.hooks) {
                    if ($cmd.command -and $cmd.command -like "*$OurMarker*") {
                        # ours — drop
                        continue
                    }
                    $subKept += $cmd
                }
            }
            if ($subKept.Count -gt 0) {
                $entry.hooks = $subKept
                $kept += $entry
            }
        }
        if ($kept.Count -eq 0) {
            $Settings.hooks.PSObject.Properties.Remove($eventName)
        } else {
            $Settings.hooks.$eventName = $kept
        }
    }
}

function Add-OurHooks {
    param(
        [PSCustomObject]$Settings,
        [PSCustomObject]$NewHooks
    )
    foreach ($eventName in $NewHooks.PSObject.Properties.Name) {
        $newEntries = @($NewHooks.$eventName)
        if ($Settings.hooks.PSObject.Properties.Name -contains $eventName) {
            $existing = @($Settings.hooks.$eventName)
            $Settings.hooks.$eventName = $existing + $newEntries
        } else {
            $Settings.hooks | Add-Member -NotePropertyName $eventName -NotePropertyValue $newEntries
        }
    }
}

# --- apply ---------------------------------------------------------------

# Always remove our existing entries first (idempotent re-install + cleanup)
Remove-OurHooks -Settings $settings

if (-not $Uninstall) {
    Add-OurHooks -Settings $settings -NewHooks $snippetHooks
    Write-Host "Installed multi-session-coordination hooks."
} else {
    Write-Host "Uninstalled multi-session-coordination hooks."
}

# --- write back ----------------------------------------------------------

# Drop "_comment" field if it accidentally ended up at top level (shouldn't)
if ($settings.PSObject.Properties.Name -contains "_comment") {
    $settings.PSObject.Properties.Remove("_comment")
}

# If hooks ended up empty, remove the empty object to keep settings.json tidy
if ($settings.hooks) {
    $remaining = @($settings.hooks.PSObject.Properties.Name | Where-Object { $_ -and $_ -ne "_comment" })
    if ($remaining.Count -eq 0) {
        $settings.PSObject.Properties.Remove("hooks")
    }
}

# Write JSON with stable indentation.
# PS 5.1 `Set-Content -Encoding UTF8` writes a BOM, which trips most JSON
# parsers (Python json.load, etc). Use .NET API for guaranteed no-BOM UTF-8.
$jsonText = $settings | ConvertTo-Json -Depth 20
$noBomUtf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($SettingsPath, $jsonText, $noBomUtf8)

Write-Host ""
Write-Host "Done. Restart any open Claude Code session to pick up the new hooks."
Write-Host "Backup: $BackupPath"
