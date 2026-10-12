$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Failures = [System.Collections.Generic.List[string]]::new()
$Passed = 0

function Get-TextUnderTest {
    param([string]$Path)

    $AbsolutePath = Join-Path $RepoRoot $Path
    if ((Split-Path -Leaf $AbsolutePath) -ne "SKILL.md") {
        return Get-Content -Raw -LiteralPath $AbsolutePath
    }

    # Phase documents are part of the skill contract; their location is not a gate.
    # Keep the boundary to this package, without pulling in unrelated skills or norms.
    $Documents = @(Get-ChildItem -LiteralPath (Split-Path -Parent $AbsolutePath) -Recurse -File -Filter "*.md" |
        Sort-Object FullName)
    return (($Documents | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName }) -join [Environment]::NewLine)
}

function Assert-TextContains {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Message
    )

    $Content = Get-TextUnderTest $Path
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

    $Content = Get-TextUnderTest $Path
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

Invoke-Test "workflow skills retain accessible platform-neutral root mappings" {
    Assert-TextContains "skills/workflow/autonomous-workflow/SKILL.md" '\(records-reference\.md\)' "autonomous workflow does not link its record reference"
    Assert-TextContains "skills/workflow/supervised-workflow/SKILL.md" '\(\.\./autonomous-workflow/records-reference\.md\)' "supervised workflow does not link the shared record reference"
    $Reference = "skills/workflow/autonomous-workflow/records-reference.md"
    Assert-TextContains $Reference 'Claude Code[^\r\n]*~/.claude[^\r\n]*<project>/\.claude/skills' "record reference lacks Claude state and project skill roots"
    Assert-TextContains $Reference 'Codex[^\r\n]*CODEX_HOME[^\r\n]*~/.codex[^\r\n]*<project>/\.agents/skills' "record reference lacks Codex state and project skill roots"
}

Invoke-Test "autonomous workflow records and compares an executable task baseline" {
    $Path = "skills/workflow/autonomous-workflow/SKILL.md"
    Assert-TextContains $Path 'git rev-parse HEAD' "autonomous workflow does not provide the starting-commit query"
    Assert-TextContains $Path 'keep that original commit as `TASK_BASELINE`' "autonomous workflow does not bind its baseline to the original commit"
    Assert-TextContains $Path 'retain both original[\s\S]*outputs[\s\S]*git status --short' "autonomous workflow does not preserve the initial dirty-state output"
    Assert-TextContains $Path '(?s)pre-existing edits before changing overlapping content.*ownership is\s+unresolved, pause that edit' "autonomous workflow does not resolve overlap with pre-existing edits before implementation"
    Assert-TextContains $Path '(?s)committed changes from the original task baseline through HEAD.*staged, unstaged and untracked task-owned content.*Preserve attribution of pre-existing changes' "whole-result review does not cover and attribute all task-owned change states"
    Assert-TextContains $Path 'git diff --name-status <TASK_BASELINE>\.\.HEAD' "autonomous workflow does not compare committed task changes"
    Assert-TextContains $Path 'git diff --cached' "autonomous workflow does not inspect staged task changes"
    Assert-TextContains $Path 'git ls-files --others --exclude-standard' "autonomous workflow does not enumerate untracked task changes"
}

