$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Failures = [System.Collections.Generic.List[string]]::new()
$Passed = 0

function Assert-TextContains {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Message
    )

    $Content = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot $Path)
    if ($Content -notmatch $Pattern) {
        throw $Message
    }
}

function Assert-TextExcludes {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Message
    )

    $Content = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot $Path)
    if ($Content -match $Pattern) {
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

Invoke-Test "entry docs describe Agent Skills for both platforms" {
    Assert-TextContains "README.md" '\.agents[\\/]skills' "README lacks the Codex skill target"
    Assert-TextContains "README.md" '\.claude[\\/]skills' "README lacks the Claude Code skill target"
    Assert-TextExcludes "AGENTS.md" 'Codex 无(?:对应机制| skill 发现机制)' "AGENTS still says Codex cannot discover skills"
}

Invoke-Test "sync script help documents user and project targets" {
    Assert-TextContains "scripts/sync-skills.ps1" 'ProjectPath' "script help does not mention ProjectPath"
    Assert-TextContains "scripts/sync-skills.ps1" '\.agents[\\/]skills' "script help does not mention the Codex target"
    Assert-TextContains "scripts/sync-skills.ps1" '\.claude[\\/]skills' "script help does not mention the Claude target"
}

Invoke-Test "UE MCP skills do not claim generic use is Claude-only" {
    Assert-TextExcludes "skills/ue/unrealmcp-usage/SKILL.md" 'from a Claude Code session' "unrealmcp description is still Claude-only"
    Assert-TextContains "skills/ue/unrealmcp-usage/SKILL.md" '\.agents/skills/unrealmcp-usage' "unrealmcp lacks the Codex-installed client path"
    Assert-TextContains "skills/ue/unrealmcp-usage/SKILL.md" '<skill-dir>' "unrealmcp commands lack a platform-neutral skill path"
    Assert-TextExcludes "skills/ue/official-mcp-usage/SKILL.md" 'from a Claude Code session' "official MCP description is still Claude-only"
    Assert-TextContains "skills/ue/official-mcp-usage/SKILL.md" '\.codex/config\.toml' "official MCP lacks Codex project configuration"
}

Invoke-Test "workflow skills define platform-neutral roots" {
    foreach ($Path in @(
        "skills/workflow/autonomous-workflow/SKILL.md",
        "skills/workflow/supervised-workflow/SKILL.md"
    )) {
        Assert-TextContains $Path '<project-skill-root>' "$Path lacks project skill root mapping"
        Assert-TextContains $Path '<agent-state-root>' "$Path lacks agent state root mapping"
    }
}

Invoke-Test "autonomous workflow records and compares an executable task baseline" {
    $Path = "skills/workflow/autonomous-workflow/SKILL.md"
    Assert-TextContains $Path 'TASK_BASELINE.*git rev-parse HEAD' "autonomous workflow does not record the starting commit"
    Assert-TextContains $Path 'git status --short.*verbatim' "autonomous workflow does not preserve the initial dirty-state manifest"
    Assert-TextContains $Path '(?s)overlap.*plan gate' "autonomous workflow does not resolve overlap with pre-existing edits before implementation"
    Assert-TextContains $Path 'SCOPE ATTRIBUTION \(all tasks' "scope attribution is not an unconditional Phase 4 gate"
    Assert-TextContains $Path 'git diff --name-status <TASK_BASELINE>\.\.HEAD' "autonomous workflow does not compare committed task changes"
    Assert-TextContains $Path 'git diff --cached' "autonomous workflow does not inspect staged task changes"
    Assert-TextContains $Path 'git ls-files --others --exclude-standard' "autonomous workflow does not enumerate untracked task changes"
}

Invoke-Test "workflow review loops stop after three failures without scope creep" {
    Assert-TextContains "guidelines/workflow/agent-lifecycle.md" 'reviewer rejection[\s\S]*counts as one[\s\S]*failed iteration' "lifecycle policy does not count reviewer rejection as a failed iteration"
    Assert-TextContains "guidelines/workflow/agent-lifecycle.md" 'Green tests do not[\s\S]*reset' "lifecycle policy lets green tests reset a rejected review loop"
    Assert-TextContains "guidelines/workflow/agent-lifecycle.md" 'override[\s\S]*repeat until approved' "lifecycle policy does not override unbounded composed review loops"
    foreach ($Path in @(
        "skills/workflow/autonomous-workflow/SKILL.md",
        "skills/workflow/supervised-workflow/SKILL.md"
    )) {
        Assert-TextContains $Path 'three-failure budget' "$Path does not inherit the shared three-failure budget"
        Assert-TextContains $Path 'scope change' "$Path does not stop reviewer-driven scope expansion"
        Assert-TextContains $Path 'repeat\s+until approved' "$Path does not override the third-party unbounded review loop"
    }
}

Invoke-Test "workflow rules triage findings and preserve approved plan identity" {
    $Lifecycle = "guidelines/workflow/agent-lifecycle.md"
    Assert-TextContains $Lifecycle 'Mandatory finding triage' "lifecycle policy lacks a mandatory pre-remediation triage"
    foreach ($Category in @('Planned defect', 'Hardening or advisory', 'Architecture or scope change', 'External feasibility blocker')) {
        Assert-TextContains $Lifecycle $Category "lifecycle policy lacks finding category: $Category"
    }
    Assert-TextContains $Lifecycle 'Severity labels do not authorize implementation' "review severity can still be mistaken for scope authorization"
    Assert-TextContains $Lifecycle 'threat model' "lifecycle policy does not prevent silent threat-model expansion"
    Assert-TextContains $Lifecycle 'failure ledger' "lifecycle policy does not require an explicit review-failure counter"

    $Autonomous = "skills/workflow/autonomous-workflow/SKILL.md"
    Assert-TextContains $Autonomous 'canonical Milestone' "autonomous workflow does not preserve the approved milestone numbering"
    Assert-TextContains $Autonomous 'failure ledger' "autonomous workflow does not maintain a review-failure ledger"
    Assert-TextContains $Autonomous 'new (?:process|transport|protocol)' "autonomous workflow does not recognize concrete architecture-change signals"
    Assert-TextContains $Autonomous 'threat model' "autonomous workflow does not lock the approved trust assumptions"

    $Supervised = "skills/workflow/supervised-workflow/SKILL.md"
    Assert-TextContains $Supervised 'canonical Milestone' "supervised workflow does not preserve the approved milestone numbering"
    Assert-TextContains $Supervised 'finding triage' "supervised workflow does not require finding classification before remediation"
}

Invoke-Test "plans prove product surface before whole-plan approval" {
    $Constraints = "guidelines/code/constraints.md"
    Assert-TextContains $Constraints 'Whole-plan approval[\s\S]*(?:does not|cannot)[\s\S]*requirement' "constraints let whole-plan approval manufacture requirement justification"
    Assert-TextContains $Constraints 'deletion test' "constraints do not require deleting unjustified plan surface"

    $Audit = "skills/workflow/auditing-plan-scope/SKILL.md"
    Assert-TextContains $Audit 'scope baseline' "scope audit does not establish a de-anchored baseline before reading candidate rationale"
    Assert-TextContains $Audit 'candidate mechanism[\s\S]*(?:does not|cannot)[\s\S]*(?:create|become)[\s\S]*requirement' "scope audit lets a candidate mechanism manufacture its own requirement"
    Assert-TextContains $Audit 'broad quality label[\s\S]*smallest observable' "scope audit lets broad quality language authorize an arbitrary mechanism set"
    Assert-TextContains $Audit 'Requirement basis[\s\S]*explicit[\s\S]*inferred' "scope audit does not distinguish explicit requirements from agent inference"
    Assert-TextContains $Audit 'reviewer[\s\S]*cannot establish[\s\S]*current[\s\S]*user flow' "scope audit lets reviewer framing manufacture a current user flow"
    Assert-TextContains $Audit 'existing request boundary' "scope audit does not prefer boundary validation before a new session lifecycle"
    Assert-TextContains $Audit 'Keep[\s\S]*Merge[\s\S]*Internalize[\s\S]*Temporary validation[\s\S]*explicit current requirement' "scope audit lets inclusion dispositions bypass explicit current requirement evidence"
    Assert-TextContains $Audit 'inferred[\s\S]*(?:Defer|Delete)[\s\S]*unresolved' "scope audit lets inferred scope enter the plan through Merge or Internalize"
    Assert-TextContains $Audit 'For every non-trivial design' "scope audit does not run the product-surface prefilter for every non-trivial design"
    Assert-TextContains $Audit 'If the list is empty[\s\S]*Otherwise run the full audit' "scope audit does not distinguish a clean prefilter from a triggered full audit"
    Assert-TextContains $Audit 'process[\s\S]*transport[\s\S]*protocol[\s\S]*persistent state[\s\S]*public interface[\s\S]*command[\s\S]*configuration[\s\S]*security or trust boundary[\s\S]*lifecycle mechanism' "scope audit misses product-surface expansion signals"
    Assert-TextContains $Audit 'Consumer and frequency[\s\S]*Requirement basis[\s\S]*Deletion consequence[\s\S]*Existing alternative[\s\S]*Disposition[\s\S]*Closure condition' "scope audit table omits an approved adjudication field"
    Assert-TextContains $Audit 'reverse traceability' "scope audit does not trace proposed surfaces upward to a current user flow"
    Assert-TextContains $Audit 'deletion test' "scope audit lacks a mandatory deletion test"
    Assert-TextContains $Audit 'Keep[\s\S]*Merge[\s\S]*Internalize[\s\S]*Temporary validation[\s\S]*Defer[\s\S]*Delete' "scope audit lacks the six approved per-candidate dispositions"
    Assert-TextContains $Audit 'temporary validation' "scope audit does not govern temporary probe or test surfaces"
    Assert-TextContains $Audit 'roadmap[\s\S]*TODO[\s\S]*issue' "scope audit silently converts deleted scope into future commitments"

    $Autonomous = "skills/workflow/autonomous-workflow/SKILL.md"
    Assert-TextContains $Autonomous 'full scope audit[\s\S]*Self-Brainstorm' "autonomous workflow does not run the full audit after self-brainstorm"
    Assert-TextContains $Autonomous 'delta scope audit[\s\S]*Self-Plan' "autonomous workflow does not review plan deltas before its only gate"
    $AutonomousContent = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot $Autonomous)
    if ([regex]::Matches($AutonomousContent, '(?m)^\[GATE[^\]]*\]').Count -ne 1) {
        throw "autonomous workflow no longer has exactly one top-level user gate"
    }

    $Supervised = "skills/workflow/supervised-workflow/SKILL.md"
    Assert-TextContains $Supervised 'full scope audit[\s\S]*Gate 1' "supervised workflow does not require the full audit before design approval"
    Assert-TextContains $Supervised 'delta scope audit[\s\S]*Gate 2' "supervised workflow does not require the delta audit before implementation-plan approval"

    Assert-TextContains "AGENTS.md" 'auditing-plan-scope/SKILL\.md' "AGENTS does not register the on-demand scope-audit skill"
}

Invoke-Test "workflow skills leave promotion decisions to knowledge-promotion" {
    foreach ($Path in @(
        "skills/workflow/autonomous-workflow/SKILL.md",
        "skills/workflow/bugfix-tdd/SKILL.md"
    )) {
        Assert-TextContains $Path 'knowledge-promotion\.md' "$Path does not route promotion decisions to the canonical policy"
        Assert-TextExcludes $Path 'confirmed[^\r\n]*(?:可进入规则库|may be promoted)' "$Path lets evidence level authorize promotion"
    }
}

Invoke-Test "Claude hook coordination skill declares its platform limit" {
    Assert-TextContains "skills/collaboration/multi-session-coordination/SKILL.md" 'Claude Code[- ]only' "multi-session skill does not declare its Claude-only limit"
}

Invoke-Test "skill frontmatter uses the shared portable fields" {
    $SkillFiles = Get-ChildItem -Recurse -Filter SKILL.md (Join-Path $RepoRoot "skills")
    foreach ($SkillFile in $SkillFiles) {
        $Content = Get-Content -Raw -LiteralPath $SkillFile.FullName
        if ($Content -match '(?m)^when_to_use:') {
            throw "$($SkillFile.FullName) contains unsupported when_to_use frontmatter"
        }
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