Invoke-Test "workflow review loops stop repeated failure signatures without scope creep" {
    $Lifecycle = "guidelines/workflow/agent-lifecycle.md"
    Assert-TextContains $Lifecycle 'reviewer rejection counts toward escalation only when remediation[\s\S]*same root cause and the same observable failure' "lifecycle policy does not bind rejection escalation to the recurring failure"
    Assert-TextContains $Lifecycle 'Green tests[\s\S]*neither erase an unresolved signature nor combine[\s\S]*distinct signatures into one counter' "lifecycle policy resets or combines unrelated failure signatures"
    Assert-TextContains $Lifecycle 'three consecutive targeted repairs fail for one signature, stop[\s\S]*notify the user' "lifecycle policy does not stop and report three failed repairs of the same signature"
    Assert-TextContains $Lifecycle 'overrides composed or third-party workflow wording[\s\S]*loop one failing method indefinitely[\s\S]*cumulative[\s\S]*cap across unrelated findings' "lifecycle policy does not override unbounded loops and unrelated cumulative caps"
    Assert-TextContains $Lifecycle 'outside the approved plan[\s\S]*immediate scope-change escalation; do not implement it first' "lifecycle policy allows reviewer-driven scope expansion before a decision"
    foreach ($Path in @(
        "skills/workflow/autonomous-workflow/SKILL.md",
        "skills/workflow/supervised-workflow/SKILL.md"
    )) {
        Assert-TextContains $Path 'agent-lifecycle\.md' "$Path does not route recurring failures to the shared policy"
        Assert-TextContains $Path 'same root cause[\s\S]*observable failure[\s\S]*three consecutive targeted repairs' "$Path loses the same-signature three-repair boundary"
        Assert-TextContains $Path '(?s)(?:outside the authorized scope need authorization|outside the plan needs a\s+decision).*before implementation|outside the plan needs a\s+decision immediately' "$Path does not stop scope expansion before implementation"
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
    Assert-TextContains $Lifecycle 'separate ledger only for a recurring failure signature[\s\S]*consecutive targeted repair attempt number' "lifecycle policy does not record recurring attempts separately"

    $Autonomous = "skills/workflow/autonomous-workflow/SKILL.md"
    Assert-TextContains $Autonomous 'canonical Milestone' "autonomous workflow does not preserve the approved milestone numbering"
    Assert-TextContains $Autonomous 'separate histories for[\s\S]*different failures' "autonomous workflow does not preserve separate recurring-failure histories"
    Assert-TextContains $Autonomous 'interfaces, dependencies, schemas or trust/lifecycle changes[\s\S]*outside the authorized scope need authorization before implementation' "autonomous workflow does not recognize concrete out-of-scope architecture changes"
    Assert-TextContains $Autonomous 'threat model' "autonomous workflow does not lock the approved trust assumptions"

    $Supervised = "skills/workflow/supervised-workflow/SKILL.md"
    Assert-TextContains $Supervised 'canonical Milestone' "supervised workflow does not preserve the approved milestone numbering"
    Assert-TextContains $Supervised 'finding triage' "supervised workflow does not require finding classification before remediation"
    foreach ($Path in @($Autonomous, $Supervised)) {
        Assert-TextContains $Path 'Required independent(?: review| or human verification)' "$Path loses required independent or human review"
    }
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
    Assert-TextContains $Autonomous "Compare the proposed work with the user's scope[\s\S]*scope expansion needs a decision before[\s\S]*implementation" "autonomous workflow does not check scope before implementing expansion"
    Assert-TextContains $Autonomous 'user requested one plan approval[\s\S]*reuse a matching explicit approval or wait for it' "autonomous workflow does not preserve a requested approval while reusing a valid one"
    Assert-TextContains $Autonomous 'Do not infer approval from silence' "autonomous workflow treats silence as approval"

    $Supervised = "skills/workflow/supervised-workflow/SKILL.md"
    Assert-TextContains $Supervised "Check scope against the request[\s\S]*authorized outcome[\s\S]*Continue — Gate 1[\s\S]*explicit approval of this design" "supervised workflow loses scope review and explicit design approval"
    Assert-TextContains $Supervised 'Compare the plan with the design[\s\S]*scope/architecture deltas[\s\S]*Continue — Gate 2[\s\S]*explicit approval covering this plan' "supervised workflow loses delta review and explicit plan approval"
    Assert-TextContains $Supervised "Wait for the user's review before starting the next unit[\s\S]*plan approval alone does not" "supervised workflow treats plan approval as acceptance of an unseen unit"
    Assert-TextContains $Supervised 'silence or an ambiguous response supplies[\s\S]*neither' "supervised workflow treats silence or ambiguity as approval"

    Assert-TextContains "AGENTS.md" '\(skills/INDEX\.md\)' "AGENTS does not route to the skill index"
    Assert-TextContains "skills/INDEX.md" '\(workflow/auditing-plan-scope/SKILL\.md\)' "skill index does not register the on-demand scope-audit skill"
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
